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
        self.assertEqual(1, receipt["receiptSchemaVersion"])
        self.assertEqual(1, receipt["capabilityReportSchemaVersion"])
        self.assertEqual("passed", receipt["status"])
        workflow = receipt["workflow"]
        self.assertEqual(30648083820, workflow["runId"])
        self.assertEqual(
            "425a1abc668a8192518668bb575cfcca6f1f8fe5",
            workflow["headSha"],
        )
        self.assertEqual(8800371523, workflow["artifactId"])
        self.assertEqual(
            "sha256:edb357cd4ba88af82c6d16e24176dfc61754fc7c90267641d426c6b65dbbf821",
            workflow["artifactDigest"],
        )
        execution_surface = receipt["executionSurface"]
        self.assertEqual(
            "copilot-requests: write",
            execution_surface["permission"],
        )
        self.assertEqual("explicit-allowlist", execution_surface["environmentPolicy"])
        self.assertEqual("auto", execution_surface["requestedModel"])
        self.assertEqual("auto-per-role", execution_surface["modelPolicy"])

    def test_all_roles_pass_with_exact_per_role_model_receipts(self):
        receipt = self.receipt
        checks = receipt["checks"]
        expected_models = {
            "director": "gpt-5-mini",
            "builder": "gpt-5-mini",
            "evaluator": "gpt-5-mini",
        }
        self.assertEqual(
            expected_models,
            receipt["executionSurface"]["resolvedModels"],
        )
        for role, expected_model in expected_models.items():
            self.assertEqual("passed", checks[role]["status"])
            self.assertEqual(expected_model, checks[role]["resolvedModel"])
        browser = checks["browser"]
        self.assertEqual("passed", browser["status"])
        self.assertEqual("passed", checks["sourceIsolation"]["status"])
        self.assertEqual([], browser["externalRequests"])
        self.assertEqual([], browser["blockedRequests"])
        self.assertEqual(0, browser["reducedMotionMaxMs"])
        self.assertEqual(0, browser["reducedPostSubmitMotionMaxMs"])
        self.assertGreater(browser["normalMotionMaxMs"], 0)
        self.assertGreater(browser["normalPostSubmitMotionMaxMs"], 0)
        self.assertTrue(browser["focusStyleChanged"])
        self.assertTrue(browser["formVisibleBefore"])
        self.assertTrue(browser["formVisibleAfter"])

    def test_documentation_and_roadmap_cite_the_receipt_without_completing_lanes(self):
        document = DOCUMENT.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")
        for marker in (
            "Status:** Verified",
            "30648083820",
            "425a1abc668a8192518668bb575cfcca6f1f8fe5",
            "copilot-cli-agent-capability.json",
            "Director resolved model: `gpt-5-mini`",
            "Builder resolved model: `gpt-5-mini`",
            "Evaluator resolved model: `gpt-5-mini`",
            "browser_profile_cleanup.mjs",
        ):
            self.assertIn(marker, document)
        self.assertIn(
            "[x] Verify a repository-scoped controlled agent execution surface",
            roadmap,
        )
        self.assertIn(
            "[sanitized receipt](benchmarks/milestone-0/evidence/copilot-cli-agent-capability.json)",
            roadmap,
        )
        self.assertIn("30648083820", roadmap)
        self.assertIn("[ ] Impeccable alone", roadmap)
        self.assertIn("[ ] current Design Studio", roadmap)
        self.assertIn("[ ] current Design Studio with Impeccable enabled", roadmap)


if __name__ == "__main__":
    unittest.main()
