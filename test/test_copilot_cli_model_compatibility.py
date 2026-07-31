from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_copilot_cli_agent_capability_gate.py"


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


if __name__ == "__main__":
    unittest.main()
