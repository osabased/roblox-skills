"""Autonomy, materiality, propagation, direction, and probe policy.

This module extends the canonical active-alignment contract.  It does not
resolve subjective dimensions independently: policy inputs are translated to
an ``AlignmentRequest`` and passed to ``resolve_alignment``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from hashlib import sha256
import json

from alignment_contract import (
    ActiveAlignmentResult,
    AlignmentRequest,
    AuthorityScope,
    DecisionDirective,
    EpistemicLabel,
    GoverningSource,
    PropagationPolicyDecision,
    Provenance,
    authorize_propagation,
    resolve_alignment,
)


class AutonomyPreset(str, Enum):
    AGENT_LED = "agent-led"
    DIRECTION_CHECKPOINT = "direction-checkpoint"
    MILESTONE_CHECKPOINT = "milestone-checkpoint"
    ELEMENT_LEVEL = "element-level"
    HIGH_INTERVENTION = "high-intervention"


class DecisionLevel(str, Enum):
    DIRECTION = "direction"
    MILESTONE = "milestone"
    ELEMENT = "element"
    ELEMENT_FAMILY = "element-family"
    DETAIL = "detail"


class CheckpointPurpose(str, Enum):
    DISCOVERY = "discovery"
    APPLICATION = "application"
    REVIEW = "review"


class PropagationRoute(str, Enum):
    NON_LOAD_BEARING = "non-load-bearing"
    DETERMINING_DIRECTIVE = "determining-directive"
    ESTABLISHED_EVIDENCE = "established-evidence"
    KNOWN_INDIFFERENCE = "known-indifference"
    DELEGATED_AUTHORITY = "delegated-authority"


_PRESET_CONTROLS: dict[AutonomyPreset, tuple[str, str]] = {
    AutonomyPreset.AGENT_LED: ("scope-boundary", "boundary"),
    AutonomyPreset.DIRECTION_CHECKPOINT: ("major-direction", "direction"),
    AutonomyPreset.MILESTONE_CHECKPOINT: (
        "milestone-or-early-risk",
        "milestone",
    ),
    AutonomyPreset.ELEMENT_LEVEL: (
        "load-bearing-element",
        "element-family",
    ),
    AutonomyPreset.HIGH_INTERVENTION: (
        "material-or-salient",
        "individual-small-batch",
    ),
}


@dataclass(frozen=True)
class AutonomySnapshot:
    preset: AutonomyPreset | str
    authority_scope: AuthorityScope
    intervention_threshold: str
    checkpoint_granularity: str
    revision: str
    effective_from_sequence: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "preset", AutonomyPreset(self.preset))
        if not self.revision:
            raise ValueError("an autonomy revision is required")
        if self.effective_from_sequence < 0:
            raise ValueError("effective_from_sequence cannot be negative")

    def applies_to(self, sequence: int) -> bool:
        return sequence >= self.effective_from_sequence


@dataclass(frozen=True)
class DecisionContext:
    sequence: int
    target: str
    level: DecisionLevel | str = DecisionLevel.DETAIL
    reusable: bool = False
    default: bool = False
    shared: bool = False
    dependents: tuple[str, ...] = ()
    expensive: bool = False
    production: bool = False
    grown: bool = False
    salient: bool = False
    milestone_due: bool = False
    expensive_before_milestone: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "level", DecisionLevel(self.level))
        if self.sequence < 0:
            raise ValueError("decision sequence cannot be negative")
        if not self.target:
            raise ValueError("a decision target is required")


@dataclass(frozen=True)
class ProvisionalChoice:
    choice_id: str
    dimension: str
    direction: str
    provenance: tuple[Provenance, ...] = ()
    dependencies: tuple[str, ...] = ()
    basis_reconstructable: bool = True


@dataclass(frozen=True)
class AggregateProvisionalDirection:
    """Several individually minor provisional choices acting as one bundle.

    Individually trivial assumptions must not evade alignment by being
    decomposed into separate decisions; an aggregate is classified as
    presumptively load-bearing before broader propagation.
    """

    aggregate_id: str
    choice_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.aggregate_id or self.aggregate_id.isspace():
            raise ValueError("an aggregate_id is required")
        if len(self.choice_ids) < 2:
            raise ValueError(
                "an aggregate needs at least two interacting choices"
            )
        _require_unique_ids(self.choice_ids, "aggregate choice ids")


@dataclass(frozen=True)
class MaterialityAssessment:
    load_bearing: bool
    reasons: tuple[str, ...]
    aggregate_choice_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DirectionDecision:
    established: bool
    discovery_required: bool
    selection_actor: str | None
    source: str | None
    candidates: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class ProbeDecision:
    uncertainty_ids: tuple[str, ...]
    probe_id: str | None
    fallback: str
    evidence_granularity: str | None
    reason: str


class UncertaintyWeight(str, Enum):
    """How much relying on an unresolved uncertainty would commit."""

    REVERSIBLE = "reversible"
    MATERIAL = "material"
    LOAD_BEARING = "load_bearing"


class ProbeFidelity(str, Enum):
    """How faithfully a probe represents the uncertainty it resolves."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


_PROBE_FIDELITY_RANK = {
    ProbeFidelity.LOW: 1,
    ProbeFidelity.MEDIUM: 2,
    ProbeFidelity.HIGH: 3,
}


@dataclass(frozen=True)
class Uncertainty:
    """One open calibration question, possibly an interacting aggregate."""

    uncertainty_id: str
    dimensions: tuple[str, ...]
    question: str
    weight: UncertaintyWeight | str = UncertaintyWeight.MATERIAL
    aggregate_members: tuple[str, ...] = ()
    minimum_fidelity: ProbeFidelity | str = ProbeFidelity.MEDIUM
    questionable_applicability: bool = False

    def __post_init__(self) -> None:
        if not self.uncertainty_id or self.uncertainty_id.isspace():
            raise ValueError("an uncertainty_id is required")
        if not self.question or self.question.isspace():
            raise ValueError("an uncertainty needs its named subjective question")
        if any(not dimension for dimension in self.dimensions):
            raise ValueError("uncertainty dimensions must be non-empty")
        object.__setattr__(self, "weight", UncertaintyWeight(self.weight))
        object.__setattr__(
            self, "minimum_fidelity", ProbeFidelity(self.minimum_fidelity)
        )
        if len(set(self.aggregate_members)) != len(self.aggregate_members):
            raise ValueError("aggregate_members must not contain duplicates")


@dataclass(frozen=True)
class ProbeOption:
    """One candidate probe with its relative cost and coverage."""

    probe_id: str
    resolves: tuple[str, ...]
    cost: int
    representative_dimensions: tuple[str, ...] = ()
    fidelity: ProbeFidelity | str = ProbeFidelity.MEDIUM

    def __post_init__(self) -> None:
        if not self.probe_id or self.probe_id.isspace():
            raise ValueError("a probe_id is required")
        if self.cost < 0:
            raise ValueError("probe cost cannot be negative")
        _require_unique_ids(self.resolves, "probe resolution targets")
        object.__setattr__(self, "fidelity", ProbeFidelity(self.fidelity))


def _require_unique_ids(values: tuple[str, ...], field_name: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")


@dataclass(frozen=True)
class DirectionCandidate:
    """One materially distinct viable direction."""

    candidate_id: str
    summary: str
    distinguishing_dimensions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.candidate_id or self.candidate_id.isspace():
            raise ValueError("a candidate_id is required")


@dataclass(frozen=True)
class DirectionSpace:
    """The generated comparison space; at least two distinct candidates."""

    candidates: tuple[DirectionCandidate, ...]

    def __post_init__(self) -> None:
        if len(self.candidates) < 2:
            raise ValueError(
                "a direction space requires at least two candidates"
            )
        _require_unique_ids(
            tuple(item.candidate_id for item in self.candidates),
            "direction candidate ids",
        )


@dataclass(frozen=True)
class DelegationOption:
    """One plausible reading of an inferred delegation's implied scope."""

    label: str
    authority: AuthorityScope


@dataclass(frozen=True)
class Delegation:
    """A runtime delegation such as "finish the rest".

    The options enumerate the plausible scopes the instruction could imply.
    Resolution adopts only the narrowest clearly supported option; broader
    readings stay unavailable until an extension checkpoint resolves them.
    A delegation grants authority; it never becomes user-taste evidence.
    """

    instruction_id: str
    options: tuple[DelegationOption, ...] = ()

    def __post_init__(self) -> None:
        if not self.instruction_id or self.instruction_id.isspace():
            raise ValueError("a delegation instruction_id is required")
        labels = [option.label for option in self.options]
        if len(set(labels)) != len(labels):
            raise ValueError("delegation option labels must be unique")


@dataclass(frozen=True)
class Checkpoint:
    key: str
    purpose: CheckpointPurpose | str
    granularity: str
    target: str
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "purpose", CheckpointPurpose(self.purpose))


@dataclass(frozen=True)
class PolicyRequest:
    alignment: AlignmentRequest
    autonomy: AutonomySnapshot
    decision: DecisionContext
    delegation: Delegation | None = None
    provisional_choices: tuple[ProvisionalChoice, ...] = ()
    aggregate: AggregateProvisionalDirection | None = None
    direction: DirectionSpace | None = None
    uncertainties: tuple[Uncertainty, ...] = ()
    probes: tuple[ProbeOption, ...] = ()
    promotion: object | None = None


@dataclass(frozen=True)
class PolicyResolution:
    alignment_request: AlignmentRequest
    alignment: ActiveAlignmentResult
    materiality: MaterialityAssessment
    direction: DirectionDecision
    probe: ProbeDecision
    checkpoints: tuple[Checkpoint, ...]
    policy_revision: str


def autonomy_snapshot(
    preset: AutonomyPreset | str,
    *,
    authority_scope: AuthorityScope,
    revision: str,
    effective_from_sequence: int,
) -> AutonomySnapshot:
    """Build a preset from the shared policy controls."""
    normalized = AutonomyPreset(preset)
    threshold, granularity = _PRESET_CONTROLS[normalized]
    return AutonomySnapshot(
        preset=normalized,
        authority_scope=authority_scope,
        intervention_threshold=threshold,
        checkpoint_granularity=granularity,
        revision=revision,
        effective_from_sequence=effective_from_sequence,
    )


def _materiality(request: PolicyRequest) -> MaterialityAssessment:
    decision = request.decision
    signals = (
        ("reusable", decision.reusable),
        ("default", decision.default),
        ("shared", decision.shared),
        ("dependents", bool(decision.dependents)),
        ("expensive", decision.expensive),
        ("production", decision.production),
        ("grown", decision.grown),
        ("aggregate-provisional-direction", request.aggregate is not None),
    )
    reasons = tuple(name for name, present in signals if present)
    aggregate_ids: tuple[str, ...] = ()
    if request.aggregate is not None:
        aggregate_ids = request.aggregate.choice_ids
    if request.alignment.material and not reasons:
        reasons = ("declared-material",)
    return MaterialityAssessment(
        load_bearing=request.alignment.material or bool(reasons),
        reasons=reasons,
        aggregate_choice_ids=aggregate_ids,
    )


def _base_alignment_request(
    request: PolicyRequest,
    materiality: MaterialityAssessment,
) -> AlignmentRequest:
    authority = list(request.alignment.authority)
    if request.autonomy.applies_to(request.decision.sequence):
        if request.autonomy.authority_scope not in authority:
            authority.append(request.autonomy.authority_scope)

    judgments = list(request.alignment.provisional_judgments)
    dependencies = list(request.alignment.dependencies)
    for choice in request.provisional_choices:
        if not choice.basis_reconstructable:
            # The original basis of this promoted choice cannot be reliably
            # reconstructed.  Fabricating provenance would manufacture
            # authority; drop the judgment so alignment re-resolves the
            # dimension from current decision-bearing state instead.
            continue
        directive = DecisionDirective(
            dimension=choice.dimension,
            direction=choice.direction,
            reason="provisional agent judgment; not user-taste evidence",
            provenance=choice.provenance,
            dependencies=choice.dependencies,
        )
        if directive not in judgments:
            judgments.append(directive)
        for dependency in choice.dependencies:
            if dependency not in dependencies:
                dependencies.append(dependency)

    return replace(
        request.alignment,
        material=materiality.load_bearing,
        authority=tuple(authority),
        provisional_judgments=tuple(judgments),
        dependencies=tuple(dependencies),
        propagation_policy=(
            request.alignment.propagation_policy
            if not request.autonomy.applies_to(request.decision.sequence)
            else None
        ),
    )


def _unresolved_major_direction(
    request: PolicyRequest, initial: ActiveAlignmentResult
) -> bool:
    """True when a major direction still lacks a determining owner."""
    return request.decision.level is DecisionLevel.DIRECTION and any(
        resolved.governing_source
        in {None, GoverningSource.AUTHORIZED_JUDGMENT, GoverningSource.CRAFT_PRIOR}
        for resolved in initial.dimensions.values()
    )


def _preset_checkpoints(
    request: PolicyRequest,
    initial: ActiveAlignmentResult,
) -> tuple[Checkpoint, ...]:
    if not request.autonomy.applies_to(request.decision.sequence):
        return ()
    preset = AutonomyPreset(request.autonomy.preset)
    decision = request.decision
    checkpoints: list[Checkpoint] = []
    unresolved_major = _unresolved_major_direction(request, initial)

    if preset in {
        AutonomyPreset.DIRECTION_CHECKPOINT,
        AutonomyPreset.HIGH_INTERVENTION,
    } and unresolved_major:
        space = request.direction
        if space is not None:
            reason = (
                "the user owns unresolved material direction selection; "
                f"compare {len(space.candidates)} materially distinct "
                "candidates before refinement"
            )
        else:
            reason = "the user owns unresolved material direction selection"
        checkpoints.append(
            Checkpoint(
                key="select-direction",
                purpose=CheckpointPurpose.DISCOVERY,
                granularity="direction",
                target=decision.target,
                reason=reason,
            )
        )

    if preset is AutonomyPreset.MILESTONE_CHECKPOINT:
        if decision.expensive_before_milestone:
            key = "review-before-propagation"
            reason = "the choice becomes expensive before the next milestone"
        elif decision.milestone_due:
            key = "review-milestone"
            reason = "the active milestone is due for integrated review"
        else:
            key = ""
            reason = ""
        if key:
            checkpoints.append(
                Checkpoint(
                    key=key,
                    purpose=CheckpointPurpose.REVIEW,
                    granularity="milestone",
                    target=decision.target,
                    reason=reason,
                )
            )

    if preset is AutonomyPreset.ELEMENT_LEVEL and (
        initial.material or decision.salient
    ):
        checkpoints.append(
            Checkpoint(
                key=f"review-element-family:{decision.target}",
                purpose=CheckpointPurpose.REVIEW,
                granularity="element-family",
                target=decision.target,
                reason="validate the load-bearing element-family direction",
            )
        )

    if preset is AutonomyPreset.HIGH_INTERVENTION and (
        initial.material or decision.salient
    ):
        checkpoints.append(
            Checkpoint(
                key=f"review-application:{decision.target}",
                purpose=CheckpointPurpose.APPLICATION,
                granularity="individual-small-batch",
                target=decision.target,
                reason="review this material or strongly salient application",
            )
        )
    return tuple(checkpoints)


def _propagation_route(
    initial: ActiveAlignmentResult,
    materiality: MaterialityAssessment,
) -> PropagationRoute | None:
    if not materiality.load_bearing:
        return PropagationRoute.NON_LOAD_BEARING
    sources = {
        resolved.governing_source for resolved in initial.dimensions.values()
    }
    if initial.unresolved_dimensions:
        return None
    if sources and sources <= {
        GoverningSource.CONSTRAINT,
        GoverningSource.INTENT,
        GoverningSource.OWNERSHIP,
    }:
        return PropagationRoute.DETERMINING_DIRECTIVE
    if sources == {GoverningSource.TASTE}:
        governed_taste = [
            resolved.taste
            for resolved in initial.dimensions.values()
            if resolved.governing_source is GoverningSource.TASTE
        ]
        if governed_taste and all(
            knowledge is not None
            and knowledge.derived_label is EpistemicLabel.CONFIRMED_PREFERENCE
            for knowledge in governed_taste
        ):
            # Only sufficiently established (confirmed) taste carries this
            # route; weaker hypotheses stay unclassified and blocked.
            return PropagationRoute.ESTABLISHED_EVIDENCE
        return None
    if sources == {GoverningSource.KNOWN_INDIFFERENCE}:
        return PropagationRoute.KNOWN_INDIFFERENCE
    if sources and sources <= {
        GoverningSource.AUTHORIZED_JUDGMENT,
        GoverningSource.CRAFT_PRIOR,
    }:
        return PropagationRoute.DELEGATED_AUTHORITY
    return None


_WEIGHT_RANK = {
    UncertaintyWeight.REVERSIBLE: 0,
    UncertaintyWeight.MATERIAL: 1,
    UncertaintyWeight.LOAD_BEARING: 2,
}


def _direction_decision(
    request: PolicyRequest, unresolved_direction: bool
) -> DirectionDecision:
    if not unresolved_direction:
        return DirectionDecision(
            established=True,
            discovery_required=False,
            selection_actor=None,
            source=None,
            candidates=(),
            reason=(
                "an established intent, owner-authorized reference, "
                "applicable taste, or selected direction already determines "
                "the direction"
            ),
        )
    actor = (
        "agent"
        if request.autonomy.preset is AutonomyPreset.AGENT_LED
        else "user"
    )
    space = request.direction
    if space is None:
        return DirectionDecision(
            established=False,
            discovery_required=True,
            selection_actor=actor,
            source=None,
            candidates=(),
            reason=(
                "material direction still requires deliberate selection; "
                "without a generated comparison space the first plausible "
                "framing must not silently define the search space"
            ),
        )
    return DirectionDecision(
        established=False,
        discovery_required=True,
        selection_actor=actor,
        source="direction-space",
        candidates=tuple(
            item.candidate_id for item in space.candidates
        ),
        reason=(
            f"compare {len(space.candidates)} materially distinct candidates "
            "before spending on detailed refinement"
        ),
    )


def _probe_decision(
    request: PolicyRequest, initial: ActiveAlignmentResult
) -> ProbeDecision:
    if not request.uncertainties:
        return ProbeDecision(
            (),
            None,
            "not-needed",
            None,
            "no calibration uncertainty was supplied",
        )

    indifferent_dimensions = {
        dimension
        for dimension, resolved in initial.dimensions.items()
        if resolved.governing_source is GoverningSource.KNOWN_INDIFFERENCE
    }

    def suppressed(item: Uncertainty) -> bool:
        return (
            not item.questionable_applicability
            and bool(item.dimensions)
            and set(item.dimensions).issubset(indifferent_dimensions)
        )

    live = [item for item in request.uncertainties if not suppressed(item)]
    if not live:
        return ProbeDecision(
            (),
            None,
            "not-needed",
            None,
            "known indifference suppresses unnecessary calibration",
        )

    def value(item: Uncertainty) -> tuple[int, int, str]:
        return (
            -_WEIGHT_RANK[UncertaintyWeight(item.weight)],
            0 if item.aggregate_members else 1,
            item.uncertainty_id,
        )

    top = min(live, key=value)
    covering = [
        probe
        for probe in request.probes
        if top.uncertainty_id in probe.resolves
        and set(top.dimensions).issubset(set(probe.representative_dimensions))
        and _PROBE_FIDELITY_RANK[ProbeFidelity(probe.fidelity)]
        >= _PROBE_FIDELITY_RANK[ProbeFidelity(top.minimum_fidelity)]
    ]
    if not covering:
        return ProbeDecision(
            (top.uncertainty_id,),
            None,
            "clarification-checkpoint",
            None,
            reason=(
                f"the highest-value unresolved uncertainty ({top.uncertainty_id}) "
                "has no sufficiently representative faithful probe; resolve it "
                "explicitly"
            ),
        )
    chosen = min(covering, key=lambda probe: (probe.cost, probe.probe_id))
    aggregate_note = (
        " (aggregate of interacting minor choices)"
        if top.aggregate_members
        else ""
    )
    return ProbeDecision(
        (top.uncertainty_id,),
        chosen.probe_id,
        "representative-probe",
        "representative",
        reason=(
            "the cheapest sufficiently representative probe targets the "
            f"highest-value unresolved uncertainty ({top.uncertainty_id})"
            f"{aggregate_note}"
        ),
    )


def _uncovered_uncertainty_checkpoint(
    request: PolicyRequest,
    initial: ActiveAlignmentResult,
) -> Checkpoint | None:
    if not request.autonomy.applies_to(request.decision.sequence):
        return None
    decision = _probe_decision(request, initial)
    if decision.probe_id is not None or not decision.uncertainty_ids:
        return None
    top_id = decision.uncertainty_ids[0]
    return Checkpoint(
        key=f"resolve-uncertainty:{top_id}",
        purpose=CheckpointPurpose.DISCOVERY,
        granularity=request.autonomy.checkpoint_granularity,
        target=request.decision.target,
        reason=(
            "no sufficiently representative probe covers the highest-value "
            "unresolved uncertainty; clarify it before material propagation"
        ),
    )


def _policy_revision(
    request: PolicyRequest,
    alignment_request: AlignmentRequest,
) -> str:
    alignment_state = asdict(alignment_request)
    alignment_state["propagation_policy"] = None
    state: dict[str, object] = {
        "alignment": alignment_state,
        "decision": asdict(request.decision),
        "provisional_choices": [asdict(item) for item in request.provisional_choices],
        "aggregate": request.aggregate,
        "direction": request.direction,
        "uncertainties": list(request.uncertainties),
        "probes": list(request.probes),
        "promotion": request.promotion,
        "delegation": request.delegation,
    }
    if request.autonomy.applies_to(request.decision.sequence):
        state["autonomy"] = asdict(request.autonomy)
    canonical = json.dumps(
        state,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
        default=lambda value: asdict(value) if hasattr(value, "__dataclass_fields__") else str(value),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _narrowest_option(options: tuple[DelegationOption, ...]) -> DelegationOption:
    return min(
        options,
        key=lambda option: (
            len(option.authority.dimensions),
            option.authority.allows_material_propagation,
            option.label,
        ),
    )


def _delegation_decision(
    request: PolicyRequest,
) -> tuple[AuthorityScope | None, Checkpoint | None]:
    delegation = request.delegation
    if delegation is None or not delegation.options:
        return None, None
    adopted = _narrowest_option(delegation.options)
    granted = {
        (tuple(sorted(option.authority.dimensions)), option.authority.allows_material_propagation)
        for option in delegation.options
    }
    checkpoint: Checkpoint | None = None
    if len(granted) > 1:
        checkpoint = Checkpoint(
            key=f"extend-authority:{delegation.instruction_id}",
            purpose=CheckpointPurpose.DISCOVERY,
            granularity=request.autonomy.checkpoint_granularity,
            target=request.decision.target,
            reason=(
                "ambiguous delegation applies only to its narrowest clearly "
                "supported scope; broader material authority needs a "
                "checkpoint before extension"
            ),
        )
    return adopted.authority, checkpoint


def resolve_policy_alignment(request: PolicyRequest) -> PolicyResolution:
    """Resolve policy, then feed its decision into canonical alignment."""
    materiality = _materiality(request)
    base_request = _base_alignment_request(request, materiality)
    adopted_authority, extension_checkpoint = _delegation_decision(request)
    if adopted_authority is not None and adopted_authority not in base_request.authority:
        base_request = replace(
            base_request, authority=(*base_request.authority, adopted_authority)
        )
    historical_policy = base_request.propagation_policy
    if historical_policy is not None:
        alignment = resolve_alignment(base_request)
        checkpoints = tuple(
            Checkpoint(
                key=key,
                purpose=CheckpointPurpose.REVIEW,
                granularity=request.autonomy.checkpoint_granularity,
                target=request.decision.target,
                reason="preserved historical checkpoint obligation",
            )
            for key in historical_policy.checkpoint_obligations
        )
        return PolicyResolution(
            alignment_request=base_request,
            alignment=alignment,
            materiality=materiality,
            direction=DirectionDecision(
                established=not alignment.unresolved_dimensions,
                discovery_required=False,
                selection_actor=None,
                source="historical-policy",
                candidates=(),
                reason="later autonomy does not rewrite a completed decision",
            ),
            probe=ProbeDecision(
                (),
                None,
                "not-needed",
                None,
                "completed decision retains its prior probe state",
            ),
            checkpoints=checkpoints,
            policy_revision=historical_policy.revision,
        )
    initial = resolve_alignment(base_request)
    checkpoints = (*_preset_checkpoints(request, initial),)
    if extension_checkpoint is not None:
        checkpoints = (*checkpoints, extension_checkpoint)
    uncertainty_checkpoint = _uncovered_uncertainty_checkpoint(request, initial)
    if uncertainty_checkpoint is not None:
        checkpoints = (*checkpoints, uncertainty_checkpoint)
    route = _propagation_route(initial, materiality)
    revision = _policy_revision(request, base_request)
    eligible = route is not None and not checkpoints
    policy = PropagationPolicyDecision(
        revision=revision,
        eligible=eligible,
        route=route.value if route is not None else None,
        checkpoint_obligations=tuple(item.key for item in checkpoints),
        reason=(
            f"propagation uses the {route.value} route"
            if route is not None
            else "no propagation route resolves every decision dimension"
        ),
    )
    bridged_request = replace(base_request, propagation_policy=policy)
    alignment = resolve_alignment(bridged_request)
    unresolved_direction = _unresolved_major_direction(request, initial)
    direction = _direction_decision(request, unresolved_direction)
    probe = _probe_decision(request, initial)
    return PolicyResolution(
        alignment_request=bridged_request,
        alignment=alignment,
        materiality=materiality,
        direction=direction,
        probe=probe,
        checkpoints=checkpoints,
        policy_revision=revision,
    )


def authorize_policy_propagation(
    resolved: PolicyResolution,
    current: PolicyRequest,
) -> ActiveAlignmentResult:
    """Re-evaluate current policy state and call the canonical guard."""
    current_resolution = resolve_policy_alignment(current)
    return authorize_propagation(
        resolved.alignment,
        current_resolution.alignment_request,
    )
