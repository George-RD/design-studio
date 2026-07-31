from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_copilot_cli_agent_capability_gate.py"


def load_module(name: str = "run_copilot_cli_auto_model"):
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
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

    def test_repeated_module_loads_reuse_original_unwrapped_functions(self):
        first = load_module("run_copilot_cli_auto_model_repeat_one")
        second = load_module("run_copilot_cli_auto_model_repeat_two")

        self.assertIs(first._BASE_CLASSIFIER, second._BASE_CLASSIFIER)
        self.assertIs(first._BASE_INVOKE_ROLE, second._BASE_INVOKE_ROLE)
        self.assertIs(first._BASE_RUN_CAPABILITY, second._BASE_RUN_CAPABILITY)
        self.assertIsNot(second._BASE_INVOKE_ROLE, first.invoke_role)
        self.assertIsNot(second._BASE_RUN_CAPABILITY, first.run_capability)

    def test_token_leak_is_scrubbed_before_failed_evidence_returns(self):
        token = "secret-token"
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary)

            def fake_base_run(*args, **kwargs):
                leak = output_root / "workspaces" / "builder" / "leak.bin"
                leak.parent.mkdir(parents=True)
                leak.write_bytes(b"prefix\x00" + token.encode("utf-8") + b"\xffsuffix")
                report = {
                    "schemaVersion": 1,
                    "status": "failed",
                    "executionSurface": {
                        "name": "github-copilot-cli",
                        "version": "1.0.74",
                        "model": "gpt-5-mini",
                    },
                    "checks": {"builder": {"status": "failed"}},
                    "error": {
                        "step": "builder",
                        "kind": "contract",
                        "message": "builder leaked a credential",
                    },
                }
                self.module.core.write_json(
                    output_root / "capability-report.json",
                    report,
                )
                return report

            with mock.patch.object(
                self.module,
                "_BASE_RUN_CAPABILITY",
                fake_base_run,
            ):
                report = self.module.run_capability(
                    token=token,
                    output_root=output_root,
                    model="gpt-5-mini",
                )

            persisted = json.loads(
                (output_root / "capability-report.json").read_text(
                    encoding="utf-8"
                )
            )
            leaked_paths = [
                path.relative_to(output_root).as_posix()
                for path in output_root.rglob("*")
                if path.is_file() and token.encode("utf-8") in path.read_bytes()
            ]

        self.assertEqual([], leaked_paths)
        self.assertEqual("failed", report["status"])
        self.assertEqual("credentialIsolation", report["error"]["step"])
        self.assertEqual("credential-leak", report["error"]["kind"])
        self.assertEqual("failed", persisted["status"])
        self.assertIn(
            "workspaces/builder/leak.bin",
            persisted["checks"]["credentialIsolation"]["scrubbedFiles"],
        )

    def test_pinned_model_mismatch_downgrades_persisted_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary)

            def fake_base_run(*args, **kwargs):
                report = {
                    "schemaVersion": 1,
                    "status": "passed",
                    "executionSurface": {
                        "name": "github-copilot-cli",
                        "version": "1.0.74",
                        "model": "gpt-5-mini",
                    },
                    "checks": {
                        role: {"resolvedModel": "claude-haiku-4.5"}
                        for role in ("director", "builder", "evaluator")
                    },
                    "error": None,
                }
                self.module.core.write_json(
                    output_root / "capability-report.json",
                    report,
                )
                return report

            with mock.patch.object(
                self.module,
                "_BASE_RUN_CAPABILITY",
                fake_base_run,
            ):
                report = self.module.run_capability(
                    output_root=output_root,
                    model="gpt-5-mini",
                )

            persisted = json.loads(
                (output_root / "capability-report.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual("failed", report["status"])
        self.assertIn("requested model", report["error"]["message"])
        self.assertEqual("failed", persisted["status"])

    def test_inconsistent_resolved_models_downgrade_persisted_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary)

            def fake_base_run(*args, **kwargs):
                report = {
                    "schemaVersion": 1,
                    "status": "passed",
                    "executionSurface": {
                        "name": "github-copilot-cli",
                        "version": "1.0.74",
                        "model": "auto",
                    },
                    "checks": {
                        "director": {"resolvedModel": "gpt-5-mini"},
                        "builder": {"resolvedModel": "claude-haiku-4.5"},
                        "evaluator": {"resolvedModel": "gpt-5-mini"},
                    },
                    "error": None,
                }
                self.module.core.write_json(
                    output_root / "capability-report.json",
                    report,
                )
                return report

            with mock.patch.object(
                self.module,
                "_BASE_RUN_CAPABILITY",
                fake_base_run,
            ):
                report = self.module.run_capability(
                    output_root=output_root,
                    model="auto",
                )

            persisted = json.loads(
                (output_root / "capability-report.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual("failed", report["status"])
        self.assertEqual("resolvedModel", report["error"]["step"])
        self.assertEqual("contract", report["error"]["kind"])
        self.assertEqual("failed", persisted["status"])
        self.assertEqual("resolvedModel", persisted["error"]["step"])


if __name__ == "__main__":
    unittest.main()
