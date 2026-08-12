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

    def test_baseline_and_label_contract_are_frozen(self) -> None:
        self.assertEqual(1, self.inventory["schemaVersion"])
        self.assertEqual("baseline", self.inventory["status"])
        baseline = self.inventory["baseline"]
        self.assertEqual("George-RD/design-studio", baseline["repository"])
        self.assertEqual(BASELINE_REVISION, baseline["revision"])
        self.assertEqual(
            ["pbakaus/impeccable", IMPECCABLE_REVISION, "Apache-2.0"],
            baseline["impeccable"],
        )
        self.assertEqual(LABEL_ACTIONS, self.inventory["labels"])

    def test_every_workflow_step_is_inventoried_exactly_once(self) -> None:
        workflow = (ROOT / "skills/design-studio/workflow.yaml").read_text(
            encoding="utf-8"
        )
        expected = set(
            re.findall(r"^    - id:\s*([a-z0-9_]+)\s*$", workflow, re.MULTILINE)
        )
        grouped = self.inventory["steps"]
        actual = [item for names in grouped.values() for item in names]
        self.assertEqual(len(actual), len(set(actual)))
        self.assertEqual(expected, set(actual))
        self.assertEqual({"core"}, set(grouped))
        self.assertEqual(28, len(actual))

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
        grouped = self.inventory["schemas"]
        actual = [item for names in grouped.values() for item in names]
        self.assertEqual(len(actual), len(set(actual)))
        self.assertEqual(expected, set(actual))
        self.assertEqual({"core"}, set(grouped))
        self.assertEqual(8, len(actual))

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
        rows = self.inventory["references"]
        paths = [row[0] for row in rows]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(expected, set(paths))
        for path, label, target, reason in rows:
            with self.subTest(path=path):
                self.assertIn(label, LABEL_ACTIONS)
                self.assertTrue((ROOT / path).is_file())
                self.assertTrue(reason.strip())
                self.assertEqual(label == "core", not target)

    def test_every_enumerated_check_family_has_members_and_an_owner(self) -> None:
        rows = self.inventory["checks"]
        checks = {row[0]: row for row in rows}
        self.assertEqual(len(rows), len(checks))
        self.assertEqual(EXPECTED_CHECK_IDS, set(checks))
        self.assertEqual(156, sum(len(row[5]) for row in rows))
        for check_id, path, locator, label, target, members in rows:
            with self.subTest(check=check_id):
                self.assertTrue((ROOT / path).is_file())
                self.assertTrue(locator.strip())
                self.assertIn(label, LABEL_ACTIONS)
                self.assertEqual(label == "core", not target)
                self.assertGreater(len(members), 0)
                self.assertEqual(len(members), len(set(members)))
                self.assertTrue(
                    all(
                        re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", member)
                        for member in members
                    )
                )

    def test_duplicate_review_and_fallback_work_are_not_marked_core(self) -> None:
        references = {row[0]: row for row in self.inventory["references"]}
        checks = {row[0]: row for row in self.inventory["checks"]}
        self.assertEqual(
            "impeccable",
            references["skills/design-studio/references/review/polish.md"][1],
        )
        self.assertEqual("compatibility", references["commands/review.md"][1])
        self.assertEqual("delete", checks["check.quality-gates.fallback-source"][3])
        self.assertEqual("delete", checks["check.quality-gates.fallback-browser"][3])
        self.assertEqual("external-workflow", checks["check.copy.local-gates"][3])
        self.assertEqual("delete", references["references/methodology.md"][1])

    def test_summary_counts_are_derived_from_inventory(self) -> None:
        label_counts = Counter()
        kind_counts = Counter()
        for label, names in self.inventory["steps"].items():
            kind_counts["step"] += len(names)
            label_counts[label] += len(names)
        for label, names in self.inventory["schemas"].items():
            kind_counts["schema"] += len(names)
            label_counts[label] += len(names)
        for _path, label, _target, _reason in self.inventory["references"]:
            kind_counts["reference"] += 1
            label_counts[label] += 1
        for _id, _path, _locator, label, _target, _members in self.inventory["checks"]:
            kind_counts["check"] += 1
            label_counts[label] += 1

        summary = self.inventory["summary"]
        self.assertEqual(sum(kind_counts.values()), summary["items"])
        self.assertEqual(dict(sorted(kind_counts.items())), summary["byKind"])
        self.assertEqual(dict(sorted(label_counts.items())), summary["byLabel"])
        self.assertEqual(
            sum(len(row[5]) for row in self.inventory["checks"]),
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
