from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import fixtures
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_resource_record import load_record, validate_record
from validate_skill import validate_skill
from validate_skill_catalog import collect_skill_directories, validate_catalog


class ResourceRecordTests(unittest.TestCase):
    def validate(self, record: dict) -> tuple[list[str], list[str]]:
        return validate_record(Path("record.yaml"), record)

    def test_artifact_only_v2_record_passes(self) -> None:
        errors, _ = self.validate(fixtures.valid_record())
        self.assertEqual(errors, [])

    def test_direct_evaluation_target_preserves_provenance_without_trust(self) -> None:
        record = fixtures.valid_record()
        record["discovery_origin"] = "other"
        record["selection_reason"] = "User directly targeted this canonical resource for evaluation only."
        record["trust"] = {"level": "untrusted", "basis": "", "reason": ""}
        errors, _ = self.validate(record)
        self.assertEqual(errors, [])

        record["selection_reason"] = ""
        errors, _ = self.validate(record)
        self.assertIn(
            "discovery_origin other requires selection_reason to preserve selection provenance",
            errors,
        )

    def test_direct_use_target_can_record_explicit_user_trust_separately(self) -> None:
        record = fixtures.valid_record()
        record["discovery_origin"] = "other"
        record["selection_reason"] = "User directly selected this canonical resource for current-task use."
        record["trust"] = {
            "level": "trusted",
            "basis": "explicit-user",
            "reason": "The user directed use of the established canonical identity.",
        }
        errors, _ = self.validate(record)
        self.assertEqual(errors, [])

        record["slug"] = ""
        record["canonical_url"] = ""
        record["package_id"] = ""
        errors, _ = self.validate(record)
        self.assertIn(
            "trusted records require slug to bind trust to a stable identity",
            errors,
        )
        self.assertIn(
            "trusted records require canonical_url or package_id to bind trust to canonical identity",
            errors,
        )

    def test_operational_adoption_requires_every_facet(self) -> None:
        record = fixtures.valid_record()
        record["host_adoptions"] = [fixtures.operational_adoption()]
        errors, _ = self.validate(record)
        self.assertEqual(errors, [])
        record["host_adoptions"][0]["evidence"]["explicit_activation"] = "not-run"
        errors, _ = self.validate(record)
        self.assertTrue(any("explicit_activation: passed" in error for error in errors))

    def test_blocked_disabled_and_removed_states(self) -> None:
        for status, evidence_field, evidence_value in (
            ("blocked", "installed", "present"),
            ("disabled", "enabled", "no"),
            ("removed", "installed", "absent"),
        ):
            record = fixtures.valid_record()
            adoption = fixtures.operational_adoption()
            adoption["status"] = status
            adoption["evidence"][evidence_field] = evidence_value
            record["host_adoptions"] = [adoption]
            errors, _ = self.validate(record)
            self.assertEqual(errors, [], (status, errors))

    def test_reconciliation_mismatch_requires_observed_state(self) -> None:
        record = fixtures.valid_record()
        record["reconciliation"].update(
            {
                "status": "mismatched",
                "checked_at": "2026-08-16",
                "detection_method": "Read project package manifest",
                "result": "Installed state differs",
            }
        )
        errors, _ = self.validate(record)
        self.assertTrue(any("observed installed identity or version" in error for error in errors))

    def test_legacy_record_is_rejected(self) -> None:
        record = fixtures.valid_record()
        del record["schema_version"]
        errors, _ = self.validate(record)
        self.assertTrue(any("legacy records must enter repair/reconcile" in error for error in errors))

    def test_yaml_loader_rejects_legacy_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "legacy.yaml"
            legacy = fixtures.valid_record()
            del legacy["schema_version"]
            path.write_text(yaml.safe_dump(legacy, sort_keys=False), encoding="utf-8")
            loaded = load_record(path)
            errors, _ = validate_record(path, loaded)
            self.assertTrue(errors)

    def test_yaml_loader_normalizes_yes_no_host_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "operational.yaml"
            record = fixtures.valid_record()
            record["host_adoptions"] = [fixtures.operational_adoption()]
            dumped = yaml.safe_dump(record, sort_keys=False).replace(
                "discoverable: 'yes'", "discoverable: yes"
            ).replace("enabled: 'yes'", "enabled: yes")
            path.write_text(dumped, encoding="utf-8")
            loaded = load_record(path)
            errors, _ = validate_record(path, loaded)
            self.assertEqual(errors, [])


class GeneratedSkillTests(unittest.TestCase):
    def write_child(self, root: Path, name: str, description: str, use_when: str) -> Path:
        skill = root / name
        skill.mkdir(parents=True)
        skill.joinpath("SKILL.md").write_text(
            fixtures.valid_skill_text(name=name, description=description, use_when=use_when),
            encoding="utf-8",
        )
        return skill

    def test_valid_reconciliation_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            skill = self.write_child(
                Path(temp),
                "roblox-widget-resource",
                "Use Widget Resource for synchronized widget replication with deterministic lifecycle cleanup.",
                "- Synchronizing replicated widget state across server-owned sessions.",
            )
            errors, _ = validate_skill(skill)
            self.assertEqual(errors, [])

    def test_missing_operational_reconciliation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            skill = self.write_child(
                Path(temp),
                "roblox-widget-resource",
                "Use Widget Resource for synchronized widget replication with deterministic lifecycle cleanup.",
                "- Synchronizing replicated widget state across server-owned sessions.",
            )
            text = skill.joinpath("SKILL.md").read_text(encoding="utf-8")
            start = text.index("## Operational reconciliation")
            end = text.index("## Common path")
            skill.joinpath("SKILL.md").write_text(text[:start] + text[end:], encoding="utf-8")
            errors, _ = validate_skill(skill)
            self.assertTrue(any("Operational reconciliation" in error for error in errors))

    def test_immutable_not_applicable_reconciliation_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            skill = self.write_child(
                Path(temp),
                "roblox-widget-resource",
                "Use Widget Resource for synchronized widget replication with deterministic lifecycle cleanup.",
                "- Synchronizing replicated widget state across server-owned sessions.",
            )
            path = skill / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            text = text.replace(
                "Policy: required — project package manifests can select a different materially version-sensitive release.",
                "Policy: not-applicable — installation is pinned to the exact immutable reviewed package version.",
            ).replace(
                "Installed-state check: Inspect the project package manifest and read the `com.example.widget` version before requiring the module.",
                "Installed-state check: The package lockfile is pinned to the exact immutable `com.example.widget` version `1.2.3`.",
            )
            path.write_text(text, encoding="utf-8")
            errors, _ = validate_skill(skill)
            self.assertEqual(errors, [])

    def test_missing_identity_and_weak_reconciliation_fields_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            skill = self.write_child(
                Path(temp),
                "roblox-widget-resource",
                "Use Widget Resource for synchronized widget replication with deterministic lifecycle cleanup.",
                "- Synchronizing replicated widget state across server-owned sessions.",
            )
            path = skill / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            text = text.replace("- Resource slug: widget-resource\n", "")
            text = text.replace(
                "Installed-state check: Inspect the project package manifest and read the `com.example.widget` version before requiring the module.",
                "Installed-state check: Review project state generally.",
            )
            text = text.replace(
                "Mismatch/unknown action: Stop the affected version-sensitive use and invoke `roblox-resource-acquisition` in `repair/reconcile` mode.",
                "Mismatch/unknown action: Continue cautiously and mention the difference later.",
            )
            text = text.replace(
                "Defect handoff: Capture the task, installed state, expected behavior, observed behavior, and smallest reproduction; then invoke `roblox-resource-acquisition` in `repair/reconcile` mode.",
                "Defect handoff: Mention the problem in the final response.",
            )
            path.write_text(text, encoding="utf-8")
            errors, _ = validate_skill(skill)
            self.assertTrue(any("Resource slug" in error for error in errors))
            self.assertTrue(any("Installed-state check" in error for error in errors))
            self.assertTrue(any("Mismatch/unknown action" in error for error in errors))
            self.assertTrue(any("Defect handoff" in error for error in errors))

    def test_catalog_duplicates_overlap_fingerprint_and_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = self.write_child(
                root,
                "roblox-widget-one",
                "Use Widget One for synchronized replicated widget sessions and deterministic lifecycle cleanup.",
                "- Synchronizing replicated widget sessions with deterministic cleanup.",
            )
            second = self.write_child(
                root,
                "roblox-widget-two",
                "Use Widget Two for synchronized replicated widget sessions and deterministic lifecycle cleanup.",
                "- Synchronizing replicated widget sessions with deterministic cleanup.",
            )
            roots = collect_skill_directories([root])
            errors, _, overlaps, fingerprint = validate_catalog(roots, host="portable")
            self.assertEqual(errors, [])
            self.assertTrue(overlaps)
            reversed_result = validate_catalog(list(reversed(roots)), host="portable")
            self.assertEqual(fingerprint, reversed_result[3])

            duplicate = self.write_child(
                root / "duplicates",
                "roblox-widget-one",
                "Use a distinct child for a completely different rendering capability.",
                "- Rendering local decorative particles for one player.",
            )
            errors, _, _, _ = validate_catalog([first, duplicate], host="portable")
            self.assertTrue(any("duplicate skill name" in error for error in errors))

            same_description = self.write_child(
                root,
                "roblox-widget-three",
                "Use Widget One for synchronized replicated widget sessions and deterministic lifecycle cleanup.",
                "- Rendering local decorative particles for one player.",
            )
            errors, _, _, _ = validate_catalog([first, same_description], host="portable")
            self.assertTrue(any("duplicate normalized description" in error for error in errors))

            long_description = "Use Long Catalog for " + "synchronized routing boundary " * 300
            long_child = self.write_child(
                root,
                "roblox-long-catalog",
                long_description,
                "- Synchronizing a deliberately large routing catalog fixture.",
            )
            _, warnings, _, _ = validate_catalog([long_child, second], host="codex")
            self.assertTrue(any("fallback budget" in warning for warning in warnings))

            unrelated = self.write_child(
                root,
                "roblox-particle-renderer",
                "Use Particle Renderer for decorative local visual bursts and camera-facing sprites.",
                "- Rendering decorative particles locally for one player's camera.",
            )
            errors, _, unrelated_overlaps, _ = validate_catalog([first, unrelated], host="portable")
            self.assertEqual(errors, [])
            self.assertEqual(unrelated_overlaps, [])

    def test_catalog_propagates_invalid_child(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            invalid = self.write_child(
                root,
                "roblox-invalid-child",
                "Use Invalid Child for a deliberately malformed catalog fixture.",
                "- Exercising invalid-child propagation through catalog validation.",
            )
            path = invalid / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            start = text.index("## Operational reconciliation")
            end = text.index("## Common path")
            path.write_text(text[:start] + text[end:], encoding="utf-8")

            errors, _, _, _ = validate_catalog([invalid], host="portable")
            self.assertTrue(any("Operational reconciliation" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
