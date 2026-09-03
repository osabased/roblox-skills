"""Applicable scoped-profile composition through one public interface."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Mapping, NamedTuple

from alignment_contract import (
    ActiveAlignmentResult,
    AuthorityScope,
    GoverningSource,
    PreferenceKnowledge,
    Provenance,
)


def _encode_alignment_component(component: str) -> str:
    """Escape a path component so dotted alignment dimensions stay injective."""
    return component.replace("%", "%25").replace(".", "%2E")


class PropertyPath(NamedTuple):
    section: str
    property_name: str

    @property
    def alignment_dimension(self) -> str:
        section = _encode_alignment_component(self.section)
        property_name = _encode_alignment_component(self.property_name)
        return f"{section}.{property_name}"


class ScopeIdentity(NamedTuple):
    kind: str
    identity: str


class ScopeOperation(str, Enum):
    DUPLICATE = "duplicate"
    BRANCH = "branch"
    COPY = "copy"
    MOVE = "move"


class ScopeOutcome(str, Enum):
    PRESERVE = "preserve"
    REPLACE = "replace"
    AMBIGUOUS = "ambiguous"


class ScopeTransitionStatus(str, Enum):
    PRESERVED = "preserved"
    REPLACED = "replaced"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class RelationalRequirement:
    property_path: PropertyPath
    direction: str


@dataclass(frozen=True)
class ProfileProperty:
    claim_id: str
    section: str
    knowledge: PreferenceKnowledge
    explicit_overrides: tuple[str, ...] = ()
    owner: str | None = None
    evidence_applicable: bool = True
    relational_requirements: tuple[RelationalRequirement, ...] = ()

    def __post_init__(self) -> None:
        if self.claim_id in self.explicit_overrides:
            raise ValueError("a profile claim cannot override itself")

    @property
    def path(self) -> PropertyPath:
        return PropertyPath(self.section, self.knowledge.dimension)


@dataclass(frozen=True)
class CompositionTarget:
    represented_subject: str
    scope_identities: Mapping[str, str]
    domain: str
    context: Mapping[str, str]
    validation_conditions: tuple[str, ...]
    exposed_properties: Mapping[str, tuple[str, ...]]
    property_owners: Mapping[PropertyPath, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TransferPolicy:
    source_domains: tuple[str, ...]
    confidence_factor: float
    allow_distant_context: bool = False

    def __post_init__(self) -> None:
        if not 0 < self.confidence_factor < 1:
            raise ValueError("transfer confidence factor must be between 0 and 1")


@dataclass(frozen=True)
class ProfileSelection:
    sections: tuple[str, ...] | None = None
    properties: tuple[PropertyPath, ...] | None = None
    scopes: tuple[ScopeIdentity, ...] | None = None

    def __post_init__(self) -> None:
        if self.sections is not None and self.properties is not None:
            raise ValueError("select sections or properties, not both")


@dataclass(frozen=True)
class CompositionRequest:
    target: CompositionTarget
    properties: tuple[ProfileProperty, ...]
    selection: ProfileSelection = field(default_factory=ProfileSelection)
    transfer_policy: TransferPolicy | None = None
    authority: tuple[AuthorityScope, ...] = ()


@dataclass(frozen=True)
class CompositionConflict:
    path: PropertyPath
    claim_ids: tuple[str, ...]
    inputs: tuple[ProfileProperty, ...]
    reason: str
    related_paths: tuple[PropertyPath, ...] = ()
    actual_source: GoverningSource | None = None


@dataclass(frozen=True)
class ComposedProperty:
    path: PropertyPath
    direction: str | None
    claim_ids: tuple[str, ...]
    contributions: tuple[ProfileProperty, ...]
    relationships: Mapping[str, str]
    relational_requirements: tuple[RelationalRequirement, ...]
    effective_confidences: Mapping[str, float]
    confidence_adjustments: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class ExcludedProfileProperty:
    property: ProfileProperty
    reason: str


@dataclass(frozen=True)
class OverriddenProfileProperty:
    property: ProfileProperty
    overridden_by_claim_id: str


@dataclass(frozen=True)
class ExcludedAuthorityScope:
    authority: AuthorityScope
    reason: str


@dataclass(frozen=True)
class CompositionResult:
    properties: Mapping[PropertyPath, ComposedProperty]
    conflicts: tuple[CompositionConflict, ...]
    provenance: tuple[Provenance, ...]
    excluded: tuple[ExcludedProfileProperty, ...]
    overridden: tuple[OverriddenProfileProperty, ...]
    alignment_authority: tuple[AuthorityScope, ...]
    excluded_authority: tuple[ExcludedAuthorityScope, ...]

    @property
    def alignment_taste(self) -> tuple[PreferenceKnowledge, ...]:
        """Return applicable, transfer-adjusted knowledge for AlignmentRequest.taste."""
        return tuple(
            replace(
                contribution.knowledge,
                dimension=composed.path.alignment_dimension,
                confidence=composed.effective_confidences[contribution.claim_id],
            )
            for composed in self.properties.values()
            for contribution in composed.contributions
        )

    @property
    def alignment_dimensions(self) -> tuple[str, ...]:
        """Return qualified dimensions, including relationships and conflicts."""
        dimensions: list[str] = []
        for path, composed in self.properties.items():
            if path.alignment_dimension not in dimensions:
                dimensions.append(path.alignment_dimension)
            for requirement in composed.relational_requirements:
                required_dimension = (
                    requirement.property_path.alignment_dimension
                )
                if required_dimension not in dimensions:
                    dimensions.append(required_dimension)
        for conflict in self.conflicts:
            conflict_dimension = conflict.path.alignment_dimension
            if conflict_dimension not in dimensions:
                dimensions.append(conflict_dimension)
        return tuple(dimensions)

    def context_revision(self, host_revision: str = "initial") -> str:
        """Bind typed relationship state into AlignmentRequest freshness."""
        relationship_state = [
            {
                "source": list(path),
                "claims": list(composed.claim_ids),
                "requirements": [
                    {
                        "property": list(requirement.property_path),
                        "direction": requirement.direction,
                    }
                    for requirement in composed.relational_requirements
                ],
            }
            for path, composed in sorted(self.properties.items())
            if composed.relational_requirements
        ]
        canonical = json.dumps(
            {
                "host_revision": host_revision,
                "profile_relationships": relationship_state,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RelationalAlignmentResult:
    alignment: ActiveAlignmentResult
    conflicts: tuple[CompositionConflict, ...]


@dataclass(frozen=True)
class ScopeTransition:
    operation: ScopeOperation | str
    source_identity: str
    target_identity: str
    outcome: ScopeOutcome | str

    def __post_init__(self) -> None:
        try:
            operation = ScopeOperation(self.operation)
        except ValueError as error:
            raise ValueError(
                f"unsupported local scope operation: {self.operation}"
            ) from error
        try:
            outcome = ScopeOutcome(self.outcome)
        except ValueError as error:
            raise ValueError(
                f"unsupported local scope outcome: {self.outcome}"
            ) from error
        object.__setattr__(self, "operation", operation)
        object.__setattr__(self, "outcome", outcome)
        if (
            outcome is ScopeOutcome.PRESERVE
            and self.target_identity != self.source_identity
        ):
            raise ValueError("preserved local scope must retain its identity")
        if (
            outcome is ScopeOutcome.REPLACE
            and self.target_identity == self.source_identity
        ):
            raise ValueError("replacement requires a new local identity")


@dataclass(frozen=True)
class ScopeTransitionResult:
    status: ScopeTransitionStatus
    source_property: ProfileProperty
    target_property: ProfileProperty | None
    checkpoint: str | None = None


def transition_local_scope(
    profile_property: ProfileProperty,
    transition: ScopeTransition,
) -> ScopeTransitionResult:
    """Apply an explicit local identity outcome without inventing copy semantics."""
    scope = profile_property.knowledge.scope
    if scope.kind != "local":
        raise ValueError(
            "only local profile properties have artifact identity transitions"
        )
    if scope.identity != transition.source_identity:
        raise ValueError(
            "transition source does not match the property's local identity"
        )
    if transition.outcome is ScopeOutcome.AMBIGUOUS:
        return ScopeTransitionResult(
            status=ScopeTransitionStatus.AMBIGUOUS,
            source_property=profile_property,
            target_property=None,
            checkpoint=(
                "resolve-local-scope:"
                f"{ScopeOperation(transition.operation).value}:"
                f"{profile_property.claim_id}"
            ),
        )
    if transition.outcome is ScopeOutcome.PRESERVE:
        return ScopeTransitionResult(
            status=ScopeTransitionStatus.PRESERVED,
            source_property=profile_property,
            target_property=profile_property,
        )

    target_scope = replace(scope, identity=transition.target_identity)
    target_knowledge = replace(profile_property.knowledge, scope=target_scope)
    target_property = replace(
        profile_property,
        claim_id=f"{profile_property.claim_id}@{transition.target_identity}",
        knowledge=target_knowledge,
    )
    return ScopeTransitionResult(
        status=ScopeTransitionStatus.REPLACED,
        source_property=profile_property,
        target_property=target_property,
    )


def _is_exposed(
    profile_property: ProfileProperty,
    target: CompositionTarget,
) -> bool:
    return profile_property.knowledge.dimension in target.exposed_properties.get(
        profile_property.section, ()
    )


def _cross_domain_transfer_allowed(
    profile_property: ProfileProperty,
    policy: TransferPolicy | None,
) -> bool:
    return (
        policy is not None
        and profile_property.knowledge.validation_context.domain
        in policy.source_domains
    )


def _scope_applies(
    profile_property: ProfileProperty,
    target: CompositionTarget,
    policy: TransferPolicy | None,
) -> bool:
    scope = profile_property.knowledge.scope
    return (
        scope.represented_subject == target.represented_subject
        and (
            target.scope_identities.get(scope.kind) == scope.identity
            or (
                scope.kind == "domain"
                and _cross_domain_transfer_allowed(profile_property, policy)
            )
        )
    )


def _context_applies(
    profile_property: ProfileProperty,
    target: CompositionTarget,
) -> bool:
    return all(
        target.context.get(key) == value
        for key, value in profile_property.knowledge.context.items()
    )


def _ownership_applies(
    profile_property: ProfileProperty,
    target: CompositionTarget,
) -> bool:
    expected_owner = target.property_owners.get(profile_property.path)
    return (
        profile_property.owner is None
        or profile_property.owner == expected_owner
    )


def _is_selected(
    profile_property: ProfileProperty,
    selection: ProfileSelection,
) -> bool:
    if selection.sections is not None:
        return profile_property.section in selection.sections
    if selection.properties is not None:
        return profile_property.path in selection.properties
    return True


def _scope_is_selected(
    kind: str,
    identity: str,
    selection: ProfileSelection,
) -> bool:
    return selection.scopes is None or ScopeIdentity(kind, identity) in selection.scopes


def _exclusion_reason(
    profile_property: ProfileProperty,
    target: CompositionTarget,
    selection: ProfileSelection,
    transfer_policy: TransferPolicy | None,
) -> str | None:
    scope = profile_property.knowledge.scope
    if not _scope_is_selected(scope.kind, scope.identity, selection):
        return "scope is outside the requested application"
    if not _is_selected(profile_property, selection):
        return "property is outside the requested application"
    if not profile_property.evidence_applicable:
        return "supporting evidence is not applicable"
    if not _is_exposed(profile_property, target):
        return "the target domain does not expose this property"
    if (
        profile_property.knowledge.scope.represented_subject
        != target.represented_subject
    ):
        return "represented subject does not match this decision"
    if not _scope_applies(profile_property, target, transfer_policy):
        return "scope identity is not active for this decision"
    if (
        profile_property.knowledge.validation_context.domain != target.domain
        and not _cross_domain_transfer_allowed(profile_property, transfer_policy)
    ):
        return "validation domain does not apply to this decision"
    validation_conditions = set(
        profile_property.knowledge.validation_context.conditions
    )
    distant_context = not validation_conditions.issubset(target.validation_conditions)
    cross_domain = profile_property.knowledge.validation_context.domain != target.domain
    if distant_context and not (
        (
            cross_domain
            and _cross_domain_transfer_allowed(profile_property, transfer_policy)
        )
        or (
            not cross_domain
            and transfer_policy is not None
            and transfer_policy.allow_distant_context
        )
    ):
        return "validation context does not support direct reuse"
    if not _context_applies(profile_property, target):
        return "profile context does not apply to this decision"
    if (
        profile_property.owner is not None
        and profile_property.path not in target.property_owners
    ):
        return "property ownership is not established for this decision"
    if not _ownership_applies(profile_property, target):
        return "property owner does not match the active owner"
    return None


def _authority_exclusion_reason(
    authority: AuthorityScope,
    target: CompositionTarget,
    selection: ProfileSelection,
) -> str | None:
    if not _scope_is_selected(
        authority.scope.kind,
        authority.scope.identity,
        selection,
    ):
        return "scope is outside the requested application"
    if authority.scope.represented_subject != target.represented_subject:
        return "represented subject does not match this decision"
    if target.scope_identities.get(authority.scope.kind) != authority.scope.identity:
        return "scope identity is not active for this decision"
    return None


def _apply_explicit_overrides(
    candidates: tuple[ProfileProperty, ...],
) -> tuple[tuple[ProfileProperty, ...], tuple[OverriddenProfileProperty, ...]]:
    overridden = {
        claim_id
        for candidate in candidates
        for claim_id in candidate.explicit_overrides
    }
    remaining = tuple(
        candidate for candidate in candidates if candidate.claim_id not in overridden
    )
    if not remaining:
        return candidates, ()
    records = tuple(
        OverriddenProfileProperty(
            property=candidate,
            overridden_by_claim_id=overriding_candidate.claim_id,
        )
        for candidate in candidates
        if candidate.claim_id in overridden
        for overriding_candidate in remaining
        if candidate.claim_id in overriding_candidate.explicit_overrides
    )
    return remaining, records


def _semantic_fingerprint(profile_property: ProfileProperty) -> object:
    knowledge = profile_property.knowledge
    return knowledge.disposition, knowledge.direction


def _relationships_are_compatible(candidates: tuple[ProfileProperty, ...]) -> bool:
    values: dict[str, str] = {}
    for candidate in candidates:
        for relationship, value in candidate.knowledge.relationships.items():
            existing = values.get(relationship)
            if existing is not None and existing != value:
                return False
            values[relationship] = value
    return True


def _relationships(candidates: tuple[ProfileProperty, ...]) -> dict[str, str]:
    return {
        relationship: value
        for candidate in candidates
        for relationship, value in candidate.knowledge.relationships.items()
    }


def _relational_requirements(
    candidates: tuple[ProfileProperty, ...],
) -> tuple[RelationalRequirement, ...]:
    requirements: list[RelationalRequirement] = []
    for candidate in candidates:
        for requirement in candidate.relational_requirements:
            if requirement not in requirements:
                requirements.append(requirement)
    return tuple(requirements)


def _confidence_adjustments(
    profile_property: ProfileProperty,
    target: CompositionTarget,
) -> tuple[str, ...]:
    adjustments: list[str] = []
    validation = profile_property.knowledge.validation_context
    if validation.domain != target.domain:
        adjustments.append("cross-domain transfer")
    if not set(validation.conditions).issubset(target.validation_conditions):
        adjustments.append("distant validation context")
    return tuple(adjustments)


def _relational_alignment_conflicts(
    composition: CompositionResult,
    alignment: ActiveAlignmentResult,
) -> tuple[CompositionConflict, ...]:
    conflicts: list[CompositionConflict] = []
    seen: set[tuple[PropertyPath, PropertyPath]] = set()
    for source_path, composed in composition.properties.items():
        dependent_resolution = alignment.dimensions.get(
            source_path.alignment_dimension
        )
        if (
            dependent_resolution is None
            or dependent_resolution.governing_source is not GoverningSource.TASTE
            or dependent_resolution.direction != composed.direction
        ):
            continue
        for requirement in composed.relational_requirements:
            required_path = requirement.property_path
            required_resolution = alignment.dimensions.get(
                required_path.alignment_dimension
            )
            conflict_key = source_path, required_path
            if (
                required_resolution is not None
                and required_resolution.direction == requirement.direction
                and required_resolution.governing_source
                not in {None, GoverningSource.CONFLICT}
            ) or conflict_key in seen:
                continue
            seen.add(conflict_key)
            inputs_by_id: dict[str, ProfileProperty] = {}
            required_property = composition.properties.get(required_path)
            required_contributions = (
                required_property.contributions
                if required_property is not None
                else ()
            )
            for candidate in composed.contributions + required_contributions:
                inputs_by_id.setdefault(candidate.claim_id, candidate)
            inputs = tuple(inputs_by_id.values())
            actual_direction = (
                required_resolution.direction
                if required_resolution is not None
                and required_resolution.direction is not None
                else "unresolved"
            )
            conflicts.append(
                CompositionConflict(
                    path=source_path,
                    claim_ids=tuple(candidate.claim_id for candidate in inputs),
                    inputs=inputs,
                    reason=(
                        "relational requirement requires "
                        f"{required_path[0]}.{required_path[1]}="
                        f"{requirement.direction}, got {actual_direction}"
                    ),
                    related_paths=(source_path, required_path),
                    actual_source=(
                        required_resolution.governing_source
                        if required_resolution is not None
                        else None
                    ),
                )
            )
    return tuple(conflicts)


def enforce_relational_alignment(
    composition: CompositionResult,
    alignment: ActiveAlignmentResult,
) -> RelationalAlignmentResult:
    """Validate profile relationships against full canonical alignment state."""
    current_alignment = alignment
    all_conflicts: list[CompositionConflict] = []
    seen_conflicts: set[tuple[PropertyPath, PropertyPath]] = set()
    while True:
        new_conflicts = tuple(
            conflict
            for conflict in _relational_alignment_conflicts(
                composition,
                current_alignment,
            )
            if (conflict.path, conflict.related_paths[-1]) not in seen_conflicts
        )
        if not new_conflicts:
            break

        dimensions = dict(current_alignment.dimensions)
        unresolved = list(current_alignment.unresolved_dimensions)
        checkpoints = list(current_alignment.checkpoint_obligations)
        for conflict in new_conflicts:
            seen_conflicts.add((conflict.path, conflict.related_paths[-1]))
            all_conflicts.append(conflict)
            dependent_dimension = conflict.path.alignment_dimension
            resolution = dimensions.get(dependent_dimension)
            if resolution is not None:
                dimensions[dependent_dimension] = replace(
                    resolution,
                    direction=None,
                    governing_source=GoverningSource.CONFLICT,
                    reason=conflict.reason,
                )
            if dependent_dimension not in unresolved:
                unresolved.append(dependent_dimension)
            checkpoint = f"resolve-relation:{dependent_dimension}"
            if current_alignment.material and checkpoint not in checkpoints:
                checkpoints.append(checkpoint)

        current_alignment = replace(
            current_alignment,
            dimensions=dimensions,
            unresolved_dimensions=tuple(unresolved),
            propagation_eligible=False,
            checkpoint_obligations=tuple(checkpoints),
        )

    return RelationalAlignmentResult(
        alignment=current_alignment,
        conflicts=tuple(all_conflicts),
    )


def compose_profiles(request: CompositionRequest) -> CompositionResult:
    """Compose only applicable profile properties; preserve conflicts and provenance."""
    applicable: list[ProfileProperty] = []
    excluded: list[ExcludedProfileProperty] = []
    for profile_property in request.properties:
        reason = _exclusion_reason(
            profile_property,
            request.target,
            request.selection,
            request.transfer_policy,
        )
        if reason is None:
            applicable.append(profile_property)
        else:
            excluded.append(
                ExcludedProfileProperty(
                    property=profile_property,
                    reason=reason,
                )
            )

    applicable_authority: list[AuthorityScope] = []
    excluded_authority: list[ExcludedAuthorityScope] = []
    for authority in request.authority:
        reason = _authority_exclusion_reason(
            authority,
            request.target,
            request.selection,
        )
        if reason is None:
            applicable_authority.append(authority)
        else:
            excluded_authority.append(
                ExcludedAuthorityScope(authority=authority, reason=reason)
            )
    grouped: dict[PropertyPath, list[ProfileProperty]] = {}
    for profile_property in applicable:
        grouped.setdefault(profile_property.path, []).append(profile_property)

    properties: dict[PropertyPath, ComposedProperty] = {}
    conflicts: list[CompositionConflict] = []
    provenance: list[Provenance] = []
    overridden: list[OverriddenProfileProperty] = []
    for path, grouped_candidates in grouped.items():
        candidates, override_records = _apply_explicit_overrides(
            tuple(grouped_candidates)
        )
        overridden.extend(override_records)
        fingerprints = {_semantic_fingerprint(candidate) for candidate in candidates}
        if len(fingerprints) != 1 or not _relationships_are_compatible(candidates):
            conflicts.append(
                CompositionConflict(
                    path=path,
                    claim_ids=tuple(candidate.claim_id for candidate in candidates),
                    inputs=candidates,
                    reason="semantically incompatible applicable knowledge",
                    related_paths=(path,),
                )
            )
            continue
        direction = candidates[0].knowledge.direction
        properties[path] = ComposedProperty(
            path=path,
            direction=direction,
            claim_ids=tuple(candidate.claim_id for candidate in candidates),
            contributions=candidates,
            relationships=_relationships(candidates),
            relational_requirements=_relational_requirements(candidates),
            effective_confidences={
                candidate.claim_id: (
                    candidate.knowledge.confidence
                    * request.transfer_policy.confidence_factor
                    if _confidence_adjustments(candidate, request.target)
                    and request.transfer_policy is not None
                    else candidate.knowledge.confidence
                )
                for candidate in candidates
            },
            confidence_adjustments={
                candidate.claim_id: adjustments
                for candidate in candidates
                if (adjustments := _confidence_adjustments(candidate, request.target))
            },
        )
        for candidate in candidates:
            for record in candidate.knowledge.provenance:
                if record not in provenance:
                    provenance.append(record)

    return CompositionResult(
        properties=properties,
        conflicts=tuple(conflicts),
        provenance=tuple(provenance),
        excluded=tuple(excluded),
        overridden=tuple(overridden),
        alignment_authority=tuple(applicable_authority),
        excluded_authority=tuple(excluded_authority),
    )
