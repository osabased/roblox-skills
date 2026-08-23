"""Behavioral scenarios for isolated exploration and direction promotion."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from alignment_contract import Scope, ValidationContext
from exploration import (
    AlternativeStatus,
    AddRiff,
    CleanupExploration,
    CombineSelection,
    DelegateSelection,
    DirectionChoice,
    DirectionSource,
    ExplorationAlternative,
    ExplorationMode,
    ExplorationQuestion,
    LearningMode,
    NoveltyBudget,
    RejectAlternatives,
    RequestRiff,
    SelectAlternative,
    StartExploration,
    promotion_evidence_event,
    run_exploration,
)
from evidence_reconciliation import TransitionStatus


def _context() -> ValidationContext:
    return ValidationContext(
        domain="interface-design",
        fidelity="high",
        conditions=("desktop", "settings"),
    )


def _alternative(
    alternative_id: str,
    *,
    density: str,
    typography: str,
    artifacts: tuple[str, ...],
) -> ExplorationAlternative:
    return ExplorationAlternative(
        alternative_id=alternative_id,
        directions=(
            DirectionChoice("layout.density", density),
            DirectionChoice("typography.expression", typography),
        ),
        high_leverage_dimensions=(
            "layout.density",
            "typography.expression",
        ),
        validation_context=_context(),
        artifact_ids=artifacts,
    )


def test_start_isolates_meaningfully_different_representative_alternatives() -> None:
    question = ExplorationQuestion(
        question_id="settings-direction",
        prompt="Which settings direction should govern the screen?",
        high_leverage_dimensions=(
            "layout.density",
            "typography.expression",
        ),
        required_context=_context(),
    )
    alternatives = (
        _alternative(
            "quiet",
            density="comfortable",
            typography="restrained",
            artifacts=("tmp/quiet.png",),
        ),
        _alternative(
            "editorial",
            density="dense",
            typography="expressive",
            artifacts=("tmp/editorial.png",),
        ),
    )

    transition = run_exploration(
        None,
        StartExploration(
            operation_id="start-1",
            exploration_id="explore-settings",
            mode=ExplorationMode.DELIBERATE_DIVERGENCE,
            learning_mode=LearningMode.NON_LEARNING,
            scope=Scope("project", "project-a", "user-1"),
            question=question,
            alternatives=alternatives,
            novelty_budget=NoveltyBudget.RADICAL,
        ),
    )

    assert transition.state.exploration_id == "explore-settings"
    assert transition.state.alternatives == alternatives
    assert transition.state.selection is None
    assert transition.production_candidate is None
    assert transition.evidence_transition is None
    assert transition.state.learning_mode is LearningMode.NON_LEARNING
    with pytest.raises(FrozenInstanceError):
        setattr(transition.state, "exploration_id", "mutated")


def _started_state():
    question = ExplorationQuestion(
        question_id="settings-direction",
        prompt="Which settings direction should govern the screen?",
        high_leverage_dimensions=(
            "layout.density",
            "typography.expression",
        ),
        required_context=_context(),
    )
    return run_exploration(
        None,
        StartExploration(
            operation_id="start-common",
            exploration_id="explore-settings",
            mode=ExplorationMode.CALIBRATION,
            learning_mode=LearningMode.LEARNING,
            scope=Scope("project", "project-a", "user-1"),
            question=question,
            alternatives=(
                _alternative(
                    "quiet",
                    density="comfortable",
                    typography="restrained",
                    artifacts=("tmp/quiet.png",),
                ),
                _alternative(
                    "editorial",
                    density="dense",
                    typography="expressive",
                    artifacts=("tmp/editorial.png",),
                ),
            ),
            novelty_budget=NoveltyBudget.CLOSE,
        ),
    ).state


def test_pick_reject_and_combine_change_only_the_production_selection() -> None:
    state = _started_state()

    rejected = run_exploration(
        state,
        RejectAlternatives("reject-1", ("editorial",)),
    )
    assert rejected.production_candidate is None
    assert rejected.evidence_transition is None
    state = rejected.state
    by_id = {item.alternative_id: item for item in state.alternatives}
    assert by_id["editorial"].status is AlternativeStatus.REJECTED

    picked = run_exploration(
        state,
        SelectAlternative("pick-1", "quiet"),
    )
    assert picked.state.selection is not None
    assert picked.state.selection.alternative_id == "quiet"
    assert picked.production_candidate is not None
    assert picked.production_candidate.alternative_id == "quiet"
    assert picked.evidence_transition is None

    combined = run_exploration(
        picked.state,
        CombineSelection(
            operation_id="combine-1",
            alternative_id="quiet-editorial",
            sources=(
                DirectionSource("layout.density", "quiet"),
                DirectionSource("typography.expression", "editorial"),
            ),
        ),
    )

    assert combined.state.selection is not None
    assert combined.state.selection.alternative_id == "quiet-editorial"
    assert combined.production_candidate is not None
    assert combined.production_candidate.directions == (
        DirectionChoice("layout.density", "comfortable"),
        DirectionChoice("typography.expression", "expressive"),
    )
    assert combined.evidence_transition is None
    assert all(
        item.alternative_id == "quiet-editorial"
        or item.status is not AlternativeStatus.SELECTED
        for item in combined.state.alternatives
    )


def test_preserve_and_riff_uses_novelty_only_for_candidate_generation() -> None:
    state = _started_state()

    requested = run_exploration(
        state,
        RequestRiff(
            operation_id="riff-request-1",
            preserved_sources=(
                DirectionSource("layout.density", "quiet"),
            ),
            novelty_budget=NoveltyBudget.RADICAL,
        ),
    )

    assert requested.generation_request is not None
    assert requested.generation_request.novelty_budget is NoveltyBudget.RADICAL
    assert requested.generation_request.preserved_directions == (
        DirectionChoice("layout.density", "comfortable"),
    )
    assert requested.production_candidate is None
    assert requested.evidence_transition is None
    assert requested.state.novelty_budget is NoveltyBudget.CLOSE

    added = run_exploration(
        requested.state,
        AddRiff(
            operation_id="riff-add-1",
            request_id="riff-request-1",
            alternative=_alternative(
                "quiet-playful",
                density="comfortable",
                typography="playful",
                artifacts=("tmp/quiet-playful.png",),
            ),
        ),
    )

    assert added.state.alternatives[-1].alternative_id == "quiet-playful"
    assert added.state.alternatives[-1].status is AlternativeStatus.CANDIDATE
    assert added.state.pending_riff is None
    assert added.production_candidate is None
    assert added.evidence_transition is None


def _delegation_state():
    started = run_exploration(
        None,
        StartExploration(
            operation_id="start-delegate",
            exploration_id="explore-delegate",
            mode=ExplorationMode.CALIBRATION,
            learning_mode=LearningMode.LEARNING,
            scope=Scope("project", "project-a", "user-1"),
            question=ExplorationQuestion(
                question_id="delegate-question",
                prompt="Which direction should govern?",
                high_leverage_dimensions=("layout.density",),
                required_context=_context(),
            ),
            alternatives=(
                _alternative(
                    "calm",
                    density="comfortable",
                    typography="restrained",
                    artifacts=("tmp/calm.png",),
                ),
                _alternative(
                    "dense",
                    density="compact",
                    typography="restrained",
                    artifacts=("tmp/dense.png",),
                ),
            ),
            novelty_budget=NoveltyBudget.CLOSE,
        ),
    )
    return started.state


def test_delegated_selection_records_delegation_without_taste_status() -> None:
    delegated = run_exploration(
        _delegation_state(),
        DelegateSelection(
            operation_id="delegate-1",
            alternative_id="calm",
        ),
    )

    assert delegated.production_candidate is not None
    intent = delegated.production_candidate
    assert intent.alternative_id == "calm"
    assert intent.selected_by == "user-delegation"
    assert intent.deliberate_divergence is False
    assert delegated.evidence_transition is None
    selection = delegated.state.selection
    assert selection is not None
    assert selection.selected_by == "user-delegation"


def test_cleanup_abandons_dead_ends_without_selection_or_taste_effects() -> None:
    state = _started_state()

    cleaned = run_exploration(
        state,
        CleanupExploration(
            operation_id="cleanup-1",
            alternative_ids=("editorial",),
            reason="stale artifacts; superseded by the settings redesign",
        ),
    )

    by_id = {item.alternative_id: item for item in cleaned.state.alternatives}
    assert by_id["editorial"].status is AlternativeStatus.ABANDONED
    assert cleaned.production_candidate is None
    assert cleaned.evidence_transition is None

    with pytest.raises(ValueError, match="abandoned"):
        run_exploration(
            cleaned.state,
            SelectAlternative("pick-abandoned", "editorial"),
        )
    with pytest.raises(ValueError, match="abandoned"):
        run_exploration(
            cleaned.state,
            DelegateSelection("delegate-abandoned", "editorial"),
        )
    with pytest.raises(ValueError, match="combination source"):
        run_exploration(
            cleaned.state,
            CombineSelection(
                operation_id="combine-cleanup",
                alternative_id="mixed",
                sources=(
                    DirectionSource("layout.density", "quiet"),
                    DirectionSource("typography.expression", "editorial"),
                ),
            ),
        )
    with pytest.raises(ValueError, match="riff source"):
        run_exploration(
            cleaned.state,
            RequestRiff(
                operation_id="riff-cleanup",
                preserved_sources=(
                    DirectionSource("typography.expression", "editorial"),
                ),
            ),
        )
    with pytest.raises(ValueError, match="unknown alternative"):
        run_exploration(
            cleaned.state,
            CleanupExploration("cleanup-missing", ("nope",), "not present"),
        )


def test_the_selected_alternative_cannot_be_abandoned() -> None:
    state = _started_state()
    picked = run_exploration(
        state, SelectAlternative("pick-first", "quiet")
    ).state

    with pytest.raises(ValueError, match="selected"):
        run_exploration(
            picked,
            CleanupExploration(
                operation_id="cleanup-selected",
                alternative_ids=("quiet",),
                reason="superseded",
            ),
        )

    others = run_exploration(
        picked,
        CleanupExploration(
            operation_id="cleanup-other",
            alternative_ids=("editorial",),
            reason="stale artifacts",
        ),
    )
    statuses = {
        item.alternative_id: item.status for item in others.state.alternatives
    }
    assert statuses["editorial"] is AlternativeStatus.ABANDONED
    assert statuses["quiet"] is AlternativeStatus.SELECTED
    final_selection = others.state.selection
    assert final_selection is not None
    assert final_selection.alternative_id == "quiet"


def test_deliberate_divergence_never_learns_and_rejection_stays_out_of_taste() -> None:
    question = ExplorationQuestion(
        question_id="divergence-question",
        prompt="How far can the hero composition go?",
        high_leverage_dimensions=("layout.density",),
        required_context=_context(),
    )
    with pytest.raises(ValueError):
        run_exploration(
            None,
            StartExploration(
                operation_id="start-divergent-learning",
                exploration_id="explore-divergent",
                mode=ExplorationMode.DELIBERATE_DIVERGENCE,
                learning_mode=LearningMode.LEARNING,
                scope=Scope("project", "project-a", "user-1"),
                question=question,
                alternatives=(
                    _alternative("a", density="airy", typography="x", artifacts=()),
                    _alternative("b", density="dense", typography="y", artifacts=()),
                ),
                novelty_budget=NoveltyBudget.RADICAL,
            ),
        )

    divergent = run_exploration(
        None,
        StartExploration(
            operation_id="start-divergent",
            exploration_id="explore-divergent",
            mode=ExplorationMode.DELIBERATE_DIVERGENCE,
            learning_mode=LearningMode.NON_LEARNING,
            scope=Scope("project", "project-a", "user-1"),
            question=question,
            alternatives=(
                _alternative("radical-a", density="airy", typography="x", artifacts=()),
                _alternative("radical-b", density="dense", typography="y", artifacts=()),
            ),
            novelty_budget=NoveltyBudget.RADICAL,
        ),
    ).state

    rejected = run_exploration(
        divergent,
        RejectAlternatives(
            operation_id="reject-divergent",
            alternative_ids=("radical-a", "radical-b"),
        ),
    )
    # Rejecting deliberate divergence is not contradictory taste evidence.
    assert rejected.evidence_transition is None
    assert rejected.production_candidate is None

    chosen = run_exploration(
        divergent,
        SelectAlternative(operation_id="select-divergent", alternative_id="radical-b"),
    )
    assert chosen.production_candidate is not None
    assert chosen.production_candidate.deliberate_divergence is True


def test_promotion_enters_the_normal_evidence_model_at_its_own_quality() -> None:
    from evidence_reconciliation import (
        Ambiguity,
        ClaimStatus,
        Consequence,
        EpistemicBasis as EvidenceBasis,
        EvidenceImplication,
        EvidenceState,
        EvidenceType,
        FeedbackKind,
        Fidelity,
        IngestEvidence,
        Judgment,
        PointClaim,
        SupportStrength,
        apply_evidence_operation,
    )
    from alignment_contract import Disposition, Provenance

    delegated = run_exploration(
        _delegation_state(),
        DelegateSelection(operation_id="delegate-promote", alternative_id="calm"),
    )
    intent = delegated.production_candidate
    assert intent is not None

    def promoted_implication(strength: SupportStrength, basis: EvidenceBasis) -> tuple:
        return (
            EvidenceImplication(
                implication_id=f"promotion-{strength.value}",
                claim=PointClaim(
                    dimension=intent.directions[0].dimension,
                    direction=intent.directions[0].direction,
                    disposition=Disposition.PREFERRED,
                ),
                basis=basis,
                represented_dimensions=(intent.directions[0].dimension,),
                fidelity=Fidelity.HIGH,
                required_fidelity=Fidelity.HIGH,
                ambiguity=Ambiguity.CLEAR,
                epistemic_strength=strength,
                preference_strength=0.7,
                consequence=Consequence.MATERIAL,
            ),
        )

    weak_promotion = promotion_evidence_event(
        intent,
        instruction_id="instruction:promote-calm",
        provenance=(Provenance(actor="user", source_id="chat:promote"),),
        validation_context=_context(),
        implications=promoted_implication(SupportStrength.WEAK, EvidenceBasis.INFERRED),
    )
    weak = apply_evidence_operation(
        EvidenceState(), IngestEvidence(operation_id="op:weak", event=weak_promotion)
    )
    assert weak.state.claims[0].status is ClaimStatus.HYPOTHESIS
    assert weak.state.claims[0].knowledge.confidence == 0.3

    strong_promotion = promotion_evidence_event(
        intent,
        instruction_id="instruction:promote-calm-strong",
        provenance=(Provenance(actor="user", source_id="chat:promote"),),
        validation_context=_context(),
        implications=promoted_implication(SupportStrength.STRONG, EvidenceBasis.EXPLICIT),
    )
    strong = apply_evidence_operation(
        EvidenceState(), IngestEvidence(operation_id="op:strong", event=strong_promotion)
    )
    assert strong.state.claims[0].status is ClaimStatus.ESTABLISHED

    replayed_promotion = apply_evidence_operation(
        strong.state,
        IngestEvidence(operation_id="op:again", event=strong_promotion),
    )
    assert replayed_promotion.status is TransitionStatus.DUPLICATE_EVENT
