from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import unittest

from test_method_kernel_routing import matching_route_ids


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "design-studio"
INTENT_RUNTIME = SKILL_ROOT / "runtime" / "design-intent" / "index.mjs"
STUDIO = "workflow.yaml"
REVIEW = "references/review/polish.md"
DOCUMENT = "references/document/document.md"
QUALITY = "references/quality-gates.md"
REVIEW_METHODS = {
    REVIEW,
    "references/review/slop.md",
    "references/review/hierarchy.md",
    "references/review/a11y.md",
}
DOCUMENT_LENSES = {
    "references/document/pagination.md",
    "references/document/tables.md",
    "references/document/furniture.md",
    "references/document/print.md",
}


def section(text: str, heading: str) -> str:
    """Read one required level-two section, failing if its heading is missing."""
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


class DesignIntentLoadingTests(unittest.TestCase):
    """Observe activated authorities at the Design Intent handoff (#88/#90)."""

    @classmethod
    def setUpClass(cls) -> None:
        """Load shipped contracts and the separately documented maintenance budget."""
        cls.contract = json.loads(
            (SKILL_ROOT / "design-intent-contract.json").read_text(encoding="utf-8")
        )
        cls.router = json.loads(
            (SKILL_ROOT / "method-router.json").read_text(encoding="utf-8")
        )
        cls.examples = {
            item["id"]: item["result"] for item in cls.contract["classificationExamples"]
        }
        budget_text = (ROOT / "docs" / "activated-context-budget.md").read_text(encoding="utf-8")
        cls.budget = json.loads(budget_text.split("```json\n", 1)[1].split("```", 1)[0])

    def validated_intent(self, example_id: str) -> dict:
        """Pass an example through the shipped CLI before inspecting its handoff."""
        completed = subprocess.run(
            ["node", str(INTENT_RUNTIME)],
            input=json.dumps(self.examples[example_id]),
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    def document_evaluation_lenses(self) -> set[str]:
        """Resolve the page procedure's actual lens references against expected paths."""
        text = (SKILL_ROOT / DOCUMENT).read_text(encoding="utf-8")
        evaluation = text.split("### 5. Evaluate complete pages", 1)[1].split("\n### ", 1)[0]
        # The Document procedure owns these explicit local lens references.
        basenames = re.findall(r"`([a-z][a-z-]*\.md)`", evaluation)
        paths = {f"references/document/{name}" for name in basenames}
        self.assertEqual(DOCUMENT_LENSES, paths)
        return paths

    def test_review_and_document_activation_exclude_studio_lifecycle(self) -> None:
        """Prevent the original eager Studio dependency in both non-Studio lanes."""
        for example_id in ("interactive-polish", "new-paginated-proposal", "existing-pdf-review"):
            with self.subTest(example=example_id):
                intent = self.validated_intent(example_id)
                activated = set(self.router["coreAuthorities"]) | set(intent["selectedProcedures"])
                self.assertNotIn(STUDIO, activated)

    def test_front_door_prerequisites_do_not_load_studio(self) -> None:
        """Keep classification and host requirements independent of Studio execution."""
        prerequisites = (
            ("invocation.md", "## Host requirements"),
            ("references/design-intent.md", "## Required context"),
        )
        for path, heading in prerequisites:
            with self.subTest(path=path):
                text = (SKILL_ROOT / path).read_text(encoding="utf-8")
                required = section(text, heading)
                self.assertNotIn("`workflow.yaml`", required)
                self.assertIn("`runtime-contract.md`", required)

    def test_universal_path_is_bounded_and_excludes_branch_authorities(self) -> None:
        """Reconcile entry-point declarations with the shared, branch-free hot path."""
        core = set(self.router["coreAuthorities"])
        self.assertEqual(6, len(core))
        self.assertEqual(len(core), len(self.router["coreAuthorities"]))
        hot_path = core | {"SKILL.md", "method-router.json"}
        self.assertEqual(8, len(hot_path))
        self.assertEqual(hot_path, set(self.budget["universalPath"]))
        self.assertEqual(8, len(self.budget["universalPath"]))

        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        declared = set(re.findall(r"^- `([^`]+)`$", section(skill, "## Required references"), re.M))
        self.assertEqual(core | {"method-router.json"}, declared)
        branch_paths = {item["path"] for item in self.router["leaves"]}
        branch_paths.update(self.contract["laneProcedures"])
        branch_paths.update(DOCUMENT_LENSES)
        for route in self.router["routes"]:
            branch_paths.update(route.get("agents", []))
        self.assertTrue(core.isdisjoint(branch_paths))
        for path in hot_path:
            self.assertTrue((SKILL_ROOT / path).is_file(), path)

    def test_representative_handoffs_load_only_selected_authorities_within_budget(self) -> None:
        """Check all six modes against independent selected and excluded method sets."""
        document_methods = {
            DOCUMENT, "references/review/slop.md", "references/review/hierarchy.md", QUALITY,
        } | DOCUMENT_LENSES
        cases = [
            (
                "create-direction", "greenfield-marketing-site", STUDIO,
                {"task": {"studio-direction"}},
                {STUDIO, "references/rationale.md"},
            ),
            (
                "selected-build", "greenfield-marketing-site", STUDIO,
                {"task": {"studio-build"}, "evidence": {"selected-direction", "mechanical-preflight"}},
                {STUDIO, "references/generation.md", QUALITY},
            ),
            (
                "accepted-world-extension", "accepted-world-new-route", STUDIO,
                {}, {STUDIO},
            ),
            (
                "overhaul-preflight", "explicit-interactive-overhaul", STUDIO,
                {"task": {"studio-overhaul"}, "evidence": {"mechanical-preflight"}},
                {STUDIO, "references/overhaul.md", "references/rationale.md", QUALITY},
            ),
            (
                "static-review", "interactive-polish", REVIEW,
                {"task": {"review"}}, REVIEW_METHODS,
            ),
            (
                "interactive-review", "interactive-polish", REVIEW,
                {"task": {"polish"}, "interaction": {"controls", "motion"}, "evidence": {"post-fix-confirmation"}},
                REVIEW_METHODS | {"references/review/interaction.md", QUALITY},
            ),
            (
                "composition-review", "interactive-polish", REVIEW,
                {"task": {"review"}, "evidence": {"composition-artifacts"}},
                REVIEW_METHODS | {"references/copy.md"},
            ),
            (
                "document-create", "new-paginated-proposal", DOCUMENT,
                {"task": {"document-create"}, "evidence": {"mechanical-preflight"}}, document_methods,
            ),
            (
                "document-review", "existing-pdf-review", DOCUMENT,
                {"task": {"document-review"}, "interaction": {"controls", "motion"}, "evidence": {"mechanical-preflight"}},
                document_methods,
            ),
        ]
        self.assertEqual({case[0] for case in cases}, set(self.budget["maxBranchAuthorities"]))
        covered_modes: set[str] = set()
        catalog = {leaf["path"] for leaf in self.router["leaves"]}
        for name, example_id, expected_procedure, signals, expected in cases:
            with self.subTest(case=name):
                intent = self.validated_intent(example_id)
                covered_modes.add(intent["designMode"])
                self.assertEqual([expected_procedure], intent["selectedProcedures"])
                current = {**signals, "surface": {intent["surface"]}}
                matching_ids = matching_route_ids(self.router, current)
                routes = [route for route in self.router["routes"] if route["id"] in matching_ids]
                procedures = {route["procedure"] for route in routes if "procedure" in route}
                self.assertTrue(procedures.issubset(intent["selectedProcedures"]), name)
                leaves = {path for route in routes for path in route["leaves"]}
                self.assertLess(len(leaves), len(catalog), "never load the full method catalog")
                activated = set(intent["selectedProcedures"]) | procedures | leaves
                if expected_procedure == DOCUMENT:
                    activated.update(self.document_evaluation_lenses())
                self.assertEqual(expected, activated)
                self.assertEqual({expected_procedure}, activated & set(self.contract["laneProcedures"]))
                self.assertLessEqual(len(activated), self.budget["maxBranchAuthorities"][name])
                roles = {path for route in routes for path in route.get("agents", [])}
                self.assertLessEqual(len(roles), self.budget["maxRoutedRoleAuthorities"])
                for path in activated | roles:
                    self.assertTrue((SKILL_ROOT / path).is_file(), path)
                if expected_procedure != DOCUMENT:
                    self.assertTrue(activated.isdisjoint(DOCUMENT_LENSES))
        self.assertEqual(set(self.contract["enums"]["designMode"]), covered_modes)

    def test_claude_adapters_load_the_same_universal_entry_not_a_lane(self) -> None:
        """Require command adapters to share the canonical pre-classification entry."""
        hot_path = set(self.budget["universalPath"])
        for name in ("create.md", "review.md"):
            with self.subTest(adapter=name):
                text = (ROOT / "commands" / name).read_text(encoding="utf-8")
                initial = text.split("Resolve `selectedProcedures`", 1)[0]
                files = set(re.findall(r"`skills/design-studio/([^`]+\.(?:md|json|yaml))`", initial))
                self.assertIn("SKILL.md", files)
                self.assertTrue(files.issubset(hot_path))
                self.assertNotIn(STUDIO, files)
                self.assertIn("validated Design Intent", initial)


if __name__ == "__main__":
    unittest.main()
