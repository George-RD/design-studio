from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_copilot_cli_agent_capability_gate.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "boundary-agent-capability.yml"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "run_copilot_cli_model_compatibility", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CopilotCliModelCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_account_model_unavailability_is_blocked(self):
        outcome = self.module.CommandOutcome(
            exit_code=1,
            stdout="",
            stderr='Error: Model "gpt-5.4" from --model flag is not available.',
        )

        self.assertEqual("blocked", self.module.classify_cli_failure(outcome))

    def test_default_requests_auto_selection_for_separate_model_receipting(self):
        self.assertEqual("auto", self.module.DEFAULT_MODEL)

    def test_live_gate_pins_a_public_cli_model_used_by_this_account(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn('COPILOT_MODEL: "claude-haiku-4.5"', workflow)
        self.assertNotIn('COPILOT_MODEL: "gpt-5-mini"', workflow)
        self.assertNotIn('COPILOT_MODEL: "auto"', workflow)

    def test_builder_prompt_preserves_form_and_exact_success_region(self):
        prompt = self.module.core.builder_prompt()

        self.assertIn("Keep the form, label, input and submit control visible", prompt)
        self.assertIn("set its textContent to exactly Capability complete", prompt)
        self.assertIn("no icon or additional text inside that region", prompt)


if __name__ == "__main__":
    unittest.main()
