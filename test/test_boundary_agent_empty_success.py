from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BROWSER_PATH = ROOT / "scripts" / "run_browser_capability.mjs"


EMPTY_SUCCESS_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Capability check</title>
<style>*{box-sizing:border-box}body{margin:0;padding:2rem;font-family:system-ui;max-width:42rem}input,button{font:inherit;padding:.75rem}button{transition:transform .2s}#capability-success{min-height:1.5em;display:flex;align-items:center}@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}</style></head>
<body><main><h1>Capability check</h1><form id="capability-form"><label for="capability-name">Name</label><input id="capability-name" name="name"><button type="submit">Complete</button></form><p id="capability-success" aria-live="polite"></p></main>
<script>const success=document.querySelector('#capability-success');document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();success.textContent='Capability complete';});</script></body></html>"""


class EmptySuccessStateRegressionTests(unittest.TestCase):
    def test_empty_live_region_is_not_a_visible_success_state(self):
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
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site = root / "site"
            evidence = root / "evidence"
            site.mkdir()
            (site / "index.html").write_text(EMPTY_SUCCESS_HTML)
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
                (evidence / "browser-report.json").read_text()
            )
            self.assertEqual(
                0, completed.returncode, completed.stderr + completed.stdout
            )
            self.assertFalse(
                report["interaction"]["successVisibleBefore"]
            )
            self.assertTrue(report["interaction"]["successVisible"])


if __name__ == "__main__":
    unittest.main()
