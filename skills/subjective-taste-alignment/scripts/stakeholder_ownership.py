"""Stakeholder ownership resolution routed through the common contract.

Spec Phase 10 obligations:

- Audience needs, brand requirements, client direction, designer
  direction, team decisions, and imported stakeholder preferences stay
  separate from user taste.  They enter alignment only as *ownership*
  directives whose scope records whose preferences they represent,
  never as user-taste evidence.
- There is no universal stakeholder precedence chain.  Which subjective
  signal governs a dimension follows exclusively from explicit ownership
  grants (project agreements, delegations, or explicitly retained
  authority).  Identical roles resolve differently under different
  agreements.
- Hard constraints bound the feasible space before ownership resolves
  competing directions inside it; that ordering is enforced by the core
  SOURCE_PRECEDENCE, not here.
- A stakeholder signal from a subject with no ownership over a dimension
  is recorded as excluded and cannot override the applicable owner.
- Materially ambiguous ownership stays unresolved and emits an explicit
  checkpoint so load-bearing propagation is blocked by the canonical
  active-alignment guard.

This module makes no semantic decision of its own: it classifies inputs
and hands canonical ``DecisionDirective`` objects to
:func:`alignment_contract.resolve_alignment`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from alignment_contract import (
    DecisionDirective,
    PropagationPolicyDecision,
    Provenance,
    Scope,
)
from identifiers import require_identifier as _require_identifier


class StakeholderRole(str, Enum):
    """The independent stakeholder families the spec names."""

    AUDIENCE = "audience"
    BRAND = "brand"
    CLIENT = "client"
    DESIGNER = "designer"
    TEAM = "team"
    IMPORTED = "imported"


class GrantBasis(str, Enum):
    """Why a subject owns a dimension; there is no default chain."""

    PROJECT_AGREEMENT = "project_agreement"
    DELEGATION = "delegation"
    RETAINED_AUTHORITY = "retained_authority"


@dataclass(frozen=True)
class StakeholderSignal:
    """One stakeholder's expressed direction for one dimension."""

    signal_id: str
    role: StakeholderRole | str
    stakeholder: str
    dimension: str
    direction: str
    note: str

    def __post_init__(self) -> None:
        _require_identifier(self.signal_id, "signal_id")
        try:
            role = StakeholderRole(self.role)
        except ValueError as error:
            raise ValueError(
                f"unsupported stakeholder role: {self.role}"
            ) from error
        object.__setattr__(self, "role", role)
        _require_identifier(self.stakeholder, "stakeholder")
        _require_identifier(self.dimension, "dimension")
        if not self.direction or self.direction.isspace():
            raise ValueError("a stakeholder signal requires a direction")
        if not self.note or self.note.isspace():
            raise ValueError("a stakeholder signal records its origin note")


@dataclass(frozen=True)
class OwnershipGrant:
    """Explicit evidence that one subject owns a set of dimensions."""

    grant_id: str
    owner_subject: str
    dimensions: tuple[str, ...]
    basis: GrantBasis | str
    provenance: tuple[Provenance, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.grant_id, "grant_id")
        _require_identifier(self.owner_subject, "owner_subject")
        if not self.dimensions or any(
            not dimension or not dimension.strip()
            for dimension in self.dimensions
        ):
            raise ValueError("an ownership grant names its dimensions")
        if len(set(self.dimensions)) != len(self.dimensions):
            raise ValueError("ownership grant dimensions must be unique")
        try:
            basis = GrantBasis(self.basis)
        except ValueError as error:
            raise ValueError(
                f"unsupported ownership basis: {self.basis}"
            ) from error
        object.__setattr__(self, "basis", basis)
        if not self.provenance:
            raise ValueError("an ownership grant requires provenance")


@dataclass(frozen=True)
class ExcludedSignal:
    """A stakeholder signal that may not govern this decision, and why."""

    signal: StakeholderSignal
    reason: str


@dataclass(frozen=True)
class DimensionOwnership:
    """The ownership outcome for one requested dimension."""

    dimension: str
    owner_subject: str | None
    ambiguous: bool
    reason: str


@dataclass(frozen=True)
class StakeholderResolution:
    """Ownership classification feeding the canonical alignment contract."""

    ownership: tuple[DimensionOwnership, ...]
    ownership_directives: tuple[DecisionDirective, ...]
    excluded_signals: tuple[ExcludedSignal, ...]
    ambiguous_dimensions: tuple[str, ...]
    checkpoints: tuple[str, ...]


def resolve_stakeholder_ownership(
    dimensions: tuple[str, ...],
    *,
    grants: tuple[OwnershipGrant, ...],
    signals: tuple[StakeholderSignal, ...],
    default_owner: str,
) -> StakeholderResolution:
    """Classify each dimension's owner and build canonical directives.

    The default owner is the active represented subject supplied by the
    caller; it applies only where no explicit grant exists. Retained
    authority is the absence of a contrary agreement, never a rank in a
    stakeholder precedence chain.
    """
    _require_identifier(default_owner, "default_owner")
    grants_by_dimension: dict[str, list[OwnershipGrant]] = {}
    for grant in grants:
        for dimension in grant.dimensions:
            grants_by_dimension.setdefault(dimension, []).append(grant)

    ownership_results: list[DimensionOwnership] = []
    directives: list[DecisionDirective] = []
    ambiguous: list[str] = []
    checkpoints: list[str] = []
    consumed_signal_ids: set[str] = set()

    for dimension in dimensions:
        applicable = grants_by_dimension.get(dimension, [])
        owners = sorted({grant.owner_subject for grant in applicable})
        if len(owners) > 1:
            ownership_results.append(
                DimensionOwnership(
                    dimension=dimension,
                    owner_subject=None,
                    ambiguous=True,
                    reason=(
                        "materially ambiguous ownership: "
                        + ", ".join(owners)
                        + " hold competing grants"
                    ),
                )
            )
            ambiguous.append(dimension)
            checkpoints.append(f"resolve-ownership:{dimension}")
            continue
        if not applicable:
            ownership_results.append(
                DimensionOwnership(
                    dimension=dimension,
                    owner_subject=default_owner,
                    ambiguous=False,
                    reason="no explicit grant exists; authority is retained",
                )
            )
            continue

        grant = applicable[0]
        owner = grant.owner_subject
        owner_signals = [
            signal
            for signal in signals
            if signal.dimension == dimension and signal.stakeholder == owner
        ]
        if not owner_signals:
            ownership_results.append(
                DimensionOwnership(
                    dimension=dimension,
                    owner_subject=owner,
                    ambiguous=True,
                    reason=(
                        f"{owner} owns this dimension per "
                        f"{grant.grant_id} but has given no direction"
                    ),
                )
            )
            ambiguous.append(dimension)
            checkpoints.append(f"resolve-ownership:{dimension}")
            continue
        signal = owner_signals[0]
        consumed_signal_ids.add(signal.signal_id)
        ownership_results.append(
            DimensionOwnership(
                dimension=dimension,
                owner_subject=owner,
                ambiguous=False,
                reason=(
                    f"{owner} owns this dimension per {grant.grant_id} "
                    f"({GrantBasis(grant.basis).value})"
                ),
            )
        )
        directives.append(
            DecisionDirective(
                dimension=dimension,
                direction=signal.direction,
                reason=(
                    f"{signal.stakeholder} owns {dimension} per "
                    f"{grant.grant_id}; represents their direction, "
                    "not user taste"
                ),
                provenance=(
                    Provenance(
                        actor=f"signal:{signal.signal_id}",
                        source_id=f"grant:{grant.grant_id}",
                    ),
                    *grant.provenance,
                ),
                dependencies=(f"ownership:{grant.grant_id}",),
                scope=Scope(
                    kind="ownership",
                    identity=grant.grant_id,
                    represented_subject=signal.stakeholder,
                ),
            )
        )

    excluded = _exclude_ungoverned_signals(
        signals, consumed_signal_ids, ownership_results
    )
    return StakeholderResolution(
        ownership=tuple(ownership_results),
        ownership_directives=tuple(directives),
        excluded_signals=excluded,
        ambiguous_dimensions=tuple(ambiguous),
        checkpoints=tuple(checkpoints),
    )


def propagation_hold(
    resolution: StakeholderResolution,
    *,
    revision: str,
) -> PropagationPolicyDecision | None:
    """A canonical propagation hold while ownership stays unresolved.

    ``None`` means ownership raised no obligations and the caller may use
    its own propagation policy.  Otherwise the hold is ineligible until
    the ownership checkpoints are resolved, so load-bearing work cannot
    proceed on a guessed owner.
    """
    _require_identifier(revision, "revision")
    if not resolution.checkpoints:
        return None
    return PropagationPolicyDecision(
        revision=revision,
        eligible=False,
        route=None,
        checkpoint_obligations=resolution.checkpoints,
        reason="stakeholder ownership is unresolved for load-bearing dimensions",
    )


def _exclude_ungoverned_signals(
    signals: tuple[StakeholderSignal, ...],
    consumed_signal_ids: set[str],
    ownership_results: list[DimensionOwnership],
) -> tuple[ExcludedSignal, ...]:
    """Record every non-governing signal with the reason it cannot govern."""
    excluded: list[ExcludedSignal] = []
    governed = {
        result.dimension
        for result in ownership_results
        if result.owner_subject is not None and not result.ambiguous
    }
    for signal in signals:
        if signal.signal_id in consumed_signal_ids:
            continue
        result_for_dimension = next(
            (
                result
                for result in ownership_results
                if result.dimension == signal.dimension
            ),
            None,
        )
        owner = (
            result_for_dimension.owner_subject
            if result_for_dimension is not None
            else None
        )
        if signal.dimension not in governed:
            excluded.append(
                ExcludedSignal(
                    signal,
                    f"ownership of {signal.dimension} is unresolved; "
                    "no signal may govern it until resolved",
                )
            )
        elif owner is not None and signal.stakeholder != owner:
            excluded.append(
                ExcludedSignal(
                    signal,
                    f"{signal.stakeholder} has no ownership over "
                    f"{signal.dimension}; {owner} is the applicable owner",
                )
            )
        else:
            excluded.append(
                ExcludedSignal(
                    signal,
                    f"{signal.stakeholder}'s direction for "
                    f"{signal.dimension} is already carried by the "
                    "governing directive",
                )
            )
    return tuple(excluded)


__all__ = [
    "DimensionOwnership",
    "ExcludedSignal",
    "GrantBasis",
    "StakeholderResolution",
    "StakeholderRole",
    "StakeholderSignal",
    "OwnershipGrant",
    "propagation_hold",
    "resolve_stakeholder_ownership",
]
