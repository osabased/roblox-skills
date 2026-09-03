"""Immutable exploration state through one transition interface."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import TypeAlias

from alignment_contract import Provenance, Scope, ValidationContext
from evidence_reconciliation import (
    EvidenceEvent,
    EvidenceImplication,
    EvidenceType,
    FeedbackKind,
    Judgment,
)
from identifiers import require_identifier as _require_identifier


class ExplorationMode(str, Enum):
    CALIBRATION = "calibration"
    DELIBERATE_DIVERGENCE = "deliberate_divergence"


class LearningMode(str, Enum):
    LEARNING = "learning"
    NON_LEARNING = "non_learning"


class NoveltyBudget(str, Enum):
    CLOSE = "close"
    ONE_UNUSUAL_DIMENSION = "one_unusual_dimension"
    RADICAL = "radical"


class AlternativeStatus(str, Enum):
    CANDIDATE = "candidate"
    REJECTED = "rejected"
    SELECTED = "selected"
    ABANDONED = "abandoned"


@dataclass(frozen=True)
class DirectionChoice:
    dimension: str
    direction: str

    def __post_init__(self) -> None:
        _require_identifier(self.dimension, "direction dimension")
        _require_identifier(self.direction, "direction")


@dataclass(frozen=True)
class ExplorationQuestion:
    question_id: str
    prompt: str
    high_leverage_dimensions: tuple[str, ...]
    required_context: ValidationContext

    def __post_init__(self) -> None:
        _require_identifier(self.question_id, "question_id")
        _require_identifier(self.prompt, "question prompt")
        if not self.high_leverage_dimensions:
            raise ValueError("an exploration question needs a named dimension")
        if len(set(self.high_leverage_dimensions)) != len(
            self.high_leverage_dimensions
        ):
            raise ValueError("question dimensions must be unique")


@dataclass(frozen=True)
class ExplorationAlternative:
    alternative_id: str
    directions: tuple[DirectionChoice, ...]
    high_leverage_dimensions: tuple[str, ...]
    validation_context: ValidationContext
    artifact_ids: tuple[str, ...] = ()
    status: AlternativeStatus | str = AlternativeStatus.CANDIDATE

    def __post_init__(self) -> None:
        _require_identifier(self.alternative_id, "alternative_id")
        object.__setattr__(self, "status", AlternativeStatus(self.status))
        if not self.directions:
            raise ValueError("an alternative needs at least one direction")
        dimensions = tuple(choice.dimension for choice in self.directions)
        if len(set(dimensions)) != len(dimensions):
            raise ValueError("alternative direction dimensions must be unique")
        if not self.high_leverage_dimensions:
            raise ValueError("an alternative needs a named high-leverage dimension")
        if not set(self.high_leverage_dimensions).issubset(dimensions):
            raise ValueError(
                "high-leverage dimensions must be represented by the alternative"
            )
        if len(set(self.artifact_ids)) != len(self.artifact_ids):
            raise ValueError("artifact identifiers must be unique")


@dataclass(frozen=True)
class StartExploration:
    operation_id: str
    exploration_id: str
    mode: ExplorationMode | str
    learning_mode: LearningMode | str
    scope: Scope
    question: ExplorationQuestion
    alternatives: tuple[ExplorationAlternative, ...]
    novelty_budget: NoveltyBudget | str

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.exploration_id, "exploration_id")
        object.__setattr__(self, "mode", ExplorationMode(self.mode))
        object.__setattr__(self, "learning_mode", LearningMode(self.learning_mode))
        object.__setattr__(self, "novelty_budget", NoveltyBudget(self.novelty_budget))


@dataclass(frozen=True)
class SelectAlternative:
    operation_id: str
    alternative_id: str

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.alternative_id, "alternative_id")


@dataclass(frozen=True)
class DelegateSelection:
    """The user delegates the pick; the choice stays authorized judgment."""

    operation_id: str
    alternative_id: str

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.alternative_id, "alternative_id")


@dataclass(frozen=True)
class RejectAlternatives:
    operation_id: str
    alternative_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        if not self.alternative_ids:
            raise ValueError("reject needs at least one alternative")
        if len(set(self.alternative_ids)) != len(self.alternative_ids):
            raise ValueError("rejected alternative identifiers must be unique")


@dataclass(frozen=True)
class CleanupExploration:
    """Retire dead-end alternatives without recording rejection as taste.

    Abandonment is bookkeeping for alternatives that are no longer viable
    (stale artifacts, superseded riffs, withdrawn work).  It is distinct
    from rejection: a rejected direction is subjective feedback, while an
    abandoned one carries no preference signal at all.
    """

    operation_id: str
    alternative_ids: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        if not self.alternative_ids:
            raise ValueError("cleanup needs at least one alternative")
        if len(set(self.alternative_ids)) != len(self.alternative_ids):
            raise ValueError("cleaned-up alternative identifiers must be unique")
        _require_identifier(self.reason, "cleanup reason")


@dataclass(frozen=True)
class DirectionSource:
    dimension: str
    alternative_id: str

    def __post_init__(self) -> None:
        _require_identifier(self.dimension, "source dimension")
        _require_identifier(self.alternative_id, "source alternative_id")


@dataclass(frozen=True)
class CombineSelection:
    operation_id: str
    alternative_id: str
    sources: tuple[DirectionSource, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.alternative_id, "alternative_id")
        if not self.sources:
            raise ValueError("a combined selection needs direction sources")
        dimensions = tuple(item.dimension for item in self.sources)
        if len(set(dimensions)) != len(dimensions):
            raise ValueError("combined source dimensions must be unique")


@dataclass(frozen=True)
class RequestRiff:
    operation_id: str
    preserved_sources: tuple[DirectionSource, ...] = ()
    novelty_budget: NoveltyBudget | str | None = None

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        dimensions = tuple(item.dimension for item in self.preserved_sources)
        if len(set(dimensions)) != len(dimensions):
            raise ValueError("preserved source dimensions must be unique")
        if self.novelty_budget is not None:
            object.__setattr__(
                self, "novelty_budget", NoveltyBudget(self.novelty_budget)
            )


@dataclass(frozen=True)
class AddRiff:
    operation_id: str
    request_id: str
    alternative: ExplorationAlternative

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.request_id, "request_id")


ExplorationCommand: TypeAlias = (
    StartExploration
    | SelectAlternative
    | DelegateSelection
    | RejectAlternatives
    | CleanupExploration
    | CombineSelection
    | RequestRiff
    | AddRiff
)


@dataclass(frozen=True)
class SelectionRecord:
    operation_id: str
    alternative_id: str
    selected_by: str


@dataclass(frozen=True)
class ProductionSelectionIntent:
    """A selected direction awaiting canonical alignment and propagation."""

    exploration_id: str
    alternative_id: str
    scope: Scope
    directions: tuple[DirectionChoice, ...]
    selected_by: str
    deliberate_divergence: bool = False


@dataclass(frozen=True)
class RiffRequest:
    request_id: str
    question: ExplorationQuestion
    preserved_directions: tuple[DirectionChoice, ...]
    novelty_budget: NoveltyBudget


@dataclass(frozen=True)
class ExplorationState:
    exploration_id: str
    mode: ExplorationMode
    learning_mode: LearningMode
    scope: Scope
    question: ExplorationQuestion
    alternatives: tuple[ExplorationAlternative, ...]
    novelty_budget: NoveltyBudget
    selection: SelectionRecord | None = None
    pending_riff: RiffRequest | None = None


@dataclass(frozen=True)
class ExplorationTransition:
    state: ExplorationState
    production_candidate: ProductionSelectionIntent | None = None
    evidence_transition: object | None = None
    generation_request: RiffRequest | None = None


def _context_is_representative(
    actual: ValidationContext, required: ValidationContext
) -> bool:
    fidelity_rank = {"low": 1, "medium": 2, "high": 3}
    return (
        actual.domain == required.domain
        and fidelity_rank.get(actual.fidelity, 0)
        >= fidelity_rank.get(required.fidelity, 0)
        and set(required.conditions).issubset(actual.conditions)
    )


def run_exploration(
    state: ExplorationState | None,
    command: ExplorationCommand,
) -> ExplorationTransition:
    """Apply one exploration command without mutating the supplied state."""
    if state is not None:
        return _continue_exploration(state, command)
    if not isinstance(command, StartExploration):
        raise ValueError("StartExploration is required before other commands")
    if (
        command.mode is ExplorationMode.DELIBERATE_DIVERGENCE
        and command.learning_mode is LearningMode.LEARNING
    ):
        raise ValueError(
            "deliberate divergence must not learn into taste profiles; "
            "rejected divergence must not become contradictory taste evidence"
        )
    if len(command.alternatives) < 2:
        raise ValueError("exploration needs at least two alternatives")
    ids = tuple(item.alternative_id for item in command.alternatives)
    if len(set(ids)) != len(ids):
        raise ValueError("alternative identifiers must be unique")
    required_dimensions = set(command.question.high_leverage_dimensions)
    signatures: set[tuple[tuple[str, str], ...]] = set()
    for alternative in command.alternatives:
        direction_by_dimension = {
            choice.dimension: choice.direction for choice in alternative.directions
        }
        if not required_dimensions.issubset(direction_by_dimension):
            raise ValueError(
                "each alternative must represent every question dimension"
            )
        if not _context_is_representative(
            alternative.validation_context,
            command.question.required_context,
        ):
            raise ValueError(
                "each alternative must use sufficiently representative context"
            )
        signatures.add(
            tuple(
                (dimension, direction_by_dimension[dimension])
                for dimension in command.question.high_leverage_dimensions
            )
        )
    if len(signatures) < 2:
        raise ValueError("alternatives must differ along a named dimension")
    return ExplorationTransition(
        state=ExplorationState(
            exploration_id=command.exploration_id,
            mode=ExplorationMode(command.mode),
            learning_mode=LearningMode(command.learning_mode),
            scope=command.scope,
            question=command.question,
            alternatives=command.alternatives,
            novelty_budget=NoveltyBudget(command.novelty_budget),
        )
    )


def promotion_evidence_event(
    intent: ProductionSelectionIntent,
    *,
    instruction_id: str,
    provenance: tuple[Provenance, ...],
    validation_context: ValidationContext,
    implications: tuple[EvidenceImplication, ...],
) -> EvidenceEvent:
    """Bridge a promoted discovery into the normal evidence model.

    The sandbox grants nothing by itself: the returned event carries only
    the attributable instruction behind the promotion, and its confidence
    is derived from the supplied implications' own quality.  The event id
    is deterministic, so promoting the same selection twice replays as a
    duplicate instead of manufacturing a second observation.
    """

    _require_identifier(instruction_id, "instruction_id")
    return EvidenceEvent(
        event_id=(
            f"{intent.exploration_id}:promotion:{instruction_id}"
            f":{intent.alternative_id}"
        ),
        evidence_type=EvidenceType.EXPLICIT_FEEDBACK,
        scope=intent.scope,
        context=(),
        provenance=provenance,
        validation_context=validation_context,
        occurred_at=0,
        implications=tuple(implications),
        feedback=FeedbackKind.APPROVAL,
        judgment=Judgment.PREFERRED,
    )


def _alternative_by_id(
    state: ExplorationState, alternative_id: str
) -> ExplorationAlternative:
    for alternative in state.alternatives:
        if alternative.alternative_id == alternative_id:
            return alternative
    raise ValueError(f"unknown alternative: {alternative_id}")


def _require_live(
    alternative: ExplorationAlternative, role: str
) -> ExplorationAlternative:
    if alternative.status is AlternativeStatus.ABANDONED:
        raise ValueError(
            f"{alternative.alternative_id} was abandoned and cannot be {role}"
        )
    return alternative


def _select(
    state: ExplorationState,
    alternative: ExplorationAlternative,
    *,
    operation_id: str,
    selected_by: str,
) -> ExplorationTransition:
    _require_live(alternative, "selected")
    alternatives = tuple(
        replace(
            item,
            status=(
                AlternativeStatus.SELECTED
                if item.alternative_id == alternative.alternative_id
                else (
                    AlternativeStatus.CANDIDATE
                    if item.status is AlternativeStatus.SELECTED
                    else item.status
                )
            ),
        )
        for item in state.alternatives
    )
    selected = _alternative_by_id(
        replace(state, alternatives=alternatives), alternative.alternative_id
    )
    selection = SelectionRecord(operation_id, selected.alternative_id, selected_by)
    next_state = replace(state, alternatives=alternatives, selection=selection)
    return ExplorationTransition(
        state=next_state,
        production_candidate=ProductionSelectionIntent(
            exploration_id=state.exploration_id,
            alternative_id=selected.alternative_id,
            scope=state.scope,
            directions=selected.directions,
            selected_by=selected_by,
            deliberate_divergence=(
                state.mode is ExplorationMode.DELIBERATE_DIVERGENCE
            ),
        ),
    )


def _continue_exploration(
    state: ExplorationState,
    command: ExplorationCommand,
) -> ExplorationTransition:
    if isinstance(command, StartExploration):
        raise ValueError("an exploration is already active")
    if isinstance(command, RejectAlternatives):
        for alternative_id in command.alternative_ids:
            _alternative_by_id(state, alternative_id)
        rejected = set(command.alternative_ids)
        alternatives = tuple(
            replace(item, status=AlternativeStatus.REJECTED)
            if item.alternative_id in rejected
            else item
            for item in state.alternatives
        )
        selection = state.selection
        if selection is not None and selection.alternative_id in rejected:
            selection = None
        return ExplorationTransition(
            state=replace(
                state,
                alternatives=alternatives,
                selection=selection,
            )
        )
    if isinstance(command, CleanupExploration):
        for alternative_id in command.alternative_ids:
            _alternative_by_id(state, alternative_id)
        selected_id = (
            state.selection.alternative_id if state.selection is not None else None
        )
        cleaned_up = set(command.alternative_ids)
        if selected_id in cleaned_up:
            raise ValueError(
                "the selected alternative cannot be abandoned; "
                "select a different alternative first"
            )
        alternatives = tuple(
            replace(item, status=AlternativeStatus.ABANDONED)
            if item.alternative_id in cleaned_up
            else item
            for item in state.alternatives
        )
        return ExplorationTransition(
            state=replace(state, alternatives=alternatives),
        )
    if isinstance(command, SelectAlternative):
        alternative = _alternative_by_id(state, command.alternative_id)
        return _select(
            state,
            alternative,
            operation_id=command.operation_id,
            selected_by="user",
        )
    if isinstance(command, DelegateSelection):
        alternative = _alternative_by_id(state, command.alternative_id)
        return _select(
            state,
            alternative,
            operation_id=command.operation_id,
            selected_by="user-delegation",
        )
    if isinstance(command, CombineSelection):
        if any(
            item.alternative_id == command.alternative_id
            for item in state.alternatives
        ):
            raise ValueError(
                f"alternative already exists: {command.alternative_id}"
            )
        required = set(state.question.high_leverage_dimensions)
        supplied = {item.dimension for item in command.sources}
        if supplied != required:
            raise ValueError(
                "a combined selection must source every question dimension"
            )
        directions: list[DirectionChoice] = []
        for source in command.sources:
            source_alternative = _require_live(
                _alternative_by_id(state, source.alternative_id),
                "used as a combination source",
            )
            try:
                direction = next(
                    choice.direction
                    for choice in source_alternative.directions
                    if choice.dimension == source.dimension
                )
            except StopIteration as error:
                raise ValueError(
                    f"{source.alternative_id} does not represent "
                    f"{source.dimension}"
                ) from error
            directions.append(DirectionChoice(source.dimension, direction))
        combined = ExplorationAlternative(
            alternative_id=command.alternative_id,
            directions=tuple(directions),
            high_leverage_dimensions=state.question.high_leverage_dimensions,
            validation_context=state.question.required_context,
        )
        combined_state = replace(
            state,
            alternatives=state.alternatives + (combined,),
        )
        return _select(
            combined_state,
            combined,
            operation_id=command.operation_id,
            selected_by="user-combination",
        )
    if isinstance(command, RequestRiff):
        preserved: list[DirectionChoice] = []
        for source in command.preserved_sources:
            source_alternative = _require_live(
                _alternative_by_id(state, source.alternative_id),
                "preserved as a riff source",
            )
            try:
                direction = next(
                    choice.direction
                    for choice in source_alternative.directions
                    if choice.dimension == source.dimension
                )
            except StopIteration as error:
                raise ValueError(
                    f"{source.alternative_id} does not represent "
                    f"{source.dimension}"
                ) from error
            preserved.append(DirectionChoice(source.dimension, direction))
        request = RiffRequest(
            request_id=command.operation_id,
            question=state.question,
            preserved_directions=tuple(preserved),
            novelty_budget=NoveltyBudget(command.novelty_budget or state.novelty_budget),
        )
        return ExplorationTransition(
            state=replace(state, pending_riff=request),
            generation_request=request,
        )
    if isinstance(command, AddRiff):
        pending = state.pending_riff
        if pending is None or pending.request_id != command.request_id:
            raise ValueError("riff does not match the active generation request")
        if any(
            item.alternative_id == command.alternative.alternative_id
            for item in state.alternatives
        ):
            raise ValueError(
                f"alternative already exists: {command.alternative.alternative_id}"
            )
        riff_directions = {
            choice.dimension: choice.direction
            for choice in command.alternative.directions
        }
        if not set(state.question.high_leverage_dimensions).issubset(
            riff_directions
        ):
            raise ValueError("a riff must represent every question dimension")
        if not _context_is_representative(
            command.alternative.validation_context,
            state.question.required_context,
        ):
            raise ValueError("a riff must use sufficiently representative context")
        for kept in pending.preserved_directions:
            if riff_directions.get(kept.dimension) != kept.direction:
                raise ValueError(
                    f"riff did not preserve {kept.dimension}"
                )
        signature = tuple(
            (dimension, riff_directions[dimension])
            for dimension in state.question.high_leverage_dimensions
        )
        existing_signatures = {
            tuple(
                (
                    dimension,
                    next(
                        choice.direction
                        for choice in alternative.directions
                        if choice.dimension == dimension
                    ),
                )
                for dimension in state.question.high_leverage_dimensions
            )
            for alternative in state.alternatives
        }
        if signature in existing_signatures:
            raise ValueError("a riff must add a meaningfully different direction")
        return ExplorationTransition(
            state=replace(
                state,
                alternatives=state.alternatives + (command.alternative,),
                pending_riff=None,
            )
        )
    raise TypeError(f"unsupported exploration command: {type(command).__name__}")
