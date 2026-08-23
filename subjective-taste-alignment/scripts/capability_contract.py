"""Host-capability declarations and constrained-fallback assessment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


REQUIRED_CAPABILITIES = (
    "persistence_durability",
    "revision_detection",
    "external_edit_authorship",
    "scope_identity",
    "source_addressability",
    "execution_surfaces",
    "domain_adapters",
)

DIRECT_EVIDENCE = {
    "persistence_durability": frozenset({"documented_storage_guarantee"}),
    "revision_detection": frozenset({"revision_token", "content_digest"}),
    "external_edit_authorship": frozenset({"host_authorship_metadata"}),
    "scope_identity": frozenset({"host_identity"}),
    "source_addressability": frozenset(
        {"immutable_locator", "versioned_locator", "retrievable_snapshot"}
    ),
    "execution_surfaces": frozenset({"callable_surface"}),
    "domain_adapters": frozenset({"registered_adapter"}),
}

FALLBACK_ENFORCEMENT = {
    "unknown": "record_unknown",
    "unresolved": "preserve_unresolved",
    "conflict": "surface_conflict",
    "checkpoint": "require_checkpoint",
    "disabled": "disable_operation",
    "blocker": "stop_implementation",
}

CAPABILITY_FALLBACKS = {
    "persistence_durability": frozenset({"disabled", "blocker"}),
    "revision_detection": frozenset({"conflict", "checkpoint", "disabled", "blocker"}),
    "external_edit_authorship": frozenset(
        {"unknown", "unresolved", "disabled", "blocker"}
    ),
    "scope_identity": frozenset({"unresolved", "checkpoint", "disabled", "blocker"}),
    "source_addressability": frozenset(
        {"unknown", "unresolved", "checkpoint", "disabled", "blocker"}
    ),
    "execution_surfaces": frozenset({"checkpoint", "disabled", "blocker"}),
    "domain_adapters": frozenset({"disabled", "blocker"}),
}


@dataclass(frozen=True)
class CapabilityResult:
    supported: bool
    outcome: str
    mechanism: str | None = None
    preserves: str | None = None
    enforcement: str | None = None


@dataclass(frozen=True)
class CapabilityAssessment:
    ready: bool
    capabilities: Mapping[str, CapabilityResult]
    blockers: tuple[str, ...]


def assess_capabilities(
    declarations: Mapping[str, Mapping[str, str]],
) -> CapabilityAssessment:
    """Assess required host facts without accepting proxies or inert fallbacks."""
    capabilities: dict[str, CapabilityResult] = {}
    blockers: list[str] = []

    for capability_id in REQUIRED_CAPABILITIES:
        declaration = declarations.get(capability_id, {})
        mechanism = declaration.get("mechanism")
        evidence = declaration.get("evidence")
        if mechanism and mechanism.strip() and evidence in DIRECT_EVIDENCE[capability_id]:
            capabilities[capability_id] = CapabilityResult(
                supported=True,
                outcome="supported",
                mechanism=mechanism,
            )
            continue

        fallback = declaration.get("fallback")
        enforcement = declaration.get("enforcement")
        preserves = declaration.get("preserves")
        valid_fallback = (
            fallback in CAPABILITY_FALLBACKS[capability_id]
            and enforcement == FALLBACK_ENFORCEMENT[fallback]
            and preserves
            and preserves.strip()
        )
        if valid_fallback and isinstance(fallback, str):
            capabilities[capability_id] = CapabilityResult(
                supported=False,
                outcome=fallback,
                preserves=preserves,
                enforcement=enforcement,
            )
            if fallback == "blocker":
                blockers.append(capability_id)
            continue

        capabilities[capability_id] = CapabilityResult(
            supported=False,
            outcome="blocker",
            enforcement="stop_implementation",
        )
        blockers.append(capability_id)

    return CapabilityAssessment(
        ready=not blockers,
        capabilities=capabilities,
        blockers=tuple(blockers),
    )
