import json
from pathlib import Path

from alignment_harness import assess_capabilities


def disabled_capabilities(*excluded: str) -> dict[str, dict[str, str]]:
    return {
        capability_id: {
            "fallback": "disabled",
            "enforcement": "disable_operation",
            "preserves": "the unsupported operation cannot proceed",
        }
        for capability_id in (
            "persistence_durability",
            "revision_detection",
            "external_edit_authorship",
            "scope_identity",
            "source_addressability",
            "execution_surfaces",
            "domain_adapters",
        )
        if capability_id not in excluded
    }


def test_unobservable_authorship_is_preserved_as_unknown() -> None:
    result = assess_capabilities(
        {
            "persistence_durability": {
                "mechanism": "workspace file with host-managed lifecycle",
                "evidence": "documented_storage_guarantee",
            },
            "revision_detection": {
                "mechanism": "content revision token",
                "evidence": "revision_token",
            },
            "external_edit_authorship": {
                "fallback": "unknown",
                "enforcement": "record_unknown",
                "preserves": "agent or external writes cannot become explicit user evidence",
            },
            "scope_identity": {
                "mechanism": "host project, session, artifact, and subject identifiers",
                "evidence": "host_identity",
            },
            "source_addressability": {
                "mechanism": "immutable source locator and revision",
                "evidence": "immutable_locator",
            },
            "execution_surfaces": {
                "mechanism": "declared callable host tools",
                "evidence": "callable_surface",
            },
            "domain_adapters": {
                "fallback": "disabled",
                "enforcement": "disable_operation",
                "preserves": "unsupported domains cannot claim implemented output",
            },
        }
    )

    assert result.ready is True
    assert result.blockers == ()
    assert result.capabilities["external_edit_authorship"].outcome == "unknown"
    assert result.capabilities["external_edit_authorship"].supported is False
    assert result.capabilities["domain_adapters"].outcome == "disabled"


def test_successful_parse_is_not_evidence_of_persistence_durability() -> None:
    declarations = disabled_capabilities("persistence_durability")
    declarations["persistence_durability"] = {
        "mechanism": "a profile parsed successfully from a local file",
        "evidence": "successful_parse",
    }

    result = assess_capabilities(declarations)

    assert result.ready is False
    assert result.capabilities["persistence_durability"].outcome == "blocker"
    assert result.blockers == ("persistence_durability",)


def test_blank_mechanisms_and_fallback_invariants_remain_blockers() -> None:
    declarations = disabled_capabilities(
        "persistence_durability", "external_edit_authorship"
    )
    declarations["persistence_durability"] = {
        "mechanism": "   ",
        "evidence": "documented_storage_guarantee",
    }
    declarations["external_edit_authorship"] = {
        "fallback": "unknown",
        "enforcement": "record_unknown",
        "preserves": "\t",
    }

    result = assess_capabilities(declarations)

    assert result.ready is False
    assert result.blockers == (
        "persistence_durability",
        "external_edit_authorship",
    )


def test_fallback_must_constrain_the_specific_unavailable_capability() -> None:
    declarations = {
        capability_id: {
            "fallback": "unknown",
            "enforcement": "record_unknown",
            "preserves": "x",
        }
        for capability_id in (
            "persistence_durability",
            "revision_detection",
            "external_edit_authorship",
            "scope_identity",
            "source_addressability",
            "execution_surfaces",
            "domain_adapters",
        )
    }

    result = assess_capabilities(declarations)

    assert result.ready is False
    assert result.capabilities["external_edit_authorship"].outcome == "unknown"
    assert result.capabilities["source_addressability"].outcome == "unknown"
    assert result.blockers == (
        "persistence_durability",
        "revision_detection",
        "scope_identity",
        "execution_surfaces",
        "domain_adapters",
    )


def test_one_atomic_round_trip_does_not_prove_storage_durability() -> None:
    declarations = disabled_capabilities("persistence_durability")
    declarations["persistence_durability"] = {
        "mechanism": "one atomic save and reload succeeded",
        "evidence": "observed_atomic_round_trip",
    }

    result = assess_capabilities(declarations)

    assert result.ready is False
    assert result.blockers == ("persistence_durability",)


def test_repository_host_declaration_is_explicit_and_safely_constrained() -> None:
    contract_path = Path(__file__).resolve().parent.parent / "references" / "host-capabilities.json"
    declarations = json.loads(contract_path.read_text(encoding="utf-8"))

    result = assess_capabilities(declarations)

    assert result.ready is True
    assert result.capabilities["external_edit_authorship"].outcome == "unknown"
    assert result.capabilities["scope_identity"].outcome == "unresolved"
    assert result.capabilities["domain_adapters"].outcome == "disabled"
