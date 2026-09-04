---
name: architecture-improvement
description: Autonomously make one justified codebase architecture improvement, or leave the codebase unchanged.
disable-model-invocation: true
---

# Architecture Improvement

Evaluate one bounded codebase scope. When architectural intervention is justified and safely executable, complete one coherent improvement. `NO CHANGE` is a successful outcome.

Invocation authorizes code changes only after the Intervention Gate passes, subject to any narrower user instruction.

## Contract

This skill owns changes to module, interface, seam, or dependency structure. Local defects, spec deviations, code smells, and preferable designs remain with their fitting owners unless architecture materially causes or obstructs a demonstrated need.

Complete one architectural objective per invocation. Preserve unrelated work; other observations do not extend this invocation.

Resolve repository-owned facts through the repository and available tools. Escalate only for user-owned product intent, externally visible compatibility policy, reopening an authoritative decision, an irreversible migration, or another material choice the available evidence cannot settle.

Use `$codebase-design` when available. Its vocabulary and principles guide architecture judgment; repository requirements, standards, domain language, and ADRs remain authoritative.

## 1. Establish the target

Use a bounded module, subsystem, pain point, or change named by the user.

When the user names the whole repository or supplies no bounded target, perform bounded triage from recent history, recurring fixes, current branch work, test friction, and repository guidance. Select the strongest-supported area for inspection. Return `NO CHANGE` when no area has a credible reason for deeper inspection. Churn is a scope signal, not evidence that intervention is warranted.

Estimate reconnaissance cost before loading source. When the target is large or unfamiliar, several independent regions need mapping, or direct inspection would materially consume the controller's context, read [references/RECONNAISSANCE.md](references/RECONNAISSANCE.md) completely and apply it.

Read applicable repository instructions, domain documentation, ADRs, standards, tests, and nearby implementation. Record the starting revision, working-tree state, and relevant baseline checks so pre-existing failures and user changes remain distinguishable.

**Complete when:** one bounded target, its authoritative context, observable baseline, and direct or delegated reconnaissance boundary are clear, or bounded triage supports `NO CHANGE` without a target.

## 2. Build intervention evidence

Inspect the target directly or synthesize reconnaissance packets across its callers, dependencies, interfaces, tests, and change history.

Potential evidence includes:

- one behavior repeatedly requiring coordinated edits across callers;
- an authorized near-term change that the current structure would spread across callers or layers;
- callers duplicating policy or depending on implementation knowledge;
- an interface nearly as complex as the behavior behind it;
- meaningful behavior that tests cannot exercise through the interface;
- recurring defects or regressions at the same seam;
- pass-through or tightly coupled structure that relocates change knowledge instead of hiding it.

These are leads. Form a candidate only when concrete evidence connects a demonstrated need to an architectural cause. A delegated claim also needs applicable provenance before it can support the candidate.

For each credible candidate, record:

- the demonstrated need and evidence;
- recurrence, current consequence, or committed change affected;
- affected callers, tests, and behavior;
- the architectural cause;
- the smallest local alternative;
- expected locality, leverage, or testability gain;
- migration, regression, and permanent abstraction cost;
- observable evidence that would establish success.

When signals are widespread, classify them as independent problems, symptoms of a shared architectural cause, or style disorder. Select by supported cause and leverage rather than visibility.

**Complete when:** the evidence supports at least one fully described candidate or supports stopping without one, and every decisive claim has traceable provenance.

## 3. Apply the Intervention Gate

A candidate authorizes architectural change only when every condition is supported:

1. **Demonstrated need** — concrete evidence shows recurring engineering cost, a current material consequence, or an authorized near-term change that the present structure materially obstructs.
2. **Architectural causality** — the current module, interface, seam, or dependency structure materially causes or obstructs that need.
3. **Direct improvement** — the proposed change addresses the demonstrated need rather than relocating complexity or changing style.
4. **Superiority** — its expected outcome is better supported than doing nothing or applying the smallest local correction.
5. **Proportionality** — expected benefit exceeds migration work, regression exposure, and permanent structural cost.
6. **Compatibility** — applicable behavior, constraints, and authoritative decisions remain satisfied, or authority exists to revise them.
7. **Verifiability** — observable checks can establish preserved behavior and the claimed architectural benefit.

Challenge each candidate with the strongest applicable case for the current design, an isolated cause, a local correction, a hypothetical seam, relocated knowledge, speculative benefit, or an ADR-backed constraint.

When qualification depends on cross-area inference, conflicting packets, or evidence gathered mainly through low-capability scans, run a focused challenger probe or perform the decisive reasoning directly.

Invocation is not evidence of need. Smells, unfamiliar organization, preference, hypothetical scale, and cleaner-looking alternatives remain non-authorizing observations. The threshold stays fixed when no candidate survives.

**Complete when:** every credible candidate either passes all seven conditions or has a decisive rejection reason.

## 4. Choose the route

Choose exactly one disposition:

- **`NO CHANGE`** — no candidate passes the Intervention Gate.
- **`LOCAL HANDOFF`** — a material need exists, but a non-architectural correction is better supported.
- **`EXECUTE`** — one bounded architectural objective is justified and can be completed and verified safely.
- **`PLANNING HANDOFF`** — intervention is justified, but one bounded change would leave an unsafe or incomplete architecture.
- **`BLOCKED`** — a user-owned decision, unavailable decision-sensitive evidence, or required verification prevents a supported disposition.

Resolve ordinary engineering tradeoffs autonomously. When materially different consequential architecture directions remain credible and evidence establishes no winner, invoke `$direction-selection` with the need, constraints, candidates, migration effects, and verification obligations. Continue only if its Direction Gate passes for this commitment.

`EXECUTE` requires traceable callers and compatibility obligations, a complete retirement or intentional transition for the old path, runnable verification, and no unresolved material decision.

Use `PLANNING HANDOFF` when a shared systemic cause, ordered migration dependencies, or required stabilization prevents one safe coherent change. Preserve the causal structure, affected behavior, stabilization, migration order, first executable slice, verification obligations, and retirement conditions. Widespread smells alone do not justify a repository-wide rewrite.

For `EXECUTE`, read [references/EXECUTION.md](references/EXECUTION.md) completely and follow it. For every other disposition, proceed directly to Output.

**Complete when:** one disposition follows from the evidence and candidate selection is not deferred to the user.

## Output

Return:

### Architecture Improvement

- **Scope:** bounded target and revision
- **Disposition:** `IMPROVED` | `NO CHANGE` | `LOCAL HANDOFF` | `PLANNING HANDOFF` | `BLOCKED`
- **Reconnaissance:** direct or delegated coverage, capability profiles used, and material limits or assignment mismatches
- **Evidence:** decisive repository evidence
- **Intervention Gate:** pass or decisive failure by condition
- **Objective:** selected architecture change, local correction boundary, planning target, or `none`
- **Work completed:** changed behavior and structure, or `none`
- **Verification:** checks and scenarios actually run, including blocked checks
- **Residuals:** remaining task-related residue, or `none`
- **Reopen if:** concrete evidence or conditions that would change the disposition

For `NO CHANGE`, report either that no credible candidate emerged or the strongest rejected candidate and its decisive failure. Keep non-authorizing observations out of the result.

For `PLANNING HANDOFF`, provide the complete supported objective, constraints, migration boundary, and verification obligations as input to the surrounding `to-spec` or `to-tickets` workflow.

Use `IMPROVED` only after the `EXECUTE` branch completes implementation, verification, and cleanup.