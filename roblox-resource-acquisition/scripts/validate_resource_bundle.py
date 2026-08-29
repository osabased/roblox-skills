#!/usr/bin/env python3
"""Validate consistency between a resource record and its generated child skill.

The standalone validators remain authoritative for each artifact. This coupled
validator adds only relationship checks so a valid record cannot accidentally
be paired with a valid child for a different resource/version/state.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_resource_record import load_record, nonempty_string, validate_record
from validate_skill import (
    NO_PACKAGE_IDENTITY_RE,
    extract_labeled_value,
    parse_frontmatter,
    parse_http_url,
    parse_sections,
    url_identity,
    validate_skill,
)


def _child_provenance(root: Path) -> tuple[dict[str, Any], dict[str, str | None]]:
    text = (root / "SKILL.md").read_text(encoding="utf-8-sig")
    metadata, body = parse_frontmatter(text)
    sections, _counts = parse_sections(body)
    provenance = sections.get("Provenance", "")
    version = extract_labeled_value(provenance, "Source version/release/commit")
    if version is None:
        version = extract_labeled_value(provenance, "Validated version/release/commit")
    values = {
        "slug": extract_labeled_value(provenance, "Resource slug"),
        "package_id": extract_labeled_value(provenance, "Package identity"),
        "devforum_url": extract_labeled_value(provenance, "DevForum"),
        "canonical_url": extract_labeled_value(provenance, "Canonical source/docs"),
        "version": version,
        "verification": extract_labeled_value(provenance, "Resource verification"),
    }
    return metadata, values


def _concrete_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = parse_http_url(value.strip())
    return parsed[0] if parsed else None


def _same_url(left: str, right: str) -> bool:
    try:
        return url_identity(left) == url_identity(right)
    except ValueError:
        return left.strip() == right.strip()


def validate_bundle(
    record_path: Path,
    record: dict[str, Any],
    skill_root: Path,
) -> tuple[list[str], list[str]]:
    """Return relationship errors/notes after validating both artifacts."""
    errors: list[str] = []
    notes: list[str] = []

    record_errors, record_notes = validate_record(record_path, record)
    skill_errors, skill_warnings = validate_skill(skill_root)
    errors.extend(f"resource record: {message}" for message in record_errors)
    errors.extend(f"generated skill: {message}" for message in skill_errors)
    notes.extend(f"resource record: {message}" for message in record_notes)
    notes.extend(f"generated skill warning: {message}" for message in skill_warnings)
    if record_errors or skill_errors:
        return errors, notes

    metadata, child = _child_provenance(skill_root)
    child_name = metadata.get("name")
    record_skill = record.get("generated_skill")
    if not isinstance(child_name, str):
        errors.append("generated skill frontmatter name is unavailable for bundle matching")
    elif not nonempty_string(record_skill) or record_skill.strip() != child_name.strip():
        errors.append("generated_skill must exactly match the child frontmatter name")

    skill_validation = record.get("skill_validation")
    if not isinstance(skill_validation, dict) or skill_validation.get("structural_passed") is not True:
        errors.append(
            "bundle finalization requires skill_validation.structural_passed: true after the current child passes validate_skill.py"
        )

    record_slug = record.get("slug")
    child_slug = child.get("slug")
    if not nonempty_string(record_slug) or not child_slug or record_slug.strip() != child_slug.strip():
        errors.append("resource record slug must exactly match child Provenance Resource slug")

    child_canonical = _concrete_url(child.get("canonical_url"))
    child_devforum = _concrete_url(child.get("devforum_url"))
    effective_child_canonical = child_canonical or child_devforum
    record_canonical = record.get("canonical_url")
    if effective_child_canonical:
        if not nonempty_string(record_canonical):
            errors.append("resource record canonical_url must carry the canonical URL used by the child provenance")
        elif not _same_url(record_canonical.strip(), effective_child_canonical):
            errors.append("resource record canonical_url must match the child canonical provenance URL")

    record_devforum = record.get("devforum_url")
    if child_devforum:
        if not nonempty_string(record_devforum):
            errors.append("resource record devforum_url must match the concrete DevForum provenance recorded by the child")
        elif not _same_url(record_devforum.strip(), child_devforum):
            errors.append("resource record devforum_url must match the child DevForum provenance URL")
    elif nonempty_string(record_devforum):
        errors.append("resource record devforum_url is populated but the child provenance explicitly has no DevForum URL")

    record_package = record.get("package_id")
    child_package = child.get("package_id")
    if child_package and NO_PACKAGE_IDENTITY_RE.fullmatch(child_package.strip()):
        if nonempty_string(record_package):
            errors.append("resource record package_id must be empty when child provenance states no package identity exists")
    elif child_package:
        if not nonempty_string(record_package) or record_package.strip() != child_package.strip():
            errors.append("resource record package_id must exactly match child Provenance Package identity")

    verification = record.get("verification")
    record_version = verification.get("version_or_commit") if isinstance(verification, dict) else None
    child_version = child.get("version")
    if not nonempty_string(record_version) or not child_version or record_version.strip() != child_version.strip():
        errors.append("resource record verification.version_or_commit must exactly match the child reviewed source state")

    record_verification = verification.get("status") if isinstance(verification, dict) else None
    child_verification = child.get("verification")
    if (
        not isinstance(record_verification, str)
        or not child_verification
        or record_verification.strip().lower() != child_verification.strip().lower()
    ):
        errors.append("resource verification status must match between the record and child Provenance")

    return errors, notes


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate consistency between a portable resource record and its generated child skill."
    )
    parser.add_argument("resource_record", type=Path, help="resource-record YAML file")
    parser.add_argument("generated_skill_directory", type=Path, help="directory containing child SKILL.md")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    record_path = args.resource_record.resolve()
    skill_root = args.generated_skill_directory.resolve()
    if not record_path.is_file() or record_path.suffix.lower() not in {".yaml", ".yml"}:
        print(f"FAIL\n- expected an existing .yaml/.yml resource record: {record_path}")
        return 1
    if not (skill_root / "SKILL.md").is_file():
        print(f"FAIL\n- expected generated skill directory containing SKILL.md: {skill_root}")
        return 1
    try:
        record = load_record(record_path)
        errors, notes = validate_bundle(record_path, record, skill_root)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"FAIL\n- {exc}")
        return 1
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        for note in notes:
            print(f"NOTE: {note}")
        return 1
    print("PASS: resource-record/generated-skill bundle consistency checks passed")
    for note in notes:
        print(f"NOTE: {note}")
    print("NOTE: bundle consistency does not establish independent behavioral validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
