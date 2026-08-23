"""Behavioral scenarios for profile lifecycle epistemic boundaries."""

from __future__ import annotations

import json

import pytest

from alignment_contract import (
    Disposition,
    EpistemicBasis,
    PreferenceKnowledge,
    Provenance,
    Scope,
    ValidationContext,
)
from evidence_reconciliation import (
    Ambiguity,
    ClaimResolution,
    ClaimStatus,
    Consequence,
    EvidenceEvent,
    EvidenceIdentityConflictError,
    EvidenceImplication,
    EvidenceState,
    EvidenceType,
    FeedbackKind,
    Fidelity,
    Judgment,
    OperationIdentityConflictError,
    PointClaim,
    SupportApplicability,
    SupportRef,
    SupportStrength,
)
from profile_composition import ProfileProperty
from profile_lifecycle import (
    BranchRegistry,
    ConsolidationRequest,
    CreateBranch,
    ImportProfileExchange,
    IngestProfileEvidence,
    LifecycleState,
    LifecycleStatus,
    LifecycleTransition,
    ProfileExchange,
    ResetSupport,
    RetractEvidence,
    SelectBranch,
    UndoLastOperation,
    apply_lifecycle_operation,
    consolidate_profiles,
    export_profile_exchange,
    initial_lifecycle_state,
    migrate_document,
)
from profile_persistence import (
    CURRENT_SCHEMA_VERSION,
    InvalidProfileStateError,
    ProfileState,
    UnsupportedSchemaVersionError,
    deserialize_profile_state,
    serialize_profile_state,
)


_SCOPE = Scope(
    kind="project",
    identity="project:alpha",
    represented_subject="user:1",
)

_VALIDATION = ValidationContext(
    domain="interface-design",
    fidelity="high",
    conditions=("desktop",),
)


def _implication(
    implication_id: str,
    dimension: str,
    direction: str,
    *,
    applicable_branches: tuple[str, ...] = (),
    strength: SupportStrength = SupportStrength.STRONG,
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
        epistemic_strength=strength,
        preference_strength=0.7,
        consequence=Consequence.REVERSIBLE,
        applicable_branches=applicable_branches,
    )


def _event(
    event_id: str,
    *implications: EvidenceImplication,
    origin_branch: str | None = None,
    occurred_at: int = 1,
) -> EvidenceEvent:
    return EvidenceEvent(
        event_id=event_id,
        evidence_type=EvidenceType.EXPLICIT_FEEDBACK,
        feedback=FeedbackKind.CORRECTION,
        judgment=Judgment.PREFERRED,
        scope=_SCOPE,
        context=(("device", "desktop"),),
        provenance=(
            Provenance(actor="user", source_id=f"message:{event_id}"),
        ),
        validation_context=_VALIDATION,
        occurred_at=occurred_at,
        origin_branch=origin_branch,
        implications=implications,
    )


def _provenance(source: str) -> tuple[Provenance, ...]:
    return (Provenance(actor="user", source_id=source),)


def _ingest(
    state: LifecycleState, event: EvidenceEvent
) -> LifecycleTransition:
    operation = IngestProfileEvidence(
        operation_id=f"ingest-{len(state.evidence.events) + 1}",
        event=event,
    )
    return apply_lifecycle_operation(state, operation)


def _claims_by_dimension(
    state: LifecycleState,
) -> dict[str, ClaimResolution]:
    return {claim.knowledge.dimension: claim for claim in state.evidence.claims}


def _property_for(claim: ClaimResolution, section: str) -> ProfileProperty:
    return ProfileProperty(
        claim_id=f"property:{claim.claim_id}",
        section=section,
        knowledge=claim.knowledge,
    )


def _profile(*properties: ProfileProperty) -> ProfileState:
    return ProfileState(
        schema_version=CURRENT_SCHEMA_VERSION,
        profile_id="profile:alpha",
        properties=tuple(properties),
    )


def _shared_layout_typography_event() -> EvidenceEvent:
    return _event(
        "feedback-1",
        _implication("layout", "layout.density", "compact"),
        _implication("typography", "typography.scale", "dense"),
    )


def test_targeted_reset_excludes_only_typography_and_keeps_history() -> None:
    event = _shared_layout_typography_event()
    seeded = _ingest(initial_lifecycle_state(_profile()), event)
    before_layout = _claims_by_dimension(seeded.state)["layout.density"]

    result = apply_lifecycle_operation(
        seeded.state,
        ResetSupport(
            operation_id="reset-typography",
            support=SupportRef("feedback-1", "typography"),
            reason="typography section relearn requested",
        ),
    )

    claims = _claims_by_dimension(result.state)
    assert "typography.scale" not in claims
    assert claims["layout.density"] == before_layout
    assert result.changed_claim_ids != ()
    assert result.state.evidence.events == (event,)
    assert len(result.state.evidence.support_lifecycle) == 1
    record = result.state.evidence.support_lifecycle[0]
    assert record.applicability is SupportApplicability.RESET_EXCLUDED
    assert record.operation_id == "reset-typography"
    assert record.support.stable_id == "feedback-1#typography"
    assert record.provenance == event.provenance


def test_unrelated_valid_evidence_survives_a_targeted_reset() -> None:
    state = _ingest(
        initial_lifecycle_state(_profile()), _shared_layout_typography_event()
    ).state
    state = _ingest(
        state,
        _event(
            "color-feedback",
            _implication("color", "color.saturation", "muted"),
            occurred_at=2,
        ),
    ).state
    before_layout = _claims_by_dimension(state)["layout.density"]
    before_color = _claims_by_dimension(state)["color.saturation"]

    result = apply_lifecycle_operation(
        state,
        ResetSupport(
            operation_id="reset-typography",
            support=SupportRef("feedback-1", "typography"),
        ),
    )

    claims = _claims_by_dimension(result.state)
    assert claims["layout.density"] == before_layout
    assert claims["color.saturation"] == before_color
    assert "typography.scale" not in claims


def test_reingesting_the_same_event_cannot_resurrect_excluded_support() -> None:
    event = _shared_layout_typography_event()
    state = _ingest(initial_lifecycle_state(_profile()), event).state
    state = apply_lifecycle_operation(
        state,
        ResetSupport(
            operation_id="reset-typography",
            support=SupportRef("feedback-1", "typography"),
        ),
    ).state

    retry = apply_lifecycle_operation(
        state,
        IngestProfileEvidence(operation_id="delivery-retry", event=event),
    )

    assert retry.status is LifecycleStatus.DUPLICATE_EVENT
    claims = _claims_by_dimension(retry.state)
    assert "typography.scale" not in claims
    assert "layout.density" in claims


def test_relearning_after_reset_derives_only_from_genuinely_new_evidence() -> (
    None
):
    event = _shared_layout_typography_event()
    state = _ingest(initial_lifecycle_state(_profile()), event).state
    state = apply_lifecycle_operation(
        state,
        ResetSupport(
            operation_id="reset-typography",
            support=SupportRef("feedback-1", "typography"),
        ),
    ).state

    relearned = _ingest(
        state,
        _event(
            "feedback-2",
            _implication("typography", "typography.scale", "spacious"),
            occurred_at=3,
        ),
    )

    claim = _claims_by_dimension(relearned.state)["typography.scale"]
    assert claim.status is ClaimStatus.ESTABLISHED
    assert claim.knowledge.direction == "spacious"
    assert claim.knowledge.evidence == ("feedback-2#typography",)
    retained = [
        record
        for record in relearned.state.evidence.support_lifecycle
        if record.support.stable_id == "feedback-1#typography"
    ]
    assert retained and (
        retained[-1].applicability is SupportApplicability.RESET_EXCLUDED
    )


def test_retraction_recomputes_claims_while_preserving_provenance() -> None:
    event = _shared_layout_typography_event()
    state = _ingest(initial_lifecycle_state(_profile()), event).state
    state = _ingest(
        state,
        _event(
            "color-feedback",
            _implication("color", "color.saturation", "muted"),
            occurred_at=2,
        ),
    ).state

    result = apply_lifecycle_operation(
        state,
        RetractEvidence(
            operation_id="retract-mistake",
            event_id="feedback-1",
            reason="feedback was recorded against the wrong project",
        ),
    )

    claims = _claims_by_dimension(result.state)
    assert set(claims) == {"color.saturation"}
    assert result.state.evidence.events == state.evidence.events
    retracted = {
        record.support.stable_id: record
        for record in result.state.evidence.support_lifecycle
    }
    assert set(retracted) == {"feedback-1#layout", "feedback-1#typography"}
    assert all(
        record.applicability is SupportApplicability.RETRACTED
        and record.provenance == event.provenance
        and record.operation_id == "retract-mistake"
        for record in retracted.values()
    )


def test_undo_restores_profile_and_applicability_without_touching_artifacts() -> (
    None
):
    twin = _ingest(
        initial_lifecycle_state(_profile()), _shared_layout_typography_event()
    )
    owned_property = _property_for(
        _claims_by_dimension(twin.state)["typography.scale"], "typography"
    )
    state = _ingest(
        initial_lifecycle_state(_profile(owned_property)),
        _shared_layout_typography_event(),
    ).state
    unrelated_artifact = {"artifact-revision": "r7"}

    after_reset = apply_lifecycle_operation(
        state,
        ResetSupport(
            operation_id="reset-typography",
            support=SupportRef("feedback-1", "typography"),
        ),
    )
    assert owned_property.claim_id in after_reset.changed_property_ids
    assert after_reset.state.profile.properties[0].evidence_applicable is False
    assert "typography.scale" not in _claims_by_dimension(after_reset.state)

    undone = apply_lifecycle_operation(
        after_reset.state,
        UndoLastOperation(operation_id="undo-reset"),
    )

    assert undone.status is LifecycleStatus.UNDONE
    assert undone.state.profile == state.profile
    assert undone.state.evidence == state.evidence
    assert undone.changed_property_ids == (owned_property.claim_id,)
    assert "typography.scale" in _claims_by_dimension(undone.state)
    assert unrelated_artifact == {"artifact-revision": "r7"}

    fully_reverted = apply_lifecycle_operation(
        undone.state,
        UndoLastOperation(operation_id="undo-ingest"),
    )
    assert fully_reverted.state.evidence.events == ()
    with pytest.raises(ValueError, match="undo ledger is empty"):
        apply_lifecycle_operation(
            fully_reverted.state,
            UndoLastOperation(operation_id="undo-nothing"),
        )


def _branchy_state() -> LifecycleState:
    state = _ingest(
        initial_lifecycle_state(_profile()),
        _event(
            "global-pref",
            _implication("density", "layout.density", "airy"),
        ),
    ).state
    state = apply_lifecycle_operation(
        state,
        CreateBranch(
            operation_id="open-alt-a",
            branch_id="alt-a",
            provenance=_provenance("instruction:open-alt-a"),
        ),
    ).state
    return apply_lifecycle_operation(
        state,
        CreateBranch(
            operation_id="open-alt-b",
            branch_id="alt-b",
            parent_branch_id="alt-a",
            provenance=_provenance("instruction:open-alt-b"),
        ),
    ).state


_A_SCOPED = _event(
    "a-feedback",
    _implication(
        "timing",
        "motion.timing",
        "snappy",
        applicable_branches=("alt-a",),
    ),
    origin_branch="alt-a",
    occurred_at=2,
)

_B_SCOPED = _event(
    "b-feedback",
    _implication(
        "saturation",
        "color.saturation",
        "muted",
        applicable_branches=("alt-b",),
    ),
    origin_branch="alt-b",
    occurred_at=3,
)


def test_created_branch_stays_inapplicable_until_explicitly_selected() -> None:
    state = _branchy_state()

    dormant = _ingest(state, _B_SCOPED)

    assert "color.saturation" not in _claims_by_dimension(dormant.state)
    assert "layout.density" in _claims_by_dimension(dormant.state)
    child = dormant.state.branches.branch("alt-b")
    assert child is not None
    assert child.parent_branch_id == "alt-a"
    assert child.provenance == _provenance("instruction:open-alt-b")
    assert dormant.state.branches.active_branch_id is None

    selected = apply_lifecycle_operation(
        dormant.state,
        SelectBranch(operation_id="choose-alt-b", branch_id="alt-b"),
    )

    claims = _claims_by_dimension(selected.state)
    assert selected.state.branches.active_branch_id == "alt-b"
    assert "color.saturation" in claims
    assert "layout.density" in claims


def test_selecting_a_branch_makes_exactly_that_alternative_applicable() -> None:
    state = _ingest(_branchy_state(), _A_SCOPED).state
    state = _ingest(state, _B_SCOPED).state
    assert _claims_by_dimension(state).keys() == {"layout.density"}

    on_b = apply_lifecycle_operation(
        state, SelectBranch(operation_id="choose-b", branch_id="alt-b")
    )
    assert _claims_by_dimension(on_b.state).keys() == {
        "layout.density",
        "color.saturation",
    }

    on_a = apply_lifecycle_operation(
        on_b.state, SelectBranch(operation_id="choose-a", branch_id="alt-a")
    )
    assert on_a.state.branches.active_branch_id == "alt-a"
    assert _claims_by_dimension(on_a.state).keys() == {
        "layout.density",
        "motion.timing",
    }


def test_branch_specific_evidence_is_isolated_from_parent_and_siblings() -> None:
    state = _branchy_state()
    state = apply_lifecycle_operation(
        state, SelectBranch(operation_id="choose-a", branch_id="alt-a")
    ).state
    state = _ingest(state, _A_SCOPED).state
    assert "motion.timing" in _claims_by_dimension(state)

    on_child = apply_lifecycle_operation(
        state, SelectBranch(operation_id="switch-b", branch_id="alt-b")
    ).state
    with_child_feedback = _ingest(on_child, _B_SCOPED)
    child_claims = _claims_by_dimension(with_child_feedback.state)
    assert "color.saturation" in child_claims
    assert "motion.timing" not in child_claims

    back_on_a = apply_lifecycle_operation(
        with_child_feedback.state,
        SelectBranch(operation_id="resume-a", branch_id="alt-a"),
    )
    claims = _claims_by_dimension(back_on_a.state)
    assert "motion.timing" in claims
    assert "color.saturation" not in claims
    assert any(
        event.event_id == "b-feedback"
        for event in back_on_a.state.evidence.events
    )


def test_broader_evidence_keeps_scope_and_records_origin_branch() -> None:
    state = apply_lifecycle_operation(
        _branchy_state(),
        SelectBranch(operation_id="choose-b", branch_id="alt-b"),
    ).state

    broader = _event(
        "broader-pref",
        _implication("scale", "typography.scale", "dense"),
        origin_branch="alt-b",
        occurred_at=4,
    )
    received = _ingest(state, broader)
    assert "typography.scale" in _claims_by_dimension(received.state)

    moved = apply_lifecycle_operation(
        received.state,
        SelectBranch(operation_id="choose-a", branch_id="alt-a"),
    )
    assert "typography.scale" in _claims_by_dimension(moved.state)
    assert "layout.density" in _claims_by_dimension(moved.state)
    stored = [
        event
        for event in moved.state.evidence.events
        if event.event_id == "broader-pref"
    ]
    assert stored and stored[0].origin_branch == "alt-b"

def _round_trip_source() -> tuple[LifecycleState, ProfileExchange]:
    seeded = _ingest(
        initial_lifecycle_state(_profile()), _shared_layout_typography_event()
    )
    claims = _claims_by_dimension(seeded.state)
    source = initial_lifecycle_state(
        _profile(
            _property_for(claims["layout.density"], "layout"),
            _property_for(claims["typography.scale"], "typography"),
        ),
        seeded.state.evidence,
    )
    return source, export_profile_exchange(source)


def test_export_import_round_trip_preserves_semantics_and_boundaries() -> None:
    source, bundle = _round_trip_source()

    imported = apply_lifecycle_operation(
        initial_lifecycle_state(_profile()),
        ImportProfileExchange(operation_id="import-1", exchange=bundle),
    )

    assert deserialize_profile_state(bundle.profile_document) == source.profile
    assert imported.state.profile == source.profile
    assert imported.state.evidence.events == source.evidence.events
    assert imported.state.evidence.claims == source.evidence.claims
    assert imported.state.evidence.support_lifecycle == ()
    assert imported.state.branches == source.branches
    assert imported.reason == "import validated against evidence"


def test_import_downgrades_tampered_confidence_and_provenance() -> None:
    moderate_event = _event(
        "moderate-feedback",
        _implication(
            "typography",
            "typography.scale",
            "dense",
            strength=SupportStrength.MODERATE,
        ),
    )
    seeded = _ingest(initial_lifecycle_state(_profile()), moderate_event)
    claim = _claims_by_dimension(seeded.state)["typography.scale"]
    source = initial_lifecycle_state(
        _profile(_property_for(claim, "typography")), seeded.state.evidence
    )
    bundle = export_profile_exchange(source)
    parsed = json.loads(bundle.profile_document.decode("utf-8"))
    knowledge = parsed["properties"][0]["knowledge"]
    knowledge["confidence"] = 0.9
    knowledge["provenance"].append(
        {"actor": "user", "source_id": "fabricated:instruction"}
    )
    tampered = ProfileExchange(
        profile_document=(
            json.dumps(
                parsed,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8"),
        evidence=bundle.evidence,
        branches=bundle.branches,
    )

    result = apply_lifecycle_operation(
        initial_lifecycle_state(_profile()),
        ImportProfileExchange(operation_id="import-1", exchange=tampered),
    )
    property_knowledge = result.state.profile.properties[0].knowledge

    assert property_knowledge.confidence == pytest.approx(0.65)
    assert property_knowledge.provenance == (
        (Provenance(actor="user", source_id="message:moderate-feedback"),)
    )
    assert "downgraded inflated confidence" in result.reason
    assert "dropped unattested provenance" in result.reason


def test_import_rejects_structurally_tampered_documents() -> None:
    _, bundle = _round_trip_source()
    broken = ProfileExchange(
        profile_document=b'{"schema_version": 1}',
        evidence=bundle.evidence,
        branches=bundle.branches,
    )

    with pytest.raises(InvalidProfileStateError, match="invalid fields"):
        apply_lifecycle_operation(
            initial_lifecycle_state(_profile()),
            ImportProfileExchange(operation_id="import-1", exchange=broken),
        )


def test_migrate_document_maps_missing_epistemic_fields_to_unknown() -> None:
    legacy = {
        "schema_version": 0,
        "profile_id": "profile:legacy",
        "properties": [
            {
                "claim_id": "claim:legacy-density",
                "section": "layout",
                "knowledge": {
                    "dimension": "layout.density",
                    "direction": "compact",
                    "disposition": "preferred",
                    "scope": {
                        "kind": "project",
                        "identity": "project:legacy",
                        "represented_subject": "user:1",
                    },
                },
            }
        ],
    }

    migrated = migrate_document(json.dumps(legacy).encode("utf-8"))

    assert migrated.schema_version == CURRENT_SCHEMA_VERSION
    assert migrated.profile_id == "profile:legacy"
    knowledge = migrated.properties[0].knowledge
    assert migrated.properties[0].claim_id == "claim:legacy-density"
    assert knowledge.dimension == "layout.density"
    assert knowledge.direction == "compact"
    assert knowledge.disposition is Disposition.PREFERRED
    assert knowledge.basis is EpistemicBasis.INFERRED
    assert knowledge.confidence == 0.0
    assert knowledge.strength == 0.0
    assert knowledge.provenance == ()
    assert knowledge.evidence == ()
    assert dict(knowledge.context) == {}
    assert dict(knowledge.relationships) == {}
    assert knowledge.validation_context.domain == "unknown"
    assert knowledge.validation_context.fidelity == "unknown"
    assert knowledge.validation_context.conditions == ()
    restored = deserialize_profile_state(serialize_profile_state(migrated))
    assert restored == migrated


def test_migration_preserves_present_fields_and_refuses_newer_versions() -> None:
    legacy = {
        "schema_version": 0,
        "profile_id": "profile:legacy",
        "properties": [
            {
                "claim_id": "claim:legacy",
                "section": "layout",
                "evidence_applicable": False,
                "knowledge": {
                    "dimension": "color.saturation",
                    "direction": "muted",
                    "disposition": "preferred",
                    "confidence": 0.5,
                    "provenance": [
                        {"actor": "user", "source_id": "message:9"}
                    ],
                    "scope": {
                        "kind": "project",
                        "identity": "project:legacy",
                        "represented_subject": "user:1",
                    },
                },
            }
        ],
    }

    migrated = migrate_document(json.dumps(legacy).encode("utf-8"))
    knowledge = migrated.properties[0].knowledge

    assert migrated.properties[0].evidence_applicable is False
    assert knowledge.confidence == pytest.approx(0.5)
    assert knowledge.provenance == (
        (Provenance(actor="user", source_id="message:9"),)
    )
    future = {
        "schema_version": CURRENT_SCHEMA_VERSION + 1,
        "profile_id": "profile:future",
        "properties": [],
    }
    with pytest.raises(
        UnsupportedSchemaVersionError, match="unsupported schema version"
    ):
        migrate_document(json.dumps(future).encode("utf-8"))


def _consolidation_knowledge(
    *,
    dimension: str = "layout.density",
    evidence: tuple[str, ...] = ("feedback:1#density",),
    provenance: tuple[Provenance, ...] = _provenance("message:1"),
    confidence: float = 0.7,
    relationships: dict[str, str] | None = None,
    context: dict[str, str] | None = None,
    represented_subject: str = "user:1",
) -> PreferenceKnowledge:
    return PreferenceKnowledge(
        dimension=dimension,
        direction="compact",
        disposition=Disposition.PREFERRED,
        basis=EpistemicBasis.EXPLICIT,
        confidence=confidence,
        strength=0.8,
        scope=Scope(
            kind="project",
            identity="project:alpha",
            represented_subject=represented_subject,
        ),
        context=context or {"device": "desktop"},
        evidence=evidence,
        provenance=provenance,
        validation_context=ValidationContext(
            domain="ui",
            fidelity="implemented",
            conditions=("desktop",),
        ),
        relationships=relationships or {},
    )


def _consolidation_property(
    claim_id: str, knowledge: PreferenceKnowledge
) -> ProfileProperty:
    return ProfileProperty(
        claim_id=claim_id,
        section="layout",
        knowledge=knowledge,
    )


def test_consolidation_merges_near_duplicates_and_keeps_distinctions() -> None:
    survivor = _profile(
        _consolidation_property(
            "claim:survivor",
            _consolidation_knowledge(
                relationships={"typography.scale": "compact"}
            ),
        )
    )
    absorbed = _profile(
        _consolidation_property(
            "claim:duplicate",
            _consolidation_knowledge(
                evidence=("feedback:2#density",),
                provenance=_provenance("message:2"),
                confidence=0.5,
                relationships={"color.saturation": "muted"},
            ),
        )
    )

    outcome = consolidate_profiles(
        ConsolidationRequest(
            operation_id="merge-1", survivor=survivor, absorbed=absorbed
        )
    )

    assert outcome.status is LifecycleStatus.APPLIED
    assert outcome.merged is not None
    merged_property = outcome.merged.properties[0]
    assert merged_property.claim_id == "claim:survivor"
    knowledge = merged_property.knowledge
    assert knowledge.confidence == pytest.approx(0.5)
    assert knowledge.basis is EpistemicBasis.EXPLICIT
    assert knowledge.evidence == ("feedback:1#density", "feedback:2#density")
    assert knowledge.provenance == (
        Provenance(actor="user", source_id="message:1"),
        Provenance(actor="user", source_id="message:2"),
    )
    assert dict(knowledge.relationships) == {
        "typography.scale": "compact",
        "color.saturation": "muted",
    }


def test_consolidation_refuses_contextually_distinct_profiles() -> None:
    survivor = _profile(
        _consolidation_property(
            "claim:a", _consolidation_knowledge(context={"device": "desktop"})
        )
    )
    absorbed = _profile(
        _consolidation_property(
            "claim:b", _consolidation_knowledge(context={"device": "mobile"})
        )
    )

    outcome = consolidate_profiles(
        ConsolidationRequest(
            operation_id="merge-1", survivor=survivor, absorbed=absorbed
        )
    )

    assert outcome.status is LifecycleStatus.REFUSED
    assert outcome.merged is None
    assert "context conditions differ" in outcome.reason
    assert "desktop" in outcome.reason and "mobile" in outcome.reason


def test_consolidation_refuses_different_represented_subjects() -> None:
    survivor = _profile(
        _consolidation_property(
            "claim:a",
            _consolidation_knowledge(represented_subject="user:1"),
        )
    )
    absorbed = _profile(
        _consolidation_property(
            "claim:b",
            _consolidation_knowledge(represented_subject="stakeholder:reader"),
        )
    )

    outcome = consolidate_profiles(
        ConsolidationRequest(
            operation_id="merge-1", survivor=survivor, absorbed=absorbed
        )
    )

    assert outcome.status is LifecycleStatus.REFUSED
    assert outcome.merged is None
    assert "stakeholder:reader" in outcome.reason
    assert "refused consolidation" in outcome.reason


def test_operations_replay_identically_and_identity_reuse_raises() -> None:
    event = _shared_layout_typography_event()
    fresh = initial_lifecycle_state(_profile())
    first_ingest = apply_lifecycle_operation(
        fresh,
        IngestProfileEvidence(operation_id="ingest-1", event=event),
    )
    replay_ingest = apply_lifecycle_operation(
        first_ingest.state,
        IngestProfileEvidence(operation_id="ingest-1", event=event),
    )
    assert replay_ingest.status is LifecycleStatus.REPLAYED
    assert replay_ingest.state == first_ingest.state

    reset = ResetSupport(
        operation_id="reset-typography",
        support=SupportRef("feedback-1", "typography"),
        reason="relearn requested",
    )
    applied_reset = apply_lifecycle_operation(first_ingest.state, reset)
    replayed_reset = apply_lifecycle_operation(applied_reset.state, reset)
    assert replayed_reset.status is LifecycleStatus.REPLAYED
    assert replayed_reset.state is applied_reset.state

    with pytest.raises(OperationIdentityConflictError, match="was reused"):
        apply_lifecycle_operation(
            applied_reset.state,
            ResetSupport(
                operation_id="reset-typography",
                support=SupportRef("feedback-1", "layout"),
            ),
        )


def test_branch_references_are_validated_against_the_registry() -> None:
    state = initial_lifecycle_state(_profile())
    ghost_scoped = _event(
        "ghost",
        _implication(
            "density",
            "layout.density",
            "compact",
            applicable_branches=("nowhere",),
        ),
    )
    with pytest.raises(ValueError, match="unknown branch identifiers"):
        _ingest(state, ghost_scoped)

    ghost_origin = _event(
        "ghost-origin",
        _implication("hue", "color.hue", "warm"),
        origin_branch="nowhere",
    )
    with pytest.raises(ValueError, match="unknown branch identifiers"):
        _ingest(state, ghost_origin)

    with pytest.raises(ValueError, match="unknown branch"):
        apply_lifecycle_operation(
            state, SelectBranch(operation_id="pick", branch_id="nowhere")
        )

    created = apply_lifecycle_operation(
        state,
        CreateBranch(
            operation_id="open-dup",
            branch_id="dup",
            provenance=_provenance("instruction:open-dup"),
        ),
    ).state
    with pytest.raises(ValueError, match="already exists"):
        apply_lifecycle_operation(
            created,
            CreateBranch(
                operation_id="open-dup-again",
                branch_id="dup",
                provenance=_provenance("instruction:again"),
            ),
        )
    with pytest.raises(ValueError, match="unknown parent branch"):
        apply_lifecycle_operation(
            created,
            CreateBranch(
                operation_id="open-orphan",
                branch_id="orphan",
                parent_branch_id="missing",
                provenance=_provenance("instruction:orphan"),
            ),
        )
    with pytest.raises(ValueError, match="requires provenance"):
        CreateBranch(operation_id="open-unattributed", branch_id="unattributed")


def _color_only_state() -> LifecycleState:
    """A non-empty receiver holding one locally derived color property."""
    seeded = _ingest(
        initial_lifecycle_state(_profile()),
        _event(
            "color-feedback",
            _implication("color", "color.saturation", "muted"),
            occurred_at=2,
        ),
    )
    color_claim = _claims_by_dimension(seeded.state)["color.saturation"]
    return initial_lifecycle_state(
        _profile(_property_for(color_claim, "color")),
        seeded.state.evidence,
    )


def test_import_into_non_empty_state_unions_evidence_and_merges_properties() -> (
    None
):
    _, bundle = _round_trip_source()
    receiver = _color_only_state()

    imported = apply_lifecycle_operation(
        receiver,
        ImportProfileExchange(operation_id="import-1", exchange=bundle),
    )

    assert imported.status is LifecycleStatus.APPLIED
    event_ids = {event.event_id for event in imported.state.evidence.events}
    assert event_ids == {"feedback-1", "color-feedback"}
    assert set(_claims_by_dimension(imported.state)) == {
        "layout.density",
        "typography.scale",
        "color.saturation",
    }
    incoming_properties = deserialize_profile_state(
        bundle.profile_document
    ).properties
    merged = imported.state.profile.properties
    assert merged[0] == receiver.profile.properties[0]
    assert list(merged[1:]) == list(incoming_properties)


def test_import_keeps_local_markers_so_pre_import_operations_still_replay() -> (
    None
):
    empty_bundle = export_profile_exchange(initial_lifecycle_state(_profile()))
    reset = ResetSupport(
        operation_id="reset-typography",
        support=SupportRef("feedback-1", "typography"),
        reason="relearn requested",
    )
    state = _ingest(
        initial_lifecycle_state(_profile()), _shared_layout_typography_event()
    ).state
    state = apply_lifecycle_operation(state, reset).state

    imported = apply_lifecycle_operation(
        state,
        ImportProfileExchange(operation_id="import-empty", exchange=empty_bundle),
    )
    assert imported.status is LifecycleStatus.APPLIED

    replay = apply_lifecycle_operation(imported.state, reset)

    assert replay.status is LifecycleStatus.REPLAYED
    assert replay.state is imported.state
    assert (
        replay.state.evidence.support_lifecycle
        == imported.state.evidence.support_lifecycle
    )


def test_stale_exchange_import_into_moved_on_state_preserves_local_claims() -> (
    None
):
    _, bundle = _round_trip_source()
    parsed = json.loads(bundle.profile_document.decode("utf-8"))
    parsed["properties"][1]["knowledge"]["confidence"] = 0.99
    stale_document = (
        json.dumps(
            parsed,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    stale = ProfileExchange(
        profile_document=stale_document,
        evidence=bundle.evidence,
        branches=bundle.branches,
    )

    moved_on = _ingest(
        _color_only_state(), _shared_layout_typography_event()
    ).state
    moved_on = apply_lifecycle_operation(
        moved_on,
        ResetSupport(
            operation_id="reset-typography",
            support=SupportRef("feedback-1", "typography"),
            reason="typography relearn requested",
        ),
    ).state

    imported = apply_lifecycle_operation(
        moved_on,
        ImportProfileExchange(operation_id="import-stale", exchange=stale),
    )

    claims = _claims_by_dimension(imported.state)
    assert claims["color.saturation"].knowledge.evidence == (
        "color-feedback#color",
    )
    assert "typography.scale" not in claims
    assert [event.event_id for event in imported.state.evidence.events] == [
        "color-feedback",
        "feedback-1",
    ]
    assert [
        record.support.stable_id
        for record in imported.state.evidence.support_lifecycle
    ] == ["feedback-1#typography"]
    typography_ceiling = next(
        claim.envelope.confidence
        for claim in stale.evidence.claims
        if claim.envelope is not None
        and claim.knowledge.dimension == "typography.scale"
    )
    properties = {
        prop.knowledge.dimension: prop
        for prop in imported.state.profile.properties
    }
    assert (
        properties["typography.scale"].knowledge.confidence
        == pytest.approx(typography_ceiling)
    )
    # The local reset wins over the imported citation: the property keeps
    # its clamped knowledge but loses applicability, so composition drops
    # it (composition excludes properties whose supporting evidence is not
    # applicable).
    assert properties["typography.scale"].evidence_applicable is False
    assert "downgraded inflated confidence" in imported.reason


def test_undo_after_merged_import_restores_exact_pre_import_state() -> None:
    _, bundle = _round_trip_source()
    pre_import = _color_only_state()

    imported = apply_lifecycle_operation(
        pre_import,
        ImportProfileExchange(operation_id="import-1", exchange=bundle),
    )
    assert imported.status is LifecycleStatus.APPLIED
    assert len(imported.state.undo_ledger) == len(pre_import.undo_ledger) + 1

    undone = apply_lifecycle_operation(
        imported.state, UndoLastOperation(operation_id="undo-import")
    )

    assert undone.status is LifecycleStatus.UNDONE
    assert undone.state == pre_import


_REMOTE_SCOPED = _event(
    "remote-feedback",
    _implication("hue", "color.hue", "warm", applicable_branches=("remote-x",)),
    origin_branch="remote-x",
    occurred_at=2,
)


def _remote_branch_exchange() -> ProfileExchange:
    state = initial_lifecycle_state(_profile())
    state = apply_lifecycle_operation(
        state,
        CreateBranch(
            operation_id="open-remote-x",
            branch_id="remote-x",
            provenance=_provenance("instruction:open-remote-x"),
        ),
    ).state
    state = apply_lifecycle_operation(
        state,
        SelectBranch(operation_id="choose-remote-x", branch_id="remote-x"),
    ).state
    return export_profile_exchange(_ingest(state, _REMOTE_SCOPED).state)


def test_import_merges_branches_local_first_and_honors_active_selection() -> None:
    imported = apply_lifecycle_operation(
        _branchy_state(),
        ImportProfileExchange(
            operation_id="import-branchy", exchange=_remote_branch_exchange()
        ),
    )

    assert imported.status is LifecycleStatus.APPLIED
    branch_ids = {
        branch.branch_id for branch in imported.state.branches.branches
    }
    assert branch_ids == {"alt-a", "alt-b", "remote-x"}
    child = imported.state.branches.branch("alt-b")
    assert child is not None
    assert child.parent_branch_id == "alt-a"
    assert imported.state.branches.active_branch_id == "remote-x"
    claims = _claims_by_dimension(imported.state)
    assert "color.hue" in claims
    assert "layout.density" in claims

    invalid_active = ProfileExchange(
        profile_document=serialize_profile_state(_profile()),
        evidence=EvidenceState(),
        branches=BranchRegistry(active_branch_id="ghost"),
    )
    branched_local = apply_lifecycle_operation(
        _branchy_state(),
        SelectBranch(operation_id="choose-alt-a", branch_id="alt-a"),
    ).state

    fallback = apply_lifecycle_operation(
        branched_local,
        ImportProfileExchange(
            operation_id="import-ghost", exchange=invalid_active
        ),
    )

    assert fallback.status is LifecycleStatus.APPLIED
    assert fallback.state.branches.active_branch_id == "alt-a"
    assert {branch.branch_id for branch in fallback.state.branches.branches} == {
        "alt-a",
        "alt-b",
    }


def test_import_rejects_divergent_event_id_collision_instead_of_merging() -> (
    None
):
    """Same event id with different content is an identity conflict.

    Merging would keep the local body while transplanting foreign
    lifecycle records keyed onto stable ids of content that was never
    adopted — a hybrid state no device ever validated.
    """
    divergent_event = _event(
        "feedback-1",
        _implication("layout", "layout.density", "airy"),
        occurred_at=9,
    )
    bundle = export_profile_exchange(
        initial_lifecycle_state(
            _profile(), EvidenceState(events=(divergent_event,))
        )
    )

    receiver = _ingest(
        initial_lifecycle_state(_profile()), _shared_layout_typography_event()
    ).state

    with pytest.raises(EvidenceIdentityConflictError, match="feedback-1"):
        apply_lifecycle_operation(
            receiver,
            ImportProfileExchange(
                operation_id="import-divergent", exchange=bundle
            ),
        )


def test_import_marker_id_collision_keeps_local_and_surfaces_on_replay() -> (
    None
):
    """Synthetic marker ids collide across devices; local wins.

    The dropped foreign marker does not silently mask divergence: a later
    application reusing the id is checked against the retained local
    fingerprint and raises instead of re-applying.
    """
    foreign = _ingest(
        initial_lifecycle_state(_profile()),
        _event(
            "other-feedback",
            _implication("hue", "color.hue", "cool"),
            occurred_at=5,
        ),
    ).state
    bundle = export_profile_exchange(foreign)

    receiver = _color_only_state()

    imported = apply_lifecycle_operation(
        receiver,
        ImportProfileExchange(
            operation_id="import-conflicting", exchange=bundle
        ),
    )
    assert imported.status is LifecycleStatus.APPLIED

    with pytest.raises(OperationIdentityConflictError, match="was reused"):
        apply_lifecycle_operation(
            imported.state,
            IngestProfileEvidence(
                operation_id="ingest-1",
                event=_event(
                    "hijack-feedback",
                    _implication("hue2", "color.hue", "neon"),
                    occurred_at=7,
                ),
            ),
        )
