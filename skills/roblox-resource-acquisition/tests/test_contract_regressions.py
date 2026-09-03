"""Regression tests for lifecycle, identity, and Agent Skills contract invariants."""
from pathlib import Path

import fixtures


def test_verified_acquisition_does_not_require_generated_child(record_mod):
    record = fixtures.verified_acquisition_record(generated_skill="")
    errors, _notes = record_mod.validate_record(Path("record.yaml"), record)
    assert errors == []


def test_child_failure_does_not_revoke_resource_side_verified_acquisition(record_mod):
    record = fixtures.verified_acquisition_record(generated_skill="roblox-evaera-promise")
    record["skill_validation"].update(
        {
            "structural_passed": False,
            "independent_behavioral_executed": True,
            "independent_behavioral_passed": False,
            "environment": "fresh-agent contract runner",
            "result": "Child instructions selected the wrong API and failed the task.",
        }
    )
    errors, _notes = record_mod.validate_record(Path("record.yaml"), record)
    assert errors == []


def test_all_trusted_bases_require_stable_identity(record_mod):
    for basis in ("project", "other"):
        record = fixtures.valid_record()
        record["discovery_origin"] = "other" if basis == "other" else "project"
        record["selection_reason"] = "Project-selected candidate." if basis == "other" else record["selection_reason"]
        record["trust"] = {
            "level": "trusted",
            "basis": basis,
            "reason": "Trusted by the applicable project/policy authority.",
        }
        record["slug"] = ""
        record["canonical_url"] = ""
        record["package_id"] = ""
        errors, _notes = record_mod.validate_record(Path("record.yaml"), record)
        assert "trusted records require slug to bind trust to a stable identity" in errors
        assert "trusted records require canonical_url or package_id to bind trust to canonical identity" in errors


def test_skill_directory_must_match_frontmatter_name(skill_mod, tmp_path):
    child = tmp_path / "wrong-directory"
    child.mkdir()
    (child / "SKILL.md").write_text(fixtures.valid_skill_text(), encoding="utf-8")
    errors, _warnings = skill_mod.validate_skill(child)
    assert "frontmatter name must match the generated skill directory name" in errors


def test_skill_description_has_agent_skills_length_limit(skill_mod, tmp_path):
    child = tmp_path / "roblox-widget-resource"
    child.mkdir()
    description = "Use Widget Resource when " + ("replicated lifecycle coordination " * 80)
    assert len(description) > 1024
    (child / "SKILL.md").write_text(
        fixtures.valid_skill_text(description=description), encoding="utf-8"
    )
    errors, _warnings = skill_mod.validate_skill(child)
    assert "frontmatter description must be at most 1024 characters" in errors




def test_skill_name_has_agent_skills_length_limit(skill_mod, tmp_path):
    name = "roblox-" + ("a" * 60)
    assert len(name) > 64
    child = tmp_path / name
    child.mkdir()
    (child / "SKILL.md").write_text(fixtures.valid_skill_text(name=name), encoding="utf-8")
    errors, _warnings = skill_mod.validate_skill(child)
    assert "frontmatter name must be at most 64 characters" in errors


def test_optional_frontmatter_types_and_compatibility_limit(skill_mod, tmp_path):
    child = tmp_path / "roblox-widget-resource"
    child.mkdir()
    text = fixtures.valid_skill_text().replace(
        "description: Use Widget Resource for synchronized widget replication with deterministic lifecycle cleanup.\n",
        "description: Use Widget Resource for synchronized widget replication with deterministic lifecycle cleanup.\n"
        "compatibility: " + ("x" * 501) + "\n"
        "license: 123\n"
        "allowed-tools: 456\n",
    )
    (child / "SKILL.md").write_text(text, encoding="utf-8")
    errors, _warnings = skill_mod.validate_skill(child)
    assert "frontmatter compatibility must be 1 to 500 characters" in errors
    assert "frontmatter license must be a string" in errors
    assert "frontmatter allowed-tools must be a string" in errors


def test_valid_metadata_mapping_is_supported(skill_mod, tmp_path):
    child = tmp_path / "roblox-widget-resource"
    child.mkdir()
    text = fixtures.valid_skill_text().replace(
        "description: Use Widget Resource for synchronized widget replication with deterministic lifecycle cleanup.\n",
        "description: Use Widget Resource for synchronized widget replication with deterministic lifecycle cleanup.\n"
        "metadata:\n"
        "  resource-slug: widget-resource\n"
        "  lifecycle: generated\n",
    )
    (child / "SKILL.md").write_text(text, encoding="utf-8")
    errors, _warnings = skill_mod.validate_skill(child)
    assert errors == []


def test_metadata_requires_string_keys_and_values(skill_mod, tmp_path):
    child = tmp_path / "roblox-widget-resource"
    child.mkdir()
    text = fixtures.valid_skill_text().replace(
        "description: Use Widget Resource for synchronized widget replication with deterministic lifecycle cleanup.\n",
        "description: Use Widget Resource for synchronized widget replication with deterministic lifecycle cleanup.\n"
        "metadata:\n"
        "  resource-slug: 123\n",
    )
    (child / "SKILL.md").write_text(text, encoding="utf-8")
    errors, _warnings = skill_mod.validate_skill(child)
    assert "frontmatter metadata keys and values must be strings" in errors


def _write_widget_child(tmp_path):
    child = tmp_path / "roblox-widget-resource"
    child.mkdir()
    (child / "SKILL.md").write_text(fixtures.valid_skill_text(), encoding="utf-8")
    return child


def test_matching_record_and_child_bundle_passes(bundle_mod, tmp_path):
    record = fixtures.matching_widget_record()
    child = _write_widget_child(tmp_path)
    errors, _notes = bundle_mod.validate_bundle(Path("record.yaml"), record, child)
    assert errors == []


def test_bundle_rejects_cross_artifact_identity_and_state_mismatch(bundle_mod, tmp_path):
    record = fixtures.matching_widget_record()
    child = _write_widget_child(tmp_path)
    record["slug"] = "different-widget"
    record["canonical_url"] = "https://example.com/different-widget"
    record["package_id"] = "com.example.different"
    record["verification"]["version_or_commit"] = "9.9.9"
    record["verification"]["status"] = "unavailable"
    record["verification"]["validated_at"] = "2026-08-16"
    record["resource_proof"]["unavailable_claims"] = ["Studio unavailable"]
    errors, _notes = bundle_mod.validate_bundle(Path("record.yaml"), record, child)
    assert any("Resource slug" in error for error in errors)
    assert any("canonical_url" in error for error in errors)
    assert any("Package identity" in error for error in errors)
    assert any("reviewed source state" in error for error in errors)
    assert any("verification status" in error for error in errors)


def test_bundle_requires_recorded_structural_pass(bundle_mod, tmp_path):
    record = fixtures.matching_widget_record()
    record["skill_validation"]["structural_passed"] = False
    child = _write_widget_child(tmp_path)
    errors, _notes = bundle_mod.validate_bundle(Path("record.yaml"), record, child)
    assert any("structural_passed: true" in error for error in errors)


def test_verified_proof_cannot_transfer_to_different_version(record_mod):
    record = fixtures.verified_acquisition_record(generated_skill="")
    record["verification"]["version_or_commit"] = "v5.0.0"
    errors, _notes = record_mod.validate_record(Path("record.yaml"), record)
    assert "executed resource proof target must exactly match verification.version_or_commit" in errors


def test_failed_proof_cannot_be_attached_to_different_version(record_mod):
    record = fixtures.valid_record()
    record["verification"] = {
        "status": "failed",
        "validated_at": "2026-08-29",
        "version_or_commit": "v5.0.0",
    }
    record["resource_proof"] = {
        "executed": True,
        "passed": False,
        "target_version_or_commit": "v4.0.0",
        "environment": "isolated Roblox Studio qualification place",
        "result": "The tested behavior failed.",
        "unavailable_claims": [],
    }
    record["blocked_use_or_version"] = "v5.0.0 affected behavior"
    errors, _notes = record_mod.validate_record(Path("record.yaml"), record)
    assert "executed resource proof target must exactly match verification.version_or_commit" in errors


def test_legacy_unexecuted_v2_record_without_proof_target_remains_valid(record_mod):
    record = fixtures.valid_record()
    record["resource_proof"].pop("target_version_or_commit", None)
    errors, _notes = record_mod.validate_record(Path("record.yaml"), record)
    assert errors == []


def test_executed_resource_proof_requires_explicit_target_version(record_mod):
    record = fixtures.verified_acquisition_record(generated_skill="")
    record["resource_proof"].pop("target_version_or_commit")
    errors, _notes = record_mod.validate_record(Path("record.yaml"), record)
    assert "executed resource proof must record resource_proof.target_version_or_commit" in errors


def test_failed_trusted_records_always_preserve_blocked_use(record_mod):
    cases = (
        ("curated", "curated"),
        ("project", "project"),
        ("explicit-user", "other"),
        ("other", "other"),
    )
    for basis, origin in cases:
        record = fixtures.valid_record()
        record["discovery_origin"] = origin
        if origin == "other":
            record["selection_reason"] = "Directly targeted resource with an explicit authorized scope."
        record["trust"] = {
            "level": "trusted",
            "basis": basis,
            "reason": "Applicable policy authority trusts this exact resource identity.",
        }
        record["verification"] = {
            "status": "failed",
            "validated_at": "2026-08-29",
            "version_or_commit": "v4.0.0",
        }
        record["resource_proof"] = {
            "executed": True,
            "passed": False,
            "target_version_or_commit": "v4.0.0",
            "environment": "isolated Roblox Studio qualification place",
            "result": "Required runtime behavior failed reproducibly.",
            "unavailable_claims": [],
        }
        record["blocked_use_or_version"] = ""
        errors, _notes = record_mod.validate_record(Path("record.yaml"), record)
        assert "failed trusted records must identify blocked_use_or_version without revoking policy trust" in errors


def test_host_adoption_cannot_exist_without_generated_child(record_mod):
    record = fixtures.valid_record()
    record["generated_skill"] = ""
    record["host_adoptions"] = [fixtures.operational_adoption()]
    errors, _notes = record_mod.validate_record(Path("record.yaml"), record)
    assert "host_adoptions require generated_skill to identify the adopted generated child" in errors


def test_catalog_routing_evidence_cannot_exist_without_generated_child(record_mod):
    record = fixtures.valid_record()
    record["generated_skill"] = ""
    record["skill_validation"].update(
        {
            "catalog_routing_status": "verified",
            "catalog_fingerprint": "sha256:" + "a" * 64,
            "catalog_environment": "isolated host routing test",
            "catalog_result": "Explicit and implicit selection checks passed.",
        }
    )
    errors, _notes = record_mod.validate_record(Path("record.yaml"), record)
    assert "catalog routing evidence requires generated_skill to identify the generated child" in errors


def test_non_generated_host_skill_can_participate_as_routing_competitor(catalog_mod, tmp_path):
    generated = tmp_path / "roblox-widget-resource"
    generated.mkdir()
    (generated / "SKILL.md").write_text(
        fixtures.valid_skill_text(
            name="roblox-widget-resource",
            description="Use Widget Resource for synchronized replicated widget sessions and deterministic lifecycle cleanup.",
            use_when="- Synchronizing replicated widget sessions with deterministic cleanup.",
        ),
        encoding="utf-8",
    )
    competitor = tmp_path / "manual-widget-helper"
    competitor.mkdir()
    (competitor / "SKILL.md").write_text(
        "---\n"
        "name: manual-widget-helper\n"
        "description: Use Manual Widget Helper for synchronized replicated widget sessions and deterministic lifecycle cleanup.\n"
        "---\n\n"
        "# Manual Widget Helper\n\n"
        "Ordinary host skill; it is intentionally not a generated resource child.\n",
        encoding="utf-8",
    )

    errors, _warnings, overlaps, with_competitor = catalog_mod.validate_catalog(
        [generated], host="portable", competitor_roots=[competitor]
    )
    assert errors == []
    assert overlaps
    _errors, _warnings, _overlaps, generated_only = catalog_mod.validate_catalog(
        [generated], host="portable"
    )
    assert with_competitor != generated_only
