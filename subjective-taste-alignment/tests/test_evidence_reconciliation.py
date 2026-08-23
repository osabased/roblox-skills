"""Behavioral scenarios for evidence interpretation and reconciliation."""

from __future__ import annotations

from dataclasses import replace

from alignment_contract import (
    Disposition,
    EpistemicBasis,
    Provenance,
    Scope,
    ValidationContext,
)
from evidence_reconciliation import (
    Ambiguity,
    BoundaryClaim,
    BundleClaim,
    ClaimStatus,
    Consequence,
    EvidenceEvent,
    EvidenceIdentityConflictError,
    EvidenceImplication,
    EvidenceState,
    EvidenceType,
    FeedbackKind,
    Fidelity,
    IngestEvidence,
    Judgment,
    OperationIdentityConflictError,
    PointClaim,
    RangeClaim,
    RejectionTarget,
    RelationshipClaim,
    SupportApplicability,
    SupportStrength,
    TransitionStatus,
    apply_evidence_operation,
)


def test_one_clear_direct_statement_can_establish_a_preference() -> None:
    state = EvidenceState()
    event = EvidenceEvent(
        event_id="feedback-1",
        evidence_type=EvidenceType.EXPLICIT_FEEDBACK,
        feedback=FeedbackKind.CORRECTION,
        judgment=Judgment.PREFERRED,
        scope=Scope("project", "project-a", "user-1"),
        context=(("device", "desktop"),),
        provenance=(Provenance(actor="user", source_id="message-1"),),
        validation_context=ValidationContext(
            domain="interface-design",
            fidelity="high",
            conditions=("desktop",),
        ),
        occurred_at=10,
        origin_branch="branch-b",
        implications=(
            EvidenceImplication(
                implication_id="layout-density",
                claim=PointClaim(
                    dimension="layout.density",
                    direction="compact",
                    disposition=Disposition.PREFERRED,
                ),
                basis=EpistemicBasis.EXPLICIT,
                represented_dimensions=("layout.density",),
                fidelity=Fidelity.HIGH,
                required_fidelity=Fidelity.HIGH,
                ambiguity=Ambiguity.CLEAR,
                epistemic_strength=SupportStrength.STRONG,
                preference_strength=0.8,
                consequence=Consequence.MATERIAL,
            ),
        ),
    )

    transition = apply_evidence_operation(
        state,
        IngestEvidence(operation_id="ingest-1", event=event),
    )

    assert transition.status is TransitionStatus.APPLIED
    assert transition.state.events == (event,)
    assert transition.changed_claim_ids == (transition.state.claims[0].claim_id,)
    resolution = transition.state.claims[0]
    assert resolution.status is ClaimStatus.ESTABLISHED
    assert resolution.knowledge.dimension == "layout.density"
    assert resolution.knowledge.direction == "compact"
    assert resolution.knowledge.disposition is Disposition.PREFERRED
    assert resolution.knowledge.basis is EpistemicBasis.EXPLICIT
    assert resolution.knowledge.scope is event.scope
    assert dict(resolution.knowledge.context) == {"device": "desktop"}
    assert resolution.knowledge.evidence == ("feedback-1#layout-density",)
    assert resolution.knowledge.provenance == event.provenance
    assert resolution.knowledge.strength == 0.8
    assert resolution.knowledge.confidence >= 0.9


def _one_implication(
    *,
    implication_id: str = "density",
    dimension: str = "layout.density",
    direction: str = "compact",
    disposition: Disposition = Disposition.PREFERRED,
) -> EvidenceImplication:
    return EvidenceImplication(
        implication_id=implication_id,
        claim=PointClaim(
            dimension=dimension,
            direction=direction,
            disposition=disposition,
        ),
        basis=EpistemicBasis.EXPLICIT,
        represented_dimensions=(dimension,),
        fidelity=Fidelity.HIGH,
        required_fidelity=Fidelity.HIGH,
        ambiguity=Ambiguity.CLEAR,
        epistemic_strength=SupportStrength.STRONG,
        preference_strength=0.7,
        consequence=Consequence.MATERIAL,
    )


def _event(
    event_id: str,
    implication: EvidenceImplication,
    *,
    evidence_type: EvidenceType = EvidenceType.EXPLICIT_FEEDBACK,
    feedback: FeedbackKind = FeedbackKind.CORRECTION,
    judgment: Judgment = Judgment.PREFERRED,
    rejection_target: RejectionTarget = RejectionTarget.NONE,
    occurred_at: int = 1,
) -> EvidenceEvent:
    return EvidenceEvent(
        event_id=event_id,
        evidence_type=evidence_type,
        feedback=feedback,
        judgment=judgment,
        rejection_target=rejection_target,
        scope=Scope("project", "project-a", "user-1"),
        context=(("device", "desktop"),),
        provenance=(Provenance(actor="user", source_id=f"source-{event_id}"),),
        validation_context=ValidationContext(
            domain="interface-design",
            fidelity="high",
            conditions=("desktop",),
        ),
        occurred_at=occurred_at,
        implications=(implication,),
    )


def test_acceptance_execution_rejection_and_success_do_not_become_taste() -> None:
    observations = (
        _event(
            "acceptable-approval",
            _one_implication(implication_id="acceptable"),
            feedback=FeedbackKind.APPROVAL,
            judgment=Judgment.ACCEPTABLE,
            occurred_at=1,
        ),
        _event(
            "good-enough",
            _one_implication(implication_id="good-enough"),
            feedback=FeedbackKind.GOOD_ENOUGH,
            judgment=Judgment.ACCEPTABLE,
            occurred_at=2,
        ),
        _event(
            "execution-rejection",
            _one_implication(
                implication_id="execution",
                disposition=Disposition.REJECTED,
            ),
            feedback=FeedbackKind.REJECTION,
            judgment=Judgment.UNSPECIFIED,
            rejection_target=RejectionTarget.EXECUTION_QUALITY,
            occurred_at=3,
        ),
        _event(
            "implementation-success",
            _one_implication(implication_id="success"),
            evidence_type=EvidenceType.IMPLEMENTATION_SUCCESS,
            feedback=FeedbackKind.NONE,
            judgment=Judgment.UNSPECIFIED,
            occurred_at=4,
        ),
    )

    state = EvidenceState()
    reasons: list[str] = []
    for index, event in enumerate(observations, start=1):
        transition = apply_evidence_operation(
            state,
            IngestEvidence(operation_id=f"observe-{index}", event=event),
        )
        state = transition.state
        reasons.extend(item.reason for item in transition.assessments)

    assert state.events == observations
    assert state.claims == ()
    assert reasons == [
        "acceptance does not assert preference",
        "good-enough feedback does not assert preference",
        "execution-quality rejection does not reject the direction",
        "implementation success is not preference evidence",
    ]


def _claim_implication(
    implication_id: str,
    claim: PointClaim | BundleClaim | RangeClaim | BoundaryClaim | RelationshipClaim,
) -> EvidenceImplication:
    return EvidenceImplication(
        implication_id=implication_id,
        claim=claim,
        basis=EpistemicBasis.EXPLICIT,
        represented_dimensions=claim.dimensions,
        fidelity=Fidelity.HIGH,
        required_fidelity=Fidelity.HIGH,
        ambiguity=Ambiguity.CLEAR,
        epistemic_strength=SupportStrength.STRONG,
        preference_strength=0.75,
        consequence=Consequence.MATERIAL,
    )


def test_comparisons_preserve_bundle_range_boundary_and_relationship_claims() -> None:
    bundle = BundleClaim(
        components=(
            ("color.palette", "muted"),
            ("layout.density", "compact"),
        ),
        disposition=Disposition.PREFERRED,
    )
    rejected_region = RangeClaim(
        dimension="layout.density",
        lower=0.0,
        upper=0.25,
        disposition=Disposition.REJECTED,
    )
    ceiling = BoundaryClaim(
        dimension="motion.intensity",
        operator=">",
        threshold=0.4,
        disposition=Disposition.REJECTED,
    )
    relationship = RelationshipClaim(
        dimensions=("typography.expression", "composition.complexity"),
        relation="expressive typography requires simple composition",
        disposition=Disposition.PREFERRED,
    )
    events = (
        _event("bundle-choice", _claim_implication("bundle", bundle), occurred_at=1),
        _event(
            "none-of-these",
            _claim_implication("rejected-region", rejected_region),
            feedback=FeedbackKind.NONE_OF_THESE,
            judgment=Judgment.UNSPECIFIED,
            rejection_target=RejectionTarget.DIRECTION,
            occurred_at=2,
        ),
        _event("motion-ceiling", _claim_implication("ceiling", ceiling), occurred_at=3),
        _event(
            "relational-correction",
            _claim_implication("relationship", relationship),
            occurred_at=4,
        ),
    )

    state = EvidenceState()
    for index, event in enumerate(events, start=1):
        state = apply_evidence_operation(
            state,
            IngestEvidence(operation_id=f"shape-{index}", event=event),
        ).state

    assert len(state.claims) == 4
    by_dimension = {
        resolution.knowledge.dimension: resolution for resolution in state.claims
    }
    bundle_resolution = by_dimension["bundle:color.palette+layout.density"]
    assert bundle_resolution.governing_claim is bundle
    assert bundle_resolution.knowledge.direction == (
        "bundle:{color.palette=muted,layout.density=compact}"
    )
    assert dict(bundle_resolution.knowledge.relationships) == {
        "claim_kind": "bundle",
        "color.palette": "muted",
        "layout.density": "compact",
    }
    assert "color.palette" not in by_dimension
    assert "layout.density" in by_dimension

    range_resolution = by_dimension["layout.density"]
    assert range_resolution.governing_claim is rejected_region
    assert range_resolution.knowledge.direction == "range:[0,0.25]"
    assert range_resolution.knowledge.disposition is Disposition.REJECTED
    assert dict(range_resolution.knowledge.relationships) == {
        "claim_kind": "range",
        "lower": "0",
        "upper": "0.25",
    }

    boundary_resolution = by_dimension["motion.intensity"]
    assert boundary_resolution.knowledge.direction == "boundary:>0.4"
    assert dict(boundary_resolution.knowledge.relationships) == {
        "claim_kind": "boundary",
        "operator": ">",
        "threshold": "0.4",
    }

    relation_resolution = by_dimension[
        "relationship:composition.complexity+typography.expression"
    ]
    assert relation_resolution.knowledge.direction == relationship.relation
    assert dict(relation_resolution.knowledge.relationships) == {
        "claim_kind": "relationship",
        "dimensions": "composition.complexity,typography.expression",
    }


def test_material_ambiguity_preserves_unresolved_property_for_clarification() -> None:
    implication = EvidenceImplication(
        implication_id="ambiguous-layout",
        claim=PointClaim(
            dimension="layout.density",
            direction=None,
            disposition=Disposition.UNRESOLVED,
        ),
        basis=EpistemicBasis.EXPLICIT,
        represented_dimensions=(
            "layout.density",
            "typography.density",
        ),
        fidelity=Fidelity.HIGH,
        required_fidelity=Fidelity.HIGH,
        ambiguity=Ambiguity.MATERIAL,
        epistemic_strength=SupportStrength.STRONG,
        preference_strength=0,
        consequence=Consequence.MATERIAL,
        plausible_dimensions=("layout.density", "typography.density"),
    )
    event = _event("ambiguous", implication)

    transition = apply_evidence_operation(
        EvidenceState(),
        IngestEvidence(operation_id="operation:ambiguous", event=event),
    )

    assert transition.state.claims == ()
    assert transition.checkpoints[0].plausible_dimensions == (
        "layout.density",
        "typography.density",
    )
    assert transition.assessments[0].usable is False
    assert transition.assessments[0].reason == (
        "subjective meaning remained materially ambiguous"
    )


def test_correction_learns_underlying_relationship_without_surface_overreach() -> None:
    correction = RelationshipClaim(
        dimensions=("motion.amount", "interface.complexity"),
        relation="reduce motion as interface complexity increases",
        disposition=Disposition.PREFERRED,
    )
    implication = _claim_implication("underlying-principle", correction)
    event = _event("correction-1", implication)

    transition = apply_evidence_operation(
        EvidenceState(),
        IngestEvidence(operation_id="operation:correction", event=event),
    )
    resolution = transition.state.claims[0]

    assert resolution.knowledge.dimension == (
        "relationship:interface.complexity+motion.amount"
    )
    assert resolution.knowledge.direction == correction.relation
    assert resolution.knowledge.evidence == ("correction-1#underlying-principle",)


def test_branch_inapplicable_support_excludes_one_implication_only() -> None:
    applicable = _one_implication(implication_id="applicable")
    excluded = EvidenceImplication(
        implication_id="branch-excluded",
        claim=PointClaim(
            dimension="color.palette",
            direction="muted",
            disposition=Disposition.PREFERRED,
        ),
        basis=EpistemicBasis.EXPLICIT,
        represented_dimensions=("color.palette",),
        fidelity=Fidelity.HIGH,
        required_fidelity=Fidelity.HIGH,
        ambiguity=Ambiguity.CLEAR,
        epistemic_strength=SupportStrength.STRONG,
        preference_strength=0.8,
        consequence=Consequence.MATERIAL,
        applicable_branches=("desktop",),
        applicability=SupportApplicability.BRANCH_INAPPLICABLE,
    )
    event = EvidenceEvent(
        event_id="feedback-branch",
        evidence_type=EvidenceType.EXPLICIT_FEEDBACK,
        feedback=FeedbackKind.CORRECTION,
        judgment=Judgment.PREFERRED,
        scope=Scope("project", "project-a", "user-1"),
        context=(("device", "desktop"),),
        provenance=(Provenance(actor="user", source_id="source:1"),),
        validation_context=ValidationContext(
            domain="interface-design",
            fidelity="high",
            conditions=("desktop",),
        ),
        occurred_at=2,
        implications=(applicable, excluded),
    )

    transition = apply_evidence_operation(
        EvidenceState(),
        IngestEvidence(operation_id="operation:branch", event=event),
    )
    dimensions = {
        resolution.knowledge.dimension for resolution in transition.state.claims
    }

    assert dimensions == {"layout.density"}
    assert transition.assessments[-1].reason == "support is branch_inapplicable"


def _variable_implication(
    *,
    implication_id: str = "density",
    dimension: str = "layout.density",
    direction: str = "compact",
    disposition: Disposition = Disposition.PREFERRED,
    basis: EpistemicBasis = EpistemicBasis.EXPLICIT,
    epistemic_strength: SupportStrength = SupportStrength.MODERATE,
    fidelity: Fidelity = Fidelity.HIGH,
    consequence: Consequence = Consequence.MATERIAL,
    independence_key: str | None = None,
) -> EvidenceImplication:
    return EvidenceImplication(
        implication_id=implication_id,
        claim=PointClaim(
            dimension=dimension,
            direction=direction,
            disposition=disposition,
        ),
        basis=basis,
        represented_dimensions=(dimension,),
        fidelity=fidelity,
        required_fidelity=Fidelity.HIGH,
        ambiguity=Ambiguity.CLEAR,
        epistemic_strength=epistemic_strength,
        preference_strength=0.7,
        consequence=consequence,
        independence_key=independence_key,
    )


def _ingest(
    state: EvidenceState, *events: EvidenceEvent
) -> EvidenceState:
    for index, event in enumerate(events, start=1):
        state = apply_evidence_operation(
            state,
            IngestEvidence(operation_id=f"op-{len(state.applied_operations) + index}", event=event),
        ).state
    return state


def test_conflicting_evidence_resolves_by_quality_not_vote_count() -> None:
    weak_votes = tuple(
        _event(
            f"weak-{index}",
            _variable_implication(
                implication_id=f"weak-{index}",
                basis=EpistemicBasis.INFERRED,
                epistemic_strength=SupportStrength.WEAK,
                independence_key=f"weak-panel-{index}",
            ),
            evidence_type=EvidenceType.OBSERVABLE_ACTION,
            feedback=FeedbackKind.NONE,
            judgment=Judgment.UNSPECIFIED,
            occurred_at=index,
        )
        for index in range(1, 4)
    )
    strong_correction = _event(
        "explicit-correction",
        _variable_implication(
            implication_id="correction",
            direction="compact",
            disposition=Disposition.REJECTED,
            basis=EpistemicBasis.EXPLICIT,
            epistemic_strength=SupportStrength.STRONG,
            fidelity=Fidelity.HIGH,
        ),
        occurred_at=5,
    )

    state = _ingest(EvidenceState(), *weak_votes, strong_correction)
    resolution = state.claims[0]
    superseded_ids = {
        record.support.stable_id
        for record in state.support_lifecycle
        if record.applicability is SupportApplicability.SUPERSEDED
    }

    assert resolution.knowledge.direction == "compact"
    assert resolution.knowledge.disposition is Disposition.REJECTED
    assert resolution.status is ClaimStatus.ESTABLISHED
    assert resolution.knowledge.confidence == 0.95
    assert resolution.knowledge.evidence == (
        "explicit-correction#correction",
    )
    assert superseded_ids == {
        "weak-1#weak-1",
        "weak-2#weak-2",
        "weak-3#weak-3",
    }
    assert "three weak observations" not in resolution.reason.lower()
    assert "higher-quality" in resolution.reason


def test_repeated_near_equivalent_observations_do_not_manufacture_certainty() -> None:
    near_equivalent = tuple(
        _event(
            f"repeat-{index}",
            _variable_implication(
                implication_id=f"repeat-{index}",
                epistemic_strength=SupportStrength.MODERATE,
                independence_key="survey-panel",
            ),
            occurred_at=index,
        )
        for index in range(1, 6)
    )

    state = _ingest(EvidenceState(), *near_equivalent)
    assert len(state.claims) == 1
    envelope = state.claims[0].envelope
    assert envelope is not None
    assert envelope.confidence == 0.65

    independent_second_observation = _event(
        "independent-repeat",
        _variable_implication(
            implication_id="independent-repeat",
            epistemic_strength=SupportStrength.MODERATE,
            independence_key="follow-up-interview",
        ),
        occurred_at=6,
    )
    corroborated = _ingest(state, independent_second_observation)

    assert len(corroborated.claims) == 1
    assert corroborated.claims[0].status is ClaimStatus.HYPOTHESIS
    confidence = corroborated.claims[0].knowledge.confidence
    assert 0.65 < confidence <= 0.75


def test_incomparable_conflicting_evidence_returns_unresolved_without_averaging() -> None:
    explicit_but_weak = _event(
        "explicit-weak",
        _variable_implication(
            implication_id="explicit-weak",
            direction="compact",
            disposition=Disposition.PREFERRED,
            basis=EpistemicBasis.EXPLICIT,
            epistemic_strength=SupportStrength.WEAK,
        ),
        evidence_type=EvidenceType.EXPLICIT_FEEDBACK,
        occurred_at=3,
    )
    inferred_but_strong = _event(
        "inferred-strong",
        _variable_implication(
            implication_id="inferred-strong",
            direction="compact",
            disposition=Disposition.REJECTED,
            basis=EpistemicBasis.INFERRED,
            epistemic_strength=SupportStrength.STRONG,
        ),
        evidence_type=EvidenceType.APPROVED_ARTIFACT,
        feedback=FeedbackKind.NONE,
        judgment=Judgment.UNSPECIFIED,
        occurred_at=4,
    )

    state = _ingest(EvidenceState(), explicit_but_weak, inferred_but_strong)
    assert len(state.claims) == 1
    resolution = state.claims[0]

    assert resolution.status is ClaimStatus.UNRESOLVED
    assert resolution.governing_claim is None
    assert resolution.envelope is None
    assert resolution.knowledge.disposition is Disposition.UNRESOLVED
    assert resolution.knowledge.direction is None
    conflicting_refs = {ref.stable_id for ref in resolution.conflicts}
    assert conflicting_refs == {
        "explicit-weak#explicit-weak",
        "inferred-strong#inferred-strong",
    }


def test_conflict_checkpoint_requests_resolution_of_the_disagreement() -> None:
    explicit_but_weak = _event(
        "explicit-weak",
        _variable_implication(
            implication_id="explicit-weak",
            basis=EpistemicBasis.EXPLICIT,
            epistemic_strength=SupportStrength.WEAK,
        ),
        occurred_at=3,
    )
    inferred_but_strong = _event(
        "inferred-strong",
        _variable_implication(
            implication_id="inferred-strong",
            direction="spacious",
            disposition=Disposition.REJECTED,
            basis=EpistemicBasis.INFERRED,
            epistemic_strength=SupportStrength.STRONG,
        ),
        occurred_at=4,
    )

    first = apply_evidence_operation(
        EvidenceState(),
        IngestEvidence(operation_id="op-a", event=explicit_but_weak),
    )
    second = apply_evidence_operation(
        first.state,
        IngestEvidence(operation_id="op-b", event=inferred_but_strong),
    )

    assert second.checkpoints
    checkpoint = second.checkpoints[0]
    assert set(checkpoint.plausible_dimensions) == {"layout.density"}
    assert "conflicting" in checkpoint.prompt.lower()


def test_newer_strong_explicit_evidence_replaces_established_claim() -> None:
    original = _event(
        "original-preference",
        _variable_implication(
            implication_id="original",
            epistemic_strength=SupportStrength.STRONG,
        ),
        occurred_at=1,
    )

    first = apply_evidence_operation(
        EvidenceState(),
        IngestEvidence(operation_id="op-first", event=original),
    )
    established_id = first.state.claims[0].claim_id
    assert first.state.claims[0].status is ClaimStatus.ESTABLISHED

    correction = _event(
        "later-correction",
        _variable_implication(
            implication_id="correction",
            direction="compact",
            disposition=Disposition.REJECTED,
            epistemic_strength=SupportStrength.STRONG,
        ),
        occurred_at=2,
    )
    second = apply_evidence_operation(
        first.state,
        IngestEvidence(operation_id="op-second", event=correction),
    )

    assert second.status is TransitionStatus.APPLIED
    assert established_id in second.changed_claim_ids
    resolution = second.state.claims[0]
    assert resolution.claim_id == established_id
    assert resolution.knowledge.disposition is Disposition.REJECTED
    assert resolution.knowledge.evidence == ("later-correction#correction",)
    superseded = {
        record.support.stable_id
        for record in second.state.support_lifecycle
        if record.applicability is SupportApplicability.SUPERSEDED
    }
    assert superseded == {"original-preference#original"}


def test_promotion_is_proportionate_to_consequence() -> None:
    scenarios = (
        (
            "load-bearing-inference",
            EpistemicBasis.INFERRED,
            SupportStrength.STRONG,
            Consequence.LOAD_BEARING,
            ClaimStatus.HYPOTHESIS,
        ),
        (
            "material-inference",
            EpistemicBasis.INFERRED,
            SupportStrength.STRONG,
            Consequence.MATERIAL,
            ClaimStatus.HYPOTHESIS,
        ),
        (
            "reversible-inference",
            EpistemicBasis.INFERRED,
            SupportStrength.STRONG,
            Consequence.REVERSIBLE,
            ClaimStatus.ESTABLISHED,
        ),
        (
            "load-bearing-explicit",
            EpistemicBasis.EXPLICIT,
            SupportStrength.STRONG,
            Consequence.LOAD_BEARING,
            ClaimStatus.ESTABLISHED,
        ),
        (
            "load-bearing-moderate-explicit",
            EpistemicBasis.EXPLICIT,
            SupportStrength.MODERATE,
            Consequence.LOAD_BEARING,
            ClaimStatus.HYPOTHESIS,
        ),
    )
    for label, basis, strength, consequence, expected_status in scenarios:
        event = _event(
            f"event-{label}",
            _variable_implication(
                implication_id=label,
                basis=basis,
                epistemic_strength=strength,
                consequence=consequence,
            ),
        )
        state = _ingest(EvidenceState(), event)
        assert state.claims[0].status is expected_status, label


def test_silence_and_delegation_never_become_preference_evidence() -> None:
    non_evidence_events = (
        _event(
            "silence",
            _variable_implication(implication_id="silence"),
            evidence_type=EvidenceType.SILENCE,
            feedback=FeedbackKind.NONE,
            judgment=Judgment.UNSPECIFIED,
        ),
        _event(
            "progress",
            _variable_implication(implication_id="progress"),
            evidence_type=EvidenceType.CONTINUED_PROGRESS,
            feedback=FeedbackKind.NONE,
            judgment=Judgment.UNSPECIFIED,
        ),
        _event(
            "delegation",
            _variable_implication(implication_id="delegation"),
            evidence_type=EvidenceType.DELEGATED_EXECUTION,
            feedback=FeedbackKind.NONE,
            judgment=Judgment.UNSPECIFIED,
        ),
    )

    reasons: list[str] = []
    state = EvidenceState()
    for index, event in enumerate(non_evidence_events, start=1):
        transition = apply_evidence_operation(
            state,
            IngestEvidence(operation_id=f"non-evidence-{index}", event=event),
        )
        state = transition.state
        reasons.extend(item.reason for item in transition.assessments)

    assert state.events == non_evidence_events
    assert state.claims == ()
    assert reasons == [
        "silence is not preference evidence",
        "continued progress is not preference evidence",
        "delegated execution is authorized judgment, not preference evidence",
    ]


def test_replay_is_idempotent_while_distinct_observations_stay_separate() -> None:
    event = _event(
        "first-observation",
        _variable_implication(
            implication_id="first",
            epistemic_strength=SupportStrength.MODERATE,
        ),
    )
    operation = IngestEvidence(operation_id="op-1", event=event)

    applied = apply_evidence_operation(EvidenceState(), operation)
    replayed = apply_evidence_operation(applied.state, operation)

    assert applied.status is TransitionStatus.APPLIED
    assert replayed.status is TransitionStatus.REPLAYED
    assert replayed.state == applied.state
    assert replayed.changed_claim_ids == ()

    duplicate_ingest = apply_evidence_operation(
        applied.state,
        IngestEvidence(operation_id="op-2", event=event),
    )
    assert duplicate_ingest.status is TransitionStatus.DUPLICATE_EVENT
    assert duplicate_ingest.state.claims == applied.state.claims
    assert len(duplicate_ingest.state.events) == 1

    distinct_later = _event(
        "second-observation",
        _variable_implication(
            implication_id="second",
            epistemic_strength=SupportStrength.MODERATE,
        ),
        occurred_at=9,
    )
    separate = apply_evidence_operation(
        duplicate_ingest.state,
        IngestEvidence(operation_id="op-3", event=distinct_later),
    )
    assert separate.status is TransitionStatus.APPLIED
    assert len(separate.state.events) == 2
    assert len(separate.state.claims) == 1
    assert separate.state.claims[0].knowledge.confidence <= 0.75

    try:
        apply_evidence_operation(
            separate.state,
            IngestEvidence(operation_id="op-3", event=event),
        )
    except OperationIdentityConflictError:
        pass
    else:
        raise AssertionError("operation id reuse must conflict")

    altered_event = _event(
        "first-observation",
        _variable_implication(implication_id="first"),
        occurred_at=99,
    )
    try:
        apply_evidence_operation(
            separate.state,
            IngestEvidence(operation_id="op-4", event=altered_event),
        )
    except EvidenceIdentityConflictError:
        pass
    else:
        raise AssertionError("event id reuse with new content must conflict")


def test_none_of_these_narrows_only_the_explored_region() -> None:
    explored_region = RangeClaim(
        dimension="layout.density",
        lower=0.25,
        upper=1.0,
        disposition=Disposition.REJECTED,
    )
    event = _event(
        "none-of-these",
        _claim_implication("explored-region", explored_region),
        feedback=FeedbackKind.NONE_OF_THESE,
        judgment=Judgment.UNSPECIFIED,
        rejection_target=RejectionTarget.DIRECTION,
    )

    state = _ingest(EvidenceState(), event)

    assert len(state.claims) == 1
    resolution = state.claims[0]
    assert resolution.knowledge.direction == "range:[0.25,1]"
    assert resolution.knowledge.disposition is Disposition.REJECTED
    assert dict(resolution.knowledge.relationships)["claim_kind"] == "range"
    assert "compact" != resolution.knowledge.direction  # no invented alternative
    assert all(
        claim.governing_claim is explored_region for claim in state.claims
    )


def test_context_split_keeps_scoped_claims_independent() -> None:
    desktop = _event(
        "desktop-preference",
        _variable_implication(
            implication_id="desktop",
            direction="compact",
            disposition=Disposition.PREFERRED,
            epistemic_strength=SupportStrength.STRONG,
        ),
        occurred_at=1,
    )
    mobile = replace(
        _event(
            "mobile-preference",
            _variable_implication(
                implication_id="mobile",
                direction="airy",
                disposition=Disposition.PREFERRED,
                epistemic_strength=SupportStrength.STRONG,
            ),
            occurred_at=2,
        ),
        context=(("device", "mobile"),),
        validation_context=ValidationContext(
            domain="interface-design",
            fidelity="high",
            conditions=("mobile",),
        ),
    )

    first = apply_evidence_operation(
        EvidenceState(), IngestEvidence(operation_id="op-desktop", event=desktop)
    )
    second = apply_evidence_operation(
        first.state, IngestEvidence(operation_id="op-mobile", event=mobile)
    )

    assert second.status is TransitionStatus.APPLIED
    assert len(second.state.claims) == 2
    by_device = {
        dict(claim.knowledge.context)["device"]: claim
        for claim in second.state.claims
    }
    assert by_device["desktop"].status is ClaimStatus.ESTABLISHED
    assert by_device["desktop"].knowledge.direction == "compact"
    assert by_device["mobile"].status is ClaimStatus.ESTABLISHED
    assert by_device["mobile"].knowledge.direction == "airy"
    assert by_device["desktop"].conflicts == ()
    assert by_device["mobile"].conflicts == ()
    assert second.checkpoints == ()
    # Splitting by context records no lifecycle damage on either side.
    assert second.state.support_lifecycle == ()


def test_later_material_contradiction_demotes_established_knowledge() -> None:
    established = _event(
        "established-preference",
        _variable_implication(
            implication_id="established",
            direction="compact",
            disposition=Disposition.PREFERRED,
            basis=EpistemicBasis.EXPLICIT,
            epistemic_strength=SupportStrength.STRONG,
        ),
        occurred_at=5,
    )
    contradiction = _event(
        "later-artifact",
        _variable_implication(
            implication_id="artifact-rejection",
            direction="compact",
            disposition=Disposition.REJECTED,
            basis=EpistemicBasis.INFERRED,
            epistemic_strength=SupportStrength.STRONG,
        ),
        evidence_type=EvidenceType.APPROVED_ARTIFACT,
        feedback=FeedbackKind.NONE,
        judgment=Judgment.UNSPECIFIED,
        occurred_at=6,
    )

    first = apply_evidence_operation(
        EvidenceState(),
        IngestEvidence(operation_id="op-establish", event=established),
    )
    claim_id = first.state.claims[0].claim_id
    assert first.state.claims[0].status is ClaimStatus.ESTABLISHED

    second = apply_evidence_operation(
        first.state,
        IngestEvidence(operation_id="op-contradict", event=contradiction),
    )
    resolution = next(
        claim for claim in second.state.claims if claim.claim_id == claim_id
    )
    assert resolution.status is not ClaimStatus.ESTABLISHED
    stale = {
        record.support.stable_id
        for record in second.state.support_lifecycle
        if record.applicability is SupportApplicability.STALE
    }
    assert stale == {"established-preference#established"}

