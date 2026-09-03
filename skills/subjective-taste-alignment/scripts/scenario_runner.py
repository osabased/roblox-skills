"""Scenario-first execution with retry and restart semantics."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class ScenarioStep:
    id: str
    feature: str
    action: str
    payload: Mapping[str, Any] | None = None
    max_attempts: int = 1


@dataclass(frozen=True)
class Scenario:
    name: str
    initial_state: Mapping[str, Any]
    steps: tuple[ScenarioStep, ...]
    expected_state: Mapping[str, Any]
    expected_observations: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class Transition:
    state: Mapping[str, Any]
    observation: Mapping[str, Any]


@dataclass(frozen=True)
class ScenarioResult:
    status: str
    state: Mapping[str, Any]
    observations: tuple[Mapping[str, Any], ...]
    failures: tuple[str, ...]
    attempts: Mapping[str, int]
    snapshot: Mapping[str, Any] | None = None


class RetryableScenarioError(RuntimeError):
    """Signal that a scenario step may be attempted again."""


def run_scenario(
    scenario: Scenario,
    dispatch: Callable[[ScenarioStep, dict[str, Any]], Transition],
    *,
    interrupt_after: int | None = None,
    resume: Mapping[str, Any] | None = None,
) -> ScenarioResult:
    """Run a user path through one observable, state-based dispatch seam."""
    if resume is None:
        state = deepcopy(dict(scenario.initial_state))
        observations: list[Mapping[str, Any]] = []
        attempts: dict[str, int] = {}
        start_index = 0
    else:
        if resume.get("scenario_name") != scenario.name:
            raise ValueError("snapshot belongs to a different scenario")
        state = deepcopy(dict(resume["state"]))
        observations = [deepcopy(dict(item)) for item in resume["observations"]]
        attempts = {str(key): int(value) for key, value in resume["attempts"].items()}
        start_index = int(resume["next_step_index"])

    executed = 0
    for step_index, step in enumerate(scenario.steps[start_index:], start=start_index):
        while True:
            attempts[step.id] = attempts.get(step.id, 0) + 1
            try:
                transition = dispatch(step, deepcopy(state))
                break
            except RetryableScenarioError:
                if attempts[step.id] >= step.max_attempts:
                    raise
        state = deepcopy(dict(transition.state))
        observations.append(deepcopy(dict(transition.observation)))
        executed += 1

        if interrupt_after is not None and executed >= interrupt_after:
            next_step_index = step_index + 1
            if next_step_index < len(scenario.steps):
                snapshot = {
                    "scenario_name": scenario.name,
                    "next_step_index": next_step_index,
                    "state": state,
                    "observations": observations,
                    "attempts": attempts,
                }
                return ScenarioResult(
                    status="interrupted",
                    state=state,
                    observations=tuple(observations),
                    failures=(),
                    attempts=attempts,
                    snapshot=snapshot,
                )

    failures: list[str] = []
    if state != dict(scenario.expected_state):
        failures.append("final state did not match the scenario oracle")
    if tuple(observations) != scenario.expected_observations:
        failures.append("observations did not match the scenario oracle")

    return ScenarioResult(
        status="passed" if not failures else "failed",
        state=state,
        observations=tuple(observations),
        failures=tuple(failures),
        attempts=attempts,
        snapshot=None,
    )
