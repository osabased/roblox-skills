---
name: subjective-taste-alignment
description: Align consequential subjective choices with the user's applicable taste, current intent, constraints, ownership, and delegated authority. Use when creative direction is uncertain or a preference-sensitive choice could propagate into costly work.
---

# Subjective Taste Alignment

Prevent uncertain, load-bearing subjective assumptions from propagating when a cheaper representative check can validate or correct them. Keep taste, intent, constraints, ownership, and authority distinct.

## Use when

- Creative direction is uncertain and the choice would propagate into costly downstream work.
- A preference-sensitive decision arises before a cheaper representative check could validate or correct it.

## Do not use when

- The choice is purely mechanical or trivially reversible.
- Explicit written constraints fully govern the outcome and leave no subjective residue to align.

## Common path

1. Establish the host capability contract through the capability contract reference.
2. Resolve one `AlignmentRequest`, then authorize propagation before material output.
3. Compose scoped profile knowledge and persist every change through `ProfilePersistence`.

## Mental model

One canonical alignment core turns applicable taste, intent, constraints, ownership, and authority into request inputs; every subsystem stays a separate capability boundary reached through its disclosed contract.

## Alternatives

Closest alternative: unaided judgment with no reusable, reconcilable profile state. Roblox built-ins and engine APIs provide no cross-session taste tracking, so none is a meaningful substitute for this capability.

## Establish the host contract

Before reading, writing, or relying on reusable profile state, read [references/capability-contract.md](references/capability-contract.md). Declare every required host capability using a directly observable mechanism or a behavior-preserving fallback. Start from [references/host-capabilities.json](references/host-capabilities.json) only in this repository host; reassess it when the host or active tools change.

Use `scripts/alignment_harness.py` to assess the declaration when Python is available. Otherwise apply the same contract explicitly. A missing mechanism and missing safe fallback is an implementation blocker.

Profile composition, evidence reconciliation, reference handling, autonomy presets, exploration, downstream reconciliation, profile lifecycle, and domain adapters remain separate capability boundaries.

## Resolve material subjective decisions

Read [references/active-alignment-contract.md](references/active-alignment-contract.md). Build one `AlignmentRequest` whose applicable taste, intent, constraints, ownership, authority, experimental state, craft priors, and provisional judgment remain separate. Resolve it through `resolve_alignment` from `scripts/alignment_harness.py`.

Use only applicable input state that the active host can support. Preserve unsupported profile lookup or scope applicability as unresolved under the host contract; do not invent knowledge to populate the request.

Before material propagation, call `authorize_propagation` with the resolved result and the current request. A stale result, unresolved dimension, conflict, or checkpoint obligation blocks propagation until current state is re-resolved or the required checkpoint occurs. Delegated or craft-based execution remains authorized agent judgment and never becomes user-taste evidence by implementation alone.

## Compose scoped profile knowledge

Before using reusable profile knowledge or scoped authority in an `AlignmentRequest`, read [references/profile-composition-contract.md](references/profile-composition-contract.md). Build one `CompositionRequest` from the active represented subject, exact scope identities, target context, exposed domain properties, ownership, evidence applicability, explicit overrides, and candidate authority. Call `compose_profiles`, then use `result.alignment_dimensions`, `result.alignment_taste`, `result.alignment_authority`, and `result.context_revision(host_revision)` as the request's section-qualified inputs and context revision. Derive other interacting dimensions from `PropertyPath.alignment_dimension`; do not manually join path components. After `resolve_alignment`, call `enforce_relational_alignment` and use its returned alignment for propagation checks.

Treat `result.conflicts` as unresolved. Keep excluded, overridden, and inactive-authority records available for history and inspection without applying them. Use `transition_local_scope` for duplicate, branch, copy, or move operations; an ambiguous identity transition requires its returned checkpoint before target-local knowledge can apply.

## Persist canonical profile state

Before storing, loading, exchanging, or migrating profile state, read [references/profile-persistence-contract.md](references/profile-persistence-contract.md). Use `ProfilePersistence` as the only storage mutation seam with optimistic revisions; treat conflicts as reload-and-reconcile signals, never as overwrites. Persistence never strengthens, flattens, broadens, or reinterprets knowledge, and persistence authorship is not additional preference evidence.

## Operate the subsystems through their contracts

Before using evidence learning, references, autonomy presets, probes, exploration, reconciliation, profile controls or lifecycle operations, stakeholder ownership, or domain adapters, read [references/subsystem-contracts.md](references/subsystem-contracts.md). Each subsystem composes through the canonical alignment core and its documented invariants.

## Develop observable behavior

For scenario work, read [references/scenario-harness.md](references/scenario-harness.md). Exercise user paths and state changes through the harness interface, including applicable retry, interruption, restart, and cross-feature behavior.

For acceptance work, read [references/acceptance-traceability.md](references/acceptance-traceability.md). Every canonical final criterion needs a named, passing scenario or structural check with an explicit oracle before the skill can be reported complete.

## Prerequisites and installation

1. Provide Python 3.8+ with standard library only for harness assessment; without Python, apply the same contracts explicitly.
2. Copy `SKILL.md`, `references/`, `scripts/`, and `agents/` from the reviewed repository commit named under Provenance.
3. Record that exact commit in `.roblox-resources/records/subjective-taste-alignment.yaml`.

## API used by this skill

Call `resolve_alignment` and `authorize_propagation` through `scripts/alignment_harness.py`; call `compose_profiles` and `enforce_relational_alignment` through `scripts/profile_composition.py`; mutate storage only through `ProfilePersistence`.

## Client/server placement

Client side: this package never runs inside a Roblox client and injects nothing into gameplay. Server side: it executes no server code and touches no replicated state, so server authority over game state remains entirely outside its reach.

## Lifecycle and cleanup

- Initialization: none; modules are import-safe with no global setup step.
- Reuse: stateless calls whose behavior depends only on passed-in state and host-owned profile stores.
- Cleanup/destruction: none required; hosts own retention and deletion of persisted profile data.

## Failure modes

### Propagation blocked unexpectedly

A stale result, unresolved dimension, or open checkpoint obligation is active. Re-resolve against current state or complete the required checkpoint, then retry the authorization call.

### Import fails with an identity conflict

The same operation or event id was reused with divergent content. Treat the histories as distinct operations instead of merging them silently.

## Limitations

- Unsupported host capabilities must remain unresolved rather than invented.
- Scenario execution and harness assessment require Python.

## Security notes

No resource-specific trust boundaries exist beyond normal Roblox server-authoritative expectations. Scripts are offline standard-library Python with no network access; never store credentials or account identifiers in profile state.

## Verify after installation

Run: `python -m pytest tests -q` from this package directory.
Pass condition: the run output shows `216 passed` and no failed count appears.

## Version drift

None occurs independently: each install pins one immutable reviewed commit and behavior depends only on that copied tree, so any update is a new reviewed commit plus an authorized reinstall. After any reinstall, re-validate by running `python -m pytest tests -q` and confirming the recorded-commit diff stays empty.

## Operational reconciliation

- Policy: not-applicable — installation is a plain copy pinned to one immutable reviewed commit, and documented behavior depends only on that copied tree, so nothing drifts independently; updates are fresh reviewed commits followed by authorized reinstall.
- Installed-state check: compare the host copy against the recorded commit, for example `git diff --stat <recorded-commit> -- subjective-taste-alignment` must be empty and installed files must hash-match their repo counterparts.
- Expected identity/state: slug subjective-taste-alignment at https://github.com/osabased/roblox-skills, exact commit recorded in `.roblox-resources/records/subjective-taste-alignment.yaml` (reviewed source state dated 2026-08-23).
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
