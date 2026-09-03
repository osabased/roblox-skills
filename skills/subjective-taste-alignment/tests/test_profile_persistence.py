from __future__ import annotations

from dataclasses import replace
import json
import pytest

from alignment_contract import (
    AuthorityScope,
    PreferenceKnowledge,
    Provenance,
    Scope,
    ValidationContext,
)
from profile_composition import ProfileProperty, PropertyPath, RelationalRequirement
from profile_persistence import (
    AtomicFileProfileStorage,
    FileWriteStage,
    InMemoryProfileStorage,
    InvalidProfileStateError,
    MutationAuthorship,
    ProfilePersistence,
    ProfileState,
    ReferenceFreshness,
    ReferenceMode,
    ReferenceSource,
    RevisionConflictError,
    UNKNOWN_EXTERNAL_AUTHORSHIP,
    deserialize_profile_state,
    serialize_profile_state,
)


def complete_profile_state(*, direction: str = "compact") -> ProfileState:
    provenance = (
        Provenance(actor="user", source_id="feedback:layout-7"),
        Provenance(actor="unknown", source_id="external:import-3"),
    )
    scope = Scope(
        kind="project",
        identity="project:alpha",
        represented_subject="stakeholder:reader",
    )
    knowledge = PreferenceKnowledge(
        dimension="density",
        direction=direction,
        disposition="preferred",
        basis="inferred",
        confidence=0.63,
        strength=0.91,
        scope=scope,
        context={"audience": "expert", "surface": "settings"},
        evidence=("observation:12", "feedback:layout-7"),
        provenance=provenance,
        validation_context=ValidationContext(
            domain="ui",
            fidelity="implemented",
            conditions=("desktop", "dark-mode"),
        ),
        relationships={
            "color.saturation": "restrained",
            "typography.scale": "compact",
        },
    )
    profile_property = ProfileProperty(
        claim_id="claim:layout-density",
        section="layout",
        knowledge=knowledge,
        explicit_overrides=("claim:old-layout-density",),
        owner="stakeholder:reader",
        evidence_applicable=False,
        relational_requirements=(
            RelationalRequirement(PropertyPath("color", "saturation"), "restrained"),
        ),
    )
    authority = AuthorityScope(
        actor="agent",
        dimensions=("layout.density", "color.saturation"),
        allows_material_propagation=False,
        checkpoint_required=True,
        scope=scope,
        provenance=(Provenance(actor="user", source_id="instruction:44"),),
    )
    reference = ReferenceSource(
        reference_id="reference:dashboard",
        source_identity="git:repo@example#7f35",
        locator="repo://example/dashboard.json",
        mode=ReferenceMode.PINNED,
        freshness=ReferenceFreshness.UNKNOWN,
        source_revision="7f35",
        derived_claim_ids=("claim:layout-density",),
        provenance=(
            Provenance(actor="user", source_id="instruction:use-dashboard"),
        ),
    )
    return ProfileState(
        schema_version=1,
        profile_id="profile:alpha",
        properties=(profile_property,),
        authority=(authority,),
        references=(reference,),
    )


def test_canonical_round_trip_preserves_all_current_profile_semantics() -> None:
    state = complete_profile_state()

    encoded = serialize_profile_state(state)
    restored = deserialize_profile_state(encoded)

    assert restored == state
    assert serialize_profile_state(restored) == encoded
    restored_property = restored.properties[0]
    assert restored_property.knowledge.scope.represented_subject == "stakeholder:reader"
    assert restored_property.evidence_applicable is False
    assert restored_property.owner == "stakeholder:reader"
    assert restored.references[0].freshness is ReferenceFreshness.UNKNOWN
    assert restored.references[0].mode is ReferenceMode.PINNED


def test_in_memory_persistence_creates_and_loads_one_complete_snapshot() -> None:
    persistence = ProfilePersistence(InMemoryProfileStorage())
    state = complete_profile_state()
    authorship = MutationAuthorship(
        actor="user",
        source_id="instruction:save-profile",
        attributable=True,
    )

    saved = persistence.save(
        state,
        expected_revision=None,
        authorship=authorship,
    )

    assert saved.state == state
    assert saved.revision.startswith("sha256:")
    assert saved.authorship == authorship
    assert persistence.load() == saved


def test_stale_save_surfaces_valid_external_state_without_overwriting_it() -> None:
    storage = InMemoryProfileStorage()
    first_writer = ProfilePersistence(storage)
    external_writer = ProfilePersistence(storage)
    initial = first_writer.save(
        complete_profile_state(direction="compact"),
        expected_revision=None,
    )
    external = external_writer.save(
        complete_profile_state(direction="spacious"),
        expected_revision=initial.revision,
        authorship=UNKNOWN_EXTERNAL_AUTHORSHIP,
    )

    with pytest.raises(RevisionConflictError) as caught:
        first_writer.save(
            complete_profile_state(direction="balanced"),
            expected_revision=initial.revision,
        )

    assert caught.value.expected_revision == initial.revision
    assert caught.value.actual_revision == external.revision
    assert caught.value.current == external
    assert caught.value.current.authorship.actor == "unknown"
    assert first_writer.load() == external


def test_restore_rejects_malformed_unsupported_and_partial_documents_whole() -> None:
    valid = serialize_profile_state(complete_profile_state())
    unsupported = valid.replace(b'"schema_version":1', b'"schema_version":999')
    missing_field = valid.replace(b'"evidence_applicable":false,', b"")
    duplicate_field = valid.replace(
        b'"profile_id":"profile:alpha"',
        b'"profile_id":"profile:other","profile_id":"profile:alpha"',
    )
    partial = valid[: len(valid) // 2]
    non_finite = json.dumps(
        {
            "authority": [],
            "profile_id": "profile:bad",
            "properties": [],
            "references": [],
            "schema_version": float("nan"),
        }
    ).encode("utf-8")

    for persisted in (
        unsupported,
        missing_field,
        duplicate_field,
        partial,
        non_finite,
    ):
        with pytest.raises(InvalidProfileStateError):
            deserialize_profile_state(persisted)


def test_file_persistence_reloads_valid_external_change_as_unknown_authorship(
    tmp_path,
) -> None:
    profile_path = tmp_path / "canonical-profile.json"
    persistence = ProfilePersistence(AtomicFileProfileStorage(profile_path))
    initial = persistence.save(
        complete_profile_state(direction="compact"),
        expected_revision=None,
        authorship=MutationAuthorship(
            actor="agent",
            source_id="operation:initial-save",
            attributable=True,
        ),
    )
    external_state = complete_profile_state(direction="spacious")
    profile_path.write_bytes(serialize_profile_state(external_state))

    with pytest.raises(RevisionConflictError) as caught:
        persistence.save(
            complete_profile_state(direction="balanced"),
            expected_revision=initial.revision,
        )

    current = caught.value.current
    assert current is not None
    assert current.state == external_state
    assert current.authorship == UNKNOWN_EXTERNAL_AUTHORSHIP
    assert persistence.load() == current


class SimulatedWriteFailure(RuntimeError):
    pass


class SimulatedInterruption(BaseException):
    pass


@pytest.mark.parametrize(
    ("failed_stage", "recovered_direction"),
    (
        (FileWriteStage.TEMP_DURABLE, "compact"),
        (FileWriteStage.REPLACEMENT_VISIBLE, "spacious"),
        (FileWriteStage.COMMIT_DURABLE, "spacious"),
    ),
)
def test_failed_atomic_write_recovers_exactly_the_old_or_new_complete_state(
    tmp_path,
    failed_stage: FileWriteStage,
    recovered_direction: str,
) -> None:
    profile_path = tmp_path / "canonical-profile.json"
    initial = ProfilePersistence(AtomicFileProfileStorage(profile_path)).save(
        complete_profile_state(direction="compact"),
        expected_revision=None,
    )

    def fail_at_stage(stage: FileWriteStage) -> None:
        if stage is failed_stage:
            raise SimulatedWriteFailure(stage.value)

    failing = ProfilePersistence(
        AtomicFileProfileStorage(
            profile_path,
            failure_injector=fail_at_stage,
        )
    )
    with pytest.raises(SimulatedWriteFailure):
        failing.save(
            complete_profile_state(direction="spacious"),
            expected_revision=initial.revision,
        )

    recovered = ProfilePersistence(AtomicFileProfileStorage(profile_path)).load()
    assert recovered is not None
    assert recovered.state.properties[0].knowledge.direction == recovered_direction
    assert deserialize_profile_state(profile_path.read_bytes()) == recovered.state
    assert list(tmp_path.glob(".canonical-profile.json.write-*.tmp")) == []


@pytest.mark.parametrize(
    ("interrupted_stage", "recovered_direction", "abandoned_temp_count"),
    (
        (FileWriteStage.TEMP_DURABLE, "compact", 1),
        (FileWriteStage.REPLACEMENT_VISIBLE, "spacious", 0),
    ),
)
def test_interrupted_write_recovers_old_or_new_state_and_cleans_abandoned_temp(
    tmp_path,
    interrupted_stage: FileWriteStage,
    recovered_direction: str,
    abandoned_temp_count: int,
) -> None:
    profile_path = tmp_path / "canonical-profile.json"
    initial = ProfilePersistence(AtomicFileProfileStorage(profile_path)).save(
        complete_profile_state(direction="compact"),
        expected_revision=None,
    )

    def interrupt(stage: FileWriteStage) -> None:
        if stage is interrupted_stage:
            raise SimulatedInterruption(stage.value)

    interrupted = ProfilePersistence(
        AtomicFileProfileStorage(profile_path, failure_injector=interrupt)
    )
    with pytest.raises(SimulatedInterruption):
        interrupted.save(
            complete_profile_state(direction="spacious"),
            expected_revision=initial.revision,
        )

    assert (
        len(list(tmp_path.glob(".canonical-profile.json.write-*.tmp")))
        == abandoned_temp_count
    )
    recovered = ProfilePersistence(AtomicFileProfileStorage(profile_path)).load()
    assert recovered is not None
    assert recovered.state == complete_profile_state(direction=recovered_direction)
    if recovered_direction == "compact":
        assert recovered.revision == initial.revision
    assert list(tmp_path.glob(".canonical-profile.json.write-*.tmp")) == []


def test_external_change_during_write_is_detected_before_atomic_replace(
    tmp_path,
) -> None:
    profile_path = tmp_path / "canonical-profile.json"
    initial = ProfilePersistence(AtomicFileProfileStorage(profile_path)).save(
        complete_profile_state(direction="compact"),
        expected_revision=None,
    )
    external_state = complete_profile_state(direction="spacious")

    def change_externally(stage: FileWriteStage) -> None:
        if stage is FileWriteStage.TEMP_DURABLE:
            profile_path.write_bytes(serialize_profile_state(external_state))

    writer = ProfilePersistence(
        AtomicFileProfileStorage(
            profile_path,
            failure_injector=change_externally,
        )
    )
    with pytest.raises(RevisionConflictError) as caught:
        writer.save(
            complete_profile_state(direction="balanced"),
            expected_revision=initial.revision,
        )

    assert caught.value.current is not None
    assert caught.value.current.state == external_state
    assert caught.value.current.authorship == UNKNOWN_EXTERNAL_AUTHORSHIP
    assert deserialize_profile_state(profile_path.read_bytes()) == external_state


def test_external_change_during_commit_is_verified_before_save_returns(
    tmp_path,
) -> None:
    profile_path = tmp_path / "canonical-profile.json"
    initial = ProfilePersistence(AtomicFileProfileStorage(profile_path)).save(
        complete_profile_state(direction="compact"),
        expected_revision=None,
    )
    external_state = complete_profile_state(direction="spacious")

    def change_externally(stage: FileWriteStage) -> None:
        if stage is FileWriteStage.COMMIT_DURABLE:
            profile_path.write_bytes(serialize_profile_state(external_state))

    writer = ProfilePersistence(
        AtomicFileProfileStorage(
            profile_path,
            failure_injector=change_externally,
        )
    )
    with pytest.raises(RevisionConflictError) as caught:
        writer.save(
            complete_profile_state(direction="balanced"),
            expected_revision=initial.revision,
        )

    assert caught.value.current is not None
    assert caught.value.current.state == external_state
    assert caught.value.current.authorship == UNKNOWN_EXTERNAL_AUTHORSHIP


def test_malformed_external_change_is_neither_overwritten_nor_partially_loaded(
    tmp_path,
) -> None:
    profile_path = tmp_path / "canonical-profile.json"
    persistence = ProfilePersistence(AtomicFileProfileStorage(profile_path))
    initial = persistence.save(
        complete_profile_state(direction="compact"),
        expected_revision=None,
    )
    malformed = b'{"schema_version":1,"profile_id":"partial"'
    profile_path.write_bytes(malformed)

    with pytest.raises(RevisionConflictError) as caught:
        persistence.save(
            complete_profile_state(direction="spacious"),
            expected_revision=initial.revision,
        )

    assert caught.value.current is None
    assert caught.value.current_validation_error is not None
    assert profile_path.read_bytes() == malformed
    with pytest.raises(InvalidProfileStateError):
        persistence.load()


def test_save_validates_the_complete_canonical_state_before_storage() -> None:
    state = complete_profile_state()
    invalid_reference = replace(state.references[0], locator=42)  # type: ignore[arg-type]
    invalid_state = replace(state, references=(invalid_reference,))
    persistence = ProfilePersistence(InMemoryProfileStorage())

    with pytest.raises(InvalidProfileStateError):
        persistence.save(invalid_state, expected_revision=None)

    assert persistence.load() is None
