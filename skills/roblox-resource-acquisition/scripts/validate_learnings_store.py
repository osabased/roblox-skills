#!/usr/bin/env python3
"""Validate external Roblox learnings-store entries.

This is a structural validator only. Passing does not establish that any
recorded observation is true or still current, and it never grants trust or
verification status to anything.

PyYAML is required (see requirements.txt). A single parser everywhere keeps
validation verdicts identical across environments; the script exits with code 2
and an install hint when PyYAML is missing.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (
    SLUG_RE,
    collect_files,
    load_yaml,
    normalize_empty_values,
    validate_date,
    validate_https_url,
)

ALLOWED_FIELDS = {
    "schema_version",
    "kind",
    "scope",
    "slug",
    "canonical_url",
    "package_id",
    "observed",
    "statement",
    "evidence",
    "version_context",
    "reconsider_when",
    "task_context",
    "related_entry",
}
REQUIRED_FIELDS = {
    "schema_version",
    "kind",
    "scope",
    "observed",
    "statement",
    "evidence",
}
STRING_FIELDS = ALLOWED_FIELDS - {"schema_version"}

# A learning must stay an observation. These field names indicate an attempt
# to smuggle trust/verification state into the store, which only the curated
# registry (trust) and executed proof (verification) are allowed to carry.
FORBIDDEN_STATE_FIELDS = {
    "trust",
    "trust_level",
    "trust_basis",
    "verification",
    "verification_status",
    "verified",
    "status",
    "resource_proof",
    "skill_validation",
}

KINDS = {
    "integration-gotcha",
    "failed-query",
    "version-drift",
    "environment-blocker",
    "rejection",
    "repair-outcome",
}
SCOPES = {"resource", "search", "environment"}

# Kind/scope compatibility. Resource-bound kinds must carry canonical
# identity; query observations must not, so learnings cannot silently attach
# to a resource by accident.
KIND_SCOPE_RULES: dict[str, set[str]] = {
    "integration-gotcha": {"resource"},
    "version-drift": {"resource"},
    "rejection": {"resource"},
    "repair-outcome": {"resource"},
    "failed-query": {"search"},
    "environment-blocker": {"resource", "environment"},
}

# Fields that must be non-empty for specific kinds. A rejection without a
# reopen condition becomes a permanent silent blacklist, which the store's
# contract forbids.
KIND_REQUIRED_FIELDS: dict[str, set[str]] = {
    "version-drift": {"version_context"},
    "rejection": {"version_context", "reconsider_when"},
}


def load_entry(path: Path) -> dict[str, Any]:
    loaded = load_yaml(path.read_text(encoding="utf-8"))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError("top-level YAML value must be a mapping")
    normalize_empty_values(loaded)
    # PyYAML resolves an unquoted ISO date to datetime.date. Accept that
    # natural YAML spelling and normalize it to the schema's string form.
    if isinstance(loaded.get("observed"), date):
        loaded["observed"] = loaded["observed"].isoformat()
    return loaded


def nonempty(data: dict[str, Any], field: str) -> bool:
    value = data.get(field)
    return isinstance(value, str) and bool(value.strip())


# Advisory only. Learnings are observations, and the consumption contract in
# references/learnings-store.md already requires directives inside a statement
# to be disregarded; this pattern merely surfaces entries that read as
# instructions so a human notices the side-channel attempt or rephrases the
# fact. Warnings never fail validation and never affect trust or verification.
# Anchored to statement-initial imperatives plus explicit policy-override
# phrases so factual uses of always/never ("Fire never clones payloads") do
# not warn.
DIRECTIVE_STATEMENT_RE = re.compile(
    r"(?:^\s*(?:always|never|ignore|skip|do not|don't|disable|bypass)\b"
    r"|\b(?:in|for)\s+(?:all\s+)?future\s+runs\b"
    r"|\bfrom\s+now\s+on\b"
    r"|\bignore\s+the\s+(?:repair\s+)?budget\b"
    r"|\b(?:skip|bypass|disable)\s+(?:runtime\s+|resource\s+)?verification\b)",
    re.I,
)


def entry_warnings(data: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    statement = data.get("statement")
    if isinstance(statement, str) and statement.strip():
        if DIRECTIVE_STATEMENT_RE.search(statement.strip()):
            warnings.append(
                "statement reads as an imperative directive; learnings are "
                "observations, so record the fact (what happened/holds), not an "
                "instruction (what to always/never do) — consumers must "
                "disregard directives per references/learnings-store.md"
            )
    return warnings


def validate_entry(path: Path, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    forbidden = sorted(set(data) & FORBIDDEN_STATE_FIELDS)
    if forbidden:
        errors.append(
            "learning entries must not carry trust or verification state; "
            "remove field(s): " + ", ".join(forbidden)
        )
    unknown = sorted(set(data) - ALLOWED_FIELDS - FORBIDDEN_STATE_FIELDS)
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

    kind = data.get("kind")
    if isinstance(kind, str) and kind:
        if kind not in KINDS:
            errors.append("kind must be one of: " + ", ".join(sorted(KINDS)))
    elif isinstance(kind, str):
        errors.append("kind must not be empty")

    scope = data.get("scope")
    if isinstance(scope, str) and scope:
        if scope not in SCOPES:
            errors.append("scope must be one of: " + ", ".join(sorted(SCOPES)))
    elif isinstance(scope, str):
        errors.append("scope must not be empty")

    if isinstance(kind, str) and kind in KIND_SCOPE_RULES and isinstance(scope, str) and scope in SCOPES:
        allowed_scopes = KIND_SCOPE_RULES[kind]
        if scope not in allowed_scopes:
            errors.append(
                f"kind {kind!r} requires scope " + " or ".join(sorted(allowed_scopes))
            )

    slug = data.get("slug")
    canonical = data.get("canonical_url")
    package_id = data.get("package_id")
    if isinstance(scope, str) and scope == "resource":
        if not nonempty(data, "slug"):
            errors.append("resource-scoped entries require a non-empty slug")
        elif isinstance(slug, str) and not SLUG_RE.fullmatch(slug):
            errors.append("slug must be lowercase kebab-case (a-z, 0-9, hyphen)")
        if not nonempty(data, "canonical_url"):
            errors.append("resource-scoped entries require canonical_url; learnings bind to canonical identity, not display names")
        elif isinstance(canonical, str):
            errors.extend(validate_https_url(canonical.strip(), field="canonical_url"))
    elif isinstance(scope, str) and scope in SCOPES:
        for field in ("slug", "canonical_url", "package_id"):
            if nonempty(data, field):
                errors.append(f"{field} must be empty when scope is {scope!r}")

    if isinstance(package_id, str) and ("\n" in package_id or "\r" in package_id):
        errors.append("package_id must be a single-line exact identifier")

    observed = data.get("observed")
    if isinstance(observed, str):
        if not observed.strip():
            errors.append("observed must not be empty")
        else:
            errors.extend(
                validate_date(
                    observed,
                    field="observed",
                    placeholder_msg="observed still contains the template placeholder YYYY-MM-DD; set a real date",
                    format_msg="observed must be YYYY-MM-DD",
                )
            )

    for field in ("statement", "evidence"):
        if field in data and isinstance(data[field], str) and not data[field].strip():
            errors.append(f"{field} must not be empty")

    if isinstance(kind, str) and kind in KIND_REQUIRED_FIELDS:
        for field in sorted(KIND_REQUIRED_FIELDS[kind]):
            if not nonempty(data, field):
                errors.append(f"kind {kind!r} requires non-empty {field}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate learnings-store entry structure. Entries from all supplied "
            "stores merge; order carries no precedence."
        )
    )
    parser.add_argument(
        "store",
        nargs="+",
        type=Path,
        help="Learnings-store directory or entry file.",
    )
    args = parser.parse_args()

    overall_errors = 0
    overall_warnings = 0

    for store_path in args.store:
        try:
            files = collect_files(store_path)
        except ValueError as exc:
            print(f"ERROR: {exc}")
            overall_errors += 1
            continue

        if not files:
            print(f"NOTE: {store_path}: no .yaml/.yml entries found")
            continue

        for file_path in files:
            try:
                data = load_entry(file_path)
            except (OSError, UnicodeError, ValueError) as exc:
                print(f"ERROR: {file_path}: {exc}")
                overall_errors += 1
                continue

            errors = validate_entry(file_path, data)
            warnings = entry_warnings(data)
            if errors:
                for error in errors:
                    print(f"ERROR: {file_path}: {error}")
                overall_errors += len(errors)
            else:
                print(f"PASS: {file_path}")
            for warning in warnings:
                print(f"WARN: {file_path}: {warning}")
            overall_warnings += len(warnings)

    if overall_errors:
        print(f"FAIL: learnings-store validation found {overall_errors} error(s)")
        return 1

    print(
        "PASS: learnings-store structural checks passed\n"
        "NOTE: this does not establish that any observation is true or current, "
        "and it never grants trust or verification"
    )
    if overall_warnings:
        print(
            f"NOTE: {overall_warnings} advisory warning(s) above; warnings never "
            "fail validation and never affect trust or verification"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
