# Lightweight Direction Selection

Use this branch for a meaningful but bounded or readily reversible choice, or for a direction already supported enough to need only proportionate confirmation. The Support threshold remains the decision standard.

## Procedure

1. Record the goal, hard constraints, and the commitment this choice authorizes.
2. Seek a genuinely different alternative when one could credibly exist, and compare it at proportionate depth.
3. Identify the decisive tradeoff under the ordered criteria.
4. Attempt to falsify the leader with a realistic failure condition or evidence that would make the alternative superior.
5. Make material uncertainty explicit. When a cheaply resolvable unknown could change the choice and the current leader does not meet the Support threshold, read [DISCOVERY.md](DISCOVERY.md) completely and apply the Discovery Entry Test. Escalate to the full protocol when proportional investigation requires a fuller model, slate, or comparison.
6. Judge the leader against the Support threshold and set a concrete reopen condition.

Escalate to the full protocol when a high-impact tradeoff emerges, materially competitive candidates remain unresolved, framing ambiguity appears, discovery becomes disproportionate for this branch, or no winner can be supported proportionately. The existence of another credible candidate alone does not require escalation.

## Lightweight Direction Gate

Set **Direction Gate: PASS** only when:

- the goal, constraints, and authorized commitment are clear enough to choose;
- credible alternatives were actively sought when one could reasonably exist;
- the leader meets the Support threshold;
- the falsification attempt found no better direction or unresolved fatal flaw; and
- residual uncertainty is acceptable and has a concrete reopen condition.

**Complete when:** every condition supports PASS, or the exact blocker routes to the full protocol, bounded discovery, a focused user question, or an explicitly unresolved decision.

## Record

For a passing gate, use this exact field set:

### Direction Decision

- **Mode:** lightweight
- **Chosen direction:** one sentence
- **Why it wins:** decisive reasons tied to the ordered criteria
- **Alternatives rejected:** each serious candidate and its decisive losing tradeoff
- **Assumptions / uncertainty:** material items only
- **Reopen if:** concrete evidence or conditions that invalidate the choice
- **Direction Gate:** PASS

When no final direction is justified, use the Discovery Decision schema in [SKILL.md](SKILL.md). Continue only into work authorized by the user's request.
