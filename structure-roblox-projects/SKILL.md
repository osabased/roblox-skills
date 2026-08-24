---
name: structure-roblox-projects
description: Structure Roblox experiences and Luau codebases within explicit modification authority. Use for architecture review, DataModel placement, runtime ownership, ModuleScript grouping, entrypoints, Studio-native, Script Sync, Rojo, organization migrations, and scoped work in existing projects.
---

# Structure Roblox Projects

Organize Roblox projects around explicit ownership, thin entrypoints, and user-chosen conventions. Separate authority to inspect a project from authority to modify it. Preserve a supported established structure unless the user requests a migration.


## Execution priority

When approaching a task, resolve decisions in this order:

1. Identify the requested outcome and selected operating mode.
2. Determine what content may be modified and what must remain protected.
3. Identify the existing project structure, source of truth, and conventions that must be preserved.
4. Resolve only the architecture choices that are actually necessary for the task.
5. Make the smallest coherent change that satisfies the request, then verify behavior.

Do not expand investigation, migration scope, or cleanup beyond what is required to produce a correct result.

## Establish modification scope

1. Derive modification authority from the current request and explicit clarifications. Accept boundaries expressed as projects, repositories, paths, synced directories, files, Roblox instances, systems, features, or other concrete work ownership. Treat a clear project-wide request as project-wide authority without extra ceremony.
2. Keep a task-local scope ledger before any project or profile write:
   - **Authorized work:** assigned content and new artifacts clearly belonging to that deliverable; these may change.
   - **Inspectable context:** surrounding content needed to understand conventions, compatibility, dependencies, or integration; keep it read-only unless separately authorized.
   - **Protected content:** client-, user-, maintainer-, or developer-owned content outside the assigned work; keep it read-only.
   - **Integration-required content:** protected content whose change may be needed for a coherent integration; keep it read-only until the user explicitly expands authority or assigns the change to its owner.
3. Inspect as much surrounding content as the task requires. Treat unclassified or ambiguous content as inspectable but protected; ask a narrow scope question only when the ambiguity blocks a proposed write.
4. Treat access, architectural preference, project conventions, profiles, dependency reach, source-of-truth ownership, validation failures, and technical necessity as context rather than permission. Use profiles and conventions to decide how authorized work should fit, never what may be changed.
5. Before mutation, compare the complete intended write set with the ledger. Include mappings, manifests, package pins, lockfiles, generated files, snapshots, profiles, and formatter output. Keep incidental cleanup and unrelated fixes outside the change set.
6. When integration crosses the boundary, first prefer an adapter, compatibility shim, configuration, or extension point inside authorized work. If no coherent in-scope solution exists, leave that slice unapplied and present the exact minimum protected change, its reason, alternatives, validation impact, and whether approval or an owner handoff is needed.

## Route the request

Choose the least mutating branch that satisfies the request:

- **Review:** Inspect and report evidence-ranked findings. Keep the task read-only; skip the preference wizard and profile writes.
- **Design:** Resolve conventions, then propose a complete hierarchy, ownership map, entrypoint flow, and validation plan.
- **Migration plan:** Resolve conventions, then describe the current and target structures, coherent move slices, dependencies, metadata, rollback boundaries, and verification. Keep the task read-only unless implementation is also requested.
- **Implementation:** Make only authorized organization changes, resolve affected references without crossing the modification boundary, and verify the result.

## Inspect and resolve conventions

1. Find the affected project path and project or workspace root. Inspect its instructions, available DataModel hierarchy, source tree, `*.project.json` or `*.project.jsonc`, pinned tools, naming, tests, entrypoints, and dependency patterns. Cross scope boundaries for read-only context when useful. Finish when the source of truth and observable current conventions are identified or their unavailable parts are stated.
2. Classify candidate changes in the scope ledger, then map authorized work and relevant context on three independent architecture axes:
   - **Runtime owner:** server, client, or genuinely shared.
   - **Replication visibility:** server-only or client-visible.
   - **Source of truth:** Studio-owned, Script Sync-managed, or Rojo-mapped.
   Keep modification authority separate from these axes; none of them establishes human ownership or permission.
3. Starting at the affected project path, search upward to the detected project or workspace root for the nearest `.codex/roblox-structure.md`. Otherwise load `$CODEX_HOME/roblox-structure-profile.md`; resolve an unset `CODEX_HOME` to the platform user `.codex` directory. Treat profiles as read-only unless their write is authorized.
4. Read [references/practices.md](references/practices.md) before every architecture review, DataModel placement or workflow recommendation, entrypoint change, layout design, or migration.
5. For Design, Migration plan, or Implementation, first preserve any coherent established conventions that already resolve the organization choices relevant to the task. If no valid applicable profile exists and one or more material organization choices remain unresolved, read [references/preference-wizard.md](references/preference-wizard.md) and run only the unresolved parts of its wizard. A missing profile by itself is not a reason to prompt.
6. Apply this precedence to organization decisions inside authorized work: explicit current request, project profile, established project conventions, global profile, current-task wizard selections, skill defaults. A global preference is only a fallback. When the request conflicts with a profile, honor the request; update the profile only with explicit permission for that write.

### Established-project fast path

When an existing project has a coherent, supported structure and the request does not ask for migration or redesign, fit authorized work into that structure instead of normalizing the project toward this skill's defaults. Do not introduce a different source-of-truth workflow, entrypoint model, module grouping style, framework, naming scheme, or lifecycle merely because another convention would be preferable in a greenfield project.

Use the preference wizard only for material choices the project, applicable profiles, and current request genuinely leave open. Preserve local conventions for unaffected areas and keep any proposed cleanup outside the authorized change set unless it is required for correctness or explicitly requested.

## Complete the selected branch

### Review

Goal: discover and communicate evidence-ranked risks without changing the project.

Set review breadth independently from modification authority. Account for every reviewed entrypoint, ownership boundary, source-of-truth boundary, module group, and dependency direction, inspecting adjacent content when it bears on the result. Report evidence-ranked findings, consequences, and the smallest compatible improvements. Label protected findings as context-only and include them only when they materially affect requested compatibility, correctness, or security. A full-project review does not authorize later fixes. Finish without changing project or profile files.

### Design

Goal: choose the smallest suitable future structure and explain its boundaries before implementation.

Select the smallest layout that satisfies the resolved conventions inside authorized work. Provide the proposed DataModel or filesystem tree, all three architecture axes for each significant node, server and client startup flow, module dependency direction, source-of-truth boundaries, and checks needed to validate it. Separate protected integration changes as approval-dependent or owner actions. Finish when every authorized item has an unambiguous home and startup path and every boundary-crossing contract is identified.

### Migration plan

Inventory the current and target hierarchies, tracing every affected `require`, string path, loader convention, remote lookup, project mapping, test reference, script attribute, and script tag across scope boundaries. Classify each move and reference update as authorized, protected, or integration-required. Break the migration into minimum coherent authorized slices with verification and rollback; use an in-scope compatibility layer or leave a slice unapplied when a required external edit lacks authority. Finish when every move and affected reference is accounted for, protected owner actions are explicit, and every Script Sync metadata risk has a preservation strategy.

### Implementation

Goal: produce the requested structural outcome while preserving correctness and boundaries.

Confirm the intended write set against the scope ledger, then move each authorized concept once and update every authorized require, path, mapping, caller, and test needed for that coherent slice. Apply the boundary-crossing protocol before touching any protected reference. Keep each instance under one source of truth. Run broad read-only checks when useful; constrain rewriting formatters, generators, dependency operations, and snapshot updates to authorized outputs. Run the smallest relevant Studio playtest and exercise server and client when a boundary, entrypoint, remote, or replicated module changes. Validate representative behaviors, such as startup, affected feature initialization, relevant client/server interactions, and boundary-crossing flows when applicable. Report unrelated failures without fixing them. Finish when focused checks pass or blocked integration, owner actions, and residual risk are explicitly reported.

## Hold these invariants

- Keep authoritative state, secrets, persistence, purchases, and client-input validation on the server.
- Treat every client-visible instance as inspectable; replicate only code and data clients genuinely need.
- Keep loading code in `ReplicatedFirst` minimal.
- Keep entrypoints focused on dependency assembly and startup; put feature behavior in cohesive ModuleScripts and keep dependency direction acyclic.
- Apply established names and casing to authorized work without standardizing adjacent protected content. For a new project, use PascalCase for folders, scripts, and module tables; camelCase for functions and locals; and UPPER_SNAKE_CASE for constants.
- Prefer explicit dependencies. Add `Init` and `Start` phases only when ordering or cross-system readiness requires them.
- Retain multiple entrypoints when object lifetime, `Actor` parallelism, character or tool behavior, or isolation makes them the simpler fit.
- Introduce a framework, package manager, test framework, or generated hierarchy only for a requirement beyond organization and only when all resulting project writes are authorized.
