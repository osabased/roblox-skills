---
name: fresh-context-behavioral-review
description: Perform a cold behavioral review of non-trivial implementation when author intent or prior reasoning could bias self-review. Use for fresh-eyes verification of observable behavior, edge cases, security, integration assumptions, and failure handling after implementation, especially for consequential or unattended code. Do not use for ordinary stylistic review or when the reviewer must know the implementing agent's rationale to judge correctness.
---

# Fresh-Context Behavioral Review

Review what the implementation **does**, not what its author intended to do. Preserve enough repository and specification context to judge correctness, but exclude the implementing agent's rationale, self-review, and claimed guarantees unless they are themselves authoritative requirements.

This is a verification review, not a defect-generation exercise. A clean result is valid when the relevant scenarios were positively exercised and no demonstrated material defect remains.

## 1. Build the cold review packet

Provide the reviewer only what is needed to establish expected behavior:

- implementation or diff under review;
- originating requirement, ticket, specification, or explicit expected behavior;
- applicable repository contracts and public interfaces;
- dependency contracts needed to understand interactions;
- relevant tests and test commands;
- environmental constraints that materially affect behavior.

Exclude:

- the implementing agent's chain of thought or rationale;
- prior self-audit conclusions;
- explanations of why the implementation is believed correct;
- suggested bugs to look for unless they are externally reported behavior.

Do not strip required context merely to make the review "blind." Intent independence is useful; specification blindness is not.

**Complete when:** the packet can establish expected observable behavior without carrying the author's justification.

## 2. Identify behavioral contracts

Extract the externally meaningful contracts the implementation must preserve:

- inputs and accepted states;
- outputs and side effects;
- error and failure semantics;
- authorization and trust assumptions;
- persistence or state-transition guarantees;
- ordering, idempotency, retry, and concurrency guarantees when relevant;
- public interfaces and compatibility commitments;
- integration preconditions supplied by dependencies.

Distinguish explicit requirements from inferred expectations. Do not promote a style preference or speculative invariant into a contract.

**Complete when:** every material behavior under review has a checkable expected outcome.

## 3. Exercise scenarios

Use behavioral scenarios as the primary unit of review. Choose only scenarios capable of exposing material defects in the changed behavior.

At minimum consider, when applicable:

- primary happy path;
- boundary, empty, zero, null, and malformed inputs;
- unauthorized or adversarial input;
- repeated action and duplicate delivery;
- retries after partial failure;
- interruption, timeout, cancellation, and recovery;
- concurrent or unexpectedly ordered operations;
- dependency failure or incompatible response;
- state carried across multiple calls;
- unusual-but-valid inputs;
- upgrade, migration, or compatibility behavior affected by the change.

Prefer executing existing tests or focused reproductions. When execution is unavailable, inspect the relevant paths and mark the scenario unverified rather than claiming it passed.

For every scenario, identify:

`setup → action → observable expected result`

A structural/source check may support the review when the requirement is inherently structural or gives coverage behavior cannot establish directly.

**Complete when:** every material contract is exercised by at least one relevant scenario or explicitly marked unverified.

## 4. Qualify findings

A finding requires:

1. **Authority:** the expected behavior comes from a requirement, contract, security boundary, repository rule, or necessary interaction invariant.
2. **Evidence:** code behavior, test output, reproduction, or direct structural evidence demonstrates the mismatch.
3. **Material consequence:** the mismatch can affect correctness, security, compatibility, reliability, or the requested outcome.

Use:

**[B-NN] Title**
- **Contract:** expected behavior and authority
- **Scenario:** setup/action/expected result
- **Evidence:** observed or inspected mismatch
- **Consequence:** material effect
- **Smallest correction:** minimum coherent fix
- **Confidence:** high | medium | low

Do not emit findings merely because:

- another implementation would be cleaner;
- a hypothetical edge case has no supported contract or credible consequence;
- a test could be added but no behavior is currently unverified or risky;
- the implementation differs from the reviewer's preferred architecture;
- the reviewer expected to find something.

If missing dependency or environment information prevents judgment, record a **verification gap**, not a defect.

## 5. Check integration assumptions

Inspect dependencies referenced by the changed behavior far enough to validate contracts that materially affect the scenarios. Do not demand the entire dependency graph.

For each material external assumption ask:

- Does the dependency exist at the referenced location/version?
- Does its public contract support the assumed input, output, error, and lifecycle behavior?
- Is the call made from a valid runtime/environment?
- Can failure, timeout, cancellation, or partial success violate the caller's contract?

When the answer cannot be established and could change the verdict, mark it as a verification gap.

## 6. Return the review

Use:

### Fresh-Context Behavioral Review

- **Scope:** implementation/change reviewed
- **Verdict:** `PASS` | `CHANGES REQUIRED` | `INSUFFICIENT EVIDENCE`

### Findings

Only demonstrated material defects using the `[B-NN]` contract above.

### Verification Gaps

Only missing evidence capable of changing the verdict.

### Scenarios Exercised

For each relevant scenario: `PASS | FAIL | BLOCKED` plus the observable check used.

### Validated Behavior

Name important contracts that were positively exercised with no demonstrated defect.

## Verdict rules

- `PASS`: every required scenario that can materially establish correctness passed, no required check is blocked, and no demonstrated material defect remains.
- `CHANGES REQUIRED`: at least one demonstrated material defect remains.
- `INSUFFICIENT EVIDENCE`: a required verification scenario is blocked or missing evidence prevents a supported verdict.

After a correction, rerun every failed scenario and every previously passing scenario whose assumptions or dependencies were affected by the fix. Stop once required verification passes and no demonstrated material defect remains.