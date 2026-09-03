"""Behavioral scenarios for stakeholder ownership conflict resolution."""

from __future__ import annotations

import pytest

from alignment_contract import (
    AlignmentRequest,
    DecisionDirective,
    Disposition,
    EpistemicBasis,
    GoverningSource,
    PreferenceKnowledge,
    PropagationBlockedError,
    Provenance,
    Scope,
    ValidationContext,
    authorize_propagation,
    is_alignment_stale,
    resolve_alignment,
)
from profile_composition import (
    CompositionRequest,
    CompositionTarget,
    ProfileProperty,
    compose_profiles,
)
from profile_lifecycle import LifecycleState, initial_lifecycle_state
from profile_persistence import ProfileState
from reconciliation import (
    CommitCorrection,
    CorrectedInput,
    DecisionInputKind,
    DependentRecord,
    ReconciliationState,
    apply_reconciliation_operation,
)
from stakeholder_ownership import (
    GrantBasis,
    OwnershipGrant,
    StakeholderRole,
    StakeholderSignal,
    propagation_hold,
    resolve_stakeholder_ownership,
)


USER_SCOPE = Scope(kind="global", identity="user-1", represented_subject="user-1")
CLIENT_SCOPE = Scope(
    kind="project", identity="project-a", represented_subject="client:acme"
)

DIMENSION = "brand.expression"


def _grant(
    grant_id: str,
    owner: str,
    *,
    basis: GrantBasis = GrantBasis.PROJECT_AGREEMENT,
) -> OwnershipGrant:
    return OwnershipGrant(
        grant_id=grant_id,
        owner_subject=owner,
        dimensions=(DIMENSION,),
        basis=basis,
        provenance=(Provenance(actor="user", source_id=f"agreement:{grant_id}"),),
    )


def _signal(
    signal_id: str,
    stakeholder: str,
    role: StakeholderRole,
    direction: str,
) -> StakeholderSignal:
    return StakeholderSignal(
        signal_id=signal_id,
        role=role,
        stakeholder=stakeholder,
        dimension=DIMENSION,
        direction=direction,
        note=f"imported from {signal_id}",
    )


def _user_taste(direction: str) -> PreferenceKnowledge:
    return PreferenceKnowledge(
        dimension=DIMENSION,
        direction=direction,
        disposition=Disposition.PREFERRED,
        basis=EpistemicBasis.EXPLICIT,
        confidence=0.95,
        strength=0.8,
        scope=USER_SCOPE,
        context={},
        evidence=("user-taste-1#impl",),
        provenance=(Provenance(actor="user", source_id="message:user-taste-1"),),
        validation_context=ValidationContext(domain="interface-design",
                                             fidelity="high"),
        relationships={},
    )


CLIENT_SIGNAL = _signal(
    "signal:client-playful", "client:acme", StakeholderRole.CLIENT, "playful"
)
USER_TASTE_AUSTERE = _user_taste("austere")


def test_stakeholder_profiles_never_merge_into_user_taste() -> None:
    client_property = ProfileProperty(
        claim_id="claim:client-brand",
        section="brand",
        knowledge=PreferenceKnowledge(
            dimension=DIMENSION,
            direction="playful",
            disposition=Disposition.PREFERRED,
            basis=EpistemicBasis.EXPLICIT,
            confidence=0.9,
            strength=0.7,
            scope=CLIENT_SCOPE,
            context={},
            evidence=("client-event#impl",),
            provenance=(Provenance(actor="client", source_id="client-brief"),),
            validation_context=ValidationContext(domain="interface-design",
                                                 fidelity="high"),
            relationships={},
        ),
    )
    user_profile = ProfileState(
        schema_version=1,
        profile_id="profile:user-1",
        properties=(),
    )

    composition = compose_profiles(
        CompositionRequest(
            target=CompositionTarget(
                represented_subject="user-1",
                scope_identities={"project": "project-a"},
                domain="interface-design",
                context={},
                validation_conditions=("settings",),
                exposed_properties={"brand": (DIMENSION,)},
            ),
            properties=(client_property,),
        )
    )

    assert composition.properties == {}
    assert composition.excluded[0].reason == (
        "represented subject does not match this decision"
    )
    # The imported stakeholder knowledge never entered the user profile.
    state_after = initial_lifecycle_state(user_profile)
    assert isinstance(state_after, LifecycleState)
    assert state_after.profile.properties == ()


def test_explicit_ownership_resolves_competing_directions() -> None:
    resolution = resolve_stakeholder_ownership(
        (DIMENSION,),
        grants=(_grant("grant:agreement-a", "client:acme"),),
        signals=(CLIENT_SIGNAL,),
        default_owner="user-1",
    )

    assert resolution.ambiguous_dimensions == ()
    directive = resolution.ownership_directives[0]
    assert directive.scope is not None
    assert directive.dimension == DIMENSION
    assert directive.direction == "playful"
    assert directive.scope.represented_subject == "client:acme"
    assert directive.dependencies == ("ownership:grant:agreement-a",)

    request = AlignmentRequest(
        decision_id="decision:landing",
        dimensions=(DIMENSION,),
        material=True,
        taste=(USER_TASTE_AUSTERE,),
        ownership=resolution.ownership_directives,
    )
    resolved = resolve_alignment(request)
    assert resolved.dimensions[DIMENSION].governing_source is (
        GoverningSource.OWNERSHIP
    )
    assert resolved.dimensions[DIMENSION].direction == "playful"


def test_resolution_follows_agreements_not_a_universal_precedence() -> None:
    client_owned = resolve_stakeholder_ownership(
        (DIMENSION,),
        grants=(_grant("grant:a", "client:acme"),),
        signals=(CLIENT_SIGNAL,),
        default_owner="user-1",
    )
    user_retained = resolve_stakeholder_ownership(
        (DIMENSION,),
        grants=(
            _grant(
                "grant:b",
                "user-1",
                basis=GrantBasis.RETAINED_AUTHORITY,
            ),
        ),
        signals=(CLIENT_SIGNAL,),
        default_owner="user-1",
    )

    client_project = resolve_alignment(
        AlignmentRequest(
            decision_id="decision:client-project",
            dimensions=(DIMENSION,),
            material=True,
            taste=(USER_TASTE_AUSTERE,),
            ownership=client_owned.ownership_directives,
        )
    )
    retained_project = resolve_alignment(
        AlignmentRequest(
            decision_id="decision:own-project",
            dimensions=(DIMENSION,),
            material=True,
            taste=(USER_TASTE_AUSTERE,),
            ownership=user_retained.ownership_directives,
        )
    )

    # Identical roles and signals; only the explicit agreements differ.
    assert client_project.dimensions[DIMENSION].direction == "playful"
    assert retained_project.dimensions[DIMENSION].governing_source is (
        GoverningSource.TASTE
    )
    assert retained_project.dimensions[DIMENSION].direction == "austere"
    assert user_retained.excluded_signals[0].reason


def test_signal_without_ownership_cannot_override_the_applicable_owner() -> None:
    team_signal = _signal(
        "signal:team-minimal", "team:design", StakeholderRole.TEAM, "minimalist"
    )
    resolution = resolve_stakeholder_ownership(
        (DIMENSION,),
        grants=(_grant("grant:agreement-c", "client:acme"),),
        signals=(CLIENT_SIGNAL, team_signal),
        default_owner="user-1",
    )

    exclusions = {
        item.signal.signal_id: item.reason for item in resolution.excluded_signals
    }
    assert "signal:team-minimal" in exclusions
    directive = resolution.ownership_directives[0]
    assert directive.direction == CLIENT_SIGNAL.direction
    # The directive cites the owning grant and the client's signal.
    assert directive.provenance[0].source_id.endswith("grant:agreement-c")
    assert directive.provenance[0].actor == f"signal:{CLIENT_SIGNAL.signal_id}"

    request = AlignmentRequest(
        decision_id="decision:dashboard",
        dimensions=(DIMENSION,),
        material=True,
        taste=(USER_TASTE_AUSTERE,),
        ownership=resolution.ownership_directives,
    )
    assert resolve_alignment(request).dimensions[DIMENSION].direction == "playful"


def test_hard_constraints_bound_the_space_before_ownership_resolves() -> None:
    resolution = resolve_stakeholder_ownership(
        (DIMENSION,),
        grants=(_grant("grant:agreement-d", "client:acme"),),
        signals=(CLIENT_SIGNAL,),
        default_owner="user-1",
    )
    constraint_directive = DecisionDirective(
        dimension=DIMENSION,
        direction="contrast-at-least-4.5",
        reason="accessibility requirement WCAG AA",
        provenance=(Provenance(actor="system", source_id="policy:wcag"),),
        dependencies=("constraint:wcag",),
    )

    resolved = resolve_alignment(
        AlignmentRequest(
            decision_id="decision:cta",
            dimensions=(DIMENSION,),
            material=True,
            constraints=(constraint_directive,),
            taste=(USER_TASTE_AUSTERE,),
            ownership=resolution.ownership_directives,
        )
    )

    assert resolved.dimensions[DIMENSION].governing_source is (
        GoverningSource.CONSTRAINT
    )


def test_materially_ambiguous_ownership_checkpoints_before_propagation() -> None:
    resolution = resolve_stakeholder_ownership(
        (DIMENSION,),
        grants=(
            _grant("grant:conflict-1", "client:acme"),
            _grant("grant:conflict-2", "designer:lee"),
        ),
        signals=(CLIENT_SIGNAL,),
        default_owner="user-1",
    )

    assert resolution.ambiguous_dimensions == (DIMENSION,)
    assert resolution.ownership_directives == ()
    hold = propagation_hold(resolution, revision="policy-rev-1")
    assert hold is not None

    request = AlignmentRequest(
        decision_id="decision:hero",
        dimensions=(DIMENSION,),
        material=True,
        taste=(USER_TASTE_AUSTERE,),
        propagation_policy=hold,
    )
    resolved = resolve_alignment(request)
    # Ownership stays explicitly unresolved and blocks load-bearing work
    # even though the user's own stored taste exists.
    assert f"resolve-ownership:{DIMENSION}" in resolved.checkpoint_obligations
    assert resolved.propagation_eligible is False
    with pytest.raises(PropagationBlockedError):
        authorize_propagation(resolved, request)


def test_ownership_correction_reconciles_only_actual_dependents() -> None:
    before_grants = (_grant("grant:rev-1", "client:acme"),)
    after_grants = (
        _grant(
            "grant:rev-2",
            "user-1",
            basis=GrantBasis.RETAINED_AUTHORITY,
        ),
    )
    before = resolve_stakeholder_ownership(
        (DIMENSION,),
        grants=before_grants,
        signals=(CLIENT_SIGNAL,),
        default_owner="user-1",
    )
    after = resolve_stakeholder_ownership(
        (DIMENSION,),
        grants=after_grants,
        signals=(CLIENT_SIGNAL,),
        default_owner="user-1",
    )

    old_request = AlignmentRequest(
        decision_id="decision:campaign",
        dimensions=(DIMENSION,),
        material=True,
        taste=(USER_TASTE_AUSTERE,),
        ownership=before.ownership_directives,
    )
    new_request = AlignmentRequest(
        decision_id="decision:campaign",
        dimensions=(DIMENSION,),
        material=True,
        taste=(USER_TASTE_AUSTERE,),
        ownership=after.ownership_directives,
    )
    old_result = resolve_alignment(old_request)
    assert is_alignment_stale(old_result, new_request)

    commit = CommitCorrection(
        operation_id="correction:ownership-revoked",
        corrected_inputs=(
            CorrectedInput(
                input_id="ownership:grant:rev-1",
                kind=DecisionInputKind.OWNERSHIP,
            ),
        ),
        basis_revision="basis-rev-2",
    )
    dependents = (
        DependentRecord(
            dependent_id="dependent:campaign-hero",
            decision_id="decision:campaign",
            input_dependencies=("ownership:grant:rev-1",),
        ),
        DependentRecord(
            dependent_id="dependent:footer",
            decision_id="decision:footer",
            input_dependencies=("taste:something-else",),
        ),
    )
    transition = apply_reconciliation_operation(
        ReconciliationState(dependents=dependents), commit
    )
    assert set(item.dependent_id for item in transition.state.work) == {
        "dependent:campaign-hero"
    }


def test_approval_of_stakeholder_work_is_not_personal_taste_evidence() -> None:
    from reconciliation import (
        ArtifactComparison,
        ArtifactJudgment,
        ChallengeApprovedArtifact,
        ComparisonFidelity,
        StoredTasteDirection,
    )

    stored_user_taste = StoredTasteDirection(
        dimension=DIMENSION,
        direction="austere",
        input_id="knowledge:user-taste-1",
        established=True,
    )
    artifact = ArtifactComparison(
        artifact_id="artifact:client-banner",
        observed=_observed_dimension_values(),
        judgment=ArtifactJudgment.PREFERRED,
        fidelity=ComparisonFidelity.HIGH,
        attributable=True,
        scope_matches=True,
        context_matches=True,
        ownership_matches=False,
    )
    operation = ChallengeApprovedArtifact(
        operation_id="challenge:client-banner",
        targets=(stored_user_taste,),
        artifact=artifact,
        basis_revision="basis-r9",
    )
    transition = apply_reconciliation_operation(
        ReconciliationState(), operation
    )

    assessment = transition.challenge
    assert assessment is not None
    assert assessment.outcome.value == "not_comparable"
    assert any("different owner" in reason for reason in assessment.reasons)
    assert transition.state.corrections == ()


def _observed_dimension_values():
    from reconciliation import DimensionValue

    return (DimensionValue(DIMENSION, "playful"),)
