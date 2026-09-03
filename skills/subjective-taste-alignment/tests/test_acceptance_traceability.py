"""Executable completeness checks for the acceptance traceability document.

The traceability document claims that every canonical criterion maps to at
least one passing check whose target exists. These tests make that claim
observable: they parse both reference documents, compare the mapped criteria
against the canonical catalog, and verify every cited test target resolves to
a real file and test function.
"""

from __future__ import annotations

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TRACEABILITY = SKILL_DIR / "references" / "acceptance-traceability.md"
CATALOG = SKILL_DIR / "references" / "final-acceptance-criteria.md"

_ROW = re.compile(r"^\|\s*`(AC-\d+)`\s*\|", re.MULTILINE)
_CATALOG_ID = re.compile(r"^- `(AC-\d+)` —", re.MULTILINE)
_TEST_REF = re.compile(
    r"`(tests/[A-Za-z0-9_]+\.py)(?:::([A-Za-z0-9_]+))?`"
)


def _mapped_criteria() -> set[str]:
    return set(_ROW.findall(TRACEABILITY.read_text(encoding="utf-8")))


def _canonical_criteria() -> set[str]:
    return set(_CATALOG_ID.findall(CATALOG.read_text(encoding="utf-8")))


def test_every_canonical_criterion_is_mapped_exactly() -> None:
    mapped = _mapped_criteria()
    canonical = _canonical_criteria()
    assert canonical, "catalog parse found no criteria"
    missing = sorted(canonical - mapped)
    unknown = sorted(mapped - canonical)
    assert missing == [], f"criteria without a mapped check: {missing}"
    assert unknown == [], f"mappings outside the canonical catalog: {unknown}"


def test_every_mapped_scenario_target_exists_and_names_a_real_check() -> None:
    document = TRACEABILITY.read_text(encoding="utf-8")
    referenced: list[tuple[str, str | None]] = [
        (path, test or None) for path, test in _TEST_REF.findall(document)
    ]
    assert referenced, "traceability document cites no executable targets"

    problems: list[str] = []
    for path, test in referenced:
        file_path = SKILL_DIR / path
        if not file_path.exists():
            problems.append(f"{path}: file does not exist")
            continue
        if test is None:
            continue
        source = file_path.read_text(encoding="utf-8")
        if f"def {test}(" not in source:
            problems.append(f"{path}::{test}: no such test function")
    assert problems == [], "\n".join(problems)
