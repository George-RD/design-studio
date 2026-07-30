from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_boundary_agent_capability.py"
BROWSER_PATH = ROOT / "scripts" / "run_browser_capability.mjs"


def load_module():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("run_boundary_agent_capability", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def model():
    return {
        "id": "openai/gpt-4.1",
        "name": "OpenAI GPT-4.1",
        "version": "2025-04-14",
        "registry": "azure-openai",
        "capabilities": ["tool-calling"],
        "supported_input_modalities": ["text", "image"],
        "supported_output_modalities": ["text"],
        "limits": {"max_input_tokens": 1000, "max_output_tokens": 500},
    }


def completion(content, *, usage=None):
    value = {"choices": [{"message": {"role": "assistant", "content": json.dumps(content)}}]}
    if usage is not None:
        value["usage"] = usage
    return value


def tool_completion(*calls, usage=None):
    value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": f"call-{index}",
                            "type": "function",
                            "function": {"name": name, "arguments": json.dumps(arguments)},
                        }
                        for index, (name, arguments) in enumerate(calls, start=1)
                    ],
                }
            }
        ]
    }
    if usage is not None:
        value["usage"] = usage
    return value


VALID_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Capability check</title>
<style>:root{--accent:#176b5b}*{box-sizing:border-box}body{margin:0;padding:2rem;font-family:system-ui;max-width:42rem}input,button{font:inherit;padding:.75rem}button:focus-visible,input:focus-visible{outline:3px solid var(--accent)}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}</style></head>
<body><main><h1>Capability check</h1><form id="capability-form"><label for="capability-name">Name</label><input id="capability-name" name="name"><button type="submit">Complete</button></form><p id="capability-success" hidden>Capability complete</p></main>
<script>document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();document.querySelector('#capability-success').hidden=false;});</script></body></html>"""


class FakeRequester:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, *, method, url, token, api_version, payload=None):
        self.calls.append({"method": method, "url": url, "token": token, "api_version": api_version, "payload": json.loads(json.dumps(payload)) if payload is not None else None})
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class BoundaryAgentCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capability = load_module()

    def test_agent_model_selection_requires_tool_calling_and_modalities(self):
        selected = self.capability.choose_agent_model(
            [
                {**model(), "id": "vendor/no-tools", "capabilities": []},
                model(),
            ],
            ("openai/gpt-4.1",),
        )
        self.assertEqual("openai/gpt-4.1", selected["id"])
        with self.assertRaisesRegex(self.capability.AgentContractError, "tool-calling"):
            self.capability.choose_agent_model(
                [{**model(), "capabilities": []}],
                ("openai/gpt-4.1",),
            )

    def test_workspace_tools_enforce_read_and_write_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            output = root / "output"
            work.mkdir()
            (work / "baseline.css").write_text(":root{}")
            tools = self.capability.WorkspaceTools(work, output)

            self.assertEqual({"files": ["baseline.css"]}, tools.list_work_files())
            self.assertEqual(":root{}", tools.read_work_file("baseline.css")["content"])
            tools.write_output_file("index.html", "<h1>ok</h1>")
            self.assertEqual("<h1>ok</h1>", (output / "index.html").read_text())
            self.assertFalse((work / "index.html").exists())

    def test_workspace_tools_reject_escape_symlink_and_binary_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            output = root / "output"
            work.mkdir()
            outside = root / "outside.css"
            outside.write_text("secret")
            tools = self.capability.WorkspaceTools(work, output)

            for path in ("../outside.css", "/tmp/outside.css", "folder\\file.css", "image.png"):
                with self.subTest(path=path):
                    with self.assertRaises(self.capability.AgentContractError):
                        tools.read_work_file(path)

            link = work / "linked.css"
            try:
                link.symlink_to(outside)
            except OSError:
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(self.capability.AgentContractError, "symlink"):
                tools.read_work_file("linked.css")

    def test_builder_uses_required_first_turn_tools_and_records_usage(self):
        requester = FakeRequester(
            [
                tool_completion(
                    ("read_work_file", {"path": "baseline.css"}),
                    ("write_output_file", {"path": "index.html", "content": VALID_HTML}),
                    usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                ),
                {"choices": [{"message": {"role": "assistant", "content": "Built and verified."}}], "usage": {"prompt_tokens": 80, "completion_tokens": 10, "total_tokens": 90}},
            ]
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            output = root / "output"
            evidence = root / "evidence"
            work.mkdir()
            (work / "baseline.css").write_text(f":root{{--accent:#176b5b}}/* {self.capability.SOURCE_CANARY} */")
            workspace = self.capability.WorkspaceTools(work, output)

            result = self.capability.run_builder(
                requester=requester,
                token="secret",
                model_id="openai/gpt-4.1",
                brief="Build the capability page.",
                direction={"concept": "calm", "palette": "green", "layout": "single", "interaction": "local"},
                workspace=workspace,
                evidence_dir=evidence,
                api_version="2026-03-10",
                inference_url="https://example.test/inference",
            )

            self.assertEqual("required", requester.calls[0]["payload"]["tool_choice"])
            self.assertEqual("auto", requester.calls[1]["payload"]["tool_choice"])
            continuation = requester.calls[1]["payload"]["messages"]
            self.assertEqual("assistant", continuation[-3]["role"])
            self.assertIsInstance(continuation[-3]["content"], str)
            self.assertEqual("tool", continuation[-2]["role"])
            self.assertNotIn("name", continuation[-2])
            self.assertEqual("tool", continuation[-1]["role"])
            self.assertEqual(["baseline.css"], result["readPaths"])
            self.assertEqual(["index.html"], result["writePaths"])
            self.assertEqual({"promptTokens": 180, "completionTokens": 60, "totalTokens": 240}, result["usage"])
            self.assertTrue((evidence / "builder-tool-events.json").is_file())

    def test_builder_fails_when_it_does_not_write_the_required_output(self):
        requester = FakeRequester(
            [
                tool_completion(("read_work_file", {"path": "baseline.css"})),
                {"choices": [{"message": {"role": "assistant", "content": "Done."}}]},
            ]
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            work.mkdir()
            (work / "baseline.css").write_text("body{}")
            workspace = self.capability.WorkspaceTools(work, root / "output")
            with self.assertRaisesRegex(self.capability.AgentContractError, "did not write"):
                self.capability.run_builder(
                    requester=requester,
                    token="secret",
                    model_id="openai/gpt-4.1",
                    brief="Build.",
                    direction={"concept": "a", "palette": "b", "layout": "c", "interaction": "d"},
                    workspace=workspace,
                    evidence_dir=root / "evidence",
                    api_version="2026-03-10",
                    inference_url="https://example.test/inference",
                )

    def test_output_contract_accepts_valid_html_with_single_quoted_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            html = VALID_HTML
            for element_id in ("capability-form", "capability-name", "capability-success"):
                html = html.replace(f'id="{element_id}"', f"id='{element_id}'")
            (output / "index.html").write_text(html)
            result = self.capability.validate_output(output)
            self.assertTrue(result["selfContained"])

    def test_output_contract_rejects_external_requests_and_source_canary(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "index.html").write_text(VALID_HTML.replace("</head>", '<link href="https://example.test/a.css"></head>'))
            with self.assertRaisesRegex(self.capability.AgentContractError, "external dependency"):
                self.capability.validate_output(output)
            (output / "index.html").write_text(VALID_HTML + self.capability.SOURCE_CANARY)
            with self.assertRaisesRegex(self.capability.AgentContractError, "canary"):
                self.capability.validate_output(output)

    def test_director_and_evaluator_payloads_are_source_blind(self):
        director = self.capability.director_payload("openai/gpt-4.1", "A public brief")
        evaluator = self.capability.evaluator_payload("openai/gpt-4.1", "A public brief", b"\x89PNG\r\n\x1a\n")
        self.assertNotIn(self.capability.SOURCE_CANARY, json.dumps(director))
        self.assertNotIn(self.capability.SOURCE_CANARY, json.dumps(evaluator))
        image = evaluator["messages"][1]["content"][1]["image_url"]["url"]
        self.assertTrue(image.startswith("data:image/png;base64,"))

    def test_complete_capability_preserves_evidence_and_token_redaction(self):
        direction = {"concept": "calm utility", "palette": "warm neutral and green", "layout": "single column", "interaction": "quiet reveal"}
        evaluation = {"titleVisible": True, "formVisible": True, "successVisible": True, "layoutUsable": True, "sourceCanaryVisible": False, "summary": "The compact form and success state are visible."}
        requester = FakeRequester(
            [
                [model()],
                completion(direction, usage={"prompt_tokens": 20, "completion_tokens": 20, "total_tokens": 40}),
                tool_completion(("read_work_file", {"path": "baseline.css"}), ("write_output_file", {"path": "index.html", "content": VALID_HTML}), usage={"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}),
                {"choices": [{"message": {"role": "assistant", "content": "Implemented."}}], "usage": {"prompt_tokens": 20, "completion_tokens": 5, "total_tokens": 25}},
                completion(evaluation, usage={"prompt_tokens": 80, "completion_tokens": 20, "total_tokens": 100}),
            ]
        )

        def browser_runner(site_dir, evidence_dir):
            browser_dir = evidence_dir / "browser"
            browser_dir.mkdir(parents=True)
            (browser_dir / "browser-after-submit.png").write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2Q1sAAAAASUVORK5CYII="))
            report = {"status": "passed", "viewport": {"width": 390, "height": 844}, "interaction": {"successVisible": True, "successText": "Capability complete", "submittedValue": "Ada", "innerWidth": 390, "scrollWidth": 390, "clientWidth": 390, "reducedMotion": True}}
            self.capability.write_json(browser_dir / "browser-report.json", report)
            return report

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            report = self.capability.run_capability(
                token="secret-token",
                output_root=output,
                requester=requester,
                browser_runner=browser_runner,
                preferred_models=("openai/gpt-4.1",),
                now=lambda: "2026-07-30T00:00:00Z",
            )

            self.assertEqual("passed", report["status"])
            self.assertEqual("passed", report["checks"]["sourceIsolation"]["status"])
            self.assertEqual({"promptTokens": 220, "completionTokens": 245, "totalTokens": 465}, report["usage"])
            self.assertTrue((output / "site" / "index.html").is_file())
            self.assertTrue((output / "capability-report.json").is_file())
            all_text = "\n".join(path.read_text(errors="ignore") for path in output.rglob("*") if path.is_file() and path.suffix != ".png")
            self.assertNotIn("secret-token", all_text)
            self.assertNotIn(self.capability.SOURCE_CANARY, (output / "evidence" / "director-request.json").read_text())
            self.assertNotIn(self.capability.SOURCE_CANARY, (output / "evidence" / "evaluator-request.json").read_text())

    def test_api_blocker_is_classified_and_reported(self):
        requester = FakeRequester(
            [
                self.capability.models.ApiRequestError(status=403, method="GET", url="catalog", body={"message": "disabled"})
            ]
        )
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            report = self.capability.run_capability(
                token="secret",
                output_root=output,
                requester=requester,
                browser_runner=lambda *_: {},
                now=lambda: "2026-07-30T00:00:00Z",
            )
            self.assertEqual("blocked", report["status"])
            self.assertEqual(403, report["error"]["httpStatus"])
            self.assertEqual(report, json.loads((output / "capability-report.json").read_text()))

    def test_browser_probe_submits_form_checks_mobile_and_captures_screenshot(self):
        if shutil.which("node") is None:
            self.skipTest("node unavailable")
        if not any(shutil.which(name) for name in ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser")):
            self.skipTest("Chrome unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site = root / "site"
            output = root / "evidence"
            site.mkdir()
            (site / "index.html").write_text(VALID_HTML)
            completed = subprocess.run(
                ["node", str(BROWSER_PATH), "--root", str(site), "--output-dir", str(output), "--entrypoint", "index.html", "--width", "390", "--height", "844"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
            report = json.loads((output / "browser-report.json").read_text())
            self.assertEqual("passed", report["status"])
            self.assertTrue(report["interaction"]["successVisible"])
            self.assertEqual(390, report["interaction"]["innerWidth"])
            self.assertLessEqual(report["interaction"]["scrollWidth"], report["interaction"]["clientWidth"])
            self.assertTrue(report["interaction"]["reducedMotion"])
            self.assertGreater((output / "browser-after-submit.png").stat().st_size, 100)

    def test_browser_probe_fails_closed_on_wrong_success_copy(self):
        if shutil.which("node") is None:
            self.skipTest("node unavailable")
        if not any(shutil.which(name) for name in ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser")):
            self.skipTest("Chrome unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site = root / "site"
            output = root / "evidence"
            site.mkdir()
            (site / "index.html").write_text(VALID_HTML.replace("Capability complete", "Finished"))
            completed = subprocess.run(
                ["node", str(BROWSER_PATH), "--root", str(site), "--output-dir", str(output)],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            self.assertEqual(1, completed.returncode)
            report = json.loads((output / "browser-report.json").read_text())
            self.assertEqual("failed", report["status"])
            self.assertIn("success state text is not exact", report["failures"])


if __name__ == "__main__":
    unittest.main()
