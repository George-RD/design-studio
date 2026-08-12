from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "benchmarks" / "milestone-0" / "ownership-inventory.json"
SUMMARY_PATH = ROOT / "benchmarks" / "milestone-0" / "OWNERSHIP_INVENTORY.md"
ROADMAP_PATH = ROOT / "ROADMAP.md"

BASELINE_REVISION = "7e8a1df3a9ce6ade1116d804abfc7b1189d61381"
IMPECCABLE_REVISION = "aee6ce9352b842217b3f57c78296a7a4fa35a7f3"
LABEL_ACTIONS = {
    "core": "keep",
    "impeccable": "delegate",
    "external-workflow": "delegate",
    "compatibility": "retain-temporarily",
    "delete": "delete",
}
EXPECTED_CHECK_IDS = {
    "check.visual-director.self-check",
    "check.builder.pre-handoff",
    "check.copy.local-gates",
    "check.evaluator.adversarial-gate",
    "check.quality-gates.fallback-source",
    "check.quality-gates.fallback-browser",
    "check.runtime.final-acceptance",
    "check.review.a11y.contrast-colour",
    "check.review.a11y.structure-names",
    "check.review.a11y.keyboard-focus",
    "check.review.a11y.motion-forms-touch",
    "check.review.hierarchy.per-screen",
    "check.review.hierarchy.rhythm",
    "check.review.interaction.inventory",
    "check.review.interaction.per-control",
    "check.review.interaction.screen-data",
    "check.review.interaction.transitions",
    "check.review.slop.swappable-composition",
    "check.review.slop.unclaimed-defaults",
    "check.review.slop.ux-filler",
    "check.review.slop.product-specificity",
    "check.review.polish.browser-evidence",
    "check.review.polish.act-once",
    "check.meta.change-discipline",
    "check.design-system-template.non-negotiables",
}


class MilestoneZeroOwnershipInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        cls.items = cls.inventory["items"]

    def test_baseline_and_label_contract_are_frozen(self) -> None:
        self.assertEqual(1, self.inventory["schemaVersion"])
        self.assertEqual("baseline", self.inventory["status"])
        baseline = self.inventory["baseline"]
        self.assertEqual("George-RD/design-studio", baseline["repository"])
        self.assertEqual(BASELINE_REVISION, baseline["revision"])
        self.assertEqual(
            {
                "repository": "pbakaus/impeccable",
                "revision": IMPECCABLE_REVISION,
                "license": "Apache-2.0",
            },
            baseline["impeccable"],
        )
        self.assertEqual(set(LABEL_ACTIONS), set(self.inventory["labels"]))
        for label, action in LABEL_ACTIONS.items():
            self.assertEqual(action, self.inventory["labels"][label]["action"])

    def test_every_item_has_one_valid_owner_and_disposition(self) -> None:
        ids = [item["id"] for item in self.items]
        self.assertEqual(len(ids), len(set(ids)), "inventory IDs must be unique")
        for item in self.items:
            with self.subTest(item=item["id"]):
                self.assertIn(item["label"], LABEL_ACTIONS)
                self.assertEqual(LABEL_ACTIONS[item["label"]], item["action"])
                self.assertIn(item["kind"], {"step", "schema", "reference", "check"})
                self.assertTrue(item["reason"].strip())
                self.assertTrue(item["locator"].strip())
                self.assertTrue((ROOT / item["path"]).is_file(), item["path"])
                self.assertTrue(item["evidence"])
                if item["label"] == "core":
                    self.assertIsNone(item["target"])
                else:
                    self.assertIsInstance(item["target"], str)
                    self.assertTrue(item["target"].strip())

    def test_every_workflow_step_is_inventoried_exactly_once(self) -> None:
        workflow = (ROOT / "skills/design-studio/workflow.yaml").read_text(
            encoding="utf-8"
        )
        expected = set(
            re.findall(r"^    - id:\s*([a-z0-9_]+)\s*$", workflow, re.MULTILINE)
        )
        actual = {
            item["locator"].removeprefix("workflow.steps.")
            for item in self.items
            if item["kind"] == "step"
        }
        self.assertEqual(expected, actual)
        self.assertEqual(len(expected), 28)
        self.assertTrue(
            all(item["label"] == "core" for item in self.items if item["kind"] == "step")
        )

    def test_every_workflow_schema_is_inventoried_exactly_once(self) -> None:
        workflow = (ROOT / "skills/design-studio/workflow.yaml").read_text(
            encoding="utf-8"
        )
        schema_block = workflow.split("  schemas:\n", 1)[1].split("\n  agents:\n", 1)[0]
        expected = set(
            re.findall(
                r"^    ([A-Za-z][A-Za-z0-9]*):\s*$",
                schema_block,
                re.MULTILINE,
            )
        )
        actual = {
            item["locator"].removeprefix("workflow.schemas.")
            for item in self.items
            if item["kind"] == "schema"
        }
        self.assertEqual(expected, actual)
        self.assertEqual(len(expected), 8)

    def test_every_runtime_reference_and_compatibility_surface_is_covered(self) -> None:
        reference_root = ROOT / "skills/design-studio/references"
        expected = {
            path.relative_to(ROOT).as_posix()
            for path in reference_root.rglob("*.md")
        }
        expected.update(
            {
                "skills/design-studio/SKILL.md",
                "skills/design-studio/workflow.yaml",
                "skills/design-studio/agents/design-agent.md",
                "skills/design-studio/agents/evaluator.md",
                "skills/design-studio/evals/evals.json",
                "skills/design-studio/assets/design-system-skill/README.md",
                "skills/design-studio/assets/design-system-skill/SKILL.md.template",
                "commands/create.md",
                "commands/review.md",
                "agents/design-agent.md",
                "agents/evaluator.md",
                "references/methodology.md",
            }
        )
        actual = {
            item["path"] for item in self.items if item["kind"] == "reference"
        }
        self.assertEqual(expected, actual)

    def test_every_enumerated_check_family_has_members_and_an_owner(self) -> None:
        checks = {item["id"]: item for item in self.items if item["kind"] == "check"}
        self.assertEqual(EXPECTED_CHECK_IDS, set(checks))
        self.assertEqual(
            156,
            sum(len(item["members"]) for item in checks.values()),
        )
        for check in checks.values():
            with self.subTest(check=check["id"]):
                self.assertGreater(len(check["members"]), 0)
                self.assertEqual(len(check["members"]), len(set(check["members"])))
                self.assertTrue(all(member.strip() for member in check["members"]))

    def test_duplicate_review_and_fallback_work_are_not_marked_core(self) -> None:
        by_id = {item["id"]: item for item in self.items}
        self.assertEqual(
            "impeccable",
            by_id[
                "reference.skills.design.studio.references.review.polish.md"
            ]["label"],
        )
        self.assertEqual(
            "compatibility",
            by_id["reference.commands.review.md"]["label"],
        )
        self.assertEqual(
            "delete",
            by_id["check.quality-gates.fallback-source"]["label"],
        )
        self.assertEqual(
            "delete",
            by_id["check.quality-gates.fallback-browser"]["label"],
        )
        self.assertEqual(
            "external-workflow",
            by_id["check.copy.local-gates"]["label"],
        )
        self.assertEqual(
            "delete",
            by_id["reference.references.methodology.md"]["label"],
        )

    def test_summary_counts_are_derived_from_items(self) -> None:
        summary = self.inventory["summary"]
        self.assertEqual(len(self.items), summary["items"])
        self.assertEqual(
            dict(sorted(Counter(item["kind"] for item in self.items).items())),
            summary["byKind"],
        )
        self.assertEqual(
            dict(sorted(Counter(item["label"] for item in self.items).items())),
            summary["byLabel"],
        )
        self.assertEqual(
            sum(
                len(item.get("members", []))
                for item in self.items
                if item["kind"] == "check"
            ),
            summary["checkMembers"],
        )

    def test_roadmap_records_evidence_without_claiming_comparison_complete(self) -> None:
        roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "- [x] Inventory every Design Studio step, reference, schema and check.",
            roadmap,
        )
        self.assertIn(
            "- [x] Identify workflows that only reproduce an Impeccable command",
            roadmap,
        )
        self.assertIn(
            "benchmarks/milestone-0/OWNERSHIP_INVENTORY.md",
            roadmap,
        )
        self.assertIn(
            "- [ ] Confirm the smallest differentiated product:",
            roadmap,
        )
        self.assertIn("- [ ] Run the same fixed briefs through:", roadmap)
        self.assertTrue(SUMMARY_PATH.is_file())


if __name__ == "__main__":
    unittest.main()
