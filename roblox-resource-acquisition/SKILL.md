---
name: roblox-resource-acquisition
description: Acquires, adopts, repairs, and reconciles Roblox community resources as reusable agent skills. Use when a Roblox task needs a community resource, when evaluating or comparing one, when generating or operationally adopting its child skill, when installed resource state may differ from that child's reviewed source state, or when ordinary use reveals a child-skill defect or a newer parent-side block.
metadata:
  compatibility: Scripts require Python 3.8+ and PyYAML (pip install -r requirements.txt). A single required parser keeps validation verdicts identical across environments; scripts exit with code 2 and an install hint when PyYAML is missing.
---

# Roblox Resource Acquisition

Acquire Roblox community tooling only when it is justified by the task. Treat user/project-curated resources as trusted policy choices, while keeping trust separate from runtime verification and from validation of any generated skill.

## Core rule

Do not turn the first plausible DevForum result into a skill.

Use this sequence:

**need + requested scope -> classify positive resource targets versus a capability need -> inspect the targeted resource directly, or check relevant built-ins/project capabilities before registry/discovery -> understand -> verify when required -> generate skill only when in scope -> validate artifact -> adopt operationally, cache, or reject -> reconcile and repair**

Curation is an explicit trust decision by the user/project. **Trusted does not mean verified.** A curated resource may be used without re-proving the library from scratch, but volatile integration facts still need refreshing and a generated skill still has its own validation burden. Likewise, a resource passing its own tests does not prove that an agent can use it correctly.

Choose the narrowest operating mode that satisfies the request:

- **evaluate/compare** — stop after the requested evidence and decision; do not generate a skill as extra scope;
- **acquire/adopt** — qualify and integrate the resource only to the requested project scope; generate a reusable child only when that guidance is in scope, then run the separate authorized host-adoption gate only when operational adoption is requested;
- **refresh** — for an existing resource skill, confirm canonical identity, re-check only the source/version surfaces that can have drifted, patch the skill, then rerun structural and affected behavioral tests. Do not restart broad discovery unless the current resource is materially unsuitable or alternatives were requested.
- **repair/reconcile** — use for a defect found during ordinary use, an installed/source-state mismatch, a current matching block or adverse observation, or legacy child/record state. Reconcile identity and project/host state, enter the existing repair classification, rerun invalidated gates, and re-adopt only with authorization.

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

Consult the external learnings store (`references/learnings-store.md`) while deriving the brief. Recorded environment blockers shape which verification route the brief can realistically plan for; recorded gotchas and rejections set expectations early. A learning is a past observation, not current proof — it informs the brief and never decides acquisition by itself.

For a capability-directed request with no positive resource target, do **not** acquire a dependency when:

- Roblox built-ins already solve the need cleanly;
- an adequate project capability is authorized under the applicable policy;
- the task is trivial enough that adding a dependency increases complexity;
- the user/project explicitly forbids third-party dependencies;
- the resource solves a more general problem but is a worse fit than a small local implementation.

Search is a means, not the goal.

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

Curated resource state is **user/project-owned data and must live outside this skill package**. Follow `references/curated-registry.md` for registry discovery, precedence, and mutation rules. The skill ships only the registry contract and `templates/curated-resource.yaml`; it must not ship the user's actual resource choices.

A **valid** catalog entry means **trusted by policy**. Validate/parse curated entries according to `references/curated-registry.md`; malformed entries do not grant trust. Do not require a valid curated resource to re-earn trust through the acquisition proof gates before it can be selected. Trust binds to the entry's stable `slug` and canonical identity (`canonical_url`, plus `package_id` when present), not merely to its display name. However, trust is not a claim that every current version, API, installation path, or integration detail has been independently verified. Re-check volatile facts such as version, maintenance, API, installation, deprecation, and canonical source before relying on them.

Load the external learnings store alongside the registry per `references/learnings-store.md`. During discovery, failed-query learnings retire known-dead query shapes without narrowing the requirement itself. A rejection learning deprioritizes its candidate only while its recorded version context still matches current upstream and its reconsider condition has not triggered; once upstream moves past the rejected state, the rejection is stale and the candidate re-enters normally. Learnings never reorder curated preference and never silently suppress a curated resource — an adverse learning about a curated resource routes through the section 2 contradiction path, not around it.

Do not add, remove, replace, or silently rewrite the identity of curated resources merely because this workflow discovers or prefers something. Registry membership and identity are controlled by the user/project. Mutate them only when explicitly directed by the user or an explicit project policy.

If one or more curated resources match the acquisition brief:

- prefer the best-fitting curated resource without broad discovery merely to second-guess the user's trust decision;
- compare multiple curated matches when their task fit differs materially;
- search outside the registry only when no curated resource fits, a material current incompatibility/deprecation/security concern is discovered, or the user explicitly asks for alternatives/comparison;
- record that trust came from curation and separately record any verification actually performed.

If no curated resource credibly matches, proceed to broad discovery.

When broad discovery is required, search the Roblox Developer Forum **Community Resources** category first. Use `references/search-playbook.md` for query expansion, thread inspection, alternative discovery, and adversarial follow-up. Follow promising threads to their linked canonical documentation, repository, package, model, or release source.

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

Use `references/evaluation-rubric.md` to compare **newly discovered** candidates and to choose among multiple curated resources when task fit is genuinely ambiguous. Do not downgrade a curated resource merely because an untrusted alternative scores slightly higher on generic qualities; curation is a policy preference unless task-specific evidence makes the curated choice unsuitable.

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

Never label an unexecuted check as a passing runtime test. If an applicable claim requires runtime execution and no compatible execution environment is available, resource verification is **unavailable**, not passed. For an untrusted resource, this prevents automatic trust promotion when the unknown is material. For a policy-trusted resource, trust remains granted by its recorded basis, but verification must remain explicitly unavailable/unverified.

Test only what matters, but cover applicable categories:

- install/require/import;
- simplest happy path;
- realistic target behavior;
- relevant client/server behavior;
- cleanup/repeated use;
- one meaningful edge or failure case;
- compatibility with the project's actual conventions.

If a test exposes an intrinsic defect in an untrusted candidate, reject it and return to discovery only when alternatives are in scope. If it exposes a defect in a trusted resource, mark the affected verification/use as failed or blocked, report it, and do not silently rewrite its trust basis. If the failure is caused by misunderstanding, correct the model and rerun. Do not modify third-party source merely to force a pass unless the task explicitly calls for maintaining a fork.

## 5. Generate the resource skill when adoption/reuse is in scope

If the user asked only to evaluate, compare, or inspect a resource and the current task does not require adopting it as reusable agent guidance, stop after the requested evaluation/verification result instead of creating a skill as extra scope.

When reusable child generation is in scope, an untrusted resource — whether discovered, already project-present, or directly targeted — may receive a dedicated reusable skill only after the required resource verification passes. A resource trusted through `curated`, `project`, or `explicit-user` may receive one after current-source understanding is sufficient even when runtime verification is unavailable, because its trust came from policy rather than this workflow. In either case, use `templates/resource-skill-template.md` and `references/resource-skill-contract.md`.

Use this same generation path for an adequate existing dependency or an explicitly targeted resource; do not create a parallel child mechanism. Generate only when reusable guidance is in scope and justified. Child creation or validation does not imply that this workflow installed the upstream resource, grant upstream trust, upgrade upstream verification, change selection provenance, or make either the resource or child operational. Host adoption remains a separate authorized gate.

The generated skill must be operational guidance, not a copy of the DevForum post or README. It should teach an agent how to decide, install, use, verify, and troubleshoot the resource with minimal irrelevant context. Include the closest credible alternative or Roblox built-in when relevant; if none is meaningful, say why. Always retain a `Security notes` section: document applicable resource-specific trust boundaries, or explicitly state when there are no special ones beyond normal Roblox server-authoritative expectations.

Every generated child must include the operational reconciliation contract from `references/resource-skill-contract.md`: stable resource identity, a `required` or justified `not-applicable` reconciliation policy, a resource-specific installed-state check, parent-state reconciliation, and a defect/mismatch handoff to this skill's `repair/reconcile` mode. Use `references/operational-lifecycle.md` for the shared lifecycle semantics; do not copy its host-independent rules into multiple references.

Pin claims to the exact source version/release/commit reviewed when possible. If no stable identifier exists, record the exact review date and source state instead of pretending it is version-pinned. In the generated skill, record resource verification separately as `verified`, `unverified`, or `unavailable`; source review is not runtime proof.

Do not treat trust in the upstream resource as proof that the generated instructions are correct. A generated skill must carry its own validation/verification state and must not claim behavioral validation merely because its resource was curated.

## 6. Validate the generated skill independently

Treat this as a second product with its own failure modes.

Use `references/testing-protocol.md`.

When the harness supports isolated/fresh subagents, give a fresh agent only:

- the generated skill;
- the minimum project context required by the test;
- a task that requires the resource.

Do not expose the research transcript or hidden assumptions used to create the skill.

At minimum validate:

- positive activation: it recognizes an appropriate use;
- negative activation: it stays out of an unrelated or simpler task;
- clean setup from the documented prerequisites;
- correct happy-path implementation;
- a realistic integration task;
- a meaningful edge/failure case;
- troubleshooting without invented APIs;
- version/provenance visibility and truthful resource-verification status;
- security guidance when applicable.

If no fresh-agent mechanism exists, run the same protocol as an explicit contract audit and mark behavioral execution as unavailable rather than pretending independence. The audit can find instruction defects, but it does **not** establish independent behavioral verification of the generated skill.

Run `scripts/validate_skill.py <generated-skill-directory>` as a structural gate when Python is available. Treat its PASS as structural evidence only, never as proof that the prose, upstream claims, or runtime behavior are correct.

Whenever a child is added, refreshed, repaired, or adopted, run `scripts/validate_skill_catalog.py <skill-directory-or-root> [...]` against the target generated-child set. Duplicate identities/descriptions fail. Reported activation-overlap clusters require the catalog behavioral tests in `references/testing-protocol.md`; static PASS never proves host routing.

**Script dependencies.** All scripts in `scripts/` require Python 3.8+ and PyYAML (`pip install -r requirements.txt`); everything else is standard library. PyYAML is required rather than optional so that every environment parses registry, learnings, and record files identically — a validation verdict, and therefore a trust decision, must never depend on which parser happened to be installed. When PyYAML is missing the scripts exit with code 2 and an install hint (exit 1 remains validation failure, 0 pass). No other packages, databases, or network access are needed.

## 7. Repair the generated skill until it converges

Repair scope is the generated resource skill and its validation/adoption evidence, whether the defect appears before adoption or during ordinary post-adoption use — never this acquisition skill's own package files, which follow the self-growth boundaries below. Full loop mechanics live in `references/repair-loop.md`.

Work in bounded cycles. One cycle: classify the failure, apply the single narrowest fix for one distinct failing check, re-run what the class prescribes plus the regression reruns required by `references/testing-protocol.md`, append one learning entry to the external learnings store, then re-assess.

Classify before editing:

- **resource failure (untrusted candidate)** -> reject the affected candidate; consider another only when alternatives are in scope; record a `rejection` learning; that candidate's resource verification is recorded failed;
- **resource failure (trusted)** -> block the affected version/use and report the contradiction; record a `version-drift` or `integration-gotcha` learning; canonical identity and recorded trust stay untouched unless the controlling user/project policy changes them;
- **understanding failure** -> correct the model from source/docs; re-run the resource proof the misunderstanding invalidated; record an `integration-gotcha` learning;
- **skill instruction failure** -> patch only the instructions responsible; re-run the failed check plus every previously passing applicable check; record a `repair-outcome` learning; the patch voids prior behavioral passes until those reruns complete;
- **environment failure** -> fix or document the prerequisite and re-run the blocked check, or record it unavailable if unfixable; record an `environment-blocker` learning; never distort the skill around a broken environment;
- **test failure** -> repair the invalid test, re-run it, and demonstrate the repaired test can still fail; record a `repair-outcome` learning; results produced by the invalid test are void.

Budget: at most **three repair cycles per distinct failing check**; the fourth failure of the same check stops the loop. Do not endlessly polish. Stop with success only when the reliability threshold in `references/testing-protocol.md` is met. Stop and escalate to the user when a check exhausts its budget, when patches oscillate (a fix reverting an earlier fix, or two checks alternately breaking), or when failures expose a fundamental mismatch rather than a fixable skill defect — then reject the untrusted candidate or block the trusted use and surface the evidence instead of lowering the bar. Escalation states the failing checks, each attempt and its result, truthful current statuses, the learnings appended, and the user's options.

No repair activity upgrades any status implicitly. Resource verification and `skill_validation` each move only when their own gate actually re-executes and passes; a patch moves affected behavioral status down until reruns restore it.

A confirmed post-adoption defect marks every affected `host_adoptions` entry `blocked` and invalidates affected behavioral and catalog-routing passes before repair. Restoring `operational` requires the regression suite, catalog validation, an authorized update of the host copy, and a fresh explicit host-activation pass. Follow `references/operational-lifecycle.md`.

## 8. Record trust and verification separately

Do not overload one status word with two meanings. Track **trust** (who/what authorizes normal use) separately from **verification** (what has actually been proven).

### Trust

For resources this workflow actively acquires, trust normally comes from:

- **curated** — valid explicit user/project catalog membership. Trust is immediate for the canonical identity named by the entry and does not require this workflow to re-prove the library;
- **verified-acquisition** — a previously untrusted candidate completed all applicable resource-proof and generated-skill behavioral gates required for normal adoption.

An explicitly project-approved dependency may arrive with inherited `project` trust. A user direction that authorizes use/adoption of the established canonical identity may supply `explicit-user` trust. Preserve the declared basis rather than pretending this workflow established it. Installation alone, transitive presence, evaluation/comparison targeting, or a child-generation request alone supplies no trust; without another valid basis the resource remains untrusted candidate/cache research.

### Verification

Resource verification describes proof of the selected upstream resource identity/version only. Track generated-skill structural and behavioral validation separately under `skill_validation`; neither layer upgrades the other automatically.

Record resource verification as one of:

- **verified** — all applicable resource/runtime proof required for the intended use actually executed and passed;
- **unverified** — verification has not yet been established; checks may be unattempted or incomplete, but no decisive failure or known execution blocker has been recorded;
- **unavailable** — a material required execution check cannot be performed in the available environment;
- **failed** — relevant executable proof failed or current evidence directly contradicts the intended use.

Thus a resource can legitimately be **trusted + unverified** through a policy trust basis. Never rewrite that as "verified." An untrusted resource remains **untrusted + unverified** while proof is incomplete, with partial evidence recorded in `resource_proof`, until it completes enough gates for verified-acquisition trust.

### Candidate/cache

Keep non-trusted candidate research here when it may be useful later but has not earned verified-acquisition trust. Do not let candidate state masquerade as trusted guidance.

### Rejected / blocked

For untrusted candidates, record enough information to avoid wasteful repeat investigation:

- resource and source URL;
- validation date;
- rejected version/state;
- concise reason;
- evidence that would justify reconsideration.

For trusted resources, record the affected version/use as failed or blocked without silently changing identity or trust. For curated resources specifically, leave catalog membership and canonical identity unchanged until explicitly modified.

Use the mandatory schema-version 2 `templates/resource-record.yaml` for a portable evidence record when the environment has no registry format of its own. The existing record model separates selection provenance from trust: use `discovery_origin: other` for a direct user target and state its exact role/scope in `selection_reason`; use `project` only for a capability found through project reconnaissance. Neither value determines `trust.basis`. Carry the established `slug`, `canonical_url`, `package_id`, and material selector/version into the record so evidence cannot drift onto a same-named or differently selected resource. Record installed/parent reconciliation separately from upstream verification, and record artifact state separately from each host adoption. An empty `host_adoptions` list means artifact only; `operational` requires every host-applicable evidence facet plus explicit activation. Legacy children and records fail the current contract and enter `repair/reconcile`; never synthesize missing lifecycle evidence. A record whose trust basis is `verified-acquisition` requires executed/passing applicable resource proof, generated-skill structural validation, executed/passing independent generated-skill behavioral validation, provenance, and no material unavailable claims. A record whose trust basis is `curated` does not require those gates to be trusted, but every verification field must still be truthful. Whenever this workflow writes or updates a portable resource record, run `scripts/validate_resource_record.py <resource-record.yaml>` when Python is available. Its PASS establishes only structural/state consistency; it does not prove the recorded evidence is true. Record discovery, reconciliation, host evidence, authorization, and state transitions per `references/operational-lifecycle.md`.

## Self-growth boundaries

Durable learning has exactly two destinations with different mutation rules.

**External learnings store** — user/project-owned observation data outside this package, governed by `references/learnings-store.md`. Appending a new entry (integration gotchas, failed query patterns, version drift notes, environment blockers, rejection reasons, repair outcomes) is autonomous and needs no permission. Editing, retargeting, or deleting any existing entry requires explicit user permission in chat, every time; there is no standing allowlist. This package ships only the store contract and `templates/learning-entry.yaml`; never bundle accumulated entries into the package or into a generated skill.

**This skill package** (SKILL.md, references/, scripts/, templates/) — never edited autonomously. When evidence shows this package's own guidance is wrong or incomplete: stop the affected step, state the evidence, propose the exact diff (file, current text, replacement), and wait for an explicit yes from the user in chat. No silent patching; each yes authorizes only the single diff it answered.

## Scope expansion proposals

This workflow may propose — never implement unprompted — expansions of its own scope: new operating modes, new resource classes, or changes to the frontmatter description or any other activation surface. A proposal is made in chat and states three things: what would newly activate, what existing behavior could regress, and what new failure modes the expansion introduces. Nothing is written until the user gives an explicit yes, and each yes authorizes only the proposal it answered.

## Source hygiene

Community Resources is discovery evidence, not authority over Roblox engine behavior. For Roblox APIs, security behavior, package behavior, and platform constraints, verify against current Roblox Creator Hub documentation when material.

When a DevForum resource links to a canonical repository/docs site, use that source to understand the resource rather than relying on third-party summaries.

Re-check volatile facts such as current versions, maintenance status, APIs, and deprecation before generating or refreshing a skill.

## Security defaults

For unfamiliar packages/models/modules:

- inspect scripts before allowing them into a real project;
- avoid opaque or dynamically fetched executable code without strong justification and inspection;
- never place secrets/API keys directly in source;
- preserve server authority and validate client-controlled inputs;
- treat auto-updating third-party packages as a supply-chain decision, not a convenience default;
- prefer isolated testing and reversible changes before project integration.

Do not publish, spend money, expose credentials, or perform irreversible project mutations merely to validate a resource.

## Output discipline

Keep research proportional to the task. The final acquisition result should make the decision auditable without dumping the entire research process.

Report:

- selected resource and why it fits; compare alternatives only when comparison was required or explicitly requested;
- verification performed and result (or explicitly unverified/unavailable);
- generated skill location/name;
- skill validation performed and result;
- reconciliation status and any blocked use/version;
- artifact-only versus per-host adoption state, with the evidence supporting `operational` when claimed;
- catalog fingerprint, static result, and independent routing result when applicable;
- important limitations/version pin;
- learning entries appended to the external store during the run, when any;
- rejected alternatives only when their rejection materially explains the decision.

Do not bundle user/project curated registry data, research transcripts, caches, temporary test fixtures, or unrelated artifacts into a generated runtime skill package. Keep only the instructions, references, templates, and helper scripts the skill actually needs.

If no permitted existing or targeted resource resolves the need and no curated/discovered candidate clears the required acquisition gates, say so and implement locally or return the unresolved need instead of manufacturing a recommendation.

