"""Profile inspection and safe user control.

Spec Phase 9 obligations, routed through the canonical lifecycle and
evidence seams:

- Inspection exposes sections, properties, relationships, unresolved
  knowledge, evidence, provenance, scope, context, confidence, and
  validation context.  Conditional rules are reported verbatim; they are
  never flattened into summaries to make inspection simpler.
- Ordinary management requests (modification, correction, reset,
  relearning, versioning, consolidation, undo) route into
  :mod:`profile_lifecycle`; users never hand-edit the representation.
- A direct-edit surface exposes only the editable preference assertion.
  Confidence, provenance, evidence identity, validation context, and
  evidence applicability are protected epistemic state: they cannot be
  written through an edit at all.
- Authorship stays distinguishable.  Edits attributable to the user enter
  the explicit-evidence pipeline; agent-authored or unknown-authorship
  mutations are recorded only as weakly supported inferred observations
  and can never masquerade as explicit user evidence.
- When the user instructs a change, the instruction is the one evidence
  event; persisting the resulting profile state is not counted as a
  second observation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from alignment_contract import (
    Disposition,
    EpistemicBasis,
    EpistemicLabel,
    Provenance,
    Scope,
    ValidationContext,
)
from evidence_reconciliation import (
    Ambiguity,
    Consequence,
    EvidenceEvent,
    EvidenceImplication,
    EvidenceType,
    FeedbackKind,
    Fidelity,
    Judgment,
    PointClaim,
    SupportApplicability,
    SupportRef,
    SupportStrength,
)
from identifiers import require_identifier as _require_identifier
from profile_lifecycle import (
    ConsolidationOutcome,
    ConsolidationRequest,
    CreateBranch,
    IngestProfileEvidence,
    LifecycleState,
    LifecycleTransition,
    ResetSupport,
    UndoLastOperation,
    apply_lifecycle_operation,
    consolidate_profiles,
)
from profile_persistence import MutationAuthorship, ProfileState
from reconciliation import (
    CommitCorrection,
    CorrectedInput,
    DecisionInputKind,
)


class ManagementKind(str, Enum):
    """The ordinary profile-management requests users can make."""

    MODIFY = "modify"
    CORRECT = "correct"
    RESET = "reset"
    RELEARN = "relearn"
    VERSION = "version"
    CONSOLIDATE = "consolidate"
    UNDO = "undo"


@dataclass(frozen=True)
class PropertyInspection:
    """One property with every facet users may need to understand it."""

    claim_id: str
    section: str
    owner: str | None
    dimension: str
    direction: str | None
    disposition: Disposition
    label: EpistemicLabel
    basis: EpistemicBasis
    confidence: float
    strength: float
    scope: Scope
    context: tuple[tuple[str, str], ...]
    validation_context: ValidationContext
    relationships: tuple[tuple[str, str], ...]
    evidence: tuple[str, ...]
    provenance: tuple[Provenance, ...]
    evidence_applicable: bool


@dataclass(frozen=True)
class ProfileInspection:
    """A complete, condition-preserving view of one profile."""

    profile_id: str
    schema_version: int
    properties: tuple[PropertyInspection, ...]
    unresolved_property_ids: tuple[str, ...]
    support_exclusions: tuple[tuple[str, str, SupportApplicability], ...]


def inspect_profile(state: LifecycleState) -> ProfileInspection:
    """Report profile knowledge without flattening conditional meaning."""
    reports: list[PropertyInspection] = []
    unresolved: list[str] = []
    for prop in state.profile.properties:
        knowledge = prop.knowledge
        label = knowledge.derived_label
        reports.append(
            PropertyInspection(
                claim_id=prop.claim_id,
                section=prop.section,
                owner=prop.owner,
                dimension=knowledge.dimension,
                direction=knowledge.direction,
                disposition=Disposition(knowledge.disposition),
                label=label,
                basis=EpistemicBasis(knowledge.basis),
                confidence=knowledge.confidence,
                strength=knowledge.strength,
                scope=knowledge.scope,
                context=tuple(knowledge.context.items()),
                validation_context=knowledge.validation_context,
                relationships=tuple(knowledge.relationships.items()),
                evidence=tuple(knowledge.evidence),
                provenance=tuple(knowledge.provenance),
                evidence_applicable=prop.evidence_applicable,
            )
        )
        if (
            knowledge.disposition is Disposition.UNRESOLVED
            or label is EpistemicLabel.UNRESOLVED_DIMENSION
        ):
            unresolved.append(prop.claim_id)
    exclusions = tuple(
        (
            record.support.stable_id,
            record.reason,
            SupportApplicability(record.applicability),
        )
        for record in state.evidence.support_lifecycle
    )
    return ProfileInspection(
        profile_id=state.profile.profile_id,
        schema_version=state.profile.schema_version,
        properties=tuple(reports),
        unresolved_property_ids=tuple(unresolved),
        support_exclusions=exclusions,
    )


@dataclass(frozen=True)
class ManagementRequest:
    """One user request for ordinary, non-manual profile management."""

    operation_id: str
    instruction_id: str
    kind: ManagementKind | str
    scope: Scope
    actor: str = "user"
    dimension: str | None = None
    new_direction: str | None = None
    prior_support: SupportRef | None = None
    support: SupportRef | None = None
    branch_id: str | None = None
    absorbed: ProfileState | None = None

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.instruction_id, "instruction_id")
        try:
            kind = ManagementKind(self.kind)
        except ValueError as error:
            raise ValueError(f"unsupported management request: {self.kind}") from error
        object.__setattr__(self, "kind", kind)
        if self.actor != "user":
            raise ValueError(
                "management requests are attributable to the user; "
                f"actor {self.actor!r} cannot issue one"
            )
        if kind in {ManagementKind.MODIFY, ManagementKind.CORRECT}:
            if not self.dimension or not self.new_direction:
                raise ValueError(
                    f"a {kind.value} request names its dimension and direction"
                )
        if kind is ManagementKind.CORRECT and self.prior_support is None:
            raise ValueError("a correction names the superseded support")
        if kind in {ManagementKind.RESET, ManagementKind.RELEARN}:
            if self.support is None:
                raise ValueError(f"a {kind.value} request targets one support")
        if kind is ManagementKind.VERSION:
            if not self.branch_id:
                raise ValueError("a version request names the new branch")
            _require_identifier(self.branch_id, "branch_id")
        if kind is ManagementKind.CONSOLIDATE and self.absorbed is None:
            raise ValueError("a consolidation request names the absorbed profile")


@dataclass(frozen=True)
class ManagementOutcome:
    """Result of one management request over the lifecycle seam."""

    transition: LifecycleTransition | None
    consolidation: ConsolidationOutcome | None
    operation_id: str
    instruction_event: EvidenceEvent | None
    reason: str

    @property
    def corrected_claim_ids(self) -> tuple[str, ...]:
        if self.transition is None:
            return ()
        return self.transition.changed_claim_ids


def _management_outcome(
    request: ManagementRequest,
    *,
    transition: LifecycleTransition | None = None,
    consolidation: ConsolidationOutcome | None = None,
    instruction_event: EvidenceEvent | None = None,
    reason: str,
) -> ManagementOutcome:
    """Build one outcome carrying only what this operation produced."""
    return ManagementOutcome(
        transition=transition,
        consolidation=consolidation,
        operation_id=request.operation_id,
        instruction_event=instruction_event,
        reason=reason,
    )


# Preference weight of a recorded instruction depends on who authored it:
# user-attributable instructions carry strong explicit preference weight;
# everything else is weakly supported inferred evidence.
_USER_PREFERENCE_STRENGTH = 0.8
_INFERRED_PREFERENCE_STRENGTH = 0.3


def _preference_strength(*, attributable_to_user: bool) -> float:
    if attributable_to_user:
        return _USER_PREFERENCE_STRENGTH
    return _INFERRED_PREFERENCE_STRENGTH


def _attributable_to_user(authorship: MutationAuthorship) -> bool:
    """Whether an edit's authorship names the user specifically."""
    return authorship.attributable and authorship.actor == "user"


def _instruction_event_for(
    request: ManagementRequest,
    state: LifecycleState,
    *,
    attributable_to_user: bool,
) -> EvidenceEvent:
    assert request.dimension is not None and request.new_direction is not None
    occurred_at = (
        max((event.occurred_at for event in state.evidence.events), default=0) + 1
    )
    basis = (
        EpistemicBasis.EXPLICIT if attributable_to_user else EpistemicBasis.INFERRED
    )
    return EvidenceEvent(
        event_id=request.instruction_id,
        evidence_type=EvidenceType.EXPLICIT_FEEDBACK,
        feedback=(
            FeedbackKind.CORRECTION
            if request.kind is ManagementKind.CORRECT
            else FeedbackKind.NONE
        ),
        judgment=Judgment.PREFERRED,
        scope=request.scope,
        context=(),
        provenance=(
            Provenance(actor=request.actor, source_id=request.instruction_id),
        ),
        validation_context=ValidationContext(
            domain="user-instruction",
            fidelity="high" if attributable_to_user else "unknown",
            conditions=(),
        ),
        occurred_at=occurred_at,
        implications=(
            EvidenceImplication(
                implication_id=f"{request.instruction_id}-impl",
                claim=PointClaim(
                    dimension=request.dimension,
                    direction=request.new_direction,
                    disposition=Disposition.PREFERRED,
                ),
                basis=basis,
                represented_dimensions=(request.dimension,),
                fidelity=Fidelity.HIGH,
                required_fidelity=Fidelity.HIGH,
                ambiguity=Ambiguity.CLEAR,
                epistemic_strength=(
                    SupportStrength.STRONG
                    if attributable_to_user
                    else SupportStrength.WEAK
                ),
                preference_strength=_preference_strength(
                    attributable_to_user=attributable_to_user
                ),
                consequence=Consequence.MATERIAL,
            ),
        ),
    )


def manage_profile(
    state: LifecycleState,
    request: ManagementRequest,
) -> ManagementOutcome:
    """Route one user request through the validated lifecycle operations."""
    kind = ManagementKind(request.kind)
    if kind is ManagementKind.RESET:
        support = request.support
        assert support is not None  # validated by ManagementRequest
        transition = apply_lifecycle_operation(
            state,
            ResetSupport(
                operation_id=f"{request.operation_id}:exclude",
                support=support,
                reason=f"user reset requested by {request.instruction_id}",
            ),
        )
        return _management_outcome(
            request,
            transition=transition,
            reason="targeted reset applied; history remains inspectable",
        )
    if kind is ManagementKind.RELEARN:
        support = request.support
        assert support is not None  # validated by ManagementRequest
        transition = apply_lifecycle_operation(
            state,
            ResetSupport(
                operation_id=f"{request.operation_id}:exclude",
                support=support,
                reason=f"relearning requested by {request.instruction_id}",
            ),
        )
        return _management_outcome(
            request,
            transition=transition,
            reason="superseded support excluded; relearning starts from new evidence",
        )
    if kind is ManagementKind.VERSION:
        branch_id = request.branch_id
        assert branch_id is not None  # validated by ManagementRequest
        transition = apply_lifecycle_operation(
            state,
            CreateBranch(
                operation_id=request.operation_id,
                branch_id=branch_id,
                provenance=(
                    Provenance(actor="user", source_id=request.instruction_id),
                ),
            ),
        )
        return _management_outcome(
            request,
            transition=transition,
            reason="alternative branch registered; inert until selected",
        )
    if kind is ManagementKind.UNDO:
        transition = apply_lifecycle_operation(
            state, UndoLastOperation(operation_id=request.operation_id)
        )
        return _management_outcome(
            request,
            transition=transition,
            reason="prior profile and applicability state restored",
        )
    if kind is ManagementKind.CONSOLIDATE:
        absorbed = request.absorbed
        assert absorbed is not None  # validated by ManagementRequest
        outcome = consolidate_profiles(
            ConsolidationRequest(
                operation_id=request.operation_id,
                survivor=state.profile,
                absorbed=absorbed,
            )
        )
        return _management_outcome(
            request, consolidation=outcome, reason=outcome.reason
        )

    # MODIFY and CORRECT: the user instruction itself is the evidence.
    event = _instruction_event_for(request, state, attributable_to_user=True)
    working = state
    if kind is ManagementKind.CORRECT:
        prior_support = request.prior_support
        assert prior_support is not None  # validated by ManagementRequest
        working = apply_lifecycle_operation(
            working,
            ResetSupport(
                operation_id=f"{request.operation_id}:exclude",
                support=prior_support,
                reason=f"superseded by correction {request.instruction_id}",
            ),
        ).state
    transition = apply_lifecycle_operation(
        working,
        IngestProfileEvidence(
            operation_id=request.operation_id, event=event
        ),
    )
    verb = "correction" if kind is ManagementKind.CORRECT else "modification"
    return _management_outcome(
        request,
        transition=transition,
        instruction_event=event,
        reason=f"user {verb} recorded once as instruction evidence",
    )


@dataclass(frozen=True)
class DirectEditRequest:
    """A change to the directly editable surface of one property.

    Only the preference assertion is editable.  Protected epistemic fields
    (confidence, strength, provenance, evidence identity, validation
    context, applicability) have no edit path at all; passing one raises.
    """

    edit_id: str
    authorship: MutationAuthorship
    claim_id: str
    direction: str
    confidence: float | None = None

    def __post_init__(self) -> None:
        _require_identifier(self.edit_id, "edit_id")
        _require_identifier(self.claim_id, "claim_id")
        _require_identifier(self.direction, "direction")
        if self.confidence is not None:
            raise ValueError(
                "confidence is protected epistemic state and cannot be set "
                "through a direct edit"
            )


@dataclass(frozen=True)
class DirectEditOutcome:
    """One validated direct edit incorporated through the lifecycle seam."""

    transition: LifecycleTransition
    instruction_event: EvidenceEvent
    reason: str


def _observation_event_for(
    request: DirectEditRequest,
    target_dimension: str,
    property_scope: Scope,
    *,
    occurred_at: int,
) -> EvidenceEvent:
    attributable_user = _attributable_to_user(request.authorship)
    actor = request.authorship.actor if request.authorship.attributable else "unknown"
    return EvidenceEvent(
        event_id=request.edit_id,
        evidence_type=(
            EvidenceType.EXPLICIT_FEEDBACK
            if attributable_user
            else EvidenceType.OBSERVABLE_ACTION
        ),
        feedback=FeedbackKind.NONE,
        judgment=Judgment.PREFERRED if attributable_user else Judgment.UNSPECIFIED,
        scope=property_scope,
        context=(),
        provenance=(Provenance(actor=actor, source_id=request.edit_id),),
        validation_context=ValidationContext(
            domain="direct-edit",
            fidelity="high" if attributable_user else "unknown",
            conditions=(),
        ),
        occurred_at=occurred_at,
        implications=(
            EvidenceImplication(
                implication_id=f"{request.edit_id}-impl",
                claim=PointClaim(
                    dimension=target_dimension,
                    direction=request.direction,
                    disposition=Disposition.PREFERRED,
                ),
                basis=(
                    EpistemicBasis.EXPLICIT
                    if attributable_user
                    else EpistemicBasis.INFERRED
                ),
                represented_dimensions=(target_dimension,),
                fidelity=Fidelity.HIGH if attributable_user else Fidelity.MEDIUM,
                required_fidelity=Fidelity.HIGH,
                ambiguity=Ambiguity.CLEAR,
                epistemic_strength=(
                    SupportStrength.STRONG
                    if attributable_user
                    else SupportStrength.WEAK
                ),
                preference_strength=_preference_strength(
                    attributable_to_user=attributable_user
                ),
                consequence=Consequence.MATERIAL,
            ),
        ),
    )


def apply_direct_edit(
    state: LifecycleState,
    request: DirectEditRequest,
) -> DirectEditOutcome:
    """Validate and incorporate one direct edit through canonical seams."""
    target = next(
        (prop for prop in state.profile.properties if prop.claim_id == request.claim_id),
        None,
    )
    if target is None:
        raise ValueError(f"unknown property: {request.claim_id}")
    # Recency participates in evidence dominance, so a fresh edit must be
    # able to outweigh prior equal-quality observations.
    occurred_at = (
        max((event.occurred_at for event in state.evidence.events), default=0) + 1
    )
    event = _observation_event_for(
        request,
        target.knowledge.dimension,
        target.knowledge.scope,
        occurred_at=occurred_at,
    )
    transition = apply_lifecycle_operation(
        state,
        IngestProfileEvidence(operation_id=request.edit_id, event=event),
    )
    attributable_user = _attributable_to_user(request.authorship)
    if attributable_user:
        reason = (
            "user edit entered the explicit-evidence pipeline at its own quality"
        )
    else:
        reason = (
            "non-user edit recorded as an inferred observation; authorship "
            f"{request.authorship.actor!r} cannot become explicit user evidence"
        )
    return DirectEditOutcome(
        transition=transition,
        instruction_event=event,
        reason=reason,
    )


def request_support_change(
    state: LifecycleState,
    authorship: MutationAuthorship,
    support: SupportRef,
    *,
    reactivate: bool,
) -> None:
    """Always refuse direct applicability changes.

    Resurrecting superseded support or suppressing valid evidence is a
    lifecycle decision that requires a validated attributable operation
    through :func:`manage_profile`; no authorship level may perform it as
    a plain edit.
    """
    del state, authorship, support
    action = "reactivate" if reactivate else "suppress"
    raise ValueError(
        f"direct edits cannot {action} evidence applicability; use a "
        "validated lifecycle operation such as undo, reset, or relearn"
    )


def correction_commit(
    outcome: ManagementOutcome,
    *,
    basis_revision: str,
) -> CommitCorrection | None:
    """Build the canonical correction commit for a profile change.

    Narrowness is not decided here: the reconciliation engine derives the
    affected dependents from their declared input dependencies when this
    commit is applied.
    """
    input_ids = tuple(
        sorted(f"knowledge:{claim_id}" for claim_id in outcome.corrected_claim_ids)
    )
    if not input_ids:
        return None
    return CommitCorrection(
        operation_id=f"{outcome.operation_id}:commit",
        corrected_inputs=tuple(
            CorrectedInput(input_id=input_id, kind=DecisionInputKind.TASTE)
            for input_id in input_ids
        ),
        basis_revision=basis_revision,
    )


__all__ = [
    "DirectEditOutcome",
    "DirectEditRequest",
    "ManagementKind",
    "ManagementOutcome",
    "ManagementRequest",
    "ProfileInspection",
    "PropertyInspection",
    "apply_direct_edit",
    "correction_commit",
    "inspect_profile",
    "manage_profile",
    "request_support_change",
]
