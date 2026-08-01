from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_copilot_cli_agent_capability_gate.py"
CSP_META = """<meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; connect-src 'none'; form-action 'none'; frame-src 'none'; img-src data:; media-src data:; object-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'">"""


def load_module():
    spec = importlib.util.spec_from_file_location(
        "run_copilot_cli_agent_capability_gate_test", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeCopilotRunner:
    def __init__(
        self,
        *,
        failure_role: str | None = None,
        leak_canary: bool = False,
        skip_baseline_tool_event: bool = False,
        site_symlink_target: Path | None = None,
        mutate_builder_input: str | None = None,
        omit_output_tool_event_role: str | None = None,
    ):
        self.failure_role = failure_role
        self.leak_canary = leak_canary
        self.skip_baseline_tool_event = skip_baseline_tool_event
        self.site_symlink_target = site_symlink_target
        self.mutate_builder_input = mutate_builder_input
        self.omit_output_tool_event_role = omit_output_tool_event_role
        self.calls: list[dict[str, object]] = []

    @staticmethod
    def tool_events(
        tool_name: str,
        path: Path,
        call_id: str,
        *,
        turn_id: str = "0",
    ) -> list[dict[str, object]]:
        return [
            {
                "type": "tool.execution_start",
                "data": {
                    "toolCallId": call_id,
                    "toolName": tool_name,
                    "arguments": {"path": str(path)},
                    "turnId": turn_id,
                },
            },
            {
                "type": "tool.execution_complete",
                "data": {
                    "toolCallId": call_id,
                    "toolName": tool_name,
                    "success": True,
                    "turnId": turn_id,
                },
            },
        ]

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

        events: list[dict[str, object]] = []
        if role == "director":
            direction_path = Path(cwd) / "direction.json"
            direction_path.write_text(
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
            if self.omit_output_tool_event_role != role:
                events.extend(
                    self.tool_events(
                        "create",
                        direction_path,
                        "call-director-create",
                    )
                )
        elif role == "builder":
            baseline = (Path(cwd) / "baseline.css").read_text()
            self.assert_canary(baseline)
            for name in ("brief.md", "direction.json"):
                events.extend(
                    self.tool_events(
                        "view",
                        Path(cwd) / name,
                        f"call-{name}-view",
                    )
                )
            if not self.skip_baseline_tool_event:
                events.extend(
                    self.tool_events(
                        "view",
                        Path(cwd) / "baseline.css",
                        "call-baseline-view",
                    )
                )
            if self.mutate_builder_input:
                seed = Path(cwd) / self.mutate_builder_input
                seed.write_text(seed.read_text() + "mutated\n")
            leaked = self.module.SOURCE_CANARY if self.leak_canary else ""
            (Path(cwd) / "index.html").write_text(
                "<!doctype html><meta name='viewport' content='width=device-width'>"
                + CSP_META
                + "<style>@media (prefers-reduced-motion: reduce){*{transition-duration:0s!important}}"
                "input,button{transition:transform .18s}"
                "input:focus-visible,button:focus-visible{outline:3px solid #176b5b}</style>"
                "<h1>Check Capability</h1><form id='capability-form'>"
                "<label for='capability-name'>Capability Name</label>"
                "<input id='capability-name' required><button type='submit'>Check</button>"
                "</form><p id='capability-success' hidden></p>"
                "<script>document.querySelector('form').addEventListener('submit',e=>{"
                "e.preventDefault();const p=document.querySelector('#capability-success');"
                "p.hidden=false;p.textContent='Capability complete';});</script>"
                + leaked
            )
            if self.omit_output_tool_event_role != role:
                events.extend(
                    self.tool_events(
                        "create",
                        Path(cwd) / "index.html",
                        "call-builder-create",
                        turn_id="1",
                    )
                )
            if self.site_symlink_target is not None:
                site_target = Path(cwd).parents[1] / "site" / "index.html"
                site_target.symlink_to(self.site_symlink_target)
        elif role == "evaluator":
            evaluation_path = Path(cwd) / "evaluation.json"
            evaluation_path.write_text(
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
            if self.omit_output_tool_event_role != role:
                events.extend(
                    self.tool_events(
                        "create",
                        evaluation_path,
                        "call-evaluator-create",
                    )
                )
        events.append(
            {"type": "session.idle", "data": {"model": "gpt-5.4"}}
        )
        return self.module.CommandOutcome(
            exit_code=0,
            stdout="".join(json.dumps(event) + "\n" for event in events),
            stderr="",
        )

    def assert_canary(self, text: str) -> None:
        if self.module.SOURCE_CANARY not in text:
            raise AssertionError("builder did not receive the source canary")


class FakeBrowserRunner:
    def __init__(
        self,
        screenshot_bytes: bytes = b"png-evidence",
        *,
        forbidden_text_visible: bool = False,
    ) -> None:
        self.screenshot_bytes = screenshot_bytes
        self.forbidden_text_visible = forbidden_text_visible

    def __call__(self, site_dir: Path, evidence_dir: Path):
        if not (site_dir / "index.html").is_file():
            raise AssertionError("browser did not receive the built page")
        browser_dir = evidence_dir / "browser"
        browser_dir.mkdir(parents=True, exist_ok=True)
        (browser_dir / "browser-after-submit.png").write_bytes(
            self.screenshot_bytes
        )
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
                "submission": {
                    "trustedSubmit": True,
                    "causedSuccess": True,
                },
                "forbiddenTextVisible": self.forbidden_text_visible,
                "motion": {"normalMaxMs": 180, "reducedMaxMs": 0},
            },
            "network": {
                "externalRequests": [],
                "blockedRequests": [],
            },
        }


class CopilotCliAgentCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        FakeCopilotRunner.module = cls.module

    def run_gate(
        self,
        runner,
        temporary: str,
        *,
        browser_runner: FakeBrowserRunner | None = None,
    ):
        return self.module.run_capability(
            token="secret-token",
            output_root=Path(temporary),
            copilot_version="1.0.74",
            model="gpt-5.4",
            command_runner=runner,
            browser_runner=browser_runner or FakeBrowserRunner(),
            now=lambda: "2026-07-31T00:00:00Z",
        )

    def test_three_roles_are_isolated_and_use_minimum_tools(self):
        runner = FakeCopilotRunner()
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.dict(
                os.environ,
                {"UNRELATED_SECRET": "must-not-reach-copilot"},
                clear=False,
            ):
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
                self.assertNotIn("UNRELATED_SECRET", call["env"])
                role = call["role"]
                command_record = json.loads(
                    (root / "evidence" / f"{role}.command.json").read_text()
                )
                self.assertEqual(
                    set(command_record["environmentContract"]),
                    set(call["env"]),
                )

            persisted = "\n".join(
                path.read_text(errors="ignore")
                for path in root.rglob("*")
                if path.is_file()
                and path.suffix not in {".png", ".db", ".db-shm", ".db-wal"}
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

    def test_builder_read_requires_observed_successful_view_event(self):
        runner = FakeCopilotRunner(skip_baseline_tool_event=True)
        with tempfile.TemporaryDirectory() as temporary:
            report = self.run_gate(runner, temporary)

        self.assertEqual("failed", report["status"])
        self.assertEqual("builder", report["error"]["step"])
        self.assertIn("tool receipt", report["error"]["message"])

    def test_publishing_rejects_existing_site_symlink_before_mutation(self):
        runner: FakeCopilotRunner
        with tempfile.TemporaryDirectory() as temporary:
            outside = Path(temporary) / "outside.html"
            outside.write_text("sentinel", encoding="utf-8")
            runner = FakeCopilotRunner(site_symlink_target=outside)
            report = self.run_gate(runner, temporary)

            self.assertEqual("failed", report["status"])
            self.assertEqual("builder", report["error"]["step"])
            self.assertIn("symlink", report["error"]["message"].lower())
            self.assertEqual("sentinel", outside.read_text(encoding="utf-8"))


    def test_builder_prompt_fails_closed_when_base_contract_marker_changes(self):
        with mock.patch.object(
            self.module,
            "_BASE_BUILDER_PROMPT",
            return_value="base prompt contract changed",
        ):
            with self.assertRaisesRegex(
                self.module.core.ContractError,
                "builder prompt contract marker",
            ):
                self.module.builder_prompt()

    def test_malformed_srcset_empty_candidates_are_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "index.html"
            path.write_text(
                "<!doctype html><meta name='viewport' content='width=device-width'>"
                + CSP_META
                + "<form id='capability-form'><label for='capability-name'>Name</label>"
                "<input id='capability-name'><button type='submit'>Go</button></form>"
                "<p id='capability-success'></p><img srcset=', , #local'>",
                encoding="utf-8",
            )

            result = self.module.core.validate_site(path)

        self.assertTrue(result["resourceReferencesAbsent"])

    def test_site_size_is_rejected_before_reading_content(self):
        path = mock.Mock()
        path.lstat.return_value.st_mode = 0o100644
        path.lstat.return_value.st_size = 200_001

        with self.assertRaisesRegex(
            self.module.core.ContractError,
            "exceeds the 200 KB capability limit",
        ):
            self.module.core.validate_site(path)

        path.read_text.assert_not_called()

    def test_site_requires_durable_no_network_csp(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "index.html"
            path.write_text(
                "<!doctype html><meta name='viewport' content='width=device-width'>"
                "<form id='capability-form'><label for='capability-name'>Name</label>"
                "<input id='capability-name'><button type='submit'>Go</button></form>"
                "<p id='capability-success'></p>",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                self.module.core.ContractError,
                "content security policy|no-network",
            ):
                self.module.core.validate_site(path)

    def test_site_rejects_network_api_even_with_durable_csp(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "index.html"
            path.write_text(
                "<!doctype html><meta name='viewport' content='width=device-width'>"
                + CSP_META
                + "<form id='capability-form'><label for='capability-name'>Name</label>"
                "<input id='capability-name'><button type='submit'>Go</button></form>"
                "<p id='capability-success'></p><script>setTimeout(()=>fetch('/later'),5000)</script>",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                self.module.core.ContractError,
                "network API",
            ):
                self.module.core.validate_site(path)

    def test_relative_resource_reference_is_not_self_contained(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "index.html"
            path.write_text(
                "<!doctype html><meta name='viewport' content='width=device-width'>"
                + CSP_META
                + "<form id='capability-form'><label for='capability-name'>Name</label>"
                "<input id='capability-name'><button type='submit'>Go</button></form>"
                "<p id='capability-success'></p><audio src='missing.mp3'></audio>",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                self.module.core.ContractError,
                "self-contained|resource",
            ):
                self.module.core.validate_site(path)

    def test_evaluator_attachment_canary_is_detected_from_actual_bytes(self):
        runner = FakeCopilotRunner()
        browser = FakeBrowserRunner(
            b"png-prefix" + self.module.SOURCE_CANARY.encode("utf-8")
        )
        with tempfile.TemporaryDirectory() as temporary:
            report = self.run_gate(
                runner,
                temporary,
                browser_runner=browser,
            )

        self.assertEqual("failed", report["status"])
        self.assertEqual("evaluator", report["error"]["step"])
        isolation = report["checks"]["sourceIsolation"]
        self.assertFalse(isolation["evaluatorRequestCanaryAbsent"])

    def test_same_output_root_can_be_rerun_without_stale_role_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = self.run_gate(FakeCopilotRunner(), temporary)
            second_runner = FakeCopilotRunner()
            second = self.run_gate(second_runner, temporary)

        self.assertEqual("passed", first["status"])
        self.assertEqual("passed", second["status"])
        self.assertEqual(
            ["director", "builder", "evaluator"],
            [call["role"] for call in second_runner.calls],
        )

    def test_command_timeout_is_classified_blocked_with_partial_output(self):
        command = [
            sys.executable,
            "-S",
            "-c",
            (
                "import sys,time; "
                "print('{\"type\":\"partial\"}', flush=True); "
                "print('partial stderr', file=sys.stderr, flush=True); "
                "time.sleep(5)"
            ),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(
                self.module.core,
                "COMMAND_TIMEOUT_SECONDS",
                0.1,
            ):
                outcome = self.module.core.default_command_runner(
                    command,
                    cwd=Path(temporary),
                    env={},
                )

        self.assertEqual(124, outcome.exit_code)
        self.assertIn('{"type":"partial"}', outcome.stdout)
        self.assertIn("partial stderr", outcome.stderr)
        self.assertIn("timed out", outcome.stderr.lower())
        self.assertEqual("blocked", self.module.classify_cli_failure(outcome))

    def test_browser_timeout_is_blocked_and_writes_partial_logs(self):
        timeout = subprocess.TimeoutExpired(
            cmd=["node"],
            timeout=90,
            output=b"partial browser stdout",
            stderr=b"partial browser stderr",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site = root / "site"
            site.mkdir()
            (site / "index.html").write_text("<!doctype html>", encoding="utf-8")
            evidence = root / "evidence"
            with mock.patch.object(
                self.module.core.subprocess,
                "run",
                side_effect=timeout,
            ):
                with self.assertRaisesRegex(
                    self.module.core.CapabilityBlocked,
                    "timed out",
                ):
                    self.module.core.default_browser_runner(site, evidence)

            browser = evidence / "browser"
            self.assertEqual(
                "partial browser stdout",
                (browser / "stdout.log").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "partial browser stderr",
                (browser / "stderr.log").read_text(encoding="utf-8"),
            )

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

    def test_builder_seed_inputs_must_remain_unchanged(self):
        runner = FakeCopilotRunner(mutate_builder_input="baseline.css")
        with tempfile.TemporaryDirectory() as temporary:
            report = self.run_gate(runner, temporary)

        self.assertEqual("failed", report["status"])
        self.assertEqual("builder", report["error"]["step"])
        self.assertIn("builder source inputs changed", report["error"]["message"])
        self.assertEqual(2, len(runner.calls))

    def test_each_role_output_requires_a_successful_tool_receipt(self):
        for role in ("director", "builder", "evaluator"):
            with self.subTest(role=role), tempfile.TemporaryDirectory() as temporary:
                runner = FakeCopilotRunner(omit_output_tool_event_role=role)
                report = self.run_gate(runner, temporary)

            self.assertEqual("failed", report["status"])
            self.assertEqual(role, report["error"]["step"])
            self.assertIn("tool receipt", report["error"]["message"])

    def test_browser_must_prove_rendered_canary_absence(self):
        runner = FakeCopilotRunner()
        with tempfile.TemporaryDirectory() as temporary:
            report = self.run_gate(
                runner,
                temporary,
                browser_runner=FakeBrowserRunner(forbidden_text_visible=True),
            )

        self.assertEqual("failed", report["status"])
        self.assertEqual("sourceIsolation", report["error"]["step"])
        self.assertIn("rendered", report["error"]["message"])
        self.assertEqual(2, len(runner.calls))

    def test_site_rejects_network_capable_csp_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "index.html"
            path.write_text(
                "<!doctype html><meta name='viewport' content='width=device-width'>"
                + CSP_META.replace("img-src data:;", "img-src data: https:;")
                + "<form id='capability-form'><label for='capability-name'>Name</label>"
                "<input id='capability-name'><button type='submit'>Go</button></form>"
                "<p id='capability-success' hidden></p>",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                self.module.core.ContractError,
                "durable no-network",
            ):
                self.module.core.validate_site(path)


if __name__ == "__main__":
    unittest.main()
