import json

from alignment_harness import (
    RetryableScenarioError,
    Scenario,
    ScenarioStep,
    Transition,
    run_scenario,
)


def test_user_path_exercises_cross_feature_state_transitions() -> None:
    def dispatch(step: ScenarioStep, state: dict[str, object]) -> Transition:
        next_state = dict(state)
        if step.action == "record-capability":
            next_state["contract_ready"] = True
            return Transition(next_state, {"contract": "ready"})
        if step.action == "request-propagation":
            permitted = bool(next_state.get("contract_ready"))
            next_state["propagation"] = "allowed" if permitted else "blocked"
            return Transition(next_state, {"propagation": next_state["propagation"]})
        raise AssertionError(f"unexpected action: {step.action}")

    scenario = Scenario(
        name="capability preflight precedes propagation",
        initial_state={"contract_ready": False},
        steps=(
            ScenarioStep("capability-1", "capabilities", "record-capability"),
            ScenarioStep("propagation-1", "propagation", "request-propagation"),
        ),
        expected_state={"contract_ready": True, "propagation": "allowed"},
        expected_observations=(
            {"contract": "ready"},
            {"propagation": "allowed"},
        ),
    )

    result = run_scenario(scenario, dispatch)

    assert result.status == "passed"
    assert result.failures == ()
    assert result.state == {"contract_ready": True, "propagation": "allowed"}


def test_retry_replays_one_step_without_committing_failed_state() -> None:
    calls = 0

    def dispatch(step: ScenarioStep, state: dict[str, object]) -> Transition:
        nonlocal calls
        calls += 1
        state["attempted"] = calls
        if calls == 1:
            raise RetryableScenarioError("temporary host failure")
        state["saved"] = True
        return Transition(state, {"saved": True})

    scenario = Scenario(
        name="transient persistence failure is retried",
        initial_state={},
        steps=(ScenarioStep("save-1", "persistence", "save", max_attempts=2),),
        expected_state={"attempted": 2, "saved": True},
        expected_observations=({"saved": True},),
    )

    result = run_scenario(scenario, dispatch)

    assert result.status == "passed"
    assert result.attempts == {"save-1": 2}


def test_retry_does_not_commit_nested_mutations_from_failed_attempt() -> None:
    calls = 0

    def dispatch(step: ScenarioStep, state: dict[str, object]) -> Transition:
        nonlocal calls
        calls += 1
        nested = state["nested"]
        assert isinstance(nested, dict)
        attempts = nested["attempts"]
        assert isinstance(attempts, list)
        attempts.append(calls)
        if calls == 1:
            raise RetryableScenarioError("temporary host failure")
        return Transition(state, {"saved": True})

    scenario = Scenario(
        name="failed nested mutation is rolled back",
        initial_state={"nested": {"attempts": []}},
        steps=(ScenarioStep("save-1", "persistence", "save", max_attempts=2),),
        expected_state={"nested": {"attempts": [2]}},
        expected_observations=({"saved": True},),
    )

    result = run_scenario(scenario, dispatch)

    assert result.status == "passed"
    assert result.state == {"nested": {"attempts": [2]}}


def test_interrupted_path_restarts_from_a_serializable_snapshot() -> None:
    def dispatch(step: ScenarioStep, state: dict[str, object]) -> Transition:
        completed_state = state.get("completed", [])
        assert isinstance(completed_state, list)
        completed = list(completed_state)
        completed.append(step.action)
        return Transition({"completed": completed}, {"completed": step.action})

    scenario = Scenario(
        name="restart continues remaining work",
        initial_state={"completed": []},
        steps=(
            ScenarioStep("prepare-1", "profiles", "prepare"),
            ScenarioStep("apply-1", "alignment", "apply"),
        ),
        expected_state={"completed": ["prepare", "apply"]},
        expected_observations=(
            {"completed": "prepare"},
            {"completed": "apply"},
        ),
    )

    interrupted = run_scenario(scenario, dispatch, interrupt_after=1)

    assert interrupted.status == "interrupted"
    assert interrupted.snapshot is not None
    serialized = json.loads(json.dumps(interrupted.snapshot))

    resumed = run_scenario(scenario, dispatch, resume=serialized)

    assert resumed.status == "passed"
    assert resumed.state == {"completed": ["prepare", "apply"]}
    assert resumed.attempts == {"prepare-1": 1, "apply-1": 1}
