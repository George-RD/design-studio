from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.6.0"
LEGACY_SURFACE = ROOT / "references" / "methodology.md"
RELEASE_RECORD = ROOT / "docs" / "releases" / "v1.6.0.md"


class V16ReleaseContractTests(unittest.TestCase):
    """Protect issue #53's externally observable v1.6 release boundary."""

    def read(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_product_and_adapter_metadata_publish_one_v16_version(self) -> None:
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
        self.assertEqual(VERSION, evals["version"])
        self.assertRegex(workflow, rf"(?m)^  version: {re.escape(VERSION)}$")

    def test_standard_install_proves_two_representative_hosts(self) -> None:
        workflow = self.read(".github/workflows/validate-agent-skill-install.yml")
        self.assertIn("agent: [codex, claude-code]", workflow)
        self.assertIn('--agent "${{ matrix.agent }}"', workflow)
        self.assertIn("skills@1.5.23", workflow)
        self.assertIn("skills/design-studio", self.read("README.md"))

    def test_final_delete_candidate_is_contracted_without_rewriting_history(self) -> None:
        self.assertFalse(LEGACY_SURFACE.exists())
        migration = json.loads(self.read("docs/migration-map.json"))
        row = next(
            item
            for item in migration["surfaces"]
            if item["path"] == "references/methodology.md"
        )
        self.assertEqual("delete-candidate", row["label"])
        self.assertEqual("authoritative-baseline", migration["status"])

    def test_public_docs_describe_the_single_self_contained_v16_runtime(self) -> None:
        readme = self.read("README.md")
        self.assertIn("## v1.6 product boundary", readme)
        self.assertIn("local deterministic mechanical runtime", readme)
        self.assertIn("Impeccable and Emil Kowalski's skills are credited sources", readme)
        self.assertNotIn("detector: fallback", readme)
        self.assertNotIn("current v1.5 release", readme)

    def test_acceptance_record_cites_each_release_evidence_seam(self) -> None:
        self.assertTrue(RELEASE_RECORD.is_file())
        record = RELEASE_RECORD.read_text(encoding="utf-8")
        required = [
            "Status:** Accepted",
            "36f6e8a2402c657b8e805136291dd7482e5678cf",
            ".github/workflows/validate-agent-skill-install.yml",
            ".github/workflows/runtime-portability.yml",
            "docs/method-authority-map.json",
            "skills/design-studio/method-router.json",
            "skills/design-studio/composition-contract.json",
            "test/test_claude_adapter_compatibility.py",
            "test/test_clean_install_contract.py",
            "references/methodology.md",
            "docs/decisions/0003-claude-adapter-and-deferred-cli.md",
        ]
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, record)


if __name__ == "__main__":
    unittest.main()
