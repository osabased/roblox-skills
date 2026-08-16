# Resource Evaluation Rubric

Use evidence, not vibes. Scores help compare candidates but do not override hard blockers.

## Hard gates

A candidate cannot be selected when any applicable hard gate fails:

- **Fit:** cannot meet the required behavior.
- **Evaluability:** behavior/source needed for safe adoption cannot be inspected or tested.
- **Compatibility:** known incompatibility with required Roblox/project behavior.
- **Safety:** unacceptable client/server trust, credential, remote-code, or asset-script risk for the use case.
- **Legitimacy:** usage/license terms clearly disallow the intended adoption.
- **Proof:** required behavior fails reproducibly in an isolated test.

Unknown is not automatically failure, but a material unknown must be resolved before a newly discovered resource earns verified-acquisition trust. Curated resources already have policy trust; unresolved facts still limit what can truthfully be called verified.

## Weighted comparison

Score each 0-5 and multiply by the weight. Choose the relevant criteria once from the acquisition brief, then score every candidate against that same set; do not drop a weak criterion for only one candidate. When criteria are omitted, compare normalized score (`earned weighted points / maximum weighted points for the selected criteria`) rather than raw totals.

| Criterion | Weight | What good evidence looks like |
|---|---:|---|
| Requirement fit | 5 | Directly solves the brief without major unrelated machinery |
| Correctness evidence | 5 | Reproducible tests, clear source behavior, credible issue history |
| Integration cost | 4 | Simple install, limited project assumptions, reversible adoption |
| Maintenance/currentness | 4 | Recent compatible releases/commits, maintained docs, responsive fixes |
| API/documentation quality | 3 | Public API and lifecycle are explicit and match source |
| Security posture | 5 | Server authority preserved, no suspicious loaders/credential practices |
| Dependency burden | 3 | Small, justified dependency graph with understandable transitive behavior |
| Testability | 4 | Can be isolated and meaningfully validated |
| Performance fit | 2 | Evidence matches the project's actual scale; benchmarks are reproducible/relevant |
| Portability/lock-in | 2 | Resource can be replaced without infecting unrelated architecture |

Adjust performance upward only when performance is genuinely a requirement.

## Evidence strength

Prefer roughly in this order:

1. Direct executable test in the target environment.
2. Source code + official/canonical documentation.
3. Maintainer release notes/issues/tests.
4. DevForum maintainer post and discussion.
5. Independent user reports.
6. Popularity signals.

Popularity is discovery evidence, not correctness evidence.

## Tie-breakers

When two candidates are close, prefer:

1. smaller conceptual/integration surface;
2. stronger testability;
3. clearer lifecycle and failure behavior;
4. fewer security-sensitive behaviors;
5. easier removal/replacement;
6. more current maintenance evidence.

Do not prefer additional features that the acquisition brief does not need.
