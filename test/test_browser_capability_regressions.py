from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BROWSER_PATH = ROOT / "scripts" / "run_browser_capability.mjs"


VALID_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Capability check</title>
<style>:root{--accent:#176b5b}*{box-sizing:border-box}body{margin:0;padding:2rem;font-family:system-ui;max-width:42rem}input,button{font:inherit;padding:.75rem}button{transition:transform .2s}button:focus-visible,input:focus-visible{outline:3px solid var(--accent)}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}</style></head>
<body><main><h1>Capability check</h1><form id="capability-form"><label for="capability-name">Name</label><input id="capability-name" name="name"><button type="submit">Complete</button></form><p id="capability-success" hidden>Capability complete</p></main>
<script>document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();document.querySelector('#capability-success').hidden=false;});</script></body></html>"""

EMPTY_SUCCESS_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Capability check</title>
<style>*{box-sizing:border-box}body{margin:0;padding:2rem;font-family:system-ui;max-width:42rem}input,button{font:inherit;padding:.75rem}button{transition:transform .2s}#capability-success{min-height:1.5em;display:flex;align-items:center}@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}</style></head>
<body><main><h1>Capability check</h1><form id="capability-form"><label for="capability-name">Name</label><input id="capability-name" name="name"><button type="submit">Complete</button></form><p id="capability-success" aria-live="polite"></p></main>
<script>const success=document.querySelector('#capability-success');document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();success.textContent='Capability complete';});</script></body></html>"""

OPACITY_SUCCESS_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Capability check</title>
<style>:root{--accent:#176b5b}*{box-sizing:border-box}body{margin:0;padding:2rem;font-family:system-ui;max-width:42rem}input,button{font:inherit;padding:.75rem}button{transition:transform .2s}button:focus-visible,input:focus-visible{outline:3px solid var(--accent)}#capability-success{opacity:0;transition:opacity .2s}#capability-success.visible{opacity:1}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}</style></head>
<body><main><h1>Capability check</h1><form id="capability-form"><label for="capability-name">Name</label><input id="capability-name" name="name"><button type="submit">Complete</button></form><p id="capability-success"></p></main>
<script>document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();const success=document.querySelector('#capability-success');success.textContent='Capability complete';success.classList.add('visible');});</script></body></html>"""


class BrowserCapabilityRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
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

    def run_browser(self, html: str):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        site = root / "site"
        evidence = root / "evidence"
        site.mkdir()
        (site / "index.html").write_text(html, encoding="utf-8")
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
        report = json.loads(
            (evidence / "browser-report.json").read_text(encoding="utf-8")
        )
        return temporary, completed, report

    def test_dynamic_external_request_fails(self):
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

    def test_missing_reduced_motion_behavior_fails(self):
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
        self.assertGreater(report["interaction"]["motion"]["normalMaxMs"], 50)
        self.assertGreater(report["interaction"]["motion"]["reducedMaxMs"], 50)

    def test_submission_url_change_fails(self):
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

    def test_previsible_success_state_fails(self):
        html = VALID_HTML.replace(
            '<p id="capability-success" hidden>',
            '<p id="capability-success">',
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "success state was visible before submission",
            report["failures"],
        )
        self.assertTrue(report["interaction"]["successVisibleBefore"])

    def test_empty_live_region_is_hidden_until_content_appears(self):
        temporary, completed, report = self.run_browser(EMPTY_SUCCESS_HTML)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        self.assertFalse(report["interaction"]["successVisibleBefore"])
        self.assertTrue(report["interaction"]["successVisible"])

    def test_opacity_zero_is_hidden_until_local_success_transition(self):
        temporary, completed, report = self.run_browser(OPACITY_SUCCESS_HTML)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        self.assertFalse(report["interaction"]["successVisibleBefore"])
        self.assertTrue(report["interaction"]["successVisible"])


if __name__ == "__main__":
    unittest.main()
