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
        "run_copilot_cli_director_retry_test",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class StructuredRunner:
    def __init__(self, module, *, always_invalid: bool = False):
        self.module = module
        self.always_invalid = always_invalid
        self.director_attempts = 0
        self.roles: list[str] = []
        self.prompts: list[str] = []

    def __call__(self, argv, *, cwd, env):
        role = Path(cwd).name
        self.roles.append(role)
        prompt = argv[argv.index("--prompt") + 1]
        self.prompts.append(prompt)
        events: list[dict[str, object]] = []

        if role == "director":
            self.director_attempts += 1
            invalid = self.always_invalid or self.director_attempts == 1
            if invalid:
                (Path(cwd) / "direction.json").write_text(
                    '{"concept":"calm","palette":"warm","layout":"compact",'
                    '"interaction":"local">}\n',
                    encoding="utf-8",
                )
            else:
                (Path(cwd) / "direction.json").write_text(
                    json.dumps(
                        {
                            "concept": "Calm capability card",
                            "palette": "Warm neutral with green accent",
                            "layout": "Single compact column",
                            "interaction": "Keep the form visible and reveal local success",
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
        elif role == "builder":
            call_id = "call-baseline-view"
            events.extend(
                [
                    {
                        "type": "tool.execution_start",
                        "data": {
                            "toolCallId": call_id,
                            "toolName": "view",
                            "arguments": {
                                "path": str(Path(cwd) / "baseline.css")
                            },
                        },
                    },
                    {
                        "type": "tool.execution_complete",
                        "data": {
                            "toolCallId": call_id,
                            "toolName": "view",
                            "success": True,
                        },
                    },
                ]
            )
            (Path(cwd) / "index.html").write_text(
                "<!doctype html><meta name='viewport' content='width=device-width'>"
                "<style>@media (prefers-reduced-motion: reduce){*{transition-duration:0s!important}}"
                "input,button{transition:transform .18s}"
                "input:focus-visible,button:focus-visible{outline:3px solid #176b5b}</style>"
                "<h1>Check Capability</h1><form id='capability-form'>"
                "<label for='capability-name'>Capability Name</label>"
                "<input id='capability-name' required><button type='submit'>Check</button>"
                "</form><p id='capability-success' hidden></p>"
                "<script>document.querySelector('form').addEventListener('submit',e=>{"
                "e.preventDefault();const p=document.querySelector('#capability-success');"
                "p.hidden=false;p.textContent='Capability complete';});</script>",
                encoding="utf-8",
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
                        "summary": "The form and local success state are visible.",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
        else:
            raise AssertionError(f"unexpected role workspace: {role}")

        events.append(
            {"type": "session.idle", "data": {"model": "gpt-5-mini"}}
        )
        return self.module.CommandOutcome(
            exit_code=0,
            stdout="".join(json.dumps(event) + "\n" for event in events),
            stderr="",
        )


class BrowserRunner:
    def __call__(self, site_dir: Path, evidence_dir: Path):
        browser_dir = evidence_dir / "browser"
        browser_dir.mkdir(parents=True, exist_ok=True)
        (browser_dir / "browser-after-submit.png").write_bytes(b"png-evidence")
        return {
            "viewport": {"width": 390, "height": 844},
            "interaction": {
                "successVisible": True,
                "successText": "Capability complete",
                "submittedValue": "Ada",
                "urlBefore": "about:blank",
                "urlAfter": "about:blank",
                "beforeSubmission": {"scrollWidth": 390, "clientWidth": 390},
                "afterSubmission": {"scrollWidth": 390, "clientWidth": 390},
                "focus": {"visible": True},
                "motion": {"normalMaxMs": 180, "reducedMaxMs": 0},
            },
            "network": {"externalRequests": [], "blockedRequests": []},
        }


class CopilotCliDirectorRetryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def run_gate(self, runner, output_root: Path):
        return self.module.run_capability(
            token="secret-token",
            output_root=output_root,
            copilot_version="1.0.74",
            model="auto",
            command_runner=runner,
            browser_runner=BrowserRunner(),
            now=lambda: "2026-07-31T00:00:00Z",
        )

    def test_invalid_director_json_is_retried_once_with_preserved_evidence(self):
        runner = StructuredRunner(self.module)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = self.run_gate(runner, root)

            self.assertEqual("passed", report["status"])
            self.assertEqual(
                ["director", "director", "builder", "evaluator"],
                runner.roles,
            )
            self.assertEqual(2, report["checks"]["director"]["attemptCount"])
            self.assertIn("strict JSON", runner.prompts[1])
            for name in (
                "director.attempt-1.command.json",
                "director.attempt-1.stdout.jsonl",
                "director.attempt-1.stderr.log",
                "director.attempt-1.direction.json",
            ):
                self.assertTrue((root / "evidence" / name).is_file(), name)

    def test_second_invalid_director_json_fails_without_starting_builder(self):
        runner = StructuredRunner(self.module, always_invalid=True)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = self.run_gate(runner, root)

            self.assertEqual("failed", report["status"])
            self.assertEqual("director", report["error"]["step"])
            self.assertEqual(["director", "director"], runner.roles)
            self.assertTrue(
                (root / "evidence" / "director.attempt-1.direction.json").is_file()
            )


if __name__ == "__main__":
    unittest.main()
