"""Pure, resumable reconciliation for corrected decision-bearing inputs.

The module owns reconciliation state and transitions only.  It deliberately
does not persist state or resolve subjective decisions independently; callers
persist :class:`ReconciliationState` with their canonical aggregate and every
dependent is evaluated through ``resolve_alignment``.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Mapping, TypeAlias, overload

from alignment_contract import (
    ActiveAlignmentResult,
    AlignmentRequest,
    PropagationBlockedError,
    StaleAlignmentError,
    authorize_propagation,
    resolve_alignment,
)
from identifiers import require_identifier as _require_identifier


RECONCILIATION_SCHEMA_VERSION = 1


def _require_unique(values: tuple[str, ...], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")


class DecisionInputKind(str, Enum):
    TASTE = "taste"
    INTENT = "intent"
    CONSTRAINT = "constraint"
    OWNERSHIP = "ownership"
    REFERENCE = "reference"
    CONTEXT = "context"
    AUTHORITY = "authority"


class WorkStatus(str, Enum):
    PENDING = "pending"
    UNVERIFIED = "unverified"
    COMPLETED = "completed"


class TransitionKind(str, Enum):
    CORRECTION_COMMITTED = "correction_committed"
    CORRECTION_REPLAYED = "correction_replayed"
    PROSPECTIVE_CHANGE_RECORDED = "prospective_change_recorded"
    DEPENDENT_UNCHANGED = "dependent_unchanged"
    DEPENDENT_CHANGE_REQUIRED = "dependent_change_required"
    DEPENDENT_BLOCKED = "dependent_blocked"
    DEPENDENT_VERIFIED = "dependent_verified"
    DEPENDENT_ALREADY_COMPLETED = "dependent_already_completed"
    PROPAGATION_ALLOWED = "propagation_allowed"
    PROPAGATION_BLOCKED = "propagation_blocked"
    CHALLENGE_ASSESSED = "challenge_assessed"
    CHALLENGE_REPLAYED = "challenge_replayed"


@dataclass(frozen=True)
class CorrectedInput:
    input_id: str
    kind: DecisionInputKind | str

    def __post_init__(self) -> None:
        _require_identifier(self.input_id, "input_id")
        try:
            kind = DecisionInputKind(self.kind)
        except ValueError as error:
            raise ValueError(f"unsupported decision input kind: {self.kind}") from error
        object.__setattr__(self, "kind", kind)


@dataclass(frozen=True, order=True)
class DimensionValue:
    dimension: str
    direction: str

    def __post_init__(self) -> None:
        _require_identifier(self.dimension, "dimension")
        _require_identifier(self.direction, "direction")


@dataclass(frozen=True)
class DependentRecord:
    dependent_id: str
    decision_id: str
    input_dependencies: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.dependent_id, "dependent_id")
        _require_identifier(self.decision_id, "decision_id")
        for input_id in self.input_dependencies:
            _require_identifier(input_id, "input_dependencies item")
        _require_unique(self.input_dependencies, "input_dependencies")
        object.__setattr__(
            self,
            "input_dependencies",
            tuple(sorted(self.input_dependencies)),
        )


@dataclass(frozen=True)
class AppliedCorrection:
    operation_id: str
    corrected_inputs: tuple[CorrectedInput, ...]
    basis_revision: str
    affected_dependents: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.basis_revision, "basis_revision")
        if not self.corrected_inputs:
            raise ValueError("a correction must identify at least one input")
        _require_unique(
            tuple(item.input_id for item in self.corrected_inputs),
            "corrected input ids",
        )
        _require_unique(self.affected_dependents, "affected dependents")


@dataclass(frozen=True)
class ReconciliationAttempt:
    correction_ids: tuple[str, ...]
    alignment_revision: str
    target_directions: tuple[DimensionValue, ...]
    observed_directions: tuple[DimensionValue, ...]
    status: WorkStatus
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_identifier(self.alignment_revision, "alignment_revision")
        _require_unique(self.correction_ids, "attempt correction ids")
        _require_unique(
            tuple(item.dimension for item in self.target_directions),
            "target dimensions",
        )
        _require_unique(
            tuple(item.dimension for item in self.observed_directions),
            "observed dimensions",
        )
        try:
            status = WorkStatus(self.status)
        except ValueError as error:
            raise ValueError(f"unsupported work status: {self.status}") from error
        object.__setattr__(self, "status", status)


@dataclass(frozen=True)
class ReconciliationWork:
    dependent_id: str
    correction_ids: tuple[str, ...]
    affected_input_ids: tuple[str, ...]
    basis_revision: str
    status: WorkStatus = WorkStatus.PENDING
    alignment_revision: str | None = None
    target_directions: tuple[DimensionValue, ...] = ()
    last_observed_directions: tuple[DimensionValue, ...] = ()
    blockers: tuple[str, ...] = ()
    attempts: tuple[ReconciliationAttempt, ...] = ()

    def __post_init__(self) -> None:
        _require_identifier(self.dependent_id, "dependent_id")
        _require_identifier(self.basis_revision, "basis_revision")
        _require_unique(self.correction_ids, "work correction ids")
        _require_unique(self.affected_input_ids, "affected input ids")
        try:
            status = WorkStatus(self.status)
        except ValueError as error:
            raise ValueError(f"unsupported work status: {self.status}") from error
        object.__setattr__(self, "status", status)


@dataclass(frozen=True)
class ReconciliationState:
    """Durable aggregate value; all nested data is immutable and canonical."""

    schema_version: int = RECONCILIATION_SCHEMA_VERSION
    dependents: tuple[DependentRecord, ...] = ()
    corrections: tuple[AppliedCorrection, ...] = ()
    work: tuple[ReconciliationWork, ...] = ()

    def __post_init__(self) -> None:
        if (
            type(self.schema_version) is not int
            or self.schema_version != RECONCILIATION_SCHEMA_VERSION
        ):
            raise ValueError(
                f"unsupported reconciliation schema version: {self.schema_version}"
            )
        dependent_ids = tuple(item.dependent_id for item in self.dependents)
        correction_ids = tuple(item.operation_id for item in self.corrections)
        work_ids = tuple(item.dependent_id for item in self.work)
        _require_unique(dependent_ids, "dependent ids")
        _require_unique(correction_ids, "correction operation ids")
        _require_unique(work_ids, "reconciliation work ids")
        unknown_work = set(work_ids) - set(dependent_ids)
        if unknown_work:
            raise ValueError(
                "reconciliation work references unknown dependents: "
                + ", ".join(sorted(unknown_work))
            )
        unknown_affected = {
            dependent_id
            for correction in self.corrections
            for dependent_id in correction.affected_dependents
            if dependent_id not in set(dependent_ids)
        }
        if unknown_affected:
            raise ValueError(
                "corrections reference unknown dependents: "
                + ", ".join(sorted(unknown_affected))
            )
        known_corrections = set(correction_ids)
        unknown_correction_ids = {
            correction_id
            for item in self.work
            for correction_id in item.correction_ids
            if correction_id not in known_corrections
        }
        if unknown_correction_ids:
            raise ValueError(
                "work references unknown corrections: "
                + ", ".join(sorted(unknown_correction_ids))
            )
        object.__setattr__(
            self,
            "dependents",
            tuple(sorted(self.dependents, key=lambda item: item.dependent_id)),
        )
        object.__setattr__(
            self,
            "work",
            tuple(sorted(self.work, key=lambda item: item.dependent_id)),
        )

    @property
    def incomplete(self) -> bool:
        return any(item.status is not WorkStatus.COMPLETED for item in self.work)


@dataclass(frozen=True)
class CommitCorrection:
    operation_id: str
    corrected_inputs: tuple[CorrectedInput, ...]
    basis_revision: str

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.basis_revision, "basis_revision")
        if not self.corrected_inputs:
            raise ValueError("a correction must identify at least one input")
        input_ids = tuple(item.input_id for item in self.corrected_inputs)
        _require_unique(input_ids, "corrected input ids")
        object.__setattr__(
            self,
            "corrected_inputs",
            tuple(sorted(self.corrected_inputs, key=lambda item: item.input_id)),
        )


@dataclass(frozen=True)
class ReconcileDependent:
    dependent_id: str
    current_request: AlignmentRequest
    observed_directions: tuple[DimensionValue, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.dependent_id, "dependent_id")
        dimensions = tuple(item.dimension for item in self.observed_directions)
        _require_unique(dimensions, "observed dimensions")
        object.__setattr__(
            self,
            "observed_directions",
            tuple(sorted(self.observed_directions)),
        )


@dataclass(frozen=True)
class CheckPropagation:
    dependent_id: str
    alignment: ActiveAlignmentResult
    current_request: AlignmentRequest

    def __post_init__(self) -> None:
        _require_identifier(self.dependent_id, "dependent_id")


class ArtifactJudgment(str, Enum):
    """Approval semantics carried by an approved artifact."""

    ACCEPTABLE = "acceptable"
    PREFERRED = "preferred"
    REFERENCE_QUALITY = "reference_quality"


class ComparisonFidelity(str, Enum):
    """How faithfully the artifact represents the compared dimensions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ChallengeOutcome(str, Enum):
    """What an approved-artifact comparison concluded about stored taste."""

    NOT_COMPARABLE = "not_comparable"
    NO_CONTRADICTION = "no_contradiction"
    ARTIFACT_EXCEPTION = "artifact_exception"
    CONTEXT_CHANGED = "context_changed"
    MODEL_STALE = "model_stale"


@dataclass(frozen=True)
class StoredTasteDirection:
    """One stored taste direction eligible (or not) for a challenge."""

    dimension: str
    direction: str
    input_id: str
    established: bool

    def __post_init__(self) -> None:
        _require_identifier(self.dimension, "dimension")
        _require_identifier(self.direction, "direction")
        _require_identifier(self.input_id, "input_id")


@dataclass(frozen=True)
class ArtifactComparison:
    """An approved artifact offered as evidence against stored taste."""

    artifact_id: str
    observed: tuple[DimensionValue, ...]
    judgment: ArtifactJudgment | str
    fidelity: ComparisonFidelity | str
    attributable: bool
    scope_matches: bool
    context_matches: bool
    ownership_matches: bool
    deliberate_exception: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.artifact_id, "artifact_id")
        _require_unique(
            tuple(item.dimension for item in self.observed),
            "observed dimensions",
        )
        try:
            judgment = ArtifactJudgment(self.judgment)
            fidelity = ComparisonFidelity(self.fidelity)
        except ValueError as error:
            raise ValueError(f"unsupported artifact comparison value: {error}") from error
        object.__setattr__(self, "judgment", judgment)
        object.__setattr__(self, "fidelity", fidelity)


@dataclass(frozen=True)
class ChallengeApprovedArtifact:
    """Compare one approved artifact against established stored taste."""

    operation_id: str
    targets: tuple[StoredTasteDirection, ...]
    artifact: ArtifactComparison
    basis_revision: str

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.basis_revision, "basis_revision")
        if not self.targets:
            raise ValueError("a challenge requires at least one stored direction")
        _require_unique(
            tuple(item.input_id for item in self.targets),
            "challenge target input ids",
        )


@dataclass(frozen=True)
class ChallengeAssessment:
    outcome: ChallengeOutcome
    contradicted_dimensions: tuple[str, ...]
    reasons: tuple[str, ...]


ReconciliationOperation: TypeAlias = (
    CommitCorrection
    | ReconcileDependent
    | CheckPropagation
    | ChallengeApprovedArtifact
)


@dataclass(frozen=True)
class RepairDirective:
    dependent_id: str
    changed_directions: tuple[DimensionValue, ...]
    alignment_revision: str


@dataclass(frozen=True)
class PropagationAssessment:
    permitted: bool
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReconciliationTransition:
    state: ReconciliationState
    kind: TransitionKind
    affected_dependents: tuple[str, ...] = ()
    alignment: ActiveAlignmentResult | None = None
    repair: RepairDirective | None = None
    propagation: PropagationAssessment | None = None
    challenge: ChallengeAssessment | None = None


class OperationIdentityConflictError(ValueError):
    """One correction operation id was reused for different input."""


def _apply_correction(
    state: ReconciliationState,
    operation: CommitCorrection,
) -> ReconciliationTransition:
    existing = next(
        (
            correction
            for correction in state.corrections
            if correction.operation_id == operation.operation_id
        ),
        None,
    )
    if existing is not None:
        if (
            existing.corrected_inputs != operation.corrected_inputs
            or existing.basis_revision != operation.basis_revision
        ):
            raise OperationIdentityConflictError(
                f"operation id {operation.operation_id!r} has different correction input"
            )
        return ReconciliationTransition(
            state=state,
            kind=TransitionKind.CORRECTION_REPLAYED,
            affected_dependents=existing.affected_dependents,
        )

    # Authority changes are prospective unless another substantive input changed
    # in the same authoritative correction.
    changed_input_ids = {
        item.input_id
        for item in operation.corrected_inputs
        if item.kind is not DecisionInputKind.AUTHORITY
    }
    affected = tuple(
        dependent.dependent_id
        for dependent in state.dependents
        if changed_input_ids.intersection(dependent.input_dependencies)
    )
    correction = AppliedCorrection(
        operation_id=operation.operation_id,
        corrected_inputs=operation.corrected_inputs,
        basis_revision=operation.basis_revision,
        affected_dependents=affected,
    )

    work_by_id = {item.dependent_id: item for item in state.work}
    dependent_by_id = {item.dependent_id: item for item in state.dependents}
    for dependent_id in affected:
        dependent = dependent_by_id[dependent_id]
        affected_inputs = tuple(
            sorted(changed_input_ids.intersection(dependent.input_dependencies))
        )
        current = work_by_id.get(dependent_id)
        correction_ids: tuple[str, ...]
        if current is None:
            correction_ids = (operation.operation_id,)
            combined_inputs = affected_inputs
        else:
            correction_ids = current.correction_ids + (operation.operation_id,)
            combined_inputs = tuple(
                sorted(set(current.affected_input_ids).union(affected_inputs))
            )
        work_by_id[dependent_id] = ReconciliationWork(
            dependent_id=dependent_id,
            correction_ids=correction_ids,
            affected_input_ids=combined_inputs,
            basis_revision=operation.basis_revision,
            status=WorkStatus.PENDING,
            attempts=current.attempts if current is not None else (),
        )

    next_state = ReconciliationState(
        schema_version=state.schema_version,
        dependents=state.dependents,
        corrections=state.corrections + (correction,),
        work=tuple(work_by_id.values()),
    )
    return ReconciliationTransition(
        state=next_state,
        kind=(
            TransitionKind.CORRECTION_COMMITTED
            if changed_input_ids
            else TransitionKind.PROSPECTIVE_CHANGE_RECORDED
        ),
        affected_dependents=affected,
    )


def _reconcile_dependent(
    state: ReconciliationState,
    operation: ReconcileDependent,
) -> ReconciliationTransition:
    dependent = next(
        (
            item
            for item in state.dependents
            if item.dependent_id == operation.dependent_id
        ),
        None,
    )
    if dependent is None:
        raise ValueError(f"unknown dependent: {operation.dependent_id}")
    work = next(
        (item for item in state.work if item.dependent_id == operation.dependent_id),
        None,
    )
    if work is None:
        raise ValueError(
            f"dependent {operation.dependent_id!r} has no reconciliation work"
        )
    if operation.current_request.decision_id != dependent.decision_id:
        raise ValueError(
            "current request decision_id does not match the tracked dependent"
        )
    if work.status is WorkStatus.COMPLETED:
        return ReconciliationTransition(
            state=state,
            kind=TransitionKind.DEPENDENT_ALREADY_COMPLETED,
        )

    requested_dimensions = set(operation.current_request.dimensions)
    observed_dimensions = {item.dimension for item in operation.observed_directions}
    if observed_dimensions != requested_dimensions:
        raise ValueError(
            "observed directions must cover exactly the current request dimensions"
        )

    alignment = resolve_alignment(operation.current_request)
    target = tuple(
        sorted(
            DimensionValue(dimension, resolved.direction)
            for dimension, resolved in alignment.dimensions.items()
            if resolved.direction is not None
        )
    )
    blockers = tuple(
        dict.fromkeys(
            tuple(f"unresolved:{item}" for item in alignment.unresolved_dimensions)
            + alignment.checkpoint_obligations
        )
    )
    if not alignment.propagation_eligible or len(target) != len(requested_dimensions):
        attempt = ReconciliationAttempt(
            correction_ids=work.correction_ids,
            alignment_revision=alignment.decision_bearing_revision,
            target_directions=target,
            observed_directions=operation.observed_directions,
            status=WorkStatus.UNVERIFIED,
            blockers=blockers or ("propagation-ineligible",),
        )
        updated = ReconciliationWork(
            dependent_id=work.dependent_id,
            correction_ids=work.correction_ids,
            affected_input_ids=work.affected_input_ids,
            basis_revision=work.basis_revision,
            status=WorkStatus.UNVERIFIED,
            alignment_revision=alignment.decision_bearing_revision,
            target_directions=target,
            last_observed_directions=operation.observed_directions,
            blockers=blockers or ("propagation-ineligible",),
            attempts=work.attempts + (attempt,),
        )
        next_work = tuple(updated if item is work else item for item in state.work)
        return ReconciliationTransition(
            state=ReconciliationState(
                state.schema_version,
                state.dependents,
                state.corrections,
                next_work,
            ),
            kind=TransitionKind.DEPENDENT_BLOCKED,
            affected_dependents=(operation.dependent_id,),
            alignment=alignment,
        )

    observed_by_dimension = {
        item.dimension: item.direction for item in operation.observed_directions
    }
    changed_directions = tuple(
        item
        for item in target
        if observed_by_dimension[item.dimension] != item.direction
    )
    status = WorkStatus.UNVERIFIED if changed_directions else WorkStatus.COMPLETED
    attempt = ReconciliationAttempt(
        correction_ids=work.correction_ids,
        alignment_revision=alignment.decision_bearing_revision,
        target_directions=target,
        observed_directions=operation.observed_directions,
        status=status,
    )
    updated = ReconciliationWork(
        dependent_id=work.dependent_id,
        correction_ids=work.correction_ids,
        affected_input_ids=work.affected_input_ids,
        basis_revision=work.basis_revision,
        status=status,
        alignment_revision=alignment.decision_bearing_revision,
        target_directions=target,
        last_observed_directions=operation.observed_directions,
        attempts=work.attempts + (attempt,),
    )
    next_work = tuple(updated if item is work else item for item in state.work)
    repair = (
        RepairDirective(
            dependent_id=operation.dependent_id,
            changed_directions=changed_directions,
            alignment_revision=alignment.decision_bearing_revision,
        )
        if changed_directions
        else None
    )
    return ReconciliationTransition(
        state=ReconciliationState(
            state.schema_version,
            state.dependents,
            state.corrections,
            next_work,
        ),
        kind=(
            TransitionKind.DEPENDENT_CHANGE_REQUIRED
            if repair is not None
            else (
                TransitionKind.DEPENDENT_VERIFIED
                if work.status is WorkStatus.UNVERIFIED
                else TransitionKind.DEPENDENT_UNCHANGED
            )
        ),
        affected_dependents=(operation.dependent_id,),
        alignment=alignment,
        repair=repair,
    )


def _check_propagation(
    state: ReconciliationState,
    operation: CheckPropagation,
) -> ReconciliationTransition:
    dependent = next(
        (
            item
            for item in state.dependents
            if item.dependent_id == operation.dependent_id
        ),
        None,
    )
    if dependent is None:
        raise ValueError(f"unknown dependent: {operation.dependent_id}")
    if (
        operation.alignment.decision_id != dependent.decision_id
        or operation.current_request.decision_id != dependent.decision_id
    ):
        raise ValueError(
            "alignment and current request must match the tracked dependent decision"
        )

    blockers: list[str] = []
    try:
        authorize_propagation(operation.alignment, operation.current_request)
    except StaleAlignmentError:
        blockers.append("stale-alignment")
    except PropagationBlockedError:
        blockers.append("alignment-ineligible")

    work = next(
        (item for item in state.work if item.dependent_id == operation.dependent_id),
        None,
    )
    if work is not None and work.status is not WorkStatus.COMPLETED:
        blockers.append(f"reconciliation:{work.status.value}")

    assessment = PropagationAssessment(
        permitted=not blockers,
        blockers=tuple(blockers),
    )
    return ReconciliationTransition(
        state=state,
        kind=(
            TransitionKind.PROPAGATION_ALLOWED
            if assessment.permitted
            else TransitionKind.PROPAGATION_BLOCKED
        ),
        alignment=operation.alignment,
        propagation=assessment,
    )


_GATE_NOT_ESTABLISHED = "only sufficiently established taste directions may be challenged"
_GATE_APPROVAL_IS_NOT_PREFERENCE = "approval semantics do not assert preference"
_GATE_LOW_FIDELITY = (
    "artifact fidelity does not represent the compared dimensions well enough"
)
_GATE_NOT_ATTRIBUTABLE = "the artifact approval was not attributable to a represented person"
_GATE_SCOPE_MISMATCH = "scope is not comparable with the stored direction's scope"
_GATE_OWNERSHIP_MISMATCH = (
    "the artifact represents a different owner's direction, not this taste"
)


def _challenge_gate_reasons(
    operation: ChallengeApprovedArtifact,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not all(target.established for target in operation.targets):
        reasons.append(_GATE_NOT_ESTABLISHED)
    if operation.artifact.judgment is ArtifactJudgment.ACCEPTABLE:
        reasons.append(_GATE_APPROVAL_IS_NOT_PREFERENCE)
    if operation.artifact.fidelity is not ComparisonFidelity.HIGH:
        reasons.append(_GATE_LOW_FIDELITY)
    if not operation.artifact.attributable:
        reasons.append(_GATE_NOT_ATTRIBUTABLE)
    if not operation.artifact.scope_matches:
        reasons.append(_GATE_SCOPE_MISMATCH)
    if not operation.artifact.ownership_matches:
        reasons.append(_GATE_OWNERSHIP_MISMATCH)
    return tuple(reasons)


def _contradicted_targets(
    operation: ChallengeApprovedArtifact,
) -> tuple[StoredTasteDirection, ...]:
    observed = {
        item.dimension: item.direction for item in operation.artifact.observed
    }
    return tuple(
        target
        for target in operation.targets
        if observed.get(target.dimension) not in {None, target.direction}
    )


def _challenge_artifact(
    state: ReconciliationState,
    operation: ChallengeApprovedArtifact,
) -> ReconciliationTransition:
    contradicted = tuple(
        sorted(_contradicted_targets(operation), key=lambda item: item.input_id)
    )
    derived_inputs = tuple(
        CorrectedInput(target.input_id, DecisionInputKind.TASTE)
        for target in contradicted
    )
    existing = next(
        (
            correction
            for correction in state.corrections
            if correction.operation_id == operation.operation_id
        ),
        None,
    )

    def assessment(
        outcome: ChallengeOutcome, reasons: tuple[str, ...]
    ) -> ChallengeAssessment:
        return ChallengeAssessment(
            outcome=outcome,
            contradicted_dimensions=tuple(
                sorted({item.dimension for item in contradicted})
            ),
            reasons=reasons,
        )

    if existing is not None:
        if (
            existing.corrected_inputs != derived_inputs
            or existing.basis_revision != operation.basis_revision
        ):
            raise OperationIdentityConflictError(
                f"operation id {operation.operation_id!r} has different challenge input"
            )
        return ReconciliationTransition(
            state=state,
            kind=TransitionKind.CHALLENGE_REPLAYED,
            affected_dependents=existing.affected_dependents,
            challenge=assessment(ChallengeOutcome.MODEL_STALE, ()),
        )

    gate_failures = _challenge_gate_reasons(operation)
    if gate_failures:
        return ReconciliationTransition(
            state=state,
            kind=TransitionKind.CHALLENGE_ASSESSED,
            challenge=assessment(ChallengeOutcome.NOT_COMPARABLE, gate_failures),
        )

    if not contradicted:
        return ReconciliationTransition(
            state=state,
            kind=TransitionKind.CHALLENGE_ASSESSED,
            challenge=assessment(
                ChallengeOutcome.NO_CONTRADICTION,
                ("the approved artifact agrees with the established direction",),
            ),
        )

    if operation.artifact.deliberate_exception:
        return ReconciliationTransition(
            state=state,
            kind=TransitionKind.CHALLENGE_ASSESSED,
            challenge=assessment(
                ChallengeOutcome.ARTIFACT_EXCEPTION,
                (
                    "a deliberate exception does not rewrite reusable taste; "
                    "record it without reopening the stored profile",
                ),
            ),
        )

    if not operation.artifact.context_matches:
        outcome = ChallengeOutcome.CONTEXT_CHANGED
        reason = (
            "a preferred artifact from another context suggests the stored "
            "direction is conditional; alignment reopens for that context"
        )
    else:
        outcome = ChallengeOutcome.MODEL_STALE
        reason = (
            "a comparable, preferred, context-matched artifact materially "
            "contradicts the stored direction; the model may be stale and "
            "alignment reopens"
        )
    reopened = _apply_correction(
        state,
        CommitCorrection(
            operation_id=operation.operation_id,
            corrected_inputs=derived_inputs,
            basis_revision=operation.basis_revision,
        ),
    )
    return ReconciliationTransition(
        state=reopened.state,
        kind=TransitionKind.CHALLENGE_ASSESSED,
        affected_dependents=reopened.affected_dependents,
        challenge=assessment(outcome, (reason,)),
    )


def apply_reconciliation_operation(
    state: ReconciliationState,
    operation: ReconciliationOperation,
) -> ReconciliationTransition:
    """Apply one immutable reconciliation command and return the next state."""
    if not isinstance(state, ReconciliationState):
        raise TypeError("state must be a ReconciliationState")
    if isinstance(operation, CommitCorrection):
        return _apply_correction(state, operation)
    if isinstance(operation, ReconcileDependent):
        return _reconcile_dependent(state, operation)
    if isinstance(operation, CheckPropagation):
        return _check_propagation(state, operation)
    if isinstance(operation, ChallengeApprovedArtifact):
        return _challenge_artifact(state, operation)
    raise TypeError(f"unsupported reconciliation operation: {type(operation).__name__}")


_ENUM_FIELDS: Mapping[str, type[DecisionInputKind] | type[WorkStatus]] = {
    "CorrectedInput.kind": DecisionInputKind,
    "ReconciliationWork.status": WorkStatus,
    "ReconciliationAttempt.status": WorkStatus,
}


def _document(value: object) -> object:
    """Convert one validated immutable value into canonical JSON data."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_document(item) for item in value]
    if isinstance(value, dict):
        return {key: _document(item) for key, item in sorted(value.items())}
    if not dataclasses.is_dataclass(value):
        raise TypeError(f"unsupported reconciliation state value: {type(value).__name__}")
    fields = dataclasses.fields(value)
    return {
        field.name: _document(getattr(value, field.name))
        for field in fields
        if field.name != "schema_version"
    }


def _identifier(value: object, path: str) -> str:
    if not isinstance(value, str) or not value or value.isspace():
        raise ValueError(f"{path} must be a non-empty stable identifier")
    return value


@overload
def _enum_value(
    value: object, path: Literal["CorrectedInput.kind"]
) -> DecisionInputKind:
    ...


@overload
def _enum_value(
    value: object,
    path: Literal["ReconciliationWork.status", "ReconciliationAttempt.status"],
) -> WorkStatus:
    ...


def _enum_value(value: object, path: str) -> DecisionInputKind | WorkStatus:
    expected = _ENUM_FIELDS[path]
    try:
        return expected(value)
    except ValueError as error:
        raise ValueError(f"unsupported value for {path}: {value}") from error


def _dimension_values(items: object, path: str) -> tuple[DimensionValue, ...]:
    if not isinstance(items, list):
        raise ValueError(f"{path} must be an array")
    return tuple(
        DimensionValue(
            dimension=_identifier(item.get("dimension"), f"{path}.dimension"),
            direction=_identifier(item.get("direction"), f"{path}.direction"),
        )
        for item in items
    )


def _strings(items: object, path: str) -> tuple[str, ...]:
    if not isinstance(items, list):
        raise ValueError(f"{path} must be an array")
    return tuple(_identifier(item, f"{path} item") for item in items)


def reconciliation_state_to_document(
    state: ReconciliationState,
) -> dict[str, object]:
    """Return the complete aggregate as JSON-compatible canonical data."""
    if not isinstance(state, ReconciliationState):
        raise TypeError("state must be a ReconciliationState")
    document = _document(state)
    if not isinstance(document, dict):
        raise TypeError("reconciliation document must be an object")
    document["schema_version"] = RECONCILIATION_SCHEMA_VERSION
    return document


def reconciliation_state_from_document(document: object) -> ReconciliationState:
    """Validate an entire persisted aggregate before returning canonical state."""
    if not isinstance(document, dict):
        raise ValueError("reconciliation document must be an object")
    required_keys = {"schema_version", "dependents", "corrections", "work"}
    difference = required_keys.symmetric_difference(set(document))
    if difference:
        raise ValueError(
            "invalid reconciliation document fields: " + ", ".join(sorted(difference))
        )
    schema_version = document["schema_version"]
    if (
        type(schema_version) is not int
        or schema_version != RECONCILIATION_SCHEMA_VERSION
    ):
        raise ValueError(f"unsupported reconciliation schema version: {schema_version}")
    try:
        dependents = tuple(
            DependentRecord(
                dependent_id=_identifier(item["dependent_id"], "$.dependent_id"),
                decision_id=_identifier(item["decision_id"], "$.decision_id"),
                input_dependencies=_strings(
                    item["input_dependencies"],
                    "$.input_dependencies",
                ),
            )
            for item in document["dependents"]
        )
        corrections = tuple(
            AppliedCorrection(
                operation_id=_identifier(item["operation_id"], "$.operation_id"),
                corrected_inputs=tuple(
                    CorrectedInput(
                        input_id=_identifier(entry["input_id"], "$.input_id"),
                        kind=_enum_value(entry["kind"], "CorrectedInput.kind"),
                    )
                    for entry in item["corrected_inputs"]
                ),
                basis_revision=_identifier(item["basis_revision"], "$.basis_revision"),
                affected_dependents=_strings(
                    item["affected_dependents"], "$.affected_dependents"
                ),
            )
            for item in document["corrections"]
        )
        work = tuple(
            ReconciliationWork(
                dependent_id=_identifier(item["dependent_id"], "$.dependent_id"),
                correction_ids=_strings(item["correction_ids"], "$.correction_ids"),
                affected_input_ids=_strings(
                    item["affected_input_ids"], "$.affected_input_ids"
                ),
                basis_revision=_identifier(item["basis_revision"], "$.basis_revision"),
                status=_enum_value(item["status"], "ReconciliationWork.status"),
                alignment_revision=item.get("alignment_revision"),
                target_directions=_dimension_values(
                    item["target_directions"], "$.target_directions"
                ),
                last_observed_directions=_dimension_values(
                    item["last_observed_directions"], "$.last_observed_directions"
                ),
                blockers=_strings(item.get("blockers", []), "$.blockers"),
                attempts=tuple(
                    ReconciliationAttempt(
                        correction_ids=_strings(
                            attempt["correction_ids"], "$.correction_ids"
                        ),
                        alignment_revision=_identifier(
                            attempt["alignment_revision"], "$.alignment_revision"
                        ),
                        target_directions=_dimension_values(
                            attempt["target_directions"], "$.target_directions"
                        ),
                        observed_directions=_dimension_values(
                            attempt["observed_directions"], "$.observed_directions"
                        ),
                        status=_enum_value(
                            attempt["status"], "ReconciliationAttempt.status"
                        ),
                        blockers=_strings(attempt.get("blockers", []), "$.blockers"),
                    )
                    for attempt in item["attempts"]
                ),
            )
            for item in document["work"]
        )
        return ReconciliationState(
            schema_version=schema_version,
            dependents=dependents,
            corrections=corrections,
            work=work,
        )
    except (KeyError, TypeError) as error:
        raise ValueError(f"invalid reconciliation document structure: {error}") from error
