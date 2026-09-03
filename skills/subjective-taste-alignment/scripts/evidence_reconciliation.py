"""Pure evidence interpretation and reconciliation for subjective taste.

The module has one mutation seam: :func:`apply_evidence_operation`.  Every
value crossing that seam is immutable, so callers can persist or retry a
transition without partially changing the supplied state.

Reconciliation semantics over time:

- Usable supports confront each other inside one claim group (same claim
  shape, scope, represented subject, context, and branch set).  Cross-scope
  confrontation stays in profile composition, which owns applicability and
  override authority.
- Conflicting sides resolve by comparable evidence quality (evidence type,
  basis, fidelity, representation sufficiency, epistemic strength,
  attribution, recency) through dominance.  Nothing is averaged and votes
  are not counted; incomparable conflict returns the claim to unresolved
  and requests a clarification checkpoint.
- Confidence follows the representative support's quality.  Only genuinely
  independent, non-weak corroborating observations add a small bounded
  bonus, so repetition can never manufacture certainty on its own.
- Promotion to established taste demands attributable explicit support
  proportionate to the consequence of relying on the claim; strong
  inference may carry only reversible consequences.
- Later higher-quality evidence replaces established claims and records the
  displaced support as superseded; distinct later observations stay
  separate observations under their own identity.
- Replaying one identifiable operation is idempotent; reusing an identity
  for different content raises instead of silently diverging.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from math import isfinite
from types import MappingProxyType
from typing import Mapping, TypeAlias, TypeVar

from alignment_contract import (
    Disposition,
    EpistemicBasis,
    PreferenceKnowledge,
    Provenance,
    Scope,
    ValidationContext,
)
from identifiers import require_identifier as _require_identifier


class EvidenceType(str, Enum):
    EXPLICIT_FEEDBACK = "explicit_feedback"
    REFERENCE = "reference"
    APPROVED_ARTIFACT = "approved_artifact"
    OBSERVABLE_ACTION = "observable_action"
    PROTOTYPE_RESULT = "prototype_result"
    IMPLEMENTATION_RESULT = "implementation_result"
    SILENCE = "silence"
    CONTINUED_PROGRESS = "continued_progress"
    IMPLEMENTATION_SUCCESS = "implementation_success"
    DELEGATED_EXECUTION = "delegated_execution"


class FeedbackKind(str, Enum):
    NONE = "none"
    APPROVAL = "approval"
    PARTIAL_APPROVAL = "partial_approval"
    REJECTION = "rejection"
    CORRECTION = "correction"
    GOOD_ENOUGH = "good_enough"
    NONE_OF_THESE = "none_of_these"


class Judgment(str, Enum):
    UNSPECIFIED = "unspecified"
    ACCEPTABLE = "acceptable"
    PREFERRED = "preferred"
    REFERENCE_QUALITY = "reference_quality"


class RejectionTarget(str, Enum):
    NONE = "none"
    DIRECTION = "direction"
    EXECUTION_QUALITY = "execution_quality"


class Fidelity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Ambiguity(str, Enum):
    CLEAR = "clear"
    MINOR = "minor"
    MATERIAL = "material"


class SupportStrength(str, Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class Consequence(str, Enum):
    REVERSIBLE = "reversible"
    MATERIAL = "material"
    LOAD_BEARING = "load_bearing"


class SupportApplicability(str, Enum):
    APPLICABLE = "applicable"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"
    RESET_EXCLUDED = "reset_excluded"
    BRANCH_INAPPLICABLE = "branch_inapplicable"
    STALE = "stale"
    HISTORICAL_ONLY = "historical_only"


class ClaimStatus(str, Enum):
    HYPOTHESIS = "hypothesis"
    ESTABLISHED = "established"
    UNRESOLVED = "unresolved"
    STALE = "stale"
    HISTORICAL = "historical"


class TransitionStatus(str, Enum):
    APPLIED = "applied"
    REPLAYED = "replayed"
    DUPLICATE_EVENT = "duplicate_event"


_FIDELITY_RANK = {
    Fidelity.LOW: 1,
    Fidelity.MEDIUM: 2,
    Fidelity.HIGH: 3,
}

_STRENGTH_CONFIDENCE = {
    SupportStrength.WEAK: 0.3,
    SupportStrength.MODERATE: 0.65,
    SupportStrength.STRONG: 0.95,
}

_STRENGTH_RANK = {
    SupportStrength.WEAK: 0,
    SupportStrength.MODERATE: 1,
    SupportStrength.STRONG: 2,
}

_EVIDENCE_TYPE_RANK = {
    EvidenceType.EXPLICIT_FEEDBACK: 5,
    EvidenceType.APPROVED_ARTIFACT: 4,
    EvidenceType.REFERENCE: 3,
    EvidenceType.PROTOTYPE_RESULT: 2,
    EvidenceType.OBSERVABLE_ACTION: 1,
}

_CORROBORATION_BONUS = 0.05
_MAX_CORROBORATION_BONUS = 0.1
_MAX_CONFIDENCE = 0.95


_EnumValue = TypeVar("_EnumValue", bound=Enum)


def _coerce_enum(
    value: object,
    enum_type: type[_EnumValue],
    field_name: str,
) -> _EnumValue:
    try:
        return enum_type(value)
    except ValueError as error:
        raise ValueError(f"unsupported {field_name}: {value}") from error


@dataclass(frozen=True)
class PointClaim:
    """An exact direction claim for one subjective dimension."""

    dimension: str
    direction: str | None
    disposition: Disposition | str

    def __post_init__(self) -> None:
        _require_identifier(self.dimension, "claim dimension")
        disposition = _coerce_enum(
            self.disposition, Disposition, "claim disposition"
        )
        object.__setattr__(self, "disposition", disposition)
        if disposition in {Disposition.PREFERRED, Disposition.REJECTED}:
            if self.direction is None or not self.direction.strip():
                raise ValueError(
                    f"a {disposition.value} point claim requires a direction"
                )
        elif self.direction is not None:
            raise ValueError(
                f"an {disposition.value} point claim cannot assert a direction"
            )

    @property
    def dimensions(self) -> tuple[str, ...]:
        return (self.dimension,)


def _structured_disposition(
    value: Disposition | str, claim_kind: str
) -> Disposition:
    disposition = _coerce_enum(value, Disposition, "claim disposition")
    if disposition not in {Disposition.PREFERRED, Disposition.REJECTED}:
        raise ValueError(
            f"a {claim_kind} claim must be preferred or rejected"
        )
    return disposition


@dataclass(frozen=True)
class BundleClaim:
    """A comparison result whose dimensions were not isolated."""

    components: tuple[tuple[str, str], ...]
    disposition: Disposition | str

    def __post_init__(self) -> None:
        disposition = _structured_disposition(self.disposition, "bundle")
        object.__setattr__(self, "disposition", disposition)
        if len(self.components) < 2:
            raise ValueError("a bundle claim requires at least two dimensions")
        dimensions = tuple(dimension for dimension, _ in self.components)
        if any(not dimension or not direction for dimension, direction in self.components):
            raise ValueError("bundle components require dimensions and directions")
        if len(set(dimensions)) != len(dimensions):
            raise ValueError("bundle dimensions must be unique")

    @property
    def dimensions(self) -> tuple[str, ...]:
        return tuple(dimension for dimension, _ in self.components)


@dataclass(frozen=True)
class RangeClaim:
    """A supported numeric band without an invented exact optimum."""

    dimension: str
    lower: float
    upper: float
    disposition: Disposition | str

    def __post_init__(self) -> None:
        _require_identifier(self.dimension, "claim dimension")
        disposition = _structured_disposition(self.disposition, "range")
        object.__setattr__(self, "disposition", disposition)
        if not isfinite(self.lower) or not isfinite(self.upper):
            raise ValueError("range bounds must be finite")
        if self.lower > self.upper:
            raise ValueError("range lower bound must not exceed its upper bound")

    @property
    def dimensions(self) -> tuple[str, ...]:
        return (self.dimension,)


@dataclass(frozen=True)
class BoundaryClaim:
    """A supported ceiling or floor without an invented exact preference."""

    dimension: str
    operator: str
    threshold: float
    disposition: Disposition | str

    def __post_init__(self) -> None:
        _require_identifier(self.dimension, "claim dimension")
        disposition = _structured_disposition(self.disposition, "boundary")
        object.__setattr__(self, "disposition", disposition)
        if self.operator not in {"<", "<=", ">", ">="}:
            raise ValueError("boundary operator must be <, <=, >, or >=")
        if not isfinite(self.threshold):
            raise ValueError("boundary threshold must be finite")

    @property
    def dimensions(self) -> tuple[str, ...]:
        return (self.dimension,)


@dataclass(frozen=True)
class RelationshipClaim:
    """A conditional or relational preference that stays cross-dimensional."""

    dimensions: tuple[str, ...]
    relation: str
    disposition: Disposition | str

    def __post_init__(self) -> None:
        disposition = _structured_disposition(self.disposition, "relationship")
        object.__setattr__(self, "disposition", disposition)
        if len(self.dimensions) < 2:
            raise ValueError(
                "a relationship claim requires at least two dimensions"
            )
        if any(not dimension for dimension in self.dimensions):
            raise ValueError("relationship dimensions must be non-empty")
        if len(set(self.dimensions)) != len(self.dimensions):
            raise ValueError("relationship dimensions must be unique")
        _require_identifier(self.relation, "relationship")


EvidenceClaim: TypeAlias = (
    PointClaim | BundleClaim | RangeClaim | BoundaryClaim | RelationshipClaim
)


@dataclass(frozen=True)
class EvidenceImplication:
    """One independently applicable claim implication of an evidence event."""

    implication_id: str
    claim: EvidenceClaim
    basis: EpistemicBasis | str
    represented_dimensions: tuple[str, ...]
    fidelity: Fidelity | str
    required_fidelity: Fidelity | str
    ambiguity: Ambiguity | str
    epistemic_strength: SupportStrength | str
    preference_strength: float
    consequence: Consequence | str
    independence_key: str | None = None
    plausible_dimensions: tuple[str, ...] = ()
    representation_sufficient: bool = True
    applicability: SupportApplicability | str = SupportApplicability.APPLICABLE
    applicable_branches: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_identifier(self.implication_id, "implication_id")
        basis = _coerce_enum(self.basis, EpistemicBasis, "epistemic basis")
        fidelity = _coerce_enum(self.fidelity, Fidelity, "fidelity")
        required_fidelity = _coerce_enum(
            self.required_fidelity, Fidelity, "required fidelity"
        )
        ambiguity = _coerce_enum(self.ambiguity, Ambiguity, "ambiguity")
        epistemic_strength = _coerce_enum(
            self.epistemic_strength,
            SupportStrength,
            "epistemic strength",
        )
        consequence = _coerce_enum(
            self.consequence, Consequence, "consequence"
        )
        applicability = _coerce_enum(
            self.applicability,
            SupportApplicability,
            "support applicability",
        )
        object.__setattr__(self, "basis", basis)
        object.__setattr__(self, "fidelity", fidelity)
        object.__setattr__(self, "required_fidelity", required_fidelity)
        object.__setattr__(self, "ambiguity", ambiguity)
        object.__setattr__(self, "epistemic_strength", epistemic_strength)
        object.__setattr__(self, "consequence", consequence)
        object.__setattr__(self, "applicability", applicability)
        if not 0 <= self.preference_strength <= 1:
            raise ValueError("preference_strength must be between 0 and 1")
        if len(set(self.represented_dimensions)) != len(
            self.represented_dimensions
        ):
            raise ValueError("represented_dimensions must not contain duplicates")
        if len(set(self.applicable_branches)) != len(self.applicable_branches):
            raise ValueError("applicable_branches must not contain duplicates")
        if self.independence_key is not None:
            _require_identifier(self.independence_key, "independence_key")


@dataclass(frozen=True)
class EvidenceEvent:
    """Normalized evidence plus all claim implications it may support."""

    event_id: str
    evidence_type: EvidenceType | str
    scope: Scope
    context: tuple[tuple[str, str], ...]
    provenance: tuple[Provenance, ...]
    validation_context: ValidationContext
    occurred_at: int
    implications: tuple[EvidenceImplication, ...]
    feedback: FeedbackKind | str = FeedbackKind.NONE
    judgment: Judgment | str = Judgment.UNSPECIFIED
    rejection_target: RejectionTarget | str = RejectionTarget.NONE
    origin_branch: str | None = None

    def __post_init__(self) -> None:
        _require_identifier(self.event_id, "event_id")
        evidence_type = _coerce_enum(
            self.evidence_type, EvidenceType, "evidence type"
        )
        feedback = _coerce_enum(self.feedback, FeedbackKind, "feedback kind")
        judgment = _coerce_enum(self.judgment, Judgment, "judgment")
        rejection_target = _coerce_enum(
            self.rejection_target, RejectionTarget, "rejection target"
        )
        object.__setattr__(self, "evidence_type", evidence_type)
        object.__setattr__(self, "feedback", feedback)
        object.__setattr__(self, "judgment", judgment)
        object.__setattr__(self, "rejection_target", rejection_target)
        if self.occurred_at < 0:
            raise ValueError("occurred_at must be non-negative")
        context_keys = tuple(key for key, _ in self.context)
        if any(not key for key in context_keys):
            raise ValueError("context keys must be non-empty")
        if len(set(context_keys)) != len(context_keys):
            raise ValueError("context keys must be unique")
        implication_ids = tuple(
            implication.implication_id for implication in self.implications
        )
        if len(set(implication_ids)) != len(implication_ids):
            raise ValueError("implication_id must be unique within an event")
        if self.origin_branch is not None:
            _require_identifier(self.origin_branch, "origin_branch")


@dataclass(frozen=True)
class SupportRef:
    event_id: str
    implication_id: str

    @property
    def stable_id(self) -> str:
        return f"{self.event_id}#{self.implication_id}"


@dataclass(frozen=True)
class SupportAssessment:
    support: SupportRef
    usable: bool
    reason: str


@dataclass(frozen=True)
class ClarificationCheckpoint:
    support: SupportRef
    plausible_dimensions: tuple[str, ...]
    prompt: str


@dataclass(frozen=True)
class QualityEnvelope:
    representative_support: SupportRef
    confidence: float
    independence_key: str


@dataclass(frozen=True)
class ClaimResolution:
    claim_id: str
    status: ClaimStatus
    knowledge: PreferenceKnowledge
    governing_claim: EvidenceClaim | None
    support: tuple[SupportRef, ...]
    conflicts: tuple[SupportRef, ...]
    envelope: QualityEnvelope | None
    reason: str


@dataclass(frozen=True)
class AppliedOperation:
    operation_id: str
    fingerprint: str


@dataclass(frozen=True)
class SupportLifecycleRecord:
    operation_id: str
    support: SupportRef
    applicability: SupportApplicability
    reason: str
    provenance: tuple[Provenance, ...]


@dataclass(frozen=True)
class EvidenceState:
    events: tuple[EvidenceEvent, ...] = ()
    support_lifecycle: tuple[SupportLifecycleRecord, ...] = ()
    claims: tuple[ClaimResolution, ...] = ()
    applied_operations: tuple[AppliedOperation, ...] = ()


@dataclass(frozen=True)
class IngestEvidence:
    operation_id: str
    event: EvidenceEvent

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")


EvidenceOperation: TypeAlias = IngestEvidence


@dataclass(frozen=True)
class EvidenceTransition:
    state: EvidenceState
    status: TransitionStatus
    operation_id: str
    event_id: str | None
    assessments: tuple[SupportAssessment, ...]
    checkpoints: tuple[ClarificationCheckpoint, ...]
    changed_claim_ids: tuple[str, ...]


class EvidenceIdentityConflictError(ValueError):
    """A stable evidence identity was reused for different content."""


class OperationIdentityConflictError(ValueError):
    """A stable operation identity was reused for a different operation."""


def _fingerprint(operation: EvidenceOperation) -> str:
    return sha256(repr(operation).encode("utf-8")).hexdigest()


def _is_attributable(event: EvidenceEvent) -> bool:
    return any(
        provenance.actor.strip().lower() not in {"", "agent", "system", "unknown"}
        for provenance in event.provenance
    )


def _assess_support(
    event: EvidenceEvent, implication: EvidenceImplication
) -> SupportAssessment:
    support = SupportRef(event.event_id, implication.implication_id)
    non_evidence_reasons = {
        EvidenceType.SILENCE: "silence is not preference evidence",
        EvidenceType.CONTINUED_PROGRESS: (
            "continued progress is not preference evidence"
        ),
        EvidenceType.IMPLEMENTATION_SUCCESS: (
            "implementation success is not preference evidence"
        ),
        EvidenceType.DELEGATED_EXECUTION: (
            "delegated execution is authorized judgment, not preference evidence"
        ),
    }
    if event.evidence_type in non_evidence_reasons:
        return SupportAssessment(
            support,
            False,
            non_evidence_reasons[EvidenceType(event.evidence_type)],
        )
    if event.feedback is FeedbackKind.GOOD_ENOUGH:
        return SupportAssessment(
            support,
            False,
            "good-enough feedback does not assert preference",
        )
    if (
        event.feedback in {FeedbackKind.APPROVAL, FeedbackKind.PARTIAL_APPROVAL}
        and event.judgment
        in {Judgment.ACCEPTABLE, Judgment.UNSPECIFIED}
    ):
        return SupportAssessment(
            support,
            False,
            "acceptance does not assert preference",
        )
    if (
        event.feedback is FeedbackKind.REJECTION
        and event.rejection_target is RejectionTarget.EXECUTION_QUALITY
    ):
        return SupportAssessment(
            support,
            False,
            "execution-quality rejection does not reject the direction",
        )
    if implication.applicability is not SupportApplicability.APPLICABLE:
        return SupportAssessment(
            support,
            False,
            f"support is {SupportApplicability(implication.applicability).value}",
        )
    if not set(implication.claim.dimensions).issubset(
        implication.represented_dimensions
    ):
        return SupportAssessment(
            support,
            False,
            "claim dimensions were not all represented",
        )
    if not implication.representation_sufficient:
        return SupportAssessment(
            support,
            False,
            "representation was insufficient for the claim",
        )
    fidelity = Fidelity(implication.fidelity)
    required_fidelity = Fidelity(implication.required_fidelity)
    if _FIDELITY_RANK[fidelity] < _FIDELITY_RANK[required_fidelity]:
        return SupportAssessment(
            support,
            False,
            "representation fidelity was insufficient for the consequence",
        )
    if implication.ambiguity is Ambiguity.MATERIAL:
        return SupportAssessment(
            support,
            False,
            "subjective meaning remained materially ambiguous",
        )
    if not _is_attributable(event):
        return SupportAssessment(
            support,
            False,
            "evidence was not attributable to a represented person",
        )
    return SupportAssessment(support, True, "support is usable")


def _claim_group_key(
    event: EvidenceEvent, implication: EvidenceImplication
) -> tuple[object, ...]:
    claim = implication.claim
    shape: tuple[str, str | tuple[str, ...]]
    if isinstance(claim, PointClaim):
        shape = ("point", claim.dimension)
    elif isinstance(claim, BundleClaim):
        shape = ("bundle", tuple(sorted(claim.dimensions)))
    elif isinstance(claim, RangeClaim):
        shape = ("range", claim.dimension)
    elif isinstance(claim, BoundaryClaim):
        shape = ("boundary", claim.dimension)
    else:
        shape = ("relationship", tuple(sorted(claim.dimensions)))
    return (
        *shape,
        event.scope.kind,
        event.scope.identity,
        event.scope.represented_subject,
        tuple(sorted(event.context)),
        tuple(sorted(implication.applicable_branches)),
    )


def _claim_id(group_key: tuple[object, ...]) -> str:
    digest = sha256(repr(group_key).encode("utf-8")).hexdigest()[:16]
    return f"evidence-claim-{digest}"


def _number(value: float) -> str:
    return format(value, "g")


def _claim_knowledge_shape(
    claim: EvidenceClaim,
) -> tuple[str, str | None, Disposition, Mapping[str, str]]:
    disposition = Disposition(claim.disposition)
    if isinstance(claim, PointClaim):
        return claim.dimension, claim.direction, disposition, {}
    if isinstance(claim, BundleClaim):
        components = tuple(sorted(claim.components))
        component_text = ",".join(
            f"{dimension}={direction}" for dimension, direction in components
        )
        relationships = {"claim_kind": "bundle"}
        relationships.update(dict(components))
        return (
            f"bundle:{'+'.join(dimension for dimension, _ in components)}",
            f"bundle:{{{component_text}}}",
            disposition,
            relationships,
        )
    if isinstance(claim, RangeClaim):
        lower = _number(claim.lower)
        upper = _number(claim.upper)
        return (
            claim.dimension,
            f"range:[{lower},{upper}]",
            disposition,
            {"claim_kind": "range", "lower": lower, "upper": upper},
        )
    if isinstance(claim, BoundaryClaim):
        threshold = _number(claim.threshold)
        return (
            claim.dimension,
            f"boundary:{claim.operator}{threshold}",
            disposition,
            {
                "claim_kind": "boundary",
                "operator": claim.operator,
                "threshold": threshold,
            },
        )
    dimensions = tuple(sorted(claim.dimensions))
    return (
        f"relationship:{'+'.join(dimensions)}",
        claim.relation,
        disposition,
        {
            "claim_kind": "relationship",
            "dimensions": ",".join(dimensions),
        },
    )


def _knowledge_for(
    event: EvidenceEvent,
    implication: EvidenceImplication,
    support: tuple[SupportRef, ...],
    confidence: float,
) -> PreferenceKnowledge:
    dimension, direction, disposition, relationships = _claim_knowledge_shape(
        implication.claim
    )
    return PreferenceKnowledge(
        dimension=dimension,
        direction=direction,
        disposition=disposition,
        basis=implication.basis,
        confidence=confidence,
        strength=implication.preference_strength,
        scope=event.scope,
        context=MappingProxyType(dict(event.context)),
        evidence=tuple(item.stable_id for item in support),
        provenance=event.provenance,
        validation_context=event.validation_context,
        relationships=MappingProxyType(dict(relationships)),
    )


def _reconcile(
    events: tuple[EvidenceEvent, ...],
    operation_id: str,
    touched_event_id: str | None = None,
) -> tuple[
    tuple[ClaimResolution, ...],
    tuple[SupportAssessment, ...],
    tuple[ClarificationCheckpoint, ...],
    tuple[SupportLifecycleRecord, ...],
]:
    assessments: list[SupportAssessment] = []
    checkpoints: list[ClarificationCheckpoint] = []
    groups: dict[tuple[object, ...], list[_UsableSupport]] = {}
    for order, event in enumerate(events):
        for implication in event.implications:
            assessment = _assess_support(event, implication)
            assessments.append(assessment)
            if not assessment.usable:
                if implication.ambiguity is Ambiguity.MATERIAL:
                    plausible = (
                        implication.plausible_dimensions
                        or implication.claim.dimensions
                    )
                    if touched_event_id is None or (
                        event.event_id == touched_event_id
                    ):
                        checkpoints.append(
                            ClarificationCheckpoint(
                                support=assessment.support,
                                plausible_dimensions=plausible,
                                prompt=(
                                    "Clarify which represented dimension matters by "
                                    f"comparing: {', '.join(plausible)}"
                                ),
                            )
                        )
                continue
            entry = _UsableSupport(
                event=event,
                implication=implication,
                assessment=assessment,
                quality=_quality_vector(event, implication),
                order=order,
            )
            groups.setdefault(
                _claim_group_key(event, implication), []
            ).append(entry)

    resolutions: list[ClaimResolution] = []
    lifecycle: list[SupportLifecycleRecord] = []
    for members in groups.values():
        resolution, superseded, conflict_checkpoint = _resolve_claim_group(
            operation_id, members
        )
        resolutions.append(resolution)
        lifecycle.extend(superseded)
        touched_group = touched_event_id is None or any(
            member.event.event_id == touched_event_id for member in members
        )
        if conflict_checkpoint is not None and touched_group:
            checkpoints.append(conflict_checkpoint)
    return (
        tuple(resolutions),
        tuple(assessments),
        tuple(checkpoints),
        tuple(lifecycle),
    )


@dataclass(frozen=True)
class _UsableSupport:
    """One assessed-usable implication plus its comparable evidence quality."""

    event: EvidenceEvent
    implication: EvidenceImplication
    assessment: SupportAssessment
    quality: tuple[int, int, int, int, int, int, int]
    order: int


def _quality_vector(
    event: EvidenceEvent, implication: EvidenceImplication
) -> tuple[int, int, int, int, int, int, int]:
    """Rank evidence quality without collapsing it into a single score.

    Scope and context match are absent because a claim group already shares
    one scope, subject, context, and branch set; cross-scope confrontation
    belongs to profile composition.  The vector orders factors by relevance:
    evidence type, explicit versus inferred basis, artifact fidelity,
    representation sufficiency, epistemic strength, attribution to the
    represented person, and recency.
    """

    return (
        _EVIDENCE_TYPE_RANK[EvidenceType(event.evidence_type)],
        1 if implication.basis is EpistemicBasis.EXPLICIT else 0,
        _FIDELITY_RANK[Fidelity(implication.fidelity)],
        1 if implication.representation_sufficient else 0,
        _STRENGTH_RANK[SupportStrength(implication.epistemic_strength)],
        1
        if any(
            provenance.actor.strip().lower() == "user"
            for provenance in event.provenance
        )
        else 0,
        event.occurred_at,
    )


def _dominates(
    left: tuple[int, ...], right: tuple[int, ...]
) -> bool:
    return left != right and all(
        left_value >= right_value
        for left_value, right_value in zip(left, right)
    )


def _same_disposition_compatible(
    left: EvidenceClaim, right: EvidenceClaim
) -> bool:
    """Decide whether same-disposition claims can coexist as one side.

    Point, bundle, and relationship claims coexist only when they assert
    identical content.  Overlapping ranges and any boundary pair coexist;
    disjoint ranges oppose.  Nothing is averaged or merged into an invented
    direction.
    """

    # A claim group never mixes claim shapes, so every reachable pairing
    # matches on both sides; the final return only serves boundary pairs.
    if isinstance(left, PointClaim) and isinstance(right, PointClaim):
        return left.direction == right.direction
    if isinstance(left, BundleClaim) and isinstance(right, BundleClaim):
        return tuple(sorted(left.components)) == tuple(sorted(right.components))
    if isinstance(left, RelationshipClaim) and isinstance(
        right, RelationshipClaim
    ):
        return left.relation == right.relation
    if isinstance(left, RangeClaim) and isinstance(right, RangeClaim):
        return left.lower <= right.upper and right.lower <= left.upper
    return True


def _representative(entries: list[_UsableSupport]) -> _UsableSupport:
    return max(
        entries,
        key=lambda entry: (entry.quality, -entry.order),
    )


@dataclass(frozen=True)
class _ClaimSide:
    """Compatible camps of usable support acting as one resolution side."""

    entries: tuple[_UsableSupport, ...]

    @property
    def representative(self) -> _UsableSupport:
        return _representative(list(self.entries))

    def compatible_with(self, implication: EvidenceImplication) -> bool:
        representative_implication = self.representative.implication
        if _camps_oppose(representative_implication, implication):
            return False
        return all(
            _same_disposition_compatible(
                member.implication.claim, implication.claim
            )
            for member in self.entries
        )


def _camps_oppose(
    left: EvidenceImplication, right: EvidenceImplication
) -> bool:
    left_disposition = left.claim.disposition
    right_disposition = right.claim.disposition
    if Disposition.UNRESOLVED in (left_disposition, right_disposition):
        return False
    if left_disposition is not right_disposition:
        return True
    return not _same_disposition_compatible(left.claim, right.claim)


def _partition_sides(
    entries: list[_UsableSupport],
) -> list[_ClaimSide]:
    sides: list[_ClaimSide] = []
    for entry in entries:
        placed = False
        for index, side in enumerate(sides):
            if side.compatible_with(entry.implication):
                sides[index] = _ClaimSide(side.entries + (entry,))
                placed = True
                break
        if not placed:
            sides.append(_ClaimSide((entry,)))
    return sides


def _promotion_status(implication: EvidenceImplication) -> ClaimStatus:
    if implication.claim.disposition is Disposition.UNRESOLVED:
        return ClaimStatus.UNRESOLVED
    strong = implication.epistemic_strength is SupportStrength.STRONG
    if strong and implication.basis is EpistemicBasis.EXPLICIT:
        return ClaimStatus.ESTABLISHED
    if (
        strong
        and implication.basis is EpistemicBasis.INFERRED
        and implication.consequence is Consequence.REVERSIBLE
    ):
        # A strong inference may carry a reversible call on its own; material
        # or load-bearing consequences demand attributable explicit support.
        return ClaimStatus.ESTABLISHED
    return ClaimStatus.HYPOTHESIS


def _confidence_for_side(side: _ClaimSide) -> float:
    representative = side.representative
    base = _STRENGTH_CONFIDENCE[
        SupportStrength(representative.implication.epistemic_strength)
    ]
    corroborating_keys = {
        (
            member.implication.independence_key or member.event.event_id
        )
        for member in side.entries
        if member.implication.epistemic_strength is not SupportStrength.WEAK
    }
    extra_independent = max(len(corroborating_keys) - 1, 0)
    bonus = min(extra_independent * _CORROBORATION_BONUS, _MAX_CORROBORATION_BONUS)
    return min(base + bonus, _MAX_CONFIDENCE)


def _resolve_claim_group(
    operation_id: str,
    entries: list[_UsableSupport],
) -> tuple[
    ClaimResolution,
    tuple[SupportLifecycleRecord, ...],
    ClarificationCheckpoint | None,
]:
    sides = _partition_sides(entries)
    governing: _ClaimSide | None = None
    if len(sides) == 1:
        governing = sides[0]
    else:
        representatives = [side.representative for side in sides]
        for candidate_index, candidate in enumerate(sides):
            candidate_quality = representatives[candidate_index].quality
            if all(
                _dominates(candidate_quality, other.quality)
                for index, other in enumerate(representatives)
                if index != candidate_index
            ):
                governing = candidate
                break

    if governing is None:
        return _unresolved_conflict_resolution(sides)

    representative = governing.representative
    confidence = _confidence_for_side(governing)
    status = _promotion_status(representative.implication)
    support_ids = tuple(
        member.assessment.support for member in governing.entries
    )
    independence_key = (
        representative.implication.independence_key
        or representative.event.event_id
    )
    if len(sides) == 1:
        reason = (
            "one compatible body of evidence governs; confidence reflects "
            "evidence quality with only genuinely independent corroboration"
        )
        superseded: tuple[SupportLifecycleRecord, ...] = ()
    else:
        reason = (
            "higher-quality evidence supersedes opposing supports instead of "
            "averaging or counting votes"
        )
        losing = tuple(
            member
            for side in sides
            if side is not governing
            for member in side.entries
        )
        superseded = tuple(
            SupportLifecycleRecord(
                operation_id=operation_id,
                support=member.assessment.support,
                applicability=SupportApplicability.SUPERSEDED,
                reason=(
                    "superseded by higher-quality opposing evidence "
                    f"({representative.assessment.support.stable_id})"
                ),
                provenance=member.event.provenance,
            )
            for member in losing
        )
    resolution = ClaimResolution(
        claim_id=_claim_id(
            _claim_group_key(representative.event, representative.implication)
        ),
        status=status,
        knowledge=_knowledge_for(
            representative.event,
            representative.implication,
            support_ids,
            confidence,
        ),
        governing_claim=representative.implication.claim,
        support=support_ids,
        conflicts=(),
        envelope=QualityEnvelope(
            representative_support=representative.assessment.support,
            confidence=confidence,
            independence_key=independence_key,
        ),
        reason=reason,
    )
    return resolution, superseded, None


def _unresolved_conflict_resolution(
    sides: list[_ClaimSide],
) -> tuple[ClaimResolution, tuple[SupportLifecycleRecord, ...], ClarificationCheckpoint | None]:
    ordered_entries = [
        member for side in sides for member in side.entries
    ]
    primary = sides[0].representative
    dimension, _, _, _ = _claim_knowledge_shape(primary.implication.claim)
    lowest_confidence = min(
        _STRENGTH_CONFIDENCE[
            SupportStrength(side.representative.implication.epistemic_strength)
        ]
        for side in sides
    )
    conflicting_refs = tuple(
        side.representative.assessment.support for side in sides
    )
    knowledge = PreferenceKnowledge(
        dimension=dimension,
        direction=None,
        disposition=Disposition.UNRESOLVED,
        basis=EpistemicBasis.INFERRED,
        confidence=lowest_confidence,
        strength=primary.implication.preference_strength,
        scope=primary.event.scope,
        context=MappingProxyType(dict(primary.event.context)),
        evidence=tuple(member.assessment.support.stable_id for member in ordered_entries),
        provenance=primary.event.provenance,
        validation_context=primary.event.validation_context,
        relationships=MappingProxyType({}),
    )
    dimensions = tuple(
        sorted(
            {
                dimension_name
                for member in ordered_entries
                for dimension_name in member.implication.claim.dimensions
            }
        )
    )
    checkpoint = ClarificationCheckpoint(
        support=primary.assessment.support,
        plausible_dimensions=dimensions,
        prompt=(
            "Resolve materially conflicting evidence of incomparable quality "
            f"for: {', '.join(dimensions)} before treating this as taste"
        ),
    )
    resolution = ClaimResolution(
        claim_id=_claim_id(_claim_group_key(primary.event, primary.implication)),
        status=ClaimStatus.UNRESOLVED,
        knowledge=knowledge,
        governing_claim=None,
        support=tuple(member.assessment.support for member in ordered_entries),
        conflicts=conflicting_refs,
        envelope=None,
        reason=(
            "materially conflicting evidence of incomparable quality left the "
            "claim unresolved rather than averaged"
        ),
    )
    return resolution, (), checkpoint


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


def apply_evidence_operation(
    state: EvidenceState, operation: EvidenceOperation
) -> EvidenceTransition:
    """Apply one immutable, retry-safe evidence operation."""

    fingerprint = _fingerprint(operation)
    for applied in state.applied_operations:
        if applied.operation_id != operation.operation_id:
            continue
        if applied.fingerprint != fingerprint:
            raise OperationIdentityConflictError(
                f"operation_id {operation.operation_id!r} was reused"
            )
        return EvidenceTransition(
            state=state,
            status=TransitionStatus.REPLAYED,
            operation_id=operation.operation_id,
            event_id=operation.event.event_id,
            assessments=(),
            checkpoints=(),
            changed_claim_ids=(),
        )

    for existing in state.events:
        if existing.event_id != operation.event.event_id:
            continue
        if existing != operation.event:
            raise EvidenceIdentityConflictError(
                f"event_id {operation.event.event_id!r} was reused"
            )
        new_state = EvidenceState(
            events=state.events,
            support_lifecycle=state.support_lifecycle,
            claims=state.claims,
            applied_operations=state.applied_operations
            + (AppliedOperation(operation.operation_id, fingerprint),),
        )
        return EvidenceTransition(
            state=new_state,
            status=TransitionStatus.DUPLICATE_EVENT,
            operation_id=operation.operation_id,
            event_id=operation.event.event_id,
            assessments=(),
            checkpoints=(),
            changed_claim_ids=(),
        )

    events = state.events + (operation.event,)
    (
        claims,
        all_assessments,
        scoped_checkpoints,
        support_lifecycle,
    ) = _reconcile(events, operation.operation_id, operation.event.event_id)
    # When later material evidence strips established knowledge of its
    # established status, the previously governing support is marked stale
    # rather than silently discarded.
    previous_by_id = {claim.claim_id: claim for claim in state.claims}
    stale_records = []
    for claim in claims:
        previous = previous_by_id.get(claim.claim_id)
        if (
            previous is not None
            and previous.status is ClaimStatus.ESTABLISHED
            and claim.status is not ClaimStatus.ESTABLISHED
            and previous.envelope is not None
        ):
            stale_records.append(
                SupportLifecycleRecord(
                    operation_id=operation.operation_id,
                    support=previous.envelope.representative_support,
                    applicability=SupportApplicability.STALE,
                    reason=(
                        "later material evidence demoted this established "
                        f"claim to {claim.status.value}"
                    ),
                    provenance=previous.knowledge.provenance,
                )
            )
    support_lifecycle = support_lifecycle + tuple(stale_records)
    event_assessments = tuple(
        item
        for item in all_assessments
        if item.support.event_id == operation.event.event_id
    )
    new_state = EvidenceState(
        events=events,
        support_lifecycle=support_lifecycle,
        claims=claims,
        applied_operations=state.applied_operations
        + (AppliedOperation(operation.operation_id, fingerprint),),
    )
    return EvidenceTransition(
        state=new_state,
        status=TransitionStatus.APPLIED,
        operation_id=operation.operation_id,
        event_id=operation.event.event_id,
        assessments=event_assessments,
            checkpoints=scoped_checkpoints,
        changed_claim_ids=_changed_claim_ids(state.claims, claims),
    )
