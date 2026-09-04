# Execute the Improvement

Use this branch only after the main skill selects `EXECUTE`. The Intervention Gate remains authoritative throughout implementation. Return to the earliest affected step when new evidence invalidates its premise.

## 1. Design the bounded change

Trace every affected caller, dependency, invariant, state owner, test surface, failure semantic, and migration step. Design the smallest coherent change that captures the supported benefit.

Prefer deep modules, useful interfaces, locality, and real seams. Replace obsolete structure instead of retaining parallel architectures unless compatibility evidence requires a transition.

When a consequential interface has materially different credible shapes, use `$codebase-design`'s design-it-twice method. If supported alternatives remain genuinely competitive, return to route selection and invoke `$direction-selection` before committing to one.

Define before editing:

- behavior that must remain unchanged;
- any authorized behavior change;
- the new module, interface, or seam;
- complete caller and data migration;
- behavioral scenarios and regression checks;
- observable architectural success evidence;
- rollback or recovery considerations when material.

When the change affects cross-part contracts, authority, retries, ordering, concurrency, durability, deployment compatibility, recovery, or operational failure paths, invoke `$system-review` for those affected scenarios and constraints.

**Complete when:** the design, migration, and verification plan cover the full objective without an unresolved material gap.

## 2. Implement

Preserve pre-existing user changes. Modify only the selected objective and its necessary callers, tests, types, and directly affected documentation.

Use `$tdd` when available and behavior can be captured through a red-green-refactor loop. Otherwise establish the smallest reliable feedback loop before restructuring.

Keep externally observable behavior stable except for authorized changes. Migrate every intended caller, then remove obsolete paths, duplicate orchestration, temporary adapters, and dead abstractions.

When implementation evidence weakens the demonstrated need, architectural cause, compatibility case, or migration completeness, return to the earliest affected main-skill step and choose the supported disposition.

**Complete when:** the coherent objective and complete migration are implemented without an unintended mixed architecture.

## 3. Verify and clean up

Run every relevant repository check, focused behavioral test, and broader regression check justified by the affected surface. Exercise normal usage and material edge, failure, retry, ordering, and migration scenarios where applicable. After a correction, rerun each failed check and each previously passing check whose assumptions changed.

When `$system-review` established affected scenarios, rerun every failed or invalidated scenario rather than beginning a new broad review.

Verify each applicable architecture claim directly:

- callers rely on fewer implementation details;
- demonstrated coordination or duplication is reduced;
- important behavior is testable through the intended interface;
- complexity and change knowledge are more local;
- every intended caller uses the new path;
- obsolete paths and speculative seams are absent;
- repository requirements and ADRs remain satisfied.

Inspect the final diff for scope growth, unrelated cleanup, compatibility residue, dead code, and temporary files. Remove task-created reconnaissance and implementation artifacts.

When a required check is blocked or the objective remains incomplete, withhold `IMPROVED`. Restore only changes made by this invocation when restoration is safe; otherwise retain the exact residuals and return `BLOCKED` through the main output contract.

Stop after this objective. Other opportunities belong to later invocations.

**Complete when:** all required checks pass, the claimed architectural benefit is observable, and task-related residue is removed. Return to the main skill's Output section.