---
name: system-review
description: Review an existing or proposed software system at the system level when the task concerns architecture, component interactions, data flow, technology fit, reliability, scalability, security boundaries, or operational failure behavior. Use when line- or module-level code review cannot establish whether the system works coherently as a whole. Do not use for ordinary local code review or purely structural Roblox DataModel organization.
---

# System Review

Review the system that exists or is being proposed. Find demonstrated system-level defects, unsupported load-bearing assumptions, and consequential visibility gaps without manufacturing issues from missing detail or generic best practices.

This skill owns **system behavior and architecture**. Local implementation defects belong to the relevant code-review path. Roblox DataModel placement and organization belong to `structure-roblox-projects` unless the placement creates a system-level failure that cannot be understood locally.

## 1. Establish the review model

Record only what is needed to evaluate the requested system:

- **Outcome:** what the system must make true for its users or operators.
- **Scope:** components, stores, external dependencies, trust boundaries, and environments relevant to that outcome.
- **Context:** prototype, internal tool, production system, regulated/high-risk system, or another constraint that materially changes the bar.
- **Authority:** requirements, specifications, repository evidence, observed behavior, tests, operational evidence, and current authoritative documentation when version-sensitive facts matter.
- **Unknowns:** missing facts that could materially change a conclusion.

Classify missing information before treating it as a problem:

- **Visibility gap:** evidence is insufficient to judge a material property.
- **Defect:** available evidence demonstrates a material failure, violated requirement, unsafe boundary, or unjustified load-bearing decision.

A visibility gap is not a defect. Ask for or obtain more evidence only when plausible answers could materially change the review.

**Complete when:** the system outcome, review boundary, applicable bar, authorities, and decision-sensitive unknowns are explicit enough to test behavior.

## 2. Build behavioral scenarios

Review through system scenarios, not an issue checklist. Select only scenarios relevant to the system and requested scope.

Cover the smallest set that can expose material interaction failures, including when applicable:

- normal end-to-end flow;
- invalid, adversarial, or unauthorized input;
- dependency slowdown, timeout, partial failure, and recovery;
- retries, duplication, reordering, and interrupted operations;
- concurrent work and conflicting state transitions;
- deploy, restart, rollback, migration, or version skew;
- load growth and backpressure at the first credible stress point;
- loss of an external service, store, queue, worker, or network path;
- observability and operator diagnosis when the scenario fails.

For each scenario, trace the relevant components, state transitions, contracts, and externally observable outcome. Do not expand into dimensions that cannot affect the requested outcome.

**Complete when:** every material cross-component behavior in scope is exercised by at least one scenario, and important failure transitions have an observable expected outcome.

## 3. Test architecture claims against evidence

Evaluate decisions only where they carry behavior in the scenarios. Typical system-level questions include:

- Are responsibilities and authoritative state owned coherently?
- Do interaction contracts preserve required consistency, ordering, idempotency, and failure semantics?
- Do synchronous and asynchronous boundaries match latency and coupling requirements?
- Can load or dependency failure amplify across the system without backpressure, isolation, or graceful degradation?
- Can deployment, schema evolution, and rollback occur without hidden ordering constraints?
- Are trust boundaries, authentication, authorization, secrets, and sensitive data enforced at the correct authority boundary?
- Can operators detect and localize the failures that matter?
- Do technology choices fit the actual workload and team/operational constraints rather than a generic ideal?

Use named architectural patterns only when their problem is demonstrated. A pattern's absence is not a finding by itself.

For a technology decision, compare at least:

1. workload fit;
2. mismatch with known weaknesses;
3. operational cost at the current scale/team;
4. future-horizon replaceability.

Prefer current project evidence, representative tests/benchmarks, and primary documentation over generic architectural doctrine.

**Complete when:** every material conclusion is tied to evidence from a scenario, requirement, observed state, or applicable authority.

## 4. Qualify findings

A review finding must contain all three:

1. **Evidence** — what demonstrates the condition.
2. **Material consequence** — what behavior, requirement, security property, operability, or credible future commitment is harmed.
3. **Smallest coherent correction** — the minimum change that addresses the demonstrated cause without unrelated redesign.

Do not emit a finding for:

- a merely imaginable failure;
- a missing fashionable pattern;
- a preference with no material consequence;
- scale the system is not credibly expected to face;
- unavailable information that is correctly classified as a visibility gap;
- a local code smell with no system-level consequence.

Assign **Confidence: high | medium | low** from the evidence. Low-confidence observations belong under visibility gaps unless evidence already demonstrates a material defect despite uncertainty about its exact cause.

## 5. Synthesize root causes

When multiple observations describe one causal problem, keep the most upstream demonstrated root cause and attach downstream evidence to it. Do not count symptoms as independent findings.

When two or more genuinely independent review perspectives are useful and subagents are available, use `cross-agent-synthesis` for the bounded exchange. Preserve independent first-pass conclusions before cross-signals are shared.

If a local implementation defect and a system defect describe the same failure, report the system root cause here and identify the implementation location as evidence. Do not duplicate it as two issues.

**Complete when:** every surviving finding is materially distinct or provides independent evidence for a distinct root cause.

## 6. Return the review

Use this format, omitting empty optional sections:

### System Review

- **Scope:** reviewed system boundary
- **Context:** applicable operating bar
- **Verdict:** `PASS` | `PASS WITH RISKS` | `CHANGES REQUIRED` | `INSUFFICIENT EVIDENCE`

### Findings

For each demonstrated defect:

**[S-NN] Title**
- **Evidence:** specific observed or authoritative evidence
- **Scenario:** behavior or failure path that exposes it
- **Consequence:** material effect
- **Correction:** smallest coherent correction
- **Confidence:** high | medium | low

### Visibility Gaps

Only decision-sensitive gaps:

**[V-NN] Gap** — what cannot be established and what conclusion it could change.

### Validated Areas

Name material areas that were positively exercised and produced no demonstrated defect. Do not claim exhaustive correctness.

### Verification

State the scenarios, tests, inspections, or authorities actually used and anything required but blocked.

## Verdict rules

- `PASS`: relevant scenarios were positively exercised and no demonstrated material defect or decision-sensitive visibility gap remains.
- `PASS WITH RISKS`: no correction is currently required, but explicit residual risk remains within the accepted scope/bar.
- `CHANGES REQUIRED`: at least one demonstrated material defect remains.
- `INSUFFICIENT EVIDENCE`: a decision-sensitive visibility gap prevents a supported verdict.

Stop when the applicable scenarios are exercised and no demonstrated material defect remains. Do not continue searching merely because another theoretically preferable architecture can be imagined.