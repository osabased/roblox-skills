# Generated Resource Skill Contract

A generated resource skill is ready for validation only if it contains all of the following information.

## Required identity

- stable skill name/slug;
- resource name;
- one-sentence capability description;
- reviewed source version, release, commit, or explicit dated source state; named non-numeric tags/releases should be labeled explicitly (for example `tag: Spring-2026`); floating labels such as `latest`, `current`, `main`, or `HEAD` are not pins unless paired with an immutable identifier or dated source state;
- explicit resource verification status: `verified`, `unverified`, or `unavailable`; source review/provenance alone must never be presented as runtime verification;
- exact DevForum topic provenance over HTTPS when applicable; if no DevForum topic is used/applicable, state that explicitly rather than inventing one; include a distinct canonical source/docs HTTPS URL when one exists, and if the DevForum thread is itself the only canonical source, say so explicitly instead of duplicating the same URL; at least one concrete HTTPS source URL must remain recoverable;

## Required decision guidance

- when to use the resource;
- when not to use it;
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

## Context economy

The skill should make the common path obvious in the first screenful or two, with deeper edge cases below or in references. A generated skill that forces an agent to reread an upstream manual for basic use has failed its purpose.
