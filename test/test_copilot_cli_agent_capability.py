from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_copilot_cli_agent_capability.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "run_copilot_cli_agent_capability", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeCopilotRunner:
    def __init__(self, *, failure_role: str | None = None, leak_canary: bool = False):
        self.failure_role = failure_role
        self.leak_canary = leak_canary
        self.calls: list[dict[str, object]] = []

    def __call__(self, argv, *, cwd, env):
        role = Path(cwd).name
        self.calls.append(
            {
                "role": role,
                "argv": list(argv),
                "cwd": Path(cwd),
                "env": dict(env),
            }
        )
        if role == self.failure_role:
            return self.module.CommandOutcome(
                exit_code=1,
                stdout="",
                stderr="Copilot Requests permission is unavailable for this token",
            )

        if role == "director":
            (Path(cwd) / "direction.json").write_text(
                json.dumps(
                    {
                        "concept": "Calm capability card",
                        "palette": "Warm neutral with green accent",
                        "layout": "Single compact column",
                        "interaction": "Submit reveals local success",
                    }
                )
                + "\n"
            )
        elif role == "builder":
            baseline = (Path(cwd) / "baseline.css").read_text()
            self.assert_canary(baseline)
            leaked = self.module.SOURCE_CANARY if self.leak_canary else ""
            (Path(cwd) / "index.html").write_text(
                "<!doctype html><meta name='viewport' content='width=device-width'>"
                "<style>@media (prefers-reduced-motion: reduce){*{transition-duration:0s!important}}"
                "input,button{transition:transform .18s}</style>"
                "<h1>Check Capability</h1><form id='capability-form'>"
                "<label for='capability-name'>Capability Name</label>"
                "<input id='capability-name' required><button>Check</button>"
                "</form><p id='capability-success' hidden></p>"
                "<script>document.querySelector('form').addEventListener('submit',e=>{"
                "e.preventDefault();const p=document.querySelector('#capability-success');"
                "p.hidden=false;p.textContent='Capability complete';});</script>"
                + leaked
            )
        elif role == "evaluator":
            (Path(cwd) / "evaluation.json").write_text(
                json.dumps(
                    {
                        "titleVisible": True,
                        "formVisible": True,
                        "successVisible": True,
                        "layoutUsable": True,
                        "sourceCanaryVisible": False,
                        "summary": "The compact form and local success state are visible.",
                    }
                )
                + "\n"
            )
        return self.module.CommandOutcome(
            exit_code=0,
            stdout='{"type":"session.idle","data":{"model":"gpt-5.4"}}\n',
            stderr="",
        )

    def assert_canary(self, text: str) -> None:
        if self.module.SOURCE_CANARY not in text:
            raise AssertionError("builder did not receive the source canary")


class FakeBrowserRunner:
    def __call__(self, site_dir: Path, evidence_dir: Path):
        if not (site_dir / "index.html").is_file():
            raise AssertionError("browser did not receive the built page")
        browser_dir = evidence_dir / "browser"
        browser_dir.mkdir(parents=True, exist_ok=True)
        (browser_dir / "browser-after-submit.png").write_bytes(b"png-evidence")
        return {
            "viewport": {"width": 390, "height": 844},
            "interaction": {
                "successVisible": True,
                "successText": "Capability complete",
                "urlUnchanged": True,
                "horizontalOverflow": False,
                "reducedMotionDurationMs": 0,
            },
            "network": {"externalRequests": []},
        }


class CopilotCliAgentCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        FakeCopilotRunner.module = cls.module

    def run_gate(self, runner, temporary: str):
        return self.module.run_capability(
            token="secret-token",
            output_root=Path(temporary),
            copilot_version="1.0.74",
            model="gpt-5.4",
            command_runner=runner,
            browser_runner=FakeBrowserRunner(),
            now=lambda: "2026-07-31T00:00:00Z",
        )

    def test_three_roles_are_isolated_and_use_minimum_tools(self):
        runner = FakeCopilotRunner()
        with tempfile.TemporaryDirectory() as temporary:
            report = self.run_gate(runner, temporary)
            root = Path(temporary)

            self.assertEqual("passed", report["status"])
            self.assertEqual(["director", "builder", "evaluator"], [
                call["role"] for call in runner.calls
            ])
            self.assertFalse((root / "workspaces" / "director" / "baseline.css").exists())
            self.assertFalse((root / "workspaces" / "evaluator" / "baseline.css").exists())
            self.assertTrue((root / "workspaces" / "builder" / "baseline.css").is_file())
            self.assertTrue((root / "evidence" / "director.stdout.jsonl").is_file())
            self.assertTrue((root / "evidence" / "builder.stdout.jsonl").is_file())
            self.assertTrue((root / "evidence" / "evaluator.stdout.jsonl").is_file())

            director = runner.calls[0]
            builder = runner.calls[1]
            evaluator = runner.calls[2]
            self.assertIn("--available-tools=create", director["argv"])
            self.assertIn("--allow-tool=write", director["argv"])
            self.assertIn("--deny-tool=read,shell,url,memory", director["argv"])
            self.assertIn(
                "--available-tools=view,create,edit,apply_patch",
                builder["argv"],
            )
            self.assertIn("--allow-tool=read,write", builder["argv"])
            self.assertIn("--deny-tool=shell,url,memory", builder["argv"])
            self.assertIn("--attachment", evaluator["argv"])
            self.assertIn("--available-tools=create", evaluator["argv"])
            for call in runner.calls:
                argv = call["argv"]
                self.assertIn("--no-custom-instructions", argv)
                self.assertIn("--disable-builtin-mcps", argv)
                self.assertIn("--no-ask-user", argv)
                self.assertIn("--no-remote", argv)
                self.assertIn("--no-remote-export", argv)
                self.assertIn("--max-ai-credits=30", argv)
                self.assertEqual("secret-token", call["env"]["GITHUB_TOKEN"])

            persisted = "\n".join(
                path.read_text(errors="ignore")
                for path in root.rglob("*")
                if path.is_file() and path.suffix != ".png"
            )
            self.assertNotIn("secret-token", persisted)

    def test_missing_copilot_permission_is_blocked(self):
        runner = FakeCopilotRunner(failure_role="director")
        with tempfile.TemporaryDirectory() as temporary:
            report = self.run_gate(runner, temporary)

        self.assertEqual("blocked", report["status"])
        self.assertEqual("director", report["error"]["step"])
        self.assertEqual("copilot-auth", report["error"]["kind"])

    def test_source_canary_leak_fails_before_browser_or_evaluator(self):
        runner = FakeCopilotRunner(leak_canary=True)
        browser = FakeBrowserRunner()
        with tempfile.TemporaryDirectory() as temporary:
            report = self.module.run_capability(
                token="secret-token",
                output_root=Path(temporary),
                copilot_version="1.0.74",
                model="gpt-5.4",
                command_runner=runner,
                browser_runner=browser,
                now=lambda: "2026-07-31T00:00:00Z",
            )

        self.assertEqual("failed", report["status"])
        self.assertEqual("builder", report["error"]["step"])
        self.assertEqual(["director", "builder"], [call["role"] for call in runner.calls])

    def test_no_token_blocks_without_starting_a_role(self):
        runner = FakeCopilotRunner()
        with tempfile.TemporaryDirectory() as temporary:
            report = self.module.run_capability(
                token="",
                output_root=Path(temporary),
                command_runner=runner,
                browser_runner=FakeBrowserRunner(),
            )

        self.assertEqual("blocked", report["status"])
        self.assertEqual([], runner.calls)


if __name__ == "__main__":
    unittest.main()
