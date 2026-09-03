# Self-Application

Use this branch when direction selection evaluates changes to itself, another decision process, or a protocol that invokes this skill.

## Bound the meta-level

1. Name the exact target behavior and decision at the current meta-level.
2. Identify the affected applicability routes, comparison stages, output contracts, context pointers, and invariants. When the change affects applicability, discovery, handoffs, or ownership, read [CALL_RETURN_OWNERSHIP_INVARIANT.md](CALL_RETURN_OWNERSHIP_INVARIANT.md) completely.
3. Apply the applicability router, proportional mode, and only conditionally triggered mechanisms to the target once. Make the smallest coherent change that can produce the intended behavior.
4. Verify observable routing and outcomes, contradictions, regressions, ownership returns, and newly introduced failure modes. Check that every affected route reaches one valid owner, output, and stopping condition.
5. Correct each concrete defect and rerun the failed check plus every previously passing check whose behavior or assumptions the correction could affect.
6. Stop when every required check passes and no demonstrated material defect remains.

Protocol invocation, clause-by-clause validation, and verification of verification are not additional evidence. Run one adversarial pass after the first verified revision. Further passes require a concrete failed check, contradiction, new material evidence, or an explicit user requirement; stylistic preference alone does not reopen the protocol.

Re-enter direction selection only when new material evidence changes the candidate space, ordered criteria, or a load-bearing assumption.

**Complete when:** self-application ends in a `Direction Decision`, `Direction Blocker`, `Adaptive Direction`, `Applicability Result`, or finite correction of a concrete defect, and every required verification check passes.
