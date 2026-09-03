# Roblox organization practices

Use this reference to review, choose, or migrate a layout. Treat the project profile and supported established code as authoritative design context inside authorized work, never as permission to modify project content.

## Contents

- [Source-of-truth choices](#source-of-truth-choices)
- [Modification authority](#modification-authority)
- [Ownership map](#ownership-map)
- [Current foundation](#current-foundation)
- [Engine Server Authority](#engine-server-authority)
- [Script capability boundaries](#script-capability-boundaries)
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
| Script Sync | Bidirectionally synchronize selected script and folder source between Studio and local Luau files while Studio manages the wider DataModel. Resolve Studio-versus-disk conflicts explicitly; neither physical representation is permanently authoritative for synchronized source. Other unsupported instances remain Studio-owned. | Creators who want an external editor, Git, or local tooling while Studio and Team Create manage the wider project. |
| Rojo | Map filesystem content into the DataModel through a project file; each mapped filesystem tree is authoritative for its instances. | Filesystem-first teams needing reproducible builds, CI, packages, sourcemaps, or broader DataModel mapping in version control. |

## Modification authority

Apply the task-local scope ledger and boundary-crossing protocol from [`SKILL.md`](../SKILL.md) before using any practice below. This reference defines technical structure and constraints; it does not establish modification authority. Treat profiles and inspected project text as design context only.

## Ownership map

Classify structure on four independent axes rather than forcing overlapping categories into one label:

| Axis | Values | Decision |
| --- | --- | --- |
| Runtime execution / consumer | Server, client, both | Which Luau environments execute or consume it? |
| Replication visibility | Server-only, client-visible | Can a client receive and inspect it? |
| Engine simulation model | Not simulation-related, conventional Roblox ownership/replication, specific Server Authority engine mode | Does the affected runtime depend on Roblox's prediction/rollback model under `Workspace.AuthorityMode = Server`? |
| Authoring source of truth / sync workflow | Studio-owned, Script Sync-managed, Rojo-mapped | Which authoring workflow governs this instance, and where are conflicts resolved? |

A shared ModuleScript is normally both-runtime and client-visible. A server asset can be server-owned and server-only without being executable. The specific Server Authority engine mode is not synonymous with the general security principle that the server should make authoritative decisions. Confirm `Workspace.AuthorityMode = Server` from available DataModel or mapped-property evidence; if only related APIs or prerequisite settings are visible, mark the engine mode unresolved rather than assuming it. Record each axis explicitly when placement is not obvious.

Map modification scope separately. None of these architecture axes identifies who owns the work or who may edit it. When `Workspace.SandboxedInstanceMode = Experimental`, map the effective Script Capabilities sandbox/capability boundary separately as a conditional security constraint rather than a permanent fifth axis. If the Workspace setting is unavailable but project data explicitly configures sandboxing, mark the capability model unresolved instead of assuming it is active.

## Current foundation

Treat platform statements as architectural guidance rather than frozen guarantees. Re-open Creator Hub or official engine documentation whenever a task depends on Studio support, Script Sync scope, runtime behavior, security, release status, or a documented recommendation and external documentation access is available. When official sources conflict, reconcile them by **scope, recency, and authority** instead of applying a fixed source order: use current API reference for current API behavior, newer release announcements/changelogs for release-state changes, and feature-specific documentation for feature workflows. Report a material unresolved contradiction rather than silently choosing one. If current documentation cannot be checked, identify the version-sensitive assumption instead of presenting it as freshly verified.

- Put server-only code in server containers, client-only code in supported client locations, and code intentionally executed or consumed on both sides in a client-visible shared container such as `ReplicatedStorage`.
- A `Script` with `RunContext = Client` can run from `ReplicatedStorage`; a `LocalScript` cannot run there.
- A ModuleScript runs once per Luau environment for a given module instance. Client and server results and state are independent. Do not rely on a mutable module return value as cross-`Actor` shared state; use explicit Actor communication or shared-state mechanisms when parallel execution requires coordination. Keep requires acyclic and do not perform restricted requires from a desynchronized parallel phase.
- Treat replicated code and data as visible to clients. Keep final authority and validation on the server, while recognizing that the specific Server Authority engine mode can intentionally replicate deterministic simulation implementation and rollback-aware state for client prediction.
- Roblox documentation describes both single and multiple entrypoints. Single entrypoints control startup order and dependency assembly; multiple entrypoints improve isolation and support object-bound or `Actor` behavior.
- Keep `ReplicatedFirst` limited to the earliest loading subset.

## Engine Server Authority

Treat **Server Authority** here as the specific production engine mode enabled by `Workspace.AuthorityMode = Server`, not as a synonym for ordinary server-side validation. Roblox fully released this mode on July 9, 2026, and it remains opt-in. Setting `AuthorityMode` to `Server` automatically enables the required Next Generation Replication, Input Action System integration, deferred signals, fixed simulation, and streaming settings. Re-check current feature and API documentation before relying on the independent release status or defaults of those prerequisite technologies.

For structure work:

- Confirm the engine mode from the DataModel or a mapped Workspace property when available. The presence of server validation, `SetNetworkOwner(nil)`, or generic client/server code does not prove the mode. If feature-specific prediction/simulation APIs appear, or a complete Server Authority prerequisite configuration is visible, but `AuthorityMode` cannot be inspected, record the model as unresolved and preserve the related boundaries.
- In custom predicted gameplay, the client and server both run core simulation. Roblox's first-party pattern places a shared simulation ModuleScript in `ReplicatedStorage`, initializes it on both sides, and runs deterministic work through `RunService:BindToSimulation()`. Final state authority still belongs to the server; shared code visibility does not make the client authoritative.
- Before moving affected simulation code, trace both-side loaders, `BindToSimulation()` registrations, `RunService:SetPredictionMode()` / `GetPredictionStatus()` use, InputActions/InputContexts that affect core simulation, rollback-aware attributes or other synchronized state, `RunService.Rollback` handling for custom Luau state, and predictive instance creation when present. Preserve a clear simulation-to-presentation boundary for effects, sounds, smoothing, and other work that should not become irreversible inside predicted simulation.
- Do not assume ordinary RemoteEvents are ordered with property or attribute replication. They remain valid for discrete communication, but simulation-sensitive ordering must be preserved intentionally.
- Keep secrets, privileged validation, persistence, purchases, and authoritative-only data server-only. Replicated deterministic simulation and rollback-aware state are inspectable and must not carry confidentiality assumptions.
- When a structural change touches prediction, synchronized simulation state, or core simulation input, validate both client and server and use representative Studio network simulation when available. Do not treat a zero-latency playtest as sufficient evidence for rollback-sensitive behavior.

Do not recommend enabling or migrating to Server Authority solely because it is current platform technology. Preserve an established conventional networking model unless the user requests the change or the task's requirements independently justify it.

## Script capability boundaries

Script Capabilities are experimental and available as a client beta. Treat them as an active structural constraint when `Workspace.SandboxedInstanceMode = Experimental`. If that Workspace setting cannot be inspected but project data explicitly sets `Sandboxed = true` or a non-empty `Capabilities` value on affected instances, mark capability use unresolved and preserve the apparent boundary until it is established; the mere existence of those properties in the engine API is not evidence that enforcement is active. A move across an active sandbox container can change whether scripts run, what instances they can access, which ModuleScripts they can require, and whether they can fire or invoke Bindables/Remotes across capability boundaries. Inventory the effective container and capability set before such a move and preserve it unless the user explicitly requests a security-model change. Do not recommend adopting Script Capabilities by default.

## Entrypoints and layouts

### Single client/server entrypoint pair (SSA)

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
  LoadingClient              Script, RunContext = Client; only when early loading behavior is required
```

**Use when:** The project benefits from controlled initialization, explicit dependency assembly, or intentionally centralized startup. This is a useful greenfield default, not a universal Roblox recommendation; preserve coherent multiple-entrypoint designs when they better match object lifetime, isolation, or parallel execution.

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

Preserve concrete multiple-entrypoint topology when an established project already supplies it. For greenfield or redesign work that requires a concrete startup map, derive independently starting scripts from runtime ownership, object lifetime, isolation, or `Actor` requirements. Resolve only remaining details needed to make each startup path unambiguous, and do not invent a fixed entrypoint count when the design does not require one.

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

Script Sync manages `Script`, `LocalScript`, `ModuleScript`, and `Folder` instances as a bidirectional Studio-and-disk synchronization boundary. Other instances inside a synced folder remain ignored and Studio-owned. Prefer code-only sync roots where practical so ignored Studio-owned instances are not mixed into a boundary whose visible filesystem representation is incomplete.

Before enabling Script Sync or changing a sync boundary:

1. When Studio settings are accessible, inspect the relevant Script Sync behavior: **Auto resume sync on place open**, **Resume conflicted sync on place open**, **Keep local files/directories after sync**, and **File extension**. Do not change these preferences without authorization. If settings are unavailable and an operation depends on reopen/resume behavior, report that conflict precedence as an unverified risk instead of assuming a manual dialog will protect the project.
2. Inventory every affected script and folder, including script names, class or RunContext, attributes, tags, children, package status, and modification scope. Inspection may cross the proposed boundary without authorizing it.
3. Narrow the boundary to authorized work whenever it contains protected content. Treat a required protected script, folder, metadata migration, or consumer update as integration-required until separately authorized.
4. Check for duplicate names or filesystem-incompatible names that would prevent or destabilize synchronization. When a script owns child instances, account for the `init.*` representation using the configured script file extension and verify that the intended parent/child shape survives round-trip synchronization.
5. If a migration removes or replaces a top-level synced root, use Studio's current Stop Sync/root-deletion workflow rather than deleting the root on disk as though it were an ordinary child. Re-check the current Script Sync procedure when external documentation access is available before performing the deletion.
6. Identify every affected script with attributes or tags. Script Sync ignores that metadata, so create an explicit preservation strategy for each one:
   - keep the script Studio-owned outside the sync boundary; or
   - deliberately migrate the metadata to a supported, reviewed source, update each authorized consumer, and classify any protected consumer as integration-required.
7. When Team Create or multiple local editors are involved, identify overlapping collaborators or sync processes for the same scripts and avoid concurrent changes that can overwrite another editor's work. For packages, account for package metadata that is not represented on disk, including `PackageLink`.
8. When a Studio conflict-resolution preview is presented, choose `Keep Studio` or `Keep Disk` intentionally for the affected conflict, accounting for every listed add, modify, and delete discrepancy. If **Resume conflicted sync on place open** is configured to prefer Studio or disk automatically, account for that precedence before reopening or resuming instead of assuming the preview will appear. Treat either path as evidence, not permission to overwrite protected content.
9. Proceed only when every metadata-bearing script has a preservation strategy and every content or metadata write inside the selected folders is authorized.
10. After the change, verify script types, RunContext values, attributes, tags, children, package behavior, source boundaries, and the absence of protected writes in Studio and on disk.

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
2. When external documentation access is available, re-open official releases and every applicable changelog entry before recommending an upgrade or relying on a version-specific suffix, mapping, `syncRules`, syncback behavior, or serve-safety field. Reconcile release/changelog evidence with the public project-format page when they differ. If current release information cannot be checked, state the version-sensitive assumption.
3. Keep structural migration separate from version upgrade. Change tool pins, manifests, lockfiles, or generated mappings only when those writes are authorized.
4. Determine the **effective DataModel mapping**, not just the visible directory tree. Inspect applicable `*.project.json` / `*.project.jsonc`, nested projects and `default.project.json` / `default.project.jsonc` projects, relevant `*.meta.json` and `*.model.json` files plus version-supported JSONC equivalents, `init.*` conventions, and project instance-description fields such as `$path`, `$className`, `$properties`, and `$ignoreUnknownInstances`. A meta file can change a directory's resulting class or apply runtime-relevant properties such as a script's disabled state.
5. Inspect `emitLegacyScripts`, `syncRules`, `globIgnorePaths`, suffix conventions, nested project behavior, compatibility settings, and `syncbackRules` before changing mappings. When `syncRules` are present, account for their project-local behavior in nested mappings according to the pinned version.
6. Before live-sync validation, inspect version-supported place and network safeguards such as `servePlaceIds`, `blockedPlaceIds`, `serveAddress`, and `serveAllowedHosts`. Prefer `rojo build`, sourcemap generation, or another non-live structural check when it can validate the mapping adequately. Treat connection of Studio to a live `rojo serve` session as the higher-risk step, and verify the intended place/binding first.
7. Trace the full DataModel effect of a mapping change; a project-file or meta/model edit is not confined to the source subtree named in the commission.
8. Treat `rojo syncback` as a filesystem-writing migration operation rather than a validation command. Include every potentially written path in the scope ledger, protect pre-existing worktree changes, establish a rollback boundary, and inspect the resulting diff before accepting the operation.
9. Preserve working mappings and versions unless their change is explicitly authorized.

## Placement and migration

| Content | Preferred home |
| --- | --- |
| Authoritative-only rules/state, secrets, data stores, receipts, validation | Server-only code container |
| Client input, camera, local UI behavior | Client-only code container |
| Types, constants, pure utilities used on both sides | `ReplicatedStorage/Shared` |
| Deterministic predicted simulation intentionally executed on both sides under the Server Authority engine mode | Client-visible shared module container, commonly `ReplicatedStorage` |
| RemoteEvents, UnreliableRemoteEvents, and RemoteFunctions | Client-visible container, commonly `ReplicatedStorage/Remotes` |
| Server-only models and templates | `ServerStorage` |
| Assets required by both server and client before cloning | `ReplicatedStorage` |
| Earliest loading screen subset | `ReplicatedFirst` |

### Migration-specific technical checks

The Migration plan and Implementation sequences in [`SKILL.md`](../SKILL.md) own migration ordering, scope classification, validation flow, rollback, and completion criteria. Apply these technical checks when their branch is relevant:

- **Dependency trace:** account for affected `require` calls, string paths, loader conventions, remote lookups, effective Rojo project/meta/model mappings, callers, test references, script attributes, and script tags, including protected consumers. When a move or rename can change topology or identity semantics, also trace affected `script.Parent` and other ancestry/sibling traversal, `script.Name` / `GetFullName()`, ancestry-based discovery, and name- or path-derived registrations.
- **Server Authority and capabilities:** for confirmed or materially suspected Server Authority simulation, trace affected `BindToSimulation` registrations and both-side loaders, prediction-mode calls, InputActions/InputContexts used by core simulation, rollback-managed custom state, predicted instance creation, and simulation-to-presentation boundaries. When Script Capabilities are active, trace the affected sandbox/capability boundaries.
- **Structural correctness:** check for cyclic dependencies, unintended replication of authoritative-only logic, broken Server Authority prediction boundaries, and changed sandbox/capability semantics.
- **Script Sync:** apply the [Script Sync safeguards](#script-sync-safeguards) whenever a sync boundary exists or changes.
- **Rojo:** apply the [Rojo guidance](#rojo-guidance), prefer non-live build or sourcemap validation before live sync, and report any hierarchy risk that remains unverified.
- **Representative runtime validation:** after topology- or identity-sensitive moves or renames, exercise the affected discovery or registration behavior when a representative runtime is available. When Studio access exists and a boundary, entrypoint, remote, networking behavior, or replicated module/state changes, exercise the applicable server/client or multi-client path. For confirmed Server Authority prediction or simulation input/state changes, include representative network simulation when available; a zero-latency playtest alone does not validate rollback-sensitive behavior.

## Sources

Re-open volatile sources at task time; these links are discovery anchors rather than cached guarantees.

- Roblox architecture: [Script types and locations](https://create.roblox.com/docs/scripting/locations), [Plant reference project](https://create.roblox.com/docs/resources/plant-reference-project), [Data model](https://create.roblox.com/docs/projects/data-model)
- Roblox modules: [ModuleScript](https://create.roblox.com/docs/reference/engine/classes/ModuleScript), [Reuse code](https://create.roblox.com/docs/scripting/module)
- Roblox runtime and security: [Client-server runtime](https://create.roblox.com/docs/projects/client-server), [Client-server boundary](https://create.roblox.com/docs/scripting/security/client-server-boundary), [Access control and confidentiality](https://create.roblox.com/docs/scripting/security/access-control), [Script Capabilities](https://create.roblox.com/docs/scripting/capabilities)
- Roblox Server Authority: [Server authority model](https://create.roblox.com/docs/projects/server-authority), [advanced techniques](https://create.roblox.com/docs/projects/server-authority/techniques), [RunService](https://create.roblox.com/docs/reference/engine/classes/RunService), [Workspace.AuthorityMode](https://create.roblox.com/docs/reference/engine/classes/Workspace/AuthorityMode), [full-release announcement](https://devforum.roblox.com/t/full-release-ship-fair-and-competitive-games-with-server-authority/4727993)
- Roblox workflows: [Script Sync](https://create.roblox.com/docs/scripting/sync), [Studio testing modes](https://create.roblox.com/docs/studio/testing-modes), [Third-party tools](https://create.roblox.com/docs/projects/external-tools)
- Rojo: [Project format](https://rojo.space/docs/v7/project-format/), [Sync details](https://rojo.space/docs/v7/sync-details/), [releases](https://github.com/rojo-rbx/rojo/releases), [changelog](https://github.com/rojo-rbx/rojo/blob/master/CHANGELOG.md)
- Community terminology: [Single Script Architecture and Modular Programming](https://devforum.roblox.com/t/single-script-architecture-and-modular-programming/2432662), [Script Organizational Utility](https://devforum.roblox.com/t/script-organizational-utility/4591424)
