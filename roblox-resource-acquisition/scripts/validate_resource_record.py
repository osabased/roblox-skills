#!/usr/bin/env python3
"""Validate portable Roblox resource evidence records.

This is a structural and state-consistency validator. Passing does not establish
that the resource, source claims, or generated skill are actually correct.

PyYAML is required (see requirements.txt). A single parser everywhere keeps
trust/verification verdicts identical across environments; the script exits
with code 2 and an install hint when PyYAML is missing.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (
    DEVFORUM_TOPIC_PATH_RE,
    SLUG_RE,
    VOLATILE_VERSION_TOKEN_RE,
    has_immutable_version_evidence,
    load_yaml,
    normalize_empty_values,
    validate_date,
    validate_https_url,
    validated_url_host,
)

TOP_LEVEL_FIELDS = {
    "resource",
    "slug",
    "discovery_origin",
    "trust",
    "canonical_url",
    "package_id",
    "verification",
    "capability",
    "devforum_url",
    "selection_reason",
    "alternatives_considered",
    "resource_proof",
    "generated_skill",
    "skill_validation",
    "limitations",
    "blocked_use_or_version",
    "rejection_reason",
    "reconsider_when",
}
REQUIRED_TOP_LEVEL_FIELDS = TOP_LEVEL_FIELDS
NESTED_FIELDS = {
    "trust": {"level", "basis", "reason"},
    "verification": {"status", "validated_at", "version_or_commit"},
    "resource_proof": {"executed", "passed", "environment", "result", "unavailable_claims"},
    "skill_validation": {
        "structural_passed",
        "independent_behavioral_executed",
        "independent_behavioral_passed",
        "environment",
        "result",
    },
}
LIST_FIELDS = {
    "alternatives_considered",
    "limitations",
    "resource_proof.unavailable_claims",
}
BOOL_FIELDS = {
    "resource_proof.executed",
    "resource_proof.passed",
    "skill_validation.structural_passed",
    "skill_validation.independent_behavioral_executed",
    "skill_validation.independent_behavioral_passed",
}
STRING_FIELDS = {
    "resource",
    "slug",
    "discovery_origin",
    "canonical_url",
    "package_id",
    "capability",
    "devforum_url",
    "selection_reason",
    "generated_skill",
    "blocked_use_or_version",
    "rejection_reason",
    "reconsider_when",
    "trust.level",
    "trust.basis",
    "trust.reason",
    "verification.status",
    "verification.validated_at",
    "verification.version_or_commit",
    "resource_proof.environment",
    "resource_proof.result",
    "skill_validation.environment",
    "skill_validation.result",
}
ALLOWED_ORIGINS = {"curated", "project", "devforum", "other"}
ALLOWED_TRUST_LEVELS = {"trusted", "untrusted"}
ALLOWED_TRUST_BASES = {"", "curated", "verified-acquisition", "project", "explicit-user", "other"}
ALLOWED_VERIFICATION = {"unverified", "unavailable", "verified", "failed"}


def load_record(path: Path) -> dict[str, Any]:
    loaded = load_yaml(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("record must be a YAML mapping")
    normalize_empty_values(loaded, LIST_FIELDS)
    # PyYAML resolves an unquoted ISO date to datetime.date. Accept that
    # natural YAML spelling and normalize it to the schema's string form.
    verification = loaded.get("verification")
    if isinstance(verification, dict) and isinstance(verification.get("validated_at"), date):
        verification["validated_at"] = verification["validated_at"].isoformat()
    return loaded


def dotted_get(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_record(path: Path, data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []

    unknown = sorted(set(data) - TOP_LEVEL_FIELDS)
    missing = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(data))
    if unknown:
        errors.append(f"unknown top-level field(s): {', '.join(unknown)}")
    if missing:
        errors.append(f"missing required top-level field(s): {', '.join(missing)}")

    for parent, allowed in NESTED_FIELDS.items():
        value = data.get(parent)
        if not isinstance(value, dict):
            errors.append(f"{parent} must be a mapping")
            continue
        nested_unknown = sorted(set(value) - allowed)
        nested_missing = sorted(allowed - set(value))
        if nested_unknown:
            errors.append(f"unknown {parent} field(s): {', '.join(nested_unknown)}")
        if nested_missing:
            errors.append(f"missing required {parent} field(s): {', '.join(nested_missing)}")

    for field in STRING_FIELDS:
        value = dotted_get(data, field)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field} must be a string")

    for field in LIST_FIELDS:
        value = dotted_get(data, field)
        if value is None:
            continue
        if not isinstance(value, list):
            errors.append(f"{field} must be a list")
            continue
        if any(not isinstance(item, str) or not item.strip() for item in value):
            errors.append(f"{field} must contain only non-empty strings")

    for field in BOOL_FIELDS:
        value = dotted_get(data, field)
        if value is not None and not isinstance(value, bool):
            errors.append(f"{field} must be true or false")

    resource = data.get("resource")
    if isinstance(resource, str) and not resource.strip():
        errors.append("resource must not be empty")

    slug = data.get("slug")
    if isinstance(slug, str) and slug.strip() and not SLUG_RE.fullmatch(slug.strip()):
        errors.append("slug must be lowercase kebab-case (a-z, 0-9, hyphen) when present")

    origin = data.get("discovery_origin")
    if isinstance(origin, str) and origin not in ALLOWED_ORIGINS:
        errors.append(f"discovery_origin must be one of: {', '.join(sorted(ALLOWED_ORIGINS))}")

    trust_level = dotted_get(data, "trust.level")
    trust_basis = dotted_get(data, "trust.basis")
    trust_reason = dotted_get(data, "trust.reason")
    if isinstance(trust_level, str) and trust_level not in ALLOWED_TRUST_LEVELS:
        errors.append("trust.level must be exactly trusted or untrusted")
    if isinstance(trust_basis, str) and trust_basis not in ALLOWED_TRUST_BASES:
        errors.append("trust.basis must be curated, verified-acquisition, project, explicit-user, other, or empty")
    if trust_level == "trusted":
        if not nonempty_string(trust_basis):
            errors.append("trusted records must name a trust.basis")
        if not nonempty_string(trust_reason):
            errors.append("trusted records must explain trust.reason")
    if trust_basis in {"curated", "verified-acquisition", "project", "explicit-user"} and trust_level != "trusted":
        errors.append(f"trust.basis {trust_basis!r} requires trust.level: trusted")
    if trust_basis == "curated" and origin != "curated":
        errors.append("trust.basis curated requires discovery_origin: curated")
    if trust_basis == "verified-acquisition" and origin == "curated":
        errors.append("verified-acquisition is for previously untrusted discovery, not curated-origin records")

    canonical = data.get("canonical_url")
    if isinstance(canonical, str) and canonical.strip():
        errors.extend(validate_https_url(canonical.strip(), field="canonical_url"))
    devforum = data.get("devforum_url")
    if isinstance(devforum, str) and devforum.strip():
        devforum_value = devforum.strip()
        errors.extend(validate_https_url(devforum_value, field="devforum_url", expected_host="devforum.roblox.com"))
        try:
            parsed_devforum = urlparse(devforum_value)
        except ValueError:
            parsed_devforum = None
        if parsed_devforum is not None and validated_url_host(parsed_devforum) == "devforum.roblox.com":
            if not DEVFORUM_TOPIC_PATH_RE.fullmatch(parsed_devforum.path):
                errors.append("devforum_url must identify a specific DevForum topic, not a category/home/search page")

    status = dotted_get(data, "verification.status")
    validated_at = dotted_get(data, "verification.validated_at")
    version = dotted_get(data, "verification.version_or_commit")
    if isinstance(status, str) and status not in ALLOWED_VERIFICATION:
        errors.append("verification.status must be unverified, unavailable, verified, or failed")
    if isinstance(validated_at, str) and validated_at.strip():
        errors.extend(validate_date(validated_at.strip(), field="verification.validated_at"))
    if status in {"verified", "unavailable", "failed"} and not nonempty_string(validated_at):
        errors.append(f"verification.status {status!r} requires verification.validated_at")
    if status == "verified" and not nonempty_string(version):
        errors.append("verified resource records must name verification.version_or_commit")
    if status == "verified" and isinstance(version, str) and version.strip() and not has_immutable_version_evidence(version):
        errors.append(
            "verified resource records require an immutable version/commit, an explicitly labeled named tag/release/build, or a valid dated source state"
        )
    if isinstance(version, str) and version.strip() and VOLATILE_VERSION_TOKEN_RE.search(version):
        if not has_immutable_version_evidence(version):
            errors.append("verification.version_or_commit must not rely only on a volatile pointer such as latest/current/main")

    proof_executed = dotted_get(data, "resource_proof.executed")
    proof_passed = dotted_get(data, "resource_proof.passed")
    proof_environment = dotted_get(data, "resource_proof.environment")
    proof_result = dotted_get(data, "resource_proof.result")
    unavailable_claims = dotted_get(data, "resource_proof.unavailable_claims")
    if proof_passed is True and proof_executed is not True:
        errors.append("resource_proof.passed cannot be true unless resource_proof.executed is true")
    if proof_executed is True:
        if not nonempty_string(proof_environment):
            errors.append("executed resource proof must record resource_proof.environment")
        if not nonempty_string(proof_result):
            errors.append("executed resource proof must record resource_proof.result")
    if status == "verified":
        if proof_executed is not True or proof_passed is not True:
            errors.append("verification.status verified requires executed and passing resource_proof")
        if isinstance(unavailable_claims, list) and unavailable_claims:
            errors.append("verification.status verified cannot have material resource_proof.unavailable_claims")
    if status == "unavailable":
        if not isinstance(unavailable_claims, list) or not unavailable_claims:
            errors.append("verification.status unavailable requires at least one resource_proof.unavailable_claims entry")
        if proof_passed is True:
            errors.append("verification.status unavailable cannot have resource_proof.passed: true")
    if status == "failed" and proof_passed is True:
        errors.append("verification.status failed cannot have resource_proof.passed: true")
    if proof_passed is True and status not in {"verified"}:
        errors.append("passing overall resource_proof requires verification.status: verified")

    structural = dotted_get(data, "skill_validation.structural_passed")
    independent_executed = dotted_get(data, "skill_validation.independent_behavioral_executed")
    independent_passed = dotted_get(data, "skill_validation.independent_behavioral_passed")
    skill_environment = dotted_get(data, "skill_validation.environment")
    skill_result = dotted_get(data, "skill_validation.result")
    if independent_passed is True and independent_executed is not True:
        errors.append("independent_behavioral_passed cannot be true unless independent_behavioral_executed is true")
    if independent_executed is True:
        if not nonempty_string(skill_environment):
            errors.append("executed independent behavioral validation must record skill_validation.environment")
        if not nonempty_string(skill_result):
            errors.append("executed independent behavioral validation must record skill_validation.result")

    generated_skill = data.get("generated_skill")
    if any(value is True for value in (structural, independent_executed, independent_passed)) and not nonempty_string(generated_skill):
        errors.append("skill validation evidence requires generated_skill to identify the generated skill")

    if trust_basis == "verified-acquisition":
        required_nonempty = {
            "canonical_url": canonical,
            "verification.validated_at": validated_at,
            "verification.version_or_commit": version,
            "generated_skill": generated_skill,
        }
        for field, value in required_nonempty.items():
            if not nonempty_string(value):
                errors.append(f"verified-acquisition requires {field}")
        if status != "verified":
            errors.append("verified-acquisition requires verification.status: verified")
        if proof_executed is not True or proof_passed is not True:
            errors.append("verified-acquisition requires executed and passing resource_proof")
        if structural is not True:
            errors.append("verified-acquisition requires skill_validation.structural_passed: true")
        if independent_executed is not True or independent_passed is not True:
            errors.append("verified-acquisition requires executed and passing independent behavioral skill validation")
        if isinstance(unavailable_claims, list) and unavailable_claims:
            errors.append("verified-acquisition cannot have material resource_proof.unavailable_claims")

    if trust_basis == "curated":
        if not nonempty_string(slug):
            errors.append("curated records must carry the curated slug")
        if not nonempty_string(canonical):
            errors.append("curated records must carry canonical_url so trust cannot drift to a same-named resource")
        if status == "unverified":
            notes.append("curated + trusted + unverified is valid; curation establishes trust, not runtime verification")

    if status == "failed":
        if trust_basis == "curated" and not nonempty_string(data.get("blocked_use_or_version")):
            errors.append("failed curated records must identify blocked_use_or_version without revoking catalog trust")
        elif trust_level == "untrusted" and not nonempty_string(data.get("rejection_reason")):
            notes.append("failed untrusted record has no rejection_reason yet; acceptable during investigation, but record one before final rejection")

    return errors, notes


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a portable Roblox resource evidence record for structural and trust/verification state consistency."
        )
    )
    parser.add_argument("resource_record", type=Path, help="resource-record YAML file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    path = args.resource_record.resolve()
    if not path.is_file() or path.suffix.lower() not in {".yaml", ".yml"}:
        print(f"FAIL\n- expected an existing .yaml/.yml resource record: {path}")
        return 1
    try:
        data = load_record(path)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"FAIL\n- {exc}")
        return 1

    errors, notes = validate_record(path, data)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        for note in notes:
            print(f"NOTE: {note}")
        return 1

    print("PASS: resource-record structural/state checks passed")
    for note in notes:
        print(f"NOTE: {note}")
    print("NOTE: this does not prove source truth, resource behavior, or generated-skill behavior; it only checks that the recorded state is internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
