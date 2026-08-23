from alignment_harness import (
    AlignmentRequest,
    AuthorityScope,
    DecisionDirective,
    PreferenceKnowledge,
    Provenance,
    Scenario,
    ScenarioStep,
    Scope,
    StaleAlignmentError,
    Transition,
    ValidationContext,
    authorize_propagation,
    is_alignment_stale,
    resolve_alignment,
    run_scenario,
)


def preference(
    *,
    dimension: str = "palette",
    direction: str | None,
    disposition: str = "preferred",
    basis: str = "explicit",
    confidence: float,
    strength: float,
) -> PreferenceKnowledge:
    return PreferenceKnowledge(
        dimension=dimension,
        direction=direction,
        disposition=disposition,
        basis=basis,
        confidence=confidence,
        strength=strength,
        scope=Scope(kind="project", identity="project-a", represented_subject="user"),
        context={"surface": "settings"},
        evidence=("feedback-1",),
        provenance=(Provenance(actor="user", source_id="feedback-1"),),
        validation_context=ValidationContext(
            domain="ui",
            fidelity="implemented-screen",
            conditions=("desktop",),
        ),
        relationships={"contrast": "high"},
    )


def test_subjective_state_labels_are_derived_from_canonical_knowledge() -> None:
    cases = (
        (
            preference(
                direction="warm",
                basis="inferred",
                confidence=0.8,
                strength=0.6,
            ),
            "strong inference",
        ),
        (
            preference(
                direction="busy",
                disposition="rejected",
                confidence=0.8,
                strength=0.7,
            ),
            "rejected direction",
        ),
        (
            preference(
                direction=None,
                disposition="indifferent",
                confidence=0.8,
                strength=0,
            ),
            "known indifference",
        ),
        (
            preference(
                direction=None,
                disposition="unresolved",
                confidence=0,
                strength=0,
            ),
            "unresolved dimension",
        ),
    )

    assert tuple(knowledge.derived_label for knowledge, _ in cases) == tuple(
        label for _, label in cases
    )


def assert_resolution_scenario(
    *,
    name: str,
    request: AlignmentRequest,
    dimension: str,
    expected_direction: str,
    expected_source: str,
    expected_propagation: bool,
) -> None:
    def dispatch(step: ScenarioStep, state: dict[str, object]) -> Transition:
        result = resolve_alignment(request)
        resolved = result.dimensions[dimension]
        return Transition(
            {"direction": resolved.direction},
            {
                "source": resolved.governing_source,
                "propagation": result.propagation_eligible,
            },
        )

    scenario = Scenario(
        name=name,
        initial_state={},
        steps=(ScenarioStep("resolve-1", "alignment", "resolve"),),
        expected_state={"direction": expected_direction},
        expected_observations=(
            {
                "source": expected_source,
                "propagation": expected_propagation,
            },
        ),
    )
    assert run_scenario(scenario, dispatch).status == "passed"


def test_strong_preference_with_weak_confidence_remains_distinct() -> None:
    request = AlignmentRequest(
        decision_id="settings-palette",
        dimensions=("palette",),
        material=True,
        taste=(preference(direction="saturated", confidence=0.3, strength=0.95),),
    )

    def dispatch(step: ScenarioStep, state: dict[str, object]) -> Transition:
        result = resolve_alignment(request)
        dimension = result.dimensions["palette"]
        return Transition(
            {"resolved": dimension.direction},
            {
                "source": dimension.governing_source,
                "confidence": dimension.taste.confidence if dimension.taste else None,
                "strength": dimension.taste.strength if dimension.taste else None,
                "propagation": result.propagation_eligible,
            },
        )

    scenario = Scenario(
        name="strong preference with weak confidence",
        initial_state={},
        steps=(ScenarioStep("resolve-1", "alignment", "resolve"),),
        expected_state={"resolved": "saturated"},
        expected_observations=(
            {
                "source": "taste",
                "confidence": 0.3,
                "strength": 0.95,
                "propagation": False,
            },
        ),
    )

    result = run_scenario(scenario, dispatch)

    assert result.status == "passed"
    alignment = resolve_alignment(request)
    assert alignment.dimensions["palette"].taste is not None
    assert alignment.dimensions["palette"].taste.derived_label == "weak hypothesis"
    assert alignment.unresolved_dimensions == ()
    assert alignment.checkpoint_obligations == ("assess-propagation:palette",)


def test_weak_preference_with_high_confidence_remains_distinct() -> None:
    request = AlignmentRequest(
        decision_id="settings-palette-subtle-preference",
        dimensions=("palette",),
        material=True,
        taste=(preference(direction="warm", confidence=0.95, strength=0.15),),
    )

    def dispatch(step: ScenarioStep, state: dict[str, object]) -> Transition:
        result = resolve_alignment(request)
        dimension = result.dimensions["palette"]
        assert dimension.taste is not None
        return Transition(
            {"resolved": dimension.direction},
            {
                "confidence": dimension.taste.confidence,
                "strength": dimension.taste.strength,
                "source": dimension.governing_source,
            },
        )

    scenario = Scenario(
        name="weak preference with high confidence",
        initial_state={},
        steps=(ScenarioStep("resolve-1", "alignment", "resolve"),),
        expected_state={"resolved": "warm"},
        expected_observations=(
            {"confidence": 0.95, "strength": 0.15, "source": "taste"},
        ),
    )

    assert run_scenario(scenario, dispatch).status == "passed"
    alignment = resolve_alignment(request)
    assert alignment.dimensions["palette"].taste is not None
    assert alignment.dimensions["palette"].taste.derived_label == "confirmed preference"
    assert alignment.unresolved_dimensions == ()
    assert alignment.checkpoint_obligations == ("assess-propagation:palette",)
    assert alignment.propagation_eligible is False


def test_unresolved_taste_checkpoints_before_material_propagation() -> None:
    request = AlignmentRequest(
        decision_id="unknown-settings-palette",
        dimensions=("palette",),
        material=True,
        taste=(
            preference(
                direction=None,
                disposition="unresolved",
                confidence=0,
                strength=0,
            ),
        ),
    )

    def dispatch(step: ScenarioStep, state: dict[str, object]) -> Transition:
        result = resolve_alignment(request)
        dimension = result.dimensions["palette"]
        return Transition(
            {"resolved": dimension.direction},
            {
                "unresolved": result.unresolved_dimensions,
                "checkpoint": result.checkpoint_obligations,
                "propagation": result.propagation_eligible,
            },
        )

    scenario = Scenario(
        name="unresolved taste before material propagation",
        initial_state={},
        steps=(ScenarioStep("resolve-1", "alignment", "resolve"),),
        expected_state={"resolved": None},
        expected_observations=(
            {
                "unresolved": ("palette",),
                "checkpoint": ("resolve:palette",),
                "propagation": False,
            },
        ),
    )

    assert run_scenario(scenario, dispatch).status == "passed"


def test_intent_constrains_only_its_dimension_while_taste_guides_the_rest() -> None:
    request = AlignmentRequest(
        decision_id="campaign-card",
        dimensions=("palette", "spacing"),
        material=True,
        taste=(
            preference(direction="colorful", confidence=0.9, strength=0.8),
            preference(
                dimension="spacing",
                direction="airy",
                confidence=0.85,
                strength=0.6,
            ),
        ),
        intent=(
            DecisionDirective(
                dimension="palette",
                direction="monochrome",
                reason="the campaign brief requires monochrome",
                provenance=(Provenance(actor="user", source_id="brief-7"),),
            ),
        ),
    )

    def dispatch(step: ScenarioStep, state: dict[str, object]) -> Transition:
        result = resolve_alignment(request)
        return Transition(
            {
                dimension: resolution.direction
                for dimension, resolution in result.dimensions.items()
            },
            {
                dimension: resolution.governing_source
                for dimension, resolution in result.dimensions.items()
            },
        )

    scenario = Scenario(
        name="project intent diverges only where explicit",
        initial_state={},
        steps=(ScenarioStep("resolve-1", "alignment", "resolve"),),
        expected_state={"palette": "monochrome", "spacing": "airy"},
        expected_observations=({"palette": "intent", "spacing": "taste"},),
    )

    result = run_scenario(scenario, dispatch)

    assert result.status == "passed"
    palette = resolve_alignment(request).dimensions["palette"]
    assert palette.taste is not None
    assert palette.taste.direction == "colorful"


def test_constraints_and_ownership_remain_distinct_governing_sources() -> None:
    constraint = DecisionDirective(
        dimension="contrast",
        direction="accessible",
        reason="minimum contrast is mandatory",
        provenance=(Provenance(actor="system", source_id="wcag"),),
    )
    owner_direction = DecisionDirective(
        dimension="voice",
        direction="formal",
        reason="the client owns brand voice",
        provenance=(Provenance(actor="client", source_id="brand-guide"),),
    )
    request = AlignmentRequest(
        decision_id="client-landing-page",
        dimensions=("contrast", "voice"),
        material=True,
        constraints=(constraint,),
        ownership=(owner_direction,),
    )

    result = resolve_alignment(request)

    assert result.dimensions["contrast"].governing_source == "constraint"
    assert result.dimensions["contrast"].constraint is constraint
    assert result.dimensions["contrast"].ownership is None
    assert result.dimensions["voice"].governing_source == "ownership"
    assert result.dimensions["voice"].ownership is owner_direction
    assert result.dimensions["voice"].constraint is None
    assert result.propagation_eligible is True


def test_delegated_judgment_resolves_execution_without_becoming_taste() -> None:
    unresolved_taste = preference(
        direction=None,
        disposition="unresolved",
        confidence=0,
        strength=0,
    )
    judgment = DecisionDirective(
        dimension="palette",
        direction="balanced-neutral",
        reason="agent selected an in-scope execution direction",
        provenance=(Provenance(actor="agent", source_id="decision-1"),),
    )
    request = AlignmentRequest(
        decision_id="delegated-palette",
        dimensions=("palette",),
        material=True,
        taste=(unresolved_taste,),
        authority=(
            AuthorityScope(
                actor="agent",
                dimensions=("palette",),
                allows_material_propagation=True,
                checkpoint_required=False,
                scope=Scope(
                    kind="project",
                    identity="project-a",
                    represented_subject="user",
                ),
                provenance=(Provenance(actor="user", source_id="delegation-1"),),
            ),
        ),
        provisional_judgments=(judgment,),
    )

    result = resolve_alignment(request)
    resolved = result.dimensions["palette"]

    assert resolved.direction == "balanced-neutral"
    assert resolved.governing_source == "authorized_judgment"
    assert resolved.authority is request.authority[0]
    assert resolved.provisional_judgment is judgment
    assert resolved.taste is unresolved_taste
    assert resolved.taste.disposition == "unresolved"
    assert result.propagation_eligible is True
    assert result.checkpoint_obligations == ()
    assert_resolution_scenario(
        name="delegated judgment without preference evidence",
        request=request,
        dimension="palette",
        expected_direction="balanced-neutral",
        expected_source="authorized_judgment",
        expected_propagation=True,
    )


def test_temporary_experiment_overrides_execution_without_mutating_taste() -> None:
    established_taste = preference(
        direction="minimal",
        confidence=0.9,
        strength=0.8,
    )
    experiment = DecisionDirective(
        dimension="palette",
        direction="maximal",
        reason="temporary sandbox direction",
        provenance=(Provenance(actor="user", source_id="experiment-1"),),
    )
    request = AlignmentRequest(
        decision_id="temporary-exception",
        dimensions=("palette",),
        material=True,
        taste=(established_taste,),
        experimental_state=(experiment,),
    )

    result = resolve_alignment(request)
    resolved = result.dimensions["palette"]

    assert resolved.direction == "maximal"
    assert resolved.governing_source == "experimental_state"
    assert resolved.experimental_state is experiment
    assert resolved.taste is established_taste
    assert resolved.taste.direction == "minimal"
    assert result.propagation_eligible is True
    assert_resolution_scenario(
        name="temporary experiment preserves reusable taste",
        request=request,
        dimension="palette",
        expected_direction="maximal",
        expected_source="experimental_state",
        expected_propagation=True,
    )


def test_craft_prior_fills_delegated_detail_without_becoming_preference() -> None:
    craft_prior = DecisionDirective(
        dimension="motion-curve",
        direction="ease-out",
        reason="responsive entrance-motion prior",
        provenance=(Provenance(actor="agent", source_id="motion-craft"),),
    )
    request = AlignmentRequest(
        decision_id="delegated-motion-detail",
        dimensions=("motion-curve",),
        material=True,
        authority=(
            AuthorityScope(
                actor="agent",
                dimensions=("motion-curve",),
                allows_material_propagation=True,
                checkpoint_required=False,
                scope=Scope(
                    kind="project",
                    identity="project-a",
                    represented_subject="user",
                ),
                provenance=(Provenance(actor="user", source_id="delegation-2"),),
            ),
        ),
        craft_priors=(craft_prior,),
    )

    result = resolve_alignment(request)
    resolved = result.dimensions["motion-curve"]

    assert resolved.direction == "ease-out"
    assert resolved.governing_source == "craft_prior"
    assert resolved.craft_prior is craft_prior
    assert resolved.taste is None
    assert result.propagation_eligible is True
    assert_resolution_scenario(
        name="delegated craft detail without preference evidence",
        request=request,
        dimension="motion-curve",
        expected_direction="ease-out",
        expected_source="craft_prior",
        expected_propagation=True,
    )


def test_active_authority_checkpoint_blocks_material_propagation() -> None:
    request = AlignmentRequest(
        decision_id="review-established-taste",
        dimensions=("palette",),
        material=True,
        taste=(preference(direction="warm", confidence=0.95, strength=0.4),),
        authority=(
            AuthorityScope(
                actor="user",
                dimensions=("palette",),
                allows_material_propagation=False,
                checkpoint_required=True,
                scope=Scope(
                    kind="project",
                    identity="project-a",
                    represented_subject="user",
                ),
                provenance=(Provenance(actor="user", source_id="preset-1"),),
            ),
        ),
    )

    result = resolve_alignment(request)

    assert result.dimensions["palette"].direction == "warm"
    assert result.checkpoint_obligations == ("review:palette",)
    assert result.propagation_eligible is False


def test_material_input_change_rejects_stale_result_until_reresolved() -> None:
    original = AlignmentRequest(
        decision_id="settings-palette",
        dimensions=("palette",),
        material=True,
        taste=(preference(direction="warm", confidence=0.9, strength=0.7),),
    )
    changed = AlignmentRequest(
        decision_id="settings-palette",
        dimensions=("palette",),
        material=True,
        taste=original.taste,
        intent=(
            DecisionDirective(
                dimension="palette",
                direction="cool",
                reason="new project intent",
                provenance=(Provenance(actor="user", source_id="intent-2"),),
            ),
        ),
    )
    old_result = resolve_alignment(original)

    assert is_alignment_stale(old_result, changed) is True
    try:
        authorize_propagation(old_result, changed)
    except StaleAlignmentError as error:
        assert "re-resolve" in str(error)
    else:
        raise AssertionError("stale material alignment was allowed to propagate")

    current_result = resolve_alignment(changed)

    assert is_alignment_stale(current_result, changed) is False
    assert authorize_propagation(current_result, changed) is current_result
    assert current_result.dimensions["palette"].direction == "cool"


def test_result_exposes_unresolved_state_provenance_and_dependents() -> None:
    intent = DecisionDirective(
        dimension="palette",
        direction="cool",
        reason="project launch direction",
        provenance=(Provenance(actor="user", source_id="intent-3"),),
        dependencies=("artifact:hero",),
    )
    request = AlignmentRequest(
        decision_id="partially-resolved-screen",
        dimensions=("palette", "motion"),
        material=True,
        intent=(intent,),
        dependencies=("decision:layout",),
    )

    result = resolve_alignment(request)

    assert result.material is True
    assert result.unresolved_dimensions == ("motion",)
    assert result.checkpoint_obligations == ("resolve:motion",)
    assert result.propagation_eligible is False
    assert result.provenance == intent.provenance
    assert result.dependencies == ("decision:layout", "artifact:hero")
    assert len(result.decision_bearing_revision) == 64


def test_conflicting_resolvers_surface_conflict_instead_of_picking_one() -> None:
    request = AlignmentRequest(
        decision_id="conflicting-project-intent",
        dimensions=("palette",),
        material=True,
        intent=(
            DecisionDirective(
                dimension="palette",
                direction="warm",
                reason="brief A",
                provenance=(Provenance(actor="user", source_id="brief-a"),),
            ),
            DecisionDirective(
                dimension="palette",
                direction="cool",
                reason="brief B",
                provenance=(Provenance(actor="user", source_id="brief-b"),),
            ),
        ),
    )

    result = resolve_alignment(request)
    resolved = result.dimensions["palette"]

    assert resolved.direction is None
    assert resolved.governing_source == "conflict"
    assert len(resolved.conflicts) == 1
    assert resolved.conflicts[0].source == "intent"
    assert resolved.conflicts[0].inputs == request.intent
    assert resolved.conflicts[0].blocking is True
    assert resolved.inputs.intent == request.intent
    assert result.unresolved_dimensions == ("palette",)
    assert result.propagation_eligible is False


def test_governing_intent_is_not_blocked_by_lower_priority_taste_conflict() -> None:
    taste = (
        preference(direction="warm", confidence=0.7, strength=0.7),
        preference(direction="cool", confidence=0.7, strength=0.7),
    )
    intent = DecisionDirective(
        dimension="palette",
        direction="monochrome",
        reason="the project brief fixes this dimension",
        provenance=(Provenance(actor="user", source_id="brief-9"),),
    )
    request = AlignmentRequest(
        decision_id="intent-over-conflicting-taste",
        dimensions=("palette",),
        material=True,
        taste=taste,
        intent=(intent,),
    )

    result = resolve_alignment(request)
    resolved = result.dimensions["palette"]

    assert resolved.direction == "monochrome"
    assert resolved.governing_source == "intent"
    assert resolved.inputs.taste == taste
    assert resolved.inputs.intent == (intent,)
    assert len(resolved.conflicts) == 1
    assert resolved.conflicts[0].source == "taste"
    assert resolved.conflicts[0].blocking is False
    assert result.unresolved_dimensions == ()
    assert result.propagation_eligible is True


def test_unrelated_dimension_change_does_not_stale_alignment() -> None:
    original = AlignmentRequest(
        decision_id="palette-only",
        dimensions=("palette",),
        material=True,
        taste=(preference(direction="warm", confidence=0.9, strength=0.7),),
    )
    with_unrelated_motion = AlignmentRequest(
        decision_id=original.decision_id,
        dimensions=original.dimensions,
        material=original.material,
        taste=original.taste,
        intent=(
            DecisionDirective(
                dimension="motion",
                direction="springy",
                reason="unrelated motion decision",
                provenance=(Provenance(actor="user", source_id="motion-1"),),
            ),
        ),
    )

    result = resolve_alignment(original)

    assert is_alignment_stale(result, with_unrelated_motion) is False


def test_known_indifference_uses_authorized_craft_without_calibration() -> None:
    indifferent = preference(
        direction=None,
        disposition="indifferent",
        confidence=0.95,
        strength=0,
    )
    craft_prior = DecisionDirective(
        dimension="palette",
        direction="balanced-neutral",
        reason="safe craft default",
        provenance=(Provenance(actor="agent", source_id="craft-2"),),
    )
    request = AlignmentRequest(
        decision_id="indifferent-palette",
        dimensions=("palette",),
        material=True,
        taste=(indifferent,),
        authority=(
            AuthorityScope(
                actor="agent",
                dimensions=("palette",),
                allows_material_propagation=True,
                checkpoint_required=False,
                scope=Scope(
                    kind="project",
                    identity="project-a",
                    represented_subject="user",
                ),
                provenance=(Provenance(actor="user", source_id="delegation-3"),),
            ),
        ),
        craft_priors=(craft_prior,),
    )

    result = resolve_alignment(request)
    resolved = result.dimensions["palette"]

    assert resolved.direction == "balanced-neutral"
    assert resolved.governing_source == "craft_prior"
    assert resolved.taste is indifferent
    assert resolved.taste.disposition == "indifferent"
    assert result.checkpoint_obligations == ()
    assert result.propagation_eligible is True
    assert_resolution_scenario(
        name="known indifference suppresses preference calibration",
        request=request,
        dimension="palette",
        expected_direction="balanced-neutral",
        expected_source="craft_prior",
        expected_propagation=True,
    )
