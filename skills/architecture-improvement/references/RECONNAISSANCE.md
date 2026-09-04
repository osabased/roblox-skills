# Delegated Reconnaissance

Use this branch when a large or unfamiliar target would materially consume the controller's context, or when parallel independent inspection materially improves coverage.

Gather enough applicable evidence for the Intervention Gate while preserving controller context for synthesis, design, implementation, and verification.

## Controller

The controller owns:

- target, search boundaries, and capability routing;
- synthesis, causal reconciliation, qualification, and falsification;
- intervention authorization and route selection;
- every source write and final conclusion.

The active controller must be `judge`-capable: able to reconcile cross-area evidence, attribute architectural causes, falsify candidates, and authorize consequential change. Switch to the strongest available judge-capable controller profile before reconnaissance when necessary. When the harness cannot switch, narrow the target until the active controller can judge it reliably or return `BLOCKED` with the capability limit.

Delegated agents are read-only with respect to repository source. They may run safe inspection or diagnostic commands within the assigned blast radius and return evidence packets. Stronger delegates can supply and challenge evidence; only the controller authorizes scope changes, further delegation, interventions, and writes.

A packet is evidence input, not a finding. Verify every decisive delegated claim directly or through applicable independent corroboration before it can pass the Intervention Gate.

## 1. Partition and route

Perform a cheap topology pass over repository instructions, layout, manifests, domain documents, ADRs, standards, recent and current changes, test entry points, and available dependency or symbol indexes.

Partition by architectural responsibility, seam, change path, or dependency region. Use the smallest set that covers materially different areas, and parallelize only independent partitions.

Choose the narrowest fitting role:

- **Explorer** — maps one bounded region: modules, interfaces, callers, dependencies, tests, change signals, and supporting or contrary evidence. It does not select a correction.
- **Probe** — answers one precise decision-sensitive question or tests one hypothesis.
- **Challenger probe** — independently tries to falsify the strongest candidate or shared-cause explanation.

Use explorers before the unknown is precise. Use probes once one discriminating answer can settle it.

Assign the lowest reliable capability:

- **`scan`** — inventories, searches, call-site enumeration, history or test indexing, and other low-ambiguity work with easily checked output;
- **`reason`** — maps one subsystem, traces an interaction, reconciles implementation with tests, or evaluates a local causal hypothesis;
- **`judge`** — handles cross-area synthesis, conflicting authority or evidence, architectural causality, candidate falsification, or analysis that materially informs consequential change.

Choose capability from ambiguity, evidence integration, omission consequence, independent verifiability, and mechanical volume. Repository size increases partitioned scanning, not every agent's intelligence. Raise capability when coverage is uncertain, authorities or packets conflict, causal inference crosses the assigned region, the result could change qualification or route selection, or independent verification is difficult.

Map `scan`, `reason`, and `judge` to the models, profiles, or reasoning effort the harness actually exposes. Request an exact assignment only when supported. Verify runtime assignment when observable and material; otherwise record the requested capability without claiming a specific model ran.

When the required capability is unavailable, narrow the work, retain decisive reasoning in a capable controller, or expose the evidence limit.

**Complete when:** meaningful partitions cover the target and every assignment has a justified role, capability, and explicit assignment limit.

## 2. Dispatch and collect

Give each agent a fresh bounded work order containing:

- **Role and capability**
- **Question:** exact result needed
- **Scope:** included paths, symbols, history, tests, or interactions
- **Authority:** applicable requirements, ADRs, standards, and context pointers
- **Evidence bar:** required inspection or execution and provenance
- **Counterevidence:** what could disprove the suspected need or cause
- **Non-goals:** adjacent work left untouched
- **Stop condition:** observable completion or blocker

Require this return:

### Reconnaissance Packet

- **Coverage:** inspected scope and material exclusions
- **Evidence:** decision-relevant claims with path, symbol, line, commit, test, or command provenance
- **Counterevidence:** facts weakening the suspected need, cause, or intervention
- **Candidate signals:** supported architectural needs; `none` is valid
- **Unknowns:** gaps whose plausible answers could change the controller's decision
- **Next probe:** smallest discriminating question, or `none`

Prefer paths, symbols, commands, requirements, and questions over copied source in the work order. Return pointers instead of source dumps, raw search logs, or full transcripts. Detailed notes may live in a shared temporary artifact, but each packet must remain compact enough to compare in controller context.

**Complete when:** each assignment returns a bounded packet or an explicit blocker matching its work order.

## 3. Synthesize and stop

Merge packets into a compact evidence map. Group symptoms when one supported architectural cause explains them; preserve independent causes separately. Distinguish a local hotspot, a shared systemic cause, and widespread style disorder.

Inspect decisive source evidence directly before applying the Intervention Gate. Add a probe only when a remaining unknown could change qualification, route selection, migration safety, or verification obligations. Use a challenger probe when the strongest candidate depends on cross-area inference, conflicting packets, or evidence gathered mainly by `scan` agents.

Stop when:

- the target and its material callers, dependencies, tests, and change paths are represented;
- each credible candidate has supporting and contrary evidence;
- every decision-sensitive unknown is resolved or explicitly blocks a disposition;
- additional exploration is unlikely to change the Intervention Gate result.

A healthy mapped target completes reconnaissance. It does not trigger a wider search, and the evidence threshold remains fixed when no candidate survives.

Remove task-created reconnaissance artifacts before final completion.

**Complete when:** the controller can apply the Intervention Gate from compact, traceable evidence without a decision-sensitive coverage gap.