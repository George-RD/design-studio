from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "design-studio"


class DocumentArtifactLaneTests(unittest.TestCase):
    """Acceptance contract for issue #64's paginated document lane."""

    def read(self, path: Path) -> str:
        """Read one repository text artifact as UTF-8."""
        return path.read_text(encoding="utf-8")

    def load(self, path: Path) -> dict:
        """Load one JSON contract fixture or manifest."""
        return json.loads(self.read(path))

    def test_document_requests_route_to_one_progressive_disclosure_procedure(self) -> None:
        """Route page artifacts through one procedure plus existing reusable leaves."""
        router = self.load(SKILL_ROOT / "method-router.json")
        route = next(row for row in router["routes"] if row["id"] == "document-artifact")
        self.assertEqual(["document-create", "document-review"], route["signals"]["task"])
        self.assertEqual(["paginated-artifact"], route["signals"]["surface"])
        self.assertEqual(
            ["references/review/slop.md", "references/review/hierarchy.md"],
            route["leaves"],
        )
        self.assertEqual("references/document/document.md", route["procedure"])

        skill = self.read(SKILL_ROOT / "SKILL.md")
        invocation = self.read(SKILL_ROOT / "invocation.md")
        self.assertIn("| **Document**", skill)
        self.assertIn("paginated artifact", skill.lower())
        self.assertIn("## Document input mapping", invocation)
        self.assertIn("quote", invocation.lower())
        self.assertIn("pdf", invocation.lower())

    def test_existing_interactive_routes_remain_separate_from_documents(self) -> None:
        """Keep existing Studio and Review surface signals out of the new page lane."""
        router = self.load(SKILL_ROOT / "method-router.json")
        routes = {row["id"]: row for row in router["routes"]}
        self.assertEqual(
            ["persuade", "operate", "read", "experience"],
            routes["studio-direction"]["signals"]["surface"],
        )
        self.assertEqual(
            ["persuade", "operate", "read", "experience"],
            routes["review-core"]["signals"]["surface"],
        )
        for route_id in ["studio-direction", "review-core", "review-interaction", "review-motion"]:
            self.assertNotIn("paginated-artifact", routes[route_id]["signals"]["surface"])

    def test_document_procedure_is_renderer_neutral_and_loads_only_page_lenses(self) -> None:
        """Use only medium-appropriate visual methods inside the Document procedure."""
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

    def test_source_blind_roles_accept_rendered_pages_without_document_source(self) -> None:
        """Prove both blind roles forbid source/renderer context while allowing page renders."""
        evaluator = self.read(SKILL_ROOT / "agents" / "evaluator.md")
        director = self.read(SKILL_ROOT / "agents" / "design-agent.md")
        director_isolation = director.split("## Isolation", 1)[1].split("## Inputs", 1)[0]
        evaluator_document = evaluator.split("## Document contract", 1)[1].split("## Pass 1", 1)[0]

        self.assertIn("rendered page", director.lower())
        self.assertIn("component/document source", director_isolation)
        self.assertIn("renderer identity", director_isolation)
        self.assertIn("rendered page", evaluator_document.lower())
        self.assertIn("Renderer identity, source", evaluator_document)
        self.assertIn("unevaluated", evaluator_document.lower())

    def test_runtime_keeps_rendering_optional_and_publishes_a_document_contract(self) -> None:
        """Publish an actual accepted contract without introducing a renderer dependency."""
        workflow = self.read(SKILL_ROOT / "workflow.yaml")
        self.assertRegex(workflow, r"required: \[file_io, shell, isolated_subagents\]")

        document = self.read(SKILL_ROOT / "references" / "document" / "document.md")
        runtime_contract = self.read(SKILL_ROOT / "runtime-contract.md")
        template = self.read(SKILL_ROOT / "assets" / "design-system-skill" / "SKILL.md.template")
        self.assertIn("page_artifact_rendering", document)
        self.assertIn("publish_document_visual_contract", runtime_contract)
        self.assertIn("page-artifact", runtime_contract)
        self.assertIn("renderer", runtime_contract.lower())
        self.assertIn("build-once-unselected", runtime_contract)
        self.assertIn("mechanical-review", runtime_contract)
        self.assertIn("document-visual-contract.json", template)

        schema = self.load(SKILL_ROOT / "references" / "document" / "document-visual-contract.schema.json")
        self.assertEqual(True, schema["properties"]["rendererNeutral"]["const"])
        for field in ["page", "typography", "colour", "spacing", "furniture", "components", "pagination", "qa"]:
            self.assertIn(field, schema["required"])

        fixture_dir = ROOT / "test" / "fixtures" / "document-artifact" / "horaxon-foundation-sprint"
        proposed = fixture_dir / "document-visual-contract.json"
        publisher = SKILL_ROOT / "runtime" / "document-contract" / "index.mjs"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "harness-output" / "design-system" / "document-visual-contract.json"
            run = subprocess.run(
                ["node", str(publisher), str(proposed), str(output)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, run.returncode, run.stderr)
            self.assertTrue(output.is_file())
            published = self.load(output)

        self.assertEqual("paginated-artifact", published["surface"])
        self.assertIs(published["rendererNeutral"], True)
        self.assertEqual("A4", published["page"]["defaultSize"])
        self.assertIn("pagination", published)
        self.assertIn("qa", published)

    def test_mechanical_runtime_normalizes_page_artifact_facts(self) -> None:
        """Join deterministic page facts to the existing current mechanical snapshot."""
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
        self.assertEqual(2, page_pass["pageCount"])
        rules = {finding["ruleId"] for finding in result["findings"]}
        self.assertIn("printable-area-overflow", rules)
        self.assertIn("document-furniture", rules)

    def test_horaxon_fixture_proves_real_quote_contract_consumption(self) -> None:
        """Dogfood the Horaxon page system against the real Avancus quote draft case."""
        fixture_dir = ROOT / "test" / "fixtures" / "document-artifact" / "horaxon-foundation-sprint"
        fixture = self.load(fixture_dir / "fixture.json")
        acceptance = self.load(fixture_dir / "acceptance.json")
        brief = self.read(fixture_dir / fixture["brief"])
        contract = self.load(fixture_dir / fixture["contractArtifact"])

        self.assertEqual("George-RD/horaxon-web#105", fixture["sourceIssue"])
        self.assertEqual("George-RD/avancus#11", fixture["contentEvidence"])
        self.assertIn("A4", fixture["pageSizes"])
        self.assertEqual("document-visual-contract.json", fixture["contractArtifact"])
        self.assertIn("working-sheet", brief)
        self.assertIs(contract["rendererNeutral"], True)
        self.assertGreaterEqual(len(acceptance["functionalChecks"]), 5)
        self.assertIn("renderer-neutral", json.dumps(acceptance).lower())


if __name__ == "__main__":
    unittest.main()
