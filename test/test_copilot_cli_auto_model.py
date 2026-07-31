from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_copilot_cli_agent_capability_gate.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "run_copilot_cli_auto_model", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CopilotCliAutoModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_resolved_model_is_read_from_session_evidence(self):
        events = [
            {"type": "assistant.message", "data": {"content": "done"}},
            {"type": "session.idle", "data": {"model": "gpt-5.3-codex"}},
        ]

        self.assertEqual(
            "gpt-5.3-codex",
            self.module.resolved_model_from_events(events, "director"),
        )

    def test_all_roles_must_resolve_to_one_model(self):
        self.assertEqual(
            "gpt-5.3-codex",
            self.module.validate_resolved_models(
                {
                    "director": "gpt-5.3-codex",
                    "builder": "gpt-5.3-codex",
                    "evaluator": "gpt-5.3-codex",
                }
            ),
        )

        with self.assertRaisesRegex(self.module.core.ContractError, "different models"):
            self.module.validate_resolved_models(
                {
                    "director": "gpt-5.3-codex",
                    "builder": "claude-haiku-4.5",
                    "evaluator": "gpt-5.3-codex",
                }
            )

    def test_missing_model_receipt_fails_closed(self):
        with self.assertRaisesRegex(self.module.core.ContractError, "no resolved model"):
            self.module.resolved_model_from_events(
                [{"type": "session.idle", "data": {}}],
                "evaluator",
            )


if __name__ == "__main__":
    unittest.main()
