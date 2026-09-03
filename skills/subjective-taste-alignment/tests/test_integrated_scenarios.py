"""Integrated behavioral scenarios spanning multiple features.

These scenarios exercise the finished skill across interacting behaviors:
reference freshness, stakeholder ownership, lifecycle resets, evidence
contradictions, checkpoint-heavy authority with ambiguous delegation and
aggregate materiality, branch isolation with export/import and undo,
and domain adapters routing reference intent and craft through one core.
"""

from __future__ import annotations

import pytest
from dataclasses import replace

from alignment_contract import (
    AlignmentRequest,
    AuthorityScope,
    DecisionDirective,
    Disposition,
    EpistemicBasis,
    GoverningSource,
    PreferenceKnowledge,
    PropagationBlockedError,
    Provenance,
    Scope,
    ValidationContext,
    is_alignment_stale,
    resolve_alignment,
)
from decision_policy import (
    AggregateProvisionalDirection,
    AutonomyPreset,
    DecisionContext,
    DecisionLevel,
    Delegation,
    DelegationOption,
    PolicyRequest,
    ProvisionalChoice,
    authorize_policy_propagation,
    autonomy_snapshot,
    resolve_policy_alignment,
)
from domain_adapters import (
    CraftTechnique,
    DomainAdapter,
    ui_contrast_pair_construction,
)
from evidence_reconciliation import (
    Ambiguity,
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
from profile_control import ManagementKind, ManagementRequest, manage_profile
from profile_lifecycle import (
    CreateBranch,
    ImportProfileExchange,
    IngestProfileEvidence,
    LifecycleStatus,
    UndoLastOperation,
    apply_lifecycle_operation,
    export_profile_exchange,
    initial_lifecycle_state,
)
from profile_persistence import (
    CURRENT_SCHEMA_VERSION,
    ProfileState,
    ReferenceFreshness,
    ReferenceMode,
    ReferenceSource,
)
from reconciliation import (
    CommitCorrection,
    CorrectedInput,
    DecisionInputKind,
    DependentRecord,
    ReconciliationState,
    apply_reconciliation_operation,
)
from reference_style import observe_live_state
from stakeholder_ownership import (
    GrantBasis,
    OwnershipGrant,
    StakeholderRole,
    StakeholderSignal,
    resolve_stakeholder_ownership,
)


PROJECT_SCOPE = Scope(kind="project", identity="project-a", represented_subject="user-1")
DIMENSION = "brand.expression"


def _knowledge(
    dimension: str,
    direction: str,
    scope: Scope = PROJECT_SCOPE,
) -> PreferenceKnowledge:
    return PreferenceKnowledge(
        dimension=dimension,
        direction=direction,
        disposition=Disposition.PREFERRED,
        basis=EpistemicBasis.EXPLICIT,
        confidence=0.95,
        strength=0.8,
        scope=scope,
        context={},
        evidence=("event-1#impl-1",),
        provenance=(Provenance(actor="user", source_id="message:event-1"),),
        validation_context=ValidationContext(domain="interface-design",
                                             fidelity="high"),
        relationships={},
    )


def _directive(
    dimension: str,
    direction: str,
    reason: str,
    dependencies: tuple[str, ...] = (),
) -> DecisionDirective:
    return DecisionDirective(
        dimension=dimension,
        direction=direction,
        reason=reason,
        provenance=(Provenance(actor="agent", source_id=f"src:{dimension}"),),
        dependencies=dependencies,
    )


def _authority(*dimensions: str) -> AuthorityScope:
    return AuthorityScope(
        actor="agent",
        dimensions=dimensions,
        allows_material_propagation=True,
        checkpoint_required=False,
        scope=PROJECT_SCOPE,
        provenance=(Provenance(actor="user", source_id="preset-selection"),),
    )


def test_live_reference_change_stales_and_repairs_only_its_dependents() -> None:
    live_style = ReferenceSource(
        reference_id="ref:live-style",
        source_identity="artifact:home",
        locator="workspace/home",
        mode=ReferenceMode.LIVE,
        freshness=ReferenceFreshness.CURRENT,
        source_revision="rev-3",
        derived_claim_ids=("reference-intent:layout.density",),
    )
    pinned_heritage = ReferenceSource(
        reference_id="ref:heritage",
        source_identity="artifact:archive-page",
        locator="workspace/archive",
        mode=ReferenceMode.PINNED,
        freshness=ReferenceFreshness.CURRENT,
        source_revision="rev-1",
        derived_claim_ids=("reference-intent:motion.transition",),
    )
    intent = (
        _directive(
            "layout.density",
            "airy",
            "reference-derived intent from ref:live-style",
            ("reference:ref:live-style",),
        ),
        _directive(
            "motion.transition",
            "gentle",
            "reference-derived intent from ref:heritage",
            ("reference:ref:heritage",),
        ),
    )
    request = AlignmentRequest(
        decision_id="decision:new-screen",
        dimensions=("layout.density", "motion.transition"),
        material=True,
        intent=intent,
    )
    resolved = resolve_alignment(request)

    # The live source moves; the pinned source is untouched.
    check = observe_live_state(live_style, observed_revision="rev-9")
    assert check.resulting_freshness is ReferenceFreshness.STALE
    assert check.stale_claim_ids == ("reference-intent:layout.density",)

    refreshed_intent = (
        _directive(
            "layout.density",
            "denser grid",
            "re-derived from rev-9",
            ("reference:ref:live-style",),
        ),
        intent[1],
    )
    new_request = replace(request, intent=refreshed_intent)
    assert is_alignment_stale(resolved, new_request)
    re_resolved = resolve_alignment(new_request)
    assert re_resolved.dimensions["layout.density"].direction == "denser grid"
    # Only decisions actually depending on the live reference need repair;
    # the heritage-dependent directive is byte-identical before and after.
    assert new_request.intent[1] == request.intent[1]
    assert pinned_heritage.source_revision == "rev-1"


def test_stakeholder_revocation_flows_through_canonical_reconciliation() -> None:
    resolution_before = resolve_stakeholder_ownership(
        (DIMENSION,),
        grants=(
            OwnershipGrant(
                grant_id="grant:r1",
                owner_subject="client:acme",
                dimensions=(DIMENSION,),
                basis=GrantBasis.PROJECT_AGREEMENT,
                provenance=(Provenance(actor="user", source_id="agreement"),),
            ),
        ),
        signals=(
            StakeholderSignal(
                signal_id="signal:c1",
                role=StakeholderRole.CLIENT,
                stakeholder="client:acme",
                dimension=DIMENSION,
                direction="playful",
                note="kickoff workshop",
            ),
        ),
        default_owner="user-1",
    )
    old_request = AlignmentRequest(
        decision_id="decision:campaign",
        dimensions=(DIMENSION,),
        material=True,
        taste=(_knowledge(DIMENSION, "austere"),),
        ownership=resolution_before.ownership_directives,
    )
    old_result = resolve_alignment(old_request)
    assert old_result.dimensions[DIMENSION].governing_source is (
        GoverningSource.OWNERSHIP
    )

    resolution_after = resolve_stakeholder_ownership(
        (DIMENSION,),
        grants=(
            OwnershipGrant(
                grant_id="grant:r2",
                owner_subject="user-1",
                dimensions=(DIMENSION,),
                basis=GrantBasis.RETAINED_AUTHORITY,
                provenance=(Provenance(actor="user", source_id="revocation"),),
            ),
        ),
        signals=(),
        default_owner="user-1",
    )
    new_request = replace(
        old_request,
        ownership=resolution_after.ownership_directives,
    )
    assert is_alignment_stale(old_result, new_request)

    commit = CommitCorrection(
        operation_id="correction:grant-revoked",
        corrected_inputs=(
            CorrectedInput(
                input_id="ownership:grant:r1",
                kind=DecisionInputKind.OWNERSHIP,
            ),
        ),
        basis_revision="basis-r2",
    )
    dependents = (
        DependentRecord(
            dependent_id="dependent:hero",
            decision_id="decision:campaign",
            input_dependencies=("ownership:grant:r1",),
        ),
        DependentRecord(
            dependent_id="dependent:footer",
            decision_id="decision:footer",
            input_dependencies=("taste:unrelated",),
        ),
    )
    transition = apply_reconciliation_operation(
        ReconciliationState(dependents=dependents), commit
    )
    assert set(item.dependent_id for item in transition.state.work) == {
        "dependent:hero"
    }


def test_contradiction_then_targeted_reset_keep_unrelated_claims_usable() -> None:
    event_a = EvidenceEvent(
        event_id="event-a",
        evidence_type=EvidenceType.EXPLICIT_FEEDBACK,
        feedback=FeedbackKind.CORRECTION,
        judgment=Judgment.PREFERRED,
        scope=PROJECT_SCOPE,
        context=(),
        provenance=(Provenance(actor="user", source_id="message:a"),),
        validation_context=ValidationContext(domain="interface-design",
                                             fidelity="high"),
        occurred_at=1,
        implications=(
            EvidenceImplication(
                implication_id="impl-typography",
                claim=PointClaim(
                    dimension="typography.expression",
                    direction="grotesque",
                    disposition=Disposition.PREFERRED,
                ),
                basis=EpistemicBasis.EXPLICIT,
                represented_dimensions=("typography.expression",),
                fidelity=Fidelity.HIGH,
                required_fidelity=Fidelity.HIGH,
                ambiguity=Ambiguity.CLEAR,
                epistemic_strength=SupportStrength.STRONG,
                preference_strength=0.8,
                consequence=Consequence.MATERIAL,
            ),
        ),
    )
    profile = ProfileState(schema_version=CURRENT_SCHEMA_VERSION,
                           profile_id="profile:user-1")
    state = initial_lifecycle_state(profile, EvidenceState(events=(event_a,)))

    reset_outcome = manage_profile(
        state,
        ManagementRequest(
            operation_id="mgmt:integrated-reset",
            instruction_id="instruction:reset-typography",
            kind=ManagementKind.RESET,
            scope=PROJECT_SCOPE,
            support=SupportRef("event-a", "impl-typography"),
        ),
    )
    transition = reset_outcome.transition
    assert transition is not None
    assert transition.status is LifecycleStatus.APPLIED
    records = transition.state.evidence.support_lifecycle
    assert records[-1].applicability is SupportApplicability.RESET_EXCLUDED
    assert any(
        record.support == SupportRef("event-a", "impl-typography")
        for record in records
    )
    # The audit history survives the targeted lifecycle change.
    assert any(
        event.event_id == "event-a"
        for event in transition.state.evidence.events
    )


def test_checkpoint_heavy_authority_with_delegation_and_aggregates() -> None:
    def delegated(*dimensions: str) -> AuthorityScope:
        return AuthorityScope(
            actor="agent",
            dimensions=dimensions,
            allows_material_propagation=True,
            checkpoint_required=False,
            scope=PROJECT_SCOPE,
            provenance=(
                Provenance(actor="user", source_id="instruction:finish-the-rest"),
            ),
        )

    narrow = DelegationOption("this-section", delegated("visual-direction"))
    broad = DelegationOption(
        "whole-project",
        delegated("visual-direction", "spacing.scale", "motion.transition"),
    )
    aggregate = AggregateProvisionalDirection(
        aggregate_id="aggregate:landing",
        choice_ids=("choice-a", "choice-b"),
    )
    choices = tuple(
        ProvisionalChoice(
            choice_id=choice_id,
            dimension="visual-direction",
            direction=direction,
            provenance=(Provenance(actor="agent", source_id=f"j:{choice_id}"),),
            dependencies=("artifact:landing",),
        )
        for choice_id, direction in (
            ("choice-a", "editorial"),
            ("choice-b", "brutalist"),
        )
    )
    request = PolicyRequest(
        alignment=AlignmentRequest(
            decision_id="decision:landing-family",
            dimensions=("visual-direction", "spacing.scale"),
            material=False,
        ),
        autonomy=autonomy_snapshot(
            AutonomyPreset.HIGH_INTERVENTION,
            authority_scope=_authority("visual-direction", "spacing.scale"),
            revision="high-intervention-1",
            effective_from_sequence=7,
        ),
        decision=DecisionContext(
            sequence=7,
            target="landing-family",
            level=DecisionLevel.DIRECTION,
        ),
        provisional_choices=choices,
        aggregate=aggregate,
        delegation=Delegation(
            instruction_id="instruction:finish-the-rest",
            options=(narrow, broad),
        ),
    )

    resolution = resolve_policy_alignment(request)

    keys = [checkpoint.key for checkpoint in resolution.checkpoints]
    # Checkpoint-heavy authority checkpoints the direction selection, and the
    # ambiguous delegation stays unresolved behind an extension checkpoint.
    assert "select-direction" in keys
    assert "extend-authority:instruction:finish-the-rest" in keys
    # Only the narrowest clearly supported delegation reading applies.
    assert narrow.authority in resolution.alignment_request.authority
    assert broad.authority not in resolution.alignment_request.authority
    # The aggregate of two interacting provisional assumptions is
    # presumptively load-bearing even though each choice looks cheap.
    assert resolution.materiality.load_bearing is True
    assert resolution.materiality.reasons == ("aggregate-provisional-direction",)
    with pytest.raises(PropagationBlockedError):
        authorize_policy_propagation(resolution, request)


def test_branch_isolation_survives_export_import_and_undo() -> None:
    profile = ProfileState(schema_version=CURRENT_SCHEMA_VERSION,
                           profile_id="profile:user-1")

    def branch_event(event_id: str) -> EvidenceEvent:
        return EvidenceEvent(
            event_id=event_id,
            evidence_type=EvidenceType.EXPLICIT_FEEDBACK,
            feedback=FeedbackKind.CORRECTION,
            judgment=Judgment.PREFERRED,
            scope=PROJECT_SCOPE,
            context=(),
            provenance=(Provenance(actor="user", source_id=f"m:{event_id}"),),
            validation_context=ValidationContext(domain="interface-design",
                                                 fidelity="high"),
            occurred_at=3,
            implications=(
                EvidenceImplication(
                    implication_id=f"{event_id}-impl",
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

    state = initial_lifecycle_state(profile)
    state = apply_lifecycle_operation(
        state,
        CreateBranch(
            operation_id="op:open-b",
            branch_id="branch-b",
            provenance=(
                Provenance(actor="user", source_id="instruction:open-b"),
            ),
        ),
    ).state
    state = apply_lifecycle_operation(
        state,
        IngestProfileEvidence(
            operation_id="op:ingest-b",
            event=replace(
                branch_event("branch-event"),
                implications=(
                    replace(
                        branch_event("branch-event").implications[0],
                        applicable_branches=("branch-b",),
                    ),
                ),
            ),
        ),
    ).state

    exchange = export_profile_exchange(state)
    imported = apply_lifecycle_operation(
        initial_lifecycle_state(
            ProfileState(schema_version=CURRENT_SCHEMA_VERSION,
                         profile_id="profile:copy")
        ),
        ImportProfileExchange(operation_id="op:import-1", exchange=exchange),
    )
    assert imported.status is LifecycleStatus.APPLIED
    assert [event.event_id for event in imported.state.evidence.events] == [
        "branch-event"
    ]
    replayed = apply_lifecycle_operation(
        imported.state,
        ImportProfileExchange(operation_id="op:import-1", exchange=exchange),
    )
    assert replayed.status is LifecycleStatus.REPLAYED

    undone = apply_lifecycle_operation(
        imported.state,
        UndoLastOperation(operation_id="op:undo-import"),
    )
    # Undoing the import restores the receiving profile's pre-import state.
    assert undone.status is LifecycleStatus.UNDONE
    assert undone.state.evidence.events == ()


def test_adapters_route_reference_intent_and_craft_through_one_core() -> None:
    adapter = DomainAdapter(
        domain="ui",
        craft_techniques=(
            CraftTechnique(
                technique_id="tech:contrast-first",
                dimension="color.palette",
                direction="high-contrast neutrals",
                rationale="readability improves perceived quality",
            ),
        ),
    )
    craft_priors = adapter.craft_priors()
    reference_directive = _directive(
        "typography.expression",
        "restrained grotesque",
        "reference-derived intent from ref:settings-ui",
    )
    accessibility = DecisionDirective(
        dimension="accessibility.contrast",
        direction="minimum-ratio-4.5",
        reason="WCAG AA requirement",
        provenance=(Provenance(actor="system", source_id="policy:wcag"),),
        dependencies=("constraint:wcag",),
    )

    resolved = resolve_alignment(
        AlignmentRequest(
            decision_id="decision:ui-button",
            dimensions=(
                "typography.expression",
                "color.palette",
                "accessibility.contrast",
            ),
            material=True,
            constraints=(accessibility,),
            intent=(reference_directive,),
            craft_priors=craft_priors,
            authority=(_authority("color.palette"),),
        )
    )

    assert resolved.dimensions["accessibility.contrast"].governing_source is (
        GoverningSource.CONSTRAINT
    )
    typography = resolved.dimensions["typography.expression"]
    assert typography.governing_source is GoverningSource.INTENT
    assert typography.taste is None
    # Craft knowledge stays a prior under delegated authority, never taste.
    color = resolved.dimensions["color.palette"]
    assert color.governing_source in {GoverningSource.CRAFT_PRIOR}
    assert color.taste is None
    constructions = (
        ui_contrast_pair_construction(
            probe_id="probe:palette-pair",
            foreground="#111",
            background="#eee",
            resolves=("color.palette",),
            representative_dimensions=("color.palette",),
            cost=2,
        ),
    )
    assert constructions[0].option.probe_id == "probe:palette-pair"
