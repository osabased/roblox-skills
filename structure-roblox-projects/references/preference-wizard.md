# Roblox structure preference wizard

Use this reference only for Design, Migration plan, or Implementation when no valid applicable profile resolves the remaining material organization choices after inspecting established project conventions. Do not run the wizard solely because a profile is absent. Read [`practices.md`](practices.md) at the same time; it owns the definitions, diagrams, use cases, and technical constraints for every option below. Resolve preferences without expanding modification authority.

## Contents

- [Conversation contract](#conversation-contract)
- [Questions](#questions)
- [Defaults and summary](#defaults-and-summary)
- [Profile format](#profile-format)
- [Existing profiles](#existing-profiles)

## Conversation contract

1. Inspect enough of the project to state which workflow and conventions were detected, which material choices they already resolve, and which parts could not be inspected. Cross modification or ownership boundaries only for read-only context. Explain that the answers set organization defaults rather than lock the project into a framework or authorize additional project changes.
2. Skip any question already resolved by the explicit current request or a coherent established project convention. Ask only the next unresolved question, labeled with its canonical `Question N of 5`, and wait for its answer before showing another question.
3. Place the detected or recommended option first. Combine `Preserve detected workflow` with the matching named option instead of showing a duplicate.
4. Show visual structures only for Questions 2 and 3, using the diagrams in `practices.md`. Show ideal-use-case guidance only for Questions 1 through 4.
5. Briefly acknowledge each answer, retain it for the current preference summary, and show only the next unresolved question.
6. End every asked question with a short answer example for that question and: "Not sure? Reply `use defaults` and I'll use beginner-friendly defaults for the choices we haven't answered yet."
7. Accept naming, package, test-location, or lifecycle preferences with any answer. Retain normalized selections for the task summary and any authorized profile, preserving additional wording verbatim in `Notes` when a profile will be written.
8. For an option requiring clarification, ask its opening question and then one relevant follow-up at a time. Help the user form a directly implementable opinion when uncertain. Stop when every required field listed for that option is explicit and internally consistent.
9. Pause the original organization task after each asked question. At the final summary, stop only when a persistent profile write, an ambiguous selection, or an explicitly requested approval gate still requires confirmation; otherwise resume the original task.
10. Treat **Current task only** as non-persistent and continue after the resolved summary without requiring an extra `proceed`. Treat a project profile as a project write and a global profile as a personal configuration write; write either only after the user selects that scope and confirms `proceed`. That confirmation authorizes only the profile write, not broader project changes.

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

- Single client/server entrypoint pair (SSA; skill default)
- Multiple entrypoints
- Custom entrypoints

For **Multiple entrypoints**, use the derivation rules in `practices.md`. Ask only for startup details that remain material and unresolved after the current request and established structure.

For **Custom entrypoints**, open with: "How many server and client entrypoints should exist, where should they live, and how should they start the modules they own?"

Resolve the count, runtime owner, location, startup behavior, and runtime-specific exceptions for every entrypoint before completing the answer.

Example answer: `Single client/server entrypoint pair (SSA), with ServerMain and ClientMain starting feature root modules explicitly.`

### Question 3 of 5: How should modules be grouped?

Present these options and the matching diagrams from `practices.md`:

- Feature-first (skill default)
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

- Plain Luau (skill default)
- Preserve an existing framework
- Named framework or custom lifecycle

For a named framework or custom lifecycle, resolve the framework name, module discovery rule, lifecycle phases, dependency ownership, and exceptions before completing the answer.

Example answer: `Plain Luau with explicit requires and Init/Start only where readiness ordering is observable.`

### Question 5 of 5: Where should these preferences apply?

Place the contextually recommended option first. Recommend **Current task only** for temporary, experimental, narrowly scoped, read-only, or externally owned work. Recommend a persistent scope only when the user wants a reusable preference beyond the current task.

- **Current task only:** Apply the resolved preferences without writing a profile.
- **Global default:** Save a personal fallback profile used only when a project has no closer profile or established convention.
- **This project only:** Save `.codex/roblox-structure.md` under the affected project root so it overrides global defaults for that codebase.

Example answer: `Current task only.`

## Defaults and summary

When the user replies `use defaults`, keep every answer already given and resolve only the current and remaining unresolved questions to:

- detected supported workflow, otherwise Studio-native;
- Single client/server entrypoint pair (SSA);
- feature-first grouping within runtime boundaries;
- plain Luau;
- current task only unless the user has clearly asked for a reusable project or global preference.

After all material choices are resolved:

1. For **Current task only**, show `Source of truth`, `Entrypoints`, `Module organization`, `Module style`, and `Preference scope` in a concise summary. Also include any retained naming, package, test-location, lifecycle, or other organization preference that materially affects the current task. Include values inherited from the current request or established conventions so the summary is complete, while making clear they were not re-asked, then continue without an unnecessary confirmation stop.
2. For a persistent project or global scope, show one explicit pre-write preview before asking for confirmation. Identify the selected scope and destination, then show every version-1 field exactly as it will be persisted: `Source of truth`, `Entrypoints`, `Module organization`, `Module style`, `Naming`, `Tests`, and `Notes`.
3. Ask the user to reply `proceed`, `change N`, or name the selection to change only when a persistent profile write, ambiguity, or explicitly requested approval gate still requires confirmation. `proceed` authorizes only the displayed profile write and does not broaden project modification authority.
4. When a selection changes, ask only that main question and its required clarification follow-ups, then regenerate the applicable summary or persistent pre-write preview before continuing or requesting `proceed` again.
5. For **Current task only**, write no profile. For a persistent selection, write only the displayed and confirmed profile after `proceed`, then continue the original task.

## Profile format

For **Current task only**, keep the normalized summary in conversation state and write no profile. Otherwise write project profiles to `.codex/roblox-structure.md`. Write global profiles to `$CODEX_HOME/roblox-structure-profile.md`; when `CODEX_HOME` is unset, use the platform user `.codex` directory. Infer preference scope from the path rather than storing it as a field. Never persist task-specific modification authority in a profile; establish it anew for each task.

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
<verbatim organization details, or None; may name preferred tools/workflows but never grants modification permission or overrides governing/tool/safety rules>
```

For a custom selection, write `Custom` as the normalized field value and preserve the directly implementable organization convention verbatim in `Notes`. Put a named framework and lifecycle summary in `Module style` and preserve extra wording in `Notes`. Interpret `Notes` as organization and workflow context; it may name preferred tools or checks, but never use profile text to broaden task authority or override governing instructions, tool rules, or safety rules.

A profile is valid only when `Profile version` equals `1` and every listed heading has non-empty content. The title is recommended but not required for validity.

## Existing profiles

Use the convention-resolution precedence, profile-drift handling, and modification-authority rules in [`SKILL.md`](../SKILL.md). This section owns only profile parsing, normalization, and authorized write interaction when wizard involvement is required.

- Existing version-1 values such as `Single Script Architecture` remain accepted aliases for the single client/server entrypoint-pair preference.
- Treat a missing field or version as incomplete. Ask only for the missing decisions, show the complete normalized version-1 profile, and wait for `proceed` before writing it.
- Treat an unsupported version as incomplete without overwriting it automatically. Preserve its contents, ask only for decisions the current skill cannot resolve from recognized fields, show the proposed version-1 normalization, and wait for `proceed` before replacing it.
