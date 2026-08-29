from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "design-studio"
VERSION = "1.7.0"


class DocumentArtifactLaneTests(unittest.TestCase):
    """Acceptance contract for issue #64's paginated document lane."""

    def read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def load(self, path: Path) -> dict:
        return json.loads(self.read(path))

    def test_document_requests_route_to_one_progressive_disclosure_leaf(self) -> None:
        router = self.load(SKILL_ROOT / "method-router.json")
        route = next(row for row in router["routes"] if row["id"] == "document-artifact")
        self.assertEqual(["document-create", "document-review"], route["signals"]["task"])
        self.assertEqual(["paginated-artifact"], route["signals"]["surface"])
        self.assertEqual(["references/document/document.md"], route["leaves"])

        skill = self.read(SKILL_ROOT / "SKILL.md")
        invocation = self.read(SKILL_ROOT / "invocation.md")
        self.assertIn("| **Document**", skill)
        self.assertIn("paginated artifact", skill.lower())
        self.assertIn("## Document input mapping", invocation)
        self.assertIn("quote", invocation.lower())
        self.assertIn("pdf", invocation.lower())

    def test_document_leaf_is_renderer_neutral_and_loads_only_document_lenses(self) -> None:
        document = self.read(SKILL_ROOT / "references" / "document" / "document.md")
        for marker in [
            "A4",
            "Letter",
            "document-visual-contract.json",
            "references/review/hierarchy.md",
            "references/review/slop.md",
            "pagination.md",
            "tables.md",
            "furniture.md",
            "print.md",
        ]:
            self.assertIn(marker, document)
        self.assertNotIn("references/review/interaction.md", document)
        self.assertIn("renderer-neutral", document.lower())

        for name in ["pagination.md", "tables.md", "furniture.md", "print.md"]:
            text = self.read(SKILL_ROOT / "references" / "document" / name)
            self.assertIn("severity", text)
            self.assertIn("evidence", text)
            self.assertIn("status", text)

    def test_source_blind_roles_accept_rendered_pages_without_renderer_identity(self) -> None:
        evaluator = self.read(SKILL_ROOT / "agents" / "evaluator.md")
        director = self.read(SKILL_ROOT / "agents" / "design-agent.md")
        self.assertIn("## Document contract", evaluator)
        self.assertIn("rendered page", evaluator.lower())
        self.assertIn("renderer identity", evaluator.lower())
        self.assertIn("unevaluated", evaluator.lower())
        self.assertIn("rendered page", director.lower())

    def test_runtime_keeps_rendering_optional_and_emits_document_visual_contract(self) -> None:
        workflow = self.read(SKILL_ROOT / "workflow.yaml")
        self.assertRegex(workflow, r"required: \[file_io, shell, isolated_subagents\]")
        self.assertIn("page_artifact_rendering", workflow)
        self.assertIn("documentVisualContract: harness-output/design-system/document-visual-contract.json", workflow)
        self.assertRegex(workflow, r"outputs: \[[^\n]*documentVisualContract[^\n]*\]")

        contract = self.read(SKILL_ROOT / "runtime-contract.md")
        self.assertIn("page-artifact", contract)
        self.assertIn("renderer", contract.lower())
        self.assertIn("build-once-unselected", contract)
        self.assertIn("mechanical-review", contract)

    def test_mechanical_runtime_normalizes_page_artifact_facts(self) -> None:
        runtime = SKILL_ROOT / "runtime" / "mechanical" / "index.mjs"
        payload = {
            "schemaVersion": 1,
            "generatedAt": "2026-08-29T12:00:00Z",
            "source": {
                "target": "document source",
                "completed": False,
                "reason": "source intentionally hidden from visual review",
            },
            "browser": [],
            "pageArtifacts": [
                {
                    "target": "horaxon-foundation-sprint-quote.pdf",
                    "completed": True,
                    "pageCount": 2,
                    "pageSize": {"name": "A4", "widthMm": 210, "heightMm": 297},
                    "printableAreaOverflowFailures": [
                        {
                            "location": "page 2",
                            "value": "right edge",
                            "evidence": "Content exceeds the printable area on page 2.",
                        }
                    ],
                    "clippedContentFailures": [],
                    "furnitureFailures": [
                        {
                            "location": "page 2 footer",
                            "value": "page-number",
                            "evidence": "The required page number is absent.",
                        }
                    ],
                    "printContrastFailures": [],
                }
            ],
            "waivers": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            run = subprocess.run(
                ["node", str(runtime), str(input_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(0, run.returncode, run.stderr)
        result = json.loads(run.stdout)
        page_pass = next(row for row in result["passes"] if row["kind"] == "page-artifact")
        self.assertEqual("horaxon-foundation-sprint-quote.pdf", page_pass["target"])
        rules = {finding["ruleId"] for finding in result["findings"]}
        self.assertIn("printable-area-overflow", rules)
        self.assertIn("document-furniture", rules)

    def test_horaxon_fixture_proves_a4_document_contract_consumption(self) -> None:
        fixture_dir = ROOT / "test" / "fixtures" / "document-artifact" / "horaxon-foundation-sprint"
        fixture = self.load(fixture_dir / "fixture.json")
        acceptance = self.load(fixture_dir / "acceptance.json")
        self.assertEqual("George-RD/horaxon-web#105", fixture["sourceIssue"])
        self.assertIn("A4", fixture["pageSizes"])
        self.assertEqual("document-visual-contract.json", fixture["contractArtifact"])
        self.assertGreaterEqual(len(acceptance["functionalChecks"]), 5)
        self.assertIn("renderer-neutral", json.dumps(acceptance).lower())

    def test_current_product_version_is_synchronized_after_the_new_lane(self) -> None:
        skill = self.read(SKILL_ROOT / "SKILL.md")
        match = re.search(r"^version:\s*([^\s]+)", skill, re.MULTILINE)
        self.assertIsNotNone(match)
        plugin = self.load(ROOT / ".claude-plugin" / "plugin.json")
        marketplace = self.load(ROOT / ".claude-plugin" / "marketplace.json")
        marketplace_plugin = next(row for row in marketplace["plugins"] if row["name"] == "design-studio")
        evals = self.load(SKILL_ROOT / "evals" / "evals.json")
        workflow = self.read(SKILL_ROOT / "workflow.yaml")
        self.assertEqual(VERSION, match.group(1))
        self.assertEqual(VERSION, plugin["version"])
        self.assertEqual(VERSION, marketplace_plugin["version"])
        self.assertEqual(VERSION, evals["version"])
        self.assertRegex(workflow, rf"(?m)^  version: {re.escape(VERSION)}$")


if __name__ == "__main__":
    unittest.main()
