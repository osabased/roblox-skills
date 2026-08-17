"""Shared test setup: load the validator scripts as importable modules."""
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

# The scripts import `_common` as a sibling module; make that resolvable when
# they are loaded from here rather than executed as files.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def common():
    return load_script("_common")


@pytest.fixture(scope="session")
def registry_mod():
    return load_script("validate_curated_registry")


@pytest.fixture(scope="session")
def learnings_mod():
    return load_script("validate_learnings_store")


@pytest.fixture(scope="session")
def record_mod():
    return load_script("validate_resource_record")


@pytest.fixture(scope="session")
def skill_mod():
    return load_script("validate_skill")


@pytest.fixture(scope="session")
def scripts_dir():
    return SCRIPTS_DIR
