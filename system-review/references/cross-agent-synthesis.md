# Cross-agent synthesis

Read this only after independent review passes exist and sharing results could materially change a conclusion, root-cause attribution, or visibility gap.

## 1. Preserve the first passes

For each perspective, retain its scope, evidence, conclusions, and material uncertainty before sharing cross-signals. Independence is lost if the first passes are rewritten into a common story first.

**Complete when:** every perspective's original conclusion can still be compared with its post-signal conclusion.

## 2. Extract cross-signals

A cross-signal is one specific result that could change another perspective's conclusion. Examples include evidence that invalidates an assumption, an implementation symptom that may expose a system cause, a system constraint that may expose an implementation failure, or evidence that can resolve another perspective's visibility gap.

Keep a signal only when the target perspective could materially change its conclusion after considering it. Send the minimum evidence needed for that re-check, not a general summary.

**Complete when:** every retained signal has a named target and a plausible decision effect.

## 3. Re-check the owning perspective

The target perspective re-evaluates its own scope and evidence and returns one disposition:

- `CONFIRMED` — the signal changes or adds a conclusion, with evidence;
- `REFUTED` — evidence shows the signal does not change the conclusion;
- `RELATED` — the signal supports an existing conclusion rather than creating another one;
- `UNRESOLVED` — specific missing evidence prevents resolution.

Agreement is not evidence. Run a second signal round only when the first re-check produces materially new evidence or a new conflict that can change the synthesis.

**Complete when:** every retained signal has an evidence-backed disposition or a specific unresolved evidence need.

## 4. Reconcile

Synthesize by evidentiary and causal strength:

1. stronger applicable authority or observed behavior outranks unsupported interpretation;
2. one demonstrated upstream cause absorbs downstream symptoms as supporting evidence;
3. independent causes remain separate;
4. genuine evidence conflicts remain visible with the discriminating evidence needed;
5. the perspective qualified for a conclusion retains ownership of it.

Return the reconciled conclusions and unresolved gaps to `system-review`. Do not start remediation or another review cycle from this reference.