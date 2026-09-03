"""Behavioral scenarios for profile inspection and safe user control."""

from __future__ import annotations

from dataclasses import replace

import pytest

from alignment_contract import (
    Disposition,
    EpistemicBasis,
    EpistemicLabel,
    Provenance,
    Scope,
    ValidationContext,
)
from evidence_reconciliation import (
    Ambiguity,
    ClaimStatus,
    Consequence,
    EvidenceEvent,
    EvidenceImplication,
    EvidenceState,
    EvidenceType,
    FeedbackKind,
    Fidelity,
    Judgment,
    PointClaim,
    SupportApplicability,
    SupportRef,
    SupportStrength,
)
from profile_composition import ProfileProperty
from profile_control import (
    DirectEditRequest,
    ManagementKind,
    ManagementRequest,
    apply_direct_edit,
    correction_commit,
    inspect_profile,
    manage_profile,
    request_support_change,
)
from profile_lifecycle import (
    LifecycleState,
    LifecycleStatus,
    initial_lifecycle_state,
)
from profile_persistence import (
    CURRENT_SCHEMA_VERSION,
    UNKNOWN_AUTHORSHIP,
    MutationAuthorship,
    ProfileState,
)


PROJECT_SCOPE = Scope(kind="project", identity="project-a", represented_subject="user-1")
SESSION_SCOPE = Scope(kind="session", identity="session-9", represented_subject="user-1")
GLOBAL_SCOPE = Scope(kind="global", identity="user-1", represented_subject="user-1")


def _implication(
    implication_id: str,
    dimension: str,
    direction: str,
) -> EvidenceImplication:
    return EvidenceImplication(
        implication_id=implication_id,
        claim=PointClaim(
            dimension=dimension,
            direction=direction,
            disposition=Disposition.PREFERRED,
        ),
        basis=EpistemicBasis.EXPLICIT,
        represented_dimensions=(dimension,),
        fidelity=Fidelity.HIGH,
        required_fidelity=Fidelity.HIGH,
        ambiguity=Ambiguity.CLEAR,
        epistemic_strength=SupportStrength.STRONG,
        preference_strength=0.8,
        consequence=Consequence.MATERIAL,
    )


def _instruction_event(
    event_id: str,
    dimension: str,
    direction: str,
    scope: Scope = PROJECT_SCOPE,
) -> EvidenceEvent:
    return EvidenceEvent(
        event_id=event_id,
        evidence_type=EvidenceType.EXPLICIT_FEEDBACK,
        feedback=FeedbackKind.CORRECTION,
        judgment=Judgment.PREFERRED,
        scope=scope,
        context=(("surface", "settings"),),
        provenance=(Provenance(actor="user", source_id=f"message:{event_id}"),),
        validation_context=ValidationContext(
            domain="interface-design",
            fidelity="high",
            conditions=("settings surface",),
        ),
        occurred_at=10,
        implications=(
            _implication(f"{event_id}-impl", dimension, direction),
        ),
    )


def _property(claim_id: str, direction: str, scope: Scope) -> ProfileProperty:
    from alignment_contract import PreferenceKnowledge

    return ProfileProperty(
        claim_id=claim_id,
        section="typography",
        knowledge=PreferenceKnowledge(
            dimension="typography.expression",
            direction=direction,
            disposition=Disposition.PREFERRED,
            basis=EpistemicBasis.EXPLICIT,
            confidence=0.95,
            strength=0.8,
            scope=scope,
            context={"surface": "settings"},
            evidence=("feedback-1#feedback-1-impl",),
            provenance=(Provenance(actor="user", source_id="message:feedback-1"),),
            validation_context=ValidationContext(
                domain="interface-design",
                fidelity="high",
                conditions=("settings surface",),
            ),
            relationships={"layout.density": "pairs-with-restrained-type"},
        ),
    )


def _state(
    *,
    scope: Scope = PROJECT_SCOPE,
    property_: ProfileProperty | None = None,
) -> LifecycleState:
    properties = (
        (property_,)
        if property_ is not None
        else (_property("claim:typography", "restrained grotesque", scope),)
    )
    profile = ProfileState(
        schema_version=CURRENT_SCHEMA_VERSION,
        profile_id="profile:user-1",
        properties=properties,
    )
    return initial_lifecycle_state(
        profile,
        EvidenceState(
            events=(
                _instruction_event(
                    "feedback-1", "typography.expression", "restrained grotesque",
                    scope,
                ),
            ),
        ),
    )


def test_inspection_exposes_facets_without_flattening_conditionals() -> None:
    inspection = inspect_profile(_state())

    assert inspection.profile_id == "profile:user-1"
    report = inspection.properties[0]
    assert report.claim_id == "claim:typography"
    assert report.section == "typography"
    assert report.dimension == "typography.expression"
    assert report.direction == "restrained grotesque"
    assert report.disposition is Disposition.PREFERRED
    assert report.label is EpistemicLabel.CONFIRMED_PREFERENCE
    assert report.basis is EpistemicBasis.EXPLICIT
    assert report.confidence == 0.95
    assert report.scope == PROJECT_SCOPE
    assert dict(report.context) == {"surface": "settings"}
    assert report.validation_context.conditions == ("settings surface",)
    # Conditional meaning survives verbatim; it is not flattened into text.
    assert dict(report.relationships) == {
        "layout.density": "pairs-with-restrained-type"
    }
    assert report.evidence == ("feedback-1#feedback-1-impl",)
    assert report.provenance[0].actor == "user"
    assert inspection.unresolved_property_ids == ()
    assert inspection.support_exclusions == ()


def test_inspection_reports_unresolved_and_excluded_knowledge() -> None:
    from alignment_contract import PreferenceKnowledge

    excluded_property = replace(
        _property("claim:typography", "restrained grotesque", PROJECT_SCOPE),
        evidence_applicable=False,
    )
    unresolved_property = ProfileProperty(
        claim_id="claim:motion",
        section="motion",
        knowledge=PreferenceKnowledge(
            dimension="motion.character",
            direction=None,
            disposition=Disposition.UNRESOLVED,
            basis=EpistemicBasis.INFERRED,
            confidence=0.0,
            strength=0.0,
            scope=PROJECT_SCOPE,
            context={},
            evidence=(),
            provenance=(),
            validation_context=ValidationContext(
                domain="interface-design", fidelity="unknown"
            ),
            relationships={},
        ),
    )
    state = _state(property_=excluded_property)

    inspection = inspect_profile(state)
    assert inspection.properties[0].evidence_applicable is False

    unresolved_profile = ProfileState(
        schema_version=CURRENT_SCHEMA_VERSION,
        profile_id="profile:user-1",
        properties=(excluded_property, unresolved_property),
    )
    unresolved_inspection = inspect_profile(
        initial_lifecycle_state(unresolved_profile)
    )
    assert unresolved_inspection.unresolved_property_ids == ("claim:motion",)


def test_management_requests_route_without_manual_representation_edits() -> None:
    state = _state()
    support = SupportRef("feedback-1", "feedback-1-impl")

    reset = manage_profile(
        state,
        ManagementRequest(
            operation_id="mgmt-reset-1",
            instruction_id="instruction:reset-typography",
            kind=ManagementKind.RESET,
            scope=PROJECT_SCOPE,
            support=support,
        ),
    )
    assert reset.transition is not None
    assert reset.transition.status is LifecycleStatus.APPLIED
    assert reset.transition.changed_claim_ids
    records = reset.transition.state.evidence.support_lifecycle
    assert records[-1].applicability is SupportApplicability.RESET_EXCLUDED

    versioned = manage_profile(
        reset.transition.state,
        ManagementRequest(
            operation_id="mgmt-version-1",
            instruction_id="instruction:branch",
            kind=ManagementKind.VERSION,
            scope=PROJECT_SCOPE,
            branch_id="branch-alt",
        ),
    )
    assert versioned.transition is not None
    assert versioned.transition.state.branches.branch("branch-alt") is not None

    undone = manage_profile(
        versioned.transition.state,
        ManagementRequest(
            operation_id="mgmt-undo-1",
            instruction_id="instruction:undo",
            kind=ManagementKind.UNDO,
            scope=PROJECT_SCOPE,
        ),
    )
    assert undone.transition is not None
    assert undone.transition.status is LifecycleStatus.UNDONE


def test_correction_preserves_exactly_the_requested_scope() -> None:
    state = _state()

    project_correction = manage_profile(
        state,
        ManagementRequest(
            operation_id="mgmt-correct-project",
            instruction_id="instruction:correct-for-this-project",
            kind=ManagementKind.CORRECT,
            scope=PROJECT_SCOPE,
            dimension="typography.expression",
            new_direction="playful serif",
            prior_support=SupportRef("feedback-1", "feedback-1-impl"),
        ),
    )
    event = project_correction.instruction_event
    assert event is not None
    assert event.scope == PROJECT_SCOPE
    assert event.provenance[0].actor == "user"

    session_correction = manage_profile(
        state,
        ManagementRequest(
            operation_id="mgmt-correct-session",
            instruction_id="instruction:just-this-session",
            kind=ManagementKind.CORRECT,
            scope=SESSION_SCOPE,
            dimension="typography.expression",
            new_direction="playful serif",
            prior_support=SupportRef("feedback-1", "feedback-1-impl"),
        ),
    )
    assert session_correction.instruction_event is not None
    assert session_correction.instruction_event.scope == SESSION_SCOPE

    global_correction = manage_profile(
        state,
        ManagementRequest(
            operation_id="mgmt-correct-global",
            instruction_id="instruction:always-prefer",
            kind=ManagementKind.CORRECT,
            scope=GLOBAL_SCOPE,
            dimension="typography.expression",
            new_direction="playful serif",
            prior_support=SupportRef("feedback-1", "feedback-1-impl"),
        ),
    )
    assert global_correction.instruction_event is not None
    assert global_correction.instruction_event.scope == GLOBAL_SCOPE


def test_direct_edit_separates_editable_assertions_from_protected_state() -> None:
    state = _state()

    outcome = apply_direct_edit(
        state,
        DirectEditRequest(
            edit_id="edit-1",
            authorship=MutationAuthorship(
                actor="user", source_id="edit-1", attributable=True
            ),
            claim_id="claim:typography",
            direction="warm humanist sans",
        ),
    )
    assert outcome.instruction_event is not None
    assert outcome.instruction_event.provenance[0].actor == "user"

    with pytest.raises(ValueError, match="protected"):
        DirectEditRequest(
            edit_id="edit-2",
            authorship=MutationAuthorship(
                actor="user", source_id="edit-2", attributable=True
            ),
            claim_id="claim:typography",
            direction="warm humanist sans",
            confidence=0.99,
        )


def test_agent_and_unknown_edits_never_become_user_evidence() -> None:
    for authorship in (
        MutationAuthorship(actor="agent", source_id="agent-edit", attributable=True),
        UNKNOWN_AUTHORSHIP,
    ):
        request_edit_id = f"edit-{authorship.actor}"
        state = _state()
        outcome = apply_direct_edit(
            state,
            DirectEditRequest(
                edit_id=request_edit_id,
                authorship=authorship,
                claim_id="claim:typography",
                direction="brutalist mono",
            ),
        )
        event = outcome.instruction_event
        assert event is not None
        assert event.provenance[0].actor == authorship.actor
        evidence_state = outcome.transition.state.evidence
        # The mutation stays inspectable as history...
        assert any(item.event_id == request_edit_id for item in evidence_state.events)
        # ...but no preference knowledge forms from it: the canonical
        # engine refuses support that is not attributable to a person.
        assert all(
            claim.knowledge.direction != "brutalist mono"
            for claim in evidence_state.claims
        )


def test_unsupported_edits_cannot_resurrect_or_suppress_evidence() -> None:
    state = _state()
    support = SupportRef("feedback-1", "feedback-1-impl")

    with pytest.raises(ValueError, match="lifecycle operation"):
        request_support_change(
            state,
            MutationAuthorship(
                actor="user", source_id="external-edit", attributable=True
            ),
            support,
            reactivate=True,
        )
    with pytest.raises(ValueError, match="lifecycle operation"):
        request_support_change(state, UNKNOWN_AUTHORSHIP, support, reactivate=False)

    # The validated path exists only through lifecycle management operations.
    managed = manage_profile(
        state,
        ManagementRequest(
            operation_id="mgmt-reset-2",
            instruction_id="instruction:reset",
            kind=ManagementKind.RESET,
            scope=PROJECT_SCOPE,
            support=support,
        ),
    )
    assert managed.transition is not None
    assert managed.transition.state.evidence.support_lifecycle[-1].support == support


def test_instruction_is_the_evidence_and_persistence_is_not_a_second_observation() -> None:
    state = _state()
    baseline = initial_lifecycle_state(
        ProfileState(schema_version=CURRENT_SCHEMA_VERSION, profile_id="profile:user-1"),
        EvidenceState(events=(_instruction_event(
            "solo-1", "typography.expression", "playful serif"
        ),)),
    )

    outcome = manage_profile(
        state,
        ManagementRequest(
            operation_id="mgmt-correct-once",
            instruction_id="instruction:single-correction",
            kind=ManagementKind.CORRECT,
            scope=PROJECT_SCOPE,
            dimension="typography.expression",
            new_direction="playful serif",
            prior_support=SupportRef("feedback-1", "feedback-1-impl"),
        ),
    )

    assert outcome.transition is not None
    events = outcome.transition.state.evidence.events
    instruction_events = [
        event
        for event in events
        if event.event_id.startswith("instruction:")
    ]
    assert len(instruction_events) == 1
    corrected_claims = [
        claim
        for claim in outcome.transition.state.evidence.claims
        if claim.knowledge.direction == "playful serif"
    ]
    assert len(corrected_claims) == 1
    solo_claim = baseline.evidence.claims[0]
    assert corrected_claims[0].knowledge.confidence == (
        solo_claim.knowledge.confidence
    )
    assert corrected_claims[0].status is ClaimStatus.ESTABLISHED


def test_correction_flags_only_actual_dependents_for_reconciliation() -> None:
    from reconciliation import (
        DependentRecord,
        ReconciliationState,
        WorkStatus,
        apply_reconciliation_operation,
    )

    state = _state()
    outcome = manage_profile(
        state,
        ManagementRequest(
            operation_id="mgmt-correct-deps",
            instruction_id="instruction:correct-dependents",
            kind=ManagementKind.CORRECT,
            scope=PROJECT_SCOPE,
            dimension="typography.expression",
            new_direction="playful serif",
            prior_support=SupportRef("feedback-1", "feedback-1-impl"),
        ),
    )
    dependents = (
        DependentRecord(
            dependent_id="dependent:new-button",
            decision_id="decision:new-button",
            input_dependencies=tuple(
                f"knowledge:{claim_id}" for claim_id in outcome.corrected_claim_ids
            ),
        ),
        DependentRecord(
            dependent_id="dependent:footer",
            decision_id="decision:footer",
            input_dependencies=("knowledge:an-unrelated-claim",),
        ),
    )

    commit = correction_commit(outcome, basis_revision="basis-r2")

    assert commit is not None
    assert outcome.corrected_claim_ids
    reconciliation = apply_reconciliation_operation(
        ReconciliationState(dependents=dependents), commit
    )
    work_by_id = {
        item.dependent_id: item for item in reconciliation.state.work
    }
    # Only the actual dependent enters narrow reconciliation work.
    assert set(work_by_id) == {"dependent:new-button"}
    assert work_by_id["dependent:new-button"].status is WorkStatus.PENDING
    applied = reconciliation.state.corrections[0]
    assert applied.affected_dependents == ("dependent:new-button",)
    input_ids = {item.input_id for item in commit.corrected_inputs}
    assert input_ids == {
        f"knowledge:{claim_id}" for claim_id in outcome.corrected_claim_ids
    }


def test_apply_lifecycle_operation_remains_the_only_write_path() -> None:
    state = _state()
    outcome = apply_direct_edit(
        state,
        DirectEditRequest(
            edit_id="edit-final",
            authorship=MutationAuthorship(
                actor="user", source_id="edit-final", attributable=True
            ),
            claim_id="claim:typography",
            direction="warm humanist sans",
        ),
    )
    assert isinstance(outcome.transition.state, LifecycleState)
    assert outcome.transition.status is LifecycleStatus.APPLIED
