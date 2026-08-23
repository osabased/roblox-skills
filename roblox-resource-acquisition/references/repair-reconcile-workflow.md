# Resource repair and reconciliation workflow

Use this reference for a generated child defect, installed/source-state mismatch, adverse current observation, legacy child/record state, or refresh work whose affected validation evidence must be rebuilt.

## Repair the generated skill until it converges

Repair scope is the generated resource skill and its validation/adoption evidence, whether the defect appears before adoption or during ordinary post-adoption use — never this acquisition skill's own package files, which follow the self-growth boundaries in [state-policy.md](state-policy.md). Full loop mechanics live in [repair-loop.md](repair-loop.md).

Work in bounded cycles. One cycle: classify the failure, apply the single narrowest fix for one distinct failing check, re-run what the class prescribes plus the regression reruns required by [testing-protocol.md](testing-protocol.md), append one learning entry to the external learnings store, then re-assess.

Classify before editing:

- **resource failure (untrusted candidate)** -> reject the affected candidate; consider another only when alternatives are in scope; record a `rejection` learning; that candidate's resource verification is recorded failed;
- **resource failure (trusted)** -> block the affected version/use and report the contradiction; record a `version-drift` or `integration-gotcha` learning; canonical identity and recorded trust stay untouched unless the controlling user/project policy changes them;
- **understanding failure** -> correct the model from source/docs; re-run the resource proof the misunderstanding invalidated; record an `integration-gotcha` learning;
- **skill instruction failure** -> patch only the instructions responsible; re-run the failed check plus every previously passing applicable check; record a `repair-outcome` learning; the patch voids prior behavioral passes until those reruns complete;
- **environment failure** -> fix or document the prerequisite and re-run the blocked check, or record it unavailable if unfixable; record an `environment-blocker` learning; never distort the skill around a broken environment;
- **test failure** -> repair the invalid test, re-run it, and demonstrate the repaired test can still fail; record a `repair-outcome` learning; results produced by the invalid test are void.

Budget: at most **three repair cycles per distinct failing check**; the fourth failure of the same check stops the loop. Do not endlessly polish. Stop with success only when the reliability threshold in [testing-protocol.md](testing-protocol.md) is met. Stop and escalate to the user when a check exhausts its budget, when patches oscillate (a fix reverting an earlier fix, or two checks alternately breaking), or when failures expose a fundamental mismatch rather than a fixable skill defect — then reject the untrusted candidate or block the trusted use and surface the evidence instead of lowering the bar. Escalation states the failing checks, each attempt and its result, truthful current statuses, the learnings appended, and the user's options.

No repair activity upgrades any status implicitly. Resource verification and `skill_validation` each move only when their own gate actually re-executes and passes; a patch moves affected behavioral status down until reruns restore it.

A confirmed post-adoption defect marks every affected `host_adoptions` entry `blocked` and invalidates affected behavioral and catalog-routing passes before repair. Restoring `operational` requires the regression suite, catalog validation, an authorized update of the host copy, and a fresh explicit host-activation pass. Follow [operational-lifecycle.md](operational-lifecycle.md).
