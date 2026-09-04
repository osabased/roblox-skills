# Delegated Reconnaissance

Use this branch when a large or unfamiliar target would materially consume the controller's context, or when parallel independent inspection materially improves coverage.

Gather enough applicable evidence for the Intervention Gate. Preserve the controller's context for synthesis, design, implementation, and verification.

## Controller contract

The controller owns:

- target and search boundaries;
- capability routing;
- synthesis and causal reconciliation;
- candidate qualification and falsification;
- intervention authorization and route selection;
- every write and final conclusion.

Delegated agents operate read-only and return evidence packets. The controller alone authorizes scope changes, further delegation, interventions, and writes.

A packet is evidence input, not a finding. Verify every decisive delegated claim directly or through applicable independent corroboration before it can pass the Intervention Gate.

### Controller capability

The active controller must be capable of `judge`-level synthesis: reconciling cross-area evidence, attributing architectural causes, falsifying candidates, and authorizing consequential change.

When the active controller cannot reliably perform that work, transfer the entire invocation to the strongest available judge-capable agent before reconnaissance. When transfer is unavailable, narrow the target until the controller can judge it reliably or return `BLOCKED` with the capability limit. Stronger delegated agents can supply evidence; they cannot replace final controller judgment.

## 1. Map and partition

Perform a cheap topology pass before loading implementation detail:

- repository instructions and domain documents;
- directory and package structure;
- manifests, ADRs, and standards;
- recent history and current changes;
- test entry points;
- available dependency or symbol indexes.

Partition the target by architectural responsibility, seam, change path, or dependency region. Use the smallest set of partitions that covers materially different areas. Parallelize only independent partitions.

Give each agent a fresh bounded work order with paths, symbols, commands, requirements, and questions rather than copied source. Store detailed notes in a shared temporary artifact when the harness supports one; return only a compact evidence index to the controller.

**Complete when:** meaningful partitions cover the bounded target without loading implementation-scale detail into the controller.

## 2. Choose the role

### Explorer

An **explorer** maps one bounded region. It identifies relevant modules, interfaces, callers, dependencies, tests, change signals, and candidate architectural needs. It reports supporting and contrary evidence without selecting a correction.

Use explorers for regions that need mapping before a precise decision-sensitive question exists.

### Probe

A **probe** answers one precise question or tests one hypothesis. Examples include:

- tracing a committed change through every caller;
- checking whether policy is actually duplicated;
- determining whether an interface hides meaningful behavior;
- locating every adapter at a seam;
- testing whether one architectural cause explains several symptoms.

A **challenger probe** independently tries to falsify the strongest candidate or shared-cause explanation.

Use a probe once its question is precise. Prefer it over a broad explorer when one discriminating answer can settle the decision.

**Complete when:** every partition or unknown has the narrowest fitting role.

## 3. Choose the capability

Role and capability are separate. An explorer may perform a mechanical inventory or interpret an ambiguous subsystem; a probe may answer a simple lookup or a consequential causal question.

Classify each work order by:

- ambiguity and inference required;
- number of areas or evidence types to integrate;
- consequence of missed or misread evidence;
- ease of independent verification;
- mechanical volume versus architectural judgment.

Assign the lowest reliable capability:

- **`scan`** — inventories, searches, call-site enumeration, history or test indexing, and other bounded low-ambiguity work with easily checked output;
- **`reason`** — mapping one subsystem, tracing one interaction, reconciling implementation with tests, or evaluating a local causal hypothesis;
- **`judge`** — cross-area synthesis, conflicting authority or evidence, architectural causal attribution, candidate falsification, or reasoning that could authorize consequential change.

Repository size increases partitioned scanning, not the intelligence required for every agent. Split broad mechanical work across `scan` agents and reserve stronger capability for ambiguity, omission risk, consequence, or weak verifiability.

When the harness exposes models, profiles, or reasoning effort, inspect the available choices and map `scan`, `reason`, and `judge` to them. Request an exact assignment only when supported. Verify runtime assignment when observable and material. Otherwise record the requested capability without claiming that a specific model ran.

Escalate or re-probe with stronger capability when:

- coverage is materially incomplete or uncertain;
- applicable authorities conflict;
- evidence from regions disagrees;
- causal inference crosses the assigned boundary;
- the result could change candidate qualification or route selection;
- independent verification is difficult.

When the needed capability is unavailable, narrow the work, retain the decisive reasoning in a capable controller, or expose the resulting evidence limit.

**Complete when:** every assignment has a justified capability and any unobservable or unavailable assignment limit is explicit.

## 4. Dispatch the work order

Every work order must specify:

- **Role:** explorer or probe;
- **Capability:** `scan`, `reason`, or `judge`;
- **Question:** exact result needed by the controller;
- **Scope:** included paths, symbols, history, tests, or interactions;
- **Authority:** applicable requirements, ADRs, standards, and context pointers;
- **Evidence bar:** required inspection or execution and provenance;
- **Counterevidence:** what could disprove the suspected need or cause;
- **Non-goals:** adjacent work left untouched;
- **Stop condition:** observable completion or blocker.

Require this return:

### Reconnaissance Packet

- **Coverage:** inspected scope and material exclusions
- **Evidence:** decision-relevant claims with path, symbol, line, commit, test, or command provenance
- **Counterevidence:** facts weakening the suspected need, cause, or intervention
- **Candidate signals:** supported architectural needs; `none` is valid
- **Unknowns:** gaps whose plausible answers could change the controller's decision
- **Next probe:** smallest discriminating question, or `none`

Return pointers rather than source dumps, raw search logs, or full transcripts. Keep each packet compact enough to compare with the others in controller context.

**Complete when:** each agent returns a bounded packet or an explicit blocker matching its work order.

## 5. Synthesize and stop

Merge packets into a compact evidence map. Group symptoms when one supported architectural cause explains them; preserve independent causes separately. Distinguish a local hotspot, a shared systemic cause, and widespread style disorder.

Inspect decisive source evidence directly before applying the Intervention Gate. Add a probe only when a remaining unknown could change candidate qualification, route selection, migration safety, or verification obligations. Use a challenger probe when the strongest candidate depends on cross-area inference, conflicting packets, or evidence gathered mainly by `scan` agents.

Stop reconnaissance when:

- the bounded target and its material callers, dependencies, tests, and change paths are represented;
- each credible candidate has supporting and contrary evidence;
- every decision-sensitive unknown is resolved or explicitly blocks a disposition;
- additional exploration is unlikely to change the Intervention Gate result.

A healthy mapped target completes reconnaissance; it does not trigger a wider search for another problem. Keep the evidence threshold unchanged when no candidate survives.

Remove task-created reconnaissance artifacts before final completion.

**Complete when:** the controller can apply the Intervention Gate from compact, traceable evidence without a decision-sensitive coverage gap.