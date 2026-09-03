"""End-to-end CLI runs of all validators against known-good/bad fixtures."""

import subprocess
import sys

import fixtures
import yaml


def run_cli(scripts_dir, script, *args):
    return subprocess.run(
        [sys.executable, str(scripts_dir / script), *map(str, args)],
        capture_output=True,
        text=True,
    )


def write_utf8(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def write_skill(root, *, name="roblox-widget-resource", description=None, use_when=None):
    skill_root = root if root.name == name else root / name
    skill_root.mkdir(parents=True, exist_ok=True)
    write_utf8(
        skill_root / "SKILL.md",
        fixtures.valid_skill_text(
            name=name,
            description=description
            or "Use Widget Resource for synchronized widget replication with deterministic lifecycle cleanup.",
            use_when=use_when
            or "- Synchronizing replicated widget state across server-owned sessions.",
        ),
    )
    return skill_root


def test_registry_valid(scripts_dir, tmp_path):
    write_utf8(tmp_path / "evaera-promise.yaml", fixtures.VALID_REGISTRY_ENTRY)
    proc = run_cli(scripts_dir, "validate_curated_registry.py", tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS: curated registry structural/identity checks passed" in proc.stdout


def test_registry_invalid_fails_for_seeded_defects(scripts_dir, tmp_path):
    write_utf8(tmp_path / "bad.yaml", fixtures.INVALID_REGISTRY_ENTRY)
    proc = run_cli(scripts_dir, "validate_curated_registry.py", tmp_path)
    assert proc.returncode == 1
    for fragment in (
        "slug must be lowercase kebab-case",
        "name must not be empty",
        "canonical_url must be an absolute https:// URL",
        "devforum_url must use host devforum.roblox.com",
        "last_reviewed must be YYYY-MM-DD or empty",
    ):
        assert fragment in proc.stdout, f"missing: {fragment}\n{proc.stdout}"


def test_registry_duplicate_slug_in_same_registry_fails(scripts_dir, tmp_path):
    write_utf8(tmp_path / "a.yaml", fixtures.VALID_REGISTRY_ENTRY)
    write_utf8(tmp_path / "b.yaml", fixtures.VALID_REGISTRY_ENTRY)
    proc = run_cli(scripts_dir, "validate_curated_registry.py", tmp_path)
    assert proc.returncode == 1
    assert "duplicate slug 'evaera-promise'" in proc.stdout


def test_learnings_valid(scripts_dir, tmp_path):
    write_utf8(tmp_path / "2026-08-11-gotcha.yaml", fixtures.VALID_LEARNING)
    proc = run_cli(scripts_dir, "validate_learnings_store.py", tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "WARN" not in proc.stdout


def test_learnings_invalid(scripts_dir, tmp_path):
    write_utf8(tmp_path / "2026-08-11-broken.yaml", fixtures.INVALID_LEARNING)
    proc = run_cli(scripts_dir, "validate_learnings_store.py", tmp_path)
    assert proc.returncode == 1
    assert "resource-scoped entries require a non-empty slug" in proc.stdout
    assert "observed must be YYYY-MM-DD" in proc.stdout


def test_learnings_directive_warns_but_passes(scripts_dir, tmp_path):
    write_utf8(tmp_path / "2026-08-11-directive.yaml", fixtures.DIRECTIVE_LEARNING)
    proc = run_cli(scripts_dir, "validate_learnings_store.py", tmp_path)
    assert proc.returncode == 0
    assert "WARN" in proc.stdout
    assert "reads as an imperative directive" in proc.stdout


def test_record_valid(scripts_dir, tmp_path):
    record = write_utf8(
        tmp_path / "record.yaml",
        yaml.safe_dump(fixtures.valid_record(), sort_keys=False),
    )
    proc = run_cli(scripts_dir, "validate_resource_record.py", record)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS: resource-record structural/state checks passed" in proc.stdout
    assert "curation establishes trust, not runtime verification" in proc.stdout


def test_record_invalid_fails_only_for_seeded_state_defects(scripts_dir, tmp_path):
    record = write_utf8(
        tmp_path / "record.yaml",
        yaml.safe_dump(fixtures.invalid_record(), sort_keys=False),
    )
    proc = run_cli(scripts_dir, "validate_resource_record.py", record)
    assert proc.returncode == 1
    for fragment in (
        "verified-acquisition is for previously untrusted discovery",
        "verification.status verified requires executed and passing resource_proof",
        "independent_behavioral_passed cannot be true unless independent_behavioral_executed is true",
    ):
        assert fragment in proc.stdout, f"missing: {fragment}\n{proc.stdout}"
    assert "missing required field" not in proc.stdout
    assert "unknown field" not in proc.stdout


def test_generated_skill_filled_passes(scripts_dir, tmp_path):
    child = write_skill(tmp_path)
    proc = run_cli(scripts_dir, "validate_skill.py", child)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_generated_skill_unfilled_template_fails(scripts_dir, tmp_path):
    template = (scripts_dir.parent / "templates" / "resource-skill-template.md").read_text(
        encoding="utf-8"
    )
    write_utf8(tmp_path / "SKILL.md", template)
    proc = run_cli(scripts_dir, "validate_skill.py", tmp_path)
    assert proc.returncode == 1
    assert "unresolved template content" in proc.stdout


def test_resource_bundle_valid_cli(scripts_dir, tmp_path):
    child = write_skill(tmp_path / "child")
    record_data = fixtures.matching_widget_record()
    record = write_utf8(
        tmp_path / "record.yaml",
        yaml.safe_dump(record_data, sort_keys=False),
    )
    proc = run_cli(scripts_dir, "validate_resource_bundle.py", record, child)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS: resource-record/generated-skill bundle consistency checks passed" in proc.stdout


def test_resource_bundle_mismatch_cli_fails(scripts_dir, tmp_path):
    child = write_skill(tmp_path / "child")
    record_data = fixtures.matching_widget_record()
    record_data["slug"] = "different-widget"
    record = write_utf8(
        tmp_path / "record.yaml",
        yaml.safe_dump(record_data, sort_keys=False),
    )
    proc = run_cli(scripts_dir, "validate_resource_bundle.py", record, child)
    assert proc.returncode == 1
    assert "Resource slug" in proc.stdout


def test_catalog_valid_cli_reports_fingerprint_and_count(scripts_dir, tmp_path):
    skill = write_skill(tmp_path / "one")
    proc = run_cli(scripts_dir, "validate_skill_catalog.py", "--host", "portable", skill)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS: catalog structural checks passed" in proc.stdout
    assert "CATALOG_FINGERPRINT: sha256:" in proc.stdout
    assert "SKILLS: 1" in proc.stdout


def test_catalog_duplicate_identity_cli_fails(scripts_dir, tmp_path):
    first = write_skill(tmp_path / "first", name="roblox-duplicate-widget")
    second = write_skill(
        tmp_path / "second",
        name="roblox-duplicate-widget",
        description="Use Duplicate Widget for a distinct local rendering capability and cleanup flow.",
        use_when="- Rendering decorative local widget particles for one player's camera.",
    )
    proc = run_cli(
        scripts_dir,
        "validate_skill_catalog.py",
        "--host",
        "portable",
        first,
        second,
    )
    assert proc.returncode == 1
    assert "duplicate skill name" in proc.stdout
    assert "FAIL" in proc.stdout


def test_catalog_overlap_cli_passes_with_routing_warning(scripts_dir, tmp_path):
    first = write_skill(
        tmp_path / "first",
        name="roblox-widget-one",
        description="Use Widget One for synchronized replicated widget sessions and deterministic lifecycle cleanup.",
        use_when="- Synchronizing replicated widget sessions with deterministic cleanup.",
    )
    second = write_skill(
        tmp_path / "second",
        name="roblox-widget-two",
        description="Use Widget Two for synchronized replicated widget sessions and deterministic lifecycle cleanup.",
        use_when="- Synchronizing replicated widget sessions with deterministic cleanup.",
    )
    proc = run_cli(
        scripts_dir,
        "validate_skill_catalog.py",
        "--host",
        "portable",
        first,
        second,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OVERLAP:" in proc.stdout
    assert "overlap clusters require independent catalog-routing tests" in proc.stdout


def test_catalog_accepts_non_generated_routing_competitor_cli(scripts_dir, tmp_path):
    generated = write_skill(
        tmp_path / "generated",
        name="roblox-widget-resource",
        description="Use Widget Resource for synchronized replicated widget sessions and deterministic lifecycle cleanup.",
        use_when="- Synchronizing replicated widget sessions with deterministic cleanup.",
    )
    competitor = tmp_path / "manual-widget-helper"
    competitor.mkdir()
    write_utf8(
        competitor / "SKILL.md",
        "---\n"
        "name: manual-widget-helper\n"
        "description: Use Manual Widget Helper for synchronized replicated widget sessions and deterministic lifecycle cleanup.\n"
        "---\n\n"
        "# Manual Widget Helper\n\n"
        "This host skill is not a generated resource child.\n",
    )
    proc = run_cli(
        scripts_dir,
        "validate_skill_catalog.py",
        "--host",
        "portable",
        "--routing-competitor",
        competitor,
        generated,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "ROUTING_COMPETITORS: 1" in proc.stdout
    assert "OVERLAP:" in proc.stdout
