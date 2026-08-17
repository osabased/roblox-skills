"""Regression tests for the parser-dependent trust flip.

Before PyYAML became required, a registry entry with a bare ``package_id:``
was FAIL with PyYAML installed and PASS without it — the same file earned a
different trust verdict depending on the environment. These tests pin the
now-deterministic verdict: bare, quoted-empty, and omitted-value spellings of
optional fields all validate identically.
"""
from pathlib import Path

import fixtures

BARE_PACKAGE_ID = fixtures.VALID_REGISTRY_ENTRY.replace(
    'package_id: "evaera/promise@4.0.0"', "package_id:"
)
EXPLICIT_EMPTY_PACKAGE_ID = fixtures.VALID_REGISTRY_ENTRY.replace(
    'package_id: "evaera/promise@4.0.0"', 'package_id: ""'
)


def _validate(registry_mod, tmp_path, text):
    path = tmp_path / "evaera-promise.yaml"
    path.write_text(text)
    data = registry_mod.load_entry(path)
    errors, _notes = registry_mod.validate_entry(path, data)
    return data, errors


def test_bare_empty_optional_field_passes(registry_mod, tmp_path):
    data, errors = _validate(registry_mod, tmp_path, BARE_PACKAGE_ID)
    assert errors == []
    assert data["package_id"] == ""


def test_explicit_empty_optional_field_passes(registry_mod, tmp_path):
    data, errors = _validate(registry_mod, tmp_path, EXPLICIT_EMPTY_PACKAGE_ID)
    assert errors == []
    assert data["package_id"] == ""


def test_bare_and_explicit_empty_agree(registry_mod, tmp_path):
    bare = _validate(registry_mod, tmp_path, BARE_PACKAGE_ID)
    explicit = _validate(registry_mod, tmp_path, EXPLICIT_EMPTY_PACKAGE_ID)
    assert bare == explicit


def test_bare_empty_list_field_passes(registry_mod, tmp_path):
    text = fixtures.VALID_REGISTRY_ENTRY.replace(
        'notes:\n  - "Prefer Promise.new over Promise.async (deprecated alias)."',
        "notes:",
    )
    data, errors = _validate(registry_mod, tmp_path, text)
    assert errors == []
    assert data["notes"] == []


def test_bare_empty_required_field_still_fails(registry_mod, tmp_path):
    text = fixtures.VALID_REGISTRY_ENTRY.replace(
        'curation_reason: "Project standard async primitive; API stable since v4."',
        "curation_reason:",
    )
    _data, errors = _validate(registry_mod, tmp_path, text)
    assert "curation_reason must not be empty" in errors


def test_bare_empty_required_list_still_fails(registry_mod, tmp_path):
    text = fixtures.VALID_REGISTRY_ENTRY.replace(
        "capabilities:\n  - promise-based async primitives for Luau",
        "capabilities:",
    )
    _data, errors = _validate(registry_mod, tmp_path, text)
    assert "capabilities must contain at least one item" in errors


def test_record_bare_nested_empty_matches_template_spelling(record_mod, tmp_path):
    import fixtures as fx

    bare = fx.VALID_RECORD.replace('  validated_at: ""', "  validated_at:")
    path = tmp_path / "record.yaml"
    path.write_text(bare)
    data = record_mod.load_record(path)
    errors, _notes = record_mod.validate_record(path, data)
    assert errors == []
    assert data["verification"]["validated_at"] == ""


def test_record_bare_list_field_matches_template_spelling(record_mod, tmp_path):
    import fixtures as fx

    bare = fx.VALID_RECORD.replace("  unavailable_claims: []", "  unavailable_claims:")
    path = tmp_path / "record.yaml"
    path.write_text(bare)
    data = record_mod.load_record(path)
    errors, _notes = record_mod.validate_record(path, data)
    assert errors == []
    assert data["resource_proof"]["unavailable_claims"] == []
