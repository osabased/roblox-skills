# Generated Skill Testing Protocol

Validate the generated skill as an interface for another agent, not as prose.

## Test A - Appropriate activation

Give a task whose requirements closely match the resource. Pass if the skill is selected for a justified reason and the agent does not over-expand scope.

## Test B - Negative activation

Give an unrelated task or a task better solved by Roblox built-ins/a tiny local implementation. Pass if the skill does not force the resource into the solution.

## Test C - Clean setup

Start from documented prerequisites only. Pass if an agent can install/place/require the resource without relying on hidden research context.

## Test D - Minimal happy path

Implement the smallest useful behavior. Pass if observed behavior matches the skill and upstream validated behavior.

## Test E - Representative integration

Use a realistic task that exercises the reason the resource was acquired. Pass if the agent uses the correct lifecycle, execution side, and configuration.

## Test F - Edge/failure diagnosis

Introduce one likely integration problem: missing dependency, wrong placement, invalid config, unavailable service, cleanup issue, or similar. Pass if the skill leads to the real cause without hallucinating methods or unrelated rewrites.

## Test G - Version/provenance/verification truthfulness

Ask what source/version the guidance targets and whether the upstream resource was actually runtime-verified. Pass if both are recoverable directly from the skill and source review is not mislabeled as runtime verification.

## Test H - Security boundary

Required when the resource touches remotes, HTTP, credentials, persistence, arbitrary assets/code, or other trust boundaries. Pass if the skill preserves Roblox's server-authoritative/security expectations and identifies special resource risks.

## Test I - Operational reconciliation

Use a project whose installed resource state is independently mutable when the child declares reconciliation `required`. Pass if the child detects the installed identity/version, compares it with its reviewed state, consults matching parent-maintained records/learnings, and stops the affected use on an unknown, mismatch, or current block. For `not-applicable`, pass only when the child gives a concrete immutable-install or version-insensitivity reason.

Introduce a new ordinary-use instruction defect. Pass if the child captures the task, installed state, expected/observed behavior, and smallest reproduction, then activates `roblox-resource-acquisition` in `repair/reconcile` mode without silently continuing.

## Test J - Catalog routing

Inspect the target host's visible skill activation surfaces whenever a generated child is added, refreshed, repaired, or adopted. Run this behavioral test when either (a) the target host set contains two or more generated children, or (b) any generated child has a plausible activation competitor among non-generated host-visible skills. First run `scripts/validate_skill_catalog.py` over the generated-child set and add each material non-generated competitor with `--routing-competitor <path>`; retain the resulting fingerprint. Non-generated competitors are routing inputs only and do not need to satisfy the generated resource-skill contract. For every reported overlap cluster, give independent agents:

- one task specific to each generated child in the cluster;
- one task specific to each competing host-visible skill needed to exercise the boundary;
- one simpler task that should select neither;
- one explicit-invocation smoke task per generated child.

Pass if the intended skill is selected for each specific task, competing skills stay out, the simpler task selects neither, explicit generated-child invocation succeeds, and the recorded fingerprint still matches the exact tested routing set. If independent execution is unavailable, record catalog routing `unavailable`, not passed. Record `not-applicable` only after host-visible activation inspection finds no plausible competitor and fewer than two generated children share the target host. Any later change to a tested generated child or routing competitor invalidates the prior fingerprint/evidence.

## Regression rule

After any repair patch, rerun:

- the failed test first;
- then every previously passing applicable test — a patch voids prior passes until they are re-established, so rerunning only A, B, and D is insufficient.

A repaired test must additionally demonstrate that it can still fail: run it against the defective state it was written to catch, or an equivalent. A test weakened until it cannot fail is deleted evidence, not a repair.

From the moment of a patch until these reruns complete and pass, the generated skill's prior behavioral validation is void and `skill_validation` must not continue to claim it. Attempt budgets, convergence, and stop criteria for the repair loop live in [repair-loop.md](repair-loop.md).

## Reliability threshold

Mark a generated resource skill behaviorally verified only when:

- all applicable tests pass through their required execution mode;
- no applicable required test is recorded as unavailable;
- generated-skill structural validator passes;
- when a portable resource record is emitted, its resource-record structural/state validator passes;
- when both a portable record and generated child exist, their `validate_resource_bundle.py` identity/source-state consistency gate passes;
- operational reconciliation Test I passes when applicable;
- catalog routing Test J passes when two or more generated children share the target host set or a generated child has a plausible non-generated host-visible competitor;
- no unsupported API statement remains;
- no high-severity safety/integration defect remains;
- runtime tests are labeled accurately;
- independent behavioral execution was actually performed rather than replaced by a same-agent contract audit;
- failures are not being hidden by weakening assertions.

Optional embellishments, more examples, or stylistic improvements are not reasons to continue once the threshold is met.

