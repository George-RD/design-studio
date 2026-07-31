from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = (
    ROOT
    / "benchmarks"
    / "milestone-0"
    / "evidence"
    / "copilot-cli-agent-capability.json"
)
DOCUMENT = ROOT / "benchmarks" / "milestone-0" / "AGENT_HARNESS.md"
ROADMAP = ROOT / "ROADMAP.md"


class CopilotCliAgentReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    def test_receipt_preserves_exact_passing_workflow(self):
        receipt = self.receipt
        self.assertEqual(1, receipt["schemaVersion"])
        self.assertEqual("passed", receipt["status"])
        workflow = receipt["workflow"]
        self.assertEqual(30620834185, workflow["runId"])
        self.assertEqual(
            "e8149f131c433b8131bf556fd46d16d710473b92",
            workflow["headSha"],
        )
        self.assertEqual(8789344449, workflow["artifactId"])
        self.assertEqual(
            "sha256:166c95d5531ab8148caeeb4781efd497c5041bdcbe2e54ecdbec68d069d19a32",
            workflow["artifactDigest"],
        )

    def test_all_roles_pass_and_resolve_to_one_model(self):
        checks = self.receipt["checks"]
        for role in ("director", "builder", "evaluator"):
            self.assertEqual("passed", checks[role]["status"])
        models = {
            checks[role]["resolvedModel"]
            for role in ("director", "builder", "evaluator")
        }
        self.assertEqual({"gpt-5-mini"}, models)
        self.assertEqual("passed", checks["browser"]["status"])
        self.assertEqual("passed", checks["sourceIsolation"]["status"])
        self.assertEqual([], checks["browser"]["externalRequests"])
        self.assertEqual(0, checks["browser"]["reducedMotionMaxMs"])

    def test_documentation_and_roadmap_cite_the_receipt_without_completing_lanes(self):
        document = DOCUMENT.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")
        for marker in (
            "Status:** Verified",
            "30620834185",
            "copilot-cli-agent-capability.json",
            "gpt-5-mini",
        ):
            self.assertIn(marker, document)
        self.assertIn(
            "[x] Verify a repository-scoped controlled agent execution surface",
            roadmap,
        )
        self.assertIn("[ ] Impeccable alone", roadmap)
        self.assertIn("[ ] current Design Studio", roadmap)
        self.assertIn("[ ] current Design Studio with Impeccable enabled", roadmap)


if __name__ == "__main__":
    unittest.main()
