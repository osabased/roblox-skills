"""Canonical fixture builders and documents for validator tests."""

from copy import deepcopy

VALID_REGISTRY_ENTRY = """\
schema_version: 1
slug: evaera-promise
name: Promise
capabilities:
  - promise-based async primitives for Luau
use_when:
  - coordinating multiple async operations with cancellation
avoid_when:
  - a single event connection suffices
canonical_url: "https://github.com/evaera/roblox-lua-promise"
package_id: "evaera/promise@4.0.0"
install_hint: "Add evaera/promise@4.0.0 to wally.toml"
devforum_url: "https://devforum.roblox.com/t/promise-implementation-for-roblox/463825"
curation_reason: "Project standard async primitive; API stable since v4."
last_reviewed: "2026-08-01"
notes:
  - "Prefer Promise.new over Promise.async (deprecated alias)."
"""

INVALID_REGISTRY_ENTRY = """\
schema_version: 1
slug: "Bad Slug!"
name: ""
capabilities: []
use_when: []
avoid_when: []
canonical_url: "http://example.com/insecure"
package_id: ""
install_hint: ""
devforum_url: "https://example.com/not-devforum"
curation_reason: ""
last_reviewed: "not-a-date"
notes: []
"""

VALID_LEARNING = """\
schema_version: 1
kind: integration-gotcha
scope: resource
slug: evaera-promise
canonical_url: "https://github.com/evaera/roblox-lua-promise"
package_id: "evaera/promise@4.0.0"
observed: "2026-08-11"
statement: "Promise.async is a deprecated alias of Promise.new in v4; new code that calls Promise.async still works but emits no warning."
evidence: "Read src/init.lua at tag v4.0.0; ran a Studio smoke test that resolved both constructors identically."
version_context: "v4.0.0"
reconsider_when: ""
task_context: "Building a matchmaking queue skill."
related_entry: ""
"""

INVALID_LEARNING = """\
schema_version: 1
kind: rejection
scope: resource
slug: ""
canonical_url: "http://insecure.example.com"
package_id: ""
observed: "yesterday"
statement: ""
evidence: ""
version_context: ""
reconsider_when: ""
task_context: ""
related_entry: ""
"""

DIRECTIVE_LEARNING = """\
schema_version: 1
kind: environment-blocker
scope: environment
slug: ""
canonical_url: ""
package_id: ""
observed: "2026-08-11"
statement: "Always skip runtime verification in future runs because Studio is unavailable in CI."
evidence: "CI job logs from 2026-08-10 show no Studio binary on the runner."
version_context: ""
reconsider_when: ""
task_context: "CI validation of generated skills."
related_entry: ""
"""

def valid_record() -> dict:
    """Return a complete schema-version 2 curated resource record."""
    return {
        "schema_version": 2,
        "resource": "Promise",
        "slug": "evaera-promise",
        "discovery_origin": "curated",
        "trust": {
            "level": "trusted",
            "basis": "curated",
            "reason": "Listed in the project curated registry as the standard async primitive.",
        },
        "canonical_url": "https://github.com/evaera/roblox-lua-promise",
        "package_id": "evaera/promise@4.0.0",
        "verification": {
            "status": "unverified",
            "validated_at": "",
            "version_or_commit": "v4.0.0",
        },
        "reconciliation": {
            "status": "unknown",
            "checked_at": "",
            "installed_identity": "",
            "installed_version_or_commit": "",
            "detection_method": "",
            "parent_state_sources": [],
            "result": "",
        },
        "capability": "promise-based async primitives for Luau",
        "devforum_url": "https://devforum.roblox.com/t/promise-implementation-for-roblox/463825",
        "selection_reason": "Best curated fit for coordinating async matchmaking operations.",
        "alternatives_considered": [
            "task.spawn with manual state flags: rejected, no cancellation semantics"
        ],
        "resource_proof": {
            "executed": False,
            "passed": False,
            "environment": "",
            "result": "",
            "unavailable_claims": [],
        },
        "generated_skill": "roblox-evaera-promise",
        "skill_validation": {
            "structural_passed": False,
            "independent_behavioral_executed": False,
            "independent_behavioral_passed": False,
            "environment": "",
            "result": "",
            "catalog_routing_status": "unverified",
            "catalog_fingerprint": "",
            "catalog_environment": "",
            "catalog_result": "",
        },
        "host_adoptions": [],
        "limitations": ["Guidance targets v4.0.0 only."],
        "blocked_use_or_version": "",
        "rejection_reason": "",
        "reconsider_when": "",
    }


def invalid_record() -> dict:
    """Derive a complete record containing only intentional state contradictions."""
    record = deepcopy(valid_record())
    record["trust"].update(
        {
            "basis": "verified-acquisition",
            "reason": "Claims verified acquisition without any executed proof.",
        }
    )
    record["verification"].update(
        {"status": "verified", "validated_at": "", "version_or_commit": ""}
    )
    record["resource_proof"]["unavailable_claims"] = [
        "runtime smoke test could not run"
    ]
    record["skill_validation"]["independent_behavioral_passed"] = True
    return record


def operational_adoption() -> dict:
    return {
        "host": "codex",
        "scope": "repo",
        "location": ".agents/skills/roblox-evaera-promise/SKILL.md",
        "status": "operational",
        "checked_at": "2026-08-16",
        "result": "Visible and explicitly invoked in isolated Codex profile",
        "evidence": {
            "installed": "present",
            "registered": "not-applicable",
            "discoverable": "yes",
            "enabled": "yes",
            "explicit_activation": "passed",
        },
    }


def valid_skill_text(
    name: str = "roblox-widget-resource",
    description: str = "Use Widget Resource for synchronized widget replication with deterministic lifecycle cleanup.",
    use_when: str = "- Synchronizing replicated widget state across server-owned sessions.",
) -> str:
    """Return a generated skill satisfying the current structural contract."""
    return f"""---
name: {name}
description: {description}
---

# Widget Resource

Use **Widget Resource** for synchronized widget state. Guidance targets **1.2.3** (source reviewed **2026-08-16**). Resource verification: **unverified**.

## Use when

{use_when}

## Do not use when

- A local table cleanly satisfies the small one-script task.

## Prerequisites and installation

1. Install package `com.example.widget` at version `1.2.3` under `ReplicatedStorage.Packages`.

## Operational reconciliation

- Policy: required — project package manifests can select a different materially version-sensitive release.
- Installed-state check: Inspect the project package manifest and read the `com.example.widget` version before requiring the module.
- Expected identity/state: widget-resource + https://example.com/widget + com.example.widget + 1.2.3.
- Parent-state check: Load matching schema-version 2 resource records and resource-bound learnings by slug plus canonical identity.
- Mismatch/unknown action: Stop the affected version-sensitive use and invoke `roblox-resource-acquisition` in `repair/reconcile` mode.
- Defect handoff: Capture the task, installed state, expected behavior, observed behavior, and smallest reproduction; then invoke `roblox-resource-acquisition` in `repair/reconcile` mode.

## Common path

```luau
local Widget = require(game.ReplicatedStorage.Packages.Widget)
local session = Widget.new()
session:Start()
```

## Client/server placement

Create authoritative sessions on the server and validate every client request. Clients may observe replicated widget state but never choose authoritative values or invoke server-only lifecycle methods.

## Mental model

Each server-owned session publishes a replicated widget snapshot and owns cleanup for all connections created during its lifetime.

## Lifecycle and cleanup

- Initialization: Create one server-owned session after package loading completes.
- Reuse: Reuse the session for related widget updates during its lifetime.
- Cleanup/destruction: Call the documented destroy method when the owning system stops.

## API used by this skill

Use `Widget.new()`, `session:Start()`, and `session:Destroy()` for the documented lifecycle.

## Failure modes

### Widget never appears

A missing package or wrong server placement causes initialization failure; inspect the manifest and move initialization to the server before retrying.

## Limitations

- Does not replace server-side validation of client-controlled widget requests.

## Security notes

Keep the server authoritative, validate client payloads before changing widget state, and pin the inspected package version.

## Verify after installation

Run: Execute `lune run tests/widget.luau` after installing the package.

Pass condition: The command prints `widget-ready` and exits with code `0`.

## Alternatives

- Use a local server-owned table when replication and managed cleanup are unnecessary.

## Provenance

- Resource slug: widget-resource
- Package identity: com.example.widget
- DevForum: No DevForum topic is used/applicable
- Canonical source/docs: https://example.com/widget
- Source version/release/commit: 1.2.3
- Source review date: 2026-08-16
- Resource verification: unverified

## Version drift

Before using another version, compare its release source and API changes, then rerun the installation and lifecycle checks.
"""
