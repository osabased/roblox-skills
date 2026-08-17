## CodeGraph

In repositories with a `.codegraph/` directory at the repo root, use CodeGraph before grep/find or reading files when you need to understand or locate code:

- **MCP (when available):** use `codegraph_explore`. Name a file or symbol in the query when you need its current line-numbered source. If the tool is listed but deferred, load it by name via tool search.
- **Shell fallback:** `codegraph explore "<symbol names or question>"`.

Without `.codegraph/`, skip CodeGraph and leave indexing to the user.

## General

Use independent judgment rather than mechanically following the literal request. Optimize for the underlying intent, and identify material gaps, weak assumptions, or better approaches throughout the work. Minor improvements may be made silently; surface significant changes in scope, behavior, or approach before making them.

Sanity-check findings and conclusions before relying on or propagating them.

Ask yourself: “Was the process that led me here capable of finding the best answer in the first place?”

Do not assume either the user's framing or your own judgment is correct by default. When they conflict in a way that could materially affect the outcome, surface the disagreement, explain the relevant tradeoffs or alternatives, and give the user enough context to make an informed decision.

## Definition of Done

A task is **Clean Done** when:

- the assigned outcome works;
- every required verification check has passed; and
- task-related temporary work and avoidable residuals are cleaned up.

Use **Messy Done** only when the outcome works and verification passes, but known residuals remain because cleanup would be impossible or disproportionate in cost, risk, or scope. Report what remains, why it remains, and why further cleanup is impossible or disproportionate.

Otherwise the task is **Not Done**. Partial progress, blocked required checks, and inadequately verified work are Not Done.

Report Messy Done or Not Done when applicable. Routine Clean Done needs no status label.

## Verification

Delegate required verification checks to `luna_verifier`. Verification scope must cover applicable project-required checks, changed behavior, affected assumptions, and material regression risks introduced by the change.

Keep verification proportional to the scope and risk of the change.

The primary agent chooses the concrete checks and owns implementation, failure diagnosis, fixes, and the final Definition of Done. The verifier independently checks for material gaps in coverage.

After a fix, delegate reruns of every failed check and every previously passing check whose covered behavior or assumptions the fix changed. Verification is complete only when every required check passes.

A required check that cannot execute is BLOCKED. It makes the task Not Done; report the concrete blocker.

If `luna_verifier` is unavailable, use the narrowest suitable available subagent under the same ownership and completion rules. If no suitable subagent is available, run the required checks in the primary thread.

More-specific project verification instructions may override this section.

## Scenario-first behavioral testing

When testing, reviewing, checking for gaps, or evaluating behavior, think in terms of **behavioral scenarios** rather than isolated issues. A scenario should exercise a user path, sequence of actions, state transitions, or interactions between behaviors.

Consider relevant variations such as normal usage, edge cases, misuse, interruptions, retries, unexpected ordering, and unusual-but-possible behavior. Treat specific issues as findings within scenarios, not as the primary unit of testing.

When a requirement can reasonably be verified through behavior, test the behavior rather than inspecting implementation details or source structure. Use static/source-inspection checks when the requirement is inherently structural or when they provide distinct coverage that behavioral scenarios cannot.