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
        "run_boundary_agent_generated_output", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


DYNAMIC_SUCCESS_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Capability check</title>
<style>:root{--accent:#176b5b}*{box-sizing:border-box}body{margin:0;padding:2rem;font-family:system-ui;max-width:42rem}input,button{font:inherit;padding:.75rem}button{transition:transform .2s}button:focus-visible,input:focus-visible{outline:3px solid var(--accent)}#capability-success{opacity:0;transition:opacity .2s}#capability-success.visible{opacity:1}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}</style></head>
<body><main><h1>Capability check</h1><form id="capability-form"><label for="capability-name">Name</label><input id="capability-name" name="name"><button type="submit">Complete</button></form><p id="capability-success"></p></main>
<script>document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();const success=document.querySelector('#capability-success');success.textContent='Capability complete';success.classList.add('visible');});</script></body></html>"""


class GeneratedOutputRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capability = load_module()

    def test_output_contract_accepts_success_copy_assigned_by_local_script(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "index.html").write_text(DYNAMIC_SUCCESS_HTML)
            contract = self.capability.validate_output(output)
            self.assertTrue(contract["selfContained"])

    def test_opacity_zero_counts_as_hidden_before_submission(self):
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
            (site / "index.html").write_text(DYNAMIC_SUCCESS_HTML)
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
