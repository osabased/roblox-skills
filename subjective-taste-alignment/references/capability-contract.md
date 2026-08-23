# Host capability contract

Establish this contract for the active host and workspace before profile state or material alignment behavior relies on host facts. A successful parse, a familiar storage path, or a successful implementation is not evidence for a fact the host does not expose.

## Declaration

Declare each capability by its exact identifier. A supported declaration contains a non-empty `mechanism` and one allowed direct `evidence` kind. An unavailable declaration contains a capability-appropriate `fallback`, its required `enforcement`, and a non-empty `preserves` statement that names the protected invariant.

`assess_capabilities` returns `ready=true` only when every capability has a direct mechanism or behavior-preserving fallback and none resolves to `blocker`. This result means the host contract is usable. It does not mean later alignment behavior is implemented or accepted.

| Capability identifier | Fact that must be observable | Allowed direct evidence | Unsafe proxies | Safe fallback examples |
| --- | --- | --- | --- | --- |
| `persistence_durability` | Storage location, durability, lifecycle, and recovery guarantees | `documented_storage_guarantee` | Parse success, path existence, one successful or atomic round trip | Disable persistence or block stateful behavior |
| `revision_detection` | A change identity that can reject stale state | `revision_token`, `content_digest` | File timestamp alone, current parse success | Conflict before write or disable mutation |
| `external_edit_authorship` | Actor identity for edits that may become evidence | `host_authorship_metadata` | File ownership, storage location, valid syntax | Preserve actor as `unknown`; exclude explicit-user interpretation |
| `scope_identity` | Project, session, artifact, and represented-subject identity and lifetime | `host_identity` | Narrow path, current directory, storage lifetime | Keep scope unresolved or checkpoint before reuse |
| `source_addressability` | A reference state that can be retrieved or checked later | `immutable_locator`, `versioned_locator`, `retrievable_snapshot` | URL reachability, source name, current content only | Mark freshness unknown and revalidate; disable pinned reuse |
| `execution_surfaces` | Operations the active host can actually invoke | `callable_surface` | Documented but unavailable tool, inferred command success | Checkpoint or disable the unsupported operation |
| `domain_adapters` | Registered adapters available for the requested medium | `registered_adapter` | Generic text generation, successful unrelated output | Disable unsupported output or report an implementation blocker |

Fallback enforcement is explicit: `unknown` requires `record_unknown`, `unresolved` requires `preserve_unresolved`, `conflict` requires `surface_conflict`, `checkpoint` requires `require_checkpoint`, `disabled` requires `disable_operation`, and `blocker` requires `stop_implementation`.

Fallback validity is capability-specific. Persistence accepts only `disabled` or `blocker`; revision detection accepts `conflict`, `checkpoint`, `disabled`, or `blocker`; authorship accepts `unknown`, `unresolved`, `disabled`, or `blocker`; scope identity accepts `unresolved`, `checkpoint`, `disabled`, or `blocker`; source addressability accepts `unknown`, `unresolved`, `checkpoint`, `disabled`, or `blocker`; execution surfaces accept `checkpoint`, `disabled`, or `blocker`; domain adapters accept only `disabled` or `blocker`.

A fallback protects the affected invariant through its named enforcement. It does not weaken an acceptance criterion. Free-form preservation text without the matching enforcement is a blocker.

## Repository-host baseline

The assessed declaration for this source repository is [host-capabilities.json](host-capabilities.json). Workspace files are writable and Git plus content digests expose revision state. Git history exists only after a commit. The repository does not expose reliable external-edit authorship, so the declaration preserves that actor as `unknown`.

Project identity may use the active repository root while it remains available. Treat session identity as task-local unless the host exposes a stable session identifier. Treat artifact moves, copies, and represented-subject ambiguity as unresolved until later scope behavior defines and verifies them.

Local paths and immutable Git revisions can provide versioned source addressability. Revalidate mutable files and external locators unless the active host supplies a retrievable snapshot or immutable revision. Inspect active tools for execution surfaces and domain adapters on each invocation; never cache assumed tool availability in profile knowledge.

## Completion rule

Report the capability contract blocked when any required row lacks both a valid direct mechanism and a behavior-preserving fallback. Report the full skill incomplete while any later required behavior lacks its own implementation mechanism, fallback, or verification.
