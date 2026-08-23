---
name: subjective-taste-alignment
description: Align consequential subjective choices with the user's applicable taste, current intent, constraints, ownership, and delegated authority. Use when creative direction is uncertain or a preference-sensitive choice could propagate into costly work.
compatibility: Python 3.8+ is required for executable harness and scenario checks. Without Python, apply the same contracts explicitly and report executable verification as unavailable rather than pretending it ran.
---

# Subjective Taste Alignment

Prevent uncertain, load-bearing subjective assumptions from propagating when a cheaper representative check can validate or correct them. Keep taste, intent, constraints, ownership, and authority distinct.

## Use when

- Creative direction is uncertain and the choice would propagate into costly downstream work.
- A preference-sensitive decision arises before a cheaper representative check could validate or correct it.

## Do not use when

- The choice is purely mechanical or trivially reversible.
- Explicit written constraints fully govern the outcome and leave no subjective residue to align.

## Choose the least stateful mode

Use the least stateful mode that satisfies the decision.

### Ephemeral alignment

Use ephemeral alignment when the decision can be resolved entirely from current-task inputs and no reusable cross-session preference knowledge, profile mutation, or persistent authority state is required. Typical inputs are the user's current instructions, directly supplied references, current artifact intent, explicit constraints, current ownership requirements, and task-local delegated authority.

Ephemeral alignment still uses the canonical `AlignmentRequest` semantics and propagation guard. It does **not** create, infer, load, or mutate profile state merely to make the decision reusable. Do not convert one-off execution choices into evidence of enduring taste.

### Profile-backed alignment

Use profile-backed alignment when the current decision needs applicable reusable profile knowledge or scoped authority, when the user explicitly wants preferences learned or reused across work, or when profile lifecycle/reconciliation is itself part of the task.

Before relying on reusable state, establish the host capability contract, compose applicable profile knowledge, and persist every mutation through `ProfilePersistence`.

## Common path

1. Choose ephemeral or profile-backed alignment.
2. Build and resolve one `AlignmentRequest` using only applicable state.
3. Authorize propagation before material downstream use.
4. For profile-backed work only, establish host capabilities, compose scoped profile knowledge, and persist state changes through the documented contracts.

## Mental model

One canonical alignment core turns applicable taste, intent, constraints, ownership, and authority into request inputs. Persistence and profile composition are optional capability layers used only when reusable state is actually part of the decision.

## Alternatives

For an ephemeral decision, the closest alternative is unaided judgment with no explicit alignment contract. For reusable preference state, Roblox built-ins and engine APIs provide no cross-session taste tracking, so none is a meaningful substitute for that capability.

## Establish the host contract when state or host facts require it

Before reading, writing, or relying on reusable profile state—or before material alignment relies on host facts whose observability matters—read [references/capability-contract.md](references/capability-contract.md). Declare every required host capability using a directly observable mechanism or a behavior-preserving fallback. Start from [references/host-capabilities.json](references/host-capabilities.json) only in this repository host; reassess it when the host or active tools change.

A purely ephemeral alignment whose decision-bearing inputs are directly present in the current task and that does not rely on persistence, cross-session scope identity, external authorship, source-addressability claims, or unavailable execution surfaces may skip profile-related host capability work.

Use `scripts/alignment_harness.py` to assess the declaration when Python is available. Otherwise apply the same contract explicitly. A missing mechanism and missing safe fallback is an implementation blocker for behavior that depends on that capability.

Profile composition, evidence reconciliation, reference handling, autonomy presets, exploration, downstream reconciliation, profile lifecycle, and domain adapters remain separate capability boundaries.

## Resolve material subjective decisions

Read [references/active-alignment-contract.md](references/active-alignment-contract.md). Build one `AlignmentRequest` whose applicable taste, intent, constraints, ownership, authority, experimental state, craft priors, and provisional judgment remain separate.

For ephemeral alignment, populate the request only from current-task evidence whose applicability is directly established. Leave absent knowledge absent; do not synthesize a profile, enduring preference, or historical authority grant. For profile-backed alignment, use only applicable state that the active host and profile-composition contract support.

When Python is available, resolve through `resolve_alignment` from `scripts/alignment_harness.py`. Otherwise apply the same per-dimension resolution semantics explicitly and report harness execution as unavailable.

Before material propagation, use `authorize_propagation` with the resolved result and current request when the harness is available; otherwise perform the equivalent current-state, unresolved-dimension, conflict, and checkpoint checks explicitly. A stale result, unresolved dimension, conflict, or checkpoint obligation blocks propagation until current state is re-resolved or the required checkpoint occurs. Delegated or craft-based execution remains authorized agent judgment and never becomes user-taste evidence by implementation alone.

## Compose scoped profile knowledge

This section applies only when reusable profile knowledge or scoped reusable authority participates in the decision.

Read [references/profile-composition-contract.md](references/profile-composition-contract.md). Build one `CompositionRequest` from the active represented subject, exact scope identities, target context, exposed domain properties, ownership, evidence applicability, explicit overrides, and candidate authority. Call `compose_profiles`, then use `result.alignment_dimensions`, `result.alignment_taste`, `result.alignment_authority`, and `result.context_revision(host_revision)` as the request's section-qualified inputs and context revision. Derive other interacting dimensions from `PropertyPath.alignment_dimension`; do not manually join path components. After `resolve_alignment`, call `enforce_relational_alignment` and use its returned alignment for propagation checks.

Treat `result.conflicts` as unresolved. Keep excluded, overridden, and inactive-authority records available for history and inspection without applying them. Use `transition_local_scope` for duplicate, branch, copy, or move operations; an ambiguous identity transition requires its returned checkpoint before target-local knowledge can apply.

## Persist canonical profile state

This section applies only when profile state is stored, loaded, exchanged, migrated, or mutated.

Read [references/profile-persistence-contract.md](references/profile-persistence-contract.md). Use `ProfilePersistence` as the only storage mutation seam with optimistic revisions; treat conflicts as reload-and-reconcile signals, never as overwrites. Persistence never strengthens, flattens, broadens, or reinterprets knowledge, and persistence authorship is not additional preference evidence.

## Operate the subsystems through their contracts

Before using evidence learning, references, autonomy presets, probes, exploration, reconciliation, profile controls or lifecycle operations, stakeholder ownership, or domain adapters, read [references/subsystem-contracts.md](references/subsystem-contracts.md). Each subsystem composes through the canonical alignment core and its documented invariants. Do not load or operate a subsystem merely because it exists; use it only when the current alignment requires that capability.

## Develop observable behavior

For scenario work, read [references/scenario-harness.md](references/scenario-harness.md). Exercise user paths and state changes through the harness interface, including applicable retry, interruption, restart, and cross-feature behavior.

For acceptance work, read [references/acceptance-traceability.md](references/acceptance-traceability.md). Every canonical final criterion needs a named, passing scenario or structural check with an explicit oracle before the skill can be reported complete.

## Prerequisites and installation

1. Provide Python 3.8+ for executable harness/scenario assessment; without Python, apply the same contracts explicitly and do not claim executable verification.
2. Resolve the exact immutable source revision being installed from the repository or installation source, then copy `SKILL.md`, `references/`, `scripts/`, and `agents/` from that revision.
3. Record that resolved revision in `.roblox-resources/records/subjective-taste-alignment.yaml`. The dated reviewed source state in Provenance identifies the reviewed source state but is not itself an embedded commit identifier.

## API used by this skill

Call `resolve_alignment` and `authorize_propagation` through `scripts/alignment_harness.py`; call `compose_profiles` and `enforce_relational_alignment` through `scripts/profile_composition.py` when profile-backed alignment requires composition; mutate storage only through `ProfilePersistence` when persistence is in scope.

## Client/server placement

Client side: this package never runs inside a Roblox client and injects nothing into gameplay. Server side: it executes no server code and touches no replicated state, so server authority over game state remains entirely outside its reach.

## Lifecycle and cleanup

- Initialization: none; modules are import-safe with no global setup step.
- Reuse: ephemeral alignment is task-local; profile-backed calls depend only on passed-in state and host-owned profile stores.
- Cleanup/destruction: none required; hosts own retention and deletion of persisted profile data.

## Failure modes

### Propagation blocked unexpectedly

A stale result, unresolved dimension, conflict, or open checkpoint obligation is active. Re-resolve against current state or complete the required checkpoint, then retry the propagation check.

### Import fails with an identity conflict

The same operation or event id was reused with divergent content. Treat the histories as distinct operations instead of merging them silently.

## Limitations

- Unsupported host capabilities must remain unresolved rather than invented when the selected mode depends on them.
- Scenario execution and harness assessment require Python.
- Ephemeral alignment deliberately creates no durable preference memory.

## Security notes

No resource-specific trust boundaries exist beyond normal Roblox server-authoritative expectations. Scripts are offline standard-library Python with no network access; never store credentials or account identifiers in profile state.

## Verify after installation

Run: `python -m pytest tests -q` from this package directory.

Pass condition: pytest process status equals `0`, and the output contains no failed or error count. Do not bind installation validity to an exact number of collected tests; legitimate test additions must not make an otherwise passing suite fail this contract.

## Version drift

Each installed copy is pinned by the exact immutable source revision recorded externally in `.roblox-resources/records/subjective-taste-alignment.yaml`. Behavior does not drift independently from that copied tree; an update is a newly resolved/reviewed revision plus an authorized reinstall. After any reinstall, re-run the test suite and confirm the installed tree matches the recorded revision.

## Operational reconciliation

- Policy: not-applicable — installation is a plain copy pinned to one immutable reviewed revision, and documented behavior depends only on that copied tree, so nothing drifts independently; updates are fresh reviewed revisions followed by authorized reinstall.
- Installed-state check: compare the host copy against the revision recorded in `.roblox-resources/records/subjective-taste-alignment.yaml`; the installed files must match that recorded source tree.
- Expected identity/state: slug `subjective-taste-alignment` at `https://github.com/osabased/roblox-skills`, with the exact installed revision recorded externally rather than self-referentially embedded in this file.
- Parent-state check: load schema-version 2 records and resource-bound learnings matching slug plus canonical identity from `<project-root>/.roblox-resources/records/`, then `~/.roblox-resources/records/`, per roblox-resource-acquisition operational-lifecycle guidance.
- Mismatch/unknown action: stop affected uses and invoke `roblox-resource-acquisition` in repair/reconcile mode.
- Defect handoff: capture task, installed state, expected versus observed behavior, and smallest reproduction, then invoke `roblox-resource-acquisition` in repair/reconcile mode.

## Provenance

- Resource slug: subjective-taste-alignment
- Package identity: not applicable because this first-party package ships directly from its own repository without any registry artifact
- DevForum: No DevForum topic is applicable.
- Canonical source/docs: https://github.com/osabased/roblox-skills
- Source version/release/commit: reviewed source state dated 2026-08-23
- Source review date: 2026-08-23
- Resource verification: unverified
