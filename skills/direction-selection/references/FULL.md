# Full direction-selection protocol

Use this protocol only after `../SKILL.md` routes the current decision to `full`. Apply the parent skill's invocation triggers, authority semantics, Continuation invariant, Support threshold, deciding-evidence applicability rule, Direction Gate scope, future-horizon reversibility rule, and output contracts throughout. If a specific decision-sensitive unknown blocks a stage and no direction meets the Support threshold, read [DISCOVERY.md](DISCOVERY.md) completely and apply its Discovery Entry Test; discovery returns to the exact owning stage.

## 1. Build and challenge the problem model

Record:

- **Invocation trigger(s):** exact item or items from the authoritative full-mode trigger set.
- **Decision boundary:** the load-bearing choice required now, the commitment it governs, and later choices that can remain open. Separate independent choices, keep materially coupled choices together, and resolve upstream choices first.
- **Framing:** whether the stated problem is the outcome, a symptom, or a requested mechanism. Consider alternate framing only when a credible framing could materially change the solution space.
- **Goal:** the outcome being optimized and the observable success condition. Distinguish the real outcome from convenient proxies.
- **Hard constraints and invariants:** non-negotiable requirements, interfaces, compatibility guarantees, safety boundaries, budgets, and environmental limits.
- **Ordered criteria:** hard constraints, primary success criteria, secondary tradeoffs, then tie-breakers such as simplicity, future-horizon reversibility, option value, implementation cost, or consistency.
- **Unknowns:** known facts, reasonable assumptions, unresolved material uncertainty, and preferences only the user can decide.

Apply the authority and preference semantics from the router. Verify decision-sensitive unstable facts through fitting authoritative evidence routes when the task authorizes it. Preserve applicable caller-provided diagnosis, constraints, and evidence with their provenance; do not inherit an upstream ranking without comparison.

**Complete when:** the trigger, boundary, governed commitment, framing, goal, hard constraints, ordered criteria, and every known material unknown are explicit enough to establish the candidate space; any irreducible user preference is isolated.

## 2. Establish and justify the candidate space

Start with known materially distinct credible candidates. There is no required candidate count. Include the current design, doing less, avoiding the decision, or preserving the status quo only when credible.

Before elaborating a favorite:

1. State every plausible direction found so far in one neutral sentence.
2. Retain only materially independent candidates that could plausibly win under the ordered criteria.
3. Describe every serious candidate at comparable, decision-relevant depth.

This stage owns candidate-space exploration. Perform one serious bounded search when invocation triggers 3–5 require it or when Stage 1 establishes another credible omitted-direction signal. Test whether a simpler formulation, changed boundary, relaxed assumption, avoided decision, or coherent hybrid removes the current tradeoff. A hybrid qualifies only when it removes weaknesses rather than combining complexity.

Known consequential competitors alone do not require another class. An imaginable candidate is not evidence that the space is inadequate. Add any credible candidate found and complete only the affected modeling needed to compare it. Repeat candidate-space exploration only after materially new evidence changes the framing, shared premises, or credible solution space.

Use an available and authorized independent second look for high-impact choices only when its expected decision value justifies the cost. Ask neutrally and treat the result as evidence, not a vote.

**Complete when:** known serious candidates are neutrally and comparably stated, every candidate-space examination required by the invocation trigger has been completed once, and the stage records whether exploration was not required, found no credible alternative, or added candidates for comparison.

## 3. Gather discriminating, applicable evidence

Investigate only facts that can change the comparison. Prefer actual repository constraints, tests and observed behavior, authoritative documentation, specifications, representative benchmarks, small disposable experiments, migration and operational constraints, and known failure modes.

For each investigation, name the uncertainty it can reduce and how plausible outcomes could change the decision. Stop when no plausible result can affect the choice. Apply the same evidentiary standard to every serious candidate and the parent deciding-evidence applicability rule before any evidence carries a decisive claim.

For benchmarks, prototypes, tests, or observations, confirm that the evidence represents the property, workload, environment, operating conditions, and integration effects at risk. For documentation, research, reviews, or prior examples, confirm that the version, interface, operating context, and compared claim apply. Inapplicable evidence may inform the model but cannot decide the comparison.

When materially new evidence changes the framing, return to Stage 1. When it creates a credible omitted-direction or shared-premise signal, return to Stage 2. Apply the Continuation invariant and repeat only affected work.

Small or reversible actions must advance a commitment already supported at that level or reduce decision-relevant uncertainty. Keep exploratory work contained, observable, replaceable, and future-horizon reversible.

**Complete when:** every decisive comparative claim has applicable proportionate evidence, or its remaining uncertainty is explicit and has been accepted, routed through bounded discovery, or identified as the exact gate blocker.

## 4. Compare without anchoring

Evaluate in order:

1. **Constraint elimination:** remove candidates that violate a hard constraint unless that constraint is under review.
2. **Dominance:** prefer a candidate no worse on important criteria and materially better on at least one, unless uncertainty undermines the comparison.
3. **Tradeoffs:** compare primary criteria, secondary criteria, then tie-breakers.
4. **Uncertainty:** label advantages as evidence-backed, likely, or speculative.

Use measurements when available and ordered qualitative judgment otherwise. Apply symmetric standards. Count concrete future integration, transition, migration, compatibility, schedule, and operating costs without counting already-spent effort as support for an incumbent. Count future requirements in proportion to credible evidence. Treat simplicity as a tie-breaker and risk reducer, not a substitute for requirements. When higher-priority criteria remain close, prefer the direction easier to validate, reverse at the likely correction horizon, leave, or extend.

When applicable evidence establishes real dominance and no unresolved higher-priority uncertainty undermines it, stop needless lower-priority comparison. If comparison exposes a materially new framing or candidate-space signal, return to the earliest affected stage under the Continuation invariant.

**Complete when:** every surviving candidate has been evaluated under the same ordered criteria and evidentiary standard, decisive tradeoffs are explicit, and the strongest surviving alternative is identified when one exists.

## 5. Falsify the leader when triggered

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
- apply the Continuation invariant if the leader, framing, candidate space, or decisive evidence changes.

Skip falsification when its trigger is absent. Route a decision-sensitive material unknown through bounded discovery when appropriate.

**Complete when:** the mechanism was skipped because its trigger is absent, the leader survived a decision-changing challenge, a replacement completed affected revalidation, or the stage entered bounded discovery.

## 6. Run the zero-based diagnostic when bias risk is present

Run this diagnostic only when sunk implementation effort, incumbent attachment, migration history, legacy consistency pressure, exploratory lock-in, or prior-investment reasoning could bias the choice.

Ask:

> If no implementation work had been done and I were choosing from scratch with everything now known, would I still choose this direction?

Already-spent effort is not evidence for retaining the incumbent. Future migration, compatibility, schedule, risk, retraining, production obligations, and retained asset value are legitimate current factors. When the answer changes, update only affected comparison work and apply any independently triggered challenge. Skip the diagnostic when no credible incumbent or sunk-cost bias risk exists.

**Complete when:** the mechanism was skipped because no bias trigger exists, or the leader remains stable under the diagnostic after affected work is updated.

## 7. Pass the Direction Gate

Set `Direction Gate: PASS` only when every applicable condition holds:

- the goal, success condition, decision boundary, framing, and governed commitment are clear enough to choose;
- hard constraints and invariants are identified;
- every credible candidate in scope was compared symmetrically;
- every candidate-space examination required by the invocation trigger was completed;
- any triggered falsification or zero-based diagnostic was resolved enough;
- decisive evidence is applicable and proportionate;
- the selected direction meets the Support threshold;
- no known candidate clearly dominates it, and any credible strongest alternative has no better-supported case;
- residual uncertainty is acceptable at this commitment level and has a concrete reopen condition; and
- the governed commitment respects future-horizon reversibility and does not rely on pre-gate de facto lock-in.

Skipped mechanisms do not need to be passed. `PASS` reports support only for the governed direction-dependent commitment and does not authorize unrelated or project-wide work.

When the gate cannot pass, identify the exact failing condition. Route a resolvable decision-sensitive unknown through bounded discovery. Ask only for a user-owned preference or external constraint. If further discovery lacks proportionate value, return a `Direction Blocker` unless the canonical `Adaptive Direction` conditions in `../SKILL.md` justify a bounded commitment.

**Complete when:** every applicable condition supports `PASS`, or the exact blocker produces bounded discovery, a focused user question, a `Direction Blocker`, or an `Adaptive Direction`.

## 8. Record and return the outcome

Use the matching `Direction Decision`, `Direction Blocker`, or `Adaptive Direction` contract in `../SKILL.md`. Keep the record concise and proportional, state the exact governed commitment, return it with gate status to the caller/controller, and continue only into work separately authorized by the user's request.
