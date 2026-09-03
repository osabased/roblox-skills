import json

from reconciliation import (
    ArtifactComparison,
    ArtifactJudgment,
    ChallengeApprovedArtifact,
    ChallengeOutcome,
    CheckPropagation,
    CommitCorrection,
    ComparisonFidelity,
    CorrectedInput,
    DecisionInputKind,
    DependentRecord,
    DimensionValue,
    ReconcileDependent,
    ReconciliationState,
    StoredTasteDirection,
    TransitionKind,
    WorkStatus,
    OperationIdentityConflictError,
    apply_reconciliation_operation,
    reconciliation_state_from_document,
    reconciliation_state_to_document,
)
from alignment_contract import (
    AlignmentRequest,
    DecisionDirective,
    Provenance,
    resolve_alignment,
)


def _challenge_state() -> ReconciliationState:
    return ReconciliationState(
        dependents=(
            DependentRecord(
                dependent_id="artifact:hero",
                decision_id="decision:hero-palette",
                input_dependencies=("taste:palette",),
            ),
        )
    )


def _taste_target(established: bool = True) -> StoredTasteDirection:
    return StoredTasteDirection(
        dimension="layout.density",
        direction="compact",
        input_id="taste:palette",
        established=established,
    )


def _artifact(**overrides: object) -> ArtifactComparison:
    values: dict[str, object] = {
        "artifact_id": "approved-hero-v2",
        "observed": (DimensionValue("layout.density", "airy"),),
        "judgment": ArtifactJudgment.PREFERRED,
        "fidelity": ComparisonFidelity.HIGH,
        "attributable": True,
        "scope_matches": True,
        "context_matches": True,
        "ownership_matches": True,
    }
    values.update(overrides)
    return ArtifactComparison(**values)  # type: ignore[arg-type]


def _challenge(
    artifact: ArtifactComparison,
    *,
    operation_id: str = "challenge:1",
    target: StoredTasteDirection | None = None,
) -> ChallengeApprovedArtifact:
    return ChallengeApprovedArtifact(
        operation_id=operation_id,
        targets=(target if target is not None else _taste_target(),),
        artifact=artifact,
        basis_revision=f"approved:{artifact.artifact_id}",
    )


def test_approved_artifacts_challenge_taste_only_when_comparison_is_supported() -> None:
    unsupported_variants = (
        (
            {"judgment": ArtifactJudgment.ACCEPTABLE},
            "approval semantics",
        ),
        (
            {"fidelity": ComparisonFidelity.LOW},
            "fidelity",
        ),
        ({"ownership_matches": False}, "owner"),
        ({"scope_matches": False}, "scope"),
        ({"attributable": False}, "attributable"),
    )
    for overrides, expected_reason_part in unsupported_variants:
        initial = _challenge_state()
        transition = apply_reconciliation_operation(
            initial, _challenge(_artifact(**overrides))
        )
        assert transition.challenge is not None
        assert transition.challenge.outcome is ChallengeOutcome.NOT_COMPARABLE
        assert any(
            expected_reason_part in reason
            for reason in transition.challenge.reasons
        ), expected_reason_part
        assert transition.state.work == ()
        assert transition.state.corrections == ()

    unestablished = apply_reconciliation_operation(
        _challenge_state(),
        _challenge(_artifact(), target=_taste_target(established=False)),
    )
    assert unestablished.challenge is not None
    assert unestablished.challenge.outcome is ChallengeOutcome.NOT_COMPARABLE
    assert any(
        "established" in reason for reason in unestablished.challenge.reasons
    )
    assert unestablished.state.corrections == ()


def test_materially_contradicting_artifact_reopens_alignment_as_stale_model() -> None:
    state = _challenge_state()

    reopened = apply_reconciliation_operation(state, _challenge(_artifact()))

    assert reopened.kind is TransitionKind.CHALLENGE_ASSESSED
    assert reopened.challenge is not None
    assert reopened.challenge.outcome is ChallengeOutcome.MODEL_STALE
    assert reopened.affected_dependents == ("artifact:hero",)
    work = reopened.state.work[0]
    assert work.dependent_id == "artifact:hero"
    assert work.status is WorkStatus.PENDING
    assert work.basis_revision == "approved:approved-hero-v2"

    blocked = apply_reconciliation_operation(
        reopened.state,
        CheckPropagation(
            dependent_id="artifact:hero",
            alignment=resolve_alignment(
                AlignmentRequest(decision_id="decision:hero-palette", dimensions=("x",), material=True)
            ),
            current_request=AlignmentRequest(
                decision_id="decision:hero-palette", dimensions=("x",), material=True
            ),
        ),
    )
    assert blocked.propagation is not None
    assert blocked.propagation.permitted is False
    assert any(
        blocker.startswith("reconciliation:")
        for blocker in blocked.propagation.blockers
    )


def test_contradiction_outcomes_distinguish_exceptions_from_context_change() -> None:
    exception_transition = apply_reconciliation_operation(
        _challenge_state(),
        _challenge(_artifact(deliberate_exception=True)),
    )
    assert exception_transition.challenge is not None
    assert (
        exception_transition.challenge.outcome
        is ChallengeOutcome.ARTIFACT_EXCEPTION
    )
    assert exception_transition.state.work == ()
    assert exception_transition.state.corrections == ()

    context_transition = apply_reconciliation_operation(
        _challenge_state(),
        _challenge(_artifact(context_matches=False)),
    )
    assert context_transition.challenge is not None
    assert context_transition.challenge.outcome is ChallengeOutcome.CONTEXT_CHANGED
    assert context_transition.affected_dependents == ("artifact:hero",)
    assert len(context_transition.state.corrections) == 1


def test_matching_or_incomparable_challenges_do_not_reopen_alignment() -> None:
    agreeing = apply_reconciliation_operation(
        _challenge_state(),
        _challenge(
            _artifact(observed=(DimensionValue("layout.density", "compact"),))
        ),
    )
    assert agreeing.challenge is not None
    assert agreeing.challenge.outcome is ChallengeOutcome.NO_CONTRADICTION
    assert agreeing.state == _challenge_state()


def test_challenge_replay_is_idempotent_and_conflicting_reuse_raises() -> None:
    first = apply_reconciliation_operation(
        _challenge_state(), _challenge(_artifact())
    )
    replayed = apply_reconciliation_operation(first.state, _challenge(_artifact()))

    assert replayed.kind is TransitionKind.CHALLENGE_REPLAYED
    assert replayed.challenge is not None
    assert replayed.challenge.outcome is ChallengeOutcome.MODEL_STALE
    assert replayed.state == first.state

    conflicting = _challenge(
        _artifact(observed=(DimensionValue("typography.scale", "dramatic"),)),
        operation_id="challenge:1",
    )
    try:
        apply_reconciliation_operation(first.state, conflicting)
    except OperationIdentityConflictError:
        pass
    else:
        raise AssertionError("challenge id reuse with new content must conflict")


def test_correction_atomically_creates_pending_work_for_exact_dependents() -> None:
    initial = ReconciliationState(
        dependents=(
            DependentRecord(
                dependent_id="artifact:hero",
                decision_id="decision:hero-palette",
                input_dependencies=("taste:palette",),
            ),
            DependentRecord(
                dependent_id="artifact:card",
                decision_id="decision:card-palette",
                input_dependencies=("taste:palette", "intent:card"),
            ),
            DependentRecord(
                dependent_id="artifact:footer",
                decision_id="decision:footer-spacing",
                input_dependencies=("taste:spacing",),
            ),
        )
    )

    transition = apply_reconciliation_operation(
        initial,
        CommitCorrection(
            operation_id="correction:palette-1",
            corrected_inputs=(
                CorrectedInput("taste:palette", DecisionInputKind.TASTE),
            ),
            basis_revision="profile:revision-2",
        ),
    )

    assert initial.work == ()
    assert transition.affected_dependents == (
        "artifact:card",
        "artifact:hero",
    )
    assert tuple(item.dependent_id for item in transition.state.work) == (
        "artifact:card",
        "artifact:hero",
    )
    assert all(item.status is WorkStatus.PENDING for item in transition.state.work)
    assert transition.state.incomplete is True
    assert transition.state.corrections[0].basis_revision == "profile:revision-2"


def test_dependents_reresolve_current_state_and_only_invalid_work_gets_repair() -> None:
    state = apply_reconciliation_operation(
        ReconciliationState(
            dependents=(
                DependentRecord(
                    "artifact:hero",
                    "decision:hero-palette",
                    ("intent:palette",),
                ),
                DependentRecord(
                    "artifact:card",
                    "decision:card-palette",
                    ("intent:palette",),
                ),
                DependentRecord(
                    "artifact:footer",
                    "decision:footer-spacing",
                    ("taste:spacing",),
                ),
            )
        ),
        CommitCorrection(
            "correction:intent-1",
            (CorrectedInput("intent:palette", DecisionInputKind.INTENT),),
            "profile:revision-2",
        ),
    ).state

    def request(decision_id: str, direction: str) -> AlignmentRequest:
        return AlignmentRequest(
            decision_id=decision_id,
            dimensions=("palette",),
            material=True,
            intent=(
                DecisionDirective(
                    dimension="palette",
                    direction=direction,
                    reason="current corrected project intent",
                    provenance=(Provenance("user", "intent:palette"),),
                ),
            ),
            context_revision="profile:revision-2",
            dependencies=("intent:palette",),
        )

    valid = apply_reconciliation_operation(
        state,
        ReconcileDependent(
            dependent_id="artifact:hero",
            current_request=request("decision:hero-palette", "warm"),
            observed_directions=(DimensionValue("palette", "warm"),),
        ),
    )
    invalid = apply_reconciliation_operation(
        valid.state,
        ReconcileDependent(
            dependent_id="artifact:card",
            current_request=request("decision:card-palette", "cool"),
            observed_directions=(DimensionValue("palette", "warm"),),
        ),
    )

    assert valid.kind is TransitionKind.DEPENDENT_UNCHANGED
    assert valid.repair is None
    assert valid.alignment is not None
    assert valid.alignment.dimensions["palette"].direction == "warm"
    assert invalid.kind is TransitionKind.DEPENDENT_CHANGE_REQUIRED
    assert invalid.repair is not None
    assert invalid.repair.changed_directions == (DimensionValue("palette", "cool"),)
    work = {item.dependent_id: item for item in invalid.state.work}
    assert work["artifact:hero"].status is WorkStatus.COMPLETED
    assert work["artifact:card"].status is WorkStatus.UNVERIFIED
    assert "artifact:footer" not in work


def test_resume_preserves_completed_pending_and_unverified_without_duplication() -> None:
    dependents = tuple(
        DependentRecord(
            f"artifact:{name}",
            f"decision:{name}",
            ("taste:palette",),
        )
        for name in ("a", "b", "c")
    )
    state = apply_reconciliation_operation(
        ReconciliationState(dependents=dependents),
        CommitCorrection(
            "correction:1",
            (CorrectedInput("taste:palette", DecisionInputKind.TASTE),),
            "profile:2",
        ),
    ).state

    def request(name: str) -> AlignmentRequest:
        return AlignmentRequest(
            decision_id=f"decision:{name}",
            dimensions=("palette",),
            material=True,
            intent=(
                DecisionDirective(
                    "palette",
                    "cool",
                    "current direction",
                    (Provenance("user", "intent:current"),),
                ),
            ),
            dependencies=("taste:palette",),
            context_revision="profile:2",
        )

    completed_a = apply_reconciliation_operation(
        state,
        ReconcileDependent(
            "artifact:a",
            request("a"),
            (DimensionValue("palette", "cool"),),
        ),
    )
    unverified_b = apply_reconciliation_operation(
        completed_a.state,
        ReconcileDependent(
            "artifact:b",
            request("b"),
            (DimensionValue("palette", "warm"),),
        ),
    )

    replay_a = apply_reconciliation_operation(
        unverified_b.state,
        ReconcileDependent(
            "artifact:a",
            request("a"),
            (DimensionValue("palette", "cool"),),
        ),
    )
    verified_b = apply_reconciliation_operation(
        replay_a.state,
        ReconcileDependent(
            "artifact:b",
            request("b"),
            (DimensionValue("palette", "cool"),),
        ),
    )

    assert replay_a.kind is TransitionKind.DEPENDENT_ALREADY_COMPLETED
    assert replay_a.state is unverified_b.state
    assert verified_b.kind is TransitionKind.DEPENDENT_VERIFIED
    work = {item.dependent_id: item for item in verified_b.state.work}
    assert work["artifact:a"].status is WorkStatus.COMPLETED
    assert work["artifact:b"].status is WorkStatus.COMPLETED
    assert work["artifact:c"].status is WorkStatus.PENDING
    assert work["artifact:a"].correction_ids == ("correction:1",)
    assert work["artifact:b"].correction_ids == ("correction:1",)


def test_newer_correction_merges_work_and_remaining_repairs_use_current_basis() -> None:
    state = apply_reconciliation_operation(
        ReconciliationState(
            dependents=tuple(
                DependentRecord(
                    f"artifact:{name}",
                    f"decision:{name}",
                    ("taste:palette",),
                )
                for name in ("a", "b", "c")
            )
        ),
        CommitCorrection(
            "correction:x-to-y",
            (CorrectedInput("taste:palette", DecisionInputKind.TASTE),),
            "profile:y",
        ),
    ).state

    def request(name: str, direction: str, revision: str) -> AlignmentRequest:
        return AlignmentRequest(
            decision_id=f"decision:{name}",
            dimensions=("palette",),
            material=True,
            intent=(
                DecisionDirective(
                    "palette",
                    direction,
                    "current authoritative direction",
                    (Provenance("user", revision),),
                ),
            ),
            dependencies=("taste:palette",),
            context_revision=revision,
        )

    repaired_a = apply_reconciliation_operation(
        state,
        ReconcileDependent(
            "artifact:a",
            request("a", "y", "profile:y"),
            (DimensionValue("palette", "y"),),
        ),
    )
    targeted_b = apply_reconciliation_operation(
        repaired_a.state,
        ReconcileDependent(
            "artifact:b",
            request("b", "y", "profile:y"),
            (DimensionValue("palette", "x"),),
        ),
    )

    superseded = apply_reconciliation_operation(
        targeted_b.state,
        CommitCorrection(
            "correction:y-to-z",
            (CorrectedInput("taste:palette", DecisionInputKind.TASTE),),
            "profile:z",
        ),
    )
    current_b = apply_reconciliation_operation(
        superseded.state,
        ReconcileDependent(
            "artifact:b",
            request("b", "z", "profile:z"),
            (DimensionValue("palette", "x"),),
        ),
    )

    merged = {item.dependent_id: item for item in superseded.state.work}
    assert all(item.status is WorkStatus.PENDING for item in merged.values())
    assert merged["artifact:a"].correction_ids == (
        "correction:x-to-y",
        "correction:y-to-z",
    )
    assert merged["artifact:a"].basis_revision == "profile:z"
    assert merged["artifact:a"].attempts[0].status is WorkStatus.COMPLETED
    assert merged["artifact:b"].attempts[0].target_directions == (
        DimensionValue("palette", "y"),
    )
    assert current_b.repair is not None
    assert current_b.repair.changed_directions == (DimensionValue("palette", "z"),)
    assert current_b.state.work[1].attempts[-1].target_directions == (
        DimensionValue("palette", "z"),
    )


def test_propagation_blocks_stale_or_incomplete_affected_work_but_not_unrelated() -> None:
    state = apply_reconciliation_operation(
        ReconciliationState(
            dependents=(
                DependentRecord("artifact:a", "decision:a", ("intent:a",)),
                DependentRecord("artifact:b", "decision:b", ("intent:b",)),
            )
        ),
        CommitCorrection(
            "correction:a",
            (CorrectedInput("intent:a", DecisionInputKind.INTENT),),
            "aggregate:2",
        ),
    ).state

    def request(decision_id: str, direction: str, revision: str) -> AlignmentRequest:
        return AlignmentRequest(
            decision_id=decision_id,
            dimensions=("palette",),
            material=True,
            intent=(
                DecisionDirective(
                    "palette",
                    direction,
                    "authoritative project intent",
                    (Provenance("user", revision),),
                ),
            ),
            context_revision=revision,
        )

    old_a = request("decision:a", "warm", "aggregate:1")
    current_a = request("decision:a", "cool", "aggregate:2")
    stale = apply_reconciliation_operation(
        state,
        CheckPropagation(
            "artifact:a",
            resolve_alignment(old_a),
            current_a,
        ),
    )
    pending = apply_reconciliation_operation(
        state,
        CheckPropagation(
            "artifact:a",
            resolve_alignment(current_a),
            current_a,
        ),
    )

    current_b = request("decision:b", "balanced", "aggregate:b")
    unrelated = apply_reconciliation_operation(
        state,
        CheckPropagation(
            "artifact:b",
            resolve_alignment(current_b),
            current_b,
        ),
    )

    assert stale.propagation is not None
    assert stale.propagation.permitted is False
    assert "stale-alignment" in stale.propagation.blockers
    assert "reconciliation:pending" in stale.propagation.blockers
    assert pending.propagation is not None
    assert pending.propagation.blockers == ("reconciliation:pending",)
    assert unrelated.propagation is not None
    assert unrelated.propagation.permitted is True
    assert unrelated.state is state


def test_ordinary_authority_change_is_prospective_and_does_not_reopen_work() -> None:
    initial = ReconciliationState(
        dependents=(
            DependentRecord(
                "artifact:existing",
                "decision:existing",
                ("authority:project", "taste:palette"),
            ),
        )
    )
    operation = CommitCorrection(
        "authority-change:1",
        (CorrectedInput("authority:project", DecisionInputKind.AUTHORITY),),
        "aggregate:authority-2",
    )

    transition = apply_reconciliation_operation(initial, operation)
    replay = apply_reconciliation_operation(transition.state, operation)

    assert transition.kind is TransitionKind.PROSPECTIVE_CHANGE_RECORDED
    assert transition.affected_dependents == ()
    assert transition.state.work == ()
    assert transition.state.incomplete is False
    assert replay.kind is TransitionKind.CORRECTION_REPLAYED
    assert replay.state is transition.state


def test_reconciliation_state_round_trips_as_a_canonical_aggregate_value() -> None:
    pending = apply_reconciliation_operation(
        ReconciliationState(
            dependents=(
                DependentRecord("artifact:a", "decision:a", ("intent:a",)),
                DependentRecord("artifact:b", "decision:b", ("intent:a",)),
            )
        ),
        CommitCorrection(
            "correction:1",
            (CorrectedInput("intent:a", DecisionInputKind.INTENT),),
            "aggregate:2",
        ),
    ).state
    request = AlignmentRequest(
        decision_id="decision:a",
        dimensions=("palette",),
        material=True,
        intent=(
            DecisionDirective(
                "palette",
                "cool",
                "current intent",
                (Provenance("user", "intent:a"),),
            ),
        ),
        context_revision="aggregate:2",
    )
    interrupted = apply_reconciliation_operation(
        pending,
        ReconcileDependent(
            "artifact:a",
            request,
            (DimensionValue("palette", "warm"),),
        ),
    ).state

    document = reconciliation_state_to_document(interrupted)
    encoded = json.dumps(document, allow_nan=False, sort_keys=True)
    restored = reconciliation_state_from_document(json.loads(encoded))

    assert restored == interrupted
    assert restored.incomplete is True
    assert tuple(item.status for item in restored.work) == (
        WorkStatus.UNVERIFIED,
        WorkStatus.PENDING,
    )
    assert restored.work[0].attempts == interrupted.work[0].attempts
