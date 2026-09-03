---
name: direction-selection
description: Compare and select among genuine direction choices when materially different directions compete, framing or candidate-space adequacy is uncertain, comparative justification is weak, or material new evidence challenges a direction. Do not use for routine, obvious, or cheaply reversible implementation choices.
---

# Direction Selection

Use this skill as a conditional direction-comparison subprotocol. It decides whether a live direction problem exists, compares directions when one does, and returns a local decision plus commitment-scoped support status. It does not control generic project uncertainty, planning, implementation, persistence, verification, or correction propagation.

Optimal means best supported by the current goal, hard constraints, applicable evidence, ordered criteria, and uncertainty. Claim only the degree of optimality the evidence warrants.

## Applicability router

Route every invocation before comparison. Classify uncertainty only far enough to determine whether plausible outcomes could materially alter the direction, framing, candidate ranking, or justified search space. Produce exactly one observable **Applicability result**:

- `exit` — no live direction problem exists and no handoff is needed;
- `handoff` — comparison does not yet own control because the caller/controller or user must resolve a directly routable unknown;
- `lightweight` — a meaningful but bounded direction choice is live; or
- `full` — a consequential, materially competitive, framing-sensitive, search-space-sensitive, or weakly justified direction problem is live.

Do not activate or continue this skill merely because a task contains uncertainty. Routine naming, small local refactors, obvious DataModel placement under established conventions, implementation details with one clearly supported option, and cheaply reversible choices should normally `exit`. Factual, behavioral, repository/project-state, or user-owned uncertainty is not a direction problem when its plausible outcomes do not affect direction, framing, ranking, or justified search space.

When one clear direction exists and the only unresolved issue is a directly inspectable factual or behavioral unknown, resolve that unknown through its fitting evidence route before generating candidates. With a surrounding controller, return `handoff`, explain why comparison does not currently own control, and give at most a fitting evidence-route hint. Do not start generic research, benchmarking, persistence, planning, or verification loops merely because an unknown is consequential.

In standalone use, when the applicability distinction itself depends on one resolvable fact, use only the minimum bounded applicability evidence probe allowed by [DISCOVERY.md](references/DISCOVERY.md). Return to this router afterward; exit when the direction problem disappears. An applicability probe is not automatically a terminal `Discovery Decision`.

### Authority and preference semantics

- An explicit user mandate such as “Use Rojo; do not evaluate alternatives” is a hard boundary unless it is impossible, unsafe, contradictory, or the user explicitly requests evaluation.
- A suggestion such as “I think A is best; choose what is actually best” is a candidate or input, not privileged evidence.
- Ask a focused question when a consequential preference or acceptable tradeoff is user-owned and cheaply resolvable; do not infer or empirically test the preference.
- Delegated authority permits choosing, but it is not evidence that the selected tradeoff reflects the user's preference.

After `lightweight` or `full`, comparison owns the direction decision. After a direction outcome, terminal discovery handoff, or adaptive commitment, return the local record and gate status to the caller/controller. The caller/controller retains broader execution and lifecycle authority.

## Support threshold

A direction is **sufficiently supported for the governed commitment** when:

- it satisfies every known hard constraint and invariant;
- its decisive comparative claims have applicable evidence proportionate to the stakes;
- no unresolved material assumption has plausible outcomes that could overturn it at this commitment level; and
- if a credible surviving alternative exists, it has no better-supported case under the ordered criteria.

Scale support to the commitment. Higher-impact or harder-to-reverse commitments require stronger evidence. Seek enough support to decide, not certainty, and spend no more on direction selection than the decision warrants. Do not manufacture an alternative to satisfy the threshold.

## Authoritative direction-space triggers

The following is the single authoritative trigger set for `full` entry and conditional candidate-space work:

1. materially different directions remain genuinely competitive;
2. framing ambiguity can materially change the solution space;
3. a credible omitted-direction or shared-premise signal exists;
4. a consequential direction has weak comparative justification;
5. the user asks for the best or ideal direction and the inherited search space is not adequately justified; or
6. material new evidence challenges the current direction.

Generic consequential uncertainty alone is not a trigger. Record the exact trigger or triggers that caused `full` entry and carry them forward only while they affect candidate-space obligations, comparison, or stopping conditions.

Multiple known competitive directions alone do not require searching for another class. Triggers 3–5 require bounded candidate-space examination before `PASS`. For trigger 6, first determine whether the new evidence changes ranking only or also creates a credible candidate-space signal.

## Choose the proportional mode

Use this routing order:

1. No live direction problem: `exit`, or `handoff` to the fitting owner/evidence route.
2. Meaningful but bounded direction choice: `lightweight`.
3. Materially competitive, framing-sensitive, search-space-sensitive, weakly justified consequential, or materially evidence-challenged direction problem: `full`.

For `lightweight`, read [LIGHTWEIGHT.md](references/LIGHTWEIGHT.md) completely, follow it, and return its local record and gate status.

For `full`, record the invocation trigger(s), read [FULL.md](references/FULL.md) completely, and follow it. At any comparison stage, if a specific decision-sensitive unknown blocks that stage and no direction meets the Support threshold, read [DISCOVERY.md](references/DISCOVERY.md) completely and apply its Discovery Entry Test. The interrupted comparison stage remains the owner; bounded discovery returns to that exact stage rather than restarting applicability or the protocol.

When changing this skill, another decision protocol, or a protocol that invokes it, read [SELF-APPLICATION.md](references/SELF-APPLICATION.md) completely before applying the full protocol.

### Direction Gate scope

Production commitment that materially depends on the direction currently being selected requires `Direction Gate: PASS` for that commitment. The gate is a local support result returned to the caller/controller, not project-wide execution authority.

When otherwise authorized and when they do not materially prejudice the unresolved choice, unrelated work, already-supported work, safely reversible increments, repository inspection, evidence-gathering tests or benchmarks, prototypes, and disposable experiments may proceed. Pre-gate work must not silently become production across the governed consequential commitment boundary or create de facto lock-in that biases or predetermines the unresolved direction.

**Future-horizon reversibility:** assess reversibility at the likely future correction point, after the next probable dependent work has accumulated—not only at the present moment. Consider dependent implementation, schema/data migration, compatibility, ecosystem or vendor lock-in, deployment, user/external commitments, and accumulated downstream assumptions when material. Apply this rule to mode choice, evidence work, tie-breaking, gate scope, and adaptive commitments.

## Output contracts

For a conventional passing direction, use:

### Direction Decision

- **Mode:** lightweight | full
- **Chosen direction:** one sentence
- **Why it wins:** decisive reasons tied to the ordered criteria
- **Alternatives rejected:** each serious candidate and its decisive losing tradeoff, or `none` when no credible alternative existed and no candidate-space trigger required searching
- **Assumptions / uncertainty:** material items only
- **Reopen if:** concrete evidence or conditions that invalidate the choice
- **Direction Gate:** PASS

Use a `Discovery Decision` only for a genuine terminal stop or handoff when required evidence cannot be obtained within the bounded run:

### Discovery Decision

- **Mode:** lightweight | full
- **Unresolved decision:** what cannot yet be selected
- **Material uncertainty:** the fact or assumption capable of changing the winner
- **Next discovery step:** the smallest proportionate discriminating action, or none when further discovery lacks value
- **Decision effect:** how plausible outcomes change the model, candidate set, comparison, or gate
- **Stop / re-evaluate when:** the evidence needed to resume the owning comparison stage
- **Direction Gate:** NOT PASSED

A bounded applicability probe that returns normally to the router does not emit this terminal record.

### Adaptive Direction

Use this outcome only when the commitment is consequential, worthwhile evidence has been gathered, important uncertainty remains structurally unstable rather than under-researched, a nominal winner would create false certainty, indefinite delay is not justified, and a bounded robust or adaptive commitment can itself be justified.

- **Mode:** adaptive
- **Current bounded commitment:** what this direction decision and gate support now
- **Why this bounded commitment is supportable now:** decisive support across the plausible conditions it must survive
- **Why a nominal winner is not justified:** concise statement
- **Structurally unstable uncertainty:** material unknowns or futures
- **Optionality preserved:** what remains open or migration-capable
- **Exposure limit:** cap on cost, scope, migration, users, data, or time
- **Adaptation trigger:** observable condition
- **Reopen / branch:** exact decision or direction to revisit
- **Direction Gate:** PASS | NOT PASSED

Adaptive `PASS` is permitted only when the current bounded commitment satisfies the Support threshold until its exposure limit or adaptation trigger. Residual uncertainty may affect later branches. If a plausible outcome could invalidate the bounded commitment before safe redirection, use `NOT PASSED`. Adaptive handling never establishes a nominal winner or grants project-wide authorization.

Keep records concise and proportional. They are local skill outputs. The caller/controller decides whether a load-bearing record should persist in project state because stale reconstruction or correction propagation would matter; this skill does not require global persistence for every record.

Return the record and gate status to the caller/controller. Continue only into work separately authorized by the user's request.

## Reopening a direction

Reopen only when implementation, tests, benchmarks, changed requirements, or verified facts materially weaken a load-bearing assumption or satisfy a concrete `Reopen if` condition. Identify the exact invalidated premise, mark the direction reopened rather than silently overwriting it, and rerun only affected direction-selection work.

When a broader controller exists, hand back the reopened direction, invalidated premise, triggering evidence, and any already-known materially affected downstream commitments or artifacts in the current context. Do not perform a new project-wide impact search, build a dependency graph, or duplicate correction-propagation machinery; implicit or transitive impact discovery belongs to the controller. In standalone use, state that known affected downstream commitments require reconsideration without prescribing a project-wide methodology. Unaffected branches remain untouched.
