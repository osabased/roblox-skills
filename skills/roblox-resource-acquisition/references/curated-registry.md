# External Curated Resource Registry

The curated registry contains **user/project-selected trusted Roblox resources**. It is mutable user/project data and must remain outside the `roblox-resource-acquisition` skill package so upgrading/replacing the skill cannot overwrite curation choices.

## Trust semantics

**Presence in the curated registry means trusted by policy.**

Curation answers: "Am I willing to use this canonical resource without making it re-earn trust from scratch?"

Trust attaches to the entry's stable `slug` plus canonical upstream identity (`canonical_url`, and `package_id` when present). It does **not** attach merely to a display name, similarly named resource, mirror, fork, re-upload, or alternate package coordinate. A fork/replacement with a different canonical identity needs its own curated entry or an explicit edit to the existing entry.

Curation does **not** answer:

- whether the current upstream version is unchanged;
- whether a particular API/integration fact is current;
- whether this exact version has been runtime-tested here;
- whether a generated agent skill correctly teaches the resource.

Track those facts separately as verification evidence.

## Registry locations

Resolve registries in this order:

1. an explicit curated-registry path supplied by the user/project/environment;
2. `<project-root>/.roblox-resources/curated/` when present;
3. `~/.roblox-resources/curated/` when present.

If more than one registry exists, merge entries by required `slug`. A project-local entry overrides a user-global entry with the same slug because the narrower project policy is more specific. An explicitly supplied registry has highest precedence. Do not use filenames as identity or precedence keys.

Do not create either directory merely to perform acquisition. If no registry exists, continue to normal discovery. Create or mutate registry state only when explicitly requested by the user or required by an explicit project policy.

## Entry format

Use `templates/curated-resource.yaml` as the portable default. One resource per `.yaml`/`.yml` file keeps ownership, diffs, deletion, and project overrides simple.

Required identity/decision fields:

- `schema_version: 1`;
- stable lowercase kebab-case `slug`;
- human-readable `name`;
- at least one `capabilities` entry;
- at least one `use_when` entry;
- `canonical_url` pointing to the canonical upstream source/docs/project identity;
- non-empty `curation_reason`.

Optional fields:

- `avoid_when`;
- exact `package_id` when the resource has a canonical package coordinate;
- non-authoritative `install_hint`;
- `devforum_url` pointing to the specific DevForum topic used as provenance/discussion;
- `last_reviewed` and `notes`.

`canonical_url` is part of the trust identity. `package_id`, when present, is also part of the identity. `install_hint` is only convenience text and must never substitute for current installation verification.

Keep entries compact and decision-oriented. Curation is not documentation duplication.

Do not require a validation record inside the curated entry. Trust state comes from membership; verification belongs in `templates/resource-record.yaml` or the host environment's evidence registry.

## Validate registry structure

Run:

`python scripts/validate_curated_registry.py <registry-path> [<registry-path> ...]`

The validator checks the schema, stable slugs, canonical URLs, field types, dates, and duplicate slugs. It validates **structure and identity only**. Passing does not prove quality, safety, maintenance, compatibility, or runtime behavior and must never auto-curate a resource.

When multiple registry paths are supplied, pass them in resolution/preference order (highest precedence first). Duplicate slugs inside one registry are errors. The same slug across separate registries is allowed and reported as an override; the earlier registry wins.

Run structural validation after manually adding/editing curated entries when practical. A malformed entry must not be silently treated as trusted; ignore that malformed entry, report the validation problem, and continue with other valid registry entries or normal discovery. Duplicate slugs within one registry are ambiguous: do not choose either duplicate as trusted until the conflict is resolved.

## Consumption rules

When acquisition is warranted:

1. Validate/parse available registry entries; malformed entries do not grant trust.
2. Match the acquisition brief against curated `capabilities`, `use_when`, and `avoid_when`.
3. Ignore entries clearly outside the need.
4. Prefer the best-fitting curated resource without broad search merely to challenge the user's choice.
5. Confirm that the source/package being used still matches the curated canonical identity; refresh volatile integration facts from canonical/current sources before implementation when they matter.
6. Search outside the registry only when no curated entry fits, current evidence reveals a material incompatibility/deprecation/security concern, or the user explicitly asks for comparison/alternatives.
7. Record verification separately and never convert "trusted by curation" into "runtime verified" without execution evidence.

## Ownership rules

- Never auto-add a discovered resource to the registry.
- Never auto-remove a curated resource because another resource won a comparison.
- Never silently rewrite `slug`, `canonical_url`, or `package_id`; those are trust-identity changes and require explicit authorization or project policy.
- Never silently revoke curated trust because a particular version/use failed testing; block that affected use, surface the evidence, and let the user/project change the trust policy.
- Agents may suggest a catalog change, but mutation requires explicit authorization or explicit project policy.
