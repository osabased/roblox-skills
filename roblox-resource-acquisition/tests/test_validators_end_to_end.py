"""End-to-end CLI runs of all four validators against known-good/bad fixtures."""
import subprocess
import sys

import fixtures


def run_cli(scripts_dir, script, *args):
    return subprocess.run(
        [sys.executable, str(scripts_dir / script), *map(str, args)],
        capture_output=True,
        text=True,
    )


def test_registry_valid(scripts_dir, tmp_path):
    (tmp_path / "evaera-promise.yaml").write_text(fixtures.VALID_REGISTRY_ENTRY)
    proc = run_cli(scripts_dir, "validate_curated_registry.py", tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS: curated registry structural/identity checks passed" in proc.stdout


def test_registry_invalid_fails_for_seeded_defects(scripts_dir, tmp_path):
    (tmp_path / "bad.yaml").write_text(fixtures.INVALID_REGISTRY_ENTRY)
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
    (tmp_path / "a.yaml").write_text(fixtures.VALID_REGISTRY_ENTRY)
    (tmp_path / "b.yaml").write_text(fixtures.VALID_REGISTRY_ENTRY)
    proc = run_cli(scripts_dir, "validate_curated_registry.py", tmp_path)
    assert proc.returncode == 1
    assert "duplicate slug 'evaera-promise'" in proc.stdout


def test_learnings_valid(scripts_dir, tmp_path):
    (tmp_path / "2026-08-11-gotcha.yaml").write_text(fixtures.VALID_LEARNING)
    proc = run_cli(scripts_dir, "validate_learnings_store.py", tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "WARN" not in proc.stdout


def test_learnings_invalid(scripts_dir, tmp_path):
    (tmp_path / "2026-08-11-broken.yaml").write_text(fixtures.INVALID_LEARNING)
    proc = run_cli(scripts_dir, "validate_learnings_store.py", tmp_path)
    assert proc.returncode == 1
    assert "resource-scoped entries require a non-empty slug" in proc.stdout
    assert "observed must be YYYY-MM-DD" in proc.stdout


def test_learnings_directive_warns_but_passes(scripts_dir, tmp_path):
    (tmp_path / "2026-08-11-directive.yaml").write_text(fixtures.DIRECTIVE_LEARNING)
    proc = run_cli(scripts_dir, "validate_learnings_store.py", tmp_path)
    assert proc.returncode == 0
    assert "WARN" in proc.stdout
    assert "reads as an imperative directive" in proc.stdout


def test_record_valid(scripts_dir, tmp_path):
    record = tmp_path / "record.yaml"
    record.write_text(fixtures.VALID_RECORD)
    proc = run_cli(scripts_dir, "validate_resource_record.py", record)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "curation establishes trust, not runtime verification" in proc.stdout


def test_record_invalid_fails_state_consistency(scripts_dir, tmp_path):
    record = tmp_path / "record.yaml"
    record.write_text(fixtures.INVALID_RECORD)
    proc = run_cli(scripts_dir, "validate_resource_record.py", record)
    assert proc.returncode == 1
    for fragment in (
        "verified-acquisition is for previously untrusted discovery",
        "verification.status verified requires executed and passing resource_proof",
        "independent_behavioral_passed cannot be true unless independent_behavioral_executed is true",
    ):
        assert fragment in proc.stdout, f"missing: {fragment}\n{proc.stdout}"


def test_generated_skill_filled_passes(scripts_dir, tmp_path):
    (tmp_path / "SKILL.md").write_text(fixtures.FILLED_SKILL)
    proc = run_cli(scripts_dir, "validate_skill.py", tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_generated_skill_unfilled_template_fails(scripts_dir, tmp_path):
    template = (
        scripts_dir.parent / "templates" / "resource-skill-template.md"
    ).read_text()
    (tmp_path / "SKILL.md").write_text(template)
    proc = run_cli(scripts_dir, "validate_skill.py", tmp_path)
    assert proc.returncode == 1
    assert "unresolved template content" in proc.stdout
