"""Canonical final-acceptance traceability assessment."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


FINAL_ACCEPTANCE_CRITERIA = tuple(f"AC-{index:03d}" for index in range(1, 80))


@dataclass(frozen=True)
class TraceabilityCheck:
    id: str
    criterion_id: str
    kind: str
    target: str
    oracle: str
    passed: bool


@dataclass(frozen=True)
class TraceabilityAssessment:
    complete: bool
    unmapped_criteria: tuple[str, ...]
    checks_without_oracles: tuple[str, ...]
    invalid_checks: tuple[str, ...]
    failed_checks: tuple[str, ...]


def assess_traceability(
    checks: tuple[TraceabilityCheck, ...],
) -> TraceabilityAssessment:
    """Require a valid, passing check for every canonical final criterion."""
    valid_kinds = {"scenario", "structural"}
    check_counts = Counter(check.id for check in checks)
    invalid_checks: list[str] = []
    for check in checks:
        label = check.id if check.id.strip() else "<blank-check-id>"
        invalid = (
            not check.id.strip()
            or check_counts[check.id] > 1
            or check.criterion_id not in FINAL_ACCEPTANCE_CRITERIA
            or check.kind not in valid_kinds
            or not check.target.strip()
        )
        if invalid and label not in invalid_checks:
            invalid_checks.append(label)

    mapped = {
        check.criterion_id
        for check in checks
        if (check.id if check.id.strip() else "<blank-check-id>") not in invalid_checks
    }
    unmapped = tuple(
        criterion_id
        for criterion_id in FINAL_ACCEPTANCE_CRITERIA
        if criterion_id not in mapped
    )
    missing_oracles = tuple(check.id for check in checks if not check.oracle.strip())
    failed_checks = tuple(check.id for check in checks if check.passed is not True)
    return TraceabilityAssessment(
        complete=(
            not unmapped
            and not missing_oracles
            and not invalid_checks
            and not failed_checks
        ),
        unmapped_criteria=unmapped,
        checks_without_oracles=missing_oracles,
        invalid_checks=tuple(invalid_checks),
        failed_checks=failed_checks,
    )
