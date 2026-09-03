# Profile persistence contract

Use `ProfilePersistence` as the only profile storage mutation seam. Its logical
state is `ProfileState`; storage adapters only retain complete canonical bytes and
an optimistic content revision. Persistence does not derive, compose, strengthen,
or reinterpret preference knowledge.

## Canonical state and exchange

Schema version `1` stores these complete values:

- `ProfileState`: `profile_id`, `schema_version`, profile properties, authority
  grants, and reference sources.
- `ProfileProperty`: claim and section identity, explicit overrides, owner,
  evidence applicability, relational requirements, and its complete
  `PreferenceKnowledge`.
- `PreferenceKnowledge`: dimension, direction, disposition, epistemic basis,
  confidence, strength, scope identity and represented subject, context, evidence
  identities, provenance, validation context, and relationships.
- `AuthorityScope`: actor, covered dimensions, propagation and checkpoint controls,
  scope, and provenance. Authority remains separate from preference evidence.
- `ReferenceSource`: reference and source identity, locator, live/pinned mode,
  current/stale/unknown freshness, optional source revision, derived claim
  identities, and provenance.

`serialize_profile_state` produces deterministic UTF-8 JSON with sorted object
keys, compact separators, finite standard JSON numbers, and one trailing newline.
It validates the complete canonical state before returning bytes.
`deserialize_profile_state` rejects invalid UTF-8, duplicate fields, unknown or
missing fields, invalid types, non-finite numbers, unsupported enum values,
duplicate claim/reference identities, malformed relationships, invalid canonical
model combinations, and unsupported schema versions. It constructs and validates
the entire document before returning any `ProfileState`. There is no partial-load
result.

Schema version `1` has no implicit migration. A different version raises
`UnsupportedSchemaVersionError`; callers must use a separately validated migration
before load. Missing epistemic fields never receive invented defaults.

## Snapshot and mutation protocol

`ProfilePersistence.load()` returns `None` for absent state or one
`ProfileSnapshot(state, revision, authorship)`. The revision is
`sha256:<canonical-byte-digest>` for the exact stored representation.

Every save supplies `expected_revision`:

- `None` means that no document may exist.
- A revision means that exact representation must still be current.

The adapter compares the current revision and replaces the document as one
operation. A mismatch raises `RevisionConflictError`; it never writes the proposed
state. When the current document is valid, the error contains its fully restored
`current` snapshot so the caller can reload, reconcile, or ask for resolution.
When the current document is invalid, `current` is `None` and
`current_validation_error` describes the whole-document failure. The invalid bytes
remain untouched for explicit recovery; they are never partially incorporated.

Retry only after reloading and deliberately reconciling against the returned
revision. Do not retry a stale write with a newly copied revision, because that
would discard the conflict instead of resolving it.

## Authorship boundary

`MutationAuthorship` describes the storage mutation separately from evidence
provenance. `attributable=True` is valid only when the host directly establishes
the actor. Unattributable mutations must use actor `unknown`.

The repository filesystem has no trustworthy external-edit authorship metadata.
Consequently, every document read through `AtomicFileProfileStorage` receives
`UNKNOWN_EXTERNAL_AUTHORSHIP`, including a valid out-of-band change returned in a
conflict. Self-asserted fields inside an edited JSON document do not change that
outer authorship. A controlled save may return its supplied attributable authorship
for the current operation, but a later file reload returns unknown. Persistence
authorship is not additional preference evidence.

`InMemoryProfileStorage` can retain supplied authorship because its mutations pass
through the controlled adapter instance. Its default safe save authorship is
unknown; callers must not label a mutation as user-authored without direct host
evidence.

## Atomic file behavior and recovery

`AtomicFileProfileStorage` implements the byte adapter with these steps under a
per-path thread lock and an operating-system file lock for cooperating processes:

1. Read and compare the expected content revision.
2. Write the complete new representation to a unique same-directory temporary
   file, flush it, and `fsync` it.
3. Compare the target revision again so an external change observed during the
   write becomes a conflict.
4. Atomically replace the target with `os.replace`.
5. Flush directory metadata where the host exposes directory `fsync`, then verify
   the target digest again before reporting success.

Therefore, failure or interruption before replacement leaves the complete previous
document. Failure or interruption after replacement leaves the complete new
document. A temporary file abandoned by an interruption is never promoted; the
next adapter read or write removes it while preserving the target. The stable lock
sidecar is coordination state, not profile state.

`FileWriteStage.TEMP_DURABLE`, `REPLACEMENT_VISIBLE`, and `COMMIT_DURABLE` are
explicit test hooks. Injected failure and interruption scenarios must demonstrate
that a fresh adapter restores exactly the old or new complete state and that scope,
provenance, uncertainty, ownership, represented subject, authority, reference
freshness, and unknown actor state remain unchanged.

External writers should use the same persistence seam. The adapter also performs
content comparisons before replacement and before success to surface observed
non-cooperating external changes. No filesystem path, parse success, or JSON actor
field is treated as proof of authorship.
