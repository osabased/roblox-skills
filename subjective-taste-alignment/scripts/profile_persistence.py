"""Canonical serialization and mutation-safe persistence for profile state."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import threading
from typing import Callable, Iterable, Iterator, Mapping, Protocol

from alignment_contract import (
    AuthorityScope,
    Disposition,
    EpistemicBasis,
    PreferenceKnowledge,
    Provenance,
    Scope,
    ValidationContext,
)
from profile_composition import (
    ProfileProperty,
    PropertyPath,
    RelationalRequirement,
)


CURRENT_SCHEMA_VERSION = 1


class ProfilePersistenceError(RuntimeError):
    """Base error for the public persistence boundary."""


class InvalidProfileStateError(ProfilePersistenceError, ValueError):
    """Canonical or persisted state failed whole-document validation."""


class UnsupportedSchemaVersionError(InvalidProfileStateError):
    """The persisted document uses a schema this module cannot interpret."""


@dataclass(frozen=True)
class MutationAuthorship:
    """Authorship observed outside preference-evidence provenance."""

    actor: str
    source_id: str | None
    attributable: bool

    def __post_init__(self) -> None:
        if not isinstance(self.actor, str):
            raise ValueError("mutation actor must be a string")
        if self.source_id is not None and not isinstance(self.source_id, str):
            raise ValueError("mutation source_id must be a string or None")
        if type(self.attributable) is not bool:
            raise ValueError("mutation attributable must be a boolean")
        if self.attributable and self.actor == "unknown":
            raise ValueError("unknown mutation authorship cannot be attributable")
        if not self.attributable and self.actor != "unknown":
            raise ValueError(
                "unattributable mutation authorship must preserve actor as unknown"
            )


UNKNOWN_AUTHORSHIP = MutationAuthorship(
    actor="unknown",
    source_id=None,
    attributable=False,
)


UNKNOWN_EXTERNAL_AUTHORSHIP = MutationAuthorship(
    actor="unknown",
    source_id="external",
    attributable=False,
)


@dataclass(frozen=True)
class ProfileSnapshot:
    state: ProfileState
    revision: str
    authorship: MutationAuthorship


class RevisionConflictError(ProfilePersistenceError):
    """A save was based on a revision that is no longer current."""

    def __init__(
        self,
        *,
        expected_revision: str | None,
        actual_revision: str | None,
        current: ProfileSnapshot | None,
        current_validation_error: str | None = None,
    ) -> None:
        super().__init__(
            "stale profile snapshot: expected "
            f"{expected_revision!r}, found {actual_revision!r}"
        )
        self.expected_revision = expected_revision
        self.actual_revision = actual_revision
        self.current = current
        self.current_validation_error = current_validation_error


@dataclass(frozen=True)
class _StoredDocument:
    data: bytes
    revision: str
    authorship: MutationAuthorship


class _StorageRevisionMismatch(RuntimeError):
    def __init__(
        self,
        expected_revision: str | None,
        current: _StoredDocument | None,
    ) -> None:
        super().__init__("persisted revision does not match the expected revision")
        self.expected_revision = expected_revision
        self.current = current


class ProfileStorage(Protocol):
    """Atomic byte-storage boundary used by ProfilePersistence."""

    def read(self) -> _StoredDocument | None:
        ...

    def compare_and_swap(
        self,
        expected_revision: str | None,
        data: bytes,
        authorship: MutationAuthorship,
    ) -> _StoredDocument:
        ...


def _content_revision(data: bytes) -> str:
    return f"sha256:{sha256(data).hexdigest()}"


class InMemoryProfileStorage:
    """Thread-safe optimistic storage for tests and ephemeral hosts."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._document: _StoredDocument | None = None

    def read(self) -> _StoredDocument | None:
        with self._lock:
            return self._document

    def compare_and_swap(
        self,
        expected_revision: str | None,
        data: bytes,
        authorship: MutationAuthorship,
    ) -> _StoredDocument:
        with self._lock:
            actual_revision = (
                None if self._document is None else self._document.revision
            )
            if actual_revision != expected_revision:
                raise _StorageRevisionMismatch(
                    expected_revision,
                    self._document,
                )
            document = _StoredDocument(
                data=bytes(data),
                revision=_content_revision(data),
                authorship=authorship,
            )
            self._document = document
            return document


class FileWriteStage(str, Enum):
    """Stable failure-injection points around an atomic file replacement."""

    TEMP_DURABLE = "temp_durable"
    REPLACEMENT_VISIBLE = "replacement_visible"
    COMMIT_DURABLE = "commit_durable"


_FILE_THREAD_LOCKS_GUARD = threading.Lock()
_FILE_THREAD_LOCKS: dict[str, threading.RLock] = {}


def _thread_lock_for(path: Path) -> threading.RLock:
    key = str(path.resolve())
    with _FILE_THREAD_LOCKS_GUARD:
        lock = _FILE_THREAD_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _FILE_THREAD_LOCKS[key] = lock
        return lock


@contextmanager
def _operating_system_file_lock(path: Path) -> Iterator[None]:
    """Lock one byte so cooperating processes serialize compare-and-swap."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = path.open("a+b", buffering=0)
    try:
        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write(b"\0")
            lock_file.flush()
        lock_file.seek(0)
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            lock_file.seek(0)
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    finally:
        lock_file.close()


def _sync_directory(path: Path) -> None:
    """Flush replacement metadata on hosts that expose directory fsync."""
    if os.name == "nt":
        return
    descriptor = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class AtomicFileProfileStorage:
    """Content-digest CAS plus same-directory durable atomic replacement."""

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        failure_injector: Callable[[FileWriteStage], None] | None = None,
    ) -> None:
        self.path = Path(path)
        self._lock_path = self.path.with_name(f".{self.path.name}.lock")
        self._temp_prefix = f".{self.path.name}.write-"
        self._thread_lock = _thread_lock_for(self.path)
        self._failure_injector = failure_injector

    def _inject(self, stage: FileWriteStage) -> None:
        if self._failure_injector is not None:
            self._failure_injector(stage)

    def _read_unlocked(self) -> _StoredDocument | None:
        try:
            data = self.path.read_bytes()
        except FileNotFoundError:
            return None
        return _StoredDocument(
            data=data,
            revision=_content_revision(data),
            authorship=UNKNOWN_EXTERNAL_AUTHORSHIP,
        )

    def _remove_abandoned_temps_unlocked(self) -> None:
        if not self.path.parent.exists():
            return
        pattern = f"{self._temp_prefix}*.tmp"
        for temp_path in self.path.parent.glob(pattern):
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    @contextmanager
    def _locked(self) -> Iterator[None]:
        with self._thread_lock:
            with _operating_system_file_lock(self._lock_path):
                yield

    def read(self) -> _StoredDocument | None:
        with self._locked():
            self._remove_abandoned_temps_unlocked()
            return self._read_unlocked()

    def compare_and_swap(
        self,
        expected_revision: str | None,
        data: bytes,
        authorship: MutationAuthorship,
    ) -> _StoredDocument:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._locked():
            self._remove_abandoned_temps_unlocked()
            current = self._read_unlocked()
            actual_revision = None if current is None else current.revision
            if actual_revision != expected_revision:
                raise _StorageRevisionMismatch(expected_revision, current)

            descriptor, temp_name = tempfile.mkstemp(
                prefix=self._temp_prefix,
                suffix=".tmp",
                dir=str(self.path.parent),
            )
            temp_path = Path(temp_name)
            replaced = False
            try:
                with os.fdopen(descriptor, "wb") as temp_file:
                    temp_file.write(data)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())
                self._inject(FileWriteStage.TEMP_DURABLE)

                # Detect an uncooperative external edit that occurred while the
                # candidate document was being made durable.
                latest = self._read_unlocked()
                latest_revision = None if latest is None else latest.revision
                if latest_revision != expected_revision:
                    raise _StorageRevisionMismatch(expected_revision, latest)

                os.replace(temp_path, self.path)
                replaced = True
                self._inject(FileWriteStage.REPLACEMENT_VISIBLE)
                _sync_directory(self.path.parent)
                self._inject(FileWriteStage.COMMIT_DURABLE)
                committed = self._read_unlocked()
                desired_revision = _content_revision(data)
                if (
                    committed is None
                    or committed.revision != desired_revision
                ):
                    raise _StorageRevisionMismatch(
                        expected_revision,
                        committed,
                    )
            except Exception:
                if not replaced:
                    try:
                        temp_path.unlink()
                    except FileNotFoundError:
                        pass
                raise

            return _StoredDocument(
                data=bytes(data),
                revision=_content_revision(data),
                authorship=authorship,
            )


class ReferenceMode(str, Enum):
    LIVE = "live"
    PINNED = "pinned"


class ReferenceFreshness(str, Enum):
    CURRENT = "current"
    STALE = "stale"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ReferenceSource:
    """Source identity and freshness retained beside reference-derived claims."""

    reference_id: str
    source_identity: str
    locator: str
    mode: ReferenceMode | str
    freshness: ReferenceFreshness | str
    source_revision: str | None = None
    derived_claim_ids: tuple[str, ...] = ()
    provenance: tuple[Provenance, ...] = ()

    def __post_init__(self) -> None:
        try:
            mode = ReferenceMode(self.mode)
        except (TypeError, ValueError) as error:
            raise ValueError(f"unsupported reference mode: {self.mode}") from error
        try:
            freshness = ReferenceFreshness(self.freshness)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"unsupported reference freshness: {self.freshness}"
            ) from error
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "freshness", freshness)


@dataclass(frozen=True)
class ProfileState:
    """Logical profile state independent of its storage backend."""

    schema_version: int
    profile_id: str
    properties: tuple[ProfileProperty, ...] = ()
    authority: tuple[AuthorityScope, ...] = ()
    references: tuple[ReferenceSource, ...] = ()

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int:
            raise ValueError("schema_version must be an integer")
        if self.schema_version != CURRENT_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema version: {self.schema_version}"
            )
        if not isinstance(self.profile_id, str):
            raise ValueError("profile_id must be a string")
        _require_unique(
            (profile_property.claim_id for profile_property in self.properties),
            "profile claim_id",
        )
        _require_unique(
            (reference.reference_id for reference in self.references),
            "reference_id",
        )


def _require_unique(values: Iterable[str], label: str) -> None:
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"{label} must be a string")
        if value in seen:
            raise ValueError(f"duplicate {label}: {value}")
        seen.add(value)


def _scope_to_document(scope: Scope) -> dict[str, object]:
    return {
        "identity": scope.identity,
        "kind": scope.kind,
        "represented_subject": scope.represented_subject,
    }


def _provenance_to_document(provenance: Provenance) -> dict[str, object]:
    return {"actor": provenance.actor, "source_id": provenance.source_id}


def _validation_context_to_document(
    validation_context: ValidationContext,
) -> dict[str, object]:
    return {
        "conditions": list(validation_context.conditions),
        "domain": validation_context.domain,
        "fidelity": validation_context.fidelity,
    }


def _string_mapping_to_document(
    value: Mapping[str, str],
    path: str,
) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise InvalidProfileStateError(
                f"{path} must contain only string keys and string values"
            )
        result[key] = item
    return result


def _knowledge_to_document(knowledge: PreferenceKnowledge) -> dict[str, object]:
    return {
        "basis": EpistemicBasis(knowledge.basis).value,
        "confidence": knowledge.confidence,
        "context": _string_mapping_to_document(knowledge.context, "knowledge.context"),
        "dimension": knowledge.dimension,
        "direction": knowledge.direction,
        "disposition": Disposition(knowledge.disposition).value,
        "evidence": list(knowledge.evidence),
        "provenance": [
            _provenance_to_document(record) for record in knowledge.provenance
        ],
        "relationships": _string_mapping_to_document(
            knowledge.relationships,
            "knowledge.relationships",
        ),
        "scope": _scope_to_document(knowledge.scope),
        "strength": knowledge.strength,
        "validation_context": _validation_context_to_document(
            knowledge.validation_context
        ),
    }


def _property_to_document(profile_property: ProfileProperty) -> dict[str, object]:
    return {
        "claim_id": profile_property.claim_id,
        "evidence_applicable": profile_property.evidence_applicable,
        "explicit_overrides": list(profile_property.explicit_overrides),
        "knowledge": _knowledge_to_document(profile_property.knowledge),
        "owner": profile_property.owner,
        "relational_requirements": [
            {
                "direction": requirement.direction,
                "property_path": [
                    requirement.property_path[0],
                    requirement.property_path[1],
                ],
            }
            for requirement in profile_property.relational_requirements
        ],
        "section": profile_property.section,
    }


def _authority_to_document(authority: AuthorityScope) -> dict[str, object]:
    return {
        "actor": authority.actor,
        "allows_material_propagation": authority.allows_material_propagation,
        "checkpoint_required": authority.checkpoint_required,
        "dimensions": list(authority.dimensions),
        "provenance": [
            _provenance_to_document(record) for record in authority.provenance
        ],
        "scope": _scope_to_document(authority.scope),
    }


def _reference_to_document(reference: ReferenceSource) -> dict[str, object]:
    return {
        "derived_claim_ids": list(reference.derived_claim_ids),
        "freshness": ReferenceFreshness(reference.freshness).value,
        "locator": reference.locator,
        "mode": ReferenceMode(reference.mode).value,
        "provenance": [
            _provenance_to_document(record) for record in reference.provenance
        ],
        "reference_id": reference.reference_id,
        "source_identity": reference.source_identity,
        "source_revision": reference.source_revision,
    }


def _state_to_document(state: ProfileState) -> dict[str, object]:
    if not isinstance(state, ProfileState):
        raise InvalidProfileStateError("state must be a ProfileState")
    try:
        ProfileState(
            schema_version=state.schema_version,
            profile_id=state.profile_id,
            properties=state.properties,
            authority=state.authority,
            references=state.references,
        )
        return {
            "authority": [_authority_to_document(item) for item in state.authority],
            "profile_id": state.profile_id,
            "properties": [_property_to_document(item) for item in state.properties],
            "references": [_reference_to_document(item) for item in state.references],
            "schema_version": state.schema_version,
        }
    except InvalidProfileStateError:
        raise
    except (AttributeError, TypeError, ValueError) as error:
        raise InvalidProfileStateError(str(error)) from error


def serialize_profile_state(state: ProfileState) -> bytes:
    """Serialize one fully validated state into deterministic canonical JSON."""
    document = _state_to_document(state)
    try:
        canonical = json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise InvalidProfileStateError(str(error)) from error
    encoded = (canonical + "\n").encode("utf-8")
    restored = deserialize_profile_state(encoded)
    if restored != state:
        raise InvalidProfileStateError(
            "canonical state changes meaning during serialization"
        )
    return encoded


def _object(
    value: object,
    path: str,
    keys: frozenset[str],
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise InvalidProfileStateError(f"{path} must be an object")
    actual = frozenset(value)
    if actual != keys:
        missing = sorted(keys - actual)
        extra = sorted(actual - keys)
        details = []
        if missing:
            details.append(f"missing {missing}")
        if extra:
            details.append(f"unexpected {extra}")
        raise InvalidProfileStateError(f"{path} has invalid fields: {', '.join(details)}")
    return value


def _array(value: object, path: str) -> list[object]:
    if not isinstance(value, list):
        raise InvalidProfileStateError(f"{path} must be an array")
    return value


def _string(value: object, path: str) -> str:
    if not isinstance(value, str):
        raise InvalidProfileStateError(f"{path} must be a string")
    return value


def _optional_string(value: object, path: str) -> str | None:
    if value is None:
        return None
    return _string(value, path)


def _boolean(value: object, path: str) -> bool:
    if type(value) is not bool:
        raise InvalidProfileStateError(f"{path} must be a boolean")
    return value


def _integer(value: object, path: str) -> int:
    if type(value) is not int:
        raise InvalidProfileStateError(f"{path} must be an integer")
    return value


def _number(value: object, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidProfileStateError(f"{path} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise InvalidProfileStateError(f"{path} must be finite")
    return result


def _string_tuple(value: object, path: str) -> tuple[str, ...]:
    return tuple(
        _string(item, f"{path}[{index}]")
        for index, item in enumerate(_array(value, path))
    )


def _string_mapping(value: object, path: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise InvalidProfileStateError(f"{path} must be an object")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise InvalidProfileStateError(f"{path} keys must be strings")
        result[key] = _string(item, f"{path}.{key}")
    return result


def _decode_scope(value: object, path: str) -> Scope:
    item = _object(
        value,
        path,
        frozenset({"identity", "kind", "represented_subject"}),
    )
    return Scope(
        kind=_string(item["kind"], f"{path}.kind"),
        identity=_string(item["identity"], f"{path}.identity"),
        represented_subject=_string(
            item["represented_subject"],
            f"{path}.represented_subject",
        ),
    )


def _decode_provenance(value: object, path: str) -> Provenance:
    item = _object(value, path, frozenset({"actor", "source_id"}))
    return Provenance(
        actor=_string(item["actor"], f"{path}.actor"),
        source_id=_string(item["source_id"], f"{path}.source_id"),
    )


def _decode_provenance_array(value: object, path: str) -> tuple[Provenance, ...]:
    return tuple(
        _decode_provenance(item, f"{path}[{index}]")
        for index, item in enumerate(_array(value, path))
    )


def _decode_validation_context(value: object, path: str) -> ValidationContext:
    item = _object(
        value,
        path,
        frozenset({"conditions", "domain", "fidelity"}),
    )
    return ValidationContext(
        domain=_string(item["domain"], f"{path}.domain"),
        fidelity=_string(item["fidelity"], f"{path}.fidelity"),
        conditions=_string_tuple(item["conditions"], f"{path}.conditions"),
    )


def _decode_knowledge(value: object, path: str) -> PreferenceKnowledge:
    item = _object(
        value,
        path,
        frozenset(
            {
                "basis",
                "confidence",
                "context",
                "dimension",
                "direction",
                "disposition",
                "evidence",
                "provenance",
                "relationships",
                "scope",
                "strength",
                "validation_context",
            }
        ),
    )
    return PreferenceKnowledge(
        dimension=_string(item["dimension"], f"{path}.dimension"),
        direction=_optional_string(item["direction"], f"{path}.direction"),
        disposition=_string(item["disposition"], f"{path}.disposition"),
        basis=_string(item["basis"], f"{path}.basis"),
        confidence=_number(item["confidence"], f"{path}.confidence"),
        strength=_number(item["strength"], f"{path}.strength"),
        scope=_decode_scope(item["scope"], f"{path}.scope"),
        context=_string_mapping(item["context"], f"{path}.context"),
        evidence=_string_tuple(item["evidence"], f"{path}.evidence"),
        provenance=_decode_provenance_array(
            item["provenance"],
            f"{path}.provenance",
        ),
        validation_context=_decode_validation_context(
            item["validation_context"],
            f"{path}.validation_context",
        ),
        relationships=_string_mapping(
            item["relationships"],
            f"{path}.relationships",
        ),
    )


def _decode_relational_requirement(
    value: object,
    path: str,
) -> RelationalRequirement:
    item = _object(value, path, frozenset({"direction", "property_path"}))
    property_path = _array(item["property_path"], f"{path}.property_path")
    if len(property_path) != 2:
        raise InvalidProfileStateError(
            f"{path}.property_path must contain exactly two strings"
        )
    return RelationalRequirement(
        property_path=PropertyPath(
            _string(property_path[0], f"{path}.property_path[0]"),
            _string(property_path[1], f"{path}.property_path[1]"),
        ),
        direction=_string(item["direction"], f"{path}.direction"),
    )


def _decode_property(value: object, path: str) -> ProfileProperty:
    item = _object(
        value,
        path,
        frozenset(
            {
                "claim_id",
                "evidence_applicable",
                "explicit_overrides",
                "knowledge",
                "owner",
                "relational_requirements",
                "section",
            }
        ),
    )
    requirements = tuple(
        _decode_relational_requirement(requirement, f"{path}.relational_requirements[{index}]")
        for index, requirement in enumerate(
            _array(item["relational_requirements"], f"{path}.relational_requirements")
        )
    )
    return ProfileProperty(
        claim_id=_string(item["claim_id"], f"{path}.claim_id"),
        section=_string(item["section"], f"{path}.section"),
        knowledge=_decode_knowledge(item["knowledge"], f"{path}.knowledge"),
        explicit_overrides=_string_tuple(
            item["explicit_overrides"],
            f"{path}.explicit_overrides",
        ),
        owner=_optional_string(item["owner"], f"{path}.owner"),
        evidence_applicable=_boolean(
            item["evidence_applicable"],
            f"{path}.evidence_applicable",
        ),
        relational_requirements=requirements,
    )


def _decode_authority(value: object, path: str) -> AuthorityScope:
    item = _object(
        value,
        path,
        frozenset(
            {
                "actor",
                "allows_material_propagation",
                "checkpoint_required",
                "dimensions",
                "provenance",
                "scope",
            }
        ),
    )
    return AuthorityScope(
        actor=_string(item["actor"], f"{path}.actor"),
        dimensions=_string_tuple(item["dimensions"], f"{path}.dimensions"),
        allows_material_propagation=_boolean(
            item["allows_material_propagation"],
            f"{path}.allows_material_propagation",
        ),
        checkpoint_required=_boolean(
            item["checkpoint_required"],
            f"{path}.checkpoint_required",
        ),
        scope=_decode_scope(item["scope"], f"{path}.scope"),
        provenance=_decode_provenance_array(
            item["provenance"],
            f"{path}.provenance",
        ),
    )


def _decode_reference(value: object, path: str) -> ReferenceSource:
    item = _object(
        value,
        path,
        frozenset(
            {
                "derived_claim_ids",
                "freshness",
                "locator",
                "mode",
                "provenance",
                "reference_id",
                "source_identity",
                "source_revision",
            }
        ),
    )
    return ReferenceSource(
        reference_id=_string(item["reference_id"], f"{path}.reference_id"),
        source_identity=_string(
            item["source_identity"],
            f"{path}.source_identity",
        ),
        locator=_string(item["locator"], f"{path}.locator"),
        mode=_string(item["mode"], f"{path}.mode"),
        freshness=_string(item["freshness"], f"{path}.freshness"),
        source_revision=_optional_string(
            item["source_revision"],
            f"{path}.source_revision",
        ),
        derived_claim_ids=_string_tuple(
            item["derived_claim_ids"],
            f"{path}.derived_claim_ids",
        ),
        provenance=_decode_provenance_array(
            item["provenance"],
            f"{path}.provenance",
        ),
    )


def _reject_nonstandard_number(value: str) -> object:
    raise ValueError(f"non-standard number: {value}")


def _reject_duplicate_fields(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object field: {key}")
        result[key] = value
    return result


def deserialize_profile_state(data: bytes) -> ProfileState:
    """Validate an entire persisted document before returning canonical state."""
    if not isinstance(data, bytes):
        raise InvalidProfileStateError("persisted state must be bytes")
    try:
        decoded = data.decode("utf-8")
        document = json.loads(
            decoded,
            object_pairs_hook=_reject_duplicate_fields,
            parse_constant=_reject_nonstandard_number,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise InvalidProfileStateError(f"invalid persisted JSON: {error}") from error

    root = _object(
        document,
        "$",
        frozenset(
            {
                "authority",
                "profile_id",
                "properties",
                "references",
                "schema_version",
            }
        ),
    )
    schema_version = _integer(root["schema_version"], "$.schema_version")
    if schema_version != CURRENT_SCHEMA_VERSION:
        raise UnsupportedSchemaVersionError(
            f"unsupported schema version: {schema_version}"
        )
    try:
        state = ProfileState(
            schema_version=schema_version,
            profile_id=_string(root["profile_id"], "$.profile_id"),
            properties=tuple(
                _decode_property(item, f"$.properties[{index}]")
                for index, item in enumerate(
                    _array(root["properties"], "$.properties")
                )
            ),
            authority=tuple(
                _decode_authority(item, f"$.authority[{index}]")
                for index, item in enumerate(
                    _array(root["authority"], "$.authority")
                )
            ),
            references=tuple(
                _decode_reference(item, f"$.references[{index}]")
                for index, item in enumerate(
                    _array(root["references"], "$.references")
                )
            ),
        )
        # Rewalk mutable Mapping fields before publishing any part of the state.
        _state_to_document(state)
        return state
    except InvalidProfileStateError:
        raise
    except (AttributeError, TypeError, ValueError) as error:
        raise InvalidProfileStateError(str(error)) from error


class ProfilePersistence:
    """Load and optimistically save complete canonical profile snapshots."""

    def __init__(self, storage: ProfileStorage) -> None:
        self._storage = storage

    def load(self) -> ProfileSnapshot | None:
        document = self._storage.read()
        if document is None:
            return None
        return self._snapshot(document)

    @staticmethod
    def _snapshot(document: _StoredDocument) -> ProfileSnapshot:
        return ProfileSnapshot(
            state=deserialize_profile_state(document.data),
            revision=document.revision,
            authorship=document.authorship,
        )

    def save(
        self,
        state: ProfileState,
        *,
        expected_revision: str | None,
        authorship: MutationAuthorship = UNKNOWN_AUTHORSHIP,
    ) -> ProfileSnapshot:
        data = serialize_profile_state(state)
        try:
            document = self._storage.compare_and_swap(
                expected_revision,
                data,
                authorship,
            )
        except _StorageRevisionMismatch as error:
            current = None
            validation_error = None
            if error.current is not None:
                try:
                    current = self._snapshot(error.current)
                except InvalidProfileStateError as invalid:
                    validation_error = str(invalid)
            raise RevisionConflictError(
                expected_revision=expected_revision,
                actual_revision=(
                    None if error.current is None else error.current.revision
                ),
                current=current,
                current_validation_error=validation_error,
            ) from error
        return ProfileSnapshot(
            state=state,
            revision=document.revision,
            authorship=document.authorship,
        )
