from __future__ import annotations

import json
from pathlib import Path
import re
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
CORE_RUNNER = ROOT / "scripts" / "run_copilot_cli_agent_capability.py"
GATE_RUNNER = ROOT / "scripts" / "run_copilot_cli_agent_capability_gate.py"


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
        self.assertEqual(31257044809, workflow["runId"])
        self.assertEqual(
            "43c1b6faf136886fa7070e553f420dac0caf1c2b",
            workflow["headSha"],
        )
        self.assertEqual(9021760833, workflow["artifactId"])
        self.assertEqual(
            "sha256:1a29d24c934ef325a3515c83e6dd9a9f6e870405cf1b3758f4c97460b6c2fddc",
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
        self.assertEqual(180, checks["browser"]["normalMotionMaxMs"])
        self.assertTrue(checks["browser"]["reducedSubmissionReplayPerformed"])
        self.assertTrue(checks["browser"]["reducedSubmissionReplayContractPassed"])
        self.assertIsNone(checks["browser"]["reducedSubmissionReplayError"])
        self.assertTrue(checks["browser"]["finalStateStable"])
        self.assertTrue(checks["sourceIsolation"]["renderedCanaryAbsent"])

    def test_documentation_preserves_the_verified_surface_without_the_old_runtime_gate(self):
        """Keep verified capability evidence while retiring the old lane requirement."""
        document = DOCUMENT.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")
        for marker in (
            "Status:** Verified",
            "31257044809",
            "copilot-cli-agent-capability.json",
            "claude-haiku-4.5",
            "gpt-5-mini",
        ):
            self.assertIn(marker, document)

        self.assertIn("Milestone 0 ownership inventory", roadmap)
        self.assertIn("one supported runtime", roadmap)
        self.assertIn("optional research, not a release gate", roadmap)
        self.assertNotIn("- [x] Controlled source-blind", roadmap)
        self.assertNotIn("[ ] current Design Studio with Impeccable enabled", roadmap)

    def test_only_hardened_gate_is_an_executable_entrypoint(self):
        core_source = CORE_RUNNER.read_text(encoding="utf-8")
        gate_source = GATE_RUNNER.read_text(encoding="utf-8")
        document = DOCUMENT.read_text(encoding="utf-8")

        entrypoint = re.compile(r"""if\s+__name__\s*==\s*['"]__main__['"]""")
        self.assertIsNone(entrypoint.search(core_source))
        self.assertIsNotNone(entrypoint.search(gate_source))
        self.assertIn(
            "scripts/run_copilot_cli_agent_capability_gate.py",
            document,
        )
        self.assertIn(
            "scripts/run_copilot_cli_agent_capability.py",
            document,
        )

    def test_contract_job_timeout_covers_browser_regressions(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("  capability-contract:", workflow)
        contract_job = workflow.split("  capability-contract:", 1)[1]
        self.assertIn("    steps:", contract_job)
        contract_header = contract_job.split("    steps:", 1)[0]
        self.assertIn("timeout-minutes: 10", contract_header)

    def test_live_job_timeout_covers_all_role_and_browser_timeouts(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("  live-agent-capability:", workflow)
        live_job = workflow.split("  live-agent-capability:", 1)[1]
        self.assertIn("    steps:", live_job)
        live_header = live_job.split("    steps:", 1)[0]
        self.assertIn("timeout-minutes: 30", live_header)

    def test_output_bound_regressions_are_enforced_by_ci(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            '- "test/test_copilot_cli_output_bounds.py"',
            workflow,
        )
        self.assertIn(
            "python3 -m unittest discover -s test -p 'test_copilot_cli_output_bounds.py' -v",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
