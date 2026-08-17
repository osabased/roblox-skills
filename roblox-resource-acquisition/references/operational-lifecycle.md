# Operational Child Lifecycle

Use this reference when adopting a generated child, reconciling it before ordinary use, repairing a post-adoption defect, or validating a multi-child catalog.

## States

Keep these claims separate:

- **Artifact:** the generated child exists and has its recorded structural and behavioral validation.
- **Installed:** the child occupies a host-recognized location, but operational checks are incomplete.
- **Operational:** every host-applicable installation, registration, discovery, and enablement check is confirmed, and explicit activation passed.
- **Blocked:** the child remains installed, but current evidence prohibits the affected use until repair and regression checks pass.

An empty `host_adoptions` list means artifact only. File placement alone never establishes operational adoption.

## Portable resource records

Resolve matching resource records in this order:

1. an explicit record path supplied by the user, project, or environment;
2. `<project-root>/.roblox-resources/records/<slug>.yaml`;
3. `~/.roblox-resources/records/<slug>.yaml`.

Bind records and learnings by `slug` plus `canonical_url`, and by `package_id` when present. A same-named fork, mirror, or package does not inherit state.

Use only schema-version 2 records. A legacy child or record fails the current contract and must enter `repair/reconcile`; do not invent missing lifecycle evidence or silently migrate it.

## Pre-use reconciliation

Every generated child declares its reconciliation policy:

- **required:** installed resource state can drift and the documented behavior is materially version-sensitive;
- **not-applicable:** the installation mechanism fixes an immutable reviewed state, or the documented behavior is demonstrably insensitive to independently drifting state. Record the concrete reason.

When reconciliation is required:

1. Run the child's resource-specific installed-state check.
2. Compare the observed canonical identity and version/commit/source state with the child's provenance.
3. Load matching resource records and resource-bound learnings.
4. Re-check adverse learnings against current evidence; a learning directs the check but never decides it alone.
5. Stop the affected use and invoke `roblox-resource-acquisition` in `repair/reconcile` mode when the installed identity differs, installed state is unknown or mismatched, a current block applies, a material adverse observation remains unresolved, or the child's instructions fail during ordinary use.

Record `matched` only after applicable installed-state and parent-state checks complete. Use `mismatched`, `blocked`, or `unknown` truthfully when they do not.

## Adoption gate

Host mutation is a separate gate after artifact validation.

1. Detect the host and its supported skill locations, registration mechanism, enablement control, discovery surface, and explicit invocation mechanism.
2. Present the exact target and mutation.
3. Install, update, enable, disable, or remove only after explicit user authorization or an explicit project policy.
4. Record each available evidence facet rather than inferring unsupported host behavior.
5. Mark the child `operational` only when all host-applicable facets are confirmed and an explicit activation smoke test passes.
6. Run catalog validation against the target host's generated-child set before completing adoption.
7. When an overlap cluster exists, require independent multi-skill routing tests before catalog routing becomes `verified`.

If a host cannot expose enough evidence, retain the strongest truthful non-operational state such as `installed` or `unavailable`.

## Codex adapter

Current official Codex guidance establishes these checks:

- Repository skills are discovered from `.agents/skills` directories from the working directory through the repository root.
- User skills are discovered from `$HOME/.agents/skills`.
- Codex normally detects skill changes automatically; restart only when the change does not appear.
- `[[skills.config]]` entries in `~/.codex/config.toml` can disable a skill by `SKILL.md` path.
- Explicit invocation uses the skill selector or `$skill-name`; implicit invocation depends on the frontmatter description.
- Large skill catalogs can cause descriptions to be shortened or skills to be omitted from the initial list.

For Codex adoption, confirm the installed path, absence of an applicable disable entry, visibility in the current skill surface, and a successful explicit `$skill-name` smoke task. Treat implicit-routing behavior as separate catalog evidence.

Source reviewed 2026-08-16: https://learn.chatgpt.com/docs/build-skills

## Post-adoption defects

Capture the task, host, project, installed identity/version, expected behavior, observed behavior, and smallest reproduction. Mark matching operational entries `blocked`, invalidate affected behavioral and catalog-routing passes, and enter the existing repair classification loop.

A repaired artifact does not update an installed host copy automatically. Obtain authorization for that host mutation, update it, rerun all invalidated regression checks, rerun catalog validation, and repeat explicit host activation before restoring `operational`.

## Catalog coherence

Run `scripts/validate_skill_catalog.py` whenever a child is added, refreshed, repaired, or adopted. Store its order-independent fingerprint with routing evidence.

Static validation detects structural conflicts and overlap risk; it does not prove host selection. Verify reported overlap clusters with independent tasks that exercise each child's positive boundary, the competing child's boundary, and a simpler task that should select neither.

