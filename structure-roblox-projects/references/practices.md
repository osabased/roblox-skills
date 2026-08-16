# Roblox organization practices

Use this reference to review, choose, or migrate a layout. Treat the project profile and supported established code as authoritative design context inside authorized work, never as permission to modify project content.

## Contents

- [Source-of-truth choices](#source-of-truth-choices)
- [Modification authority](#modification-authority)
- [Ownership map](#ownership-map)
- [Current foundation](#current-foundation)
- [Entrypoints and layouts](#entrypoints-and-layouts)
- [Module grouping](#module-grouping)
- [Module style](#module-style)
- [Script Sync safeguards](#script-sync-safeguards)
- [Rojo guidance](#rojo-guidance)
- [Placement and migration](#placement-and-migration)
- [Sources](#sources)

## Source-of-truth choices

| Choice | Meaning | Ideal use case |
| --- | --- | --- |
| Preserve detected workflow | Keep the project's current source of truth and sync boundaries. Combine this with the matching named option rather than presenting a duplicate. | An established project whose current Studio, Script Sync, or Rojo workflow works. |
| Studio-native | Keep the full DataModel, including script source, in the Studio place and edit scripts in Studio. | Beginners, solo creators, or Team Create projects that want one native editor and no filesystem build workflow. |
| Script Sync | Keep Studio as the project source of truth while synchronizing selected script and folder instances with local Luau files. Other instances remain Studio-owned. | Creators who want an external editor, Git, or local tooling while Studio and Team Create manage the wider project. |
| Rojo | Map filesystem content into the DataModel through a project file; each mapped filesystem tree is authoritative for its instances. | Filesystem-first teams needing reproducible builds, CI, packages, sourcemaps, or broader DataModel mapping in version control. |

## Modification authority

Apply the task-local scope ledger from `SKILL.md` before using any practice below:

- Inspect context across the project when it is relevant to conventions, compatibility, dependency tracing, or integration.
- Apply layout choices, cleanup, migrations, and fixes only to authorized work. Treat unclassified content as protected for mutation.
- Keep human modification authority independent from runtime ownership, replication visibility, source-of-truth ownership, architectural quality, and technical necessity.
- Prefer an authorized adapter or compatibility seam when integration reaches protected content. Otherwise classify the minimum external change as approval-dependent or an owner action and leave the dependent migration slice unapplied.

## Ownership map

Classify structure on three independent axes rather than forcing overlapping categories into one label:

| Axis | Values | Decision |
| --- | --- | --- |
| Runtime owner | Server, client, genuinely shared | Which Luau environment executes or consumes it? |
| Replication visibility | Server-only, client-visible | Can a client receive and inspect it? |
| Source of truth | Studio-owned, Script Sync-managed, Rojo-mapped | Which representation owns edits for this instance? |

A shared ModuleScript is normally both-runtime and client-visible. A server asset can be server-owned and server-only without being executable. Record each axis explicitly when placement is not obvious.

Map modification scope separately. None of these architecture axes identifies who owns the work or who may edit it.

## Current foundation

Treat platform statements as architectural guidance rather than frozen guarantees. Re-open Creator Hub or official engine documentation whenever a task depends on Studio support, Script Sync scope, runtime behavior, security, or a documented recommendation.

- Put server code in server containers, client code in supported client locations, and genuinely shared ModuleScripts in `ReplicatedStorage`.
- A `Script` with `RunContext = Client` can run from `ReplicatedStorage`; a `LocalScript` cannot run there.
- A ModuleScript runs once per Luau environment for a given module instance. Client and server results and state are independent. Keep requires acyclic.
- Treat replicated code and data as visible to clients. Keep authority and validation on the server.
- Roblox documentation describes both single and multiple entrypoints. Single entrypoints control startup order and dependency assembly; multiple entrypoints improve isolation and support object-bound or `Actor` behavior.
- Keep `ReplicatedFirst` limited to the earliest loading subset.

## Entrypoints and layouts

### Single Script Architecture

Use one server bootstrap and one client bootstrap to start focused ModuleScripts. This controls assembly and startup order; it does not imply a performance gain or a monolithic source file.

```text
ReplicatedStorage/
  ClientMain                 Script, RunContext = Client; client entrypoint
  Client/                    client-only ModuleScripts
  Shared/                    genuinely shared ModuleScripts and data
  Remotes/                   shared communication instances
ServerScriptService/
  ServerMain                 Script, RunContext = Server; server entrypoint
  Server/                    server-only ModuleScripts
ServerStorage/
  Assets/                    server-only templates and assets
ReplicatedFirst/
  LoadingClient              only when early loading behavior is required
```

**Use when:** Most medium or large games, teams, or systems that need controlled initialization, explicit dependencies, or shared module state within each Luau environment.

If an established project uses a `LocalScript` in `StarterPlayerScripts`, preserve it unless migration is requested. Server-only modules may live in `ServerScriptService` or `ServerStorage`; keep the existing choice consistent.

### Multiple entrypoints

Use independently starting scripts where Roblox permits them to run. Their execution order is nondeterministic.

```text
ServerScriptService/
  InventoryServer            Script
  RoundServer                Script
StarterPlayerScripts/
  CameraClient               LocalScript
  InputClient                LocalScript
Workspace/Door/
  DoorServer                 Script
```

**Use when:** Small prototypes, isolated behavior, self-contained models or tools, object lifetimes, or code whose startup order does not matter.

### Custom entrypoints

Use when a concrete runtime requirement is not represented above. Resolve the number, location, ownership, startup behavior, and runtime-specific exceptions for every server and client entrypoint.

### Entrypoint rules

- Require root feature modules explicitly. Use discovery loaders only when the project already owns a reliable one.
- Treat shared entrypoints and discovery loaders as integration boundaries: inspect all consumers, then change them only when authorized or extend them through an authorized seam.
- Start small projects directly. Use separate `Init` and `Start` passes only when every module must exist before work begins or startup order is otherwise observable.
- Keep work out of entrypoints beyond dependency assembly and startup.
- Point dependencies toward stable shared or domain modules, not back toward entrypoints.
- Split modules by cohesive responsibility rather than arbitrary line count.

## Module grouping

### Feature-first

Group by gameplay capability inside separate runtime boundaries. Use for growing games whose developers usually work on complete features.

```text
Server/Combat/
  DamageService
  HitValidation
Client/Combat/
  CombatController
Shared/Combat/
  Types
  Config
```

### Runtime layers

Keep one shallow list per execution side. Use for small games where feature folders add more navigation than clarity.

```text
Server/
  Combat
  Inventory
Client/
  Input
  UI
Shared/
  Constants
  Types
```

### Service/controller

Organize long-lived server APIs as services and client orchestration as controllers without requiring a framework. Use when the team already uses this vocabulary or the systems are naturally long-lived.

```text
Server/Services/
  InventoryService
  RoundService
Client/Controllers/
  InventoryController
  RoundController
```

### Components or ECS

Represent repeated behavior or data as components and process matching instances or entities through systems. Use for many similarly behaved NPCs, interactables, projectiles, or simulations.

```text
Components/
  Health
  Damageable
Systems/
  DamageSystem                processes tagged instances or entities
```

### Preserve or Custom

- **Preserve:** Continue a coherent established grouping convention.
- **Custom:** Define grouping rules inside server, client, and shared boundaries, including naming and exceptions.

Architectures can combine. Single entrypoints can start feature folders containing components. Record the combination in the profile without inventing a framework label.

Apply the selected grouping to authorized work. Preserve adjacent groups even when a wider reorganization would be cleaner unless that migration is also authorized.

## Module style

| Choice | Meaning | Ideal use case |
| --- | --- | --- |
| Plain Luau | Focused ModuleScripts return functions or tables, require dependencies explicitly, and add lifecycle phases only when ordering requires them. | New projects that want modular code without framework conventions or loader dependencies. |
| Preserve an existing framework | Keep its discovery, naming, and lifecycle intact. | A working project that already depends on a framework and has no migration requirement. |
| Named framework or custom lifecycle | Choose a named framework or define phases such as `Init` followed by `Start`, including discovery and ownership rules. | Projects needing cross-system readiness or deliberate team-wide framework conventions. |

## Script Sync safeguards

Script Sync manages `Script`, `LocalScript`, `ModuleScript`, and `Folder` instances. Other instances inside a synced folder remain ignored and Studio-owned.

Before enabling Script Sync or changing a sync boundary:

1. Inventory every affected script and folder, including script names, class or RunContext, attributes, tags, children, and modification scope. Inspection may cross the proposed boundary without authorizing it.
2. Narrow the boundary to authorized work whenever it contains protected content. Treat a required protected script, folder, metadata migration, or consumer update as integration-required until separately authorized.
3. Identify every affected script with attributes or tags. Script Sync ignores that metadata, so create an explicit preservation strategy for each one:
   - keep the script Studio-owned outside the sync boundary; or
   - deliberately migrate the metadata to a supported, reviewed source, update each authorized consumer, and classify any protected consumer as integration-required.
4. Review the Studio conflict-resolution preview and select the authoritative side intentionally. Treat the preview as evidence, not permission to overwrite protected content.
5. Proceed only when every metadata-bearing script has a preservation strategy and every content or metadata write inside the selected folders is authorized.
6. After the change, verify script types, RunContext values, attributes, tags, children, source boundaries, and the absence of protected writes in Studio and on disk.

Script Sync supports scripts and folders rather than the wider DataModel. Use Rojo when the filesystem must own a broader hierarchy.

## Rojo guidance

For a small filesystem-first project, prefer a compact tree and let the project file define the DataModel mapping:

```text
src/
  client/
    init.client.luau
  server/
    init.server.luau
  shared/
default.project.json
```

Before version-sensitive Rojo work:

1. Inspect the repository's pin and run `rojo --version` when available.
2. Re-open official releases and every applicable changelog entry before recommending an upgrade or version-specific suffix or mapping behavior.
3. Keep structural migration separate from version upgrade. Change tool pins, manifests, lockfiles, or generated mappings only when those writes are authorized.
4. Read the actual `*.project.json` or `*.project.jsonc`; directory names alone do not establish DataModel placement.
5. Inspect `emitLegacyScripts`, suffix conventions, nested project files, compatibility settings, and `syncbackRules` before changing mappings.
6. Trace the full DataModel effect of a mapping change; a project-file edit is not confined to the source subtree named in the commission.
7. Preserve working mappings and versions unless their change is explicitly authorized.

## Placement and migration

| Content | Preferred home |
| --- | --- |
| Server authority, data stores, receipts, validation | Server-only code container |
| Client input, camera, local UI behavior | Client-only code container |
| Types, constants, pure utilities used on both sides | `ReplicatedStorage/Shared` |
| RemoteEvents and RemoteFunctions | Client-visible container, commonly `ReplicatedStorage/Remotes` |
| Server-only models and templates | `ServerStorage` |
| Assets required by both server and client before cloning | `ReplicatedStorage` |
| Earliest loading screen subset | `ReplicatedFirst` |

For every migration:

1. Inventory the DataModel, filesystem mappings, tool versions, source-of-truth boundaries, entrypoints, attributes, and tags.
2. Classify modification scope separately from runtime ownership, replication visibility, and source of truth before moving anything.
3. Trace every require, string path, loader convention, remote lookup, project mapping, caller, and test reference, including protected consumers.
4. Move the minimum coherent authorized slice and update its authorized references in the same change. If a protected edit is required, use a compatibility layer or leave the slice unapplied while requesting approval or an owner action.
5. Check for cyclic dependencies and unintended replicated server logic.
6. Apply the Script Sync safeguards when a sync boundary exists or changes.
7. Run existing type, lint, format, build, and test commands when present. Prefer read-only or path-scoped modes; allow rewriting output only where it is authorized.
8. Playtest server and client startup; use multiple clients when networking or replicated state changes.
9. Verify the build or serve path and resulting Studio hierarchy when mappings change.
10. Record a rollback boundary and result for each coherent slice, plus every approval-dependent or owner action that remains.

## Sources

Re-open volatile sources at task time; these links are discovery anchors rather than cached guarantees.

- Roblox architecture: [Script types and locations](https://create.roblox.com/docs/scripting/locations), [Plant reference project](https://create.roblox.com/docs/resources/plant-reference-project), [Data model](https://create.roblox.com/docs/projects/data-model)
- Roblox modules: [ModuleScript](https://create.roblox.com/docs/reference/engine/classes/ModuleScript), [Reuse code](https://create.roblox.com/docs/scripting/module)
- Roblox runtime and security: [Client-server runtime](https://create.roblox.com/docs/projects/client-server), [Client-server boundary](https://create.roblox.com/docs/scripting/security/client-server-boundary), [Access control and confidentiality](https://create.roblox.com/docs/scripting/security/access-control)
- Roblox workflows: [Script Sync](https://create.roblox.com/docs/scripting/sync), [Studio testing modes](https://create.roblox.com/docs/studio/testing-modes), [Third-party tools](https://create.roblox.com/docs/projects/external-tools)
- Rojo: [Project format](https://rojo.space/docs/v7/project-format/), [Sync details](https://rojo.space/docs/v7/sync-details/), [releases](https://github.com/rojo-rbx/rojo/releases), [changelog](https://github.com/rojo-rbx/rojo/blob/master/CHANGELOG.md)
- Community terminology: [Single Script Architecture and Modular Programming](https://devforum.roblox.com/t/single-script-architecture-and-modular-programming/2432662), [Script Organizational Utility](https://devforum.roblox.com/t/script-organizational-utility/4591424)
