---
name: direction-selection
description: Select a best-supported direction before consequential planning or implementation. Use when the user asks to compare approaches, materially different directions remain competitive, the problem framing could change the solution, or new evidence challenges an existing direction.
---

# Direction Selection

Select the best-supported direction before detailed planning or production implementation. Treat the first plausible solution, the user's suggestion, and the existing design as candidates rather than defaults.

Optimal means best supported by the current goal, hard constraints, evidence, ordered criteria, and uncertainty. Claim only the degree of optimality the evidence warrants.

## Support threshold

A direction is **sufficiently supported for the commitment being authorized** when:

- it satisfies every known hard constraint and invariant;
- its decisive comparative claims have evidence proportionate to the stakes;
- no unresolved material assumption has plausible outcomes that could overturn it at this commitment level; and
- the strongest surviving alternative has no better-supported case under the ordered criteria.

Scale support to the commitment. Higher-impact or harder-to-reverse commitments require stronger evidence. Seek enough support to decide, not certainty, and spend no more on direction selection than the decision warrants.

## Choose the proportional mode

Exit this skill and execute normally when the task is mechanical, low-risk, readily reversible, and has one clearly dominant path.

Use the lightweight mode for a meaningful but bounded or readily reversible choice, or for a direction already supported enough to need only proportionate confirmation. When this applies, read [LIGHTWEIGHT.md](LIGHTWEIGHT.md) completely, follow it, and return with its record.

Use the full protocol when materially competitive approaches remain unresolved, framing ambiguity could cause significant rework, or a consequential commitment still rests on material uncertainty. Consequential commitments include architecture, public interfaces, persistent data, dependencies, security boundaries, performance characteristics, migration strategy, and substantial downstream work.

At any full-protocol stage, when a specific unresolved unknown prevents that stage from meeting its completion criterion and no direction meets the Support threshold, read [DISCOVERY.md](DISCOVERY.md) completely and apply the Discovery Entry Test. Return to the interrupted stage after the bounded discovery work.

When selecting changes to this skill, another decision protocol, or a protocol that invokes this skill, read [SELF-APPLICATION.md](SELF-APPLICATION.md) completely before applying the full protocol.

**Production implementation requires Direction Gate: PASS.** Repository inspection, documentation lookup, tests, benchmarks, and disposable experiments may precede the gate when they reduce decision-relevant uncertainty. Exploratory artifacts remain disposable until the gate passes.

## Full protocol

### 1. Build and challenge the problem model

Record:

- **Decision boundary:** the load-bearing choice required now, the commitment it authorizes, and later choices that can remain open. Separate choices that vary independently, keep materially coupled choices together, and resolve upstream choices first.
- **Framing:** whether the stated problem is the outcome, a symptom, or a requested mechanism. Generate one or two alternate framings only when they would materially change the solution space.
- **Goal:** the outcome being optimized and the observable success condition. Distinguish the real outcome from convenient proxies.
- **Hard constraints and invariants:** non-negotiable requirements, interfaces, compatibility guarantees, safety boundaries, budgets, and environmental limits.
- **Ordered criteria:** hard constraints, primary success criteria, secondary tradeoffs, then tie-breakers such as simplicity, reversibility, option value, implementation cost, or consistency.
- **Unknowns:** known facts, reasonable assumptions, unresolved material uncertainty, and preferences only the user can decide.

Treat explicit user technology or architecture mandates as hard boundaries unless they are impossible, unsafe, contradictory, or the user asks to evaluate them. Keep preferences as preferences. Verify decision-sensitive, unstable facts from authoritative sources.

**Complete when:** the boundary, authorized commitment, goal, hard constraints, ordered criteria, and every known material unknown are recorded; any irreducible user preference is isolated.

### 2. Generate a neutral candidate slate

Generate enough materially independent candidates to cover the credible solution space, usually two to five. Include the current design, doing less, or preserving the status quo when credible. Derive each candidate from the problem model rather than by modifying a favorite.

Before elaborating any candidate:

1. State every plausible direction found so far in one neutral sentence.
2. Seek at least one different solution class when one is credible.
3. Retain only candidates that could plausibly win under the ordered criteria.
4. Describe every serious candidate at comparable, decision-relevant depth.

Use an available and authorized independent second look for high-impact choices when its expected value justifies the cost. Ask for candidates or critique without priming the reviewer with the current favorite; treat the result as evidence, not a vote.

This checkpoint prevents first-solution anchoring, cosmetic alternatives, and straw alternatives.

**Complete when:** every materially distinct credible candidate is neutrally stated, could plausibly win, and has comparable decision-relevant detail.

### 3. Gather discriminating evidence

Investigate facts that can change the comparison. Prefer actual repository constraints, tests and observed behavior, authoritative documentation, specifications, representative benchmarks, small disposable experiments, migration and operational constraints, and known failure modes.

For each investigation, name the uncertainty it can reduce and how a plausible result could change the decision. Stop research theater when no plausible result can affect the choice. Apply the same evidentiary standard to every serious candidate.

Small or reversible actions must either advance a commitment already supported at that level or reduce decision-relevant uncertainty. Keep exploratory code contained, observable, and replaceable.

**Complete when:** every decisive comparative claim has proportionate evidence, or its remaining uncertainty is explicit and has been accepted or routed through the Discovery Entry Test.

### 4. Compare without anchoring

Evaluate in order:

1. **Constraint elimination:** remove candidates that violate a hard constraint unless that constraint is itself under review.
2. **Dominance:** prefer a candidate that is no worse on important criteria and materially better on at least one, unless uncertainty undermines the comparison.
3. **Tradeoffs:** compare primary criteria, then secondary criteria, then tie-breakers.
4. **Uncertainty:** label advantages as evidence-backed, likely, or speculative.

Use real measurements when available and ordered qualitative judgment otherwise. Equal standards prevent asymmetric skepticism and fake objectivity. Count concrete integration and migration costs without treating local consistency as inherently superior. Count future requirements in proportion to credible evidence. Treat simplicity as a tie-breaker and risk reducer, not a substitute for requirements.

When candidates remain close under the higher-priority criteria, prefer the direction that is easier to validate, reverse, leave, or extend.

**Complete when:** every surviving candidate has been evaluated under the same ordered criteria and evidentiary standard, decisive tradeoffs are explicit, and the strongest alternative is identified.

### 5. Search once for a dominating alternative

Perform one deliberate search for a missed solution class. Test whether a simpler formulation, changed boundary, relaxed assumption, avoided decision, or coherent hybrid removes the current tradeoff. A hybrid qualifies only when it removes weaknesses rather than combining complexity.

Add any credible new candidate to the slate and repeat only the affected evidence and comparison work. Repeat this search again only after materially new information changes the solution space.

**Complete when:** a credible new candidate has been compared, or one serious search finds no missed class likely to dominate.

### 6. Adversarially challenge the leader

Treat the leader as a hypothesis to falsify:

- identify its load-bearing assumptions and strongest realistic failure scenario;
- surface hidden migration, maintenance, operational, security, and compatibility costs;
- identify the scale, workload, environment, or future requirement that would break it;
- state evidence that would make the runner-up superior;
- retest the problem framing, actual scope, and location of complexity; and
- check whether sunk investment or exploratory lock-in is weighting the choice.

Apply the same realistic failure scenario to the leader and strongest alternative. A challenge earns its place only when it could change the decision.

When the leader fails, promote or generate another candidate, repeat the minimum affected evidence and comparison work, and challenge the replacement. When the challenge reveals a material unknown, follow the Discovery pointer under Choose the proportional mode.

**Complete when:** the current leader survives a decision-relevant falsification attempt, a replacement has been revalidated, or the stage has routed to bounded discovery.

### 7. Perform the zero-based challenge

Ask:

> If no implementation work had been done and I were choosing from scratch with everything now known, would I still choose this direction?

Treat prior work as sunk cost. Count future migration effort, compatibility impact, schedule cost, risk, retraining, and assets that retain future value. Existing production obligations remain real constraints.

When the answer changes, update the replacement's comparison, adversarially challenge it, and rerun the zero-based question. Return to earlier stages only when the failure invalidates their model, slate, criteria, or evidence.

**Complete when:** the leader remains stable under the zero-based question, or a replacement has completed the same comparison and challenge sequence.

### 8. Pass the Direction Gate

Set **Direction Gate: PASS** only when every applicable condition holds:

- the goal and success condition are clear enough to choose;
- the decision boundary and framing are appropriate;
- hard constraints and invariants are identified;
- every materially distinct credible candidate found was compared;
- decision-relevant unknowns were investigated proportionately;
- the selected direction meets the Support threshold;
- no known candidate clearly dominates it;
- it best satisfies the ordered criteria on available evidence;
- the adversarial and zero-based challenges still select it; and
- residual uncertainty is acceptable and has a concrete reopen condition.

When the gate cannot pass, identify its exact failing condition. Route a resolvable material unknown through the Discovery pointer. Ask only for an irreducible user preference or external constraint. If action is necessary and further discovery lacks proportionate decision value, select under the ordered criteria with residual uncertainty explicit, then rerun the gate. If action is optional, leave the direction explicitly unresolved.

**Complete when:** every applicable condition supports PASS, or the exact blocker produces a bounded discovery action, a focused user question, or an explicitly unresolved decision.

### 9. Record the decision

For a passing gate, use this exact field set:

#### Direction Decision

- **Mode:** full
- **Chosen direction:** one sentence
- **Why it wins:** decisive reasons tied to the ordered criteria
- **Alternatives rejected:** each serious candidate and its decisive losing tradeoff
- **Assumptions / uncertainty:** material items only
- **Reopen if:** concrete evidence or conditions that invalidate the choice
- **Direction Gate:** PASS

When a final direction is not yet justified, use this exact field set:

#### Discovery Decision

- **Mode:** lightweight or full
- **Unresolved decision:** what cannot yet be selected
- **Material uncertainty:** the fact or assumption capable of changing the winner
- **Next discovery step:** the smallest proportionate discriminating action, or none when further discovery lacks decision value
- **Decision effect:** how plausible outcomes change the model, slate, comparison, or gate
- **Stop / re-evaluate when:** the evidence needed to resume the interrupted stage
- **Direction Gate:** NOT PASSED

Keep each field concise and proportional to the decision. Reopen a passing decision only when implementation, tests, benchmarks, changed requirements, or verified facts materially weaken a load-bearing assumption or satisfy its Reopen if condition. Continue only into planning, implementation, or discovery work authorized by the user's request.
