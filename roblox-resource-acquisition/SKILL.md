---
name: roblox-resource-acquisition
description: Evaluate, acquire, adopt, refresh, repair, or reconcile Roblox community resources and their reusable agent skills. Use when a task actually needs a community resource decision or existing resource-skill lifecycle work; do not activate merely because a third-party dependency could be used.
compatibility: Scripts require Python 3.8+ and PyYAML (pip install -r requirements.txt). Scripts exit with code 2 and an install hint when PyYAML is missing.
---

# Roblox Resource Acquisition

Acquire Roblox community tooling only when it is justified by the task. Treat user/project-curated resources as trusted policy choices while keeping trust separate from runtime verification and from validation of any generated skill.

## Core rule

Do not turn the first plausible DevForum result into a skill, and do not acquire a dependency just because one exists.

For a capability-directed task with no positive resource target, prefer a Roblox built-in, an adequate authorized project capability, or a small local implementation when it solves the need cleanly. Resource acquisition becomes live only when a community resource is materially useful, explicitly targeted, being compared, being integrated or used, being adopted as reusable guidance, or already has lifecycle state that must be refreshed, repaired, or reconciled.

Curation is an explicit trust decision by the user/project. **Trusted does not mean verified.** A resource passing its own tests also does not prove that an agent can use it correctly.

## Route the operating mode

Choose the narrowest mode that satisfies the request, then read only the references required by that mode.

### `evaluate/compare`

Use when the task is to inspect, evaluate, compare, or select a resource without using/integrating it or creating/operationally adopting reusable child guidance.

1. Read [references/qualification-workflow.md](references/qualification-workflow.md).
2. Read [references/state-policy.md](references/state-policy.md) for truthful trust/verification status and output discipline.
3. Stop after the requested evidence and decision. Do not integrate the resource or generate a child skill as extra scope.

### `acquire/adopt`

Use when the task requires selecting, using, installing, or integrating a resource beyond evaluation. Reusable child guidance and operational host adoption are optional subscopes, not prerequisites for this mode.

1. Read [references/qualification-workflow.md](references/qualification-workflow.md).
2. Integrate or use the resource only to the authorized task/project scope after its applicable qualification and verification requirements are satisfied.
3. When reusable child guidance is in scope, read [references/generation-validation.md](references/generation-validation.md).
4. Apply host adoption and reconciliation semantics from [references/operational-lifecycle.md](references/operational-lifecycle.md) only when operational adoption of generated guidance is requested.
5. Read [references/state-policy.md](references/state-policy.md) before recording state or reporting completion.

### `refresh`

Use for an existing resource skill whose canonical identity is known and whose source/version facts or generated guidance may have drifted.

1. Confirm canonical identity and installed/recorded state first; do not restart broad discovery unless current evidence makes the resource materially unsuitable or alternatives were requested.
2. Read only the affected parts of [references/qualification-workflow.md](references/qualification-workflow.md) needed to refresh volatile source/version/API facts.
3. Read [references/generation-validation.md](references/generation-validation.md) to patch and rerun the structural and behavioral checks invalidated by the refresh.
4. If the refresh exposes a defect, mismatch, or blocked adoption, read [references/repair-reconcile-workflow.md](references/repair-reconcile-workflow.md).
5. Read [references/state-policy.md](references/state-policy.md) before updating records or status.

### `repair/reconcile`

Use for a generated child defect, installed/source-state mismatch, adverse current observation, legacy child/record state, or a newer parent-side block.

1. Reconcile the canonical identity, recorded state, installed state, and affected host adoption before changing status.
2. Read [references/repair-reconcile-workflow.md](references/repair-reconcile-workflow.md).
3. Read [references/qualification-workflow.md](references/qualification-workflow.md) only when current upstream facts or trust qualification are themselves in question.
4. Read [references/generation-validation.md](references/generation-validation.md) only for the validation surfaces invalidated by the repair.
5. Read [references/state-policy.md](references/state-policy.md) before recording the outcome.

## Shared invariants

Hold these across every mode:

- Preserve positive resource targets, their roles, selectors, and requested scope; do not silently substitute an alternative.
- Treat technical fit, trust, verification, generated-skill validation, installation, and operational host adoption as separate states.
- Project presence, popularity, naming similarity, or successful parsing is not evidence of trust or correctness.
- Bind trust and evidence to canonical identity plus any material selector/version; same-named forks, mirrors, modified vendored copies, and re-uploads do not inherit it automatically.
- Prefer primary/canonical sources for resource behavior and current Roblox Creator Hub documentation for platform behavior when material.
- Never invent an API from naming conventions or analogous libraries.
- Never label an unexecuted runtime check as passing. Use `unverified`, `unavailable`, or `failed` truthfully.
- Keep resource proof proportional to the intended use and use isolated/reversible verification where practical.
- Preserve Roblox server authority, validate client-controlled inputs, and never expose credentials or secrets merely to validate a resource.
- Do not publish, spend money, or perform irreversible project mutations merely to prove a resource works.
- Generate reusable child guidance only when that lifecycle scope is requested or required by the task; evaluation or ordinary resource integration alone grants no generation or host-adoption authority.
- A generated child is a second product with its own structural and behavioral validation burden.
- Repair in bounded cycles; do not lower the bar, silently rewrite trust, or endlessly polish around a fundamental mismatch.
- Keep user/project curated registry data and durable learnings outside this package according to the referenced contracts.

## Completion

A mode is complete only when its requested decision or lifecycle action is finished, every applicable verification/validation status is truthful, and any blocked use, unavailable proof, owner action, or reconciliation mismatch is explicit. Use [references/state-policy.md](references/state-policy.md) for the final reporting contract.
