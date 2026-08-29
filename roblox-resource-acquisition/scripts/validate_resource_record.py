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
import re
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
    "schema_version",
    "resource",
    "slug",
    "discovery_origin",
    "trust",
    "canonical_url",
    "package_id",
    "verification",
    "reconciliation",
    "capability",
    "devforum_url",
    "selection_reason",
    "alternatives_considered",
    "resource_proof",
    "generated_skill",
    "skill_validation",
    "host_adoptions",
    "limitations",
    "blocked_use_or_version",
    "rejection_reason",
    "reconsider_when",
}
REQUIRED_TOP_LEVEL_FIELDS = TOP_LEVEL_FIELDS
NESTED_FIELDS = {
    "trust": {"level", "basis", "reason"},
    "verification": {"status", "validated_at", "version_or_commit"},
    "reconciliation": {
        "status",
        "checked_at",
        "installed_identity",
        "installed_version_or_commit",
        "detection_method",
        "parent_state_sources",
        "result",
    },
    "resource_proof": {"executed", "passed", "target_version_or_commit", "environment", "result", "unavailable_claims"},
    "skill_validation": {
        "structural_passed",
        "independent_behavioral_executed",
        "independent_behavioral_passed",
        "environment",
        "result",
        "catalog_routing_status",
        "catalog_fingerprint",
        "catalog_environment",
        "catalog_result",
    },
}
OPTIONAL_NESTED_FIELDS = {
    "resource_proof": {"target_version_or_commit"},
}
LIST_FIELDS = {
    "alternatives_considered",
    "limitations",
    "resource_proof.unavailable_claims",
    "reconciliation.parent_state_sources",
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
    "reconciliation.status",
    "reconciliation.checked_at",
    "reconciliation.installed_identity",
    "reconciliation.installed_version_or_commit",
    "reconciliation.detection_method",
    "reconciliation.result",
    "resource_proof.target_version_or_commit",
    "resource_proof.environment",
    "resource_proof.result",
    "skill_validation.environment",
    "skill_validation.result",
    "skill_validation.catalog_routing_status",
    "skill_validation.catalog_fingerprint",
    "skill_validation.catalog_environment",
    "skill_validation.catalog_result",
}
ALLOWED_ORIGINS = {"curated", "project", "devforum", "other"}
ALLOWED_TRUST_LEVELS = {"trusted", "untrusted"}
ALLOWED_TRUST_BASES = {"", "curated", "verified-acquisition", "project", "explicit-user", "other"}
ALLOWED_VERIFICATION = {"unverified", "unavailable", "verified", "failed"}
ALLOWED_RECONCILIATION = {"matched", "mismatched", "blocked", "unknown", "not-applicable"}
ALLOWED_CATALOG_ROUTING = {"not-applicable", "unverified", "verified", "unavailable", "failed"}
ALLOWED_HOST_SCOPES = {"repo", "user", "admin", "plugin", "other"}
ALLOWED_HOST_STATUSES = {"installed", "operational", "blocked", "disabled", "removed", "unavailable", "failed"}
ALLOWED_PRESENCE = {"present", "absent", "not-applicable", "unknown"}
ALLOWED_DISCOVERY = {"yes", "no", "unknown"}
ALLOWED_ENABLED = {"yes", "no", "not-applicable", "unknown"}
ALLOWED_ACTIVATION = {"passed", "failed", "not-run", "unavailable"}
HOST_FIELDS = {"host", "scope", "location", "status", "checked_at", "result", "evidence"}
HOST_EVIDENCE_FIELDS = {"installed", "registered", "discoverable", "enabled", "explicit_activation"}
FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


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
    reconciliation = loaded.get("reconciliation")
    if isinstance(reconciliation, dict) and isinstance(reconciliation.get("checked_at"), date):
        reconciliation["checked_at"] = reconciliation["checked_at"].isoformat()
    host_adoptions = loaded.get("host_adoptions")
    if isinstance(host_adoptions, list):
        for adoption in host_adoptions:
            if isinstance(adoption, dict) and isinstance(adoption.get("checked_at"), date):
                adoption["checked_at"] = adoption["checked_at"].isoformat()
            # PyYAML follows YAML 1.1 and resolves unquoted yes/no as booleans.
            # Preserve the public yes/no evidence vocabulary for ordinary YAML input.
            if isinstance(adoption, dict) and isinstance(adoption.get("evidence"), dict):
                evidence = adoption["evidence"]
                for field in ("discoverable", "enabled"):
                    if isinstance(evidence.get(field), bool):
                        evidence[field] = "yes" if evidence[field] else "no"
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

    if data.get("schema_version") != 2:
        errors.append("schema_version must be integer 2; legacy records must enter repair/reconcile")

    for parent, allowed in NESTED_FIELDS.items():
        value = data.get(parent)
        if not isinstance(value, dict):
            errors.append(f"{parent} must be a mapping")
            continue
        nested_unknown = sorted(set(value) - allowed)
        optional = OPTIONAL_NESTED_FIELDS.get(parent, set())
        nested_missing = sorted((allowed - optional) - set(value))
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

    selection_reason = data.get("selection_reason")
    if origin == "other" and not nonempty_string(selection_reason):
        errors.append("discovery_origin other requires selection_reason to preserve selection provenance")

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
        if not nonempty_string(slug):
            errors.append("trusted records require slug to bind trust to a stable identity")
        if not nonempty_string(data.get("canonical_url")) and not nonempty_string(data.get("package_id")):
            errors.append("trusted records require canonical_url or package_id to bind trust to canonical identity")
    if trust_basis in {"curated", "verified-acquisition", "project", "explicit-user", "other"} and trust_level != "trusted":
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
    proof_target = dotted_get(data, "resource_proof.target_version_or_commit")
    proof_environment = dotted_get(data, "resource_proof.environment")
    proof_result = dotted_get(data, "resource_proof.result")
    unavailable_claims = dotted_get(data, "resource_proof.unavailable_claims")
    if proof_passed is True and proof_executed is not True:
        errors.append("resource_proof.passed cannot be true unless resource_proof.executed is true")
    if proof_executed is True:
        if not nonempty_string(proof_target):
            errors.append("executed resource proof must record resource_proof.target_version_or_commit")
        if not nonempty_string(proof_environment):
            errors.append("executed resource proof must record resource_proof.environment")
        if not nonempty_string(proof_result):
            errors.append("executed resource proof must record resource_proof.result")
    if proof_executed is True and nonempty_string(proof_target) and nonempty_string(version):
        if proof_target.strip() != version.strip():
            errors.append("executed resource proof target must exactly match verification.version_or_commit")
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

    reconciliation_status = dotted_get(data, "reconciliation.status")
    reconciliation_checked = dotted_get(data, "reconciliation.checked_at")
    installed_identity = dotted_get(data, "reconciliation.installed_identity")
    installed_version = dotted_get(data, "reconciliation.installed_version_or_commit")
    detection_method = dotted_get(data, "reconciliation.detection_method")
    parent_sources = dotted_get(data, "reconciliation.parent_state_sources")
    reconciliation_result = dotted_get(data, "reconciliation.result")
    if isinstance(reconciliation_status, str) and reconciliation_status not in ALLOWED_RECONCILIATION:
        errors.append(
            "reconciliation.status must be matched, mismatched, blocked, unknown, or not-applicable"
        )
    if isinstance(reconciliation_checked, str) and reconciliation_checked.strip():
        errors.extend(validate_date(reconciliation_checked.strip(), field="reconciliation.checked_at"))
    if reconciliation_status in {"matched", "mismatched", "blocked", "not-applicable"}:
        if not nonempty_string(reconciliation_checked):
            errors.append(f"reconciliation.status {reconciliation_status!r} requires reconciliation.checked_at")
        if not nonempty_string(detection_method):
            errors.append(f"reconciliation.status {reconciliation_status!r} requires reconciliation.detection_method")
        if not nonempty_string(reconciliation_result):
            errors.append(f"reconciliation.status {reconciliation_status!r} requires reconciliation.result")
    if reconciliation_status == "matched":
        if not nonempty_string(installed_identity):
            errors.append("matched reconciliation requires reconciliation.installed_identity")
        if not nonempty_string(installed_version):
            errors.append("matched reconciliation requires reconciliation.installed_version_or_commit")
        if not isinstance(parent_sources, list) or not parent_sources:
            errors.append("matched reconciliation requires reconciliation.parent_state_sources")
    if reconciliation_status == "mismatched" and not (
        nonempty_string(installed_identity) or nonempty_string(installed_version)
    ):
        errors.append("mismatched reconciliation must record an observed installed identity or version/state")
    if reconciliation_status == "blocked" and not nonempty_string(data.get("blocked_use_or_version")):
        errors.append("blocked reconciliation requires blocked_use_or_version")

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

    catalog_status = dotted_get(data, "skill_validation.catalog_routing_status")
    catalog_fingerprint = dotted_get(data, "skill_validation.catalog_fingerprint")
    catalog_environment = dotted_get(data, "skill_validation.catalog_environment")
    catalog_result = dotted_get(data, "skill_validation.catalog_result")
    if isinstance(catalog_status, str) and catalog_status not in ALLOWED_CATALOG_ROUTING:
        errors.append(
            "skill_validation.catalog_routing_status must be not-applicable, unverified, verified, unavailable, or failed"
        )
    if nonempty_string(catalog_fingerprint) and not FINGERPRINT_RE.fullmatch(catalog_fingerprint.strip()):
        errors.append("skill_validation.catalog_fingerprint must use sha256:<64 lowercase hex characters>")
    if catalog_status in {"verified", "unavailable", "failed"}:
        if not nonempty_string(catalog_fingerprint):
            errors.append(f"catalog routing status {catalog_status!r} requires skill_validation.catalog_fingerprint")
        if not nonempty_string(catalog_environment):
            errors.append(f"catalog routing status {catalog_status!r} requires skill_validation.catalog_environment")
        if not nonempty_string(catalog_result):
            errors.append(f"catalog routing status {catalog_status!r} requires skill_validation.catalog_result")

    host_adoptions = data.get("host_adoptions")
    if not isinstance(host_adoptions, list):
        errors.append("host_adoptions must be a list")
        host_adoptions = []
    seen_host_targets: set[tuple[str, str, str]] = set()
    for index, adoption in enumerate(host_adoptions):
        prefix = f"host_adoptions[{index}]"
        if not isinstance(adoption, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        unknown_host_fields = sorted(set(adoption) - HOST_FIELDS)
        missing_host_fields = sorted(HOST_FIELDS - set(adoption))
        if unknown_host_fields:
            errors.append(f"{prefix} has unknown field(s): {', '.join(unknown_host_fields)}")
        if missing_host_fields:
            errors.append(f"{prefix} is missing field(s): {', '.join(missing_host_fields)}")
        for field in ("host", "scope", "location", "status", "checked_at", "result"):
            if not nonempty_string(adoption.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        scope = adoption.get("scope")
        host_status = adoption.get("status")
        if isinstance(scope, str) and scope not in ALLOWED_HOST_SCOPES:
            errors.append(f"{prefix}.scope must be repo, user, admin, plugin, or other")
        if isinstance(host_status, str) and host_status not in ALLOWED_HOST_STATUSES:
            errors.append(
                f"{prefix}.status must be installed, operational, blocked, disabled, removed, unavailable, or failed"
            )
        checked_at = adoption.get("checked_at")
        if isinstance(checked_at, str) and checked_at.strip():
            errors.extend(validate_date(checked_at.strip(), field=f"{prefix}.checked_at"))
        target = tuple(str(adoption.get(field, "")).strip().lower() for field in ("host", "scope", "location"))
        if target in seen_host_targets:
            errors.append(f"duplicate host adoption target at {prefix}")
        seen_host_targets.add(target)

        evidence = adoption.get("evidence")
        if not isinstance(evidence, dict):
            errors.append(f"{prefix}.evidence must be a mapping")
            continue
        evidence_unknown = sorted(set(evidence) - HOST_EVIDENCE_FIELDS)
        evidence_missing = sorted(HOST_EVIDENCE_FIELDS - set(evidence))
        if evidence_unknown:
            errors.append(f"{prefix}.evidence has unknown field(s): {', '.join(evidence_unknown)}")
        if evidence_missing:
            errors.append(f"{prefix}.evidence is missing field(s): {', '.join(evidence_missing)}")
        installed = evidence.get("installed")
        registered = evidence.get("registered")
        discoverable = evidence.get("discoverable")
        enabled = evidence.get("enabled")
        activation = evidence.get("explicit_activation")
        if installed not in ALLOWED_PRESENCE:
            errors.append(f"{prefix}.evidence.installed has an invalid state")
        if registered not in ALLOWED_PRESENCE:
            errors.append(f"{prefix}.evidence.registered has an invalid state")
        if discoverable not in ALLOWED_DISCOVERY:
            errors.append(f"{prefix}.evidence.discoverable has an invalid state")
        if enabled not in ALLOWED_ENABLED:
            errors.append(f"{prefix}.evidence.enabled has an invalid state")
        if activation not in ALLOWED_ACTIVATION:
            errors.append(f"{prefix}.evidence.explicit_activation has an invalid state")

        if host_status == "operational":
            if installed not in {"present", "not-applicable"}:
                errors.append(f"{prefix} operational requires installed present or not-applicable")
            if registered not in {"present", "not-applicable"}:
                errors.append(f"{prefix} operational requires registered present or not-applicable")
            if discoverable != "yes":
                errors.append(f"{prefix} operational requires discoverable: yes")
            if enabled not in {"yes", "not-applicable"}:
                errors.append(f"{prefix} operational requires enabled yes or not-applicable")
            if activation != "passed":
                errors.append(f"{prefix} operational requires explicit_activation: passed")
        elif host_status == "installed" and installed != "present":
            errors.append(f"{prefix} installed status requires evidence.installed: present")
        elif host_status == "blocked" and installed not in {"present", "not-applicable"}:
            errors.append(f"{prefix} blocked status requires installed present or not-applicable")
        elif host_status == "disabled" and enabled != "no":
            errors.append(f"{prefix} disabled status requires evidence.enabled: no")
        elif host_status == "removed" and installed != "absent":
            errors.append(f"{prefix} removed status requires evidence.installed: absent")
        elif host_status == "unavailable" and not (
            "unknown" in {installed, registered, discoverable, enabled} or activation == "unavailable"
        ):
            errors.append(f"{prefix} unavailable status requires unknown or unavailable evidence")
        elif host_status == "failed" and not (
            activation == "failed" or installed == "absent" or registered == "absent" or discoverable == "no"
        ):
            errors.append(f"{prefix} failed status requires a failed/negative evidence facet")

    generated_skill = data.get("generated_skill")
    if any(value is True for value in (structural, independent_executed, independent_passed)) and not nonempty_string(generated_skill):
        errors.append("skill validation evidence requires generated_skill to identify the generated skill")
    if not nonempty_string(generated_skill):
        if host_adoptions:
            errors.append("host_adoptions require generated_skill to identify the adopted generated child")
        if catalog_status in {"verified", "unavailable", "failed"} or any(
            nonempty_string(value) for value in (catalog_fingerprint, catalog_environment, catalog_result)
        ):
            errors.append("catalog routing evidence requires generated_skill to identify the generated child")

    if trust_basis == "verified-acquisition":
        # Resource-side promotion is independent of the optional generated child.
        # Generic verification rules above already require dated immutable source
        # state, executed/passing resource proof, and no unavailable claims when
        # verification.status is verified.
        if status != "verified":
            errors.append("verified-acquisition requires verification.status: verified")

    if trust_basis == "curated":
        if not nonempty_string(slug):
            errors.append("curated records must carry the curated slug")
        if not nonempty_string(canonical):
            errors.append("curated records must carry canonical_url so trust cannot drift to a same-named resource")
        if status == "unverified":
            notes.append("curated + trusted + unverified is valid; curation establishes trust, not runtime verification")

    if status == "failed":
        if trust_level == "trusted" and not nonempty_string(data.get("blocked_use_or_version")):
            errors.append("failed trusted records must identify blocked_use_or_version without revoking policy trust")
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

