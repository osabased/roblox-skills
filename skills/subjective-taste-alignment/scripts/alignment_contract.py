"""Canonical subjective state and active-alignment resolution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Mapping


class Disposition(str, Enum):
    PREFERRED = "preferred"
    REJECTED = "rejected"
    INDIFFERENT = "indifferent"
    UNRESOLVED = "unresolved"


class EpistemicBasis(str, Enum):
    EXPLICIT = "explicit"
    INFERRED = "inferred"


class EpistemicLabel(str, Enum):
    CONFIRMED_PREFERENCE = "confirmed preference"
    STRONG_INFERENCE = "strong inference"
    WEAK_HYPOTHESIS = "weak hypothesis"
    REJECTED_DIRECTION = "rejected direction"
    KNOWN_INDIFFERENCE = "known indifference"
    UNRESOLVED_DIMENSION = "unresolved dimension"


class GoverningSource(str, Enum):
    CONSTRAINT = "constraint"
    OWNERSHIP = "ownership"
    INTENT = "intent"
    EXPERIMENTAL_STATE = "experimental_state"
    TASTE = "taste"
    AUTHORIZED_JUDGMENT = "authorized_judgment"
    CRAFT_PRIOR = "craft_prior"
    KNOWN_INDIFFERENCE = "known_indifference"
    AUTHORITY = "authority"
    CONFLICT = "conflict"


SOURCE_PRECEDENCE = (
    GoverningSource.CONSTRAINT,
    GoverningSource.OWNERSHIP,
    GoverningSource.INTENT,
    GoverningSource.EXPERIMENTAL_STATE,
    GoverningSource.TASTE,
    GoverningSource.AUTHORIZED_JUDGMENT,
    GoverningSource.CRAFT_PRIOR,
)


@dataclass(frozen=True)
class Scope:
    kind: str
    identity: str
    represented_subject: str


@dataclass(frozen=True)
class Provenance:
    actor: str
    source_id: str


@dataclass(frozen=True)
class ValidationContext:
    domain: str
    fidelity: str
    conditions: tuple[str, ...] = ()


@dataclass(frozen=True)
class PreferenceKnowledge:
    dimension: str
    direction: str | None
    disposition: Disposition | str
    basis: EpistemicBasis | str
    confidence: float
    strength: float
    scope: Scope
    context: Mapping[str, str]
    evidence: tuple[str, ...]
    provenance: tuple[Provenance, ...]
    validation_context: ValidationContext
    relationships: Mapping[str, str]

    def __post_init__(self) -> None:
        try:
            disposition = Disposition(self.disposition)
        except ValueError as error:
            raise ValueError(f"unsupported disposition: {self.disposition}") from error
        try:
            basis = EpistemicBasis(self.basis)
        except ValueError as error:
            raise ValueError(f"unsupported epistemic basis: {self.basis}") from error
        object.__setattr__(self, "disposition", disposition)
        object.__setattr__(self, "basis", basis)

        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not 0 <= self.strength <= 1:
            raise ValueError("strength must be between 0 and 1")
        if disposition in {Disposition.PREFERRED, Disposition.REJECTED}:
            if self.direction is None:
                raise ValueError(f"a {disposition.value} disposition requires a direction")
        elif self.direction is not None:
            raise ValueError(f"an {disposition.value} disposition cannot assert a direction")

    @property
    def derived_label(self) -> EpistemicLabel:
        """Present a useful view without creating competing preference state."""
        if self.disposition is Disposition.UNRESOLVED:
            return EpistemicLabel.UNRESOLVED_DIMENSION
        if self.confidence < 0.5:
            return EpistemicLabel.WEAK_HYPOTHESIS
        if self.disposition is Disposition.REJECTED:
            return EpistemicLabel.REJECTED_DIRECTION
        if self.disposition is Disposition.INDIFFERENT:
            return EpistemicLabel.KNOWN_INDIFFERENCE
        if self.basis is EpistemicBasis.INFERRED:
            return EpistemicLabel.STRONG_INFERENCE
        return EpistemicLabel.CONFIRMED_PREFERENCE


@dataclass(frozen=True)
class DecisionDirective:
    dimension: str
    direction: str
    reason: str
    provenance: tuple[Provenance, ...]
    dependencies: tuple[str, ...] = ()
    scope: Scope | None = None


@dataclass(frozen=True)
class AuthorityScope:
    actor: str
    dimensions: tuple[str, ...]
    allows_material_propagation: bool
    checkpoint_required: bool
    scope: Scope
    provenance: tuple[Provenance, ...]


DecisionBearingInput = PreferenceKnowledge | DecisionDirective | AuthorityScope


@dataclass(frozen=True)
class DimensionInputs:
    taste: tuple[PreferenceKnowledge, ...] = ()
    intent: tuple[DecisionDirective, ...] = ()
    constraints: tuple[DecisionDirective, ...] = ()
    ownership: tuple[DecisionDirective, ...] = ()
    experimental_state: tuple[DecisionDirective, ...] = ()
    craft_priors: tuple[DecisionDirective, ...] = ()
    authority: tuple[AuthorityScope, ...] = ()
    provisional_judgments: tuple[DecisionDirective, ...] = ()

    def for_source(self, source: GoverningSource) -> tuple[DecisionBearingInput, ...]:
        source_inputs: dict[GoverningSource, tuple[DecisionBearingInput, ...]] = {
            GoverningSource.CONSTRAINT: self.constraints,
            GoverningSource.OWNERSHIP: self.ownership,
            GoverningSource.INTENT: self.intent,
            GoverningSource.EXPERIMENTAL_STATE: self.experimental_state,
            GoverningSource.TASTE: self.taste,
            GoverningSource.AUTHORIZED_JUDGMENT: self.provisional_judgments,
            GoverningSource.CRAFT_PRIOR: self.craft_priors,
            GoverningSource.AUTHORITY: self.authority,
        }
        return source_inputs.get(source, ())


@dataclass(frozen=True)
class AlignmentConflict:
    source: GoverningSource
    inputs: tuple[DecisionBearingInput, ...]
    blocking: bool


@dataclass(frozen=True)
class ResolvedDimension:
    dimension: str
    direction: str | None
    governing_source: GoverningSource | None
    reason: str
    inputs: DimensionInputs
    conflicts: tuple[AlignmentConflict, ...] = ()

    @property
    def taste(self) -> PreferenceKnowledge | None:
        return self.inputs.taste[0] if len(self.inputs.taste) == 1 else None

    @property
    def intent(self) -> DecisionDirective | None:
        return self.inputs.intent[0] if len(self.inputs.intent) == 1 else None

    @property
    def constraint(self) -> DecisionDirective | None:
        return self.inputs.constraints[0] if len(self.inputs.constraints) == 1 else None

    @property
    def ownership(self) -> DecisionDirective | None:
        return self.inputs.ownership[0] if len(self.inputs.ownership) == 1 else None

    @property
    def experimental_state(self) -> DecisionDirective | None:
        items = self.inputs.experimental_state
        return items[0] if len(items) == 1 else None

    @property
    def craft_prior(self) -> DecisionDirective | None:
        return self.inputs.craft_priors[0] if len(self.inputs.craft_priors) == 1 else None

    @property
    def authority(self) -> AuthorityScope | None:
        return self.inputs.authority[0] if len(self.inputs.authority) == 1 else None

    @property
    def provisional_judgment(self) -> DecisionDirective | None:
        items = self.inputs.provisional_judgments
        return items[0] if len(items) == 1 else None


@dataclass(frozen=True)
class ActiveAlignmentResult:
    decision_id: str
    dimensions: Mapping[str, ResolvedDimension]
    unresolved_dimensions: tuple[str, ...]
    material: bool
    propagation_eligible: bool
    checkpoint_obligations: tuple[str, ...]
    provenance: tuple[Provenance, ...]
    dependencies: tuple[str, ...]
    decision_bearing_revision: str


@dataclass(frozen=True)
class PropagationPolicyDecision:
    """Decision-policy output consumed by the canonical propagation guard."""

    revision: str
    eligible: bool
    route: str | None
    checkpoint_obligations: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class AlignmentRequest:
    decision_id: str
    dimensions: tuple[str, ...]
    material: bool
    taste: tuple[PreferenceKnowledge, ...] = ()
    intent: tuple[DecisionDirective, ...] = ()
    constraints: tuple[DecisionDirective, ...] = ()
    ownership: tuple[DecisionDirective, ...] = ()
    experimental_state: tuple[DecisionDirective, ...] = ()
    craft_priors: tuple[DecisionDirective, ...] = ()
    authority: tuple[AuthorityScope, ...] = ()
    provisional_judgments: tuple[DecisionDirective, ...] = ()
    context_revision: str = "initial"
    dependencies: tuple[str, ...] = ()
    propagation_policy: PropagationPolicyDecision | None = None


class StaleAlignmentError(RuntimeError):
    """A material decision-bearing input changed after resolution."""


class PropagationBlockedError(RuntimeError):
    """The active alignment still has unresolved or checkpoint obligations."""


def _json_key(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _relevant_request_state(request: AlignmentRequest) -> dict[str, object]:
    relevant = set(request.dimensions)

    def filtered(
        items: tuple[PreferenceKnowledge, ...] | tuple[DecisionDirective, ...]
    ) -> list[dict[str, object]]:
        values = [
            asdict(item)
            for item in items
            if getattr(item, "dimension", None) in relevant
        ]
        return sorted(values, key=_json_key)

    authority = []
    for grant in request.authority:
        applicable_dimensions = sorted(relevant.intersection(grant.dimensions))
        if not applicable_dimensions:
            continue
        value = asdict(grant)
        value["dimensions"] = applicable_dimensions
        authority.append(value)

    return {
        "decision_id": request.decision_id,
        "dimensions": sorted(relevant),
        "material": request.material,
        "taste": filtered(request.taste),
        "intent": filtered(request.intent),
        "constraints": filtered(request.constraints),
        "ownership": filtered(request.ownership),
        "experimental_state": filtered(request.experimental_state),
        "craft_priors": filtered(request.craft_priors),
        "authority": sorted(authority, key=_json_key),
        "provisional_judgments": filtered(request.provisional_judgments),
        "context_revision": request.context_revision,
        "dependencies": sorted(set(request.dependencies)),
        "propagation_policy": (
            asdict(request.propagation_policy)
            if request.propagation_policy is not None
            else None
        ),
    }


def _decision_bearing_revision(request: AlignmentRequest) -> str:
    canonical = _json_key(_relevant_request_state(request))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _dimension_inputs(request: AlignmentRequest, dimension: str) -> DimensionInputs:
    return DimensionInputs(
        taste=tuple(item for item in request.taste if item.dimension == dimension),
        intent=tuple(item for item in request.intent if item.dimension == dimension),
        constraints=tuple(
            item for item in request.constraints if item.dimension == dimension
        ),
        ownership=tuple(
            item for item in request.ownership if item.dimension == dimension
        ),
        experimental_state=tuple(
            item for item in request.experimental_state if item.dimension == dimension
        ),
        craft_priors=tuple(
            item for item in request.craft_priors if item.dimension == dimension
        ),
        authority=tuple(
            grant for grant in request.authority if dimension in grant.dimensions
        ),
        provisional_judgments=tuple(
            item
            for item in request.provisional_judgments
            if item.dimension == dimension
        ),
    )


def _input_fingerprint(item: DecisionBearingInput) -> object:
    if isinstance(item, PreferenceKnowledge):
        return item.disposition, item.direction
    if isinstance(item, DecisionDirective):
        return item.direction
    return (
        item.actor,
        item.allows_material_propagation,
        item.checkpoint_required,
        item.scope,
    )


def _source_conflicts(inputs: DimensionInputs) -> dict[GoverningSource, AlignmentConflict]:
    conflicts: dict[GoverningSource, AlignmentConflict] = {}
    for source in SOURCE_PRECEDENCE + (GoverningSource.AUTHORITY,):
        items = inputs.for_source(source)
        if len({_input_fingerprint(item) for item in items}) > 1:
            conflicts[source] = AlignmentConflict(source, items, blocking=False)
    return conflicts


def _agent_authorized(request: AlignmentRequest, inputs: DimensionInputs) -> bool:
    return any(
        grant.actor == "agent"
        and (not request.material or grant.allows_material_propagation)
        for grant in inputs.authority
    )


def _eligible_source_inputs(
    source: GoverningSource,
    request: AlignmentRequest,
    inputs: DimensionInputs,
) -> tuple[DecisionBearingInput, ...]:
    items = inputs.for_source(source)
    if source is GoverningSource.TASTE:
        return tuple(
            item
            for item in items
            if isinstance(item, PreferenceKnowledge)
            and item.disposition is Disposition.PREFERRED
        )
    if source in {
        GoverningSource.AUTHORIZED_JUDGMENT,
        GoverningSource.CRAFT_PRIOR,
    } and not _agent_authorized(request, inputs):
        return ()
    return items


def _direction(item: DecisionBearingInput) -> str | None:
    if isinstance(item, AuthorityScope):
        return None
    return item.direction


def _reason(source: GoverningSource, item: DecisionBearingInput) -> str:
    if isinstance(item, DecisionDirective):
        return item.reason
    if source is GoverningSource.TASTE:
        return "applicable preference knowledge resolves this dimension"
    return "authorized decision-bearing input resolves this dimension"


def _extend_governing_metadata(
    source: GoverningSource | None,
    governing_inputs: tuple[DecisionBearingInput, ...],
    inputs: DimensionInputs,
    provenance: list[Provenance],
    dependencies: list[str],
) -> None:
    selected = list(governing_inputs)
    if source in {
        GoverningSource.AUTHORIZED_JUDGMENT,
        GoverningSource.CRAFT_PRIOR,
    }:
        selected.extend(inputs.authority)
    for item in selected:
        for record in item.provenance:
            if record not in provenance:
                provenance.append(record)
        if isinstance(item, DecisionDirective):
            for dependency in item.dependencies:
                if dependency not in dependencies:
                    dependencies.append(dependency)


def _resolve_dimension(
    request: AlignmentRequest,
    dimension: str,
) -> tuple[ResolvedDimension, tuple[DecisionBearingInput, ...]]:
    inputs = _dimension_inputs(request, dimension)
    conflicts = _source_conflicts(inputs)
    governing_source: GoverningSource | None = None
    governing_inputs: tuple[DecisionBearingInput, ...] = ()
    direction: str | None = None
    reason = "no decision-bearing source resolves this dimension"
    blocking_source: GoverningSource | None = None

    for source in SOURCE_PRECEDENCE:
        source_inputs = inputs.for_source(source)
        if source in conflicts and source_inputs:
            blocking_source = source
            governing_source = GoverningSource.CONFLICT
            reason = f"conflicting {source.value} inputs require resolution"
            governing_inputs = source_inputs
            break
        eligible = _eligible_source_inputs(source, request, inputs)
        if not eligible:
            continue
        governing_source = source
        governing_inputs = eligible
        direction = _direction(eligible[0])
        reason = _reason(source, eligible[0])
        break

    if governing_source is None and any(
        knowledge.disposition is Disposition.INDIFFERENT for knowledge in inputs.taste
    ):
        governing_source = GoverningSource.KNOWN_INDIFFERENCE
        reason = "taste is known indifferent; an execution direction is still required"

    blocking_sources = {
        source
        for source in (blocking_source, GoverningSource.AUTHORITY)
        if source is not None and source in conflicts
    }
    preserved_conflicts = tuple(
        AlignmentConflict(conflict.source, conflict.inputs, source in blocking_sources)
        for source, conflict in conflicts.items()
    )
    return (
        ResolvedDimension(
            dimension=dimension,
            direction=direction,
            governing_source=governing_source,
            reason=reason,
            inputs=inputs,
            conflicts=preserved_conflicts,
        ),
        governing_inputs,
    )


def resolve_alignment(request: AlignmentRequest) -> ActiveAlignmentResult:
    """Resolve every requested dimension through one observable contract."""
    dimensions: dict[str, ResolvedDimension] = {}
    unresolved: list[str] = []
    checkpoints: list[str] = []
    provenance: list[Provenance] = []
    dependencies = list(dict.fromkeys(request.dependencies))

    for dimension in request.dimensions:
        resolved, governing_inputs = _resolve_dimension(request, dimension)
        dimensions[dimension] = resolved
        blocking_conflict = next(
            (conflict for conflict in resolved.conflicts if conflict.blocking),
            None,
        )
        if resolved.direction is None or blocking_conflict is not None:
            unresolved.append(dimension)
            if request.material:
                if blocking_conflict is not None:
                    checkpoints.append(f"resolve-conflict:{dimension}")
                elif resolved.governing_source is GoverningSource.KNOWN_INDIFFERENCE:
                    checkpoints.append(f"decide:{dimension}")
                else:
                    checkpoints.append(f"resolve:{dimension}")
        elif (
            request.material
            and resolved.governing_source is GoverningSource.TASTE
            and request.propagation_policy is None
            and not any(
                grant.checkpoint_required or grant.allows_material_propagation
                for grant in resolved.inputs.authority
            )
        ):
            checkpoints.append(f"assess-propagation:{dimension}")

        metadata_source = (
            None
            if resolved.governing_source is GoverningSource.CONFLICT
            else resolved.governing_source
        )
        _extend_governing_metadata(
            metadata_source,
            governing_inputs,
            resolved.inputs,
            provenance,
            dependencies,
        )

        if request.material and not any(
            conflict.source is GoverningSource.AUTHORITY
            for conflict in resolved.conflicts
        ):
            if any(grant.checkpoint_required for grant in resolved.inputs.authority):
                checkpoints.append(f"review:{dimension}")

    if request.propagation_policy is not None:
        checkpoints.extend(request.propagation_policy.checkpoint_obligations)

    checkpoints = list(dict.fromkeys(checkpoints))
    policy_eligible = (
        request.propagation_policy is None
        or request.propagation_policy.eligible
    )

    return ActiveAlignmentResult(
        decision_id=request.decision_id,
        dimensions=dimensions,
        unresolved_dimensions=tuple(unresolved),
        material=request.material,
        propagation_eligible=not unresolved and not checkpoints and policy_eligible,
        checkpoint_obligations=tuple(checkpoints),
        provenance=tuple(provenance),
        dependencies=tuple(dependencies),
        decision_bearing_revision=_decision_bearing_revision(request),
    )


def is_alignment_stale(
    result: ActiveAlignmentResult,
    current_request: AlignmentRequest,
) -> bool:
    """Return whether the result no longer represents current decision-bearing state."""
    return result.decision_bearing_revision != _decision_bearing_revision(current_request)


def authorize_propagation(
    result: ActiveAlignmentResult,
    current_request: AlignmentRequest,
) -> ActiveAlignmentResult:
    """Reject stale or ineligible alignment before downstream propagation."""
    if is_alignment_stale(result, current_request):
        raise StaleAlignmentError(
            "decision-bearing state changed; re-resolve alignment before propagation"
        )
    if not result.propagation_eligible:
        raise PropagationBlockedError(
            "alignment has unresolved dimensions or checkpoint obligations"
        )
    return result
