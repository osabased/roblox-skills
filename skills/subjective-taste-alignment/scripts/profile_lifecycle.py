"""Profile lifecycle operations preserving exact epistemic boundaries.

This module owns the operational seam around a persisted profile: targeted
reset/relearn/retraction, undo, profile branching and selection, import and
export, schema migration, and consolidation.  All evidence interpretation and
claim reconciliation stays in :mod:`evidence_reconciliation`; lifecycle
decisions are expressed purely as evidence-applicability overlays:

- Events are never deleted or rewritten.  ``EvidenceState.events`` keeps the
  full audit history; targeted lifecycle operations append
  ``SupportLifecycleRecord`` entries that narrow which evidence-to-claim
  support may participate in future derivation.
- Recomputation projects recorded applicability onto immutable event copies
  and replays them through :func:`apply_evidence_operation`.  A reset
  typography implication therefore cannot silently resurrect, while the
  independently supported layout implication of the same event keeps
  working, and re-ingesting the same event cannot reactivate excluded
  support.  Corrections and relearns are retractions plus genuinely new
  evidence, never reactivated superseded basis.
- Branches are inert until explicitly selected.  Exactly one alternative
  branch is applicable at a time; branch-specific support stays isolated
  from parent and sibling branches, while explicitly broader evidence keeps
  its declared scope and merely records the receiving branch as provenance
  (``origin_branch`` never narrows applicability).
- Undo restores the complete prior profile and evidence-applicability state
  from an in-module ledger.  Unrelated artifact state never enters this
  seam, so reverting taste state cannot revert artifact implementation.
- Import distrusts externally supplied derived metadata: confidence is
  clamped to what the accompanying evidence state can derive, and
  provenance is filtered to what the cited evidence attests.  Structural
  tampering is rejected by the strict canonical deserializer.  The four
  evidence ledgers (events, lifecycle records, applied-operation markers,
  branches) are union-merged with local-first precedence instead of being
  replaced, so importing never destroys local audit history and locally
  applied operations stay detectable as replays afterwards.
- Migration keeps unavailable epistemic information unknown or explicitly
  absent instead of inventing provenance, confidence, or validation
  context.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import TypeAlias

from alignment_contract import (
    Disposition,
    EpistemicBasis,
    PreferenceKnowledge,
    Provenance,
)
from evidence_reconciliation import (
    AppliedOperation,
    ClaimResolution,
    EvidenceEvent,
    EvidenceImplication,
    EvidenceIdentityConflictError,
    EvidenceState,
    IngestEvidence,
    OperationIdentityConflictError,
    SupportApplicability,
    SupportLifecycleRecord,
    SupportRef,
    TransitionStatus,
    apply_evidence_operation,
)
from identifiers import require_identifier as _require_identifier
from profile_composition import ProfileProperty, PropertyPath
from profile_persistence import (
    CURRENT_SCHEMA_VERSION,
    InvalidProfileStateError,
    ProfileState,
    UnsupportedSchemaVersionError,
    deserialize_profile_state,
    serialize_profile_state,
)


class LifecycleStatus(str, Enum):
    """Outcome of one lifecycle seam invocation."""

    APPLIED = "applied"
    REPLAYED = "replayed"
    DUPLICATE_EVENT = "duplicate_event"
    UNDONE = "undone"
    REFUSED = "refused"


class LifecycleError(ValueError):
    """A lifecycle request violated an epistemic or identity boundary."""


@dataclass(frozen=True)
class ProfileBranch:
    """One named alternative with recorded ancestry and provenance."""

    branch_id: str
    parent_branch_id: str | None
    provenance: tuple[Provenance, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.branch_id, "branch_id")
        if self.parent_branch_id is not None:
            _require_identifier(self.parent_branch_id, "parent_branch_id")
        if self.parent_branch_id == self.branch_id:
            raise ValueError("a branch cannot be its own parent")
        if not self.provenance:
            raise ValueError("a branch requires recorded provenance")


@dataclass(frozen=True)
class BranchRegistry:
    """Registered alternative branches plus the single active selection."""

    branches: tuple[ProfileBranch, ...] = ()
    active_branch_id: str | None = None

    def branch(self, branch_id: str) -> ProfileBranch | None:
        for branch in self.branches:
            if branch.branch_id == branch_id:
                return branch
        return None


@dataclass(frozen=True)
class UndoEntry:
    """Snapshot of the complete lifecycle state preceding one operation."""

    operation_id: str
    state: LifecycleState


@dataclass(frozen=True)
class LifecycleState:
    """Profile, evidence applicability, branches, and the undo ledger."""

    profile: ProfileState
    evidence: EvidenceState
    branches: BranchRegistry
    undo_ledger: tuple[UndoEntry, ...] = ()


@dataclass(frozen=True)
class LifecycleTransition:
    """Result of one lifecycle operation over immutable state."""

    state: LifecycleState
    status: LifecycleStatus
    operation_id: str
    changed_claim_ids: tuple[str, ...]
    changed_property_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class IngestProfileEvidence:
    """Ingest one evidence event under the lifecycle applicability rules."""

    operation_id: str
    event: EvidenceEvent

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")


@dataclass(frozen=True)
class ResetSupport:
    """Exclude exactly one evidence-to-claim support as reset superseded."""

    operation_id: str
    support: SupportRef
    reason: str = "targeted reset excluded this superseded basis"

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.support.event_id, "support.event_id")
        _require_identifier(self.support.implication_id, "support.implication_id")
        if not self.reason or not self.reason.strip():
            raise ValueError("reason must be a non-empty explanation")


@dataclass(frozen=True)
class RetractEvidence:
    """Retract one whole event while keeping its history inspectable."""

    operation_id: str
    event_id: str
    reason: str = "event retracted by its source"

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.event_id, "event_id")
        if not self.reason or not self.reason.strip():
            raise ValueError("reason must be a non-empty explanation")


@dataclass(frozen=True)
class CreateBranch:
    """Register an inert alternative branch with ancestry and provenance."""

    operation_id: str
    branch_id: str
    parent_branch_id: str | None = None
    provenance: tuple[Provenance, ...] = ()

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        if not self.provenance:
            raise ValueError("creating a branch requires provenance")


@dataclass(frozen=True)
class SelectBranch:
    """Make exactly one registered branch the applicable alternative."""

    operation_id: str
    branch_id: str

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.branch_id, "branch_id")


@dataclass(frozen=True)
class ProfileExchange:
    """Exported profile document plus its accompanying epistemic state."""

    profile_document: bytes
    evidence: EvidenceState
    branches: BranchRegistry


@dataclass(frozen=True)
class ImportProfileExchange:
    """Adopt an exported bundle after validating derived metadata."""

    operation_id: str
    exchange: ProfileExchange

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")


@dataclass(frozen=True)
class UndoLastOperation:
    """Restore the state recorded immediately before the last mutation."""

    operation_id: str

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")


LifecycleOperation: TypeAlias = (
    IngestProfileEvidence
    | ResetSupport
    | RetractEvidence
    | CreateBranch
    | SelectBranch
    | ImportProfileExchange
    | UndoLastOperation
)


@dataclass(frozen=True)
class ConsolidationRequest:
    """Ask whether two profiles may merge without losing distinctions."""

    operation_id: str
    survivor: ProfileState
    absorbed: ProfileState

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")


@dataclass(frozen=True)
class ConsolidationOutcome:
    """Merged profile or a refusal that names the preserved distinction."""

    status: LifecycleStatus
    reason: str
    merged: ProfileState | None


def initial_lifecycle_state(
    profile: ProfileState,
    evidence: EvidenceState | None = None,
) -> LifecycleState:
    """Build a fresh lifecycle state, recomputing claims once from events."""
    if evidence is None:
        evidence = EvidenceState()
    return _assemble(
        profile=profile,
        events=evidence.events,
        lifecycle_records=evidence.support_lifecycle,
        applied_operations=evidence.applied_operations,
        branches=BranchRegistry(),
    )


def export_profile_exchange(state: LifecycleState) -> ProfileExchange:
    """Serialize the profile canonically beside its evidence and branches."""
    return ProfileExchange(
        profile_document=serialize_profile_state(state.profile),
        evidence=state.evidence,
        branches=state.branches,
    )


def apply_lifecycle_operation(
    state: LifecycleState,
    operation: LifecycleOperation,
) -> LifecycleTransition:
    """Apply one immutable, retry-safe lifecycle operation."""
    if isinstance(operation, IngestProfileEvidence):
        return _apply_ingest(state, operation)
    if isinstance(operation, ResetSupport):
        return _apply_reset(state, operation)
    if isinstance(operation, RetractEvidence):
        return _apply_retract(state, operation)
    if isinstance(operation, CreateBranch):
        return _apply_create_branch(state, operation)
    if isinstance(operation, SelectBranch):
        return _apply_select_branch(state, operation)
    if isinstance(operation, ImportProfileExchange):
        return _apply_import(state, operation)
    if isinstance(operation, UndoLastOperation):
        return _apply_undo(state, operation)
    raise LifecycleError(
        f"unsupported lifecycle operation: {type(operation).__name__}"
    )


def consolidate_profiles(request: ConsolidationRequest) -> ConsolidationOutcome:
    """Merge near-duplicate profiles or refuse with the preserved reason."""
    refusal = _consolidation_refusal(request.survivor, request.absorbed)
    if refusal is not None:
        return ConsolidationOutcome(
            status=LifecycleStatus.REFUSED,
            reason=refusal,
            merged=None,
        )
    return ConsolidationOutcome(
        status=LifecycleStatus.APPLIED,
        reason=(
            "merged near-duplicate profiles while preserving scope, context, "
            "provenance, and validation distinctions"
        ),
        merged=_merged_profile(request.survivor, request.absorbed),
    )


# --- internal helpers -----------------------------------------------------


_RECONCILE_PREFIX = "profile-lifecycle-reconcile"


def migrate_document(data: bytes) -> ProfileState:
    """Lift an older-schema document, keeping missing epistemics unknown."""
    if not isinstance(data, bytes):
        raise InvalidProfileStateError("persisted state must be bytes")
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InvalidProfileStateError(
            f"invalid persisted JSON: {error}"
        ) from error
    if not isinstance(document, dict):
        raise InvalidProfileStateError("$ must be an object")
    version = document.get("schema_version")
    if type(version) is not int:
        raise InvalidProfileStateError("$.schema_version must be an integer")
    if version > CURRENT_SCHEMA_VERSION:
        raise UnsupportedSchemaVersionError(
            f"unsupported schema version: {version}"
        )
    if version == CURRENT_SCHEMA_VERSION:
        return deserialize_profile_state(data)
    return deserialize_profile_state(_current_document_bytes(document))


def _fingerprint(operation: LifecycleOperation) -> str:
    return sha256(repr(operation).encode("utf-8")).hexdigest()


def _stable_id(event_id: str, implication_id: str) -> str:
    return f"{event_id}#{implication_id}"


def _as_basis(value: EpistemicBasis | str) -> EpistemicBasis:
    try:
        return EpistemicBasis(value)
    except ValueError as error:
        raise ValueError(f"unsupported epistemic basis: {value}") from error


def _as_disposition(value: Disposition | str) -> Disposition:
    try:
        return Disposition(value)
    except ValueError as error:
        raise ValueError(f"unsupported disposition: {value}") from error


def _as_applicability(value: SupportApplicability | str) -> SupportApplicability:
    try:
        return SupportApplicability(value)
    except ValueError as error:
        raise ValueError(f"unsupported support applicability: {value}") from error


def _check_operation_identity(
    applied_operations: tuple[AppliedOperation, ...],
    operation_id: str,
    fingerprint: str,
) -> bool:
    """Return True for an exact replay; raise on identity reuse."""
    for applied in applied_operations:
        if applied.operation_id != operation_id:
            continue
        if applied.fingerprint != fingerprint:
            raise OperationIdentityConflictError(
                f"operation_id {operation_id!r} was reused"
            )
        return True
    return False


def _replayed_transition(
    state: LifecycleState, operation: LifecycleOperation
) -> LifecycleTransition:
    """Build the shared no-op transition for an exact operation replay."""
    return LifecycleTransition(
        state=state,
        status=LifecycleStatus.REPLAYED,
        operation_id=operation.operation_id,
        changed_claim_ids=(),
        changed_property_ids=(),
        reason="operation was already applied",
    )


def _effective_events(
    events: tuple[EvidenceEvent, ...],
    lifecycle_records: tuple[SupportLifecycleRecord, ...],
    registry: BranchRegistry,
) -> tuple[EvidenceEvent, ...]:
    """Project lifecycle and branch applicability onto event copies."""
    overrides: dict[str, SupportApplicability] = {}
    for record in lifecycle_records:
        overrides[record.support.stable_id] = _as_applicability(
            record.applicability
        )
    effective: list[EvidenceEvent] = []
    for event in events:
        implications: list[EvidenceImplication] = []
        changed = False
        for implication in event.implications:
            declared = _as_applicability(implication.applicability)
            applicability = declared
            if implication.applicable_branches and (
                registry.active_branch_id is None
                or registry.active_branch_id
                not in implication.applicable_branches
            ):
                applicability = SupportApplicability.BRANCH_INAPPLICABLE
            override = overrides.get(
                _stable_id(event.event_id, implication.implication_id)
            )
            if override is not None:
                applicability = override
            if applicability is not declared:
                implication = replace(implication, applicability=applicability)
                changed = True
            implications.append(implication)
        if changed:
            event = replace(event, implications=tuple(implications))
        effective.append(event)
    return tuple(effective)


def _recompute_claims(
    events: tuple[EvidenceEvent, ...],
    lifecycle_records: tuple[SupportLifecycleRecord, ...],
    registry: BranchRegistry,
) -> tuple[ClaimResolution, ...]:
    """Replay projected events through the one reconciliation seam."""
    state = EvidenceState()
    for index, event in enumerate(
        _effective_events(events, lifecycle_records, registry)
    ):
        state = apply_evidence_operation(
            state,
            IngestEvidence(
                operation_id=f"{_RECONCILE_PREFIX}-{index}",
                event=event,
            ),
        ).state
    return state.claims


def _assemble(
    *,
    profile: ProfileState,
    events: tuple[EvidenceEvent, ...],
    lifecycle_records: tuple[SupportLifecycleRecord, ...],
    applied_operations: tuple[AppliedOperation, ...],
    branches: BranchRegistry,
) -> LifecycleState:
    return LifecycleState(
        profile=profile,
        evidence=EvidenceState(
            events=events,
            support_lifecycle=lifecycle_records,
            claims=_recompute_claims(events, lifecycle_records, branches),
            applied_operations=applied_operations,
        ),
        branches=branches,
    )


def _respond(
    before: LifecycleState,
    after: LifecycleState,
    *,
    operation_id: str,
    status: LifecycleStatus,
    reason: str,
    record_undo: bool,
) -> LifecycleTransition:
    if record_undo:
        after = replace(
            after,
            undo_ledger=before.undo_ledger
            + (UndoEntry(operation_id=operation_id, state=before),),
        )
    return LifecycleTransition(
        state=after,
        status=status,
        operation_id=operation_id,
        changed_claim_ids=_changed_claim_ids(
            before.evidence.claims, after.evidence.claims
        ),
        changed_property_ids=_changed_property_ids(
            before.profile.properties, after.profile.properties
        ),
        reason=reason,
    )


def _changed_claim_ids(
    before: tuple[ClaimResolution, ...],
    after: tuple[ClaimResolution, ...],
) -> tuple[str, ...]:
    old = {claim.claim_id: claim for claim in before}
    new = {claim.claim_id: claim for claim in after}
    return tuple(
        claim_id
        for claim_id in sorted(old.keys() | new.keys())
        if old.get(claim_id) != new.get(claim_id)
    )


def _changed_property_ids(
    before: tuple[ProfileProperty, ...],
    after: tuple[ProfileProperty, ...],
) -> tuple[str, ...]:
    old = {prop.claim_id: prop for prop in before}
    new = {prop.claim_id: prop for prop in after}
    return tuple(
        claim_id
        for claim_id in sorted(old.keys() | new.keys())
        if old.get(claim_id) != new.get(claim_id)
    )


def _find_event(
    events: tuple[EvidenceEvent, ...], event_id: str
) -> EvidenceEvent:
    for event in events:
        if event.event_id == event_id:
            return event
    raise ValueError(f"unknown evidence event: {event_id}")


def _validate_branch_references(
    event: EvidenceEvent, registry: BranchRegistry
) -> None:
    known = {branch.branch_id for branch in registry.branches}
    referenced = {
        branch_id
        for implication in event.implications
        for branch_id in implication.applicable_branches
    }
    if event.origin_branch is not None:
        referenced.add(event.origin_branch)
    unknown = sorted(referenced - known)
    if unknown:
        raise ValueError(f"unknown branch identifiers: {', '.join(unknown)}")


# --- operation handlers ---------------------------------------------------


def _apply_ingest(
    state: LifecycleState, operation: IngestProfileEvidence
) -> LifecycleTransition:
    # Identity, idempotent replay, duplicate-event, and conflict semantics
    # stay delegated to the one evidence seam; its markers fingerprint the
    # underlying IngestEvidence operation.
    _validate_branch_references(operation.event, state.branches)
    underlying = apply_evidence_operation(
        state.evidence,
        IngestEvidence(operation_id=operation.operation_id, event=operation.event),
    )
    if underlying.status is TransitionStatus.REPLAYED:
        return _replayed_transition(state, operation)
    after = _assemble(
        profile=state.profile,
        events=underlying.state.events,
        lifecycle_records=state.evidence.support_lifecycle,
        applied_operations=underlying.state.applied_operations,
        branches=state.branches,
    )
    if underlying.status is TransitionStatus.DUPLICATE_EVENT:
        return LifecycleTransition(
            state=after,
            status=LifecycleStatus.DUPLICATE_EVENT,
            operation_id=operation.operation_id,
            changed_claim_ids=(),
            changed_property_ids=(),
            reason=(
                "event was already recorded; lifecycle exclusions still hold"
            ),
        )
    return _respond(
        state,
        after,
        operation_id=operation.operation_id,
        status=LifecycleStatus.APPLIED,
        reason="evidence ingested and claims recomputed",
        record_undo=True,
    )


def _apply_reset(
    state: LifecycleState, operation: ResetSupport
) -> LifecycleTransition:
    if _check_operation_identity(
        state.evidence.applied_operations,
        operation.operation_id,
        _fingerprint(operation),
    ):
        return _replayed_transition(state, operation)
    target_event = _find_event(state.evidence.events, operation.support.event_id)
    implication_ids = {
        implication.implication_id for implication in target_event.implications
    }
    if operation.support.implication_id not in implication_ids:
        raise ValueError(f"unknown support: {operation.support.stable_id}")
    record = SupportLifecycleRecord(
        operation_id=operation.operation_id,
        support=operation.support,
        applicability=SupportApplicability.RESET_EXCLUDED,
        reason=operation.reason,
        provenance=target_event.provenance,
    )
    after = _assemble(
        profile=_exclude_from_profile(
            state.profile, {operation.support.stable_id}
        ),
        events=state.evidence.events,
        lifecycle_records=state.evidence.support_lifecycle + (record,),
        applied_operations=state.evidence.applied_operations
        + (
            AppliedOperation(operation.operation_id, _fingerprint(operation)),
        ),
        branches=state.branches,
    )
    return _respond(
        state,
        after,
        operation_id=operation.operation_id,
        status=LifecycleStatus.APPLIED,
        reason=f"support {operation.support.stable_id} reset-excluded",
        record_undo=True,
    )


def _apply_retract(
    state: LifecycleState, operation: RetractEvidence
) -> LifecycleTransition:
    if _check_operation_identity(
        state.evidence.applied_operations,
        operation.operation_id,
        _fingerprint(operation),
    ):
        return _replayed_transition(state, operation)
    target_event = _find_event(state.evidence.events, operation.event_id)
    records = tuple(
        SupportLifecycleRecord(
            operation_id=operation.operation_id,
            support=SupportRef(operation.event_id, implication.implication_id),
            applicability=SupportApplicability.RETRACTED,
            reason=operation.reason,
            provenance=target_event.provenance,
        )
        for implication in target_event.implications
    )
    excluded = {
        _stable_id(operation.event_id, implication.implication_id)
        for implication in target_event.implications
    }
    after = _assemble(
        profile=_exclude_from_profile(state.profile, excluded),
        events=state.evidence.events,
        lifecycle_records=state.evidence.support_lifecycle + records,
        applied_operations=state.evidence.applied_operations
        + (AppliedOperation(operation.operation_id, _fingerprint(operation)),),
        branches=state.branches,
    )
    return _respond(
        state,
        after,
        operation_id=operation.operation_id,
        status=LifecycleStatus.APPLIED,
        reason=f"event {operation.event_id} retracted; history retained",
        record_undo=True,
    )


def _exclude_from_profile(
    profile: ProfileState, stable_ids: set[str]
) -> ProfileState:
    properties: list[ProfileProperty] = []
    changed = False
    for prop in profile.properties:
        if set(prop.knowledge.evidence) & stable_ids:
            prop = replace(prop, evidence_applicable=False)
            changed = True
        properties.append(prop)
    if not changed:
        return profile
    return replace(profile, properties=tuple(properties))


def _apply_create_branch(
    state: LifecycleState, operation: CreateBranch
) -> LifecycleTransition:
    if _check_operation_identity(
        state.evidence.applied_operations,
        operation.operation_id,
        _fingerprint(operation),
    ):
        return _replayed_transition(state, operation)
    if state.branches.branch(operation.branch_id) is not None:
        raise ValueError(f"branch already exists: {operation.branch_id}")
    if (
        operation.parent_branch_id is not None
        and state.branches.branch(operation.parent_branch_id) is None
    ):
        raise ValueError(f"unknown parent branch: {operation.parent_branch_id}")
    branch = ProfileBranch(
        branch_id=operation.branch_id,
        parent_branch_id=operation.parent_branch_id,
        provenance=operation.provenance,
    )
    after = _assemble(
        profile=state.profile,
        events=state.evidence.events,
        lifecycle_records=state.evidence.support_lifecycle,
        applied_operations=state.evidence.applied_operations
        + (AppliedOperation(operation.operation_id, _fingerprint(operation)),),
        branches=BranchRegistry(
            branches=state.branches.branches + (branch,),
            active_branch_id=state.branches.active_branch_id,
        ),
    )
    ancestry = operation.parent_branch_id or "root lineage"
    return _respond(
        state,
        after,
        operation_id=operation.operation_id,
        status=LifecycleStatus.APPLIED,
        reason=(
            f"branch {operation.branch_id} created from {ancestry}; "
            "it stays inapplicable until selected"
        ),
        record_undo=True,
    )


def _apply_select_branch(
    state: LifecycleState, operation: SelectBranch
) -> LifecycleTransition:
    if _check_operation_identity(
        state.evidence.applied_operations,
        operation.operation_id,
        _fingerprint(operation),
    ):
        return _replayed_transition(state, operation)
    if state.branches.branch(operation.branch_id) is None:
        raise ValueError(f"unknown branch: {operation.branch_id}")
    if state.branches.active_branch_id == operation.branch_id:
        return LifecycleTransition(
            state=state,
            status=LifecycleStatus.APPLIED,
            operation_id=operation.operation_id,
            changed_claim_ids=(),
            changed_property_ids=(),
            reason=f"branch {operation.branch_id} was already active",
        )
    after = _assemble(
        profile=state.profile,
        events=state.evidence.events,
        lifecycle_records=state.evidence.support_lifecycle,
        applied_operations=state.evidence.applied_operations
        + (
            AppliedOperation(
                operation.operation_id, _fingerprint(operation)
            ),
        ),
        branches=replace(
            state.branches, active_branch_id=operation.branch_id
        ),
    )
    return _respond(
        state,
        after,
        operation_id=operation.operation_id,
        status=LifecycleStatus.APPLIED,
        reason=(
            f"branch {operation.branch_id} is now the only applicable "
            "alternative"
        ),
        record_undo=True,
    )


def _apply_import(
    state: LifecycleState, operation: ImportProfileExchange
) -> LifecycleTransition:
    if _check_operation_identity(
        state.evidence.applied_operations,
        operation.operation_id,
        _fingerprint(operation),
    ):
        return _replayed_transition(state, operation)
    incoming = deserialize_profile_state(operation.exchange.profile_document)
    evidence_in = operation.exchange.evidence
    validated, notes = _validate_derived_metadata(
        incoming.properties, evidence_in
    )
    merged_properties = _merge_properties(state.profile.properties, validated)
    merged_records = _merge_lifecycle_records(
        state.evidence.support_lifecycle,
        evidence_in.support_lifecycle,
    )
    profile = _exclude_from_profile(
        replace(incoming, properties=merged_properties),
        {
            record.support.stable_id
            for record in merged_records
            if record.applicability is not SupportApplicability.APPLICABLE
        },
    )
    applied_operations = _merge_applied_operations(
        state.evidence.applied_operations, evidence_in.applied_operations
    ) + (AppliedOperation(operation.operation_id, _fingerprint(operation)),)
    after = _assemble(
        profile=profile,
        events=_merge_events(state.evidence.events, evidence_in.events),
        lifecycle_records=merged_records,
        applied_operations=applied_operations,
        branches=_merge_branches(state.branches, operation.exchange.branches),
    )
    reason = "; ".join(notes) if notes else "import validated against evidence"
    return _respond(
        state,
        after,
        operation_id=operation.operation_id,
        status=LifecycleStatus.APPLIED,
        reason=reason,
        record_undo=True,
    )


def _validate_derived_metadata(
    properties: tuple[ProfileProperty, ...],
    evidence: EvidenceState,
) -> tuple[tuple[ProfileProperty, ...], list[str]]:
    """Clamp imported derived metadata to what the evidence can attest."""
    ceilings: dict[str, float] = {}
    for claim in evidence.claims:
        if claim.envelope is not None:
            ceilings[claim.envelope.representative_support.stable_id] = (
                claim.envelope.confidence
            )
    attested: dict[str, tuple[Provenance, ...]] = {}
    for event in evidence.events:
        for implication in event.implications:
            attested[_stable_id(event.event_id, implication.implication_id)] = (
                event.provenance
            )
    notes: list[str] = []
    validated: list[ProfileProperty] = []
    for prop in properties:
        cited = prop.knowledge.evidence
        if not cited:
            validated.append(prop)
            continue
        confidence = prop.knowledge.confidence
        attested_ceiling = max(
            (ceilings[support_id] for support_id in cited if support_id in ceilings),
            default=None,
        )
        if attested_ceiling is not None:
            if confidence > attested_ceiling:
                notes.append(
                    f"downgraded inflated confidence for {prop.claim_id} "
                    f"from {confidence} to {attested_ceiling}"
                )
                confidence = attested_ceiling
        else:
            notes.append(
                f"reset unverifiable confidence for {prop.claim_id} to 0.0; "
                "cited support derives no applicable claim"
            )
            confidence = 0.0
        allowed: set[Provenance] = set()
        for support_id in cited:
            allowed.update(attested.get(support_id, ()))
        provenance = tuple(
            item for item in prop.knowledge.provenance if item in allowed
        )
        if len(provenance) != len(prop.knowledge.provenance):
            notes.append(
                f"dropped unattested provenance entries for {prop.claim_id}"
            )
        if (
            confidence != prop.knowledge.confidence
            or provenance != prop.knowledge.provenance
        ):
            prop = replace(
                prop,
                knowledge=replace(
                    prop.knowledge,
                    confidence=confidence,
                    provenance=provenance,
                ),
            )
        validated.append(prop)
    return tuple(validated), notes


def _merge_properties(
    existing: tuple[ProfileProperty, ...],
    incoming: tuple[ProfileProperty, ...],
) -> tuple[ProfileProperty, ...]:
    replaced = {prop.claim_id: prop for prop in incoming}
    merged: list[ProfileProperty] = []
    seen: set[str] = set()
    for prop in existing:
        merged.append(replaced.get(prop.claim_id, prop))
        seen.add(prop.claim_id)
    for prop in incoming:
        if prop.claim_id not in seen:
            merged.append(prop)
    return tuple(merged)


def _merge_events(
    existing: tuple[EvidenceEvent, ...],
    incoming: tuple[EvidenceEvent, ...],
) -> tuple[EvidenceEvent, ...]:
    """Union events by event_id with local items first.

    Reusing an identity with divergent content raises instead of silently
    building a hybrid state, matching the ingest seam's conflict contract.
    """
    by_id = {event.event_id: event for event in existing}
    appended: list[EvidenceEvent] = []
    for event in incoming:
        local = by_id.get(event.event_id)
        if local is None:
            by_id[event.event_id] = event
            appended.append(event)
        elif local != event:
            raise EvidenceIdentityConflictError(
                f"event_id {event.event_id!r} was reused"
            )
    return existing + tuple(appended)


def _merge_lifecycle_records(
    existing: tuple[SupportLifecycleRecord, ...],
    incoming: tuple[SupportLifecycleRecord, ...],
) -> tuple[SupportLifecycleRecord, ...]:
    """Union lifecycle records by their identity with local items first.

    A record's identity is the pair of its creating operation and targeted
    support — the same key ``_assemble`` projects applicability from, so
    merging never drops local exclusions or reorders recorded history.
    """
    def identity(record: SupportLifecycleRecord) -> tuple[str, str]:
        return (record.operation_id, record.support.stable_id)

    seen = {identity(record) for record in existing}
    appended: list[SupportLifecycleRecord] = []
    for record in incoming:
        key = identity(record)
        if key not in seen:
            seen.add(key)
            appended.append(record)
    return existing + tuple(appended)


def _merge_applied_operations(
    existing: tuple[AppliedOperation, ...],
    incoming: tuple[AppliedOperation, ...],
) -> tuple[AppliedOperation, ...]:
    """Union applied-operation markers by operation_id, locals first.

    Synthetic operation ids are generated per device (``ingest-1`` on every
    history), so equal ids across independent histories usually name
    unrelated operations; the local marker wins and the foreign one is
    dropped.  A genuine divergence still surfaces: any later application
    reusing that id is checked against the retained local fingerprint and
    raises :class:`OperationIdentityConflictError`.
    """
    seen = {applied.operation_id for applied in existing}
    appended: list[AppliedOperation] = []
    for applied in incoming:
        if applied.operation_id not in seen:
            seen.add(applied.operation_id)
            appended.append(applied)
    return existing + tuple(appended)


def _merge_branches(
    existing: BranchRegistry, incoming: BranchRegistry
) -> BranchRegistry:
    """Union branch registries by branch_id, keeping the active selection.

    Local branches keep their position; unseen incoming branches are
    appended.  The incoming active selection wins when it names a branch
    that exists after the merge; otherwise the local selection stands.
    """
    seen = {branch.branch_id for branch in existing.branches}
    appended: list[ProfileBranch] = []
    for branch in incoming.branches:
        if branch.branch_id not in seen:
            seen.add(branch.branch_id)
            appended.append(branch)
    branches = existing.branches + tuple(appended)
    active = incoming.active_branch_id
    if active is None or not any(
        branch.branch_id == active for branch in branches
    ):
        active = existing.active_branch_id
    return BranchRegistry(branches=branches, active_branch_id=active)


def _apply_undo(
    state: LifecycleState, operation: UndoLastOperation
) -> LifecycleTransition:
    if not state.undo_ledger:
        raise ValueError("undo ledger is empty")
    entry = state.undo_ledger[-1]
    return LifecycleTransition(
        state=entry.state,
        status=LifecycleStatus.UNDONE,
        operation_id=operation.operation_id,
        changed_claim_ids=_changed_claim_ids(
            state.evidence.claims, entry.state.evidence.claims
        ),
        changed_property_ids=_changed_property_ids(
            state.profile.properties, entry.state.profile.properties
        ),
        reason=f"restored state preceding {entry.operation_id}",
    )


# --- schema migration -----------------------------------------------------


_UNKNOWN_DOMAIN = "unknown"


def _current_document_bytes(document: dict[str, object]) -> bytes:
    current: dict[str, object] = {
        "authority": document.get("authority", []),
        "profile_id": _require_string(document.get("profile_id"), "$.profile_id"),
        "properties": [
            _migrated_property(item, f"$.properties[{index}]")
            for index, item in enumerate(_as_array(document.get("properties")))
        ],
        "references": document.get("references", []),
        "schema_version": CURRENT_SCHEMA_VERSION,
    }
    canonical = json.dumps(
        current,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (canonical + "\n").encode("utf-8")


def _as_array(value: object) -> list[object]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise InvalidProfileStateError("expected an array")
    return value


def _require_string(value: object, path: str) -> str:
    if not isinstance(value, str):
        raise InvalidProfileStateError(f"{path} must be a string")
    return value


def _migrated_property(item: object, path: str) -> dict[str, object]:
    if not isinstance(item, dict):
        raise InvalidProfileStateError(f"{path} must be an object")
    knowledge = item.get("knowledge")
    if not isinstance(knowledge, dict):
        raise InvalidProfileStateError(f"{path}.knowledge must be an object")
    return {
        "claim_id": _require_string(
            item.get("claim_id"), f"{path}.claim_id"
        ),
        "evidence_applicable": item.get("evidence_applicable", True),
        "explicit_overrides": item.get("explicit_overrides", []),
        "knowledge": _migrated_knowledge(knowledge, f"{path}.knowledge"),
        "owner": item.get("owner"),
        "relational_requirements": item.get("relational_requirements", []),
        "section": _require_string(item.get("section"), f"{path}.section"),
    }


def _migrated_knowledge(
    knowledge: dict[str, object], path: str
) -> dict[str, object]:
    """Fill absent epistemic fields with unknown/absent values only.

    Missing provenance stays absent, missing confidence and strength stay at
    zero asserted weight, and missing validation context becomes an explicit
    unknown-domain placeholder.  Nothing stronger is ever invented.
    """
    validation_context = knowledge.get("validation_context")
    if validation_context is None:
        validation_context = {
            "conditions": [],
            "domain": _UNKNOWN_DOMAIN,
            "fidelity": _UNKNOWN_DOMAIN,
        }
    return {
        "basis": knowledge.get("basis", EpistemicBasis.INFERRED.value),
        "confidence": knowledge.get("confidence", 0.0),
        "context": knowledge.get("context", {}),
        "dimension": _require_string(
            knowledge.get("dimension"), f"{path}.dimension"
        ),
        "direction": knowledge.get("direction"),
        "disposition": _require_string(
            knowledge.get("disposition"), f"{path}.disposition"
        ),
        "evidence": knowledge.get("evidence", []),
        "provenance": knowledge.get("provenance", []),
        "relationships": knowledge.get("relationships", {}),
        "scope": knowledge.get("scope") or {},
        "strength": knowledge.get("strength", 0.0),
        "validation_context": validation_context,
    }


# --- consolidation --------------------------------------------------------


def _property_key(prop: ProfileProperty) -> PropertyPath:
    return PropertyPath(prop.section, prop.knowledge.dimension)


def _consolidation_refusal(
    survivor: ProfileState, absorbed: ProfileState
) -> str | None:
    if not survivor.properties or not absorbed.properties:
        return (
            "refused consolidation: a profile without scoped properties "
            "cannot be verified as a near duplicate"
        )
    survivor_keys = [_property_key(prop) for prop in survivor.properties]
    absorbed_keys = [_property_key(prop) for prop in absorbed.properties]
    if len(set(survivor_keys)) != len(survivor_keys) or len(
        set(absorbed_keys)
    ) != len(absorbed_keys):
        return (
            "refused consolidation: a profile has ambiguous duplicated "
            "property paths"
        )
    absorbed_by_key = dict(zip(absorbed_keys, absorbed.properties))
    for key, survivor_prop in zip(survivor_keys, survivor.properties):
        absorbed_prop = absorbed_by_key.get(key)
        if absorbed_prop is None:
            continue
        refusal = _pairwise_refusal(survivor_prop, absorbed_prop)
        if refusal is not None:
            return refusal
    survivor_subjects = {
        prop.knowledge.scope.represented_subject
        for prop in survivor.properties
    }
    absorbed_subjects = {
        prop.knowledge.scope.represented_subject
        for prop in absorbed.properties
    }
    if survivor_subjects != absorbed_subjects:
        return (
            "refused consolidation: profiles represent different subjects "
            f"({sorted(survivor_subjects)} vs {sorted(absorbed_subjects)})"
        )
    return None


def _pairwise_refusal(
    survivor_prop: ProfileProperty, absorbed_prop: ProfileProperty
) -> str | None:
    left = survivor_prop.knowledge
    right = absorbed_prop.knowledge
    label = f"{survivor_prop.section}.{left.dimension}"
    if left.direction != right.direction or left.disposition != right.disposition:
        return (
            f"refused consolidation: conflicting direction for {label} "
            f"({_as_disposition(left.disposition).value}:{left.direction} vs "
            f"{_as_disposition(right.disposition).value}:{right.direction})"
        )
    if dict(left.context) != dict(right.context):
        return (
            f"refused consolidation: context conditions differ for {label} "
            f"({dict(left.context)} vs {dict(right.context)})"
        )
    if left.validation_context != right.validation_context:
        return (
            f"refused consolidation: validation contexts differ for {label} "
            f"({left.validation_context} vs {right.validation_context})"
        )
    if left.scope != right.scope:
        return (
            f"refused consolidation: scopes differ for {label} "
            f"({left.scope} vs {right.scope})"
        )
    if (
        survivor_prop.owner is not None
        and absorbed_prop.owner is not None
        and survivor_prop.owner != absorbed_prop.owner
    ):
        return (
            f"refused consolidation: ownership differs for {label} "
            f"({survivor_prop.owner} vs {absorbed_prop.owner})"
        )
    for dimension, relation in right.relationships.items():
        existing = left.relationships.get(dimension)
        if existing is not None and existing != relation:
            return (
                "refused consolidation: relationships differ for "
                f"{label}:{dimension} ({existing} vs {relation})"
            )
    return None


def _ordered_union(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    return left + tuple(item for item in right if item not in left)


def _merged_knowledge(
    survivor_prop: ProfileProperty, absorbed_prop: ProfileProperty
) -> PreferenceKnowledge:
    left = survivor_prop.knowledge
    right = absorbed_prop.knowledge
    explicit = EpistemicBasis.EXPLICIT
    basis = (
        explicit
        if _as_basis(left.basis) is explicit and _as_basis(right.basis) is explicit
        else EpistemicBasis.INFERRED
    )
    relationships = dict(left.relationships)
    for dimension, relation in right.relationships.items():
        relationships.setdefault(dimension, relation)
    return PreferenceKnowledge(
        dimension=left.dimension,
        direction=left.direction,
        disposition=left.disposition,
        basis=basis,
        confidence=min(left.confidence, right.confidence),
        strength=min(left.strength, right.strength),
        scope=left.scope,
        context=left.context,
        evidence=_ordered_union(left.evidence, right.evidence),
        provenance=left.provenance
        + tuple(item for item in right.provenance if item not in left.provenance),
        validation_context=left.validation_context,
        relationships=relationships,
    )


def _merged_profile(
    survivor: ProfileState, absorbed: ProfileState
) -> ProfileState:
    absorbed_by_key = {
        _property_key(prop): prop for prop in absorbed.properties
    }
    properties: list[ProfileProperty] = []
    requirements_seen: set[tuple[PropertyPath, str]] = set()
    for prop in survivor.properties:
        other = absorbed_by_key.get(_property_key(prop))
        if other is None:
            properties.append(prop)
        else:
            requirements = list(prop.relational_requirements)
            for requirement in other.relational_requirements:
                key = (requirement.property_path, requirement.direction)
                if key not in requirements_seen:
                    requirements_seen.add(key)
                    requirements.append(requirement)
            properties.append(
                ProfileProperty(
                    claim_id=prop.claim_id,
                    section=prop.section,
                    knowledge=_merged_knowledge(prop, other),
                    explicit_overrides=_ordered_union(
                        prop.explicit_overrides, other.explicit_overrides
                    ),
                    owner=prop.owner,
                    evidence_applicable=(
                        prop.evidence_applicable and other.evidence_applicable
                    ),
                    relational_requirements=tuple(requirements),
                )
            )
    for prop in absorbed.properties:
        if _property_key(prop) not in {
            _property_key(existing) for existing in survivor.properties
        }:
            properties.append(prop)
    return ProfileState(
        schema_version=CURRENT_SCHEMA_VERSION,
        profile_id=survivor.profile_id,
        properties=tuple(properties),
        authority=survivor.authority + tuple(
            item for item in absorbed.authority if item not in survivor.authority
        ),
        references=survivor.references + tuple(
            item for item in absorbed.references if item not in survivor.references
        ),
    )
