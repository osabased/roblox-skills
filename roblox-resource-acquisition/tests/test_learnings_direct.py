"""Direct tests for learnings-store logic so coverage measures validator branches."""
from pathlib import Path

import fixtures
import pytest
import yaml


def _valid_data():
    return yaml.safe_load(fixtures.VALID_LEARNING)


def test_load_entry_normalizes_yaml_date_and_empty_values(learnings_mod, tmp_path):
    path = tmp_path / "entry.yaml"
    path.write_text(fixtures.VALID_LEARNING.replace('related_entry: ""', 'related_entry:'), encoding="utf-8")
    data = learnings_mod.load_entry(path)
    assert data["observed"] == "2026-08-11"
    assert data["related_entry"] == ""
    assert learnings_mod.validate_entry(path, data) == []


def test_load_entry_empty_document_and_non_mapping(learnings_mod, tmp_path):
    empty = tmp_path / "empty.yaml"
    empty.write_text("", encoding="utf-8")
    assert learnings_mod.load_entry(empty) == {}

    scalar = tmp_path / "scalar.yaml"
    scalar.write_text("hello\n", encoding="utf-8")
    with pytest.raises(ValueError, match="top-level YAML value must be a mapping"):
        learnings_mod.load_entry(scalar)


def test_directive_warning_is_advisory(learnings_mod):
    data = yaml.safe_load(fixtures.DIRECTIVE_LEARNING)
    warnings = learnings_mod.entry_warnings(data)
    assert len(warnings) == 1
    assert "imperative directive" in warnings[0]
    data["statement"] = "Fire never clones payloads during the observed failure."
    assert learnings_mod.entry_warnings(data) == []


def test_validate_entry_rejects_state_smuggling_unknowns_and_bad_types(learnings_mod):
    data = _valid_data()
    data.update({"trust": {"level": "trusted"}, "mystery": "x"})
    data["schema_version"] = 2
    data["task_context"] = 123
    errors = learnings_mod.validate_entry(Path("entry.yaml"), data)
    assert any("must not carry trust" in e for e in errors)
    assert "unknown field(s): mystery" in errors
    assert "schema_version must be integer 1" in errors
    assert "task_context must be a string" in errors


def test_validate_entry_rejects_kind_scope_identity_and_package_defects(learnings_mod):
    data = _valid_data()
    data["kind"] = "failed-query"
    data["scope"] = "resource"
    data["slug"] = "Bad Slug"
    data["canonical_url"] = "http://example.com/insecure"
    data["package_id"] = "bad\npackage"
    errors = learnings_mod.validate_entry(Path("entry.yaml"), data)
    assert any("requires scope search" in e for e in errors)
    assert any("slug must be lowercase" in e for e in errors)
    assert any("canonical_url must be an absolute https:// URL" in e for e in errors)
    assert "package_id must be a single-line exact identifier" in errors


def test_non_resource_scope_must_not_carry_resource_identity(learnings_mod):
    data = _valid_data()
    data["kind"] = "failed-query"
    data["scope"] = "search"
    errors = learnings_mod.validate_entry(Path("entry.yaml"), data)
    assert "slug must be empty when scope is 'search'" in errors
    assert "canonical_url must be empty when scope is 'search'" in errors
    assert "package_id must be empty when scope is 'search'" in errors


def test_validate_entry_required_content_dates_and_kind_specific_fields(learnings_mod):
    data = _valid_data()
    data["kind"] = "rejection"
    data["observed"] = "yesterday"
    data["statement"] = ""
    data["evidence"] = ""
    data["version_context"] = ""
    data["reconsider_when"] = ""
    errors = learnings_mod.validate_entry(Path("entry.yaml"), data)
    assert "observed must be YYYY-MM-DD" in errors
    assert "statement must not be empty" in errors
    assert "evidence must not be empty" in errors
    assert "kind 'rejection' requires non-empty version_context" in errors
    assert "kind 'rejection' requires non-empty reconsider_when" in errors


def test_validate_entry_empty_and_invalid_kind_scope(learnings_mod):
    data = _valid_data()
    data["kind"] = ""
    data["scope"] = ""
    errors = learnings_mod.validate_entry(Path("entry.yaml"), data)
    assert "kind must not be empty" in errors
    assert "scope must not be empty" in errors

    data["kind"] = "made-up"
    data["scope"] = "made-up"
    errors = learnings_mod.validate_entry(Path("entry.yaml"), data)
    assert any("kind must be one of" in e for e in errors)
    assert any("scope must be one of" in e for e in errors)
