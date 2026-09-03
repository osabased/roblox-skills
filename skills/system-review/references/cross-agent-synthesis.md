# Cross-agent synthesis

Read this only after independent review passes exist and sharing results could materially change a finding, causal attribution, disposition, or visibility gap.

## 1. Preserve the first passes

For each perspective, retain its scope, target, evidence, conclusions, and material uncertainty before sharing cross-signals. Independence is lost if first passes are rewritten into a common story first.

**Complete when:** every perspective's original conclusion can still be compared with its post-signal conclusion.

## 2. Extract cross-signals

A cross-signal is one specific result that could change another perspective's conclusion. Examples include evidence that invalidates an assumption, exposes another failed contract or control, resolves a visibility gap, changes causal attribution, or changes the supported finding disposition.

Keep a signal only when the target perspective could materially change its conclusion after considering it. Send the minimum evidence and provenance needed for that re-check, not a general summary.

**Complete when:** every retained signal has a named target, applicable evidence, and a plausible decision effect.

## 3. Re-check the owning perspective

The target perspective re-evaluates its own scope and evidence and returns one disposition:

- `CONFIRMED` — the signal changes or adds a conclusion, with evidence;
- `REFUTED` — evidence shows the signal does not change the conclusion;
- `RELATED` — the signal supports an existing conclusion rather than creating another one;
- `UNRESOLVED` — specific missing evidence prevents resolution.

Agreement is not evidence. Run a second signal round only when the first re-check produces materially new evidence or a new conflict that can change the synthesis.

**Complete when:** every retained signal has an evidence-backed disposition or a specific unresolved evidence need.

## 4. Reconcile

Apply the evidence-reach, causal, finding, and verdict rules in `system-review`:

1. applicable authority or observed behavior outranks unsupported interpretation;
2. triggers remain distinct from violated contracts or failed controls;
3. observations sharing one failed contract or control are grouped, while independently material failed controls remain separate;
4. genuine evidence conflicts remain visible with the discriminating evidence needed;
5. the perspective qualified for a conclusion retains ownership of it.

Return reconciled findings, dispositions, residual risks, and unresolved gaps to `system-review`. Do not introduce a parallel issue taxonomy, start remediation, or open another generic review cycle from this reference.

**Complete when:** each surviving conclusion has one qualified owner and applicable supporting evidence, and every unresolved conflict names the evidence needed to settle it.
