"""Behavioral scenarios for reference-derived style profiles."""

from __future__ import annotations

import pytest

from alignment_contract import (
    AlignmentRequest,
    GoverningSource,
    Provenance,
    Scope,
    resolve_alignment,
)
from decision_policy import (
    AuthorityScope,
    DecisionContext,
    DecisionLevel,
    PolicyRequest,
    PropagationRoute,
    autonomy_snapshot,
)
from evidence_reconciliation import Fidelity
from profile_persistence import ReferenceFreshness, ReferenceMode, ReferenceSource
from reference_style import (
    ObservedReferenceProperty,
    PropertyStatus,
    ReferenceInstruction,
    ReferenceOrigin,
    ReferenceRequestKind,
    classify_reference_request,
    derive_reference_style,
    validate_against_reference,
)


PROJECT_SCOPE = Scope(kind="project", identity="project-a", represented_subject="user-1")


def _reference(**overrides: object) -> ReferenceSource:
    values: dict[str, object] = {
        "reference_id": "ref:settings-ui",
        "source_identity": "artifact:settings-screen",
        "locator": "workspace/settings-screen",
        "mode": ReferenceMode.PINNED,
        "freshness": ReferenceFreshness.CURRENT,
        "source_revision": "rev-7",
    }
    values.update(overrides)
    return ReferenceSource(**values)  # type: ignore[arg-type]


def _instruction(
    kind: ReferenceRequestKind = ReferenceRequestKind.MATCH,
    *,
    target_dimensions: tuple[str, ...] = ("typography.expression",),
) -> ReferenceInstruction:
    return ReferenceInstruction(
        instruction_id="instruction:match-settings",
        kind=kind,
        scope=PROJECT_SCOPE,
        target_dimensions=target_dimensions,
    )


def _observed() -> tuple[ObservedReferenceProperty, ...]:
    return (
        ObservedReferenceProperty(
            dimension="typography.expression",
            direction="restrained grotesque",
            fidelity=Fidelity.HIGH,
        ),
        ObservedReferenceProperty(
            dimension="color.palette",
            direction="cool neutrals",
            fidelity=Fidelity.HIGH,
        ),
    )


@pytest.mark.parametrize("kind", list(ReferenceRequestKind))
def test_explicit_reference_requests_route_through_derivation(
    kind: ReferenceRequestKind,
) -> None:
    derivation = derive_reference_style(
        _instruction(kind), _reference(), _observed()
    )
    assert derivation.included
    assert derivation.binding.reference_id == "ref:settings-ui"

    with pytest.raises(ValueError):
        ReferenceInstruction(
            instruction_id="instruction:other",
            kind="vibes-based",
            scope=PROJECT_SCOPE,
        )


def test_classify_rejects_non_reference_requests() -> None:
    assert (
        classify_reference_request("keep this consistent with the settings UI")
        is ReferenceRequestKind.REMAIN_CONSISTENT
    )
    with pytest.raises(ValueError):
        classify_reference_request("make it pop more")


def test_user_selected_reference_governs_only_the_requested_scope() -> None:
    derivation = derive_reference_style(
        _instruction(target_dimensions=("typography.expression",)),
        _reference(),
        _observed(),
    )

    included_dimensions = [item.dimension for item in derivation.included]
    excluded_dimensions = [item.dimension for item in derivation.excluded]
    assert included_dimensions == ["typography.expression"]
    assert excluded_dimensions == ["color.palette"]
    typography = derivation.included[0]
    assert typography.status is PropertyStatus.EXPLICIT_REQUEST
    assert not derivation.direction_selection_required
    assert len(derivation.intent_directives) == 1


def test_whole_style_request_includes_only_sufficiently_represented_properties() -> None:
    observed = (
        ObservedReferenceProperty(
            dimension="layout.density",
            direction="airy",
            fidelity=Fidelity.HIGH,
        ),
        ObservedReferenceProperty(
            dimension="motion.transition",
            direction="springy",
            fidelity=Fidelity.LOW,
        ),
    )
    derivation = derive_reference_style(
        _instruction(target_dimensions=()),
        _reference(),
        observed,
    )

    assert [item.dimension for item in derivation.included] == ["layout.density"]
    assert derivation.included[0].status is PropertyStatus.INFERRED_SIMILARITY
    motion = derivation.excluded[0]
    assert motion.dimension == "motion.transition"
    assert "strongly enough" in motion.reason
    # No dimension is manufactured beyond what the reference exposes.
    assert len(derivation.included) + len(derivation.excluded) == len(observed)


def test_ambiguous_project_consistency_requires_direction_selection_first() -> None:
    ambiguous = derive_reference_style(
        ReferenceInstruction(
            instruction_id="instruction:consistent",
            kind=ReferenceRequestKind.REMAIN_CONSISTENT,
            origin=ReferenceOrigin.PROJECT_CONSISTENCY,
            scope=PROJECT_SCOPE,
        ),
        _reference(reference_id="ref:project-style"),
        (ObservedReferenceProperty("layout.density", "dense", Fidelity.HIGH),),
        project_style_candidates=("marketing-pages style", "tooling-console style"),
    )
    assert ambiguous.direction_selection_required is True
    assert ambiguous.included == ()
    assert all(
        "unresolved" in item.reason for item in ambiguous.excluded
    )

    single_candidate = derive_reference_style(
        ReferenceInstruction(
            instruction_id="instruction:consistent",
            kind=ReferenceRequestKind.REMAIN_CONSISTENT,
            origin=ReferenceOrigin.PROJECT_CONSISTENCY,
            scope=PROJECT_SCOPE,
        ),
        _reference(reference_id="ref:project-style"),
        (ObservedReferenceProperty("layout.density", "dense", Fidelity.HIGH),),
        project_style_candidates=("tooling-console style",),
    )
    assert single_candidate.direction_selection_required is False
    assert len(single_candidate.included) == 1


def test_derived_intent_governs_without_becoming_user_taste() -> None:
    derivation = derive_reference_style(
        _instruction(target_dimensions=("typography.expression",)),
        _reference(),
        _observed(),
    )
    request = AlignmentRequest(
        decision_id="decision:new-button",
        dimensions=("typography.expression", "color.palette"),
        material=True,
        intent=derivation.intent_directives,
    )
    resolved = resolve_alignment(request)

    typography = resolved.dimensions["typography.expression"]
    assert typography.governing_source is GoverningSource.INTENT
    assert typography.direction == "restrained grotesque"
    # The unmentioned dimension stays unresolved; nothing was inferred for it.
    assert "color.palette" in resolved.unresolved_dimensions
    assert request.taste == ()


def test_derivation_retains_the_instruction_scope_on_directives() -> None:
    derivation = derive_reference_style(
        _instruction(target_dimensions=("typography.expression",)),
        _reference(),
        _observed(),
    )

    assert derivation.scope is PROJECT_SCOPE
    assert all(
        directive.scope is PROJECT_SCOPE
        for directive in derivation.intent_directives
    )


def test_validate_against_reference_rejects_unusable_sources() -> None:
    observation = _observed()[0]
    validate_against_reference(observation, _reference())  # current: usable

    with pytest.raises(ValueError, match="stale"):
        validate_against_reference(
            observation,
            _reference(freshness=ReferenceFreshness.STALE),
        )
    with pytest.raises(ValueError, match="unknown"):
        validate_against_reference(
            observation,
            _reference(freshness=ReferenceFreshness.UNKNOWN),
        )
    with pytest.raises(ValueError, match="locator"):
        validate_against_reference(observation, _reference(locator=""))
    with pytest.raises(ValueError, match="identity"):
        validate_against_reference(
            observation, _reference(source_identity="")
        )


def test_multi_reference_composition_stays_intent_and_never_taste() -> None:
    typography_reference = _reference()
    motion_reference = _reference(
        reference_id="ref:motion-ui",
        source_identity="artifact:motion-screen",
        locator="workspace/motion-screen",
        source_revision="rev-2",
    )
    typography_derivation = derive_reference_style(
        _instruction(target_dimensions=("typography.expression",)),
        typography_reference,
        (
            ObservedReferenceProperty(
                dimension="typography.expression",
                direction="restrained grotesque",
                fidelity=Fidelity.HIGH,
            ),
        ),
    )
    motion_instruction = ReferenceInstruction(
        instruction_id="instruction:follow-motion",
        kind=ReferenceRequestKind.FOLLOW,
        scope=PROJECT_SCOPE,
        target_dimensions=("motion.character",),
    )
    motion_derivation = derive_reference_style(
        motion_instruction,
        motion_reference,
        (
            ObservedReferenceProperty(
                dimension="motion.character",
                direction="springy eased",
                fidelity=Fidelity.HIGH,
            ),
        ),
    )

    combined_directives = (
        *typography_derivation.intent_directives,
        *motion_derivation.intent_directives,
    )
    assert len(combined_directives) == 2
    dependencies = {
        dependency
        for directive in combined_directives
        for dependency in directive.dependencies
    }
    assert dependencies == {"reference:ref:settings-ui", "reference:ref:motion-ui"}
    provenance_ids = {
        item.source_id
        for directive in combined_directives
        for item in directive.provenance
    }
    assert any("instruction:match-settings" in item for item in provenance_ids)
    assert any("instruction:follow-motion" in item for item in provenance_ids)

    request = AlignmentRequest(
        decision_id="decision:combined-screen",
        dimensions=("typography.expression", "motion.character"),
        material=True,
        intent=combined_directives,
    )
    resolved = resolve_alignment(request)

    for dimension in ("typography.expression", "motion.character"):
        assert resolved.dimensions[dimension].governing_source is GoverningSource.INTENT
        assert resolved.dimensions[dimension].taste is None
        assert resolved.dimensions[dimension].inputs.taste == ()
    assert resolved.unresolved_dimensions == ()
    assert request.taste == ()
