from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "scripts" / "run_copilot_cli_agent_capability_gate.py"
BROWSER_PATH = ROOT / "scripts" / "run_browser_capability.mjs"
STRESS_PATH = ROOT / "scripts" / "run_browser_capability_stress.py"


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def assistant_turn_start(turn_id: str) -> dict[str, object]:
    return {"type": "assistant.turn_start", "data": {"turnId": turn_id}}


def assistant_turn_end(turn_id: str) -> dict[str, object]:
    return {"type": "assistant.turn_end", "data": {"turnId": turn_id}}


def tool_events(
    tool_name: str,
    path: Path,
    call_id: str,
    *,
    turn_id: str,
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


def valid_builder_seed_events(workspace: Path) -> list[dict[str, object]]:
    events: list[dict[str, object]] = [assistant_turn_start("seed")]
    for filename, call_id in (
        ("brief.md", "read-brief"),
        ("direction.json", "read-direction"),
        ("baseline.css", "read-baseline"),
    ):
        events.extend(
            tool_events(
                "view",
                workspace / filename,
                call_id,
                turn_id="seed",
            )
        )
    events.append(assistant_turn_end("seed"))
    return events


class BuilderSelfInspectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = load_module(GATE_PATH, "capability_gate_hardening_test")

    def test_builder_allows_only_root_and_own_output_self_inspection(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            events = valid_builder_seed_events(workspace)
            events.extend(
                [
                    assistant_turn_start("write"),
                    *tool_events(
                        "create",
                        workspace / "index.html",
                        "write-index",
                        turn_id="write",
                    ),
                    assistant_turn_end("write"),
                    assistant_turn_start("inspect"),
                    *tool_events(
                        "view",
                        workspace,
                        "inspect-root",
                        turn_id="inspect",
                    ),
                    *tool_events(
                        "view",
                        workspace / "index.html",
                        "inspect-output",
                        turn_id="inspect",
                    ),
                    assistant_turn_end("inspect"),
                ]
            )

            receipt = self.gate.validate_role_tool_receipt(
                "builder",
                events,
                workspace,
            )

        self.assertEqual(
            ["baseline.css", "brief.md", "direction.json"],
            receipt["seedRead"],
        )
        self.assertEqual([".", "index.html"], receipt["selfInspectionRead"])
        self.assertEqual(["index.html"], receipt["written"])

    def test_self_inspection_does_not_replace_a_required_seed_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            events: list[dict[str, object]] = [
                assistant_turn_start("seed"),
                *tool_events(
                    "view",
                    workspace / "brief.md",
                    "read-brief",
                    turn_id="seed",
                ),
                *tool_events(
                    "view",
                    workspace / "direction.json",
                    "read-direction",
                    turn_id="seed",
                ),
                *tool_events(
                    "view",
                    workspace / "index.html",
                    "inspect-output",
                    turn_id="seed",
                ),
                assistant_turn_end("seed"),
                assistant_turn_start("write"),
                *tool_events(
                    "create",
                    workspace / "index.html",
                    "write-index",
                    turn_id="write",
                ),
                assistant_turn_end("write"),
            ]

            with self.assertRaisesRegex(
                self.gate.core.ContractError,
                "does not match the role contract",
            ):
                self.gate.validate_role_tool_receipt(
                    "builder",
                    events,
                    workspace,
                )

    def test_first_turn_self_inspection_does_not_satisfy_seed_read_requirement(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            events: list[dict[str, object]] = [
                assistant_turn_start("inspect-first"),
                *tool_events(
                    "view",
                    workspace,
                    "inspect-root",
                    turn_id="inspect-first",
                ),
                assistant_turn_end("inspect-first"),
                *valid_builder_seed_events(workspace),
                assistant_turn_start("write"),
                *tool_events(
                    "create",
                    workspace / "index.html",
                    "write-index",
                    turn_id="write",
                ),
                assistant_turn_end("write"),
            ]

            with self.assertRaisesRegex(
                self.gate.core.ContractError,
                "required first-turn tool use",
            ):
                self.gate.validate_role_tool_receipt(
                    "builder",
                    events,
                    workspace,
                )

    def test_undeclared_and_parent_reads_remain_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            workspace.mkdir()
            cases = (
                (workspace / "secret.md", "unauthorized read"),
                (workspace / ".." / "source.py", "escaped"),
            )
            for index, (path, message) in enumerate(cases):
                with self.subTest(path=path):
                    events = [
                        assistant_turn_start(f"turn-{index}"),
                        *tool_events(
                            "view",
                            path,
                            f"read-{index}",
                            turn_id=f"turn-{index}",
                        ),
                        assistant_turn_end(f"turn-{index}"),
                    ]
                    with self.assertRaisesRegex(
                        self.gate.core.ContractError,
                        message,
                    ):
                        self.gate.validate_role_tool_receipt(
                            "builder",
                            events,
                            workspace,
                        )

    def test_symlink_read_outside_workspace_remains_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            source = root / "source.txt"
            source.write_text("source", encoding="utf-8")
            link = workspace / "index.html"
            try:
                link.symlink_to(source)
            except OSError as error:
                self.skipTest(f"symlink unavailable: {error}")
            events = [
                assistant_turn_start("inspect"),
                *tool_events(
                    "view",
                    link,
                    "inspect-link",
                    turn_id="inspect",
                ),
                assistant_turn_end("inspect"),
            ]

            with self.assertRaisesRegex(
                self.gate.core.ContractError,
                "escaped",
            ):
                self.gate.validate_role_tool_receipt(
                    "builder",
                    events,
                    workspace,
                )


class BrowserStartupClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node unavailable")

    def run_stubbed_wrapper(self, stub_source: str):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name) / "browser wrapper path"
        root.mkdir()
        wrapper = root / BROWSER_PATH.name
        shutil.copy2(BROWSER_PATH, wrapper)
        (root / "run_browser_capability_base.mjs").write_text(
            stub_source,
            encoding="utf-8",
        )
        site = root / "site"
        site.mkdir()
        (site / "index.html").write_text("<!doctype html>", encoding="utf-8")
        evidence = root / "evidence"
        completed = subprocess.run(
            [
                "node",
                str(wrapper),
                "--root",
                str(site),
                "--output-dir",
                str(evidence),
                "--entrypoint",
                "index.html",
                "--width",
                "390",
                "--height",
                "844",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            env=os.environ.copy(),
        )
        report = json.loads(
            (evidence / "browser-report.json").read_text(encoding="utf-8")
        )
        return temporary, completed, evidence, report

    def test_startup_block_is_retried_then_security_failure_wins(self):
        stub = r"""import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
const args=process.argv.slice(2);const output=args[args.indexOf('--output-dir')+1];
await mkdir(output,{recursive:true});const countPath=join(output,'attempt-count');
let count=0;try{count=Number(await readFile(countPath,'utf8'))||0;}catch{}
count+=1;await writeFile(countPath,String(count));
const blocked={schemaVersion:1,status:'blocked',error:'BrowserBlockedError: Chrome DevTools did not become ready',failures:[]};
const failed={schemaVersion:1,status:'failed',network:{observationMs:1300,externalRequests:['https://example.invalid/delayed.png'],blockedRequests:['https://example.invalid/delayed.png']},failures:['external network request attempted']};
await writeFile(join(output,'browser-report.json'),JSON.stringify(count===1?blocked:failed));
process.exitCode=count===1?2:1;
"""
        temporary, completed, evidence, report = self.run_stubbed_wrapper(stub)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode, completed.stderr + completed.stdout)
        self.assertEqual("failed", report["status"])
        self.assertEqual("contract", report["phase"])
        self.assertTrue(report["startupRetry"]["attempted"])
        self.assertEqual(2, report["startupRetry"]["attempts"])
        self.assertEqual(
            "startup",
            report["startupRetry"]["firstAttempt"]["phase"],
        )
        self.assertEqual("2", (evidence / "attempt-count").read_text())
        self.assertIn(
            "https://example.invalid/delayed.png",
            report["network"]["externalRequests"],
        )

    def test_security_failure_is_not_retried(self):
        stub = r"""import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
const args=process.argv.slice(2);const output=args[args.indexOf('--output-dir')+1];
await mkdir(output,{recursive:true});const countPath=join(output,'attempt-count');
let count=0;try{count=Number(await readFile(countPath,'utf8'))||0;}catch{}
count+=1;await writeFile(countPath,String(count));
await writeFile(join(output,'browser-report.json'),JSON.stringify({schemaVersion:1,status:'failed',network:{observationMs:1300,externalRequests:['https://example.invalid/delayed.png'],blockedRequests:['https://example.invalid/delayed.png']},failures:['external network request attempted']}));
process.exitCode=1;
"""
        temporary, completed, evidence, report = self.run_stubbed_wrapper(stub)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertFalse(report["startupRetry"]["attempted"])
        self.assertEqual("1", (evidence / "attempt-count").read_text())


class BrowserStressEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stress = load_module(STRESS_PATH, "browser_stress_hardening_test")

    def test_repeated_security_failures_pass_the_stress_contract(self):
        attempts = [
            {
                "exitCode": 1,
                "status": "failed",
                "phase": "contract",
                "contractPassed": True,
            }
            for _ in range(3)
        ]
        evidence = self.stress.build_evidence(
            attempts=attempts,
            root=Path("fixture"),
            expected_url=self.stress.DEFAULT_EXPECTED_URL,
        )

        self.assertIsInstance(evidence["schemaVersion"], int)
        self.assertEqual("passed", evidence["status"])
        self.assertEqual(3, evidence["checks"]["runCount"])
        self.assertEqual({"failed": 3}, evidence["checks"]["runStatuses"])
        self.assertIn("proves", evidence["scope"])
        self.assertIn("doesNotProve", evidence["scope"])

    def test_any_persisting_startup_block_fails_the_stress_contract(self):
        attempts = [
            {
                "exitCode": 1,
                "status": "failed",
                "phase": "contract",
                "contractPassed": True,
            },
            {
                "exitCode": 2,
                "status": "blocked",
                "phase": "startup",
                "contractPassed": False,
            },
        ]

        self.assertEqual("failed", self.stress.evaluate_attempts(attempts))


if __name__ == "__main__":
    unittest.main()
