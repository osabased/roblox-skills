# Generated-Skill Repair Loop

Use this reference for iterative repair of a **generated resource skill or affected resource/child validation evidence**. For installed/host reconciliation and post-adoption blocking/restoration semantics, also use [operational-lifecycle.md](operational-lifecycle.md). It never authorizes editing the `roblox-resource-acquisition` package itself; evidence that this package's own guidance is defective follows the self-growth boundaries in [state-policy.md](state-policy.md).

## Post-adoption entry

When ordinary use exposes a defect after host adoption, first follow [operational-lifecycle.md](operational-lifecycle.md#post-adoption-defects) to capture the reproduction, reconcile installed/parent state, block affected host adoptions, and invalidate affected evidence. Then enter the normal repair cycle below.

## The cycle

One repair cycle, in order:

1. **Classify** the failure into exactly one class below. If two defects are visible, take the one closest to the evidence and leave the other for its own cycle.
2. **Fix once, narrowly.** Apply the single smallest change the class prescribes for one distinct failing check. Batched speculative edits hide which change fixed or broke what.
3. **Re-run** what the class prescribes, then the regression reruns required by [testing-protocol.md](testing-protocol.md).
4. **Record** one learning entry in the external store per [learnings-store.md](learnings-store.md), kind per the class.
5. **Re-assess** against the budget, convergence, and stop rules.

## Classes

### 1. Resource failure — untrusted candidate

The resource itself cannot do what the acquisition brief requires.

- **Action:** reject the affected candidate. Return to candidate selection/discovery in [qualification-workflow.md](qualification-workflow.md) for another candidate only when alternatives are in scope; otherwise report that the targeted or existing candidate cannot satisfy the request.
- **Re-run:** nothing for the rejected candidate.
- **Record:** a `rejection` learning — identity, `version_context`, concise reason, `reconsider_when`.
- **Status:** the candidate's resource verification is recorded `failed`. Nothing else moves.

### 2. Resource failure — trusted

A resource with a recorded policy trust basis contradicts the intended use.

- **Action:** block the affected version/use and report the contradiction to the user. Canonical identity and recorded trust stay untouched until the controlling user/project policy changes them; curated catalog membership also remains untouched.
- **Re-run:** nothing automatically; the user's decision determines the next step.
- **Record:** a `version-drift` or `integration-gotcha` learning bound to the trusted identity.
- **Status:** the affected verification is recorded `failed`/blocked. Trust is not revoked.

### 3. Understanding failure

The resource is fine; the model of it was wrong, and proof or skill text built on the misreading is contaminated.

- **Action:** re-read source/docs, correct the understanding, correct any generated text derived from it.
- **Re-run:** every upstream resource proof in [qualification-workflow.md](qualification-workflow.md) that the misunderstanding invalidated; then, if skill text changed, the generated-skill regression reruns.
- **Record:** an `integration-gotcha` learning stating the misread and the actual behavior.
- **Status:** invalidated proof results reset to unexecuted until re-run.

### 4. Skill instruction failure

The resource behaves as understood; the generated skill teaches it wrong.

- **Action:** patch only the instructions responsible.
- **Re-run:** the failed check first, then **every previously passing applicable check** per the testing-protocol regression rule.
- **Record:** a `repair-outcome` learning — defect class, fix pattern, which check caught it.
- **Status:** the patch voids the skill's prior behavioral pass. `skill_validation.independent_behavioral_passed` cannot remain true until the reruns complete and pass.
- **Adoption:** affected host entries remain `blocked` until the repaired artifact is authorized for host update, the full regression/catalog checks pass, and explicit activation passes again.

### 5. Environment failure

A prerequisite of the check — not the skill and not the resource — is broken.

- **Action:** fix the prerequisite when possible; otherwise document it and record the blocked check `unavailable`. Never distort the skill to route around a broken environment.
- **Re-run:** the blocked check after the fix; nothing while `unavailable` stands.
- **Record:** an `environment-blocker` learning.
- **Status:** `unavailable` stays `unavailable`; it never converts to a pass.

### 6. Test failure

The check itself is invalid — wrong assertion, wrong fixture, or it tests something the contract never claimed.

- **Action:** repair the test.
- **Re-run:** the repaired test, plus a falsifiability demonstration — run it against the defective state it was written to catch (or an equivalent) and see it fail there. A test weakened until it cannot fail is deleted evidence, not a repair.
- **Record:** a `repair-outcome` learning stating why the test was invalid.
- **Status:** every result the invalid test produced is void; only the repaired test's fresh runs count.

## Budget

At most **three repair cycles per distinct failing check**. The fourth failure of the same check stops the loop and escalates.

"Distinct failing check" is the check, not the excuse: if check E fails again after a fix, for any cause, that consumes E's budget. Re-describing a defect does not reset a counter.

## Convergence

A cycle converged when its target check now passes **and** no previously passing check newly fails. A cycle that fixes A while breaking B did not converge: B's failure consumes B's own budget and raises the oscillation question below.

## Stop criteria

**Stop with success** the moment the reliability threshold in [testing-protocol.md](testing-protocol.md#reliability-threshold) is met. Additional polishing past the threshold is out of scope.

**Stop and escalate** when any of the following holds:

- a check exhausts its three-cycle budget;
- oscillation: a patch reverts an earlier cycle's patch, or two checks alternate failing across cycles — the defect model is wrong and further patching will not fix it;
- the evidence shows fundamental mismatch between resource and need: follow class 1 or class 2 instead of lowering the bar;
- the only remaining fix would edit this acquisition skill's own package: the self-growth boundaries in [state-policy.md](state-policy.md) take over.

## Escalation report

State, truthfully and compactly:

- the failing check(s) and each attempt made, with its patch and result;
- current resource verification and `skill_validation` states, with no optimistic rounding;
- the learning entries appended during the loop;
- the user's options: reject the untrusted candidate, block the trusted use, accept `unavailable`, supply an environment fix, or direct a specific change.

## Status separation

No repair activity upgrades any status implicitly:

- resource verification moves only when the applicable upstream resource proof in [qualification-workflow.md](qualification-workflow.md) actually re-executes and passes;
- structural skill validation moves only when `scripts/validate_skill.py` re-runs and passes;
- behavioral skill validation moves only when independent behavioral execution re-runs and passes;
- catalog routing moves only when the current catalog fingerprint's independent routing tests re-run and pass;
- host adoption returns to `operational` only after authorized host update and explicit activation re-run;
- a patch moves affected behavioral status **down** until reruns restore it.

## Learning emission

Every repair cycle appends exactly one learning entry per [learnings-store.md](learnings-store.md). If no store exists and one cannot be created, put the learning's content in the escalation or final report so it is not lost — never write it into this skill's package.

