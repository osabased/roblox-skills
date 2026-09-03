---
name: system-review
description: Review software systems when correctness depends on interactions among multiple components or operational failure behavior. Use for system or architecture review of data flow, authority, consistency, reliability, scalability, security boundaries, technology fit, or failure handling. Skip ordinary local code review, Roblox organization-only work, and selection among competing replacement directions.
---

# System Review

Evaluate whether the system achieves its required outcome across component interactions. Evidence governs the review: a defect needs a demonstrated condition and material consequence; missing decision-sensitive evidence is a visibility gap.

## 1. Establish the review boundary

Capture only what the review needs:

- **Outcome:** the state the system must produce for users or operators.
- **Scope:** relevant components, stores, dependencies, trust boundaries, and environments.
- **Operating bar:** prototype, internal, production, regulated/high-risk, or another constraint that changes what matters.
- **Authority:** requirements, repository evidence, tests, observed behavior, operational evidence, and current primary documentation when a version-sensitive fact matters.
- **Unknowns:** missing facts whose plausible answers could change the verdict.

Keep local implementation review with the code-review path. Keep Roblox DataModel organization with `structure-roblox-projects` unless the placement participates in a cross-component failure.

**Complete when:** the outcome, system boundary, operating bar, authorities, and decision-sensitive unknowns are explicit enough to test behavior.

## 2. Build the scenario set

Choose the smallest scenario set that covers every material cross-component contract and credible failure transition in scope. Tie each scenario to a requirement, observed topology, trust boundary, or credible operating condition.

Consider when applicable:

- normal end-to-end flow;
- invalid or unauthorized input;
- dependency slowdown, partial failure, timeout, and recovery;
- retry, duplication, reordering, interruption, and concurrency;
- restart, deploy, rollback, migration, or version skew;
- credible load growth, resource exhaustion, or backpressure;
- operator detection and diagnosis of a material failure.

Write each scenario as:

`setup → action/event → observable expected outcome`

**Complete when:** every material interaction in scope is exercised by at least one scenario and every relevant failure transition has an observable expected outcome.

## 3. Trace and test

For each scenario, trace authority, state transitions, contracts, and failure propagation across the participating components. Inspect or execute only the evidence needed to compare actual behavior with the expected outcome.

Pay particular attention where the scenario depends on:

- ownership of authoritative state;
- consistency, ordering, idempotency, or concurrency guarantees;
- synchronous or asynchronous coupling;
- backpressure, isolation, or graceful degradation;
- schema/deployment compatibility and rollback;
- authentication, authorization, secrets, or sensitive-data boundaries;
- observability needed to localize the failure.

When a technology choice carries the scenario, judge it by workload fit, mismatch with known weaknesses, operational cost at the current team/scale, and future-horizon replaceability. Named patterns are evidence only when the problem they solve is actually present.

Prefer behavioral execution and representative evidence. Use structural inspection where the requirement is inherently structural. Mark an unexecuted decision-sensitive check as unverified.

When two or more genuinely distinct independent perspectives can materially change a conclusion or root-cause attribution, preserve their first passes and read [references/cross-agent-synthesis.md](references/cross-agent-synthesis.md). Otherwise synthesize directly.

**Complete when:** every material conclusion is supported by an exercised scenario, observed state, requirement, or applicable authority; required blocked checks are explicit.

## 4. Qualify, reconcile, and hand off

A finding survives only when it has:

1. **Evidence** — what demonstrates the condition.
2. **Consequence** — the material behavior, requirement, security property, operability, or credible commitment harmed.
3. **Correction or handoff** — one evidence-determined smallest coherent correction, or an explicit direction handoff when selection remains open.

Treat insufficient evidence as a visibility gap when it can change the verdict. Treat preferences, generic best practices, absent fashionable patterns, and unsupported future scale as non-findings.

Collapse symptoms into the most upstream demonstrated root cause and attach downstream observations as evidence. Keep independent causes separate.

System review owns diagnosis, not comparative replacement selection. Use a smallest coherent correction when the evidence determines one. When two or more materially different consequential corrections remain credible, preserve the finding and return a **Direction handoff** containing:

- the defect and exposing scenario evidence;
- hard constraints and invariants that the correction must satisfy;
- the exact decision boundary;
- already-established correction options, if any, stated without ranking.

Hand the decision to `direction-selection` when the surrounding task includes choosing the correction. Otherwise return the handoff to the caller. Do not search for or rank replacement directions inside this review.

**Complete when:** every surviving finding is materially distinct and evidence-backed, every decision-sensitive gap is explicit, and each finding has either one evidence-determined correction or a direction handoff.

## 5. Return the review

Use:

### System Review

- **Scope:** reviewed system boundary
- **Context:** applicable operating bar
- **Verdict:** `PASS` | `PASS WITH RISKS` | `CHANGES REQUIRED` | `INSUFFICIENT EVIDENCE`

### Findings

For each demonstrated defect:

**[S-NN] Title**
- **Evidence:** specific evidence
- **Scenario:** exposing behavior or failure path
- **Consequence:** material effect
- **Correction:** smallest coherent correction

When correction selection remains open, replace `Correction` with:

- **Direction handoff:** decision boundary, hard constraints, and evidence to pass to `direction-selection`.

### Visibility Gaps

Only gaps capable of changing the verdict:

**[V-NN] Gap** — what cannot be established and what conclusion it could change.

### Validated Areas

Material areas positively exercised without a demonstrated defect.

### Verification

Checks, scenarios, inspections, and authorities actually used; include required blocked checks.

Verdicts mean:

- `PASS` — relevant scenarios passed, no demonstrated material defect remains, and no decision-sensitive gap blocks the conclusion.
- `PASS WITH RISKS` — no correction is required at the current bar, but explicit residual risk remains.
- `CHANGES REQUIRED` — at least one demonstrated material defect remains.
- `INSUFFICIENT EVIDENCE` — a decision-sensitive gap prevents a supported verdict.

Stop when the applicable scenarios are exercised and no demonstrated material defect remains. A preferable alternative architecture is not by itself a reason to continue.

**Complete when:** the verdict follows from the recorded findings, visibility gaps, validated areas, and checks actually performed, then control returns to the caller.
