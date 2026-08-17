"""Fail-fast behavior when PyYAML is unavailable: exit 2, hint, no traceback."""
import os
import subprocess
import sys

import pytest

SCRIPTS = [
    "validate_curated_registry.py",
    "validate_learnings_store.py",
    "validate_resource_record.py",
    "validate_skill.py",
    "validate_skill_catalog.py",
]


@pytest.fixture()
def blocked_yaml_env(tmp_path):
    (tmp_path / "yaml.py").write_text(
        'raise ImportError("pyyaml blocked for testing")\n', encoding="utf-8"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path)
    return env


@pytest.mark.parametrize("script", SCRIPTS)
def test_missing_pyyaml_exits_2_with_hint(scripts_dir, tmp_path, blocked_yaml_env, script):
    target = tmp_path / "input.yaml"
    target.write_text("x: 1\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(scripts_dir / script), str(target)],
        capture_output=True,
        text=True,
        env=blocked_yaml_env,
    )
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "PyYAML is required" in proc.stderr
    assert "pip install -r requirements.txt" in proc.stderr
    assert "Traceback" not in proc.stderr
