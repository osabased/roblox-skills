---
name: cross-agent-synthesis
description: Synthesize two or more independent agent analyses when their scopes overlap or can reveal cross-cutting causes. Use after independent first passes when targeted cross-signals could materially change findings, rankings, or root-cause attribution. Do not use as a general orchestrator, for routine single-perspective work, or when additional agents would only restate the same evidence.
---

# Cross-Agent Synthesis

Use this as a bounded reconciliation protocol after independent analyses already exist. It does not own the surrounding task, choose what work should happen next, or create a permanent discussion loop.

Core pattern:

`independent passes → cross-signals → targeted re-checks → root-cause synthesis`

## 1. Confirm synthesis is justified

Use this protocol only when all are true:

- at least two materially distinct perspectives or scopes exist;
- first-pass conclusions were formed independently;
- one perspective could expose evidence, assumptions, or consequences relevant to another;
- reconciliation can materially change the result.

Skip it when agents used the same evidence for the same question and no meaningful scope distinction exists.

**Complete when:** the distinct perspectives and the decision or result synthesis can change are explicit.

## 2. Preserve the independent first passes

Before sharing anything across agents, capture for each perspective:

- scope it owned;
- evidence it relied on;
- findings or conclusions;
- material uncertainty;
- explicit no-finding areas when useful.

Do not merge, rerank, or rewrite conclusions yet. Independence is useful only if the original signal survives long enough to compare.

## 3. Extract cross-signals

A cross-signal is a specific result from one perspective that could alter another perspective's conclusion.

Good cross-signals include:

- an implementation symptom suggesting a system-level cause;
- a system constraint exposing an implementation failure location;
- evidence that invalidates another agent's assumption;
- two findings that may be symptoms of one root cause;
- an apparent conflict in requirements, authority, or observed behavior;
- one agent's visibility gap that another agent's evidence can resolve.

Do not send general summaries. Send only the minimum signal needed for the target to re-check its own scope.

For every proposed cross-signal, ask:

> If the target agent considered this signal, could a material conclusion change?

If no, discard it.

**Complete when:** every retained cross-signal is decision-relevant and has a named target perspective.

## 4. Run targeted re-checks

Return each cross-signal only to the perspective qualified to evaluate its implication. The target re-checks its original evidence and scope; it does not adopt the source agent's conclusion by default.

Ask the target to return only one of:

- `CONFIRMED` — the signal demonstrates a new or changed conclusion, with evidence;
- `REFUTED` — evidence shows the signal does not alter the target conclusion;
- `RELATED` — the signal is relevant but is downstream/upstream evidence for an existing conclusion;
- `UNRESOLVED` — specific missing evidence prevents resolution.

A re-check must identify the evidence that supports its result. Agreement between agents is not evidence.

Do not recurse automatically. A second cross-signal round is allowed only when the first targeted re-check creates materially new evidence or a new conflict capable of changing synthesis. Otherwise stop.

**Complete when:** every retained cross-signal has a supported disposition or an explicit unresolved evidence need.

## 5. Reconcile without voting

Synthesize by causal and evidentiary strength, not majority agreement.

Apply these rules:

1. **Authority wins:** stronger applicable source or observed behavior outranks unsupported interpretation.
2. **Root cause wins:** when one demonstrated upstream cause explains downstream symptoms, keep the cause and attach symptoms as evidence.
3. **Independent causes stay separate:** do not collapse findings merely because they appear in the same scenario.
4. **Conflicts remain visible:** when evidence genuinely conflicts, preserve the conflict and identify the discriminating evidence needed.
5. **Scope ownership remains:** a perspective can contribute evidence outside its scope, but the qualified perspective owns the conclusion.
6. **No vote counting:** two agents agreeing does not outweigh one agent with stronger evidence.

A finding survives synthesis only when its own evidence and material consequence survive, not because another agent echoed it.

## 6. Return a compact synthesis

Use:

### Cross-Agent Synthesis

- **Perspectives:** names/scopes of the independent passes
- **Cross-signals checked:** count
- **Outcome:** `STABLE` | `CHANGED` | `UNRESOLVED`

### Surviving Conclusions

For each materially distinct conclusion:

**[X-NN] Conclusion**
- **Owner:** perspective qualified to own it
- **Evidence:** strongest applicable evidence
- **Cross-support:** other perspective evidence, if material
- **Disposition:** unchanged | strengthened | narrowed | replaced

### Resolved Conflicts

Only conflicts whose resolution materially affected the result.

### Unresolved

Only evidence gaps or conflicts capable of changing the result.

`STABLE` means cross-checking did not materially alter the independent conclusions. `CHANGED` means at least one conclusion was added, removed, narrowed, strengthened, or replaced. `UNRESOLVED` means a material conflict remains that available evidence cannot settle.

Return control to the invoking skill or caller. Do not continue into remediation, planning, implementation, or another review pass unless separately authorized.