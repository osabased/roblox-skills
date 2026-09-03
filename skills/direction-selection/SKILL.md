---
name: direction-selection
description: Choose or reassess consequential directions when alternatives compete, the framing or candidate space is uncertain, or evidence challenges the current choice.
---

# Direction Selection

Use this skill as a conditional direction-comparison subprotocol. It decides whether a live direction problem exists, compares directions when one does, and returns a local decision plus commitment-scoped support status. It does not control generic project uncertainty, planning, implementation, persistence, verification, or correction propagation.

Optimal means best supported by the current goal, hard constraints, applicable evidence, ordered criteria, and uncertainty. Claim only the degree of optimality the evidence warrants.

## Applicability router

Route every invocation before comparison. Classify uncertainty only far enough to determine whether plausible outcomes could materially alter the direction, framing, candidate ranking, or justified candidate space. Produce exactly one observable **Applicability Result** or enter one comparison mode:

- `exit` — no live direction problem exists and no handoff is needed;
- `handoff` — comparison does not own a directly routable fact, behavior, project-state unknown, constraint, or user preference that must be resolved first;
- `lightweight` — a meaningful but bounded choice is live, and the framing, criteria, and candidate space are already adequate; or
- `full` — an authoritative full-mode trigger is live.

Do not activate or continue this skill merely because a task contains uncertainty. Routine naming, small local refactors, obvious DataModel placement under established conventions, implementation details with one clearly supported option, and cheaply reversible choices should normally `exit`. Factual, behavioral, repository/project-state, or user-owned uncertainty is not a direction problem when its plausible outcomes do not affect direction, framing, ranking, or candidate-space adequacy.

When one clear direction exists and the only unresolved issue is a directly inspectable factual or behavioral unknown, resolve that unknown through its fitting evidence route before generating candidates. With a surrounding controller, return `handoff`, explain why comparison does not own control, and give at most a fitting evidence-route hint. Do not start generic research, benchmarking, persistence, planning, or verification loops merely because an unknown is consequential.

In standalone use, when applicability itself depends on one resolvable fact, use only the minimum bounded applicability evidence probe allowed by [DISCOVERY.md](references/DISCOVERY.md). Return to this router afterward. If the probe cannot resolve the fact within the bounded run, return `handoff` to the fitting owner or user; do not emit a comparison outcome before a comparison mode exists.

### Authority and preference semantics

- An explicit user mandate such as “Use Rojo; do not evaluate alternatives” is a hard boundary unless it is impossible, unsafe, contradictory, or the user explicitly requests evaluation.
- A suggestion such as “I think A is best; choose what is actually best” is a candidate or input, not privileged evidence.
- Ask a focused question when a consequential preference or acceptable tradeoff is user-owned and cheaply resolvable; do not infer or empirically test the preference.
- Delegated authority permits choosing, but it is not evidence that the selected tradeoff reflects the user's preference.

After `lightweight` or `full`, comparison owns the local direction decision. After a direction outcome, blocker, or adaptive commitment, return the record and gate status to the caller/controller. The caller/controller retains broader execution and lifecycle authority.

## Continuation invariant

Across discovery calls, mode escalation, caller handoffs, leader changes, and reopened directions, preserve all still-applicable boundaries, constraints, authorities, evidence and provenance, assumptions, candidates, and completed results. Transfer control to the receiving owner at the earliest affected stage and repeat only work invalidated by the trigger, new evidence, or changed premise.

Caller-provided diagnosis and evidence remain established inputs when applicable, not privileged rankings or conclusions. Re-check them only when a conflict, scope mismatch, applicability problem, or decision-sensitive uncertainty makes that necessary.

## Support threshold

A direction is **sufficiently supported for the governed commitment** when:

- it satisfies every known hard constraint and invariant;
- its decisive comparative claims have applicable evidence proportionate to the stakes;
- no unresolved material assumption has plausible outcomes that could overturn it at this commitment level;
- if a credible surviving alternative exists, it has no better-supported case under the ordered criteria; and
- any material tie is resolved by an applicable ordered tie-breaker; otherwise no nominal winner is claimed.

Scale support to the commitment. Higher-impact or harder-to-reverse commitments require stronger evidence. Seek enough support to decide, not certainty, and spend no more on direction selection than the decision warrants. Do not manufacture an alternative to satisfy the threshold.

## Deciding-evidence applicability

Evidence may carry a decisive comparative claim only when it represents the property actually at risk and applies to the relevant version or interface, environment, workload or population, operating conditions, and material integration effects. Evidence that misses a material part of the claim may remain informative, but it is non-deciding.

## Authoritative full-mode triggers

The following is the single authoritative trigger set for `full` entry and required candidate-space work:

1. materially different directions remain genuinely competitive for a consequential or hard-to-reverse commitment;
2. framing ambiguity can materially change the solution space;
3. a credible omitted-direction or shared-premise signal exists;
4. a consequential direction has weak comparative justification;
5. the user asks for the best or ideal direction and the inherited candidate space is not adequately justified; or
6. material new evidence challenges the current direction.

Generic consequential uncertainty alone is not a trigger. Record the exact trigger or triggers that caused `full` entry and carry them forward only while they affect candidate-space obligations, comparison, or stopping conditions.

Multiple known competitive directions alone do not require searching for another class. Triggers 3–5 require one bounded candidate-space examination before `PASS`. For trigger 6, first determine whether the evidence changes ranking only, changes framing, or creates a credible candidate-space signal.

## Choose the proportional mode

Use this routing order:

1. No live direction problem: `exit`, or `handoff` to the fitting owner/evidence route.
2. Meaningful bounded choice with adequate framing, criteria, and candidate space: `lightweight`.
3. Any authoritative full-mode trigger: `full`.

For `lightweight`, read [LIGHTWEIGHT.md](references/LIGHTWEIGHT.md) completely, follow it, and return its local record and gate status.

For `full`, record the invocation trigger(s), read [FULL.md](references/FULL.md) completely, and follow it. At any comparison stage, if a specific decision-sensitive unknown blocks that stage and no direction meets the Support threshold, read [DISCOVERY.md](references/DISCOVERY.md) completely and apply its Discovery Entry Test. Discovery returns to the exact owning stage rather than restarting applicability or the protocol.

When changing this skill, another decision protocol, or a protocol that invokes it, read [SELF-APPLICATION.md](references/SELF-APPLICATION.md) completely before applying the full protocol.

### Direction Gate scope

Production commitment that materially depends on the direction currently being selected requires `Direction Gate: PASS` for that commitment. The gate is a local support result returned to the caller/controller, not project-wide execution authority.

When otherwise authorized and when they do not materially prejudice the unresolved choice, unrelated work, already-supported work, safely reversible increments, repository inspection, evidence-gathering tests or benchmarks, prototypes, and disposable experiments may proceed. Pre-gate work must not silently become production across the governed consequential commitment boundary or create de facto lock-in that biases or predetermines the unresolved direction.

**Future-horizon reversibility:** assess reversibility at the likely future correction point, after the next probable dependent work has accumulated—not only at the present moment. Consider dependent implementation, schema/data migration, compatibility, ecosystem or vendor lock-in, deployment, user/external commitments, and accumulated downstream assumptions when material. Apply this rule to mode choice, evidence work, tie-breaking, gate scope, and adaptive commitments.

## Output contracts

Use this result when comparison never becomes the owner:

### Applicability Result

- **Result:** exit | handoff
- **Reason:** why no comparison currently owns the decision
- **Owner / next route:** fitting owner or action, or `none`

For a conventional passing direction, use:

### Direction Decision

- **Mode:** lightweight | full
- **Governed commitment:** exact direction-dependent commitment supported by this gate
- **Chosen direction:** one sentence
- **Why it wins:** decisive reasons tied to the ordered criteria
- **Alternatives / candidate-space result:** serious candidates and decisive losing tradeoffs; `none — no search required`; or `none — required bounded search found no credible alternative`
- **Assumptions / uncertainty:** material items only
- **Reopen if:** concrete evidence or conditions that invalidate the choice
- **Direction Gate:** PASS

Use this result only after a comparison mode exists and the gate cannot pass:

### Direction Blocker

- **Mode:** lightweight | full
- **Governed commitment:** what cannot yet proceed
- **Unresolved decision:** the choice still open
- **Blocking condition:** exact evidence, preference, constraint, tie, or support failure
- **Owner / next step:** fitting owner, smallest proportionate action, or `none` when no justified action remains
- **Decision effect:** how plausible resolution outcomes could change the result
- **Resume when:** observable condition sufficient to resume comparison, or `none` when no justified condition is known
- **Direction Gate:** NOT PASSED

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

Reopen only when implementation, tests, benchmarks, changed requirements, or verified facts materially weaken a load-bearing assumption or satisfy a concrete `Reopen if` condition. Identify the exact invalidated premise, mark the direction reopened rather than silently overwriting it, and apply the Continuation invariant.

When a broader controller exists, hand back the reopened direction, invalidated premise, triggering evidence, and any already-known materially affected downstream commitments or artifacts in the current context. Do not perform a new project-wide impact search, build a dependency graph, or duplicate correction-propagation machinery; implicit or transitive impact discovery belongs to the controller. In standalone use, state that known affected downstream commitments require reconsideration without prescribing a project-wide methodology. Unaffected branches remain untouched.
