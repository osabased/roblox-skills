"""Domain adapters proving one alignment contract across creative media.

Spec Phase 11 obligation: the central alignment system owns every semantic
contract (evidence, confidence, profiles, applicability, ownership,
authority, active alignment, checkpoints, propagation, learning,
provenance, reconciliation) while domain adapters supply craft knowledge
and execution.  This module is the executable proof of that split.

Every adapter below contributes only canonical *inputs* -- craft priors as
``DecisionDirective`` directives, medium-worded ``Uncertainty`` questions,
medium-built ``ProbeOption`` constructions, and direction candidates --
and consumes only canonical *outputs* (``resolve_alignment``,
``resolve_policy_alignment``, ``authorize_propagation``).  Adapter-local
state (descriptions, craft libraries) feeds construction only; it is never
copied into an ``AlignmentRequest``, so tampering with it cannot move a
resolution.  There is no private confidence math, no private precedence
chain, and no private propagation gate anywhere in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from alignment_contract import (
    ActiveAlignmentResult,
    AlignmentRequest,
    DecisionDirective,
    Provenance,
    authorize_propagation,
)
from decision_policy import ProbeDecision, ProbeFidelity, ProbeOption
from identifiers import require_identifier


class DomainKind(str, Enum):
    """The representative adapter families validated for cross-domain use."""

    UI = "ui"
    WRITING = "writing"
    MOTION = "motion"


def _validated_domain(value: DomainKind | str) -> DomainKind:
    try:
        return DomainKind(value)
    except ValueError as error:
        raise ValueError(f"unsupported domain: {value}") from error


@dataclass(frozen=True)
class CraftTechnique:
    """One piece of expert medium knowledge offered strictly as a prior."""

    technique_id: str
    dimension: str
    direction: str
    rationale: str

    def __post_init__(self) -> None:
        require_identifier(self.technique_id, "technique_id")
        if not self.dimension or self.dimension.isspace():
            raise ValueError("a craft technique dimension is required")
        if not self.direction or self.direction.isspace():
            raise ValueError("a craft technique direction is required")
        if not self.rationale or self.rationale.isspace():
            raise ValueError("a craft technique rationale is required")


@dataclass(frozen=True)
class DomainAdapter:
    """One medium's plug into the common active-alignment contract.

    The adapter holds craft knowledge and inert presentation metadata.  It
    exposes that knowledge only through canonical input builders; it never
    resolves, reinterprets, or gates semantic decisions itself.
    """

    domain: DomainKind | str
    craft_techniques: tuple[CraftTechnique, ...] = ()
    medium_description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", _validated_domain(self.domain))
        ids = [item.technique_id for item in self.craft_techniques]
        if len(set(ids)) != len(ids):
            raise ValueError("craft technique ids must not contain duplicates")

    @property
    def kind(self) -> DomainKind:
        return DomainKind(self.domain)

    def craft_priors(self) -> tuple[DecisionDirective, ...]:
        """Translate craft knowledge into canonical craft-prior directives."""
        domain = DomainKind(self.domain)
        return tuple(
            DecisionDirective(
                dimension=technique.dimension,
                direction=technique.direction,
                reason=(
                    f"{domain.value} craft prior ({technique.technique_id}): "
                    f"{technique.rationale}"
                ),
                provenance=(
                    Provenance(
                        actor="agent",
                        source_id=f"craft:{technique.technique_id}",
                    ),
                ),
            )
            for technique in self.craft_techniques
        )

    def with_craft_priors(self, request: AlignmentRequest) -> AlignmentRequest:
        """Extend a request's craft-prior slot without touching other slots."""
        merged = (*request.craft_priors, *self.craft_priors())
        return replace(request, craft_priors=merged)

    def authorize(
        self,
        result: ActiveAlignmentResult,
        current_request: AlignmentRequest,
    ) -> ActiveAlignmentResult:
        """The adapter's only propagation authority is the canonical guard."""
        return authorize_propagation(result, current_request)


@dataclass(frozen=True)
class ProbeConstruction:
    """How a medium materializes one calibration probe for execution."""

    kind: str
    instruction: str
    option: ProbeOption

    def __post_init__(self) -> None:
        if not self.kind or self.kind.isspace():
            raise ValueError("a probe construction kind is required")
        if not self.instruction or self.instruction.isspace():
            raise ValueError("a probe execution instruction is required")


def _probe_construction(
    *,
    kind: str,
    instruction: str,
    probe_id: str,
    resolves: tuple[str, ...],
    representative_dimensions: tuple[str, ...],
    cost: int,
    fidelity: ProbeFidelity | str,
) -> ProbeConstruction:
    """Bind one canonical probe option to its medium execution framing."""
    option = ProbeOption(
        probe_id=probe_id,
        resolves=resolves,
        cost=cost,
        representative_dimensions=representative_dimensions,
        fidelity=ProbeFidelity(fidelity),
    )
    return ProbeConstruction(kind=kind, instruction=instruction, option=option)


def ui_contrast_pair_construction(
    *,
    probe_id: str,
    foreground: str,
    background: str,
    resolves: tuple[str, ...],
    representative_dimensions: tuple[str, ...],
    cost: int,
    fidelity: ProbeFidelity | str = ProbeFidelity.MEDIUM,
) -> ProbeConstruction:
    """Build a side-by-side contrast-pair probe for interface decisions."""
    instruction = (
        f"render '{foreground}' on '{background}' beside its alternative "
        "and record which pairing reads better"
    )
    return _probe_construction(
        kind="contrast-pair",
        instruction=instruction,
        probe_id=probe_id,
        resolves=resolves,
        representative_dimensions=representative_dimensions,
        cost=cost,
        fidelity=fidelity,
    )


def writing_excerpt_ab_construction(
    *,
    probe_id: str,
    excerpt_a: str,
    excerpt_b: str,
    resolves: tuple[str, ...],
    representative_dimensions: tuple[str, ...],
    cost: int,
    fidelity: ProbeFidelity | str = ProbeFidelity.MEDIUM,
) -> ProbeConstruction:
    """Build an A/B excerpt probe for prose voice decisions."""
    instruction = (
        f"present excerpt A ('{excerpt_a}') against excerpt B "
        f"('{excerpt_b}') in randomized order and record the chosen voice"
    )
    return _probe_construction(
        kind="excerpt-ab",
        instruction=instruction,
        probe_id=probe_id,
        resolves=resolves,
        representative_dimensions=representative_dimensions,
        cost=cost,
        fidelity=fidelity,
    )


def motion_timing_curve_preview_construction(
    *,
    probe_id: str,
    curve_a: str,
    curve_b: str,
    resolves: tuple[str, ...],
    representative_dimensions: tuple[str, ...],
    cost: int,
    fidelity: ProbeFidelity | str = ProbeFidelity.MEDIUM,
) -> ProbeConstruction:
    """Build a timing-curve preview probe for motion feel decisions."""
    instruction = (
        f"play the same interaction with '{curve_a}' versus '{curve_b}' "
        "timing back to back and capture the felt preference"
    )
    return _probe_construction(
        kind="timing-curve-preview",
        instruction=instruction,
        probe_id=probe_id,
        resolves=resolves,
        representative_dimensions=representative_dimensions,
        cost=cost,
        fidelity=fidelity,
    )


def declared_probes(
    constructions: tuple[ProbeConstruction, ...],
) -> tuple[ProbeOption, ...]:
    """Strip constructions down to their canonical probe declarations."""
    ids = [item.option.probe_id for item in constructions]
    if len(set(ids)) != len(ids):
        raise ValueError("probe constructions must not repeat a probe_id")
    return tuple(item.option for item in constructions)


def execution_instruction(
    constructions: tuple[ProbeConstruction, ...],
    decision: ProbeDecision,
) -> str | None:
    """Bind medium execution to the canonically selected probe only.

    Consumes the canonical ``ProbeDecision`` verbatim: a ``None`` selection
    means the fallback (for example a clarification checkpoint) governs and
    no probe may be manufactured; a selected id must name a declared
    construction or the binding fails loudly.
    """
    if decision.probe_id is None:
        return None
    for construction in constructions:
        if construction.option.probe_id == decision.probe_id:
            return construction.instruction
    raise ValueError(
        f"no construction declared for selected probe: {decision.probe_id}"
    )


__all__ = [
    "CraftTechnique",
    "DomainAdapter",
    "DomainKind",
    "ProbeConstruction",
    "declared_probes",
    "execution_instruction",
    "motion_timing_curve_preview_construction",
    "ui_contrast_pair_construction",
    "writing_excerpt_ab_construction",
]
