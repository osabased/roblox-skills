from alignment_harness import (
    FINAL_ACCEPTANCE_CRITERIA,
    TraceabilityCheck,
    assess_traceability,
)


def passing_checks() -> tuple[TraceabilityCheck, ...]:
    return tuple(
        TraceabilityCheck(
            id=f"check-{criterion_id.lower()}",
            criterion_id=criterion_id,
            kind="scenario",
            target=f"tests/{criterion_id.lower()}.py",
            oracle=f"{criterion_id} behavior matches its acceptance oracle",
            passed=True,
        )
        for criterion_id in FINAL_ACCEPTANCE_CRITERIA
    )


def replace_check(
    checks: tuple[TraceabilityCheck, ...],
    criterion_id: str,
    replacement: TraceabilityCheck,
) -> tuple[TraceabilityCheck, ...]:
    return tuple(
        replacement if check.criterion_id == criterion_id else check for check in checks
    )


def test_traceability_requires_a_check_and_explicit_oracle_per_final_criterion() -> None:
    checks = replace_check(
        passing_checks(),
        "AC-079",
        TraceabilityCheck(
            id="suite-integrated",
            criterion_id="AC-079",
            kind="scenario",
            target="tests/test_integrated_scenarios.py",
            oracle="",
            passed=True,
        ),
    )

    result = assess_traceability(checks)

    assert result.complete is False
    assert result.unmapped_criteria == ()
    assert result.checks_without_oracles == ("suite-integrated",)


def test_traceability_reports_unmapped_final_acceptance_criteria() -> None:
    checks = tuple(
        check for check in passing_checks() if check.criterion_id != "AC-029"
    )

    result = assess_traceability(checks)

    assert result.complete is False
    assert result.unmapped_criteria == ("AC-029",)


def test_traceability_requires_every_mapped_check_to_pass() -> None:
    checks = replace_check(
        passing_checks(),
        "AC-001",
        TraceabilityCheck(
            id="host-contract",
            criterion_id="AC-001",
            kind="structural",
            target="references/host-capabilities.json",
            oracle="every host capability has a mechanism or constrained fallback",
            passed=False,
        ),
    )

    result = assess_traceability(checks)

    assert result.complete is False
    assert result.failed_checks == ("host-contract",)


def test_traceability_rejects_nonobservable_or_untargeted_checks() -> None:
    checks = replace_check(
        passing_checks(),
        "AC-001",
        TraceabilityCheck(
            id="host-contract",
            criterion_id="AC-001",
            kind="note",
            target="",
            oracle="the prose sounds complete",
            passed=True,
        ),
    )

    result = assess_traceability(checks)

    assert result.complete is False
    assert result.invalid_checks == ("host-contract",)


def test_traceability_rejects_unknown_blank_and_duplicate_identifiers() -> None:
    checks = passing_checks() + (
        TraceabilityCheck(
            id="extra-check",
            criterion_id="not-a-final-criterion",
            kind="scenario",
            target="tests/test_extra.py",
            oracle="an unrelated behavior passes",
            passed=True,
        ),
        TraceabilityCheck(
            id="",
            criterion_id="AC-001",
            kind="scenario",
            target="tests/test_capability_contract.py",
            oracle="the contract is ready",
            passed=True,
        ),
        TraceabilityCheck(
            id="check-ac-002",
            criterion_id="AC-002",
            kind="scenario",
            target="tests/test_duplicate.py",
            oracle="a duplicate check identifier cannot be stable",
            passed=True,
        ),
    )

    result = assess_traceability(checks)

    assert result.complete is False
    assert result.invalid_checks == (
        "check-ac-002",
        "extra-check",
        "<blank-check-id>",
    )


def test_traceability_cannot_claim_complete_for_a_caller_supplied_subset() -> None:
    result = assess_traceability((passing_checks()[0],))

    assert result.complete is False
    assert len(result.unmapped_criteria) == 78


def test_traceability_completes_only_when_all_canonical_checks_pass() -> None:
    result = assess_traceability(passing_checks())

    assert result.complete is True
    assert result.unmapped_criteria == ()
    assert result.failed_checks == ()
