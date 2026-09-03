#!/usr/bin/env python3
"""Validate external curated Roblox resource registry entries.

This is a structural/identity validator only. Passing does not establish that a
resource is good, safe, maintained, compatible, or runtime-correct.

PyYAML is required (see requirements.txt). A single parser everywhere keeps
trust verdicts identical across environments; the script exits with code 2 and
an install hint when PyYAML is missing.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (
    DEVFORUM_TOPIC_PATH_RE,
    SLUG_RE,
    collect_files,
    load_yaml,
    normalize_empty_values,
    validate_date,
    validate_https_url,
    validated_url_host,
)

ALLOWED_FIELDS = {
    "schema_version",
    "slug",
    "name",
    "capabilities",
    "use_when",
    "avoid_when",
    "canonical_url",
    "package_id",
    "install_hint",
    "devforum_url",
    "curation_reason",
    "last_reviewed",
    "notes",
}
REQUIRED_FIELDS = {
    "schema_version",
    "slug",
    "name",
    "capabilities",
    "use_when",
    "canonical_url",
    "curation_reason",
}
LIST_FIELDS = {"capabilities", "use_when", "avoid_when", "notes"}
STRING_FIELDS = {
    "slug",
    "name",
    "canonical_url",
    "package_id",
    "install_hint",
    "devforum_url",
    "curation_reason",
    "last_reviewed",
}


def load_entry(path: Path) -> dict[str, Any]:
    loaded = load_yaml(path.read_text(encoding="utf-8"))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError("top-level YAML value must be a mapping")
    normalize_empty_values(loaded, LIST_FIELDS)
    # PyYAML resolves an unquoted ISO date to datetime.date. Accept that
    # natural YAML spelling and normalize it to the schema's string form.
    if isinstance(loaded.get("last_reviewed"), date):
        loaded["last_reviewed"] = loaded["last_reviewed"].isoformat()
    return loaded


def validate_entry(path: Path, data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []

    unknown = sorted(set(data) - ALLOWED_FIELDS)
    if unknown:
        errors.append("unknown field(s): " + ", ".join(unknown))
    missing = sorted(field for field in REQUIRED_FIELDS if field not in data)
    if missing:
        errors.append("missing required field(s): " + ", ".join(missing))

    if data.get("schema_version") != 1:
        errors.append("schema_version must be integer 1")

    for field in STRING_FIELDS:
        if field in data and not isinstance(data[field], str):
            errors.append(f"{field} must be a string")

    for field in LIST_FIELDS:
        value = data.get(field, [])
        if not isinstance(value, list):
            errors.append(f"{field} must be a list")
            continue
        bad = [item for item in value if not isinstance(item, str) or not item.strip()]
        if bad:
            errors.append(f"{field} must contain only non-empty strings")

    slug = data.get("slug")
    if isinstance(slug, str):
        if not slug:
            errors.append("slug must not be empty")
        elif not SLUG_RE.fullmatch(slug):
            errors.append("slug must be lowercase kebab-case (a-z, 0-9, hyphen)")

    name = data.get("name")
    if isinstance(name, str) and not name.strip():
        errors.append("name must not be empty")

    capabilities = data.get("capabilities")
    if isinstance(capabilities, list) and not capabilities:
        errors.append("capabilities must contain at least one item")

    use_when = data.get("use_when")
    if isinstance(use_when, list) and not use_when:
        errors.append("use_when must contain at least one item")

    reason = data.get("curation_reason")
    if isinstance(reason, str) and not reason.strip():
        errors.append("curation_reason must not be empty")

    canonical = data.get("canonical_url")
    if isinstance(canonical, str):
        if not canonical.strip():
            errors.append("canonical_url must not be empty")
        else:
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

    reviewed = data.get("last_reviewed")
    if isinstance(reviewed, str) and reviewed.strip():
        errors.extend(
            validate_date(
                reviewed,
                field="last_reviewed",
                placeholder_msg="last_reviewed still contains the template placeholder YYYY-MM-DD; set a real date or empty string",
                format_msg="last_reviewed must be YYYY-MM-DD or empty",
            )
        )

    package_id = data.get("package_id")
    if isinstance(package_id, str) and ("\n" in package_id or "\r" in package_id):
        errors.append("package_id must be a single-line exact identifier")

    if path.stem != slug and isinstance(slug, str) and slug:
        notes.append(f"filename {path.name!r} differs from slug {slug!r}; slug remains authoritative")

    return errors, notes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate curated Roblox resource registry structure and canonical identity."
    )
    parser.add_argument(
        "registry",
        nargs="+",
        type=Path,
        help="Registry directory or entry file. For multiple registries, pass highest precedence first.",
    )
    args = parser.parse_args()

    overall_errors = 0
    all_entries: list[tuple[int, Path, dict[str, Any]]] = []

    for registry_index, registry_path in enumerate(args.registry):
        try:
            files = collect_files(registry_path)
        except ValueError as exc:
            print(f"ERROR: {exc}")
            overall_errors += 1
            continue

        if not files:
            print(f"NOTE: {registry_path}: no .yaml/.yml entries found")
            continue

        results: list[dict[str, Any]] = []
        slug_to_results: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for file_path in files:
            try:
                data = load_entry(file_path)
            except (OSError, UnicodeError, ValueError) as exc:
                results.append({"path": file_path, "data": {}, "errors": [str(exc)], "notes": []})
                continue

            errors, notes = validate_entry(file_path, data)
            result = {"path": file_path, "data": data, "errors": errors, "notes": notes}
            results.append(result)
            slug = data.get("slug")
            if isinstance(slug, str) and slug:
                slug_to_results[slug].append(result)

        # Same-registry duplicates are ambiguous. Mark every duplicate entry as
        # invalid so no arbitrary file appears to have earned trust.
        for slug, dupes in slug_to_results.items():
            if len(dupes) > 1:
                paths = ", ".join(str(item["path"]) for item in dupes)
                for item in dupes:
                    item["errors"].append(
                        f"duplicate slug {slug!r} in same registry; conflicting entries: {paths}"
                    )

        for result in results:
            file_path = result["path"]
            errors = result["errors"]
            notes = result["notes"]
            if errors:
                for error in errors:
                    print(f"ERROR: {file_path}: {error}")
                overall_errors += len(errors)
            else:
                print(f"PASS: {file_path}")
                all_entries.append((registry_index, file_path, result["data"]))
            for note in notes:
                print(f"NOTE: {file_path}: {note}")

    by_slug: dict[str, list[tuple[int, Path]]] = defaultdict(list)
    for registry_index, path, data in all_entries:
        slug = data.get("slug")
        if isinstance(slug, str) and slug:
            by_slug[slug].append((registry_index, path))

    for slug, occurrences in sorted(by_slug.items()):
        registry_ids = {idx for idx, _ in occurrences}
        if len(registry_ids) > 1:
            winner = min(occurrences, key=lambda pair: pair[0])
            overridden = [str(path) for idx, path in occurrences if (idx, path) != winner]
            print(
                f"NOTE: slug {slug!r} appears across registries; highest-precedence entry is {winner[1]}; "
                f"overrides: {', '.join(overridden)}"
            )

    if overall_errors:
        print(f"FAIL: curated registry validation found {overall_errors} error(s)")
        return 1

    print(
        "PASS: curated registry structural/identity checks passed\n"
        "NOTE: this does not establish quality, safety, maintenance, compatibility, or runtime correctness"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
