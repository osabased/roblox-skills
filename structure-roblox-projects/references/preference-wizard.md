# Roblox structure preference wizard

Use this reference only for Design, Migration plan, or Implementation when no valid project or global profile exists. Read `practices.md` at the same time; it owns the definitions, diagrams, use cases, and technical constraints for every option below. Resolve preferences without expanding modification authority.

## Contents

- [Conversation contract](#conversation-contract)
- [Questions](#questions)
- [Defaults and summary](#defaults-and-summary)
- [Profile format](#profile-format)
- [Existing profiles](#existing-profiles)

## Conversation contract

1. Inspect enough of the project to state which workflow and conventions were detected and which parts could not be inspected. Cross commission boundaries only for read-only context. Explain that the answers set organization defaults rather than lock the project into a framework or authorize additional project changes.
2. Ask only the next unanswered question, labeled `Question N of 5`, and wait for its answer before showing another question.
3. Place the detected or recommended option first. Combine `Preserve detected workflow` with the matching named option instead of showing a duplicate.
4. Show visual structures only for Questions 2 and 3, using the diagrams in `practices.md`. Show ideal-use-case guidance only for Questions 1 through 4.
5. Briefly acknowledge each answer, retain it for the current preference summary, and show only the current question.
6. End every question with a short answer example for that question and: "Not sure? Reply `use defaults` and I'll use beginner-friendly defaults for the choices we haven't answered yet."
7. Accept naming, package, test-location, or lifecycle preferences with any answer. Retain normalized selections for the task summary and any authorized profile, preserving additional wording verbatim in `Notes` when a profile will be written.
8. For an option requiring clarification, ask its opening question and then one relevant follow-up at a time. Help the user form a directly implementable opinion when uncertain. Stop when every required field listed for that option is explicit and internally consistent.
9. Pause the original organization task after each question and at the final summary.
10. Treat **Current task only** as non-persistent. Treat a project profile as a project write and a global profile as a personal configuration write; write either only after the user selects that scope and confirms `proceed`. That confirmation authorizes only the profile write, not broader project changes.

## Questions

### Question 1 of 5: Where should scripts be edited and stored?

Present these options with meanings and ideal use cases from `practices.md`:

- Preserve detected workflow
- Studio-native
- Script Sync
- Rojo

Example answer: `Script Sync; keep models and other instances Studio-owned.`

### Question 2 of 5: How should game code start?

Present these options and the matching diagrams from `practices.md`:

- Single Script Architecture (SSA, recommended)
- Multiple entrypoints
- Custom entrypoints

For **Custom entrypoints**, open with: "How many server and client entrypoints should exist, where should they live, and how should they start the modules they own?"

Resolve the count, runtime owner, location, startup behavior, and runtime-specific exceptions for every entrypoint before completing the answer.

Example answer: `SSA, with ServerMain and ClientMain starting feature root modules explicitly.`

### Question 3 of 5: How should modules be grouped?

Present these options and the matching diagrams from `practices.md`:

- Feature-first (recommended)
- Runtime layers
- Service/controller
- Components or ECS
- Preserve
- Custom

For **Custom**, open with: "How should modules be grouped inside the server, client, and shared boundaries, including any naming convention that matters?"

Resolve runtime boundaries, grouping rules, naming, and exceptions before completing the answer.

Example answer: `Feature-first inside separate Server, Client, and Shared boundaries.`

### Question 4 of 5: What module style should be used?

Present these options with meanings and ideal use cases from `practices.md`:

- Plain Luau (recommended)
- Preserve an existing framework
- Named framework or custom lifecycle

For a named framework or custom lifecycle, resolve the framework name, module discovery rule, lifecycle phases, dependency ownership, and exceptions before completing the answer.

Example answer: `Plain Luau with explicit requires and Init/Start only where readiness ordering is observable.`

### Question 5 of 5: Where should these preferences apply?

Place the contextually recommended option first. Recommend **Current task only** for commissioned, narrowly scoped, or read-only work; recommend **Global default** otherwise.

- **Current task only:** Apply the resolved preferences without writing a profile.
- **Global default:** Save a personal fallback profile used only when a project has no closer profile or established convention.
- **This project only:** Save `.codex/roblox-structure.md` under the affected project root so it overrides global defaults for that codebase.

Example answer: `Current task only.`

## Defaults and summary

When the user replies `use defaults`, keep every answer already given and resolve the current and remaining questions to:

- detected supported workflow, otherwise Studio-native;
- Single Script Architecture;
- feature-first grouping within runtime boundaries;
- plain Luau;
- current task only for commissioned, narrowly scoped, or read-only work; global default otherwise.

After all five choices are resolved:

1. Show `Source of truth`, `Entrypoints`, `Module organization`, `Module style`, and `Preference scope` in a concise summary.
2. Ask the user to reply `proceed`, `change N`, or name the selection to change.
3. When a selection changes, ask only that main question and its required clarification follow-ups, then show the revised summary.
4. For **Current task only**, continue without writing a profile. For a persistent selection, write only the confirmed profile after `proceed`, then continue the original task.

## Profile format

For **Current task only**, keep the normalized summary in conversation state and write no profile. Otherwise write project profiles to `.codex/roblox-structure.md`. Write global profiles to `$CODEX_HOME/roblox-structure-profile.md`; when `CODEX_HOME` is unset, use the platform user `.codex` directory. Infer preference scope from the path rather than storing it as a field. Never persist commission or modification authority in a profile; establish it anew for each task.

Use this exact version-1 shape and keep every field non-empty:

```markdown
# Roblox Structure Profile

## Profile version
1

## Source of truth
<normalized selection>

## Entrypoints
<normalized selection>

## Module organization
<normalized selection>

## Module style
<normalized selection>

## Naming
<explicit preference, or Preserve project conventions; use new-project defaults only where no convention exists.>

## Tests
<explicit preference, or Use existing checks and the smallest relevant Studio playtests.>

## Notes
<verbatim custom details, or None>
```

For a custom selection, write `Custom` as the normalized field value and preserve the directly implementable convention verbatim in `Notes`. Put a named framework and lifecycle summary in `Module style` and preserve extra wording in `Notes`.

A profile is valid only when `Profile version` equals `1` and every listed heading has non-empty content. The title is recommended but not required for validity.

## Existing profiles

- Reuse a valid profile without running the wizard.
- Treat every profile as organization context, never modification permission.
- Treat a missing field or version as incomplete. Ask only for the missing decisions, show the complete normalized version-1 profile, and wait for `proceed` before writing it.
- Treat an unsupported version as incomplete without overwriting it automatically. Preserve its contents, ask only for decisions the current skill cannot resolve from recognized fields, show the proposed version-1 normalization, and wait for `proceed` before replacing it.
- Apply explicit current requests over profile values. Ask whether a conflict is one-off or should update the selected profile; update it only after the user explicitly authorizes that write.
