"""Fixture documents used by the end-to-end validator tests."""

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

VALID_RECORD = """\
resource: Promise
slug: evaera-promise
discovery_origin: curated

trust:
  level: trusted
  basis: curated
  reason: "Listed in the project curated registry as the standard async primitive."

canonical_url: "https://github.com/evaera/roblox-lua-promise"
package_id: "evaera/promise@4.0.0"

verification:
  status: unverified
  validated_at: ""
  version_or_commit: "v4.0.0"

capability: "promise-based async primitives for Luau"
devforum_url: "https://devforum.roblox.com/t/promise-implementation-for-roblox/463825"
selection_reason: "Best curated fit for coordinating async matchmaking operations."
alternatives_considered:
  - "task.spawn with manual state flags: rejected, no cancellation semantics"

resource_proof:
  executed: false
  passed: false
  environment: ""
  result: ""
  unavailable_claims: []

generated_skill: "roblox-evaera-promise"
skill_validation:
  structural_passed: false
  independent_behavioral_executed: false
  independent_behavioral_passed: false
  environment: ""
  result: ""

limitations:
  - "Guidance targets v4.0.0 only."
blocked_use_or_version: ""
rejection_reason: ""
reconsider_when: ""
"""

INVALID_RECORD = """\
resource: Promise
slug: evaera-promise
discovery_origin: curated

trust:
  level: trusted
  basis: verified-acquisition
  reason: "Claims verified acquisition without any executed proof."

canonical_url: "https://github.com/evaera/roblox-lua-promise"
package_id: "evaera/promise@4.0.0"

verification:
  status: verified
  validated_at: ""
  version_or_commit: ""

capability: "promise-based async primitives for Luau"
devforum_url: ""
selection_reason: ""
alternatives_considered: []

resource_proof:
  executed: false
  passed: false
  environment: ""
  result: ""
  unavailable_claims:
    - "runtime smoke test could not run"

generated_skill: ""
skill_validation:
  structural_passed: false
  independent_behavioral_executed: false
  independent_behavioral_passed: true
  environment: ""
  result: ""

limitations: []
blocked_use_or_version: ""
rejection_reason: ""
reconsider_when: ""
"""

FILLED_SKILL = """\
---
name: roblox-evaera-promise
description: Use the evaera Promise library (v4.0.0) when a Roblox task needs promise-based async coordination with cancellation in Luau.
---

# Promise

Use **Promise** for promise-based async coordination in Luau. Guidance targets **v4.0.0** (source reviewed **2026-08-11**). Resource verification: **UNVERIFIED**.

## Use when

- Coordinating several async operations whose results must be combined or raced.
- An async operation must be cancellable after it starts.

## Do not use when

- A single event connection or one `task.spawn` call already solves the need.
- The project forbids third-party dependencies.

## Prerequisites and installation

1. Add `Promise = "evaera/promise@4.0.0"` to the `[dependencies]` section of `wally.toml`.
2. Run `wally install` and confirm `Packages/Promise.lua` exists.
3. Require it from a shared module: `local Promise = require(ReplicatedStorage.Packages.Promise)`.

## Common path

Create a promise around one async operation, then chain consumption. This sequence is grounded in the v4.0.0 source review and is not runtime-verified.

```luau
local Promise = require(game:GetService("ReplicatedStorage").Packages.Promise)

local function fetchProfile(userId: number)
    return Promise.new(function(resolve, reject)
        local ok, result = pcall(function()
            return game:GetService("Players"):GetNameFromUserIdAsync(userId)
        end)
        if ok then resolve(result) else reject(result) end
    end)
end

fetchProfile(1):andThen(print):catch(warn)
```

## Client/server placement

Place the Promise module in `ReplicatedStorage.Packages` so both sides can require it. Promises never cross the client/server boundary; resolve them locally and send plain data over RemoteEvents. The server retains authority over all game state; never resolve a server decision from a client-supplied promise result.

## Mental model

A Promise wraps one eventual value in states Started -> Resolved/Rejected/Cancelled. Chaining with `andThen` returns a new promise; rejection propagates down the chain until a `catch`.

## Lifecycle and cleanup

- Initialization: construct with `Promise.new(executor)`; the executor runs immediately on its own thread.
- Reuse: a settled promise can be observed repeatedly; it never re-runs its executor.
- Cleanup/destruction: call `:cancel()` on promises tied to destroyed instances; register cleanup in the executor's `onCancel` hook.

## API used by this skill

Source-reviewed (not runtime-verified) public APIs from v4.0.0: `Promise.new`, `Promise.all`, `Promise.race`, `andThen`, `catch`, `finally`, `cancel`, `Promise.delay`.

## Failure modes

### Chain silently stops after an error

Likely cause: no `catch` at the chain end -> diagnosis: add `:catch(warn)` temporarily and observe the surfaced rejection -> repair: handle or propagate the rejection explicitly.

## Limitations

- Guidance targets v4.0.0 only; older v3 APIs differ around cancellation.

## Security notes

No trust boundary is special to this resource: it performs no networking, persistence, or remote access by itself. Preserve server authority; never embed secrets in source.

## Verify after installation

Run: in Studio's command bar, `local P = require(game.ReplicatedStorage.Packages.Promise); P.resolve(42):andThen(print)`

Pass condition: the output window prints `42` with no error within one second.

## Alternatives

Roblox built-in `task.spawn` plus manual state flags was considered the closest built-in; Promise was preferred because cancellation and composition (`Promise.all`) would otherwise need bespoke code.

## Provenance

- DevForum: https://devforum.roblox.com/t/promise-implementation-for-roblox/463825
- Canonical source/docs: https://github.com/evaera/roblox-lua-promise
- Source version/release/commit: v4.0.0
- Source review date: 2026-08-11
- Resource verification: UNVERIFIED

## Version drift

Before using newer upstream versions, check release notes/source for changes affecting the APIs and behavior documented above. Re-review material changes before updating this skill's source state, and rerun runtime proof when the claimed verification status would otherwise become stale.
"""
