---
name: roblox-RESOURCE-SLUG
description: USE-TRIGGER-IN-ONE-SENTENCE
---

# RESOURCE NAME

Use **RESOURCE NAME** for CAPABILITY. Guidance targets **VERSION/COMMIT/STATE** (source reviewed **YYYY-MM-DD**). Resource verification: **VERIFIED/UNVERIFIED/UNAVAILABLE**.

## Use when

- ...

## Do not use when

- ...

## Prerequisites and installation

1. ...

## Operational reconciliation

- Policy: REQUIRED/NOT-APPLICABLE — REASON
- Installed-state check: RESOURCE-SPECIFIC CHECK OR IMMUTABLE-INSTALL EXPLANATION
- Expected identity/state: RESOURCE SLUG + CANONICAL URL + PACKAGE ID WHEN APPLICABLE + REVIEWED VERSION/COMMIT/STATE
- Parent-state check: Load matching schema-version 2 resource records and resource-bound learnings by resource slug plus canonical identity.
- Mismatch/unknown action: Stop the affected version-sensitive use and invoke `roblox-resource-acquisition` in `repair/reconcile` mode.
- Defect handoff: Capture the task, installed state, expected and observed behavior, and smallest reproduction; then invoke `roblox-resource-acquisition` in `repair/reconcile` mode.

## Common path

Provide the shortest source-grounded setup/use sequence. Do not call it runtime-verified unless the recorded resource verification status is `verified`.

```luau
-- Minimal example grounded in the reviewed source/API.
```

## Client/server placement

State where modules and calls belong on both client and server, what crosses the boundary, and what authority the server must retain. If one side must not use the resource, say so explicitly.

## Mental model

Explain the minimum concepts needed to use the resource correctly.

## Lifecycle and cleanup

- Initialization: ...
- Reuse: ...
- Cleanup/destruction: ...

## API used by this skill

Document only source-grounded public APIs that the agent needs frequently; distinguish source review from runtime verification.

## Failure modes

### Symptom

Likely cause -> diagnosis -> repair.

## Limitations

- ...

## Security notes

State the applicable resource-specific trust boundaries and mitigations. If none are special to this resource, say so explicitly. Preserve server authority; never embed secrets in source.

## Verify after installation

Run: ...

Pass condition: ...

Both lines must be concrete enough for another agent to execute/check; do not use placeholders or generic outcomes such as “check it” or “it works.”

## Alternatives

Compare against the closest Roblox built-in or credible alternative. If none is meaningful, state why.

## Provenance

- Resource slug: RESOURCE-SLUG
- Package identity: PACKAGE-ID (or explicitly state that the resource has no package identity)
- DevForum: HTTPS URL (or explicitly state that no DevForum topic is used/applicable)
- Canonical source/docs: HTTPS URL (or explicitly state that no separate canonical source exists when the DevForum topic above is the canonical source)
- Source version/release/commit: IDENTIFIER (immutable version/commit, an explicitly labeled named tag/release/build, or a dated explicit source state; not bare latest/current/main/HEAD)
- Source review date: YYYY-MM-DD
- Resource verification: VERIFIED/UNVERIFIED/UNAVAILABLE

## Version drift

Before using newer upstream versions, check release notes/source for changes affecting the APIs and behavior documented above. Re-review material changes before updating this skill's source state, and rerun runtime proof when the claimed verification status would otherwise become stale.

