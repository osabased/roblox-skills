from dataclasses import replace

from alignment_contract import (
    AlignmentRequest,
    AuthorityScope,
    DecisionDirective,
    Disposition,
    EpistemicBasis,
    GoverningSource,
    PreferenceKnowledge,
    Provenance,
    Scope,
    ValidationContext,
)
from decision_policy import (
    AutonomyPreset,
    AutonomySnapshot,
    CheckpointPurpose,
    DecisionContext,
    DecisionLevel,
    Delegation,
    DelegationOption,
    DirectionCandidate,
    DirectionSpace,
    PolicyRequest,
    ProbeDecision,
    ProbeFidelity,
    ProbeOption,
    PropagationRoute,
    ProvisionalChoice,
    Uncertainty,
    UncertaintyWeight,
    AggregateProvisionalDirection,
    authorize_policy_propagation,
    autonomy_snapshot,
    resolve_policy_alignment,
)


PROJECT_SCOPE = Scope(
    kind="project",
    identity="project-a",
    represented_subject="user-1",
)


def authority(*dimensions: str) -> AuthorityScope:
    return AuthorityScope(
        actor="agent",
        dimensions=dimensions,
        allows_material_propagation=True,
        checkpoint_required=False,
        scope=PROJECT_SCOPE,
        provenance=(Provenance(actor="user", source_id="preset-selection"),),
    )


def preset_request(preset: AutonomyPreset) -> PolicyRequest:
    return PolicyRequest(
        alignment=AlignmentRequest(
            decision_id="hero-direction",
            dimensions=("visual-direction",),
            material=True,
        ),
        autonomy=autonomy_snapshot(
            preset,
            authority_scope=authority("visual-direction"),
            revision=f"{preset.value}-1",
            effective_from_sequence=4,
        ),
        decision=DecisionContext(
            sequence=4,
            target="hero-family",
            level=DecisionLevel.DIRECTION,
            shared=True,
            salient=True,
            milestone_due=True,
        ),
        provisional_choices=(
            ProvisionalChoice(
                choice_id="hero-direction-a",
                dimension="visual-direction",
                direction="editorial",
                provenance=(
                    Provenance(actor="agent", source_id="judgment:hero-a"),
                ),
                dependencies=("artifact:hero",),
            ),
        ),
    )


def test_five_presets_share_controls_but_produce_distinct_checkpoint_contracts() -> None:
    resolutions = {
        preset: resolve_policy_alignment(preset_request(preset))
        for preset in AutonomyPreset
    }

    assert {
        preset: (
            resolution.alignment_request.authority[0],
            resolution.checkpoints,
        )
        for preset, resolution in resolutions.items()
    } == {
        AutonomyPreset.AGENT_LED: (authority("visual-direction"), ()),
        AutonomyPreset.DIRECTION_CHECKPOINT: (
            authority("visual-direction"),
            (resolutions[AutonomyPreset.DIRECTION_CHECKPOINT].checkpoints[0],),
        ),
        AutonomyPreset.MILESTONE_CHECKPOINT: (
            authority("visual-direction"),
            (resolutions[AutonomyPreset.MILESTONE_CHECKPOINT].checkpoints[0],),
        ),
        AutonomyPreset.ELEMENT_LEVEL: (
            authority("visual-direction"),
            (resolutions[AutonomyPreset.ELEMENT_LEVEL].checkpoints[0],),
        ),
        AutonomyPreset.HIGH_INTERVENTION: (
            authority("visual-direction"),
            resolutions[AutonomyPreset.HIGH_INTERVENTION].checkpoints,
        ),
    }
    assert [
        checkpoint.key
        for checkpoint in resolutions[
            AutonomyPreset.DIRECTION_CHECKPOINT
        ].checkpoints
    ] == ["select-direction"]
    assert [
        checkpoint.key
        for checkpoint in resolutions[
            AutonomyPreset.MILESTONE_CHECKPOINT
        ].checkpoints
    ] == ["review-milestone"]
    assert [
        checkpoint.key
        for checkpoint in resolutions[AutonomyPreset.ELEMENT_LEVEL].checkpoints
    ] == ["review-element-family:hero-family"]
    assert [
        checkpoint.key
        for checkpoint in resolutions[
            AutonomyPreset.HIGH_INTERVENTION
        ].checkpoints
    ] == ["select-direction", "review-application:hero-family"]
    assert resolutions[AutonomyPreset.AGENT_LED].alignment.propagation_eligible
    agent_led_policy = (
        resolutions[AutonomyPreset.AGENT_LED]
        .alignment_request.propagation_policy
    )
    assert agent_led_policy is not None
    assert agent_led_policy.route == PropagationRoute.DELEGATED_AUTHORITY
    assert all(
        resolution.alignment_request.taste == ()
        for resolution in resolutions.values()
    )


def test_runtime_autonomy_change_is_prospective_and_preserves_completed_decision() -> None:
    completed_request = preset_request(AutonomyPreset.AGENT_LED)
    completed = resolve_policy_alignment(completed_request)
    lowered_autonomy = autonomy_snapshot(
        AutonomyPreset.HIGH_INTERVENTION,
        authority_scope=authority("visual-direction"),
        revision="high-intervention-2",
        effective_from_sequence=5,
    )
    preserved_completed = replace(
        completed_request,
        alignment=completed.alignment_request,
        autonomy=lowered_autonomy,
    )

    assert authorize_policy_propagation(completed, preserved_completed) is completed.alignment

    pending = replace(
        completed_request,
        autonomy=lowered_autonomy,
        decision=replace(completed_request.decision, sequence=5),
    )
    pending_resolution = resolve_policy_alignment(pending)

    assert pending_resolution.alignment.propagation_eligible is False
    assert [item.key for item in pending_resolution.checkpoints] == [
        "select-direction",
        "review-application:hero-family",
    ]
    assert completed.alignment.provenance == (
        Provenance(actor="agent", source_id="judgment:hero-a"),
        Provenance(actor="user", source_id="preset-selection"),
    )


def delegation_authority(
    *dimensions: str, allows_material_propagation: bool = True
) -> AuthorityScope:
    return AuthorityScope(
        actor="agent",
        dimensions=dimensions,
        allows_material_propagation=allows_material_propagation,
        checkpoint_required=False,
        scope=PROJECT_SCOPE,
        provenance=(Provenance(actor="user", source_id="finish-the-rest"),),
    )


def delegation_request(*options: DelegationOption) -> PolicyRequest:
    base = preset_request(AutonomyPreset.ELEMENT_LEVEL)
    return replace(
        base,
        decision=replace(
            base.decision,
            level=DecisionLevel.ELEMENT_FAMILY,
            milestone_due=False,
        ),
        delegation=Delegation(instruction_id="finish-the-rest", options=options),
    )


def test_ambiguous_delegation_expands_only_to_the_narrowest_supported_scope() -> None:
    family = DelegationOption(
        label="component-family",
        authority=delegation_authority("hero-card"),
    )
    whole_screen = DelegationOption(
        label="remaining-screen",
        authority=delegation_authority(
            "hero-card",
            "page-layout",
            "navigation",
        ),
    )

    resolved = resolve_policy_alignment(delegation_request(whole_screen, family))

    assert family.authority in resolved.alignment_request.authority
    assert whole_screen.authority not in resolved.alignment_request.authority
    assert [item.key for item in resolved.checkpoints] == [
        "review-element-family:hero-family",
        "extend-authority:finish-the-rest",
    ]
    extension = resolved.checkpoints[-1]
    assert isinstance(extension.purpose, CheckpointPurpose)
    assert extension.purpose.value == "discovery"
    assert "narrowest" in extension.reason
    assert (
        resolved.alignment_request.propagation_policy is not None
        and resolved.alignment_request.propagation_policy.eligible is False
    )


def test_unambiguous_delegation_applies_without_extension_checkpoint() -> None:
    single = DelegationOption(
        label="component-family",
        authority=delegation_authority("hero-card"),
    )
    equivalent = DelegationOption(
        label="rest-of-the-family",
        authority=delegation_authority("hero-card"),
    )

    resolved = resolve_policy_alignment(
        delegation_request(single, equivalent)
    )
    narrowed_only = resolve_policy_alignment(delegation_request(single))

    assert single.authority in resolved.alignment_request.authority
    assert all(
        item.key != "extend-authority:finish-the-rest"
        for item in resolved.checkpoints
    )
    assert single.authority in narrowed_only.alignment_request.authority


def test_delegated_selection_stays_authorized_judgment_not_taste() -> None:
    single = DelegationOption(
        label="component-family",
        authority=delegation_authority("visual-direction"),
    )

    resolved = resolve_policy_alignment(
        replace(
            delegation_request(single),
            alignment=replace(
                preset_request(AutonomyPreset.ELEMENT_LEVEL).alignment,
                dimensions=("visual-direction",),
            ),
        )
    )

    dimension = resolved.alignment.dimensions["visual-direction"]
    assert dimension.governing_source is GoverningSource.AUTHORIZED_JUDGMENT
    assert resolved.alignment_request.taste == ()


def _intent_governed_request(preset: AutonomyPreset) -> PolicyRequest:
    return PolicyRequest(
        alignment=AlignmentRequest(
            decision_id="hero-direction",
            dimensions=("visual-direction",),
            material=True,
            intent=(
                DecisionDirective(
                    dimension="visual-direction",
                    direction="editorial",
                    reason="the project brief fixes the visual direction",
                    provenance=(Provenance(actor="user", source_id="brief-1"),),
                ),
            ),
        ),
        autonomy=autonomy_snapshot(
            preset,
            authority_scope=authority("visual-direction"),
            revision=f"{preset.value}-intent-1",
            effective_from_sequence=0,
        ),
        decision=DecisionContext(
            sequence=0,
            target="hero-family",
            level=DecisionLevel.DIRECTION,
        ),
    )


def test_established_direction_bypasses_gratuitous_discovery() -> None:
    for preset in (
        AutonomyPreset.DIRECTION_CHECKPOINT,
        AutonomyPreset.HIGH_INTERVENTION,
    ):
        resolved = resolve_policy_alignment(_intent_governed_request(preset))
        assert resolved.direction.established is True, preset
        assert resolved.direction.discovery_required is False, preset
        assert all(
            checkpoint.key != "select-direction"
            for checkpoint in resolved.checkpoints
        ), preset
    governed = resolve_policy_alignment(
        _intent_governed_request(AutonomyPreset.DIRECTION_CHECKPOINT)
    )
    assert (
        governed.alignment.dimensions["visual-direction"].governing_source
        is GoverningSource.INTENT
    )


def direction_space() -> DirectionSpace:
    return DirectionSpace(
        candidates=(
            DirectionCandidate(
                candidate_id="editorial-calm",
                summary="calm editorial layout with restrained motion",
                distinguishing_dimensions=("visual-direction", "motion.intensity"),
            ),
            DirectionCandidate(
                candidate_id="playful-bold",
                summary="bold playful composition with expressive motion",
                distinguishing_dimensions=("visual-direction", "motion.intensity"),
            ),
        )
    )


def unresolved_direction_request(
    preset: AutonomyPreset,
    space: DirectionSpace | None,
) -> PolicyRequest:
    return replace(
        preset_request(preset),
        decision=replace(
            preset_request(preset).decision,
            milestone_due=preset is AutonomyPreset.MILESTONE_CHECKPOINT,
        ),
        direction=space,
    )


def test_unresolved_direction_compares_candidates_before_refinement() -> None:
    agent_led = resolve_policy_alignment(
        unresolved_direction_request(AutonomyPreset.AGENT_LED, direction_space())
    )
    assert agent_led.direction.discovery_required is True
    assert agent_led.direction.selection_actor == "agent"
    assert agent_led.direction.candidates == ("editorial-calm", "playful-bold")
    assert agent_led.direction.source == "direction-space"
    assert "materially distinct" in agent_led.direction.reason
    assert all(
        checkpoint.key != "select-direction"
        for checkpoint in agent_led.checkpoints
    )

    user_owned = resolve_policy_alignment(
        unresolved_direction_request(
            AutonomyPreset.DIRECTION_CHECKPOINT, direction_space()
        )
    )
    assert user_owned.direction.selection_actor == "user"
    assert any(
        checkpoint.key == "select-direction"
        and "materially distinct" in checkpoint.reason
        for checkpoint in user_owned.checkpoints
    )
    assert user_owned.alignment_request.taste == ()


def test_first_plausible_candidate_does_not_silently_define_the_search_space() -> None:
    none_supplied = resolve_policy_alignment(
        unresolved_direction_request(AutonomyPreset.AGENT_LED, None)
    )
    assert none_supplied.direction.candidates == ()
    assert none_supplied.direction.discovery_required is True
    assert "search space" in none_supplied.direction.reason

    try:
        DirectionSpace(
            candidates=(
                DirectionCandidate(
                    candidate_id="only-one",
                    summary="a single framing cannot be compared",
                ),
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError("a one-candidate space cannot support comparison")


def uncertainties_and_probes() -> tuple[tuple[Uncertainty, ...], tuple[ProbeOption, ...]]:
    uncertainties = (
        Uncertainty(
            uncertainty_id="u-detail",
            dimensions=("button.radius",),
            question="How rounded should secondary buttons feel?",
            weight=UncertaintyWeight.REVERSIBLE,
        ),
        Uncertainty(
            uncertainty_id="u-aggregate",
            dimensions=("hero.composition", "hero.density", "hero.motion"),
            question="Which hero composition bundle feels right overall?",
            weight=UncertaintyWeight.MATERIAL,
            aggregate_members=(
                "choice:composition-a",
                "choice:density-b",
                "choice:motion-c",
            ),
        ),
        Uncertainty(
            uncertainty_id="u-material",
            dimensions=("navigation.layout",),
            question="Should navigation stay top-fixed?",
            weight=UncertaintyWeight.MATERIAL,
        ),
    )
    probes = (
        ProbeOption(
            probe_id="probe-everything",
            resolves=("u-detail", "u-aggregate", "u-material"),
            cost=9,
            representative_dimensions=(
                "button.radius",
                "hero.composition",
                "hero.density",
                "hero.motion",
                "navigation.layout",
            ),
        ),
        ProbeOption(
            probe_id="probe-aggregate-composite",
            resolves=("u-aggregate",),
            cost=2,
            representative_dimensions=(
                "hero.composition",
                "hero.density",
                "hero.motion",
            ),
        ),
        ProbeOption(
            probe_id="probe-button-only",
            resolves=("u-detail",),
            cost=1,
            representative_dimensions=("button.radius",),
        ),
    )
    return uncertainties, probes


def test_probe_selection_targets_the_highest_value_uncertainty_cheaply() -> None:
    uncertainties, probes = uncertainties_and_probes()
    base = preset_request(AutonomyPreset.AGENT_LED)
    resolved = resolve_policy_alignment(
        replace(base, uncertainties=uncertainties, probes=probes)
    )

    assert resolved.probe.uncertainty_ids == ("u-aggregate",)
    assert resolved.probe.probe_id == "probe-aggregate-composite"
    assert resolved.probe.evidence_granularity == "representative"
    assert "highest-value" in resolved.probe.reason


def test_aggregate_uncertainty_outranks_equal_weight_single_choice() -> None:
    uncertainties, probes = uncertainties_and_probes()
    without_aggregate_flag = tuple(
        item if item.uncertainty_id != "u-material" else replace(item)
        for item in uncertainties
    )
    base = preset_request(AutonomyPreset.AGENT_LED)
    resolved = resolve_policy_alignment(
        replace(base, uncertainties=without_aggregate_flag, probes=probes)
    )

    assert resolved.probe.uncertainty_ids == ("u-aggregate",)


def test_uncovered_top_uncertainty_requests_a_resolution_checkpoint() -> None:
    uncertainties, probes = uncertainties_and_probes()
    covering_only_detail = tuple(
        probe for probe in probes if probe.probe_id == "probe-button-only"
    )
    base = preset_request(AutonomyPreset.AGENT_LED)
    resolved = resolve_policy_alignment(
        replace(
            base,
            uncertainties=uncertainties,
            probes=covering_only_detail,
        )
    )

    assert resolved.probe.probe_id is None
    assert resolved.probe.fallback == "clarification-checkpoint"
    assert any(
        checkpoint.key == "resolve-uncertainty:u-aggregate"
        for checkpoint in resolved.checkpoints
    )


def _confirmed_taste(
    dimension: str = "visual-direction",
    direction: str = "editorial",
) -> PreferenceKnowledge:
    return PreferenceKnowledge(
        dimension=dimension,
        direction=direction,
        disposition=Disposition.PREFERRED,
        basis=EpistemicBasis.EXPLICIT,
        confidence=0.95,
        strength=0.8,
        scope=PROJECT_SCOPE,
        context={},
        evidence=("taste-1#explicit",),
        provenance=(Provenance(actor="user", source_id="taste-1"),),
        validation_context=ValidationContext(
            domain="interface-design", fidelity="high"
        ),
        relationships={},
    )


def test_established_taste_routes_propagation_without_bypassing_checkpoints() -> None:
    base = preset_request(AutonomyPreset.HIGH_INTERVENTION)
    request = replace(base, alignment=replace(base.alignment, taste=(_confirmed_taste(),)))
    resolved = resolve_policy_alignment(request)

    taste_resolved = resolved.alignment.dimensions["visual-direction"]
    assert taste_resolved.governing_source is GoverningSource.TASTE
    policy = resolved.alignment_request.propagation_policy
    assert policy is not None
    assert policy.route == PropagationRoute.ESTABLISHED_EVIDENCE
    # The route classifies the basis; stricter checkpoint obligations stand.
    assert any(
        checkpoint.key.startswith("review-application:")
        for checkpoint in resolved.checkpoints
    )
    assert resolved.alignment.propagation_eligible is False
    assert all(
        checkpoint.key != "select-direction" for checkpoint in resolved.checkpoints
    )


def test_hypothesis_taste_does_not_claim_the_established_route() -> None:
    hypothesis = replace(_confirmed_taste(), confidence=0.3)
    base = preset_request(AutonomyPreset.AGENT_LED)
    request = replace(base, alignment=replace(base.alignment, taste=(hypothesis,)))
    resolved = resolve_policy_alignment(request)

    policy = resolved.alignment_request.propagation_policy
    assert policy is not None
    assert policy.route != PropagationRoute.ESTABLISHED_EVIDENCE


def test_aggregate_provisional_direction_is_load_bearing() -> None:
    base = preset_request(AutonomyPreset.AGENT_LED)
    request = replace(
        base,
        alignment=replace(base.alignment, material=False),
        decision=replace(
            base.decision, shared=False, salient=False, milestone_due=False
        ),
        aggregate=AggregateProvisionalDirection(
            aggregate_id="aggregate:hero-details",
            choice_ids=("choice:a", "choice:b", "choice:c"),
        ),
    )
    resolved = resolve_policy_alignment(request)

    assert resolved.materiality.load_bearing is True
    assert "aggregate-provisional-direction" in resolved.materiality.reasons
    assert resolved.materiality.aggregate_choice_ids == (
        "choice:a",
        "choice:b",
        "choice:c",
    )


def test_non_reconstructable_provisional_basis_is_reresolved_not_fabricated() -> None:
    lost_basis = ProvisionalChoice(
        choice_id="hero-lost",
        dimension="visual-direction",
        direction="editorial",
        provenance=(),
        basis_reconstructable=False,
    )
    intact = ProvisionalChoice(
        choice_id="hero-intact",
        dimension="visual-direction",
        direction="editorial",
        provenance=(Provenance(actor="agent", source_id="judgment:kept"),),
    )
    base = preset_request(AutonomyPreset.AGENT_LED)

    with_lost = resolve_policy_alignment(
        replace(base, provisional_choices=(lost_basis,))
    )
    with_intact = resolve_policy_alignment(
        replace(base, provisional_choices=(intact,))
    )

    assert with_lost.alignment_request.provisional_judgments == ()
    lost_source = with_lost.alignment.dimensions["visual-direction"].governing_source
    assert lost_source is not GoverningSource.AUTHORIZED_JUDGMENT
    assert with_lost.direction.discovery_required is True

    assert len(with_intact.alignment_request.provisional_judgments) == 1
    intact_source = with_intact.alignment.dimensions["visual-direction"].governing_source
    assert intact_source is GoverningSource.AUTHORIZED_JUDGMENT


def test_probe_must_match_shape_and_fidelity_of_the_uncertainty() -> None:
    uncertainties, probes = uncertainties_and_probes()
    aggregate_only = tuple(
        item for item in uncertainties if item.uncertainty_id == "u-aggregate"
    )
    base = preset_request(AutonomyPreset.AGENT_LED)

    unfaithful = (
        ProbeOption(
            probe_id="probe-cheap-half-shape",
            resolves=("u-aggregate",),
            cost=1,
            representative_dimensions=("hero.composition",),
            fidelity=ProbeFidelity.HIGH,
        ),
    )
    rejected_shape = resolve_policy_alignment(
        replace(base, uncertainties=aggregate_only, probes=unfaithful)
    )
    assert rejected_shape.probe.probe_id is None
    assert rejected_shape.probe.fallback == "clarification-checkpoint"
    assert any(
        checkpoint.key == "resolve-uncertainty:u-aggregate"
        for checkpoint in rejected_shape.checkpoints
    )

    faithful_high_cost = (
        ProbeOption(
            probe_id="probe-faithful",
            resolves=("u-aggregate",),
            cost=7,
            representative_dimensions=(
                "hero.composition",
                "hero.density",
                "hero.motion",
            ),
            fidelity=ProbeFidelity.HIGH,
        ),
    )
    accepted = resolve_policy_alignment(
        replace(base, uncertainties=aggregate_only, probes=faithful_high_cost)
    )
    assert accepted.probe.probe_id == "probe-faithful"

    low_fidelity_only = (
        ProbeOption(
            probe_id="probe-lowfi",
            resolves=("u-aggregate",),
            cost=1,
            representative_dimensions=(
                "hero.composition",
                "hero.density",
                "hero.motion",
            ),
            fidelity=ProbeFidelity.LOW,
        ),
    )
    demanding = tuple(
        replace(item, minimum_fidelity=ProbeFidelity.HIGH) for item in aggregate_only
    )
    rejected_fidelity = resolve_policy_alignment(
        replace(base, uncertainties=demanding, probes=low_fidelity_only)
    )
    assert rejected_fidelity.probe.probe_id is None

    del probes  # default probe set remains exercised by other scenarios


def test_known_indifference_suppresses_calibration_unless_questionable() -> None:
    indifference = PreferenceKnowledge(
        dimension="color.palette",
        direction=None,
        disposition=Disposition.INDIFFERENT,
        basis=EpistemicBasis.EXPLICIT,
        confidence=0.95,
        strength=0.0,
        scope=PROJECT_SCOPE,
        context={},
        evidence=("taste-indifferent-1",),
        provenance=(Provenance(actor="user", source_id="taste-indifferent-1"),),
        validation_context=ValidationContext(
            domain="interface-design", fidelity="high"
        ),
        relationships={},
    )
    palette_uncertainty = Uncertainty(
        uncertainty_id="u-palette",
        dimensions=("color.palette",),
        question="Which palette direction should we calibrate?",
        weight=UncertaintyWeight.MATERIAL,
    )
    questionable_palette = replace(
        palette_uncertainty, questionable_applicability=True
    )
    probes = (
        ProbeOption(
            probe_id="probe-palette",
            resolves=("u-palette",),
            cost=2,
            representative_dimensions=("color.palette",),
        ),
    )
    craft_fill = DecisionDirective(
        dimension="color.palette",
        direction="balanced-neutral",
        reason="craft fills execution while the user is indifferent",
        provenance=(Provenance(actor="agent", source_id="craft:palette"),),
    )
    base = preset_request(AutonomyPreset.AGENT_LED)
    based = replace(
        base,
        alignment=replace(
            base.alignment,
            dimensions=("visual-direction", "color.palette"),
            craft_priors=(craft_fill,),
            taste=(_confirmed_taste(), indifference),
        ),
        uncertainties=(palette_uncertainty,),
        probes=probes,
    )

    suppressed = resolve_policy_alignment(based)
    assert suppressed.probe.uncertainty_ids == ()
    assert suppressed.probe.probe_id is None
    assert "suppresses" in suppressed.probe.reason
    assert all(
        checkpoint.key != "resolve-uncertainty:u-palette"
        for checkpoint in suppressed.checkpoints
    )

    reopened = resolve_policy_alignment(
        replace(based, uncertainties=(questionable_palette,))
    )
    assert reopened.probe.uncertainty_ids == ("u-palette",)
    assert reopened.probe.probe_id == "probe-palette"
