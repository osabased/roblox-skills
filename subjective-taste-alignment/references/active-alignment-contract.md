# Active-alignment contract

Use `resolve_alignment` from `scripts/alignment_harness.py` as the one semantic path for a subjective decision. Supply only decision-bearing state whose scope and applicability the caller has established through [profile-composition-contract.md](profile-composition-contract.md) when reusable profile knowledge is involved.

## Canonical state

`PreferenceKnowledge` keeps these facts independent:

- `disposition`: `preferred`, `rejected`, `indifferent`, or `unresolved`;
- `basis`: `explicit` or `inferred`;
- epistemic `confidence` and preference `strength`;
- scope and represented subject;
- decision context, evidence identifiers, provenance, and validation context;
- conditional or relational knowledge.

High strength does not increase confidence. High confidence does not increase strength. `derived_label` presents confirmed preference, strong inference, weak hypothesis, rejected direction, known indifference, or unresolved dimension as a view over canonical state; it is never an independent input. Consequence-sensitive evidence gating belongs to the later propagation-policy contract and must not be replaced here by a universal confidence threshold. Until that policy exists, a material direction governed only by taste remains resolved but receives an `assess-propagation:<dimension>` checkpoint and is not eligible for downstream propagation. A resolved implementation direction never mutates the supplied preference object.

`AlignmentRequest` has separate collections for taste, intent, constraints, stakeholder ownership or requirements, authority, experimental state, craft priors, and provisional agent judgment. Do not translate one category into another to make resolution succeed.

## Per-dimension resolution

The resolver preserves all applicable sources on each `ResolvedDimension` and identifies the governing source and reason. It applies these semantic rules within one dimension:

1. a hard constraint determines the feasible direction;
2. an applicable owner direction governs an owned dimension;
3. explicit artifact or project intent governs only the dimension it names;
4. a deliberate temporary or sandbox direction governs execution without changing taste;
5. applicable preferred taste governs remaining subjective freedom; known indifference skips preference calibration and permits an authorized execution choice without creating taste;
6. an in-scope agent authority grant may use provisional judgment;
7. an in-scope agent authority grant may use a craft prior for otherwise unresolved execution detail;
8. otherwise the dimension remains unresolved.

This is a semantic resolution policy, not a universal scope hierarchy. `compose_profiles` must establish which scoped inputs are applicable before calling this contract.

Two incompatible values from the same governing semantic source produce `governing_source="conflict"`; the dimension remains unresolved. A conflict in a lower-priority source remains visible in `ResolvedDimension.inputs` and `conflicts` but does not override a valid higher-priority governing source. The resolver does not average or silently select between incompatible inputs.

The result exposes materiality, unresolved dimensions, propagation eligibility, checkpoint obligations, governing provenance, downstream dependency identifiers, and a digest of all decision-bearing request state. Authority or craft provenance can authorize execution, but it is not taste evidence.

## Propagation guard

Call `authorize_propagation(result, current_request)` immediately before downstream material use. Revision identity includes only the requested dimensions and their applicable authority state, so unrelated inputs do not invalidate the result. The guard rejects:

- a result whose decision-bearing digest differs from the current request; or
- a result with unresolved dimensions or active checkpoint obligations.

After a stale rejection, rebuild the request from current state and call `resolve_alignment` again. Do not copy the old direction into a new result or reuse the old revision identity.

When composed profile knowledge carries relational requirements, follow [profile-composition-contract.md](profile-composition-contract.md): it specifies how the request consumes the composition result and how `enforce_relational_alignment` wraps resolution before the propagation guard above.
