"""Tests for validate_skill.py frontmatter parsing (now real YAML)."""
import subprocess
import sys

import pytest

import fixtures


def test_plain_frontmatter(skill_mod):
    meta, body = skill_mod.parse_frontmatter(
        "---\nname: roblox-thing\ndescription: Does a thing well.\n---\n# Body\n"
    )
    assert meta == {"name": "roblox-thing", "description": "Does a thing well."}
    assert body.startswith("# Body")


def test_folded_description_parses(skill_mod):
    text = (
        "---\n"
        "name: roblox-thing\n"
        "description: >-\n"
        "  Use this when a Roblox task needs promise-based\n"
        "  async coordination with cancellation.\n"
        "---\n"
        "# Body\n"
    )
    meta, _body = skill_mod.parse_frontmatter(text)
    assert meta["description"] == (
        "Use this when a Roblox task needs promise-based "
        "async coordination with cancellation."
    )


def test_duplicate_frontmatter_key_still_fails(skill_mod):
    with pytest.raises(ValueError, match="duplicate key"):
        skill_mod.parse_frontmatter("---\nname: a\nname: b\n---\nbody\n")


def test_metadata_mapping_parses(skill_mod):
    meta, _body = skill_mod.parse_frontmatter(
        "---\nname: roblox-thing\ndescription: Does a thing well.\nmetadata:\n  owner: tooling\n---\nbody\n"
    )
    assert meta["metadata"] == {"owner": "tooling"}


def test_non_metadata_nested_frontmatter_value_fails(skill_mod):
    with pytest.raises(ValueError, match="must be a scalar"):
        skill_mod.parse_frontmatter("---\nname:\n  nested: x\n---\nbody\n")


def test_missing_frontmatter_fails(skill_mod):
    with pytest.raises(ValueError, match="must start with YAML frontmatter"):
        skill_mod.parse_frontmatter("# No frontmatter\n")


def test_unclosed_frontmatter_fails(skill_mod):
    with pytest.raises(ValueError, match="not closed"):
        skill_mod.parse_frontmatter("---\nname: a\n")


def test_filled_skill_with_folded_description_passes_cli(scripts_dir, tmp_path):
    filled = fixtures.valid_skill_text()
    folded = filled.replace(
        "description: Use Widget Resource for synchronized widget replication "
        "with deterministic lifecycle cleanup.",
        "description: >-\n"
        "  Use Widget Resource for synchronized widget replication\n"
        "  with deterministic lifecycle cleanup.",
    )
    assert folded != filled, "fixture replacement did not apply"
    child = tmp_path / "roblox-widget-resource"
    child.mkdir()
    (child / "SKILL.md").write_text(folded, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(scripts_dir / "validate_skill.py"), str(child)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
