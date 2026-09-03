---
name: system-review
description: Review defined systems when required behavior depends on interactions between parts or on failure, concurrency, change, or operational stress.
---

# System Review

Evaluate whether a defined system achieves its required outcome across interactions. A defect needs a demonstrated failed contract or control and a material consequence. Missing decision-sensitive evidence is a visibility gap.

## 1. Route and establish the target

System review owns defined cross-part behavior and operational failure paths. Local implementation, domain-specific organization or qualification, and preference work remain with their fitting owners unless needed as evidence for the system diagnosis. Comparison among open directions remains with `direction-selection`; system review evaluates choices only as they carry defined scenarios, diagnoses failures, and constrains corrections. When this review does not own the requested outcome, return `System Review Applicability: HANDOFF` with the reason and owner, then stop.

Capture:

- **Outcome:** the state the system must produce for users or operators.
- **Scope:** participating components, modules, agents, tools, stores, dependencies, human steps, trust boundaries, and environments.
- **Review stage:** proposed design, implementation, operation, or a stated combination.
- **Target identity:** applicable revision or version, configuration, environment, workload, and operational time window.
- **Operating bar:** prototype, internal, production, regulated/high-risk, or another constraint that changes what matters.
- **Normative authority:** requirements, invariants, and accepted constraints defining expected behavior.
- **Unknowns:** missing facts whose plausible answers could change a conclusion.

Classify evidence by reach: normative evidence defines what must happen; structural evidence shows what exists; behavioral evidence shows what happens; external authority establishes relevant platform or dependency behavior. A conclusion cannot reach beyond the stage, target, or operating conditions represented by its evidence.

**Complete when:** the task is handed off, or the outcome, boundary, stage, target, operating bar, authority, and decision-sensitive unknowns are explicit enough to map material interactions.

## 2. Map contracts and derive scenarios

Build a compact working map for every interaction capable of affecting the outcome:

`source → target | state or control exchanged | authoritative owner or invariant | success and failure semantics | observable result`

Relevant semantics include state authority; synchronous or asynchronous coupling; authentication, authorization, secrets, and sensitive-data boundaries; timeout, cancellation, retry, duplication, ordering, and concurrency; consistency and durability; schema or deployment compatibility; isolation, backpressure, and degradation; and observability or operator intervention.

Derive the smallest scenario set that covers every material contract and credible failure transition. One scenario may cover several related contracts; equivalent contracts may share a scenario. Tie each scenario to the contract map, a requirement, a trust boundary, or a credible operating condition.

Consider when applicable:

- normal end-to-end flow;
- invalid or unauthorized input;
- dependency slowdown, partial failure, timeout, and recovery;
- retry, duplication, reordering, interruption, and concurrency;
- restart, deploy, rollback, migration, or version skew;
- credible load growth, resource exhaustion, or backpressure;
- operator detection, diagnosis, and recovery.

Write each scenario as:

`setup → action or event → observable expected outcome`

**Complete when:** every material contract is covered by at least one scenario and every relevant failure transition has an observable expected outcome.

## 3. Trace scenarios against applicable evidence

For each scenario, trace:

`trigger or condition → required contract or control → actual state transitions → propagation → consequence → detection and recovery`

Inspect only the safest available evidence needed to compare actual behavior with the expected outcome. Resolve directly inspectable unknowns before reporting gaps, and use current primary documentation for version-sensitive external facts. Prefer behavioral execution when it can establish the property and structural inspection when the requirement is inherently structural. Keep active probes within authorization and an acceptable blast radius; otherwise record the check as blocked or unverified.

When a technology choice carries a scenario, judge it by workload fit, mismatch with known weaknesses, operational cost at the current team and scale, and future-horizon replaceability. Named patterns are evidence only when their problem is present.

When genuinely distinct independent perspectives could materially change a finding, causal attribution, disposition, or visibility gap, preserve their first passes and read [references/cross-agent-synthesis.md](references/cross-agent-synthesis.md). Otherwise synthesize directly.

On re-review, preserve still-applicable boundaries, contract maps, scenario and finding identifiers, authorities, and evidence provenance. Invalidate evidence affected by a changed target or premise. Rerun every failed or blocked scenario and every previously passing scenario whose contracts or assumptions may be affected; leave unaffected scenarios intact.

**Complete when:** every material scenario has applicable evidence or an explicit blocked check, every conclusion is bounded to that evidence, and all invalidated re-review coverage has been rerun.

## 4. Reconcile findings and choose dispositions

Trace each candidate finding through:

`trigger → violated contract or failed control → propagation → material consequence`

A trigger is not automatically a system defect. Group observations when the same violated contract or failed control explains them and attach downstream symptoms as evidence. Preserve independently material failed controls as separate findings, even when one trigger exposed them.

A finding survives only when it has evidence, a material consequence, and one supported disposition:

- **Correction:** one smallest coherent correction is supported.
- **Diagnostic handoff:** the defect is demonstrated but its causal boundary or correction is not. Include the unresolved boundary, missing discriminating evidence, smallest safe next check, and fitting owner.
- **Direction handoff:** the defect and correction constraints are established but materially different consequential corrections remain credible. Include the defect evidence, hard constraints and invariants, exact decision boundary, and established options without ranking.

Hand comparative correction selection to `direction-selection` when the surrounding task includes choosing the direction. System review preserves the diagnosis and does not search for or rank replacements.

Treat preferences, generic best practices, absent fashionable patterns, and unsupported future scale as non-findings. A visibility gap may affect the verdict, finding qualification, causal attribution, or correction determination. It must not erase a demonstrated defect or force an invented correction.

Record **Close when** for every finding: the exact scenario and observable evidence required to establish correction. On re-review, close a finding only when that condition is positively established.

**Complete when:** every surviving finding is materially distinct, evidence-backed, causally reconciled, and assigned one supported disposition and closure condition; every decision-sensitive gap is explicit.

## 5. Return the review

Use:

### System Review

- **Scope:** reviewed system boundary
- **Stage and target:** applicable stage, revision, configuration, environment, workload, and time window
- **Operating bar:** applicable bar
- **Verdict:** `PASS` | `PASS WITH RISKS` | `CHANGES REQUIRED` | `INSUFFICIENT EVIDENCE`

### Findings

For each demonstrated defect:

**[S-NN] Title**
- **Evidence:** specific normative, structural, behavioral, or external evidence
- **Scenario:** exposing behavior or failure path
- **Failure:** violated contract or failed control
- **Consequence:** material effect
- **Correction:** smallest coherent correction
- **Close when:** scenario and observable evidence required to close the finding

Replace `Correction` when another disposition applies:

- **Diagnostic handoff:** unresolved boundary, missing discriminating evidence, smallest safe next check, and owner
- **Direction handoff:** decision boundary, hard constraints, established evidence, and options without ranking

### Visibility Gaps

Only gaps capable of changing a conclusion:

**[V-NN] Gap**
- **Missing evidence:** what cannot be established
- **Decision effect:** what verdict, finding, cause, or correction it could change
- **Next check / owner:** smallest safe evidence route and fitting owner

### Residual Risks

Only known, evidence-backed exposures accepted at the current operating bar:

**[R-NN] Risk**
- **Evidence:** what establishes the exposure
- **Exposure:** what may happen and under what conditions
- **Why accepted:** why no correction is required at the current bar
- **Reopen if:** observable condition that invalidates the acceptance

A residual risk is a sufficiently understood exposure accepted at the current bar. A visibility gap is missing evidence whose plausible answers could materially change a conclusion. Unverified uncertainty is not a residual risk.

### Validated Areas

Material contracts and scenarios supported without a demonstrated defect. State the evidence type and reach; do not imply broader correctness.

### Verification

Scenarios, tests, inspections, observations, and authorities actually used; include blocked checks and invalidated re-review coverage that was rerun.

Apply verdict precedence:

1. `CHANGES REQUIRED` — at least one demonstrated material defect remains, even when visibility gaps also exist.
2. `INSUFFICIENT EVIDENCE` — no demonstrated defect requires changes, but a decision-sensitive gap prevents deciding whether the operating bar is met.
3. `PASS WITH RISKS` — no correction is required, no verdict-blocking gap remains, and at least one residual-risk record is present.
4. `PASS` — within the recorded stage and target, applicable scenarios support the required outcome and no defect, verdict-blocking gap, or residual risk remains.

Stop when applicable scenarios are evaluated and the evidence supports the stage-scoped verdict. A preferable alternative system or architecture is not by itself a reason to continue.

**Complete when:** the verdict follows deterministically from the findings, visibility gaps, residual risks, validated areas, and verification actually recorded, then control returns to the caller.
