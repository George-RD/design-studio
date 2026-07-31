from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BROWSER_PATH = ROOT / "scripts" / "run_browser_capability.mjs"


BASE_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Capability check</title>
<style>*{box-sizing:border-box}body{margin:0;padding:2rem;font-family:system-ui;max-width:42rem}input,button{font:inherit;padding:.75rem}button{transition:transform .2s}button:focus-visible,input:focus-visible{outline:3px solid #176b5b}@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}</style></head>
<body><main><h1>Capability check</h1><form id="capability-form"><label for="capability-name">Name</label><input id="capability-name" name="name"><button type="submit">Complete</button></form><p id="capability-success" hidden></p></main>
<script>const form=document.querySelector('#capability-form');const success=document.querySelector('#capability-success');form.addEventListener('submit',event=>{event.preventDefault();success.textContent='Capability complete';success.hidden=false;});</script></body></html>"""

PREPOPULATED_SUCCESS_HTML = BASE_HTML.replace(
    '<p id="capability-success" hidden></p>',
    '<p id="capability-success" hidden>Capability complete</p>',
).replace(
    "success.textContent='Capability complete';",
    "",
)

FORM_HIDDEN_HTML = BASE_HTML.replace(
    "success.hidden=false;",
    "success.hidden=false;form.hidden=true;",
)


class BrowserCompletionContractTests(unittest.TestCase):
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
            timeout=35,
        )
        self.assertTrue(
            (evidence / "browser-report.json").is_file(),
            completed.stderr + completed.stdout,
        )
        report = json.loads(
            (evidence / "browser-report.json").read_text(encoding="utf-8")
        )
        return temporary, completed, report

    def test_hidden_success_region_must_start_empty(self):
        temporary, completed, report = self.run_browser(PREPOPULATED_SUCCESS_HTML)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "success state contained content before submission",
            report["failures"],
        )
        self.assertEqual(
            "Capability complete",
            report["interaction"]["successTextBefore"],
        )

    def test_form_must_remain_visible_after_submission(self):
        temporary, completed, report = self.run_browser(FORM_HIDDEN_HTML)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "form controls did not remain visible after submission",
            report["failures"],
        )
        self.assertFalse(report["interaction"]["formVisibleAfter"])


if __name__ == "__main__":
    unittest.main()
