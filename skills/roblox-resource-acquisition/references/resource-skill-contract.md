# Generated Resource Skill Contract

A generated resource skill is ready for validation only if it contains all of the following information.

## Required identity

- stable skill name/slug;
- resource name;
- stable resource slug used by matching external records/learnings;
- canonical resource identity (`canonical_url`, plus `package_id` when applicable);
- one-sentence capability description;
- reviewed source version, release, commit, or explicit dated source state; named non-numeric tags/releases should be labeled explicitly (for example `tag: Spring-2026`); floating labels such as `latest`, `current`, `main`, or `HEAD` are not pins unless paired with an immutable identifier or dated source state;
- explicit resource verification status: `verified`, `unverified`, or `unavailable`; source review/provenance alone must never be presented as runtime verification;
- exact DevForum topic provenance over HTTPS when applicable; if no DevForum topic is used/applicable, state that explicitly rather than inventing one; include a distinct canonical source/docs HTTPS URL when one exists, and if the DevForum thread is itself the only canonical source, say so explicitly instead of duplicating the same URL; at least one concrete HTTPS source URL must remain recoverable;

## Required decision and behavioral purpose

A generated skill is not complete merely because it documents the resource. It must make clear:

- when it should activate/use the resource;
- when not to use it;
- what failure mode or recurring integration problem the guidance prevents;
- what the agent should do differently because this skill exists;
- how that changed behavior can be validated;
- project assumptions/prerequisites;
- an explicit alternatives section naming the closest meaningful alternative or Roblox built-in when relevant; if none is meaningful, state that explicitly with a short reason.

## Required operating knowledge

- installation/placement;
- minimal mental model;
- only the public API surface necessary for common tasks, or an explicit statement that the resource exposes no callable API;
- initialization and cleanup lifecycle;
- client/server placement and authority, explicitly covering both sides even when the resource is intentionally one-sided;
- concise working examples derived from source-grounded APIs, with runtime-verification claims only when the resource verification status supports them;
- known limitations;
- common failure modes and diagnosis.

## Required safety guidance

Include a **Security notes** section in every generated skill. When no resource-specific trust boundary exists, state that explicitly and preserve normal Roblox server-authoritative expectations. When applicable, cover:

- remote/client input validation expectations;
- secrets/external HTTP handling;
- dynamic `require`/asset-loading implications;
- auto-update/version drift implications;
- data persistence/destructive behavior.

## Required verification

Provide a small verification recipe an agent can run after installation. It must include a concrete runnable/checkable step and a specific observable pass condition; placeholders or generic statements such as “check it” / “it works” do not satisfy this contract. It must not claim stronger coverage than it provides.

## Required operational reconciliation

Include an **Operational reconciliation** section containing these labeled fields:

- `Policy`: exactly `required` or `not-applicable` followed by a concrete reason;
- `Installed-state check`: a resource-specific command, file/manifest inspection, package/asset identity check, or an explicit immutable-install explanation;
- `Expected identity/state`: the canonical identity and reviewed version/commit/source state the guidance targets;
- `Parent-state check`: how to load matching schema-version 2 resource records and resource-bound learnings by slug plus canonical identity;
- `Mismatch/unknown action`: stop the affected version-sensitive use and invoke `roblox-resource-acquisition` in `repair/reconcile` mode;
- `Defect handoff`: capture the task, installed state, expected/observed behavior, and smallest reproduction, then invoke the same parent repair route.

Use `required` when installed resource state can drift independently and the guidance is materially version-sensitive. Use `not-applicable` only when the install is fixed to the exact immutable reviewed state or the documented behavior is demonstrably insensitive to independent drift. Unknown material state never counts as a match.

The child does not bundle the external learnings store. It consults matching external state during direct use and treats a current `blocked_use_or_version` as a stop, while re-checking adverse learnings as observations rather than executable policy.

## Prohibited behavior

The skill must not:

- invent undocumented APIs;
- present old examples as current without a version warning;
- reproduce large portions of upstream documentation unnecessarily;
- hide transitive dependencies;
- call a resource "safe" merely because it is popular/open source;
- make auto-update the default for third-party packages without considering supply-chain risk;
- require human confirmation for routine reversible engineering steps unless the surrounding environment requires it;
- silently publish places, expose credentials, spend money, or mutate production data.
- call a validated artifact operational merely because it exists in a filesystem location;
- continue version-sensitive guidance through an unresolved identity/version mismatch or matching current block.

## Context economy

The skill should make the common path obvious in the first screenful or two, with deeper edge cases below or in references. A generated skill that forces an agent to reread an upstream manual for basic use has failed its purpose.

