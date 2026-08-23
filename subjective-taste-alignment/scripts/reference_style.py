"""Reference-derived style profiles routed through the common contract.

Mimicry and consistency requests never build a parallel preference system.
This module derives exactly the reference properties needed for the
requested work, records whether each was explicitly requested or merely
inferred as similarity, binds every property to its source-level
provenance, and hands the result to the canonical active-alignment
contract as *intent* — never as reusable user taste.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import Enum

from alignment_contract import (
    DecisionDirective,
    Provenance,
    Scope,
)
from evidence_reconciliation import Fidelity
from identifiers import require_identifier as _require_identifier
from profile_persistence import (
    ReferenceFreshness,
    ReferenceMode,
    ReferenceSource,
)


class ReferenceRequestKind(str, Enum):
    """The explicit requests that route into reference-derived handling."""

    MIMIC = "mimic"
    MATCH = "match"
    FOLLOW = "follow"
    CONTINUE = "continue"
    REMAIN_CONSISTENT = "remain_consistent"


class ReferenceOrigin(str, Enum):
    USER_SELECTED = "user_selected"
    PROJECT_CONSISTENCY = "project_consistency"


class PropertyStatus(str, Enum):
    EXPLICIT_REQUEST = "explicit_request"
    INFERRED_SIMILARITY = "inferred_similarity"


_FIDELITY_RANK = {
    Fidelity.LOW: 1,
    Fidelity.MEDIUM: 2,
    Fidelity.HIGH: 3,
}


@dataclass(frozen=True)
class ReferenceInstruction:
    """A parsed mimicry or consistency request."""

    instruction_id: str
    kind: ReferenceRequestKind | str
    scope: Scope
    target_dimensions: tuple[str, ...] = ()
    origin: ReferenceOrigin | str = ReferenceOrigin.USER_SELECTED

    def __post_init__(self) -> None:
        if not self.instruction_id or self.instruction_id.isspace():
            raise ValueError("an instruction_id is required")
        try:
            kind = ReferenceRequestKind(self.kind)
            origin = ReferenceOrigin(self.origin)
        except ValueError as error:
            raise ValueError(
                f"the request does not route through reference-derived "
                f"handling: {error}"
            ) from error
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "origin", origin)
        dimensions = self.target_dimensions
        if len(set(dimensions)) != len(dimensions):
            raise ValueError("target_dimensions must not contain duplicates")
        if any(not dimension for dimension in dimensions):
            raise ValueError("target_dimensions must be non-empty")


@dataclass(frozen=True)
class ObservedReferenceProperty:
    """One subjective property the reference actually exposes."""

    dimension: str
    direction: str
    fidelity: Fidelity | str

    def __post_init__(self) -> None:
        if not self.dimension or self.dimension.isspace():
            raise ValueError("an observed dimension is required")
        if not self.direction or self.direction.isspace():
            raise ValueError("an observed direction is required")
        object.__setattr__(self, "fidelity", Fidelity(self.fidelity))


@dataclass(frozen=True)
class DerivedReferenceProperty:
    """One derivation outcome with explicit-versus-inferred status."""

    dimension: str
    direction: str
    status: PropertyStatus
    included: bool
    reason: str


@dataclass(frozen=True)
class ReferenceDerivation:
    """What the reference contributes to the common alignment system."""

    intent_directives: tuple[DecisionDirective, ...]
    included: tuple[DerivedReferenceProperty, ...]
    excluded: tuple[DerivedReferenceProperty, ...]
    direction_selection_required: bool
    binding: ReferenceSource
    scope: Scope | None = None


def validate_against_reference(
    observation: ObservedReferenceProperty,
    reference: ReferenceSource,
) -> None:
    """Reject observations that cannot be grounded in a usable reference.

    A property can only be derived from a reference whose identity and
    locator are retained and whose freshness still supports reproduction.
    Stale or unidentifiable sources must not silently seed intent.
    """
    if not reference.reference_id or reference.reference_id.isspace():
        raise ValueError(
            "the observed property cannot be grounded: the reference has no id"
        )
    if not reference.source_identity or reference.source_identity.isspace():
        raise ValueError(
            f"the observed property {observation.dimension!r} cannot be "
            "grounded: the reference retains no source identity"
        )
    if not reference.locator or reference.locator.isspace():
        raise ValueError(
            f"the observed property {observation.dimension!r} cannot be "
            "grounded: the reference retains no source locator"
        )
    freshness = ReferenceFreshness(reference.freshness)
    if freshness is not ReferenceFreshness.CURRENT:
        raise ValueError(
            f"the observed property {observation.dimension!r} comes from a "
            f"{freshness.value} reference; refresh the reference before "
            "reproducing properties from it"
        )


@dataclass(frozen=True)
class ReferenceCheck:
    """Outcome of comparing a reference binding to an observed source state.

    ``source_changed`` is ``None`` when the host could not observe whether
    the source moved; freshness then becomes explicitly unknown and every
    derived claim is constrained until revalidation.
    """

    reference_id: str
    mode: ReferenceMode
    previous_freshness: ReferenceFreshness
    resulting_freshness: ReferenceFreshness
    source_changed: bool | None
    verifiable: bool
    reason: str
    stale_claim_ids: tuple[str, ...]
    binding: ReferenceSource


def _check_source_state(
    reference: ReferenceSource,
    observed_revision: str | None,
    expected_mode: ReferenceMode,
    role: str,
) -> str | None:
    mode = ReferenceMode(reference.mode)
    if mode is not expected_mode:
        raise ValueError(
            f"{role} requires a {expected_mode.value} reference; "
            f"{reference.reference_id} is {mode.value}"
        )
    if observed_revision is not None and not observed_revision.strip():
        observed_revision = None
    return observed_revision


def _reference_check(
    reference: ReferenceSource,
    *,
    mode: ReferenceMode,
    previous_freshness: ReferenceFreshness,
    resulting_freshness: ReferenceFreshness,
    source_changed: bool | None,
    verifiable: bool,
    reason: str,
) -> ReferenceCheck:
    """Build one check outcome, staling derived claims unless nothing moved."""
    if source_changed is False:
        stale_claim_ids: tuple[str, ...] = ()
    else:
        stale_claim_ids = tuple(reference.derived_claim_ids)
    return ReferenceCheck(
        reference_id=reference.reference_id,
        mode=mode,
        previous_freshness=previous_freshness,
        resulting_freshness=resulting_freshness,
        source_changed=source_changed,
        verifiable=verifiable,
        reason=reason,
        stale_claim_ids=stale_claim_ids,
        binding=replace(reference, freshness=resulting_freshness),
    )


def verify_pinned_state(
    reference: ReferenceSource,
    *,
    observed_revision: str | None = None,
) -> ReferenceCheck:
    """Compare a pinned reference against its fixed source state.

    The pin never moves: the returned binding keeps the identity and
    revision that derivation actually used. When the locator now serves
    different content, or the pinned state cannot be verified at all,
    freshness becomes explicitly unknown and derived claims are staled
    until the original source is re-supplied or revalidated.
    """
    revision = _check_source_state(
        reference, observed_revision, ReferenceMode.PINNED, "pin verification"
    )
    previous = ReferenceFreshness(reference.freshness)
    if revision is None:
        return _reference_check(
            reference,
            mode=ReferenceMode.PINNED,
            previous_freshness=previous,
            resulting_freshness=ReferenceFreshness.UNKNOWN,
            source_changed=None,
            verifiable=False,
            reason=(
                "the pinned source state cannot be recovered or verified; "
                "freshness is unknown until the original source is revalidated"
            ),
        )
    if revision == reference.source_revision:
        return _reference_check(
            reference,
            mode=ReferenceMode.PINNED,
            previous_freshness=previous,
            resulting_freshness=previous,
            source_changed=False,
            verifiable=True,
            reason="the pinned source state still matches the bound revision",
        )
    return _reference_check(
        reference,
        mode=ReferenceMode.PINNED,
        previous_freshness=previous,
        resulting_freshness=ReferenceFreshness.UNKNOWN,
        source_changed=True,
        verifiable=True,
        reason=(
            f"the locator now serves different content ({revision}); the pin "
            f"remains bound to {reference.source_identity} at "
            f"{reference.source_revision}"
        ),
    )


def observe_live_state(
    reference: ReferenceSource,
    *,
    observed_revision: str | None = None,
) -> ReferenceCheck:
    """Compare a live reference against its most recently derived state.

    A live reference tracks its evolving source. A reliable revision
    signal detects change (freshness becomes stale) or confirms no change;
    without one, freshness stays explicitly unknown and material
    fidelity-dependent reuse requires revalidation first.
    """
    revision = _check_source_state(
        reference, observed_revision, ReferenceMode.LIVE, "live observation"
    )
    previous = ReferenceFreshness(reference.freshness)
    if revision is None:
        return _reference_check(
            reference,
            mode=ReferenceMode.LIVE,
            previous_freshness=previous,
            resulting_freshness=ReferenceFreshness.UNKNOWN,
            source_changed=None,
            verifiable=False,
            reason=(
                "the live locator exposes no reliable revision signal; "
                "revalidation is required before material reuse"
            ),
        )
    if revision == reference.source_revision:
        return _reference_check(
            reference,
            mode=ReferenceMode.LIVE,
            previous_freshness=previous,
            resulting_freshness=previous,
            source_changed=False,
            verifiable=True,
            reason="the live source still matches the last derived revision",
        )
    return _reference_check(
        reference,
        mode=ReferenceMode.LIVE,
        previous_freshness=previous,
        resulting_freshness=ReferenceFreshness.STALE,
        source_changed=True,
        verifiable=True,
        reason=(
            f"the live source moved from {reference.source_revision} to "
            f"{revision}; derived knowledge may be stale"
        ),
    )


def reference_dependency(reference_id: str) -> str:
    """The canonical dependency token linking derived work to a reference."""
    _require_identifier(reference_id, "reference_id")
    return f"reference:{reference_id}"


def decisions_depending_on(
    dependencies_by_decision: Mapping[str, Iterable[str]],
    reference_id: str,
) -> tuple[str, ...]:
    """Return only the decisions whose dependencies include the reference."""
    token = reference_dependency(reference_id)
    return tuple(
        decision_id
        for decision_id, dependencies in dependencies_by_decision.items()
        if token in set(dependencies)
    )


_REQUEST_KEYWORDS: tuple[tuple[ReferenceRequestKind, tuple[str, ...]], ...] = (
    (ReferenceRequestKind.REMAIN_CONSISTENT, ("consistent", "consistency")),
    (ReferenceRequestKind.MIMIC, ("mimic",)),
    (ReferenceRequestKind.MATCH, ("match",)),
    (ReferenceRequestKind.FOLLOW, ("follow",)),
    (ReferenceRequestKind.CONTINUE, ("continue",)),
)


def classify_reference_request(text: str) -> ReferenceRequestKind:
    """Map request wording onto the routing vocabulary."""
    _require_identifier(text, "request text")
    normalized = text.strip().lower()
    for kind, keywords in _REQUEST_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return kind
    raise ValueError(
        f"the request {text!r} is not a reference-derived style request"
    )


def derive_reference_style(
    instruction: ReferenceInstruction,
    reference: ReferenceSource,
    observed_properties: tuple[ObservedReferenceProperty, ...],
    *,
    project_style_candidates: tuple[str, ...] = (),
    minimum_fidelity: Fidelity | str = Fidelity.MEDIUM,
) -> ReferenceDerivation:
    """Derive only the properties the requested work can honestly use."""

    minimum = Fidelity(minimum_fidelity)
    threshold = _FIDELITY_RANK[minimum]
    origin = ReferenceOrigin(instruction.origin)

    direction_selection_required = (
        origin is ReferenceOrigin.PROJECT_CONSISTENCY
        and len(project_style_candidates) > 1
    )

    included: list[DerivedReferenceProperty] = []
    excluded: list[DerivedReferenceProperty] = []
    seen: set[str] = set()
    directives: list[DecisionDirective] = []
    for observation in observed_properties:
        if observation.dimension in seen:
            raise ValueError(
                f"observed dimension {observation.dimension!r} was duplicated"
            )
        seen.add(observation.dimension)
        explicit = observation.dimension in instruction.target_dimensions
        whole_style_request = not instruction.target_dimensions
        status = (
            PropertyStatus.EXPLICIT_REQUEST
            if explicit
            else PropertyStatus.INFERRED_SIMILARITY
        )
        if _FIDELITY_RANK[Fidelity(observation.fidelity)] < threshold:
            excluded.append(
                DerivedReferenceProperty(
                    dimension=observation.dimension,
                    direction=observation.direction,
                    status=status,
                    included=False,
                    reason=(
                        "the reference does not represent this property "
                        "strongly enough to reproduce"
                    ),
                )
            )
            continue
        if not explicit and not whole_style_request:
            excluded.append(
                DerivedReferenceProperty(
                    dimension=observation.dimension,
                    direction=observation.direction,
                    status=status,
                    included=False,
                    reason=(
                        "the request scoped the reference to specific "
                        "dimensions; this unrequested property must not "
                        "imply preference"
                    ),
                )
            )
            continue
        if (
            origin is ReferenceOrigin.PROJECT_CONSISTENCY
            and direction_selection_required
        ):
            excluded.append(
                DerivedReferenceProperty(
                    dimension=observation.dimension,
                    direction=observation.direction,
                    status=status,
                    included=False,
                    reason=(
                        "which existing project style to follow remains "
                        "unresolved; select a representative reference first"
                    ),
                )
            )
            continue
        included.append(
            DerivedReferenceProperty(
                dimension=observation.dimension,
                direction=observation.direction,
                status=status,
                included=True,
                reason=(
                    "explicitly requested by the user"
                    if explicit
                    else "inferred as part of the reference's style"
                ),
            )
        )
        observed_state = (
            f"@{reference.source_revision}"
            if reference.source_revision
            else "@unrevised-source"
        )
        directives.append(
            DecisionDirective(
                dimension=observation.dimension,
                direction=observation.direction,
                reason=(
                    f"reference-derived intent from {reference.reference_id} "
                    f"({status.value}); not user-taste evidence"
                ),
                provenance=(
                    Provenance(
                        actor="user",
                        source_id=(
                            f"{instruction.instruction_id}:"
                            f"{reference.reference_id}{observed_state}"
                            f"#dimension:{observation.dimension}"
                        ),
                    ),
                ),
                dependencies=(reference_dependency(reference.reference_id),),
                scope=instruction.scope,
            )
        )

    binding = ReferenceSource(
        reference_id=reference.reference_id,
        source_identity=reference.source_identity,
        locator=reference.locator,
        mode=reference.mode,
        freshness=reference.freshness,
        source_revision=reference.source_revision,
        derived_claim_ids=tuple(
            f"reference-intent:{item.dimension}" for item in included
        ),
        provenance=(
            *reference.provenance,
            Provenance(
                actor="user",
                source_id=instruction.instruction_id,
            ),
        ),
    )

    return ReferenceDerivation(
        intent_directives=tuple(directives),
        included=tuple(included),
        excluded=tuple(excluded),
        direction_selection_required=direction_selection_required,
        binding=binding,
        scope=instruction.scope,
    )


__all__ = [
    "DerivedReferenceProperty",
    "ObservedReferenceProperty",
    "PropertyStatus",
    "ReferenceCheck",
    "ReferenceDerivation",
    "ReferenceInstruction",
    "ReferenceOrigin",
    "ReferenceRequestKind",
    "classify_reference_request",
    "decisions_depending_on",
    "derive_reference_style",
    "observe_live_state",
    "reference_dependency",
    "validate_against_reference",
    "verify_pinned_state",
]
