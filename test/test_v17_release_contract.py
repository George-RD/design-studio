from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.7.0"
PRE_RELEASE_BASE = "066000c10b358744554a1e8d2028cb965c5e25b6"
RELEASE_RECORD = ROOT / "docs" / "releases" / "v1.7.0.md"


class V17ReleaseContractTests(unittest.TestCase):
    """Protect issue #77's repository-owned v1.7 product identity under #74."""

    def read(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_product_and_adapter_metadata_publish_one_v17_version(self) -> None:
        skill = self.read("skills/design-studio/SKILL.md")
        match = re.search(r"^version:\s*([^\s]+)", skill, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(VERSION, match.group(1))

        plugin = json.loads(self.read(".claude-plugin/plugin.json"))
        marketplace = json.loads(self.read(".claude-plugin/marketplace.json"))
        marketplace_plugin = next(
            row for row in marketplace["plugins"] if row["name"] == "design-studio"
        )
        self.assertEqual(VERSION, plugin["version"])
        self.assertEqual(VERSION, marketplace_plugin["version"])

        evals = json.loads(self.read("skills/design-studio/evals/evals.json"))
        workflow = self.read("skills/design-studio/workflow.yaml")
        self.assertNotIn("version", evals)
        self.assertIsNone(re.search(r"(?m)^  version:\s*", workflow))

    def test_public_install_proof_keeps_reproducible_and_drift_signals(self) -> None:
        workflow = self.read(".github/workflows/validate-agent-skill-install.yml")
        self.assertIn("agent: [codex, claude-code]", workflow)
        self.assertIn("skills@1.5.23", workflow)
        self.assertIn("public-source-install:", workflow)
        self.assertIn("George-RD/design-studio", workflow)
        self.assertIn("advisory-latest-installer:", workflow)
        self.assertIn("continue-on-error: true", workflow)
        self.assertIn("test/test_public_source_install_contract.py", workflow)

    def test_document_lane_remains_first_class(self) -> None:
        skill = self.read("skills/design-studio/SKILL.md")
        self.assertIn("| **Studio** |", skill)
        self.assertIn("| **Review** |", skill)
        self.assertIn("| **Document** |", skill)
        self.assertTrue((ROOT / "skills/design-studio/references/document/document.md").is_file())
        self.assertTrue((ROOT / "test/test_document_artifact_lane.py").is_file())

    def test_public_docs_describe_the_current_product_boundary(self) -> None:
        readme = self.read("README.md")
        required = [
            "## Lanes",
            "**Studio**",
            "**Review**",
            "**Document**",
            "## v1.7 product boundary",
            "npx skills add George-RD/design-studio",
            "not a Design Studio runtime dependency",
            "optional, thin adapter",
            "local deterministic mechanical runtime",
            "Impeccable and Emil Kowalski's skills are credited sources",
        ]
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, readme)
        self.assertNotIn("## v1.6 product boundary", readme)
        self.assertNotIn("/design-studio:document", readme)

    def test_release_candidate_record_cites_each_v17_evidence_seam(self) -> None:
        self.assertTrue(RELEASE_RECORD.is_file())
        record = RELEASE_RECORD.read_text(encoding="utf-8")
        required = [
            "**Status:** Prepared",
            "#74",
            "#77",
            PRE_RELEASE_BASE,
            ".github/workflows/validate-agent-skill-install.yml",
            ".github/workflows/runtime-portability.yml",
            "test/test_runtime_contract.py",
            "test/test_document_artifact_lane.py",
            "test/test_public_source_install_contract.py",
            "docs/decisions/0003-claude-adapter-and-deferred-cli.md",
            "docs/decisions/0004-installer-compatibility-proof.md",
            "#78",
        ]
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, record)


if __name__ == "__main__":
    unittest.main()
