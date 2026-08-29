"""Regression checks for the parent router and internal document navigation."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PARENT = (ROOT / "SKILL.md").read_text(encoding="utf-8")
REFERENCES = {
    path.name: path.read_text(encoding="utf-8")
    for path in (ROOT / "references").glob("*.md")
}


def _mode(name: str) -> str:
    match = re.search(
        rf"^### `{re.escape(name)}`\n(.*?)(?=^### `|^## Shared invariants)",
        PARENT,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"missing parent mode {name!r}"
    return match.group(1)


def _anchor(text: str) -> str:
    text = re.sub(r"[`*_~]", "", text.strip().lower())
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s-]+", "-", text).strip("-")


def _anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        base = _anchor(match.group(1))
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def test_relative_markdown_links_and_anchors_resolve():
    files = [
        ROOT / "SKILL.md",
        *(ROOT / "references").glob("*.md"),
        *(ROOT / "templates").glob("*.md"),
    ]
    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for source in files:
        for target in link_re.findall(source.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("mailto:"):
                continue
            path_part, _, anchor = target.partition("#")
            target_path = source if not path_part else (source.parent / path_part).resolve()
            assert target_path.is_file(), f"{source}: missing link target {target}"
            if anchor:
                assert anchor in _anchors(target_path), f"{source}: missing anchor {target}"


def test_evaluate_compare_stops_before_integration_and_generation():
    section = _mode("evaluate/compare")
    assert "qualification-workflow.md" in section
    assert "state-policy.md" in section
    assert "Do not integrate the resource or generate a child skill as extra scope" in section


def test_acquire_adopt_keeps_child_generation_and_host_adoption_conditional():
    section = _mode("acquire/adopt")
    assert "optional subscopes" in section
    assert "When reusable child guidance is in scope" in section
    assert "generation-validation.md" in section
    assert "When operational host adoption of generated guidance is requested" in section
    assert "operational-lifecycle.md" in section


def test_refresh_preserves_target_bound_proof_and_avoids_default_rediscovery():
    section = _mode("refresh")
    assert "restart broad discovery only when" in section
    assert "Prior runtime proof remains bound to its recorded target" in section
    assert "repair-loop.md" in section


def test_repair_reconcile_keeps_upstream_and_child_revalidation_conditional():
    section = _mode("repair/reconcile")
    assert "qualification-workflow.md" in section
    assert "only when upstream identity, source facts, qualification, or trust are themselves in question" in section
    assert "generation-validation.md" in section
    assert "only for child validation surfaces invalidated by the repair" in section


def test_post_adoption_defect_blocks_host_state_before_repair():
    operational = REFERENCES["operational-lifecycle.md"]
    repair = REFERENCES["repair-loop.md"]
    assert "Mark matching operational entries `blocked`" in operational
    assert "invalidate affected behavioral and catalog-routing passes" in operational
    assert "operational-lifecycle.md#post-adoption-defects" in repair


def test_self_package_repair_requires_explicit_authorization():
    state = REFERENCES["state-policy.md"]
    assert "never edited autonomously" in state
    assert "wait for an explicit yes from the user in chat" in state


def test_reference_file_pointers_are_links_not_bare_code_paths():
    bare_reference = re.compile(r"`references/[A-Za-z0-9_.-]+\.md(?:#[A-Za-z0-9_.-]+)?`")
    for name, text in REFERENCES.items():
        assert not bare_reference.search(text), f"{name}: use a Markdown link for internal reference navigation"


def test_openai_skill_metadata_is_parseable_and_matches_parent_modes():
    data = yaml.safe_load((ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    interface = data["interface"]
    assert interface["display_name"] == "Roblox Resource Acquisition"
    assert interface["short_description"].strip()
    prompt = interface["default_prompt"]
    assert "$roblox-resource-acquisition" in prompt
    for mode in ("evaluate/compare", "acquire/adopt", "refresh", "repair/reconcile"):
        assert mode in prompt
