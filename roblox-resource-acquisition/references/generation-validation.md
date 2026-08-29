# Generated resource-skill workflow

Use this reference only when reusable child guidance is in scope, or when an existing generated child must be refreshed and revalidated.

## Generate the resource skill when adoption/reuse is in scope

If the user asked only to evaluate, compare, or inspect a resource and the current task does not require adopting it as reusable agent guidance, stop after the requested evaluation/verification result instead of creating a skill as extra scope.

When reusable child generation is in scope, an untrusted resource — whether discovered, already project-present, or directly targeted — may receive a dedicated reusable skill only after the required resource verification passes. A resource trusted through `curated`, `project`, or `explicit-user` may receive one after current-source understanding is sufficient even when runtime verification is unavailable, because its trust came from policy rather than this workflow. In either case, use [resource-skill-template.md](../templates/resource-skill-template.md) and [resource-skill-contract.md](resource-skill-contract.md).

Use this same generation path for an adequate existing dependency or an explicitly targeted resource; do not create a parallel child mechanism. Generate only when reusable guidance is in scope and justified. Child creation or validation does not imply that this workflow installed the upstream resource, grant upstream trust, upgrade upstream verification, change selection provenance, or make either the resource or child operational. Host adoption remains a separate authorized gate.

The generated skill must be operational guidance, not a copy of the DevForum post or README. It should teach an agent how to decide, install, use, verify, and troubleshoot the resource with minimal irrelevant context. Include the closest credible alternative or Roblox built-in when relevant; if none is meaningful, say why. Always retain a `Security notes` section: document applicable resource-specific trust boundaries, or explicitly state when there are no special ones beyond normal Roblox server-authoritative expectations.

Every generated child must include the operational reconciliation contract from [resource-skill-contract.md](resource-skill-contract.md): stable resource identity, a `required` or justified `not-applicable` reconciliation policy, a resource-specific installed-state check, parent-state reconciliation, and a defect/mismatch handoff to this skill's `repair/reconcile` mode. Use [operational-lifecycle.md](operational-lifecycle.md) for the shared lifecycle semantics; do not copy its host-independent rules into multiple references.

Pin claims to the exact source version/release/commit reviewed when possible. If no stable identifier exists, record the exact review date and source state instead of pretending it is version-pinned. In the generated skill, record resource verification separately as `verified`, `unverified`, or `unavailable`; source review is not runtime proof.

Do not treat trust in the upstream resource as proof that the generated instructions are correct. A generated skill must carry its own validation/verification state and must not claim behavioral validation merely because its resource was curated.

## Validate the generated skill independently

Treat the generated skill as a second product with its own failure modes. Use [testing-protocol.md](testing-protocol.md).

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

When the child is associated with a portable resource record, update the record's `generated_skill` and current structural result, then run `scripts/validate_resource_bundle.py <resource-record.yaml> <generated-skill-directory>`. This coupled gate verifies that the independently valid artifacts actually describe the same resource slug, canonical/package identity, reviewed source state, and resource-verification status. It is **not** run for ordinary resource acquisition when no child exists. Rerun this gate whenever a refresh or repair changes child provenance, resource identity, reviewed source state, or the record's generated-skill linkage.

Whenever a child is added, refreshed, repaired, or adopted, run `scripts/validate_skill_catalog.py <generated-skill-directory-or-root> [...]` against the target generated-child set. Also inspect host-visible skill activation metadata; pass every plausible non-generated routing competitor as `--routing-competitor <path>`. Competitors contribute routing metadata/fingerprint state but are not forced through the generated resource-skill contract. Duplicate generated identities/descriptions fail. Reported activation-overlap clusters require the catalog behavioral tests in [testing-protocol.md](testing-protocol.md); static PASS never proves host routing.

### Script dependencies

All scripts in `scripts/` require Python 3.10+ and PyYAML (`pip install -r requirements.txt`); everything else is standard library. PyYAML is required rather than optional so that every environment parses registry, learnings, and record files identically — a validation verdict, and therefore a trust decision, must never depend on which parser happened to be installed. When PyYAML is missing the scripts exit with code 2 and an install hint (exit 1 remains validation failure, 0 pass). No other packages, databases, or network access are needed.
