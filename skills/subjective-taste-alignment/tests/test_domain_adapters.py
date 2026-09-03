"""Behavioral scenarios for the domain-adapter proof layer."""

from __future__ import annotations

from dataclasses import replace

import pytest

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
    StaleAlignmentError,
    ValidationContext,
    resolve_alignment,
)
from decision_policy import (
    AutonomyPreset,
    DecisionContext,
    DecisionLevel,
    DirectionCandidate,
    DirectionSpace,
    ProbeDecision,
    ProbeFidelity,
    ProbeOption,
    PolicyRequest,
    PropagationRoute,
    Uncertainty,
    UncertaintyWeight,
    authorize_policy_propagation,
    autonomy_snapshot,
    resolve_policy_alignment,
)
from domain_adapters import (
    CraftTechnique,
    DomainAdapter,
    DomainKind,
    declared_probes,
    execution_instruction,
    motion_timing_curve_preview_construction,
    ui_contrast_pair_construction,
    writing_excerpt_ab_construction,
)


PROJECT_SCOPE = Scope(
    kind="project",
    identity="project-a",
    represented_subject="user-1",
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


def _confirmed_taste(
    dimension: str,
    direction: str,
    domain: str = "motion",
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
        evidence=(f"taste:{dimension}",),
        provenance=(Provenance(actor="user", source_id=f"taste:{dimension}"),),
        validation_context=ValidationContext(domain=domain, fidelity="high"),
        relationships={},
    )


def _directive(
    dimension: str,
    direction: str,
    *,
    reason: str,
    source_id: str,
    actor: str = "user",
) -> DecisionDirective:
    return DecisionDirective(
        dimension=dimension,
        direction=direction,
        reason=reason,
        provenance=(Provenance(actor=actor, source_id=source_id),),
    )


def _intent_directive(
    dimension: str,
    direction: str,
    source_id: str,
) -> DecisionDirective:
    return _directive(
        dimension,
        direction,
        reason="the project brief fixes this direction",
        source_id=source_id,
    )


def _constraint_directive(dimension: str, direction: str) -> DecisionDirective:
    return _directive(
        dimension,
        direction,
        reason="hard constraint binds this decision",
        source_id=f"constraint:{dimension}",
        actor="project",
    )


def _ui_adapter() -> DomainAdapter:
    return DomainAdapter(
        domain="ui",
        medium_description="interface layout, styling, and component decisions",
        craft_techniques=(
            CraftTechnique(
                technique_id="ui-density",
                dimension="ui.layout-density",
                direction="compact-scannable",
                rationale="dense scannable layouts reduce cognitive load",
            ),
            CraftTechnique(
                technique_id="ui-empty-state",
                dimension="ui.empty-state",
                direction="illustrated-guidance",
                rationale="illustrated empty states teach the interaction model",
            ),
        ),
    )


def _writing_adapter() -> DomainAdapter:
    return DomainAdapter(
        domain="writing",
        medium_description="prose voice, rhythm, and clarity decisions",
        craft_techniques=(
            CraftTechnique(
                technique_id="prose-rhythm",
                dimension="prose.sentence-length",
                direction="varied-rhythm",
                rationale="varied sentence rhythm keeps readers engaged",
            ),
            CraftTechnique(
                technique_id="prose-jargon",
                dimension="prose.jargon",
                direction="plain-terms",
                rationale="plain terms widen the audience",
            ),
        ),
    )


def _motion_adapter() -> DomainAdapter:
    return DomainAdapter(
        domain="motion",
        medium_description="animation and game-feel timing decisions",
        craft_techniques=(
            CraftTechnique(
                technique_id="motion-duration",
                dimension="motion.duration-scale",
                direction="under-250ms",
                rationale="entrances under 250 ms preserve perceived responsiveness",
            ),
            CraftTechnique(
                technique_id="motion-easing",
                dimension="motion.easing-family",
                direction="standard-out",
                rationale="deceleration curves read as natural settling",
            ),
        ),
    )


def _policy_request(
    adapter: DomainAdapter,
    *,
    dimensions: tuple[str, ...],
    preset: AutonomyPreset,
    target: str,
    level: DecisionLevel | str = DecisionLevel.ELEMENT_FAMILY,
    material: bool = True,
    taste: tuple[PreferenceKnowledge, ...] = (),
    intent: tuple[DecisionDirective, ...] = (),
    constraints: tuple[DecisionDirective, ...] = (),
    craft_priors: bool = False,
    direction: DirectionSpace | None = None,
    uncertainties: tuple[Uncertainty, ...] = (),
    probes: tuple[ProbeOption, ...] = (),
) -> PolicyRequest:
    alignment = AlignmentRequest(
        decision_id=f"{adapter.kind.value}-{target}",
        dimensions=dimensions,
        material=material,
        taste=taste,
        intent=intent,
        constraints=constraints,
    )
    if craft_priors:
        alignment = adapter.with_craft_priors(alignment)
    return PolicyRequest(
        alignment=alignment,
        autonomy=autonomy_snapshot(
            preset,
            authority_scope=_authority(*dimensions),
            revision=f"{adapter.kind.value}-{preset.value}-1",
            effective_from_sequence=0,
        ),
        decision=DecisionContext(sequence=0, target=target, level=level),
        direction=direction,
        uncertainties=uncertainties,
        probes=probes,
    )


def _build_request() -> AlignmentRequest:
    """A motion build decision whose detail dims carry delegated authority."""
    return AlignmentRequest(
        decision_id="motion-build",
        dimensions=("motion.duration-scale", "motion.easing-family"),
        material=True,
        authority=(_authority("motion.duration-scale", "motion.easing-family"),),
    )


def test_adapter_rejects_unknown_domain_kinds() -> None:
    with pytest.raises(ValueError, match="unsupported domain: film"):
        DomainAdapter(domain="film")


def test_adapter_local_metadata_and_input_order_cannot_change_core_outcomes() -> None:
    original = _motion_adapter()
    reordered = DomainAdapter(
        domain=original.domain,
        medium_description="an entirely different description of the medium",
        craft_techniques=tuple(reversed(original.craft_techniques)),
    )
    request = _build_request()

    first = resolve_alignment(original.with_craft_priors(request))
    second = resolve_alignment(reordered.with_craft_priors(request))

    assert first.decision_bearing_revision == second.decision_bearing_revision
    for dimension in request.dimensions:
        left = first.dimensions[dimension]
        right = second.dimensions[dimension]
        assert left.governing_source is GoverningSource.CRAFT_PRIOR
        assert right.governing_source is GoverningSource.CRAFT_PRIOR
        assert (left.direction, left.reason) == (right.direction, right.reason)
        assert not left.conflicts and not right.conflicts
    assert first.checkpoint_obligations == second.checkpoint_obligations
    assert first.propagation_eligible == second.propagation_eligible
    assert set(first.provenance) == set(second.provenance)


def test_only_canonical_input_changes_move_core_outcomes() -> None:
    original = _motion_adapter()
    relabeled = DomainAdapter(
        domain=original.domain,
        craft_techniques=original.craft_techniques,
        medium_description="tampered presentation copy",
    )
    flipped = DomainAdapter(
        domain=original.domain,
        craft_techniques=(
            original.craft_techniques[0],
            replace(original.craft_techniques[1], direction="springy-settle"),
        ),
    )
    request = _build_request()

    baseline = resolve_alignment(original.with_craft_priors(request))
    relabeled_result = resolve_alignment(relabeled.with_craft_priors(request))
    flipped_result = resolve_alignment(flipped.with_craft_priors(request))

    assert (
        relabeled_result.decision_bearing_revision
        == baseline.decision_bearing_revision
    )
    assert (
        flipped_result.decision_bearing_revision
        != baseline.decision_bearing_revision
    )
    eased_before = baseline.dimensions["motion.easing-family"]
    eased_after = flipped_result.dimensions["motion.easing-family"]
    assert eased_before.direction == "standard-out"
    assert eased_after.direction == "springy-settle"
    assert eased_after.governing_source is GoverningSource.CRAFT_PRIOR
    untouched_before = baseline.dimensions["motion.duration-scale"]
    untouched_after = flipped_result.dimensions["motion.duration-scale"]
    assert untouched_before.direction == untouched_after.direction == "under-250ms"


def test_adapter_propagation_authority_is_exactly_the_canonical_guard() -> None:
    adapter = _writing_adapter()
    open_request = AlignmentRequest(
        decision_id="writing-open",
        dimensions=("prose.opening-line",),
        material=True,
    )
    blocked = resolve_alignment(open_request)

    with pytest.raises(PropagationBlockedError, match="unresolved dimensions"):
        adapter.authorize(blocked, open_request)

    resolved_request = replace(
        open_request,
        intent=(_intent_directive("prose.opening-line", "in-medias-res", "brief-7"),),
    )
    settled = resolve_alignment(resolved_request)

    assert adapter.authorize(settled, resolved_request) is settled

    changed_request = replace(resolved_request, material=False)

    with pytest.raises(StaleAlignmentError, match="decision-bearing state changed"):
        adapter.authorize(settled, changed_request)


def test_craft_prior_without_taste_or_authority_leaves_dimension_unresolved() -> None:
    expert = DomainAdapter(
        domain="writing",
        craft_techniques=(
            CraftTechnique(
                technique_id="opening-craft",
                dimension="prose.opening-line",
                direction="in-medias-res",
                rationale="master stylists insist readers prefer immersive openings",
            ),
        ),
    )
    request = expert.with_craft_priors(
        AlignmentRequest(
            decision_id="writing-opening",
            dimensions=("prose.opening-line",),
            material=True,
        )
    )
    result = resolve_alignment(request)
    resolved = result.dimensions["prose.opening-line"]

    assert resolved.governing_source is None
    assert resolved.direction is None
    assert resolved.craft_prior is not None
    assert resolved.craft_prior.direction == "in-medias-res"
    assert "prose.opening-line" in result.unresolved_dimensions
    assert "resolve:prose.opening-line" in result.checkpoint_obligations
    assert result.propagation_eligible is False
    assert request.taste == ()
    assert resolved.taste is None


def test_delegated_authority_lets_craft_execute_while_taste_stays_absent() -> None:
    expert = DomainAdapter(
        domain="writing",
        craft_techniques=(
            CraftTechnique(
                technique_id="opening-craft",
                dimension="prose.opening-line",
                direction="in-medias-res",
                rationale="master stylists insist readers prefer immersive openings",
            ),
        ),
    )
    request = expert.with_craft_priors(
        AlignmentRequest(
            decision_id="writing-opening",
            dimensions=("prose.opening-line",),
            material=True,
            authority=(_authority("prose.opening-line"),),
        )
    )
    result = resolve_alignment(request)
    resolved = result.dimensions["prose.opening-line"]

    assert resolved.governing_source is GoverningSource.CRAFT_PRIOR
    assert resolved.direction == "in-medias-res"
    assert "craft prior" in resolved.reason
    assert request.taste == ()
    assert resolved.taste is None
    source_ids = {record.source_id for record in result.provenance}
    assert "craft:opening-craft" in source_ids
    assert "preset-selection" in source_ids


def test_constraints_outrank_intent_and_intent_outranks_craft() -> None:
    full = AlignmentRequest(
        decision_id="motion-transition",
        dimensions=("motion.transition",),
        material=True,
        constraints=(
            _directive(
                "motion.transition",
                "reduced-motion-fallback",
                reason="prefers-reduced-motion must be honored",
                source_id="a11y-policy",
                actor="project",
            ),
        ),
        intent=(
            _intent_directive("motion.transition", "expressive-emphasis", "brief-3"),
        ),
        craft_priors=(
            _directive(
                "motion.transition",
                "platform-convention",
                reason="platform conventions favor system curves",
                source_id="craft:transition",
                actor="agent",
            ),
        ),
        authority=(_authority("motion.transition"),),
    )

    three_way = resolve_alignment(full)
    governed = three_way.dimensions["motion.transition"]
    assert governed.governing_source is GoverningSource.CONSTRAINT
    assert governed.direction == "reduced-motion-fallback"
    assert "prefers-reduced-motion" in governed.reason

    without_constraint = resolve_alignment(replace(full, constraints=()))
    overridden = without_constraint.dimensions["motion.transition"]
    assert overridden.governing_source is GoverningSource.INTENT
    assert overridden.direction == "expressive-emphasis"


def test_three_domains_run_one_call_pattern_with_distinct_vocabularies() -> None:
    cases = (
        (
            _ui_adapter(),
            (
                "ui.accent-color",
                "ui.navigation-pattern",
                "ui.focus-visible",
                "ui.card-shadow",
            ),
            ("warm-accent", "left-rail-navigation", "always-visible-focus"),
        ),
        (
            _writing_adapter(),
            (
                "prose.voice",
                "prose.persona",
                "prose.fact-checking",
                "prose.pun-density",
            ),
            ("dry-wit", "second-person-coach", "verify-claims-before-publish"),
        ),
        (
            _motion_adapter(),
            (
                "motion.transition-style",
                "motion.purpose",
                "motion.accessibility",
                "motion.feel-check",
            ),
            ("subtle-transitions", "communicate-progress", "reduced-motion-fallback"),
        ),
    )

    vocabularies: list[set[str]] = []
    routes: list[str | None] = []
    reasons: list[str] = []
    for adapter, (taste_dim, intent_dim, constraint_dim, open_dim), directions in cases:
        resolved = resolve_policy_alignment(
            _policy_request(
                adapter,
                dimensions=(taste_dim, intent_dim, constraint_dim, open_dim),
                preset=AutonomyPreset.AGENT_LED,
                target=f"{adapter.kind.value}-bundle",
                taste=(_confirmed_taste(taste_dim, directions[0]),),
                intent=(_intent_directive(intent_dim, directions[1], "brief-x"),),
                constraints=(_constraint_directive(constraint_dim, directions[2]),),
            )
        )
        sources = [
            resolved.alignment.dimensions[name].governing_source
            for name in (taste_dim, intent_dim, constraint_dim, open_dim)
        ]
        assert sources == [
            GoverningSource.TASTE,
            GoverningSource.INTENT,
            GoverningSource.CONSTRAINT,
            None,
        ]
        assert resolved.alignment.unresolved_dimensions == (open_dim,)
        assert resolved.alignment.checkpoint_obligations == (f"resolve:{open_dim}",)
        assert resolved.alignment_request.taste[0].dimension == taste_dim
        vocabularies.append({taste_dim, intent_dim, constraint_dim, open_dim})
        propagation = resolved.alignment_request.propagation_policy
        assert propagation is not None
        routes.append(propagation.route)
        reasons.append(propagation.reason)

    ui_vocab, writing_vocab, motion_vocab = vocabularies
    assert not ui_vocab & writing_vocab
    assert not ui_vocab & motion_vocab
    assert not writing_vocab & motion_vocab
    assert len(set(routes)) == 1
    assert routes[0] is None
    assert len(set(reasons)) == 1


def test_medium_probes_are_selected_by_the_shared_contract() -> None:
    ui_uncertainty = Uncertainty(
        "u-ui-contrast",
        ("ui.contrast",),
        "Which pairing reads calmer?",
        weight=UncertaintyWeight.MATERIAL,
    )
    ui_pair = ui_contrast_pair_construction(
        probe_id="probe:ui-pair",
        foreground="#111111",
        background="#f4f4f4",
        resolves=("u-ui-contrast",),
        representative_dimensions=("ui.contrast",),
        cost=2,
    )
    ui_audit = ui_contrast_pair_construction(
        probe_id="probe:ui-audit",
        foreground="#111111",
        background="#f4f4f4",
        resolves=("u-ui-contrast",),
        representative_dimensions=("ui.contrast",),
        cost=9,
    )
    writing_uncertainty = Uncertainty(
        "u-writing-voice",
        ("prose.voice",),
        "Which narrative voice should carry the guide?",
    )
    writing_ab = writing_excerpt_ab_construction(
        probe_id="probe:writing-ab",
        excerpt_a="The lighthouse blinked twice.",
        excerpt_b="Twice, the lighthouse blinked.",
        resolves=("u-writing-voice",),
        representative_dimensions=("prose.voice",),
        cost=3,
    )
    writing_chapter = writing_excerpt_ab_construction(
        probe_id="probe:writing-chapter",
        excerpt_a="Chapter one opens the story.",
        excerpt_b="The story opens chapter one.",
        resolves=(writing_uncertainty.uncertainty_id,),
        representative_dimensions=("prose.voice",),
        cost=12,
    )
    motion_uncertainty = Uncertainty(
        "u-motion-easing",
        ("motion.easing-family",),
        "Which timing curve feels right for entrances?",
        minimum_fidelity=ProbeFidelity.HIGH,
    )
    motion_static = motion_timing_curve_preview_construction(
        probe_id="probe:motion-static",
        curve_a="ease-out-200ms",
        curve_b="linear-400ms",
        resolves=(motion_uncertainty.uncertainty_id,),
        representative_dimensions=("motion.easing-family",),
        cost=1,
        fidelity=ProbeFidelity.LOW,
    )
    motion_preview = motion_timing_curve_preview_construction(
        probe_id="probe:motion-preview",
        curve_a="ease-out-200ms",
        curve_b="linear-400ms",
        resolves=(motion_uncertainty.uncertainty_id,),
        representative_dimensions=("motion.easing-family",),
        cost=4,
        fidelity=ProbeFidelity.HIGH,
    )
    cases = (
        (
            _ui_adapter(),
            ui_uncertainty,
            (ui_pair, ui_audit),
            "probe:ui-pair",
        ),
        (
            _writing_adapter(),
            writing_uncertainty,
            (writing_ab, writing_chapter),
            "probe:writing-ab",
        ),
        (
            _motion_adapter(),
            motion_uncertainty,
            (motion_static, motion_preview),
            "probe:motion-preview",
        ),
    )

    selected_ids: list[str | None] = []
    instructions: list[str] = []
    for adapter, uncertainty, constructions, expected in cases:
        resolved = resolve_policy_alignment(
            _policy_request(
                adapter,
                dimensions=uncertainty.dimensions,
                preset=AutonomyPreset.AGENT_LED,
                target=f"{adapter.kind.value}-calibration",
                uncertainties=(uncertainty,),
                probes=declared_probes(constructions),
            )
        )

        assert resolved.probe.uncertainty_ids == (uncertainty.uncertainty_id,)
        assert resolved.probe.probe_id == expected
        assert resolved.probe.fallback == "representative-probe"
        assert resolved.probe.evidence_granularity == "representative"
        instruction = execution_instruction(constructions, resolved.probe)
        assert instruction is not None
        selected_ids.append(resolved.probe.probe_id)
        instructions.append(instruction)

    assert len(set(selected_ids)) == 3
    assert "render" in instructions[0]
    assert "excerpt A" in instructions[1]
    assert "timing" in instructions[2]


def test_uncoverable_uncertainty_yields_identical_clarification_fallback() -> None:
    ui_uncertainty = Uncertainty(
        "u-ui-contrast",
        ("ui.contrast",),
        "Which pairing reads calmer?",
    )
    unrelated_pair = ui_contrast_pair_construction(
        probe_id="probe:ui-unrelated",
        foreground="#111111",
        background="#ffffff",
        resolves=("u-something-else",),
        representative_dimensions=("ui.contrast",),
        cost=1,
    )
    writing_uncertainty = Uncertainty(
        "u-writing-voice",
        ("prose.voice",),
        "Which narrative voice should carry the guide?",
    )
    unrelated_excerpt = writing_excerpt_ab_construction(
        probe_id="probe:writing-unrelated",
        excerpt_a="A.",
        excerpt_b="B.",
        resolves=("u-something-else",),
        representative_dimensions=("prose.voice",),
        cost=1,
    )
    motion_uncertainty = Uncertainty(
        "u-motion-easing",
        ("motion.easing-family",),
        "Which timing curve feels right for entrances?",
        minimum_fidelity=ProbeFidelity.HIGH,
    )
    unfaithful_preview = motion_timing_curve_preview_construction(
        probe_id="probe:motion-static",
        curve_a="ease-out-200ms",
        curve_b="linear-400ms",
        resolves=(motion_uncertainty.uncertainty_id,),
        representative_dimensions=("motion.easing-family",),
        cost=1,
        fidelity=ProbeFidelity.LOW,
    )
    cases = (
        (_ui_adapter(), ui_uncertainty, (unrelated_pair,)),
        (_writing_adapter(), writing_uncertainty, (unrelated_excerpt,)),
        (_motion_adapter(), motion_uncertainty, (unfaithful_preview,)),
    )

    for adapter, uncertainty, constructions in cases:
        resolved = resolve_policy_alignment(
            _policy_request(
                adapter,
                dimensions=uncertainty.dimensions,
                preset=AutonomyPreset.AGENT_LED,
                target=f"{adapter.kind.value}-calibration",
                uncertainties=(uncertainty,),
                probes=declared_probes(constructions),
            )
        )

        assert resolved.probe.probe_id is None
        assert resolved.probe.fallback == "clarification-checkpoint"
        assert resolved.probe.uncertainty_ids == (uncertainty.uncertainty_id,)
        checkpoint_keys = [item.key for item in resolved.checkpoints]
        assert (
            f"resolve-uncertainty:{uncertainty.uncertainty_id}" in checkpoint_keys
        )
        policy = resolved.alignment_request.propagation_policy
        assert policy is not None and policy.eligible is False


def test_probe_execution_instructions_bind_to_canonical_probe_decisions() -> None:
    constructions = (
        ui_contrast_pair_construction(
            probe_id="probe:ui-pair",
            foreground="#111111",
            background="#ffffff",
            resolves=("u-ui-contrast",),
            representative_dimensions=("ui.contrast",),
            cost=2,
        ),
    )
    selected = ProbeDecision(
        ("u-ui-contrast",),
        "probe:ui-pair",
        "representative-probe",
        "representative",
        "canonical selection",
    )
    fallback = ProbeDecision(
        ("u-ui-contrast",),
        None,
        "clarification-checkpoint",
        None,
        "no faithful probe exists",
    )
    unknown = replace(selected, probe_id="probe:undeclared")

    selected_instruction = execution_instruction(constructions, selected)
    assert selected_instruction is not None
    assert "#111111" in selected_instruction
    assert execution_instruction(constructions, fallback) is None

    with pytest.raises(ValueError, match="no construction declared"):
        execution_instruction(constructions, unknown)


def test_motion_walkthrough_existence_purpose_build_feelcheck_review_none() -> None:
    adapter = _motion_adapter()

    # (i) Decide whether motion should exist at all: compare materially
    # distinct candidates, including "no animation", before refining.
    space = DirectionSpace(
        candidates=(
            DirectionCandidate(
                candidate_id="motion:none",
                summary="no animation at all",
            ),
            DirectionCandidate(
                candidate_id="motion:fade",
                summary="one gentle fade on entry",
            ),
            DirectionCandidate(
                candidate_id="motion:slide",
                summary="directional slide with settle",
            ),
        )
    )
    existence = resolve_policy_alignment(
        _policy_request(
            adapter,
            dimensions=("motion.purpose", "motion.intensity"),
            preset=AutonomyPreset.DIRECTION_CHECKPOINT,
            level=DecisionLevel.DIRECTION,
            target="onboarding-flow",
            direction=space,
        )
    )

    assert existence.direction.discovery_required is True
    assert existence.direction.selection_actor == "user"
    assert existence.direction.source == "direction-space"
    assert existence.direction.candidates == (
        "motion:none",
        "motion:fade",
        "motion:slide",
    )
    assert [item.key for item in existence.checkpoints] == ["select-direction"]
    assert existence.alignment_request.taste == ()

    # (ii) Identify motion's purpose through user intent.
    purpose_intent = _intent_directive(
        "motion.purpose",
        "communicate-progress",
        "brief-onboarding",
    )
    intensity_intent = _intent_directive(
        "motion.intensity",
        "gentle",
        "candidate-selection",
    )
    directed = resolve_policy_alignment(
        _policy_request(
            adapter,
            dimensions=("motion.purpose", "motion.intensity"),
            preset=AutonomyPreset.DIRECTION_CHECKPOINT,
            level=DecisionLevel.DIRECTION,
            target="onboarding-flow",
            intent=(purpose_intent, intensity_intent),
        )
    )

    assert directed.direction.established is True
    assert directed.direction.discovery_required is False
    assert directed.checkpoints == ()
    for dimension, expected in (
        ("motion.purpose", "communicate-progress"),
        ("motion.intensity", "gentle"),
    ):
        resolved = directed.alignment.dimensions[dimension]
        assert resolved.governing_source is GoverningSource.INTENT
        assert resolved.direction == expected

    # (iii) Build according to the established direction: craft executes
    # implementation details under delegated authority only.
    build_dimensions = (
        "motion.purpose",
        "motion.intensity",
        "motion.duration-scale",
        "motion.easing-family",
    )
    build = resolve_policy_alignment(
        _policy_request(
            adapter,
            dimensions=build_dimensions,
            preset=AutonomyPreset.AGENT_LED,
            target="onboarding-flow-build",
            intent=(purpose_intent, intensity_intent),
            craft_priors=True,
        )
    )

    build_sources = {
        name: item.governing_source
        for name, item in build.alignment.dimensions.items()
    }
    assert build_sources == {
        "motion.purpose": GoverningSource.INTENT,
        "motion.intensity": GoverningSource.INTENT,
        "motion.duration-scale": GoverningSource.CRAFT_PRIOR,
        "motion.easing-family": GoverningSource.CRAFT_PRIOR,
    }
    assert (
        build.alignment.dimensions["motion.duration-scale"].direction
        == "under-250ms"
    )
    assert build.alignment_request.taste == ()

    # (iv) Remaining human feel-checks surface as canonical checkpoints;
    # the adapter must not fabricate a verdict for them.
    feel = resolve_policy_alignment(
        _policy_request(
            adapter,
            dimensions=(*build_dimensions, "motion.feel-check"),
            preset=AutonomyPreset.AGENT_LED,
            target="onboarding-flow-feel",
            intent=(purpose_intent, intensity_intent),
            craft_priors=True,
        )
    )

    assert "motion.feel-check" in feel.alignment.unresolved_dimensions
    obligations = list(feel.alignment.checkpoint_obligations)
    assert "resolve:motion.feel-check" in obligations
    assert feel.alignment.propagation_eligible is False

    # (v) Review responsiveness, performance, accessibility, craft, and
    # established taste as separate dimensions; accessibility stays an
    # independent hard constraint even against opposing intent.
    review = resolve_policy_alignment(
        _policy_request(
            adapter,
            dimensions=(
                *build_dimensions,
                "motion.accessibility",
                "motion.performance",
                "motion.responsiveness",
                "motion.transition-style",
            ),
            preset=AutonomyPreset.AGENT_LED,
            target="onboarding-flow-review",
            intent=(
                purpose_intent,
                intensity_intent,
                _intent_directive(
                    "motion.accessibility",
                    "expressive-emphasis",
                    "brief-onboarding",
                ),
            ),
            constraints=(
                _constraint_directive(
                    "motion.accessibility",
                    "reduced-motion-fallback",
                ),
                _constraint_directive(
                    "motion.performance",
                    "frame-budget-under-16ms",
                ),
                _constraint_directive(
                    "motion.responsiveness",
                    "input-echo-immediate",
                ),
            ),
            craft_priors=True,
            taste=(
                _confirmed_taste("motion.transition-style", "subtle-transitions"),
            ),
        )
    )

    actual_sources = {
        name: item.governing_source
        for name, item in review.alignment.dimensions.items()
    }
    assert actual_sources == {
        "motion.purpose": GoverningSource.INTENT,
        "motion.intensity": GoverningSource.INTENT,
        "motion.duration-scale": GoverningSource.CRAFT_PRIOR,
        "motion.easing-family": GoverningSource.CRAFT_PRIOR,
        "motion.accessibility": GoverningSource.CONSTRAINT,
        "motion.performance": GoverningSource.CONSTRAINT,
        "motion.responsiveness": GoverningSource.CONSTRAINT,
        "motion.transition-style": GoverningSource.TASTE,
    }
    accessibility = review.alignment.dimensions["motion.accessibility"]
    assert accessibility.direction == "reduced-motion-fallback"
    assert review.alignment.unresolved_dimensions == ()
    assert review.checkpoints == ()
    review_policy = review.alignment_request.propagation_policy
    assert review_policy is not None
    assert review_policy.route is None

    # (vi) "No animation" is a valid aligned outcome: it resolves cleanly
    # and propagates when policy allows, with no manufactured preference.
    none_request = _policy_request(
        adapter,
        dimensions=("motion.purpose", "motion.intensity", "motion.accessibility"),
        preset=AutonomyPreset.AGENT_LED,
        target="onboarding-flow-none",
        intent=(
            _intent_directive("motion.purpose", "no-animation", "brief-onboarding"),
            _intent_directive("motion.intensity", "none", "candidate-selection"),
        ),
        constraints=(
            _constraint_directive("motion.accessibility", "reduced-motion-fallback"),
        ),
    )
    none_resolved = resolve_policy_alignment(none_request)

    assert none_resolved.alignment.unresolved_dimensions == ()
    assert none_resolved.checkpoints == ()
    assert none_resolved.alignment.propagation_eligible is True
    policy = none_resolved.alignment_request.propagation_policy
    assert policy is not None
    assert policy.route == PropagationRoute.DETERMINING_DIRECTIVE
    for dimension in ("motion.purpose", "motion.intensity"):
        resolved = none_resolved.alignment.dimensions[dimension]
        assert resolved.governing_source is GoverningSource.INTENT
        assert resolved.taste is None
    authorized = authorize_policy_propagation(none_resolved, none_request)
    assert authorized is none_resolved.alignment
    assert none_resolved.alignment_request.taste == ()
