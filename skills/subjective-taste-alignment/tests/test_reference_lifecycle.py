"""Behavioral scenarios for live and pinned reference lifecycles."""

from __future__ import annotations

import pytest

from evidence_reconciliation import Fidelity
from alignment_contract import Scope
from profile_persistence import ReferenceFreshness, ReferenceMode, ReferenceSource
from reference_style import (
    ObservedReferenceProperty,
    ReferenceInstruction,
    ReferenceOrigin,
    ReferenceRequestKind,
    decisions_depending_on,
    derive_reference_style,
    observe_live_state,
    reference_dependency,
    validate_against_reference,
    verify_pinned_state,
)


PROJECT_SCOPE = Scope(kind="project", identity="project-a", represented_subject="user-1")


def _pinned(**overrides: object) -> ReferenceSource:
    values: dict[str, object] = {
        "reference_id": "ref:pinned-site",
        "source_identity": "artifact:settings-screen",
        "locator": "workspace/settings-screen",
        "mode": ReferenceMode.PINNED,
        "freshness": ReferenceFreshness.CURRENT,
        "source_revision": "rev-7",
        "derived_claim_ids": ("reference-intent:typography.expression",),
    }
    values.update(overrides)
    return ReferenceSource(**values)  # type: ignore[arg-type]


def _live(**overrides: object) -> ReferenceSource:
    values: dict[str, object] = {
        "reference_id": "ref:live-project-style",
        "source_identity": "artifact:project-homepage",
        "locator": "workspace/project-homepage",
        "mode": ReferenceMode.LIVE,
        "freshness": ReferenceFreshness.CURRENT,
        "source_revision": "rev-3",
        "derived_claim_ids": (
            "reference-intent:layout.density",
            "reference-intent:motion.transition",
        ),
    }
    values.update(overrides)
    return ReferenceSource(**values)  # type: ignore[arg-type]


def test_derivation_records_the_observed_source_state_per_property() -> None:
    derivation = derive_reference_style(
        ReferenceInstruction(
            instruction_id="instruction:match-settings",
            kind=ReferenceRequestKind.MATCH,
            scope=PROJECT_SCOPE,
            target_dimensions=("typography.expression",),
        ),
        _pinned(),
        (
            ObservedReferenceProperty(
                dimension="typography.expression",
                direction="restrained grotesque",
                fidelity=Fidelity.HIGH,
            ),
        ),
    )

    assert derivation.binding.source_identity == "artifact:settings-screen"
    assert derivation.binding.source_revision == "rev-7"
    provenance_ids = {
        record.source_id
        for directive in derivation.intent_directives
        for record in directive.provenance
    }
    assert any("@rev-7" in item for item in provenance_ids)
    assert all(
        directive.dependencies == ("reference:ref:pinned-site",)
        for directive in derivation.intent_directives
    )


def test_pinned_reference_stays_bound_when_the_locator_serves_new_content() -> None:
    reference = _pinned()
    check = verify_pinned_state(reference, observed_revision="rev-9")

    assert check.source_changed is True
    assert check.verifiable is True
    assert check.resulting_freshness is ReferenceFreshness.UNKNOWN
    assert check.stale_claim_ids == ("reference-intent:typography.expression",)
    # The pin does not move: identity and revision stay at the observed state.
    assert check.binding.source_revision == "rev-7"
    assert check.binding.source_identity == "artifact:settings-screen"
    assert "different content" in check.reason


def test_unverifiable_pinned_source_becomes_explicitly_unknown() -> None:
    check = verify_pinned_state(_pinned(), observed_revision=None)

    assert check.source_changed is None
    assert check.verifiable is False
    assert check.resulting_freshness is ReferenceFreshness.UNKNOWN
    assert check.stale_claim_ids == ("reference-intent:typography.expression",)

    # Material reuse of derived knowledge requires revalidation.
    observation = ObservedReferenceProperty(
        dimension="typography.expression",
        direction="restrained grotesque",
        fidelity=Fidelity.HIGH,
    )
    with pytest.raises(ValueError, match="unknown"):
        validate_against_reference(observation, check.binding)


def test_pinned_source_with_matching_revision_stays_current() -> None:
    check = verify_pinned_state(_pinned(), observed_revision="rev-7")

    assert check.source_changed is False
    assert check.verifiable is True
    assert check.previous_freshness is ReferenceFreshness.CURRENT
    assert check.resulting_freshness is ReferenceFreshness.CURRENT
    assert check.stale_claim_ids == ()
    assert check.binding.freshness is ReferenceFreshness.CURRENT


def test_verify_pinned_state_rejects_live_references() -> None:
    with pytest.raises(ValueError, match="pinned"):
        verify_pinned_state(_live())


def test_live_change_marks_only_its_own_derived_claims_stale() -> None:
    typography = _pinned()
    style = _live()
    typography_check = verify_pinned_state(typography, observed_revision="rev-7")
    style_check = observe_live_state(style, observed_revision="rev-4")

    assert style_check.source_changed is True
    assert style_check.verifiable is True
    assert style_check.resulting_freshness is ReferenceFreshness.STALE
    assert style_check.stale_claim_ids == (
        "reference-intent:layout.density",
        "reference-intent:motion.transition",
    )
    assert typography_check.stale_claim_ids == ()
    assert typography_check.binding.freshness is ReferenceFreshness.CURRENT


def test_live_reference_without_revision_signal_requires_revalidation() -> None:
    check = observe_live_state(_live(), observed_revision=None)

    assert check.source_changed is None
    assert check.verifiable is False
    assert check.resulting_freshness is ReferenceFreshness.UNKNOWN
    assert "revalidat" in check.reason
    assert check.stale_claim_ids == (
        "reference-intent:layout.density",
        "reference-intent:motion.transition",
    )

    observation = ObservedReferenceProperty(
        dimension="layout.density",
        direction="dense",
        fidelity=Fidelity.HIGH,
    )
    with pytest.raises(ValueError, match="unknown"):
        validate_against_reference(observation, check.binding)


def test_live_reference_with_matching_revision_stays_current() -> None:
    check = observe_live_state(_live(), observed_revision="rev-3")

    assert check.source_changed is False
    assert check.resulting_freshness is ReferenceFreshness.CURRENT
    assert check.stale_claim_ids == ()


def test_observe_live_state_rejects_pinned_references() -> None:
    with pytest.raises(ValueError, match="live"):
        observe_live_state(_pinned(), observed_revision="rev-7")


def test_only_actual_dependents_are_flagged_for_reference_rework() -> None:
    dependencies_by_decision = {
        "decision:new-button": ("reference:ref:live-project-style", "other:input"),
        "decision:footer": ("reference:ref:pinned-site",),
        "decision:hero": (),
    }

    assert decisions_depending_on(
        dependencies_by_decision, "ref:live-project-style"
    ) == ("decision:new-button",)
    assert decisions_depending_on(dependencies_by_decision, "ref:unknown") == ()
    assert (
        reference_dependency("ref:live-project-style")
        == "reference:ref:live-project-style"
    )


def test_pinned_style_never_tracks_the_evolved_project_style() -> None:
    pinned_heritage = _pinned()
    live_style = _live()

    # The project style evolves behind both locators.
    evolved_live = observe_live_state(live_style, observed_revision="rev-8")
    assert evolved_live.source_changed is True

    heritage_instruction = ReferenceInstruction(
        instruction_id="instruction:heritage-page",
        kind=ReferenceRequestKind.MIMIC,
        scope=Scope(
            kind="project", identity="project-b", represented_subject="user-1"
        ),
        target_dimensions=("typography.expression",),
    )
    heritage_derivation = derive_reference_style(
        heritage_instruction,
        pinned_heritage,
        (
            ObservedReferenceProperty(
                dimension="typography.expression",
                direction="restrained grotesque",
                fidelity=Fidelity.HIGH,
            ),
        ),
    )
    # The pinned reference reproduces its fixed source state, not the
    # evolved project style, and its binding never adopted rev-8.
    assert heritage_derivation.included[0].direction == "restrained grotesque"
    assert heritage_derivation.binding.source_revision == "rev-7"
    assert heritage_derivation.binding.mode is ReferenceMode.PINNED


def test_project_consistency_origin_keeps_tracking_through_a_live_binding() -> None:
    derivation = derive_reference_style(
        ReferenceInstruction(
            instruction_id="instruction:stay-consistent",
            kind=ReferenceRequestKind.REMAIN_CONSISTENT,
            origin=ReferenceOrigin.PROJECT_CONSISTENCY,
            scope=PROJECT_SCOPE,
            target_dimensions=("layout.density",),
        ),
        _live(source_revision="rev-3"),
        (
            ObservedReferenceProperty(
                dimension="layout.density",
                direction="airy",
                fidelity=Fidelity.HIGH,
            ),
        ),
    )
    before = derivation.binding

    after_change = observe_live_state(before, observed_revision="rev-5")
    assert after_change.source_changed is True
    assert after_change.resulting_freshness is ReferenceFreshness.STALE
    # Re-derivation binds the refreshed source state for continued tracking.
    refreshed = derive_reference_style(
        ReferenceInstruction(
            instruction_id="instruction:stay-consistent",
            kind=ReferenceRequestKind.REMAIN_CONSISTENT,
            origin=ReferenceOrigin.PROJECT_CONSISTENCY,
            scope=PROJECT_SCOPE,
            target_dimensions=("layout.density",),
        ),
        after_change.binding,
        (
            ObservedReferenceProperty(
                dimension="layout.density",
                direction="denser grid",
                fidelity=Fidelity.HIGH,
            ),
        ),
    )
    assert refreshed.included[0].direction == "denser grid"
