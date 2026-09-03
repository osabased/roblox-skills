import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "system-review"
MANIFEST_PATH = Path(__file__).with_name("scenarios.json")


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


class SystemReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = read_text("system-review/SKILL.md")
        cls.reference = read_text(
            "system-review/references/cross-agent-synthesis.md"
        )
        cls.readme = read_text("README.md")
        cls.metadata = read_text("system-review/agents/openai.yaml")
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_states_verification_limit(self) -> None:
        purpose = self.manifest.get("purpose", "").casefold()
        self.assertIn("does not execute a language model", purpose)

    def test_required_scenarios_are_recorded_once(self) -> None:
        required = {
            "local-code-review-routes-away",
            "roblox-organization-routes-away",
            "resource-selection-routes-away",
            "subjective-choice-routes-away",
            "retry-failure-invokes-system-review",
            "missing-evidence-is-a-visibility-gap",
            "duplicate-symptoms-collapse-to-root-cause",
            "clean-review-can-pass",
            "multiple-corrections-hand-off-direction",
            "cross-agent-round-is-bounded",
        }
        scenarios = self.manifest.get("scenarios", [])
        ids = [scenario.get("id") for scenario in scenarios]
        self.assertEqual(len(ids), len(set(ids)), "scenario IDs must be unique")
        self.assertTrue(required.issubset(ids), required - set(ids))

    def test_each_scenario_has_contract_evidence(self) -> None:
        for scenario in self.manifest["scenarios"]:
            with self.subTest(scenario=scenario["id"]):
                self.assertTrue(scenario.get("prompt", "").strip())
                self.assertTrue(scenario.get("expected_owner", "").strip())
                self.assertTrue(scenario.get("expected_behavior", "").strip())
                checks = scenario.get("checks", [])
                self.assertTrue(checks, "scenario must cite contract evidence")

                for check in checks:
                    path = REPO_ROOT / check["path"]
                    self.assertTrue(path.is_file(), f"missing contract file: {path}")
                    content = path.read_text(encoding="utf-8").casefold()
                    needle = check["contains"].casefold()
                    self.assertIn(needle, content)

    def test_catalogue_names_one_owner_for_each_problem_class(self) -> None:
        expected_rows = (
            "Materially different consequential directions remain competitive",
            "A consequential subjective choice is unresolved",
            "A defined system may fail across components or operational conditions",
            "Roblox DataModel placement, runtime ownership, entrypoints",
            "A Roblox community resource must be found, qualified, adopted, refreshed, or repaired",
        )
        for row in expected_rows:
            with self.subTest(row=row):
                self.assertIn(row, self.readme)

        for skill in (
            "direction-selection",
            "subjective-taste-alignment",
            "system-review",
            "structure-roblox-projects",
            "roblox-resource-acquisition",
        ):
            with self.subTest(skill=skill):
                self.assertIn(f"./{skill}/", self.readme)

        self.assertIn("## Repository guidance", self.readme)
        self.assertIn("It is not a skill", self.readme)

    def test_main_skill_has_one_completion_criterion_per_step(self) -> None:
        headings = [
            line for line in self.skill.splitlines() if line.startswith("## ")
        ]
        numbered = [line for line in headings if line[3:4].isdigit()]
        self.assertEqual(5, len(numbered))
        self.assertEqual(5, self.skill.count("**Complete when:**"))

    def test_direction_selection_handoff_is_explicit(self) -> None:
        self.assertIn("System review owns diagnosis", self.skill)
        self.assertIn("Direction handoff", self.skill)
        self.assertIn("Hand the decision to `direction-selection`", self.skill)
        self.assertIn("$direction-selection", self.metadata)

    def test_cross_agent_synthesis_is_conditional_reference(self) -> None:
        self.assertTrue(
            (SKILL_DIR / "references" / "cross-agent-synthesis.md").is_file()
        )
        self.assertFalse(
            (REPO_ROOT / "cross-agent-synthesis").exists(),
            "cross-agent synthesis should not be a standalone catalogue skill",
        )
        self.assertIn(
            "read [references/cross-agent-synthesis.md]",
            self.skill.casefold(),
        )
        self.assertEqual(4, self.reference.count("**Complete when:**"))

    def test_frontmatter_preserves_catalogue_boundaries(self) -> None:
        description = self.skill.split("---", 2)[1]
        for phrase in (
            "interactions among multiple components",
            "Skip ordinary local code review",
            "Roblox organization-only work",
            "selection among competing replacement directions",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.casefold(), description.casefold())
        self.assertNotIn("disable-model-invocation", description)


if __name__ == "__main__":
    unittest.main()
