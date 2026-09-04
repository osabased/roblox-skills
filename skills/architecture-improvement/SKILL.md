---
name: architecture-improvement
description: Evaluate and autonomously carry out one justified codebase architecture improvement, or stop when intervention is unsupported.
disable-model-invocation: true
---

# Architecture Improvement

Determine whether one bounded architectural intervention is justified, then design, implement, and verify it without asking the user to choose among ordinary engineering alternatives. `NO CHANGE` is a successful outcome.

Invoking this skill authorizes code changes after the intervention gate passes, subject to any narrower user instruction.

## Operating contract

This skill owns architectural intervention within a bounded codebase scope. It does not turn local defects, spec deviations, generic code smells, or preferable designs into architecture work without evidence that architecture materially causes or obstructs a demonstrated need.

Complete one coherent architectural objective per invocation. Preserve unrelated work and stop rather than widening into a cleanup campaign.

Resolve inspectable engineering questions from the repository and available tools. Escalate only when progress depends on user-owned product intent, externally visible compatibility policy, reopening an authoritative decision, an irreversible migration, or another material choice that repository evidence cannot settle.

When available, invoke `$codebase-design` before judging candidates. Use its architecture vocabulary and principles; repository requirements, standards, domain language, and ADRs remain authoritative.

## 1. Establish the target

If the user names a module, subsystem, pain point, or change, use that scope.

Otherwise perform a bounded scope triage using recent change history, recurring fixes, current branch work, test friction, and repository guidance. Select the strongest-supported target for deep inspection. If no area has a credible reason for inspection, return `NO CHANGE`. Churn identifies where to look; it is not proof that intervention is warranted. Do not scan the entire repository deeply or widen merely because the selected target is healthy.

Read applicable repository instructions, domain documentation, ADRs, standards, tests, and nearby implementation. Record the starting revision, working-tree state, and relevant baseline checks so pre-existing failures and user changes are not attributed to this invocation.

**Complete when:** one bounded target, its authoritative context, and its observable baseline are clear, or the bounded triage supports stopping without a target.

## 2. Gather intervention evidence

Inspect the target through its callers, dependencies, interfaces, tests, and change history. Look for a demonstrated architectural need, using evidence such as:

- one behavior repeatedly requiring coordinated edits across callers;
- an authorized near-term change that the current structure would spread across callers or layers;
- callers duplicating policy or learning implementation details;
- an interface nearly as complex as the behavior behind it;
- tests bypassing the interface because meaningful behavior cannot be exercised through it;
- recurring defects or regressions at the same seam;
- tightly coupled modules whose changes repeatedly propagate across the seam;
- pass-through structure that relocates rather than hides complexity.

These are leads, not findings. Do not generate a fixed number of candidates.

For each credible candidate, record:

- concrete need and its evidence;
- recurrence, current material consequence, or committed change affected;
- affected callers, tests, and behavior;
- the architectural cause;
- the smallest local alternative;
- the expected gain in locality, leverage, or testability;
- migration, regression, and ongoing abstraction cost;
- observable evidence that would show the improvement succeeded.

**Complete when:** the inspected evidence either supports at least one fully described candidate or supports stopping with no candidate.

## 3. Apply the intervention gate

A candidate authorizes architectural change only when every condition is supported:

1. **Demonstrated need** — concrete evidence shows recurring engineering cost, a current material consequence, or an authorized near-term change that the present structure materially obstructs.
2. **Architectural causality** — the current module, interface, seam, or dependency structure materially causes or obstructs the demonstrated need.
3. **Direct improvement** — the proposed change directly addresses the demonstrated need rather than merely moving complexity or changing style.
4. **Superiority** — the intervention has a better supported expected outcome than doing nothing or applying the smallest local correction.
5. **Proportionality** — expected benefit exceeds migration work, regression exposure, and the permanent cost of the new structure.
6. **Compatibility** — the change respects applicable behavior, constraints, and authoritative decisions, or has explicit authority to revise them.
7. **Verifiability** — observable checks can establish both preserved behavior and the claimed architectural benefit.

Falsify the candidate before acting. Seek evidence that the current design is adequate, the friction is isolated, a local fix is enough, the proposed seam is hypothetical, the abstraction only relocates knowledge, the benefit is speculative, or an ADR explains the present structure.

Invocation authorizes evaluation; it is not evidence that a change is needed. Code smells, unusual organization, personal preference, hypothetical scale, and a cleaner-looking design cannot pass the gate by themselves. Do not lower the threshold because no other candidate exists.

**Complete when:** each credible candidate either passes every gate condition or has a recorded rejection reason.

## 4. Choose the route

Use the evidence to choose exactly one route:

- **`NO CHANGE`** — no candidate passes the intervention gate.
- **`LOCAL HANDOFF`** — material friction exists, but a non-architectural correction is better supported.
- **`EXECUTE`** — one bounded architectural objective is justified and can be completed and verified safely.
- **`PLANNING HANDOFF`** — intervention is justified, but completing the migration as one bounded change would leave an unsafe or incomplete architecture.
- **`BLOCKED`** — a user-owned decision, unavailable evidence, or required verification prevents a supported route.

Choose ordinary engineering tradeoffs autonomously. When materially different consequential architecture directions remain credible and evidence does not establish a winner, invoke `$direction-selection` with the established friction, constraints, candidates, migration effects, and verification needs. Continue only if its Direction Gate passes for this commitment. Do not invoke it to manufacture alternatives.

Use `EXECUTE` only when all affected callers and compatibility obligations can be traced, the old path can be fully retired or intentionally retained, required verification can run, and no unresolved material decision remains. Use `PLANNING HANDOFF` only when those conditions genuinely require staged work; size alone is not a reason to avoid execution. Do not use `BLOCKED` for ordinary engineering uncertainty.

**Complete when:** one route follows from the intervention evidence and no candidate selection is being deferred to the user.

## 5. Design the bounded change

For `EXECUTE`, trace all affected callers, dependencies, state ownership, invariants, tests, failure semantics, and migration steps. Design the smallest coherent change that captures the supported benefit.

Prefer deep modules, useful interfaces, locality, and real seams over additional layers. Replace obsolete structure rather than maintaining parallel architectures unless compatibility evidence requires a transition.

When a consequential interface has materially different credible shapes, use `$codebase-design`'s design-it-twice method before selecting one; invoke `$direction-selection` only if supported alternatives remain genuinely competitive.

Define before editing:

- behavior that must remain unchanged;
- any intentional behavior change;
- the new module, interface, or seam;
- complete caller and data migration;
- behavioral scenarios and regression checks;
- architectural success evidence;
- rollback or recovery considerations when material.

If the change affects cross-part contracts, authority, retries, ordering, concurrency, durability, deployment compatibility, recovery, or operational failure paths, invoke `$system-review` to establish the applicable scenarios and constraints. Use it only for the affected system behavior, not as a general search for more findings.

**Complete when:** the design, complete migration, and verification plan cover the full objective without unresolved material gaps.

## 6. Implement

Preserve pre-existing user changes. Modify only the selected objective and its necessary callers, tests, types, and directly affected documentation.

Use `$tdd` when available and behavior can be captured through a red-green-refactor loop. Otherwise establish the smallest reliable feedback loop before restructuring.

Keep externally observable behavior stable unless an intentional change was authorized. Remove obsolete paths, duplicate orchestration, temporary adapters, and dead abstractions once their callers are migrated. Do not repair unrelated observations encountered during the work.

If implementation reveals that the intervention gate relied on a false premise, stop and reassess from the earliest affected step rather than forcing the chosen design through.

**Complete when:** the coherent objective and migration are implemented, with no unintended mixed architecture left by this invocation.

## 7. Verify and clean up

Run every relevant repository check, focused behavioral test, and broader regression check justified by the affected surface. Exercise normal usage and material edge, failure, retry, ordering, or migration scenarios where applicable. Rerun every failed check after correction and every previously passing check whose assumptions changed.

When `$system-review` established affected scenarios, rerun every failed or invalidated scenario after implementation rather than starting a fresh broad review.

Verify the applicable architecture claims directly:

- callers rely on fewer implementation details;
- the demonstrated coordination or duplication is actually reduced;
- important behavior is testable through the intended interface;
- complexity and change knowledge are more local;
- every intended caller uses the new path;
- obsolete paths and speculative seams are absent;
- the result still satisfies repository requirements and ADRs.

Inspect the final diff for accidental scope growth, unrelated cleanup, compatibility residue, dead code, and temporary files. If the work cannot be completed or a required check is blocked, do not report `IMPROVED`. Restore only changes made by this invocation when that is safe; otherwise report the exact residuals as `BLOCKED`.

Stop after this objective. Other opportunities do not extend the current invocation.

**Complete when:** all required checks pass, the architectural benefit is observable, and task-related residue is removed.

## Output

Return:

### Architecture Improvement

- **Scope:** bounded target and revision
- **Disposition:** `IMPROVED` | `NO CHANGE` | `LOCAL HANDOFF` | `PLANNING HANDOFF` | `BLOCKED`
- **Evidence:** decisive repository evidence
- **Intervention gate:** pass/fail by condition, with only material reasons
- **Objective:** selected architectural change, local correction boundary, planning target, or `none`
- **Work completed:** changed behavior and structure, or `none`
- **Verification:** checks and scenarios actually run, including blocked checks
- **Residuals:** remaining task-related residue, or `none`
- **Reopen if:** concrete evidence or conditions that would change the disposition

For `NO CHANGE`, state that no credible candidate emerged or report the strongest rejected candidate and its decisive failure; do not fill the output with speculative observations.

For `PLANNING HANDOFF`, include the complete supported objective, constraints, migration boundary, and verification obligations as input to the surrounding `to-spec` or `to-tickets` workflow.

Report `IMPROVED` only after the `EXECUTE` route finishes implementation, verification, and cleanup.
