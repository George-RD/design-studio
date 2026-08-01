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
WORKFLOW = ROOT / ".github" / "workflows" / "boundary-agent-capability.yml"


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
        self.assertEqual(30643540826, workflow["runId"])
        self.assertEqual(
            "6f21c4ec32ab34a2974db607a3197d5e586a86a7",
            workflow["headSha"],
        )
        self.assertEqual(8798533579, workflow["artifactId"])
        self.assertEqual(
            "sha256:685e259ce6478dadd6078297a16ccace7379d4aa9d43167b169ad2be0003af04",
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
            "director": "claude-haiku-4.5",
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
        self.assertEqual("passed", checks["browser"]["status"])
        self.assertEqual("passed", checks["sourceIsolation"]["status"])
        self.assertEqual([], checks["browser"]["externalRequests"])
        self.assertEqual(0, checks["browser"]["reducedMotionMaxMs"])

    def test_documentation_and_roadmap_cite_the_receipt_without_completing_lanes(self):
        document = DOCUMENT.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")
        for marker in (
            "Status:** Verified",
            "30643540826",
            "copilot-cli-agent-capability.json",
            "claude-haiku-4.5",
            "gpt-5-mini",
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
        self.assertIn("30643540826", roadmap)
        self.assertIn("[ ] Impeccable alone", roadmap)
        self.assertIn("[ ] current Design Studio", roadmap)
        self.assertIn("[ ] current Design Studio with Impeccable enabled", roadmap)


    def test_live_job_timeout_covers_all_role_and_browser_timeouts(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        live_job = workflow.split("  live-agent-capability:", 1)[1]
        live_header = live_job.split("    steps:", 1)[0]
        self.assertIn("timeout-minutes: 30", live_header)


if __name__ == "__main__":
    unittest.main()
