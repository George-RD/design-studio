from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_copilot_cli_agent_capability_gate.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "run_copilot_cli_output_bounds", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CopilotCliOutputBoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_default_command_runner_bounds_stdout_and_keeps_partial_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(
                self.module.core,
                "MAX_STDOUT_BYTES",
                256,
                create=True,
            ), mock.patch.object(
                self.module.core,
                "MAX_STDERR_BYTES",
                128,
                create=True,
            ):
                outcome = self.module.core.default_command_runner(
                    [sys.executable, "-c", "print('x' * 4096)"],
                    cwd=Path(temporary),
                    env={},
                )

        self.assertNotEqual(0, outcome.exit_code)
        self.assertLessEqual(len(outcome.stdout.encode("utf-8")), 256)
        self.assertIn("output limit", outcome.stderr.lower())

    def test_custom_runner_output_is_bounded_before_persistence_or_parsing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "director"
            evidence = root / "evidence"
            workspace.mkdir()
            evidence.mkdir()

            def oversized_runner(argv, *, cwd, env):
                return self.module.CommandOutcome(
                    exit_code=0,
                    stdout='{"type":"session.idle","data":{"model":"gpt-5.4","padding":"'
                    + ("x" * 4096)
                    + '"}}\n',
                    stderr="",
                )

            with mock.patch.object(
                self.module.core,
                "MAX_STDOUT_BYTES",
                256,
                create=True,
            ):
                with self.assertRaisesRegex(
                    self.module.core.ContractError,
                    "stdout exceeds",
                ):
                    self.module.invoke_role(
                        role="director",
                        workspace=workspace,
                        evidence_dir=evidence,
                        token="secret-token",
                        copilot_bin="copilot",
                        model="gpt-5.4",
                        prompt="create direction.json",
                        available_tools="create",
                        allow_tools="write",
                        deny_tools="read,shell,url,memory",
                        command_runner=oversized_runner,
                    )

            persisted = evidence / "director.stdout.jsonl"
            if persisted.exists():
                self.assertLessEqual(persisted.stat().st_size, 256)


if __name__ == "__main__":
    unittest.main()
