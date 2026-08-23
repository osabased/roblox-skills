from alignment_harness import (
    AlignmentRequest,
    AuthorityScope,
    CompositionRequest,
    CompositionTarget,
    DecisionDirective,
    PreferenceKnowledge,
    PropertyPath,
    ProfileProperty,
    ProfileSelection,
    Provenance,
    RelationalRequirement,
    Scope,
    ScopeIdentity,
    ScopeTransition,
    TransferPolicy,
    ValidationContext,
    compose_profiles,
    enforce_relational_alignment,
    is_alignment_stale,
    resolve_alignment,
    transition_local_scope,
)


def profile_property(
    *,
    claim_id: str,
    section: str,
    property_name: str,
    direction: str | None,
    scope_kind: str,
    scope_identity: str,
    confidence: float = 0.8,
    context: dict[str, str] | None = None,
    relationships: dict[str, str] | None = None,
    explicit_overrides: tuple[str, ...] = (),
    validation_domain: str = "ui",
    validation_conditions: tuple[str, ...] = (),
    owner: str | None = None,
    evidence_applicable: bool = True,
    represented_subject: str = "user-1",
    disposition: str = "preferred",
    relational_requirements: tuple[RelationalRequirement, ...] = (),
) -> ProfileProperty:
    knowledge = PreferenceKnowledge(
        dimension=property_name,
        direction=direction,
        disposition=disposition,
        basis="explicit",
        confidence=confidence,
        strength=0.7,
        scope=Scope(
            kind=scope_kind,
            identity=scope_identity,
            represented_subject=represented_subject,
        ),
        context=context or {},
        evidence=(f"evidence:{claim_id}",),
        provenance=(Provenance(actor="user", source_id=f"source:{claim_id}"),),
        validation_context=ValidationContext(
            domain=validation_domain,
            fidelity="implemented",
            conditions=validation_conditions,
        ),
        relationships=relationships or {},
    )
    return ProfileProperty(
        claim_id=claim_id,
        section=section,
        knowledge=knowledge,
        explicit_overrides=explicit_overrides,
        owner=owner,
        evidence_applicable=evidence_applicable,
        relational_requirements=relational_requirements,
    )


def target() -> CompositionTarget:
    return CompositionTarget(
        represented_subject="user-1",
        scope_identities={
            "user": "user-1",
            "domain": "ui",
            "project": "project-a",
            "session": "session-current",
            "local": "artifact-a",
        },
        domain="ui",
        context={"surface": "settings", "device": "desktop"},
        validation_conditions=("desktop",),
        exposed_properties={
            "typography": ("family",),
            "layout": ("density",),
        },
    )


def test_explicit_project_override_beats_narrower_session_claim_without_hiding_local_layout() -> None:
    session_typography = profile_property(
        claim_id="session-type",
        section="typography",
        property_name="family",
        direction="sans",
        scope_kind="session",
        scope_identity="session-current",
        confidence=0.3,
    )
    project_typography = profile_property(
        claim_id="project-type",
        section="typography",
        property_name="family",
        direction="serif",
        scope_kind="project",
        scope_identity="project-a",
        explicit_overrides=("session-type",),
    )
    local_layout = profile_property(
        claim_id="local-layout",
        section="layout",
        property_name="density",
        direction="compact",
        scope_kind="local",
        scope_identity="artifact-a",
    )

    result = compose_profiles(
        CompositionRequest(
            target=target(),
            properties=(session_typography, project_typography, local_layout),
        )
    )

    assert result.conflicts == ()
    assert result.properties[PropertyPath("typography", "family")].direction == "serif"
    assert result.properties[PropertyPath("typography", "family")].claim_ids == (
        "project-type",
    )
    assert result.properties[PropertyPath("layout", "density")].direction == "compact"
    assert tuple(
        (
            overridden.property.claim_id,
            overridden.overridden_by_claim_id,
        )
        for overridden in result.overridden
    ) == (("session-type", "project-type"),)
    assert result.provenance == (
        Provenance(actor="user", source_id="source:project-type"),
        Provenance(actor="user", source_id="source:local-layout"),
    )


def test_expired_or_unrelated_scopes_remain_historical_without_entering_resolution() -> None:
    expired_session = profile_property(
        claim_id="old-session",
        section="typography",
        property_name="family",
        direction="serif",
        scope_kind="session",
        scope_identity="session-expired",
    )
    unrelated_project = profile_property(
        claim_id="other-project",
        section="layout",
        property_name="density",
        direction="spacious",
        scope_kind="project",
        scope_identity="project-b",
    )
    other_artifact = profile_property(
        claim_id="other-artifact",
        section="layout",
        property_name="density",
        direction="compact",
        scope_kind="local",
        scope_identity="artifact-b",
    )
    other_subject = profile_property(
        claim_id="other-subject",
        section="layout",
        property_name="density",
        direction="compact",
        scope_kind="project",
        scope_identity="project-a",
        represented_subject="client-1",
    )

    result = compose_profiles(
        CompositionRequest(
            target=target(),
            properties=(
                expired_session,
                unrelated_project,
                other_artifact,
                other_subject,
            ),
        )
    )

    assert result.properties == {}
    assert tuple((item.property.claim_id, item.reason) for item in result.excluded) == (
        ("old-session", "scope identity is not active for this decision"),
        ("other-project", "scope identity is not active for this decision"),
        ("other-artifact", "scope identity is not active for this decision"),
        ("other-subject", "represented subject does not match this decision"),
    )


def test_full_section_and_property_application_select_only_requested_domain_properties() -> None:
    properties = (
        profile_property(
            claim_id="type-family",
            section="typography",
            property_name="family",
            direction="serif",
            scope_kind="project",
            scope_identity="project-a",
        ),
        profile_property(
            claim_id="type-scale",
            section="typography",
            property_name="scale",
            direction="compact",
            scope_kind="project",
            scope_identity="project-a",
        ),
        profile_property(
            claim_id="layout-density",
            section="layout",
            property_name="density",
            direction="spacious",
            scope_kind="project",
            scope_identity="project-a",
        ),
    )
    application_target = CompositionTarget(
        represented_subject="user-1",
        scope_identities=target().scope_identities,
        domain="ui",
        context=target().context,
        validation_conditions=("desktop",),
        exposed_properties={
            "typography": ("family", "scale"),
            "layout": ("density",),
        },
    )

    full = compose_profiles(
        CompositionRequest(target=application_target, properties=properties)
    )
    section = compose_profiles(
        CompositionRequest(
            target=application_target,
            properties=properties,
            selection=ProfileSelection(sections=("typography",)),
        )
    )
    one_property = compose_profiles(
        CompositionRequest(
            target=application_target,
            properties=properties,
            selection=ProfileSelection(
                properties=(PropertyPath("typography", "family"),)
            ),
        )
    )

    assert tuple(full.properties) == (
        ("typography", "family"),
        ("typography", "scale"),
        ("layout", "density"),
    )
    assert tuple(section.properties) == (
        ("typography", "family"),
        ("typography", "scale"),
    )
    assert tuple(one_property.properties) == (("typography", "family"),)


def test_requested_scope_can_omit_an_active_scope_without_hiding_its_identity() -> None:
    user_layout = profile_property(
        claim_id="user-layout",
        section="layout",
        property_name="density",
        direction="compact",
        scope_kind="user",
        scope_identity="user-1",
    )
    active_project_typography = profile_property(
        claim_id="project-type",
        section="typography",
        property_name="family",
        direction="serif",
        scope_kind="project",
        scope_identity="project-a",
    )

    result = compose_profiles(
        CompositionRequest(
            target=target(),
            properties=(user_layout, active_project_typography),
            selection=ProfileSelection(
                scopes=(ScopeIdentity("user", "user-1"),)
            ),
        )
    )

    assert tuple(result.properties) == (("layout", "density"),)
    assert result.excluded[0].property is active_project_typography
    assert result.excluded[0].reason == (
        "scope is outside the requested application"
    )


def test_same_property_name_in_different_sections_remains_distinct_in_alignment() -> None:
    typography_scale = profile_property(
        claim_id="typography-scale",
        section="typography",
        property_name="scale",
        direction="compact",
        scope_kind="project",
        scope_identity="project-a",
    )
    motion_scale = profile_property(
        claim_id="motion-scale",
        section="motion",
        property_name="scale",
        direction="subtle",
        scope_kind="project",
        scope_identity="project-a",
    )
    sectioned_target = CompositionTarget(
        represented_subject="user-1",
        scope_identities=target().scope_identities,
        domain="ui",
        context=target().context,
        validation_conditions=("desktop",),
        exposed_properties={
            "typography": ("scale",),
            "motion": ("scale",),
        },
    )
    composition = compose_profiles(
        CompositionRequest(
            target=sectioned_target,
            properties=(typography_scale, motion_scale),
        )
    )
    alignment = resolve_alignment(
        AlignmentRequest(
            decision_id="sectioned-scale",
            dimensions=composition.alignment_dimensions,
            material=False,
            taste=composition.alignment_taste,
        )
    )

    assert composition.alignment_dimensions == (
        "typography.scale",
        "motion.scale",
    )
    assert tuple(knowledge.dimension for knowledge in composition.alignment_taste) == (
        "typography.scale",
        "motion.scale",
    )
    assert alignment.dimensions["typography.scale"].direction == "compact"
    assert alignment.dimensions["motion.scale"].direction == "subtle"


def test_compatible_scoped_knowledge_composes_provenance_and_relational_meaning() -> None:
    user_layout = profile_property(
        claim_id="user-layout",
        section="layout",
        property_name="density",
        direction="compact",
        scope_kind="user",
        scope_identity="user-1",
        context={"surface": "settings"},
        relationships={"hierarchy": "strong", "rhythm": "tight"},
    )
    project_layout = profile_property(
        claim_id="project-layout",
        section="layout",
        property_name="density",
        direction="compact",
        scope_kind="project",
        scope_identity="project-a",
        context={"device": "desktop"},
        relationships={"contrast": "high", "pacing": "deliberate"},
    )

    result = compose_profiles(
        CompositionRequest(target=target(), properties=(user_layout, project_layout))
    )

    composed = result.properties[PropertyPath("layout", "density")]
    assert composed.direction == "compact"
    assert composed.claim_ids == ("user-layout", "project-layout")
    assert composed.relationships == {
        "hierarchy": "strong",
        "rhythm": "tight",
        "contrast": "high",
        "pacing": "deliberate",
    }
    assert result.provenance == (
        Provenance(actor="user", source_id="source:user-layout"),
        Provenance(actor="user", source_id="source:project-layout"),
    )


def test_cross_property_relationship_conflict_blocks_the_incompatible_bundle() -> None:
    dense_layout = profile_property(
        claim_id="dense-layout",
        section="layout",
        property_name="density",
        direction="dense",
        scope_kind="project",
        scope_identity="project-a",
        relational_requirements=(
            RelationalRequirement(
                property_path=PropertyPath("color", "palette"),
                direction="restrained",
            ),
        ),
    )
    vivid_color = profile_property(
        claim_id="vivid-color",
        section="color",
        property_name="palette",
        direction="vivid",
        scope_kind="project",
        scope_identity="project-a",
    )
    relational_target = CompositionTarget(
        represented_subject="user-1",
        scope_identities=target().scope_identities,
        domain="ui",
        context=target().context,
        validation_conditions=("desktop",),
        exposed_properties={
            "layout": ("density",),
            "color": ("palette",),
        },
    )

    composition = compose_profiles(
        CompositionRequest(
            target=relational_target,
            properties=(dense_layout, vivid_color),
        )
    )
    alignment = resolve_alignment(
        AlignmentRequest(
            decision_id="incompatible-bundle",
            dimensions=composition.alignment_dimensions,
            material=True,
            taste=composition.alignment_taste,
        )
    )
    result = enforce_relational_alignment(composition, alignment)

    assert len(result.conflicts) == 1
    assert result.conflicts[0].related_paths == (
        ("layout", "density"),
        ("color", "palette"),
    )
    assert result.conflicts[0].inputs == (dense_layout, vivid_color)
    assert result.conflicts[0].reason == (
        "relational requirement requires color.palette=restrained, got vivid"
    )
    assert result.alignment.dimensions["layout.density"].direction is None
    assert result.alignment.propagation_eligible is False


def test_missing_relational_dependency_keeps_the_conditional_claim_unresolved() -> None:
    dense_layout = profile_property(
        claim_id="dense-layout",
        section="layout",
        property_name="density",
        direction="dense",
        scope_kind="project",
        scope_identity="project-a",
        relational_requirements=(
            RelationalRequirement(
                property_path=PropertyPath("color", "palette"),
                direction="restrained",
            ),
        ),
    )

    composition = compose_profiles(
        CompositionRequest(target=target(), properties=(dense_layout,))
    )
    alignment = resolve_alignment(
        AlignmentRequest(
            decision_id="missing-required-color",
            dimensions=composition.alignment_dimensions,
            material=True,
            taste=composition.alignment_taste,
        )
    )
    result = enforce_relational_alignment(composition, alignment)

    assert result.conflicts[0].related_paths == (
        ("layout", "density"),
        ("color", "palette"),
    )
    assert result.conflicts[0].reason == (
        "relational requirement requires color.palette=restrained, got unresolved"
    )


def test_resolved_intent_can_satisfy_a_profile_relationship() -> None:
    dense_layout = profile_property(
        claim_id="dense-layout",
        section="layout",
        property_name="density",
        direction="dense",
        scope_kind="project",
        scope_identity="project-a",
        relational_requirements=(
            RelationalRequirement(
                property_path=PropertyPath("color", "palette"),
                direction="restrained",
            ),
        ),
    )
    composition = compose_profiles(
        CompositionRequest(target=target(), properties=(dense_layout,))
    )
    alignment = resolve_alignment(
        AlignmentRequest(
            decision_id="intent-satisfies-color-relation",
            dimensions=composition.alignment_dimensions,
            material=False,
            taste=composition.alignment_taste,
            intent=(
                DecisionDirective(
                    dimension="color.palette",
                    direction="restrained",
                    reason="current artifact intent",
                    provenance=(Provenance(actor="user", source_id="intent-color"),),
                ),
            ),
        )
    )

    result = enforce_relational_alignment(composition, alignment)

    assert result.conflicts == ()
    assert result.alignment.dimensions["layout.density"].direction == "dense"
    assert result.alignment.dimensions["color.palette"].governing_source == "intent"


def test_non_governing_conditional_taste_cannot_override_dependent_intent() -> None:
    dense_layout = profile_property(
        claim_id="dense-layout",
        section="layout",
        property_name="density",
        direction="dense",
        scope_kind="project",
        scope_identity="project-a",
        relational_requirements=(
            RelationalRequirement(
                property_path=PropertyPath("color", "palette"),
                direction="restrained",
            ),
        ),
    )
    composition = compose_profiles(
        CompositionRequest(target=target(), properties=(dense_layout,))
    )
    alignment = resolve_alignment(
        AlignmentRequest(
            decision_id="intent-overrides-conditional-taste",
            dimensions=composition.alignment_dimensions,
            material=True,
            taste=composition.alignment_taste,
            intent=(
                DecisionDirective(
                    dimension="layout.density",
                    direction="spacious",
                    reason="current artifact intent",
                    provenance=(Provenance(actor="user", source_id="intent-density"),),
                ),
            ),
        )
    )

    result = enforce_relational_alignment(composition, alignment)

    assert result.conflicts == ()
    assert result.alignment.dimensions["layout.density"].direction == "spacious"
    assert result.alignment.dimensions["layout.density"].governing_source == "intent"


def test_relational_invalidation_propagates_to_a_fixed_point() -> None:
    first = profile_property(
        claim_id="first",
        section="composition",
        property_name="a",
        direction="a-on",
        scope_kind="project",
        scope_identity="project-a",
        relational_requirements=(
            RelationalRequirement(PropertyPath("composition", "b"), "b-on"),
        ),
    )
    second = profile_property(
        claim_id="second",
        section="composition",
        property_name="b",
        direction="b-on",
        scope_kind="project",
        scope_identity="project-a",
        relational_requirements=(
            RelationalRequirement(PropertyPath("composition", "c"), "c-on"),
        ),
    )
    chain_target = CompositionTarget(
        represented_subject="user-1",
        scope_identities=target().scope_identities,
        domain="ui",
        context=target().context,
        validation_conditions=("desktop",),
        exposed_properties={"composition": ("a", "b", "c")},
    )
    composition = compose_profiles(
        CompositionRequest(target=chain_target, properties=(first, second))
    )
    alignment = resolve_alignment(
        AlignmentRequest(
            decision_id="relationship-chain",
            dimensions=composition.alignment_dimensions,
            material=True,
            taste=composition.alignment_taste,
        )
    )

    result = enforce_relational_alignment(composition, alignment)

    assert tuple(conflict.path.property_name for conflict in result.conflicts) == (
        "b",
        "a",
    )
    assert result.alignment.dimensions["composition.a"].direction is None
    assert result.alignment.dimensions["composition.b"].direction is None
    assert result.alignment.unresolved_dimensions == (
        "composition.c",
        "composition.b",
        "composition.a",
    )


def test_rejected_matching_direction_does_not_satisfy_a_relationship() -> None:
    dense_layout = profile_property(
        claim_id="dense-layout",
        section="layout",
        property_name="density",
        direction="dense",
        scope_kind="project",
        scope_identity="project-a",
        relational_requirements=(
            RelationalRequirement(
                property_path=PropertyPath("color", "palette"),
                direction="restrained",
            ),
        ),
    )
    rejected_color = profile_property(
        claim_id="reject-restrained",
        section="color",
        property_name="palette",
        direction="restrained",
        disposition="rejected",
        scope_kind="project",
        scope_identity="project-a",
    )
    relational_target = CompositionTarget(
        represented_subject="user-1",
        scope_identities=target().scope_identities,
        domain="ui",
        context=target().context,
        validation_conditions=("desktop",),
        exposed_properties={
            "layout": ("density",),
            "color": ("palette",),
        },
    )
    composition = compose_profiles(
        CompositionRequest(
            target=relational_target,
            properties=(dense_layout, rejected_color),
        )
    )
    alignment = resolve_alignment(
        AlignmentRequest(
            decision_id="rejected-color-relation",
            dimensions=composition.alignment_dimensions,
            material=False,
            taste=composition.alignment_taste,
        )
    )

    result = enforce_relational_alignment(composition, alignment)

    assert result.conflicts[0].actual_source is None
    assert result.alignment.dimensions["layout.density"].direction is None


def test_relationship_change_stales_prior_alignment_revision() -> None:
    def composition_requiring(direction: str):
        layout = profile_property(
            claim_id="dense-layout",
            section="layout",
            property_name="density",
            direction="dense",
            scope_kind="project",
            scope_identity="project-a",
            relational_requirements=(
                RelationalRequirement(
                    property_path=PropertyPath("color", "palette"),
                    direction=direction,
                ),
            ),
        )
        return compose_profiles(
            CompositionRequest(target=target(), properties=(layout,))
        )

    original = composition_requiring("restrained")
    changed = composition_requiring("vivid")
    original_request = AlignmentRequest(
        decision_id="relationship-revision",
        dimensions=original.alignment_dimensions,
        material=True,
        taste=original.alignment_taste,
        context_revision=original.context_revision("host-revision-1"),
    )
    old_alignment = resolve_alignment(original_request)
    changed_request = AlignmentRequest(
        decision_id=original_request.decision_id,
        dimensions=original_request.dimensions,
        material=True,
        taste=changed.alignment_taste,
        context_revision=changed.context_revision("host-revision-1"),
    )

    assert original.context_revision("host-revision-1") != changed.context_revision(
        "host-revision-1"
    )
    assert is_alignment_stale(old_alignment, changed_request) is True


def test_incompatible_directions_remain_an_explicit_unaveraged_conflict() -> None:
    warm = profile_property(
        claim_id="warm",
        section="typography",
        property_name="family",
        direction="warm-serif",
        scope_kind="user",
        scope_identity="user-1",
    )
    cool = profile_property(
        claim_id="cool",
        section="typography",
        property_name="family",
        direction="cool-sans",
        scope_kind="project",
        scope_identity="project-a",
    )

    result = compose_profiles(
        CompositionRequest(target=target(), properties=(warm, cool))
    )

    assert ("typography", "family") not in result.properties
    assert len(result.conflicts) == 1
    assert result.conflicts[0].path == ("typography", "family")
    assert result.conflicts[0].inputs == (warm, cool)
    assert result.conflicts[0].reason == (
        "semantically incompatible applicable knowledge"
    )
    assert result.alignment_dimensions == ("typography.family",)

    alignment = resolve_alignment(
        AlignmentRequest(
            decision_id="conflicted-profile-property",
            dimensions=result.alignment_dimensions,
            material=True,
            taste=result.alignment_taste,
        )
    )

    assert alignment.propagation_eligible is False
    assert alignment.unresolved_dimensions == (
        "typography.family",
    )


def test_alignment_dimension_encoding_is_injective_for_dotted_path_components() -> None:
    dotted_section = PropertyPath("visual.motion", "scale")
    dotted_property = PropertyPath("visual", "motion.scale")

    assert dotted_section.alignment_dimension == "visual%2Emotion.scale"
    assert dotted_property.alignment_dimension == "visual.motion%2Escale"
    assert dotted_section.alignment_dimension != dotted_property.alignment_dimension


def test_explicit_cross_domain_transfer_reduces_confidence_without_mutating_knowledge() -> None:
    writing_rhythm = profile_property(
        claim_id="writing-rhythm",
        section="layout",
        property_name="density",
        direction="restrained",
        scope_kind="domain",
        scope_identity="writing",
        confidence=0.8,
        validation_domain="writing",
        validation_conditions=("long-form",),
    )

    without_transfer = compose_profiles(
        CompositionRequest(target=target(), properties=(writing_rhythm,))
    )
    with_transfer = compose_profiles(
        CompositionRequest(
            target=target(),
            properties=(writing_rhythm,),
            transfer_policy=TransferPolicy(
                source_domains=("writing",), confidence_factor=0.5
            ),
        )
    )

    assert without_transfer.properties == {}
    assert without_transfer.excluded[0].reason == (
        "scope identity is not active for this decision"
    )
    composed = with_transfer.properties[PropertyPath("layout", "density")]
    assert composed.direction == "restrained"
    assert composed.effective_confidences == {"writing-rhythm": 0.4}
    assert composed.confidence_adjustments == {
        "writing-rhythm": ("cross-domain transfer", "distant validation context")
    }
    assert with_transfer.alignment_taste[0].confidence == 0.4
    assert writing_rhythm.knowledge.confidence == 0.8


def test_same_domain_distant_context_requires_an_explicit_reduced_confidence_transfer() -> None:
    mobile_layout = profile_property(
        claim_id="mobile-layout",
        section="layout",
        property_name="density",
        direction="spacious",
        scope_kind="user",
        scope_identity="user-1",
        confidence=0.8,
        validation_conditions=("mobile",),
    )

    no_policy = compose_profiles(
        CompositionRequest(target=target(), properties=(mobile_layout,))
    )
    unrelated_policy = compose_profiles(
        CompositionRequest(
            target=target(),
            properties=(mobile_layout,),
            transfer_policy=TransferPolicy(
                source_domains=("writing",), confidence_factor=0.5
            ),
        )
    )
    explicit_transfer = compose_profiles(
        CompositionRequest(
            target=target(),
            properties=(mobile_layout,),
            transfer_policy=TransferPolicy(
                source_domains=(),
                confidence_factor=0.5,
                allow_distant_context=True,
            ),
        )
    )

    assert no_policy.properties == {}
    assert unrelated_policy.properties == {}
    assert no_policy.excluded[0].reason == (
        "validation context does not support direct reuse"
    )
    assert explicit_transfer.properties[
        PropertyPath("layout", "density")
    ].effective_confidences == {
        "mobile-layout": 0.4
    }


def test_expired_session_delegation_remains_historical_and_inactive() -> None:
    current = AuthorityScope(
        actor="agent",
        dimensions=("density",),
        allows_material_propagation=True,
        checkpoint_required=False,
        scope=Scope(
            kind="session",
            identity="session-current",
            represented_subject="user-1",
        ),
        provenance=(Provenance(actor="user", source_id="delegation-current"),),
    )
    expired = AuthorityScope(
        actor="agent",
        dimensions=("density",),
        allows_material_propagation=True,
        checkpoint_required=False,
        scope=Scope(
            kind="session",
            identity="session-expired",
            represented_subject="user-1",
        ),
        provenance=(Provenance(actor="user", source_id="delegation-expired"),),
    )

    result = compose_profiles(
        CompositionRequest(
            target=target(),
            properties=(),
            authority=(expired, current),
        )
    )

    assert result.alignment_authority == (current,)
    assert tuple(
        (excluded.authority, excluded.reason)
        for excluded in result.excluded_authority
    ) == ((expired, "scope identity is not active for this decision"),)


def test_local_identity_operations_preserve_replace_or_surface_ambiguity_explicitly() -> None:
    local = profile_property(
        claim_id="artifact-layout",
        section="layout",
        property_name="density",
        direction="compact",
        scope_kind="local",
        scope_identity="artifact-a",
    )

    moved = transition_local_scope(
        local,
        ScopeTransition(
            operation="move",
            source_identity="artifact-a",
            target_identity="artifact-a",
            outcome="preserve",
        ),
    )
    duplicated = transition_local_scope(
        local,
        ScopeTransition(
            operation="duplicate",
            source_identity="artifact-a",
            target_identity="artifact-b",
            outcome="replace",
        ),
    )
    copied = transition_local_scope(
        local,
        ScopeTransition(
            operation="copy",
            source_identity="artifact-a",
            target_identity="artifact-c",
            outcome="replace",
        ),
    )
    branched = transition_local_scope(
        local,
        ScopeTransition(
            operation="branch",
            source_identity="artifact-a",
            target_identity="artifact-branch",
            outcome="ambiguous",
        ),
    )

    assert moved.status == "preserved"
    assert moved.target_property is local
    assert duplicated.status == "replaced"
    assert duplicated.source_property is local
    assert duplicated.target_property is not None
    assert duplicated.target_property.knowledge.scope.identity == "artifact-b"
    assert duplicated.target_property.claim_id == "artifact-layout@artifact-b"
    assert copied.target_property is not None
    assert copied.target_property.knowledge.scope.identity == "artifact-c"
    assert branched.status == "ambiguous"
    assert branched.target_property is None
    assert branched.checkpoint == "resolve-local-scope:branch:artifact-layout"


def test_replacement_transition_requires_a_new_local_identity() -> None:
    try:
        ScopeTransition(
            operation="copy",
            source_identity="artifact-a",
            target_identity="artifact-a",
            outcome="replace",
        )
    except ValueError as error:
        assert "new local identity" in str(error)
    else:
        raise AssertionError("replacement retained the source local identity")


def test_evidence_context_and_ownership_must_be_observable_before_application() -> None:
    unknown_owner = profile_property(
        claim_id="unknown-owner",
        section="layout",
        property_name="density",
        direction="compact",
        scope_kind="project",
        scope_identity="project-a",
        owner="client",
    )
    superseded = profile_property(
        claim_id="superseded",
        section="typography",
        property_name="family",
        direction="serif",
        scope_kind="project",
        scope_identity="project-a",
        evidence_applicable=False,
    )
    wrong_context = profile_property(
        claim_id="mobile-only",
        section="layout",
        property_name="density",
        direction="spacious",
        scope_kind="project",
        scope_identity="project-a",
        context={"device": "mobile"},
    )

    result = compose_profiles(
        CompositionRequest(
            target=target(),
            properties=(unknown_owner, superseded, wrong_context),
        )
    )

    assert result.properties == {}
    assert tuple((item.property.claim_id, item.reason) for item in result.excluded) == (
        ("unknown-owner", "property ownership is not established for this decision"),
        ("superseded", "supporting evidence is not applicable"),
        ("mobile-only", "profile context does not apply to this decision"),
    )


def test_mutual_override_cycle_remains_an_explicit_conflict() -> None:
    first = profile_property(
        claim_id="first",
        section="typography",
        property_name="family",
        direction="serif",
        scope_kind="project",
        scope_identity="project-a",
        explicit_overrides=("second",),
    )
    second = profile_property(
        claim_id="second",
        section="typography",
        property_name="family",
        direction="sans",
        scope_kind="session",
        scope_identity="session-current",
        explicit_overrides=("first",),
    )

    result = compose_profiles(
        CompositionRequest(target=target(), properties=(first, second))
    )

    assert result.properties == {}
    assert result.conflicts[0].inputs == (first, second)


def test_indifference_and_unresolved_taste_survive_composition_into_alignment() -> None:
    indifferent = profile_property(
        claim_id="indifferent-density",
        section="layout",
        property_name="density",
        direction=None,
        disposition="indifferent",
        scope_kind="user",
        scope_identity="user-1",
    )
    unresolved = profile_property(
        claim_id="unresolved-family",
        section="typography",
        property_name="family",
        direction=None,
        disposition="unresolved",
        scope_kind="project",
        scope_identity="project-a",
    )

    composition = compose_profiles(
        CompositionRequest(target=target(), properties=(indifferent, unresolved))
    )
    alignment = resolve_alignment(
        AlignmentRequest(
            decision_id="unknown-settings",
            dimensions=composition.alignment_dimensions,
            material=True,
            taste=composition.alignment_taste,
        )
    )

    assert composition.properties[
        PropertyPath("layout", "density")
    ].direction is None
    assert composition.properties[
        PropertyPath("typography", "family")
    ].direction is None
    assert tuple(
        knowledge.disposition for knowledge in composition.alignment_taste
    ) == ("indifferent", "unresolved")
    assert alignment.dimensions["layout.density"].governing_source == "known_indifference"
    assert alignment.dimensions["typography.family"].governing_source is None
    assert alignment.unresolved_dimensions == (
        "layout.density",
        "typography.family",
    )


def test_composed_taste_flows_through_the_canonical_alignment_contract() -> None:
    typography = profile_property(
        claim_id="project-type",
        section="typography",
        property_name="family",
        direction="serif",
        scope_kind="project",
        scope_identity="project-a",
    )
    layout = profile_property(
        claim_id="local-layout",
        section="layout",
        property_name="density",
        direction="compact",
        scope_kind="local",
        scope_identity="artifact-a",
    )
    composition = compose_profiles(
        CompositionRequest(target=target(), properties=(typography, layout))
    )

    alignment = resolve_alignment(
        AlignmentRequest(
            decision_id="settings-composition",
            dimensions=composition.alignment_dimensions,
            material=False,
            taste=composition.alignment_taste,
        )
    )

    assert alignment.unresolved_dimensions == ()
    assert alignment.dimensions["typography.family"].direction == "serif"
    assert alignment.dimensions["layout.density"].direction == "compact"
    assert tuple(
        dimension.governing_source for dimension in alignment.dimensions.values()
    ) == ("taste", "taste")


def test_whole_system_check_catches_drift_that_local_approvals_miss() -> None:
    # Decision 1 (approved earlier): a density choice that relationally
    # depends on the palette staying restrained.
    dense_layout = profile_property(
        claim_id="approved-dense-layout",
        section="layout",
        property_name="density",
        direction="dense",
        scope_kind="project",
        scope_identity="project-a",
        relational_requirements=(
            RelationalRequirement(
                property_path=PropertyPath("color", "palette"),
                direction="restrained",
            ),
        ),
    )
    # Decision 2 (approved later, in isolation): a palette shift that is
    # individually valid and conflicts with nothing on its own.
    vivid_palette = profile_property(
        claim_id="approved-vivid-palette",
        section="color",
        property_name="palette",
        direction="vivid",
        scope_kind="project",
        scope_identity="project-a",
    )
    sweep_target = CompositionTarget(
        represented_subject="user-1",
        scope_identities=target().scope_identities,
        domain="ui",
        context=target().context,
        validation_conditions=("desktop",),
        exposed_properties={
            "layout": ("density",),
            "color": ("palette",),
        },
    )
    composition = compose_profiles(
        CompositionRequest(
            target=sweep_target,
            properties=(dense_layout, vivid_palette),
        )
    )
    alignment = resolve_alignment(
        AlignmentRequest(
            decision_id="periodic-coherence-sweep",
            dimensions=composition.alignment_dimensions,
            material=True,
            taste=composition.alignment_taste,
        )
    )

    # Each locally approved decision looks fine in isolation: both
    # dimensions resolve to established taste with no local conflict.
    assert alignment.unresolved_dimensions == ()
    assert (
        alignment.dimensions["layout.density"].governing_source == "taste"
    )
    assert alignment.dimensions["color.palette"].governing_source == "taste"

    swept = enforce_relational_alignment(composition, alignment)

    # The periodic whole-system check is what catches the relational drift.
    assert len(swept.conflicts) == 1
    conflict = swept.conflicts[0]
    assert conflict.path.property_name == "density"
    assert "restrained" in conflict.reason
    assert conflict.related_paths[1] == PropertyPath("color", "palette")
    assert swept.alignment.dimensions["layout.density"].direction is None
    assert "layout.density" in swept.alignment.unresolved_dimensions
    assert swept.alignment.propagation_eligible is False
    assert "resolve-relation:layout.density" in (
        swept.alignment.checkpoint_obligations
    )
