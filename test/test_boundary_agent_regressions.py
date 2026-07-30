from __future__ import annotations

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
    spec = importlib.util.spec_from_file_location(
        "run_boundary_agent_capability_regressions", MODULE_PATH
    )
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
        "supportedInputModalities": ["text", "image"],
        "supportedOutputModalities": ["text"],
        "limits": {"max_input_tokens": 1000, "max_output_tokens": 500},
    }


def write_model_receipt(path: Path, *, model_value=None, status="passed") -> Path:
    value = {
        "schemaVersion": 1,
        "status": status,
        "verifiedAt": "2026-07-30T00:00:00Z",
        "workflow": {
            "runId": 123,
            "headSha": "a" * 40,
            "artifactId": 456,
            "artifactName": "github-models-capability-123",
            "artifactDigest": "sha256:" + "b" * 64,
        },
        "probe": {
            "apiVersion": "2026-03-10",
            "model": model_value or model(),
            "checks": {
                "structuredText": {"status": "passed"},
                "vision": {"status": "passed"},
            },
        },
    }
    path.write_text(json.dumps(value))
    return path


def completion(content, *, usage=None):
    value = {
        "choices": [
            {"message": {"role": "assistant", "content": json.dumps(content)}}
        ]
    }
    if usage is not None:
        value["usage"] = usage
    return value


def tool_completion(*calls):
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": f"call-{index}",
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": json.dumps(arguments),
                            },
                        }
                        for index, (name, arguments) in enumerate(calls, start=1)
                    ],
                }
            }
        ]
    }


VALID_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Capability check</title>
<style>:root{--accent:#176b5b}*{box-sizing:border-box}body{margin:0;padding:2rem;font-family:system-ui;max-width:42rem}input,button{font:inherit;padding:.75rem}button{transition:transform .2s}button:focus-visible,input:focus-visible{outline:3px solid var(--accent)}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}</style></head>
<body><main><h1>Capability check</h1><form id="capability-form"><label for="capability-name">Name</label><input id="capability-name" name="name"><button type="submit">Complete</button></form><p id="capability-success" hidden>Capability complete</p></main>
<script>document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();document.querySelector('#capability-success').hidden=false;});</script></body></html>"""


class FakeRequester:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, *, method, url, token, api_version, payload=None):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "token": token,
                "api_version": api_version,
                "payload": payload,
            }
        )
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class BoundaryAgentRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capability = load_module()

    def run_browser(self, html: str):
        if shutil.which("node") is None:
            self.skipTest("node unavailable")
        if not any(
            shutil.which(name)
            for name in (
                "google-chrome-stable",
                "google-chrome",
                "chromium",
                "chromium-browser",
            )
        ):
            self.skipTest("Chrome unavailable")
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        site = root / "site"
        evidence = root / "evidence"
        site.mkdir()
        (site / "index.html").write_text(html)
        completed = subprocess.run(
            [
                "node",
                str(BROWSER_PATH),
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
            timeout=30,
        )
        report = json.loads((evidence / "browser-report.json").read_text())
        return temporary, completed, report

    def test_verified_model_receipt_replaces_duplicate_live_catalog_request(self):
        direction = {
            "concept": "calm utility",
            "palette": "warm neutral and green",
            "layout": "single column",
            "interaction": "quiet reveal",
        }
        evaluation = {
            "titleVisible": True,
            "formVisible": True,
            "successVisible": True,
            "layoutUsable": True,
            "sourceCanaryVisible": False,
            "summary": "The compact form and success state are visible.",
        }
        requester = FakeRequester(
            [
                completion(direction),
                tool_completion(
                    ("read_work_file", {"path": "baseline.css"}),
                    (
                        "write_output_file",
                        {"path": "index.html", "content": VALID_HTML},
                    ),
                ),
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "Implemented.",
                            }
                        }
                    ]
                },
                completion(evaluation),
            ]
        )

        def browser_runner(site_dir, evidence_dir):
            browser_dir = evidence_dir / "browser"
            browser_dir.mkdir(parents=True)
            (browser_dir / "browser-after-submit.png").write_bytes(
                b"\x89PNG\r\n\x1a\n" + b"body"
            )
            return {
                "status": "passed",
                "viewport": {"width": 390, "height": 844},
                "interaction": {
                    "successVisible": True,
                    "successText": "Capability complete",
                    "submittedValue": "Ada",
                    "innerWidth": 390,
                    "scrollWidth": 390,
                    "clientWidth": 390,
                    "reducedMotion": {"supported": True},
                },
            }

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            receipt = write_model_receipt(output / "model-receipt.json")
            selected = self.capability.load_verified_model_receipt(receipt)
            self.assertEqual("openai/gpt-4.1", selected["model"]["id"])
            self.assertEqual(64, len(selected["sha256"]))

            report = self.capability.run_capability(
                token="secret",
                output_root=output / "run",
                requester=requester,
                browser_runner=browser_runner,
                model_receipt_path=receipt,
                now=lambda: "2026-07-30T00:00:00Z",
            )

        self.assertEqual("passed", report["status"])
        self.assertEqual("passed", report["checks"]["modelReceipt"]["status"])
        self.assertEqual(
            ["POST", "POST", "POST", "POST"],
            [call["method"] for call in requester.calls],
        )

    def test_verified_model_receipt_rejects_unproven_tool_capability(self):
        with tempfile.TemporaryDirectory() as temporary:
            receipt = Path(temporary) / "receipt.json"
            write_model_receipt(
                receipt,
                model_value={**model(), "capabilities": []},
            )
            with self.assertRaisesRegex(
                self.capability.AgentContractError, "tool-calling"
            ):
                self.capability.load_verified_model_receipt(receipt)

    def test_turn_limit_preserves_executed_tool_results(self):
        requester = FakeRequester(
            [
                tool_completion(("list_work_files", {})),
                tool_completion(("list_work_files", {})),
            ]
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            work.mkdir()
            (work / "baseline.css").write_text("body{}")
            evidence = root / "evidence"
            with self.assertRaisesRegex(
                self.capability.AgentContractError, "exceeded 2 turns"
            ):
                self.capability.run_builder(
                    requester=requester,
                    token="secret",
                    model_id="openai/gpt-4.1",
                    brief="Build.",
                    direction={
                        "concept": "a",
                        "palette": "b",
                        "layout": "c",
                        "interaction": "d",
                    },
                    workspace=self.capability.WorkspaceTools(
                        work, root / "output"
                    ),
                    evidence_dir=evidence,
                    api_version="2026-03-10",
                    inference_url="https://example.test/inference",
                    max_turns=2,
                )
            events = json.loads(
                (evidence / "builder-tool-events.json").read_text()
            )
            self.assertEqual(2, len(events["events"]))
            self.assertTrue(
                all(event["status"] == "passed" for event in events["events"])
            )

    def test_browser_fails_on_dynamically_constructed_external_request(self):
        html = VALID_HTML.replace(
            "</script>",
            "new Image().src='https:'+'//example.invalid/pixel.png';</script>",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)
        self.assertEqual(1, completed.returncode)
        self.assertIn("external network request observed", report["failures"])
        self.assertIn(
            "https://example.invalid/pixel.png",
            report["network"]["externalRequests"],
        )

    def test_browser_fails_when_reduced_motion_does_not_change_behavior(self):
        html = VALID_HTML.replace(
            "@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}",
            "",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)
        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "reduced-motion path did not suppress active motion",
            report["failures"],
        )
        self.assertGreater(
            report["interaction"]["motion"]["normalMaxMs"], 50
        )
        self.assertGreater(
            report["interaction"]["motion"]["reducedMaxMs"], 50
        )

    def test_browser_fails_when_submission_changes_document_url(self):
        html = VALID_HTML.replace(
            "document.querySelector('#capability-success').hidden=false;",
            "location.hash='changed';document.querySelector('#capability-success').hidden=false;",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)
        self.assertEqual(1, completed.returncode)
        self.assertIn("submission changed the document URL", report["failures"])
        self.assertNotEqual(
            report["interaction"]["urlBefore"],
            report["interaction"]["urlAfter"],
        )

    def test_browser_fails_when_success_is_visible_before_submission(self):
        html = VALID_HTML.replace(
            '<p id="capability-success" hidden>',
            '<p id="capability-success">',
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)
        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "success state was visible before submission", report["failures"]
        )
        self.assertTrue(report["interaction"]["successVisibleBefore"])


if __name__ == "__main__":
    unittest.main()
