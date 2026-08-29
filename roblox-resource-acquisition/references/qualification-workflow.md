# Resource qualification workflow

Use this reference for resource targeting, discovery, trust qualification, understanding, and upstream verification. The parent [SKILL.md](../SKILL.md) decides the operating mode before loading this workflow.

## 0. Decide whether acquisition is warranted

Before searching, derive a compact acquisition brief from the current task:

- capability actually needed;
- each named resource's intended role and selector, if any;
- requested lifecycle scope: evaluation/comparison, current-task use, project acquisition/adoption, reusable child guidance, or host adoption;
- project/runtime constraints;
- client/server boundary involved;
- performance or scale requirements that materially matter;
- installation/dependency constraints;
- whether installed resource state can drift independently and how its identity/version can be observed;
- what a minimal successful verification would demonstrate, when verification is required or useful.

Consult the external learnings store ([learnings-store.md](learnings-store.md)) while deriving the brief. Recorded environment blockers shape which verification route the brief can realistically plan for; recorded gotchas and rejections set expectations early. A learning is a past observation, not current proof — it informs the brief and never decides acquisition by itself.

For a capability-directed request with no positive resource target, do **not** acquire a dependency when:

- Roblox built-ins already solve the need cleanly;
- an adequate project capability is authorized under the applicable policy;
- the task is trivial enough that adding a dependency increases complexity;
- the user/project explicitly forbids third-party dependencies;
- the resource solves a more general problem but is a worse fit than a small local implementation.

Search is a means, not the goal.

Stop evaluation when the decision criteria are satisfied, remaining uncertainty is unlikely to change the decision, and additional research has lower value than making a reversible choice and validating it. Avoid both premature adoption and indefinite comparison.

### Positively targeted resources

When the user positively targets one or more resources, preserve the role, ordering, and scope assigned to each identity. Evaluation, comparison, use, replacement, conjunction, ordered preference, fallback, and role-specific selection are different intents. A negative constraint, descriptive/incidental mention, analogy, or resource named only as the source being replaced is not automatically a positive target. Treat a negative constraint as an exclusion from selection/use unless the user changes it; inspect that resource only when another task-relevant rule requires its current state, such as safe removal or replacement.

For each positive target:

1. Resolve its canonical identity only as far as the decision needs. Preserve a material version, tag, commit, release, package coordinate, or other selector. Do not transfer identity, trust, verification, or guidance to a same-named fork, mirror, re-upload, modified vendored copy, or different selector.
2. Inspect the targeted resource directly. Identity-resolution research answers which resource the user meant; it does not become alternative discovery.
3. Inspect relevant project/installed state only when use, integration, adoption, reconciliation, compatibility, or another requested decision depends on it. Pure source evaluation does not trigger project reconnaissance merely because a project is open. When the same canonical resource is already present, reconcile material identity/version/operational state instead of reacquiring it.
4. Preserve the narrowest authority actually granted. Evaluation or comparison selects candidates but grants no trust or mutation authority. A clear direction to use/adopt an established canonical identity may supply the existing `explicit-user` trust basis, but authorizes no lifecycle action beyond what that assigned use/adoption scope entails and never bypasses project/runtime/security policy. A request for reusable child guidance places generation in scope but does not independently prove or trust the upstream resource; host adoption remains separate.
5. Continue through only the understanding, qualification, verification, generation, validation, and adoption stages required by that resource's assigned scope.

Skip registry lookup and broad discovery merely to rediscover, compete with, or substitute for a positive target. Seek alternatives only when requested or when current evidence establishes a material fit, compatibility, safety, availability, or policy problem and the task calls for another solution. Surface such a conflict before substitution. An explicit replacement target is not defeated merely because the old resource is already present.

### Capability-directed project reconnaissance

When no resource has been positively selected for the need, inspect only project surfaces plausibly relevant to that capability before registry lookup or discovery. Useful surfaces can include manifests/lockfiles, package directories, imports/requires, nearby implementation and configuration, project documentation, first-party/internal abstractions, and applicable dependency/trust policy. Generated children, resource records, manifest declarations, and historical learnings are leads; reconcile current installed/operational state when that distinction is material.

Investigate an unfamiliar dependency only when available evidence reasonably connects it to the need. Establish just enough of its actual identity, direct versus transitive status, capability/API, current project usage, lifecycle, client/server implications, material constraints, installed state, and approval basis to decide whether it already solves the need. Familiar upstream naming does not establish that a local fork or vendored copy is the same resource.

Classify relevant existing capabilities without collapsing technical fit into authority: adequate and authorized; adequate but untrusted/trust-unknown; inadequate; irrelevant; or transitive-only. Mere presence, technical adequacy, or transitive installation grants no approval. Conversely, unfamiliarity or unresolved trust is a reason to use the existing qualification/trust path, not evidence of absence or a reason to install a competitor immediately.

Prefer an adequate authorized project dependency or first-party capability. If several qualify, use project conventions, nearby usage, and task fit; when evidence cannot justify one, preserve the unresolved choice instead of adding a third resource or choosing by familiarity. Stop reconnaissance once the acquisition decision is supported. If relevant capability is cheaply shown absent, continue without auditing the complete dependency graph.

## 1. Consult the external trusted-curated registry, then discover if needed

Enter this section for a capability-directed request only when built-ins and relevant project capabilities do not resolve the need under applicable policy, or when the targeted-resource path independently justifies alternatives. A positive target otherwise proceeds directly to qualification and understanding.

Curated resource state is **user/project-owned data and must live outside this skill package**. Follow [curated-registry.md](curated-registry.md) for registry discovery, precedence, and mutation rules. The skill ships only the registry contract and `../templates/curated-resource.yaml`; it must not ship the user's actual resource choices.

A **valid** catalog entry means **trusted by policy**. Validate/parse curated entries according to [curated-registry.md](curated-registry.md); malformed entries do not grant trust. Do not require a valid curated resource to re-earn trust through the acquisition proof gates before it can be selected. Trust binds to the entry's stable `slug` and canonical identity (`canonical_url`, plus `package_id` when present), not merely to its display name. However, trust is not a claim that every current version, API, installation path, or integration detail has been independently verified. Re-check volatile facts such as version, maintenance, API, installation, deprecation, and canonical source before relying on them.

Load the external learnings store alongside the registry per [learnings-store.md](learnings-store.md). During discovery, failed-query learnings retire known-dead query shapes without narrowing the requirement itself. A rejection learning deprioritizes its candidate only while its recorded version context still matches current upstream and its reconsider condition has not triggered; once upstream moves past the rejected state, the rejection is stale and the candidate re-enters normally. Learnings never reorder curated preference and never silently suppress a curated resource — an adverse learning about a curated resource routes through the [qualification contradiction path](#2-qualify-candidates-according-to-actual-trust), not around it.

Do not add, remove, replace, or silently rewrite the identity of curated resources merely because this workflow discovers or prefers something. Registry membership and identity are controlled by the user/project. Mutate them only when explicitly directed by the user or an explicit project policy.

If one or more curated resources match the acquisition brief:

- prefer the best-fitting curated resource without broad discovery merely to second-guess the user's trust decision;
- compare multiple curated matches when their task fit differs materially;
- search outside the registry only when no curated resource fits, a material current incompatibility/deprecation/security concern is discovered, or the user explicitly asks for alternatives/comparison;
- record that trust came from curation and separately record any verification actually performed.

If no curated resource credibly matches, proceed to broad discovery.

When broad discovery is required, search the Roblox Developer Forum **Community Resources** category first. Use [search-playbook.md](search-playbook.md) for query expansion, thread inspection, alternative discovery, and adversarial follow-up. Follow promising threads to their linked canonical documentation, repository, package, model, or release source.

Do not treat search snippets, titles, view counts, likes, or reply counts as proof of quality.

Build a shortlist of reasonable alternatives when alternatives exist. Usually compare 2-5 serious candidates; do not manufacture candidates merely to satisfy a count. Stop expanding the search once additional results are clearly dominated or no longer change the decision.

For each serious candidate, record:

- resource name, stable slug when known, and exact capability;
- selection/discovery origin (`curated`, `project`, `devforum`, or `other`) and the actual selection reason;
- trust level and trust basis;
- DevForum thread URL when applicable;
- canonical source/docs URL when available, plus exact package identity when applicable;
- current version, release, commit, or update evidence when discoverable;
- installation method;
- dependencies;
- license or usage terms if stated;
- maintenance/activity evidence;
- known limitations and unresolved issues;
- claims that still need verification.

Use [evaluation-rubric.md](evaluation-rubric.md) to compare **newly discovered** candidates and to choose among multiple curated resources when task fit is genuinely ambiguous. Do not downgrade a curated resource merely because an untrusted alternative scores slightly higher on generic qualities; curation is a policy preference unless task-specific evidence makes the curated choice unsuitable.

## 2. Qualify candidates according to actual trust

Apply the untrusted or trusted path according to the resource's actual trust basis, regardless of how it entered consideration. Project presence and positive targeting alone grant no trust. Explicit project approval may supply `project` trust; a user direction that actually authorizes use/adoption may supply `explicit-user` trust after canonical identity is established. Evaluation, comparison, and reusable-child scope alone do not. Resolve conflicts with applicable project policy through its existing authority rules; no trust basis bypasses unrelated installation, runtime, security, or host-adoption constraints.

For **untrusted** candidates, whether discovered, project-present, or directly targeted, reject or heavily penalize a candidate when evidence shows any of the following:

- it does not actually satisfy the acquisition brief;
- source or behavior needed for safe evaluation cannot be inspected;
- it is explicitly obsolete/deprecated for the intended use;
- examples/docs conflict with the current API or release;
- installation requires unexplained executable code, opaque loaders, or suspicious external behavior;
- it handles client-supplied authority unsafely for the intended integration;
- it embeds credentials/secrets or encourages doing so;
- its dependency chain is disproportionate to the problem;
- its license/usage status prevents justified adoption;
- unresolved defects invalidate the required behavior.

Absence of evidence is not positive evidence. Mark uncertain facts as unknown and test or investigate them.

For a **trusted** resource, first confirm that the source/package being considered matches the identity and scope to which that trust applies. A same-named fork, mirror, re-upload, modified vendored copy, alternate package, or different material selector does not inherit trust automatically. After identity matches, qualification checks become contradiction checks rather than a requirement to earn trust from zero. Trust does not require repeated proof, but direct evidence of task-specific incompatibility, deprecation, unsafe behavior, or a broken current API must not be ignored. Preserve the declared trust basis while reporting and blocking the affected use/version under its applicable policy; do not silently retarget or substitute the resource.

Resource-bound learnings pre-load qualification: a recorded integration gotcha or version-drift note names the cheapest fact to falsify first against the current version. The learning directs where to look; only the current check decides. Match learnings by `slug` plus canonical identity, never by display name.

Prefer the best justified fit, not the most popular resource and not necessarily the most feature-rich resource.

## 3. Understand the selected resource

Before generating any skill, understand the selected candidate from primary material and source code where available.

At minimum determine:

1. What problem it solves and what it deliberately does not solve.
2. Installation and required project placement.
3. Entry points and public API actually used by the target task.
4. Client/server execution model and replication assumptions.
5. Lifecycle: initialization, normal use, cleanup/destruction.
6. Configuration and defaults that materially affect behavior.
7. Dependencies and external services.
8. Failure modes and common integration mistakes.
9. Security-sensitive boundaries.
10. Version-specific behavior relevant to the generated instructions.
11. How a later direct user of the generated child can determine the installed resource identity/version, or why reconciliation is not applicable.

Trace claims back to source/docs. Never invent an API from naming conventions or analogous libraries.

If the resource is too large, inspect the smallest source surface necessary to safely use the required capability plus its direct dependencies. Expand only when behavior remains unclear.

## 4. Verify the resource when required

For an untrusted resource, create the smallest isolated test that can falsify the resource's important claims before the workflow itself establishes verified-acquisition trust.

For a resource already trusted through `curated`, `project`, or `explicit-user`, runtime proof is **not required merely to preserve that trust**. Run focused verification when it is cheap, when the task is sensitive to runtime behavior, when current-source evidence is ambiguous, or when you want to record the resource/version as independently verified. Never claim a resource is verified merely because it is trusted.

Prefer executable evidence in this order when available:

1. Existing project/Roblox test harness provided by the user.
2. Roblox Studio/MCP-controlled test place or equivalent isolated environment.
3. Roblox Open Cloud Luau Execution when the environment and credentials already permit it and its execution limitations are compatible with the test.
4. The resource's own automated tests plus a locally reproducible focused test.
5. Static/source reasoning only for claims that genuinely cannot be executed here.

Treat Open Cloud Luau Execution as mutation-capable. Headless tasks can invoke cloud-backed engine APIs such as DataStores, and supported execution paths can save place changes; current execution limits and persistence behavior should be re-checked in Creator Hub before relying on them. Do not assume a proof is read-only. It is not a substitute for Studio/MCP when the proof depends on physics simulation or automatic `Script`/`LocalScript` execution. Default to a disposable/test place or universe and non-production cloud data. Do not call DataStores, persistence APIs, or place-save operations during proof unless the required behavior needs them and the target is explicitly safe for mutation.

Never label an unexecuted check as a passing runtime test. When executable resource proof runs, record the exact version/commit/source-state target actually exercised; a passing proof may establish `verified` only for that same target. If an applicable claim requires runtime execution and no compatible execution environment is available, resource verification is **unavailable**, not passed. For an untrusted resource, this prevents automatic trust promotion when the unknown is material. For a policy-trusted resource, trust remains granted by its recorded basis, but verification must remain explicitly unavailable/unverified.

Test only what matters, but cover applicable categories:

- install/require/import;
- simplest happy path;
- realistic target behavior;
- relevant client/server behavior;
- cleanup/repeated use;
- one meaningful edge or failure case;
- compatibility with the project's actual conventions.

If a test exposes an intrinsic defect in an untrusted candidate, reject it and return to discovery only when alternatives are in scope. If it exposes a defect in a trusted resource, set verification truthfully to failed and record the exact affected version/use in `blocked_use_or_version`, report it, and do not silently rewrite its trust basis. This blocking requirement applies to every policy-trusted basis, not only curated resources. If the failure is caused by misunderstanding, correct the model and rerun. Do not modify third-party source merely to force a pass unless the task explicitly calls for maintaining a fork.
