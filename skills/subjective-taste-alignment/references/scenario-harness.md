# Scenario harness

Use `scripts/alignment_harness.py` as the public seam for scenario-first behavioral checks. Tests and callers supply a `Scenario` and one `dispatch(step, state)` adapter. The harness owns step sequencing, retry accounting, interruption snapshots, restart position, observations, and final oracle comparison.

## Scenario shape

- `Scenario.name` identifies the user path and binds restart snapshots to it.
- `Scenario.initial_state` is JSON-compatible state visible to the dispatch adapter.
- Each `ScenarioStep` has a stable logical `id`, a `feature`, an `action`, optional payload, and `max_attempts`.
- `dispatch` returns a `Transition` with replacement state and one observable result.
- `expected_state` and `expected_observations` are the explicit oracle.

The dispatch adapter receives a copy of committed state. A retryable failure does not commit mutations from the failed attempt. Raise `RetryableScenarioError` only for failures that the scenario explicitly permits retrying.

Pass `interrupt_after` to stop after a completed step. The returned snapshot contains the scenario name, next step index, committed state, prior observations, and attempt counts. Serialize the snapshot before a restart and pass the decoded value as `resume`. A snapshot from another scenario is invalid.

Feature labels make cross-feature sequences visible without creating separate harness interfaces. Add domain behavior behind the dispatch adapter; keep callers and tests on this seam.

Canonical subjective decisions use `resolve_alignment` inside the dispatch adapter. Exercise the returned governing source, unresolved state, propagation eligibility, checkpoint obligations, provenance, dependencies, and revision guard rather than reconstructing resolution inside a test adapter.

## Required scenario coverage

Choose scenarios from user paths and state transitions rather than source structure. Cover applicable normal use, edge cases, misuse, retries, interruptions, restarts, stale state, unexpected ordering, and cross-feature interaction. Use structural checks only for requirements that are inherently structural or provide distinct coverage.

The canonical alignment model includes strong preference with weak confidence, weak preference with high confidence, known indifference, unresolved taste, dimension-scoped intent divergence, delegated judgment, temporary experimental direction, craft-prior execution detail, relevant decision-input staleness, and conflicting decision-bearing inputs.
