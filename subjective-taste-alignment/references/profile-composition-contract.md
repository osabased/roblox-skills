# Profile composition contract

Use `compose_profiles` from `scripts/alignment_harness.py` before building an `AlignmentRequest` from reusable profile knowledge. The composition module establishes applicability; the active-alignment module decides which semantic source governs each dimension.

## Inputs

Create one `CompositionTarget` with the active represented subject, observable scope identities, domain, decision context, validation conditions, domain-exposed properties, and known property owners. A stored profile or authority scope is historical unless its exact identity is active in the target.

Wrap each canonical `PreferenceKnowledge` value in `ProfileProperty`. Keep its section, stable claim identity, evidence applicability, declared owner, and explicit claim-level overrides. Use `ProfileSelection` as follows:

- omit both fields for full-profile application;
- set `sections` for section application;
- set `properties` for exact property application;
- set `scopes` to select exact active scope identities for this application without hiding other active identities from history or inspection.

For intentional cross-domain reuse, supply a `TransferPolicy` that names each allowed source domain and a confidence factor below `1`. Set `allow_distant_context` for intentional same-domain reuse outside validated devices, audiences, or interaction conditions. The module keeps the original knowledge unchanged. A transfer applies only when the policy explicitly covers its domain or distant-context case, and always reduces effective confidence.

## Result

`CompositionResult` keeps each result view distinct:

- `properties` contains semantically compatible, applicable knowledge grouped by section and property, including known indifference and unresolved knowledge;
- `conflicts` retains incompatible inputs without averaging or silently selecting one;
- `excluded` retains historical or inapplicable inputs with an observable reason;
- `overridden` retains each applicable claim suppressed by an explicit claim-level override and identifies the governing claim;
- `provenance` identifies the sources of composed properties;
- `alignment_dimensions` returns every composed, relationally required, and conflicted dimension through `PropertyPath.alignment_dimension`;
- `alignment_taste` returns applicable knowledge with transfer confidence adjustments and section-qualified dimensions applied, ready for `AlignmentRequest.taste`;
- `alignment_authority` returns only grants whose represented subject and exact scope identity are active;
- `excluded_authority` retains inactive grants for history.

Compatible properties keep every contributing claim, provenance record, context, and relationship. Attach a typed `RelationalRequirement` to a `ProfileProperty` for each direction that another section/property must provide. Explicit overrides suppress only the named applicable claims. Scope narrowness, storage location, weak inference, or successful use never creates override authority.

Build the canonical `AlignmentRequest` with `dimensions=composition.alignment_dimensions` and `context_revision=composition.context_revision(host_revision)`. Derive interacting intent, constraint, ownership, authority, and other semantic-input dimensions from the same `PropertyPath.alignment_dimension` property instead of assembling dimension strings manually. Ordinary components render as `section.property`; literal `%` and `.` characters inside either component are percent-escaped so distinct paths cannot collide. Then resolve the request and call `enforce_relational_alignment(composition, alignment)`. The combined revision makes a changed relationship stale even when its preference direction is unchanged. Any host-revision change raises the combined revision for every composed request, including requests whose composition carries no `RelationalRequirement`; non-relational callers accept this host-revision sensitivity as part of one uniform freshness rule. Relational enforcement applies a conditional requirement only when that taste property governs its dependent dimension; explicit intent, constraints, or ownership on the dependent dimension remain authoritative. Each requirement is evaluated against the full resolved semantic state rather than direction text from a single profile source. A required direction may be satisfied by intent, ownership, or another valid governing source, while rejected taste cannot satisfy it. Enforcement repeats to a fixed point so invalidation propagates through relationship chains. Use its returned `alignment` for `authorize_propagation`. A violated or unresolved requirement marks the dependent dimension unresolved, records an explicit relational conflict, and blocks propagation.

Any conflict that affects a requested dimension remains unresolved. Resolve it through current intent, ownership, evidence, or a checkpoint before material propagation.

## Local identity transitions

Call `transition_local_scope` when duplicate, branch, copy, or move behavior can change a local artifact identity. Supply an observable `ScopeTransition` outcome:

- `preserve` retains the exact source identity;
- `replace` creates knowledge under a new target identity while retaining the source record;
- `ambiguous` creates no target-scoped knowledge and returns a checkpoint.

The caller must derive this outcome from host-supported identity semantics or an explicit user operation. An unknown outcome stays ambiguous.
