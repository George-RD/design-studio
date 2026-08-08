from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BROWSER_PATH = ROOT / "scripts" / "run_browser_capability.mjs"

DELAYED_SUCCESS_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; connect-src 'none'; form-action 'none'; frame-src 'none'; img-src data:; media-src data:; object-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'"><title>Capability check</title>
<style>*{box-sizing:border-box}body{margin:0;padding:2rem;font-family:system-ui;max-width:42rem}input,button{font:inherit;padding:.75rem}button{transition:transform .2s}button:focus-visible,input:focus-visible{outline:3px solid #176b5b}#capability-success{min-height:1.5em;display:flex;align-items:center}@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}</style></head>
<body><main><h1>Capability check</h1><form id="capability-form"><label for="capability-name">Name</label><input id="capability-name" name="name"><button type="submit">Complete</button></form><p id="capability-success" aria-live="polite"></p></main>
<script>const success=document.querySelector('#capability-success');document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();setTimeout(()=>{success.textContent='Capability complete';},900);});</script></body></html>"""

NESTED_DELAYED_SUCCESS_HTML = DELAYED_SUCCESS_HTML.replace(
    "setTimeout(()=>{success.textContent='Capability complete';},900);",
    "setTimeout(()=>{setTimeout(()=>{success.textContent='Capability complete';},100);},100);",
)


class BrowserSubmissionAttributionTests(unittest.TestCase):
    def setUp(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node unavailable")
        configured = os.environ.get("CHROME_PATH")
        if configured:
            if not Path(configured).is_file():
                self.skipTest("configured Chrome unavailable")
            return
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

    def test_delayed_success_is_attributed_to_the_trusted_submission(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site = root / "site"
            evidence = root / "evidence"
            site.mkdir()
            (site / "index.html").write_text(
                DELAYED_SUCCESS_HTML,
                encoding="utf-8",
            )
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
                timeout=35,
            )
            self.assertTrue(
                (evidence / "browser-report.json").is_file(),
                completed.stderr + completed.stdout,
            )
            report = json.loads(
                (evidence / "browser-report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        self.assertTrue(report["interaction"]["submission"]["trustedSubmit"])
        self.assertTrue(report["interaction"]["submission"]["causedSuccess"])
        self.assertTrue(report["interaction"]["successVisible"])

    def test_nested_delayed_success_is_attributed_to_the_trusted_submission(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site = root / "site"
            evidence = root / "evidence"
            site.mkdir()
            (site / "index.html").write_text(
                NESTED_DELAYED_SUCCESS_HTML,
                encoding="utf-8",
            )
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
                timeout=35,
            )
            self.assertTrue(
                (evidence / "browser-report.json").is_file(),
                completed.stderr + completed.stdout,
            )
            report = json.loads(
                (evidence / "browser-report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        self.assertTrue(report["interaction"]["submission"]["trustedSubmit"])
        self.assertTrue(report["interaction"]["submission"]["causedSuccess"])
        self.assertTrue(report["interaction"]["successVisible"])


if __name__ == "__main__":
    unittest.main()
