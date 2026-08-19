---
name: direction-selection
description: Compare and select among genuine direction choices when materially different directions compete, framing or candidate-space adequacy is uncertain, comparative justification is weak, or material new evidence challenges a direction.
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

Factual, behavioral, repository/project-state, or user-owned uncertainty is not a direction problem when its plausible outcomes do not affect direction, framing, ranking, or justified search space. When one clear direction exists and the only unresolved issue is a directly inspectable factual or behavioral unknown, resolve that unknown through its fitting evidence route before generating candidates; direction selection becomes live only if the result actually creates a direction, framing, ranking, or search-space problem. With a surrounding controller, return `handoff`, explain why comparison does not currently own control, and give at most a fitting evidence-route hint. Do not start generic research, benchmarking, persistence, planning, or verification loops merely because an unknown is consequential.

In standalone use, when the distinction itself depends on one resolvable fact, use only the minimum bounded applicability evidence probe allowed by [DISCOVERY.md](DISCOVERY.md). Return to this router afterward; exit when the direction problem disappears. An applicability probe is not automatically a terminal `Discovery Decision`.

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

The following is the single authoritative trigger set for full-mode entry and conditional candidate-space work:

1. materially different directions remain genuinely competitive;
2. framing ambiguity can materially change the solution space;
3. a credible omitted-direction or shared-premise signal exists;
4. a consequential direction has weak comparative justification;
5. the user asks for the best or ideal direction and the inherited search space is not adequately justified; or
6. material new evidence challenges the current direction.

Generic consequential uncertainty alone is not a trigger. Record the exact trigger or triggers that caused full entry. Carry them forward only while they affect candidate-space obligations, comparison, or stopping conditions.

Multiple known competitive directions alone do not require searching for another class. Triggers 3–5 require bounded candidate-space examination before `PASS`. For trigger 6, first determine whether the new evidence changes ranking only or also creates a credible candidate-space signal.

## Choose the proportional mode

Use this routing order:

1. No live direction problem: `exit`, or `handoff` to the fitting owner/evidence route.
2. Meaningful but bounded direction choice: `lightweight`.
3. Materially competitive, framing-sensitive, search-space-sensitive, weakly justified consequential, or materially evidence-challenged direction problem: `full`.

For `lightweight`, read [LIGHTWEIGHT.md](LIGHTWEIGHT.md) completely, follow it, and return its local record and gate status.

For `full`, record the invocation trigger(s) and follow the protocol below. At any comparison stage, if a specific decision-sensitive unknown blocks that stage and no direction meets the Support threshold, read [DISCOVERY.md](DISCOVERY.md) completely and apply its Discovery Entry Test. The interrupted comparison stage remains the owner; bounded discovery returns to that exact stage rather than restarting applicability or the protocol.

When changing this skill, another decision protocol, or a protocol that invokes it, read [SELF-APPLICATION.md](SELF-APPLICATION.md) completely before applying the full protocol.

### Direction Gate scope

Production commitment that materially depends on the direction currently being selected requires `Direction Gate: PASS` for that commitment. The gate is a local support result returned to the caller/controller, not project-wide execution authority.

When otherwise authorized and when they do not materially prejudice the unresolved choice, unrelated work, already-supported work, safely reversible increments, repository inspection, evidence-gathering tests or benchmarks, prototypes, and disposable experiments may proceed. Pre-gate work must not silently become production across the governed consequential commitment boundary or create de facto lock-in that biases or predetermines the unresolved direction.

**Future-horizon reversibility:** assess reversibility at the likely future correction point, after the next probable dependent work has accumulated—not only at the present moment. Consider dependent implementation, schema/data migration, compatibility, ecosystem or vendor lock-in, deployment, user/external commitments, and accumulated downstream assumptions when material. Apply this rule to mode choice, evidence work, tie-breaking, gate scope, and adaptive commitments.

## Full protocol

### 1. Build and challenge the problem model

Record:

- **Invocation trigger(s):** exact item or items from the authoritative trigger set.
- **Decision boundary:** the load-bearing choice required now, the commitment it governs, and later choices that can remain open. Separate independent choices, keep materially coupled choices together, and resolve upstream choices first.
- **Framing:** whether the stated problem is the outcome, a symptom, or a requested mechanism. Consider alternate framing only when a credible framing could materially change the solution space; there is no numeric target.
- **Goal:** the outcome being optimized and the observable success condition. Distinguish the real outcome from convenient proxies.
- **Hard constraints and invariants:** non-negotiable requirements, interfaces, compatibility guarantees, safety boundaries, budgets, and environmental limits.
- **Ordered criteria:** hard constraints, primary success criteria, secondary tradeoffs, then tie-breakers such as simplicity, future-horizon reversibility, option value, implementation cost, or consistency.
- **Unknowns:** known facts, reasonable assumptions, unresolved material uncertainty, and preferences only the user can decide.

Apply the authority and preference semantics from the router. Verify decision-sensitive, unstable facts from authoritative sources when the task authorizes it.

**Complete when:** the trigger, boundary, governed commitment, goal, hard constraints, ordered criteria, and every known material unknown are recorded; any irreducible user preference is isolated.

### 2. Establish the credible candidate set

Start with known materially distinct credible candidates. There is no required candidate count. Include the current design, doing less, or preserving the status quo only when credible. Before elaborating a favorite:

1. State every plausible direction found so far in one neutral sentence.
2. Retain only materially independent candidates that could plausibly win under the ordered criteria.
3. Describe every serious candidate at comparable, decision-relevant depth.

Perform bounded direction-space exploration when entry was caused by weak comparative justification, an inherited or unjustified search space, or a shared-premise or omitted-direction signal. If entry was caused only by known materially competitive directions, compare them without automatically seeking another class. If new evidence challenged the incumbent, broaden only when it creates a credible candidate-space signal. An imaginable candidate is not credible evidence that the space is inadequate.

Use an available and authorized independent second look for high-impact choices only when its expected value justifies the cost. Ask neutrally and treat the result as evidence, not a vote.

**Complete when:** known serious candidates are neutrally and comparably stated, and any candidate-space examination required by the invocation trigger has been bounded and completed.

### 3. Gather discriminating, applicable evidence

Investigate facts that can change the comparison. Prefer actual repository constraints, tests and observed behavior, authoritative documentation, specifications, representative benchmarks, small disposable experiments, migration and operational constraints, and known failure modes.

For each investigation, name the uncertainty it can reduce and how a plausible result could change the decision. Stop when no plausible result can affect the choice. Apply the same evidentiary standard to every serious candidate.

Before any evidence carries a deciding comparative claim, verify that its scope supports that claim:

- For benchmarks, prototypes, tests, or observations: does it measure the property actually at risk; represent the relevant workload, environment, population, and operating conditions; include material integration effects; and would passing justify the conclusion being drawn?
- For research, documentation, reviews, or prior examples: is the version, environment or interface, operating context, and compared claim actually applicable?

Inapplicable evidence may remain informative, but it cannot carry the decisive comparative claim. A microbenchmark cannot settle a broader integration or end-to-end load claim without representative applicability.

Small or reversible actions must advance a commitment already supported at that level or reduce decision-relevant uncertainty. Keep exploratory work contained, observable, replaceable, and future-horizon reversible.

**Complete when:** every decisive comparative claim has applicable, proportionate evidence, or its remaining uncertainty is explicit and has been accepted or routed through the Discovery Entry Test.

### 4. Compare without anchoring

Evaluate in order:

1. **Constraint elimination:** remove candidates that violate a hard constraint unless that constraint is under review.
2. **Dominance:** prefer a candidate no worse on important criteria and materially better on at least one, unless uncertainty undermines the comparison.
3. **Tradeoffs:** compare primary criteria, secondary criteria, then tie-breakers.
4. **Uncertainty:** label advantages as evidence-backed, likely, or speculative.

Use measurements when available and ordered qualitative judgment otherwise. Apply symmetric standards. Count concrete future integration, transition, and migration costs without counting already-spent effort as support for an incumbent. Count future requirements in proportion to credible evidence. Treat simplicity as a tie-breaker and risk reducer, not a substitute for requirements. When higher-priority criteria remain close, prefer the direction easier to validate, reverse at the likely correction horizon, leave, or extend.

When applicable evidence establishes real dominance and no unresolved higher-priority uncertainty undermines it, stop needless lower-priority tradeoff comparison.

**Complete when:** every surviving candidate has been evaluated under the same ordered criteria and evidentiary standard, decisive tradeoffs are explicit, and the strongest surviving alternative is identified when one exists.

### 5. Search for an omitted direction when triggered

Run one serious bounded search only when the recorded trigger or material new evidence indicates that the candidate space may be inadequate, including when:

- current candidates share an unsupported premise;
- evidence repeatedly fits the current frame poorly;
- a supposed hard constraint may be an inherited implementation choice;
- the search space was inherited rather than justified;
- a consequential direction has weak comparative justification and no adequate candidate-space check occurred; or
- another materially different class has a credible signal that it could change the decision.

Skip this mechanism when the space is already justified and the live problem is comparison among known competitive directions. When triggered, test whether a simpler formulation, changed boundary, relaxed assumption, avoided decision, or coherent hybrid removes the current tradeoff. A hybrid qualifies only when it removes weaknesses rather than combining complexity.

Add any credible candidate found and repeat only affected evidence and comparison work. Repeat the search only after materially new information changes the solution space; a desire for another pass is not a trigger.

**Complete when:** the mechanism was skipped because no trigger exists, or a triggered bounded search has compared any credible result or found no missed class likely to change the decision.

### 6. Falsify the leader when triggered

Run falsification only when all three conditions substantially hold:

1. a proposition supporting the leader is load-bearing;
2. it remains meaningfully uncertain or confidence is suspiciously correlated; and
3. a realistic decision-changing challenge can be obtained at justified cost.

When triggered:

- target the strongest realistic failure scenario and load-bearing assumptions;
- surface hidden transition, maintenance, operational, security, and compatibility costs;
- identify the scale, workload, environment, or future requirement that would break the leader;
- state evidence that would make the strongest surviving alternative superior;
- apply symmetric challenge standards to the leader and strongest alternative; and
- rerun only affected work if the leader changes.

Skip falsification when its trigger is absent. Route a decision-sensitive material unknown through bounded discovery when appropriate.

**Complete when:** the mechanism was skipped because its trigger is absent, the leader survived a decision-changing challenge, a replacement completed affected revalidation, or the stage entered bounded discovery.

### 7. Run the zero-based diagnostic when bias risk is present

Run this diagnostic only when sunk implementation effort, incumbent attachment, migration history, legacy consistency pressure, exploratory lock-in, or prior-investment reasoning could bias the choice.

Ask:

> If no implementation work had been done and I were choosing from scratch with everything now known, would I still choose this direction?

Already-spent effort is not evidence for retaining the incumbent. Future migration, compatibility, schedule, risk, retraining, production obligations, and retained asset value are legitimate current factors. When the answer changes, update affected comparison work and apply any independently triggered challenge. Skip the diagnostic when no credible incumbent or sunk-cost bias risk exists.

**Complete when:** the mechanism was skipped because no bias trigger exists, or the leader remains stable under the diagnostic after affected work is updated.

### 8. Pass the Direction Gate

Set `Direction Gate: PASS` only when every applicable condition holds:

- the goal, success condition, decision boundary, framing, and governed commitment are clear enough to choose;
- hard constraints and invariants are identified;
- all credible candidates in scope were compared symmetrically;
- any triggered candidate-space search, falsification, or zero-based review was resolved enough;
- decisive evidence is applicable and proportionate;
- the selected direction meets the Support threshold;
- no known candidate clearly dominates it, and any credible strongest alternative has no better-supported case;
- residual uncertainty is acceptable at this commitment level and has a concrete reopen condition; and
- the governed commitment respects future-horizon reversibility and does not rely on pre-gate de facto lock-in.

Skipped mechanisms do not need to be “passed.” `PASS` reports support only for the governed direction-dependent commitment and does not authorize unrelated or project-wide work.

When the gate cannot pass, identify the exact failing condition. Route a resolvable, decision-sensitive unknown through bounded discovery. Ask only for a user-owned preference or external constraint. If further discovery lacks proportionate value, leave the direction explicitly unresolved unless the Adaptive Direction conditions below are met.

**Complete when:** every applicable condition supports `PASS`, or the blocker produces bounded discovery, a focused user question, an Adaptive Direction, or an explicit unresolved state with `NOT PASSED`.

### 9. Record and return the outcome

For a conventional passing direction, use:

#### Direction Decision

- **Mode:** lightweight | full
- **Chosen direction:** one sentence
- **Why it wins:** decisive reasons tied to the ordered criteria
- **Alternatives rejected:** each serious candidate and its decisive losing tradeoff, or `none` when no credible alternative existed and no candidate-space trigger required searching
- **Assumptions / uncertainty:** material items only
- **Reopen if:** concrete evidence or conditions that invalidate the choice
- **Direction Gate:** PASS

Use a `Discovery Decision` only for a genuine terminal stop or handoff when required evidence cannot be obtained within the bounded run:

#### Discovery Decision

- **Mode:** lightweight | full
- **Unresolved decision:** what cannot yet be selected
- **Material uncertainty:** the fact or assumption capable of changing the winner
- **Next discovery step:** the smallest proportionate discriminating action, or none when further discovery lacks value
- **Decision effect:** how plausible outcomes change the model, candidate set, comparison, or gate
- **Stop / re-evaluate when:** the evidence needed to resume the owning comparison stage
- **Direction Gate:** NOT PASSED

A bounded applicability probe that returns normally to the router does not emit this terminal record.

#### Adaptive Direction

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

