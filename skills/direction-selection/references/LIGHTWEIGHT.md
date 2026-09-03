# Lightweight Direction Selection

Use this branch only after the [SKILL.md](../SKILL.md) applicability router returns `lightweight`: a meaningful bounded choice is live, and the framing, ordered criteria, and candidate space are already adequate. The parent skill's authority semantics, Continuation invariant, Support threshold, deciding-evidence applicability rule, future-horizon reversibility definition, Direction Gate scope, and output contracts apply throughout.

## Procedure

1. Record the goal, hard constraints, ordered criteria, governed commitment, and credible known alternatives. Do not search for another candidate merely to fill the record.
2. Compare the known serious alternatives under the same decisive criteria. Identify the strongest surviving alternative when one exists. Do not count already-spent effort as support for an incumbent; count concrete future migration, compatibility, schedule, and operating costs.
3. When one cheap decision-sensitive unknown prevents the Support threshold from passing, resolve it through the fitting evidence route. If bounded discovery is warranted, read [DISCOVERY.md](DISCOVERY.md) completely, preserve this comparison as owner, and resume this step afterward.
4. Challenge one load-bearing reason only when it remains meaningfully uncertain and one cheap realistic check could change the winner. Apply the parent deciding-evidence applicability rule to the result. Skip this check when its trigger is absent.
5. Judge the selected direction against the Support threshold using future-horizon reversibility. Set a concrete reopen condition, then return a `Direction Decision`, `Direction Blocker`, or justified `Adaptive Direction`.

Lightweight mode does not broaden or re-justify the candidate space. When an authoritative full-mode trigger emerges—including framing ambiguity, candidate-space inadequacy, consequential unresolved competition, weak comparative justification requiring structured challenge, or material evidence that changes the frame or candidate space—preserve all still-applicable work under the Continuation invariant and enter `full` at the earliest affected stage. Do not restart completed work.

## Lightweight Direction Gate

Set `Direction Gate: PASS` only when every applicable condition holds:

- the goal, constraints, ordered criteria, and governed commitment are clear enough to choose;
- every credible known alternative was compared symmetrically;
- decisive evidence is applicable and proportionate;
- any triggered cheap unknown or disconfirming check was resolved enough;
- the selected direction meets the Support threshold;
- reversibility was assessed at the likely future correction point; and
- residual uncertainty is acceptable for the governed commitment and has a concrete reopen condition.

Skipped mechanisms do not need to be performed or passed. The gate is a support result for this commitment and not broader implementation authority.

**Complete when:** every applicable condition supports `PASS`; the exact blocker produces a `Direction Blocker`; structural instability justifies an `Adaptive Direction`; or an authoritative full-mode trigger preserves current work and transfers control to `full`.

## Record

Use the canonical `Direction Decision`, `Direction Blocker`, or `Adaptive Direction` schema in [SKILL.md](../SKILL.md). A conventional passing record uses `Mode: lightweight` and states the exact governed commitment. `Alternatives / candidate-space result: none — no search required` is valid when no credible alternative existed.

Return the local record and commitment-scoped gate status to the caller/controller. Continue only into work separately authorized by the user's request.
