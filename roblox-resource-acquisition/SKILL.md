---
name: roblox-resource-acquisition
description: Finds, evaluates, verifies, learns, packages, refreshes, and validates Roblox community resources as reusable agent skills. Use when a Roblox task needs a reusable capability not adequately covered by Roblox built-ins or already-trusted dependencies, when an existing resource skill needs source/version refresh, or when explicitly asked to discover, compare, or evaluate a community library, module, framework, plugin, package, or other Community Resource.
compatibility: Scripts require Python 3.8+ and PyYAML (pip install -r requirements.txt). A single required parser keeps validation verdicts identical across environments; scripts exit with code 2 and an install hint when PyYAML is missing.
---

# Roblox Resource Acquisition

Acquire Roblox community tooling only when it is justified by the task. Treat user/project-curated resources as trusted policy choices, while keeping trust separate from runtime verification and from validation of any generated skill.

## Core rule

Do not turn the first plausible DevForum result into a skill.

Use this sequence:

**need -> check built-ins/project -> consult trusted curated registry -> use if fit or discover if needed -> understand -> verify when required -> generate skill -> validate skill -> adopt, cache, or reject**

Curation is an explicit trust decision by the user/project. **Trusted does not mean verified.** A curated resource may be used without re-proving the library from scratch, but volatile integration facts still need refreshing and a generated skill still has its own validation burden. Likewise, a resource passing its own tests does not prove that an agent can use it correctly.

Choose the narrowest operating mode that satisfies the request:

- **evaluate/compare** — stop after the requested evidence and decision; do not generate a skill as extra scope;
- **acquire/adopt** — run the full workflow through generated-skill validation;
- **refresh** — for an existing resource skill, confirm canonical identity, re-check only the source/version surfaces that can have drifted, patch the skill, then rerun structural and affected behavioral tests. Do not restart broad discovery unless the current resource is materially unsuitable or alternatives were requested.

## 0. Decide whether acquisition is warranted

Before searching, derive a compact acquisition brief from the current task:

- capability actually needed;
- project/runtime constraints;
- client/server boundary involved;
- performance or scale requirements that materially matter;
- installation/dependency constraints;
- what a minimal successful verification would demonstrate, when verification is required or useful.

Consult the external learnings store (`references/learnings-store.md`) while deriving the brief. Recorded environment blockers shape which verification route the brief can realistically plan for; recorded gotchas and rejections set expectations early. A learning is a past observation, not current proof — it informs the brief and never decides acquisition by itself.

Do **not** acquire a dependency when:

- Roblox built-ins already solve the need cleanly;
- an already-trusted project dependency or installed skill covers it adequately;
- the task is trivial enough that adding a dependency increases complexity;
- the user/project explicitly forbids third-party dependencies;
- the resource solves a more general problem but is a worse fit than a small local implementation.

Search is a means, not the goal.

## 1. Consult the external trusted-curated registry, then discover if needed

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
- discovery origin (`curated`, `project`, `devforum`, or other);
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

## 2. Qualify newly discovered candidates; sanity-check curated ones

For **newly discovered, untrusted** candidates, reject or heavily penalize a candidate when evidence shows any of the following:

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

For a **curated/trusted** resource, first confirm that the source/package being considered matches the curated canonical identity. A same-named fork, mirror, re-upload, or alternate package does not inherit trust automatically. After identity matches, qualification checks become contradiction checks rather than a requirement to earn trust from zero. Trust does not require repeated proof, but direct evidence of task-specific incompatibility, deprecation, unsafe behavior, or a broken current API must not be ignored. Do not silently remove the resource from the user's registry; report the contradiction and avoid the affected use/version until the user changes the trust policy or the issue is resolved.

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

Trace claims back to source/docs. Never invent an API from naming conventions or analogous libraries.

If the resource is too large, inspect the smallest source surface necessary to safely use the required capability plus its direct dependencies. Expand only when behavior remains unclear.

## 4. Verify the resource when required

For a newly discovered resource, create the smallest isolated test that can falsify the resource's important claims before the workflow itself establishes trust.

For a curated resource, runtime proof is **not required to preserve or exercise its trusted status**. Run focused verification when it is cheap, when the task is sensitive to runtime behavior, when current-source evidence is ambiguous, or when you want to record the resource/version as independently verified. Never claim a curated resource is verified merely because it is trusted.

Prefer executable evidence in this order when available:

1. Existing project/Roblox test harness provided by the user.
2. Roblox Studio/MCP-controlled test place or equivalent isolated environment.
3. Roblox Open Cloud Luau Execution when the environment and credentials already permit it and its execution limitations are compatible with the test.
4. The resource's own automated tests plus a locally reproducible focused test.
5. Static/source reasoning only for claims that genuinely cannot be executed here.

Treat Open Cloud Luau Execution as mutation-capable. Headless tasks can invoke cloud-backed engine APIs such as DataStores, and supported execution paths can save place changes; current execution limits and persistence behavior should be re-checked in Creator Hub before relying on them. Do not assume a proof is read-only. It is not a substitute for Studio/MCP when the proof depends on physics simulation or automatic `Script`/`LocalScript` execution. Default to a disposable/test place or universe and non-production cloud data. Do not call DataStores, persistence APIs, or place-save operations during proof unless the required behavior needs them and the target is explicitly safe for mutation.

Never label an unexecuted check as a passing runtime test. If an applicable claim requires runtime execution and no compatible execution environment is available, resource verification is **unavailable**, not passed. For an untrusted discovered resource, this prevents automatic trust promotion when the unknown is material. For a curated resource, trust remains user/project-granted, but verification must remain explicitly unavailable/unverified.

Test only what matters, but cover applicable categories:

- install/require/import;
- simplest happy path;
- realistic target behavior;
- relevant client/server behavior;
- cleanup/repeated use;
- one meaningful edge or failure case;
- compatibility with the project's actual conventions.

If a test exposes an intrinsic defect in an untrusted candidate, reject it and return to discovery. If it exposes a defect in a curated resource, mark the affected verification as failed/blocked, report it, and do not silently revoke catalog trust. If the failure is caused by misunderstanding, correct the model and rerun. Do not modify third-party source merely to force a pass unless the task explicitly calls for maintaining a fork.

## 5. Generate the resource skill when adoption/reuse is in scope

If the user asked only to evaluate, compare, or inspect a resource and the current task does not require adopting it as reusable agent guidance, stop after the requested evaluation/verification result instead of creating a skill as extra scope.

For acquisition/adoption work, create a dedicated reusable skill for a newly discovered resource only after the required resource verification passes. For a curated/trusted resource, you may generate the skill after current-source understanding is sufficient even when runtime verification is unavailable, because trust comes from the user's curation rather than from this workflow. In either case, use `templates/resource-skill-template.md` and `references/resource-skill-contract.md`.

The generated skill must be operational guidance, not a copy of the DevForum post or README. It should teach an agent how to decide, install, use, verify, and troubleshoot the resource with minimal irrelevant context. Include the closest credible alternative or Roblox built-in when relevant; if none is meaningful, say why. Always retain a `Security notes` section: document applicable resource-specific trust boundaries, or explicitly state when there are no special ones beyond normal Roblox server-authoritative expectations.

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

**Script dependencies.** All scripts in `scripts/` require Python 3.8+ and PyYAML (`pip install -r requirements.txt`); everything else is standard library. PyYAML is required rather than optional so that every environment parses registry, learnings, and record files identically — a validation verdict, and therefore a trust decision, must never depend on which parser happened to be installed. When PyYAML is missing the scripts exit with code 2 and an install hint (exit 1 remains validation failure, 0 pass). No other packages, databases, or network access are needed.

## 7. Repair the generated skill until it converges

Repair scope is the generated resource skill and its validation evidence only — never this acquisition skill's own package files, which follow the self-growth boundaries below. Full loop mechanics live in `references/repair-loop.md`.

Work in bounded cycles. One cycle: classify the failure, apply the single narrowest fix for one distinct failing check, re-run what the class prescribes plus the regression reruns required by `references/testing-protocol.md`, append one learning entry to the external learnings store, then re-assess.

Classify before editing:

- **resource failure (untrusted discovery)** -> reject the candidate; the next candidate enters section 2 fresh; record a `rejection` learning; that candidate's resource verification is recorded failed;
- **resource failure (curated/trusted)** -> block the affected version/use and report the contradiction; record a `version-drift` or `integration-gotcha` learning; catalog membership, canonical identity, and trust stay untouched;
- **understanding failure** -> correct the model from source/docs; re-run the resource proof the misunderstanding invalidated; record an `integration-gotcha` learning;
- **skill instruction failure** -> patch only the instructions responsible; re-run the failed check plus every previously passing applicable check; record a `repair-outcome` learning; the patch voids prior behavioral passes until those reruns complete;
- **environment failure** -> fix or document the prerequisite and re-run the blocked check, or record it unavailable if unfixable; record an `environment-blocker` learning; never distort the skill around a broken environment;
- **test failure** -> repair the invalid test, re-run it, and demonstrate the repaired test can still fail; record a `repair-outcome` learning; results produced by the invalid test are void.

Budget: at most **three repair cycles per distinct failing check**; the fourth failure of the same check stops the loop. Do not endlessly polish. Stop with success only when the reliability threshold in `references/testing-protocol.md` is met. Stop and escalate to the user when a check exhausts its budget, when patches oscillate (a fix reverting an earlier fix, or two checks alternately breaking), or when failures expose a fundamental mismatch rather than a fixable skill defect — then reject the untrusted candidate or block the curated use and surface the evidence instead of lowering the bar. Escalation states the failing checks, each attempt and its result, truthful current statuses, the learnings appended, and the user's options.

No repair activity upgrades any status implicitly. Resource verification and `skill_validation` each move only when their own gate actually re-executes and passes; a patch moves affected behavioral status down until reruns restore it.

## 8. Record trust and verification separately

Do not overload one status word with two meanings. Track **trust** (who/what authorizes normal use) separately from **verification** (what has actually been proven).

### Trust

For resources this workflow actively acquires, trust normally comes from:

- **curated** — valid explicit user/project catalog membership. Trust is immediate for the canonical identity named by the entry and does not require this workflow to re-prove the library;
- **verified-acquisition** — a previously untrusted discovered resource completed all applicable resource-proof and generated-skill behavioral gates required for normal adoption.

An already-installed/project-approved dependency may also arrive with inherited `project` or `explicit-user` trust. Preserve that declared basis rather than pretending this workflow established it. A resource with no declared trust basis remains untrusted candidate/cache research.

### Verification

Resource verification describes proof of the selected upstream resource identity/version only. Track generated-skill structural and behavioral validation separately under `skill_validation`; neither layer upgrades the other automatically.

Record resource verification as one of:

- **verified** — all applicable resource/runtime proof required for the intended use actually executed and passed;
- **unverified** — verification has not yet been established; checks may be unattempted or incomplete, but no decisive failure or known execution blocker has been recorded;
- **unavailable** — a material required execution check cannot be performed in the available environment;
- **failed** — relevant executable proof failed or current evidence directly contradicts the intended use.

Thus a resource can legitimately be **trusted + unverified** when it is curated. Never rewrite that as "verified." A newly discovered resource remains **untrusted + unverified** while proof is incomplete, with partial evidence recorded in `resource_proof`, until it completes enough gates for verified-acquisition trust.

### Candidate/cache

Keep discovered non-trusted research here when it may be useful later but has not earned verified-acquisition trust. Do not let candidate state masquerade as trusted guidance.

### Rejected / blocked

For untrusted discoveries, record enough information to avoid wasteful rediscovery:

- resource and source URL;
- validation date;
- rejected version/state;
- concise reason;
- evidence that would justify reconsideration.

For curated resources, do not silently delete, de-trust, or retarget the entry when a test fails. Record the affected version/use as failed or blocked, warn the user/project, and leave catalog membership/canonical identity unchanged until explicitly modified.

Use `templates/resource-record.yaml` for a portable evidence record when the environment has no registry format of its own. Carry the curated `slug`, `canonical_url`, and `package_id` into that record so evidence cannot drift onto a same-named resource. A record whose trust basis is `verified-acquisition` requires executed/passing applicable resource proof, generated-skill structural validation, executed/passing independent generated-skill behavioral validation, provenance, and no material unavailable claims. A record whose trust basis is `curated` does not require those gates to be trusted, but every verification field must still be truthful. Whenever this workflow writes or updates a portable resource record, run `scripts/validate_resource_record.py <resource-record.yaml>` when Python is available. Its PASS establishes only structural/state consistency; it does not prove the recorded evidence is true.

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
- important limitations/version pin;
- learning entries appended to the external store during the run, when any;
- rejected alternatives only when their rejection materially explains the decision.

Do not bundle user/project curated registry data, research transcripts, caches, temporary test fixtures, or unrelated artifacts into a generated runtime skill package. Keep only the instructions, references, templates, and helper scripts the skill actually needs.

If no usable curated resource exists and no discovered candidate clears the required acquisition gates, say so and implement locally or return the unresolved need instead of manufacturing a recommendation.
