# Resource state and lifecycle policy

Apply this reference whenever the workflow records trust or verification, writes portable records or learnings, changes host adoption state, or reports a final acquisition result.

## Record trust and verification separately

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

Thus a resource can legitimately be **trusted + unverified** through a policy trust basis. Never rewrite that as `verified`. An untrusted resource remains **untrusted + unverified** while proof is incomplete, with partial evidence recorded in `resource_proof`, until it completes enough gates for verified-acquisition trust.

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

Use the mandatory schema-version 2 `../templates/resource-record.yaml` for a portable evidence record when the environment has no registry format of its own. The existing record model separates selection provenance from trust: use `discovery_origin: other` for a direct user target and state its exact role/scope in `selection_reason`; use `project` only for a capability found through project reconnaissance. Neither value determines `trust.basis`. Carry the established `slug`, `canonical_url`, `package_id`, and material selector/version into the record so evidence cannot drift onto a same-named or differently selected resource. Record installed/parent reconciliation separately from upstream verification, and record artifact state separately from each host adoption. An empty `host_adoptions` list means artifact only; `operational` requires every host-applicable evidence facet plus explicit activation. Legacy children and records fail the current contract and enter `repair/reconcile`; never synthesize missing lifecycle evidence.

A record whose trust basis is `verified-acquisition` requires executed/passing applicable resource proof, generated-skill structural validation, executed/passing independent generated-skill behavioral validation, provenance, and no material unavailable claims. A record whose trust basis is `curated` does not require those gates to be trusted, but every verification field must still be truthful. Whenever this workflow writes or updates a portable resource record, run `scripts/validate_resource_record.py <resource-record.yaml>` when Python is available. Its PASS establishes only structural/state consistency; it does not prove the recorded evidence is true. Record discovery, reconciliation, host evidence, authorization, and state transitions per [operational-lifecycle.md](operational-lifecycle.md).

## Self-growth boundaries

Durable learning has exactly two destinations with different mutation rules.

**External learnings store** — user/project-owned observation data outside this package, governed by [learnings-store.md](learnings-store.md). Appending a new entry (integration gotchas, failed query patterns, version drift notes, environment blockers, rejection reasons, repair outcomes) is autonomous and needs no permission. Editing, retargeting, or deleting any existing entry requires explicit user permission in chat, every time; there is no standing allowlist. This package ships only the store contract and `../templates/learning-entry.yaml`; never bundle accumulated entries into the package or into a generated skill.

**This skill package** (`SKILL.md`, `references/`, `scripts/`, `templates/`) — never edited autonomously. When evidence shows this package's own guidance is wrong or incomplete: stop the affected step, state the evidence, propose the exact diff (file, current text, replacement), and wait for an explicit yes from the user in chat. No silent patching; each yes authorizes only the single diff it answered.

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

Report only applicable fields:

- selected resource and why it fits; compare alternatives only when comparison was required or explicitly requested;
- verification performed and result, or explicitly `unverified`/`unavailable`;
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
