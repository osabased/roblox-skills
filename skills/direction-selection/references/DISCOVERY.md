# Discovery Direction

Discovery is a bounded call/return subroutine for a specific direction-sensitive unknown. It is not a generic pre-direction evidence router, a conservative default, a production direction, or a way to maximize confidence.

## Invocation and ownership

With a surrounding controller, hand a non-directional unknown encountered before a genuine direction problem is live back to that controller. Discovery does not own general research, benchmarking, user clarification, project-state inspection, planning, persistence, or verification before invocation.

When a live direction comparison exists, enter discovery only when plausible outcomes can materially change the framing, candidate set, ranking, or Direction Gate. Preserve the interrupted comparison stage as owner, gather only the justified evidence, and return to that exact stage. Do not restart applicability or the full protocol.

For standalone use only, discovery may serve a minimum bounded **applicability evidence probe** when evidence is necessary to determine whether a genuine direction problem exists or whether the incumbent is supportable. Apply the test below, then return to the [SKILL.md](../SKILL.md) applicability/mode router. Exit if no direction problem remains. The probe is not automatically a terminal `Discovery Decision`; emit that record only when required evidence cannot be resolved in the bounded run and an actual stop or handoff is necessary.

## Discovery Entry Test

Apply this test before every discovery call. When the user explicitly mandates discovery work, only that specified work is authorized without the test; any extension requires a fresh test.

Every transition must satisfy all applicable conditions:

1. **Specific material uncertainty:** a concrete unknown could materially affect applicability, the owning comparison stage, or the eventual direction result.
2. **Decision sensitivity:** at least two plausible outcomes would change applicability, framing, candidates, ranking, or gate status.
3. **Worth investigating now:** expected decision value is proportionate to cost, delay, risk, and commitment.
4. **No sufficiently supported direction:** the current best-defined direction cannot meet the canonical Support threshold for the governed commitment while accepting this uncertainty.

When the test fails, return to the owner. The applicability router may exit or hand off; comparison may use the best-supported direction with explicit residual uncertainty and a reopen condition, or leave the choice unresolved when action is optional and no direction is supportable.

**Complete when:** all applicable conditions pass and a bounded step is defined, or a failing condition returns control to the owner, a focused user question, or an explicit unresolved state.

## Select the discovery step

Choose the lowest-cost, lowest-commitment action or short bounded sequence that can materially discriminate the uncertainty. Prefer one high-information observation, inspection, test, benchmark, measurement, prototype, or disposable experiment over broad research or partial implementation.

Record before acting:

1. **Owner and return point:** standalone applicability router or the exact interrupted comparison stage.
2. **Material uncertainty:** what is unknown and why it could change the owner's result.
3. **Discriminating step:** the cheapest reliable action that distinguishes relevant outcomes.
4. **Decision effect:** how plausible outcomes change applicability or the interrupted stage.
5. **Commitment:** cost, delay, risk, and anything made harder to reverse at the likely future correction point.
6. **Stop / re-evaluate condition:** the evidence sufficient to return to the owner.

Use the smallest contained experiment that yields representative evidence. Give higher-commitment experiments explicit limits, observability, and a rollback or exit path.

Before evidence can resolve applicability or carry a deciding comparative claim, apply the deciding-evidence applicability rule in [SKILL.md](../SKILL.md). Cheap or discriminating evidence that does not represent the actual property, version, environment, integration effects, or claim at risk is informative but non-deciding.

**Complete when:** the step has a named owner, uncertainty, discriminating outcomes, proportionate and future-horizon-reversible commitment, and checkable stop condition.

## Execute a bounded discovery loop

1. Perform only the defined discovery work.
2. Update only the affected applicability fact, problem model, assumptions, candidate set, evidence, or comparison.
3. Return to the recorded owner and exact return point when the stop condition is met.
4. Before another discovery step, rerun the Discovery Entry Test against the remaining uncertainty.

Continue only while a material unknown remains and the next step can realistically change the owner's result. Increase commitment only as support increases, and stop once a direction can pass its commitment-scoped gate with acceptable residual uncertainty.

Distinguish:

- **Resolvable uncertainty:** evidence progressively narrows the unknown within a stable decision model. Continue only while the entry test passes.
- **Structurally unstable uncertainty:** worthwhile evidence keeps changing the model or credible futures, or commitment must occur before the question can be resolved. When further investigation has low decision value, stop ordinary discovery and return to `SKILL.md` for possible `Adaptive Direction` handling. Difficulty alone does not justify adaptive handling.

Do not rerun discovery indefinitely merely because uncertainty remains.

Exploratory code, scaffolding, prototypes, and migrations are disposable by default. They may not silently cross the governed consequential commitment boundary without a passing conventional direction or a passing bounded adaptive commitment. This does not block unrelated, already-supported, or safely future-horizon-reversible production work, and no pre-gate work may create de facto lock-in.

The loop is **complete when:** applicable evidence resolves or bounds the uncertainty enough to return to the owner, another entry test fails and returns control, a terminal `Discovery Decision` is required, or structurally unstable uncertainty returns to the canonical adaptive path.
