from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_copilot_cli_agent_capability_gate.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "run_copilot_cli_trusted_workspace", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CopilotCliTrustedWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_config_trusts_only_the_role_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "copilot-home" / "director"
            workspace = root / "workspaces" / "director"
            workspace.mkdir(parents=True)

            config_path = self.module.write_trusted_workspace_config(home, workspace)
            config = json.loads(config_path.read_text())

        self.assertEqual([str(workspace.resolve())], config["trustedFolders"])
        self.assertEqual({"trustedFolders"}, set(config))

    def test_existing_unrelated_config_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "copilot-home" / "builder"
            workspace = root / "workspaces" / "builder"
            home.mkdir(parents=True)
            workspace.mkdir(parents=True)
            (home / "config.json").write_text(
                json.dumps({"trustedFolders": ["/unexpected"]}) + "\n"
            )

            with self.assertRaisesRegex(self.module.core.ContractError, "already exists"):
                self.module.write_trusted_workspace_config(home, workspace)

    def test_successful_file_view_must_remain_inside_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            outside = root / "outside.txt"
            outside.write_text("private\n", encoding="utf-8")
            events = [
                {
                    "type": "tool.execution_start",
                    "data": {
                        "toolCallId": "outside-view",
                        "toolName": "view",
                        "arguments": {"path": str(outside)},
                    },
                },
                {
                    "type": "tool.execution_complete",
                    "data": {
                        "toolCallId": "outside-view",
                        "toolName": "view",
                        "success": True,
                    },
                },
            ]

            with self.assertRaisesRegex(
                self.module.core.ContractError,
                "escaped the trusted role workspace",
            ):
                self.module.successful_file_views(events, workspace)


    def test_successful_file_write_must_remain_inside_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            outside = root / "outside.html"
            events = [
                {
                    "type": "tool.execution_start",
                    "data": {
                        "toolCallId": "outside-create",
                        "toolName": "create",
                        "arguments": {"path": str(outside)},
                    },
                },
                {
                    "type": "tool.execution_complete",
                    "data": {
                        "toolCallId": "outside-create",
                        "toolName": "create",
                        "success": True,
                    },
                },
            ]

            with self.assertRaisesRegex(
                self.module.core.ContractError,
                "write escaped the trusted role workspace",
            ):
                self.module.successful_file_views(events, workspace)

    def test_json_writer_rejects_symlink_destination_without_mutating_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / "outside.json"
            outside.write_text("keep\n", encoding="utf-8")
            destination = root / "capability-report.json"
            destination.symlink_to(outside)

            with self.assertRaisesRegex(
                self.module.core.ContractError,
                "must not be a symlink",
            ):
                self.module.write_json_no_follow(
                    destination,
                    {"status": "failed"},
                )

            self.assertEqual("keep\n", outside.read_text(encoding="utf-8"))

    def test_blocked_receipt_preserves_actual_cause(self):
        cases = {
            ("authentication", "GITHUB_TOKEN is required"): "copilot-auth",
            ("director", "model is not available"): "model-unavailable",
            ("builder", "rate limit exceeded"): "rate-limit",
            ("evaluator", "AI credits exhausted"): "credit-exhausted",
            ("browser", "Chrome is not installed"): "browser-unavailable",
            ("browser", "browser probe timed out"): "browser-timeout",
            ("director", "service unavailable"): "service-unavailable",
        }
        for (step, message), expected in cases.items():
            with self.subTest(step=step, message=message):
                self.assertEqual(
                    expected,
                    self.module.classify_blocker_kind(step, message),
                )


if __name__ == "__main__":
    unittest.main()
