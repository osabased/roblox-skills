# Discovery Direction

Use discovery only when a specific decision-relevant unknown prevents the current stage from completing and no defined direction meets the Support threshold. Discovery is a temporary branch that reduces uncertainty; it is not a conservative default, a production direction, or a way to maximize confidence.

## Discovery Entry Test

Apply this test before every transition into discovery. When the user explicitly mandates the discovery work itself, treat only that specified work as authorized without the test; any extension requires a fresh test.

Every tested transition must satisfy all applicable conditions:

1. **Specific material uncertainty:** a concrete unknown could materially affect the current protocol stage or eventual winner.
2. **Decision sensitivity:** at least two plausible outcomes would change the framing, candidates, ranking, or gate result.
3. **Worth investigating now:** the expected decision value is proportionate to cost, delay, risk, and commitment.
4. **No sufficiently supported winner:** the current best-defined direction cannot meet the Support threshold for the commitment with the uncertainty accepted.

An entry decision is **complete when:** all applicable conditions pass and a bounded step is defined, or the failing condition returns the process to a defined direction, an explicit unresolved state, or a focused user question.

When the test fails, return to the best-supported defined direction with residual uncertainty and a reopen condition. If action is optional and no direction is supportable, leave the choice unresolved.

## Select the Discovery Direction

Choose the lowest-cost, lowest-commitment action or short bounded sequence that can materially discriminate the uncertainty. Prefer one high-information observation, inspection, test, benchmark, measurement, prototype, or disposable experiment over broad research or partial implementation.

Record before acting:

1. **Material uncertainty:** what is unknown and why it could change the decision.
2. **Discriminating step:** the cheapest reliable action that distinguishes relevant outcomes.
3. **Decision effect:** how each plausible outcome changes the interrupted stage.
4. **Commitment:** cost, delay, risk, and anything made harder to reverse.
5. **Stop / re-evaluate condition:** the evidence sufficient to resume comparison.

Use the smallest contained experiment that yields representative evidence. Give higher-commitment experiments explicit limits, observability, and a rollback or exit path.

**Complete when:** the chosen step has a named uncertainty, discriminating outcomes, proportionate commitment, and a checkable stop condition.

## Execute a bounded discovery loop

1. Perform only the defined discovery work.
2. Update the affected problem model, assumptions, candidate slate, evidence, or comparison.
3. Return to the interrupted protocol stage when the stop condition is met.
4. Before another discovery step, rerun the Discovery Entry Test against the remaining uncertainty.

Continue only while a material unknown remains and the next step can realistically change the decision. Increase commitment as support increases, and stop discovery once a direction can pass its gate with acceptable residual uncertainty.

Exploratory code, scaffolding, prototypes, and migrations are disposable by default. **They must not become production implementation before Direction Gate: PASS.**

The loop is **complete when:** the evidence resolves or bounds the material uncertainty enough to resume the interrupted stage, or another entry test fails and returns the process to a defined direction or explicit unresolved state.
