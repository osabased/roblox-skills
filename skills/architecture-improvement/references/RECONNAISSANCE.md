# Delegated Reconnaissance

Use this branch when the bounded target is too large or unfamiliar for the controller to map directly without materially consuming its context, or when parallel independent inspection materially improves coverage.

The goal is not maximal exploration. It is enough applicable evidence for the intervention gate while preserving the controller's context for synthesis, design, implementation, and verification.

## Control boundary

The controller owns:

- target and search boundaries;
- capability routing;
- synthesis and causal reconciliation;
- candidate qualification and falsification;
- intervention authorization and route selection;
- every write and final conclusion.

Delegated agents are read-only unless later work separately authorizes writes. They may not widen scope, authorize an intervention, or recursively delegate without the controller's explicit instruction.

A delegated report is an evidence packet, not a finding. The controller must verify decisive claims directly or through applicable independent corroboration before a claim can pass the intervention gate.

## Protect the controller context

Before dispatching agents, perform only a cheap topology pass: repository instructions, directory and package structure, manifests, domain documents, ADRs, recent history, current changes, test entry points, and available dependency or symbol indexes.

Partition work by meaningful architectural responsibility, seam, change path, or dependency region. Do not assign arbitrary equal file ranges or one agent per directory.

Give each agent a fresh, bounded work order containing only the context pointers it needs. Prefer paths, symbols, commands, requirements, and questions over copied source. When the harness supports shared artifacts, place detailed notes outside the repository and return a compact evidence index; otherwise return the compact index directly. Do not import raw search logs, source dumps, or full delegated transcripts into the controller context.

Clean up task-created reconnaissance artifacts before completion.

## Delegation roles

Use the smallest set of agents that covers materially different areas.

### Explorer

An explorer maps one bounded region. It identifies relevant modules, interfaces, callers, dependencies, tests, change signals, and candidate architectural needs. It reports supporting and contrary evidence without selecting a correction.

Use parallel explorers for independent regions whose results do not depend on one another.

### Probe

A probe answers one decision-sensitive question or tests one hypothesis. Examples include tracing a specific change across callers, checking whether policy is actually duplicated, testing whether an interface hides behavior, locating every implementation of a seam, or determining whether a suspected cause explains several symptoms.

Use probes after the map exposes a precise unknown. A challenger probe is an independent attempt to falsify the strongest candidate or shared-cause explanation.

Do not dispatch a broad explorer when a narrow probe can settle the decision, or a probe before its question is precise.

## Capability routing

Role and capability are separate. An explorer may need little reasoning for an inventory or strong reasoning for an ambiguous subsystem; a probe may be mechanical or judgment-heavy.

Classify each work order by:

- ambiguity and inference required;
- number of areas or evidence types that must be integrated;
- consequence if relevant evidence is missed or misread;
- ease of independently verifying the result;
- mechanical volume versus architectural judgment.

Map the task to the lowest capability profile that can reliably satisfy it:

- **`scan`** — inventories, searches, call-site enumeration, history or test indexing, and other bounded low-ambiguity work with easily checked outputs;
- **`reason`** — mapping one subsystem, tracing one interaction, reconciling implementation with tests, or evaluating a local causal hypothesis;
- **`judge`** — cross-area synthesis, conflicting authority or evidence, architectural causal attribution, candidate falsification, or comparisons whose answer can authorize consequential change.

Repository size increases the amount of partitioned scanning, not automatically the intelligence required for every agent. Split broad mechanical work rather than assigning it wholesale to the strongest profile. Raise capability when ambiguity, omission risk, consequence, or weak verifiability increases.

When the harness exposes agent profiles, models, or reasoning effort, inspect the available choices and map `scan`, `reason`, and `judge` to them. Request an exact profile only when the harness supports it. Verify the assigned model or effort from runtime metadata when available and when a mismatch could affect the result. When assignment cannot be observed or controlled, state the requested capability without claiming that a specific model ran.

If the needed capability is unavailable, narrow the work until an available agent can perform it reliably, perform the decisive reasoning in the controller, or report the resulting evidence limit. Never treat an unverified low-capability result as sufficient merely because it is the only result available.

Escalate a delegated task or re-probe with a stronger profile when:

- the agent reports material uncertainty or incomplete coverage;
- applicable authorities conflict;
- evidence from different regions disagrees;
- causal inference crosses the assigned boundary;
- the result could materially change candidate qualification or route selection;
- independent verification is difficult.

## Work-order contract

Every delegated work order must specify:

- **Role:** explorer or probe;
- **Capability:** `scan`, `reason`, or `judge`;
- **Question:** exact result needed by the controller;
- **Scope:** included paths, symbols, history, tests, or interactions;
- **Authority:** applicable requirements, ADRs, standards, and context pointers;
- **Evidence bar:** what must be inspected or executed and how provenance is recorded;
- **Counterevidence:** what could disprove the suspected need or cause;
- **Non-goals:** adjacent work the agent must leave untouched;
- **Stop condition:** observable condition that completes or blocks the assignment.

Require this compact return:

### Reconnaissance packet

- **Coverage:** inspected scope and material exclusions
- **Evidence:** decision-relevant claims with path, symbol, line, commit, test, or command provenance
- **Counterevidence:** facts weakening the suspected need, cause, or intervention
- **Candidate signals:** supported architectural needs only; `none` is valid
- **Unknowns:** only gaps whose plausible answers could change the controller's decision
- **Next probe:** smallest discriminating question, or `none`

Return pointers rather than copied code. Detailed notes may live in a shared temporary artifact, but the packet must remain compact enough to compare with other packets in the controller context.

## Synthesis and stopping

The controller merges packets into a compact evidence map. Group symptoms when one supported architectural cause explains them; preserve independent causes separately. Distinguish a local hotspot, a shared systemic cause, and widespread style disorder.

Inspect decisive source evidence directly before passing the intervention gate. Use another probe only when a remaining unknown could change candidate qualification, the selected route, migration safety, or verification obligations. Use a challenger probe when the strongest candidate depends on cross-area inference, conflicting reports, or evidence gathered mainly by `scan` agents.

Stop reconnaissance when:

- the bounded target and its material callers, dependencies, tests, and change paths are represented;
- each credible candidate has supporting and contrary evidence;
- every decision-sensitive unknown is resolved or explicitly blocks a supported route;
- additional exploration is unlikely to change the intervention-gate result.

Do not widen to find another problem after the selected target is adequately mapped, and do not lower the evidence bar because delegated exploration found no candidate.
