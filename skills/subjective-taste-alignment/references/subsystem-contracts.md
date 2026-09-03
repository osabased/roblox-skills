# Subsystem contracts

These are the observable contracts for the subsystems built on the canonical
alignment core. Each section states what callers may rely on and what the
implementation forbids. Behavior below is verified by the mapped checks in
[acceptance-traceability.md](acceptance-traceability.md).

## Evidence lifecycle

Evidence enters as events carrying implications; claims derive from applicable,
sufficiently represented support. One clear strong explicit statement can
establish a preference; acceptance, execution quality rejection, implementation
success, silence, continued progress, and delegated execution never become
preference or indifference evidence.

- Confidence follows evidence quality and independence, not observation count:
  near-equivalent observations sharing an independence key stay capped;
  genuinely independent corroboration lifts confidence modestly.
- Promotion is proportionate to consequence: inferred support establishes only
  reversible consequences; load-bearing material needs strong explicit strength.
- Comparisons preserve structure: bundles, ranges, boundaries, and relationships
  remain composite claims and are never over-decomposed into item votes.
- Conflicting evidence resolves by relevance and evidentiary strength. Incomparable
  conflicts stay explicitly unresolved with both supports referenced; comparable
  conflicts request a resolution checkpoint scoped to the disputed dimension.
- A later material contradiction demotes established knowledge and records the
  prior support as stale in the support lifecycle; audit history survives.
- Replay of one logical operation is idempotent (`REPLAYED`); distinct events stay
  separate observations. Operation or event identity reuse with altered content
  raises a conflict error instead of mutating state.
- Materially ambiguous observations produce no claim and request clarification
  listing plausible dimensions. “None of these” rejects exactly the explored
  region and invents nothing beyond it.

## Reference behavior

Reference derivations produce scoped style directives that govern alignment as
intent and never become user taste. Explicitly requested properties govern
exactly their requested dimensions; inferred similarities join only with strong
representation, and unobserved dimensions are never manufactured.

- Every derived property records its source identity, revision, provenance tag,
  and canonical dependency key, enabling narrow re-derivation and correction.
- Derivation scope follows the requested work: directives carry the instruction's
  scope, and classification rejects requests that are not reference requests.
- Live and pinned modes behave differently and reject mode-mismatched
  verification. Pinned bindings never follow changed served content; they become
  explicitly unknown and flag their derived claims stale.
- Freshness is `current`, `stale`, or `unknown`. Unverifiable or revision-less
  sources become unknown and block material reuse without revalidation.
- A source change stales exactly its own derived claims. Pinned heritage never
  adopts evolved style; project-consistency origins keep tracking a live binding.

## Autonomy and propagation

Five autonomy presets share identical authority controls yet produce distinct
observable checkpoint contracts; only agent-led grants delegated-authority
propagation. Selecting a preset changes authority scope, intervention threshold,
and checkpoint granularity, and never manufactures preference evidence.

- Runtime preset changes apply prospectively: completed decisions retain their
  alignment, provenance, and route; later sequences inherit the new contract.
- Material commitment passes a propagation-eligibility gate: unresolved
  dimensions, hypothesis-grade routes, and open checkpoint obligations block
  authorization (`authorize_propagation` is the single guard).
- Load-bearing classification uses declared materiality plus reusable, default,
  shared, dependent, expensive, production, grown, and aggregate-direction
  signals so cheap implementations are not under-classified. An aggregate of
  interacting minor assumptions is presumptively load-bearing.
- Eligible routing never bypasses stricter checkpoint obligations without an
  explicit scoped authority change. Delegated authority propagates in-scope
  authorized judgment while taste stays unresolved; delegated judgment and
  craft priors are never preference evidence.
- Ambiguous inferred delegations adopt only the narrowest clearly supported
  option and hold broader readings behind an `extend-authority` checkpoint.
  Cheap reversible choices are reevaluated when reuse, dependencies, aggregate
  direction, or integration makes them load-bearing; choices whose provisional
  basis is not reconstructable are re-resolved, never fabricated.

## Probe selection

Probes exist to resolve named subjective uncertainties before relying on them.

- Selection targets the highest-value uncertainty first; aggregate uncertainties
  outrank equally weighted singles; among sufficient options the cheapest wins.
- A probe must cover the uncertainty's full shape and meet its minimum fidelity;
  shape-missing or low-fidelity probes are rejected rather than trusted.
- When no probe covers the top uncertainty, policy falls back to a clarification
  checkpoint (`resolve-uncertainty`) instead of guessing.
- Known indifference suppresses calibration probing until applicability becomes
  questionable, which reopens the uncertainty.

## Exploration

Exploration and deliberate divergence isolate alternatives without contaminating
established profiles.

- Non-learning divergence runs with learning disabled: starting, picking,
  rejecting, combining, and cleanup emit no evidence transitions and never write
  taste. Sandbox use leaves reusable state unchanged.
- Novelty budgets affect candidate generation only. Cleanup abandons dead ends so
  they can no longer be picked, delegated, combined, or riffed.
- Delegated selections record attribution (`user-delegation`) without taste
  status. Promoting an explored direction submits it to the normal evidence
  model at its own quality: strength and basis decide status, and replays are
  detected as duplicates.

## Reconciliation

Decision-bearing input changes trigger dependency-aware reevaluation through the
canonical reconciliation seam.

- Committing a correction atomically creates pending work exactly for dependents
  whose input dependencies include the corrected input. Dependents reresolve
  against current corrected state; valid observations complete unchanged while
  invalid ones need targeted repair.
- Reconciliation remains explicitly incomplete across interruption: resume
  preserves completed, pending, and unverified statuses without duplication, and
  propagation blocks while affected work is stale or incomplete. Canonical
  serialization round-trips state so committed corrections survive crash or
  restart with obligations intact.
- Superseding corrections merge into existing pending work and rebase remaining
  repairs onto the current basis. Ordinary authority changes record
  prospectively and do not reopen completed work.
- Approved artifacts challenge stored taste only when representation, approval
  semantics, context, scope, attribution, and establishment support comparison;
  contradictions reopen alignment and queue dependent work, deliberate
  exceptions and context changes classify distinctly, and challenge replay is
  idempotent.
- Whole-system coherence is checked separately from local approvals at
  integration points (`enforce_relational_alignment`): individually approved
  decisions that relationally drift surface as conflicts with unresolved
  dimensions, blocked propagation, and resolve-relation checkpoints.

## Profile controls and lifecycle operations

Users can inspect and control their profiles; `apply_lifecycle_operation` is the
only validated write path for lifecycle change.

- Inspection exposes knowledge facets verbatim — relationships, evidence ids,
  provenance — and separately reports excluded and unresolved knowledge without
  flattening conditionals.
- Corrections and direct edits carry actor provenance: user instructions become
  exactly one instruction event and one claim (persistence is not a second
  observation); protected fields such as confidence reject edits; agent and
  unknown authorship persists as inspectable history and never becomes user
  evidence; evidence resurrection or suppression outside validated management
  fails.
- Targeted reset excludes only the supported links, keeps sibling claims and
  audit history, and cannot be resurrected by reingestion; relearning derives
  only from genuinely new evidence. Retraction removes derived claims while
  retaining raw events. Undo restores prior state exactly without touching
  external artifacts.
- Branches register inertly with ancestry and provenance, become applicable only
  through explicit activation, validate all branch references against the
  registry, and keep branch-originated claims isolated from parent and siblings
  while broader evidence records its origin branch.
- Import/export round-trips semantics and boundaries; imports recompute inflated
  confidence from evidence, drop fabricated provenance, and reject structurally
  tampered documents. Importing into a moved-on state union-merges all evidence
  ledgers with local-first precedence instead of replacing them: locally
  excluded supports keep suppressing imported properties that cite them, and an
  event id reused with divergent content is an identity conflict, not a silent
  merge. Applied-operation marker ids are device-local, so collisions resolve
  to the retained local marker while any replay against it still raises.
  Migration maps missing epistemic fields to conservative
  unknown values and refuses newer schema versions. Consolidation merges near
  duplicates conservatively (lower confidence, unioned provenance) and refuses
  contextually distinct profiles or different represented subjects.
- External edits to derived confidence or provenance cannot manufacture
  certainty anywhere in this pipeline.

## Stakeholder ownership

Stakeholder requirements stay separate from user preference.

- Stakeholder-owned knowledge never merges into user taste: composition excludes
  it by represented-subject mismatch and consolidation refuses subject mixing.
- Ownership grants (with explicit basis) convert stakeholder signals into
  governing directives; identical roles resolve by agreements, not a universal
  hierarchy. Signals without grants cannot override the applicable owner.
- Hard constraints bound the decision space before ownership resolves. Ambiguous
  ownership produces propagation holds and requires an ownership checkpoint
  before load-bearing work. Grant revocation stales affected alignment and
  reconciles only actual dependents; approving stakeholder-owned work is not
  personal-taste evidence.

## Domain adapter contracts

Domain adapters prove the common contract across media while preserving
medium-specific policy.

- Adapters exist only for supported domains; constructing one for an unknown
  domain kind raises immediately.
- Local metadata, medium descriptions, and input ordering cannot change core
  outcomes: revisions, directions, reasons, checkpoints, eligibility, and
  provenance depend only on canonical inputs. Only canonical input changes move
  outcomes, and only along the affected dimension.
- Adapter authorization is exactly the canonical guard: unresolved dimensions
  block, settled results pass, stale decision-bearing states raise.
- Governing precedence ranks constraints above intent above craft priors. Craft
  priors without taste or authority leave dimensions unresolved with advisory
  data and checkpoints; delegated authority lets craft execute while taste stays
  absent.
- Probes come from the shared contract with medium-specific constructions
  (contrast pairs, excerpt ABs, timing-curve previews) bound to canonical probe
  decisions; uncoverable uncertainties fall back identically to clarification
  checkpoints with propagation blocked across all domains. “No animation” and
  similar null outcomes propagate cleanly without manufactured preference.
