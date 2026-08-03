from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
BROWSER_PATH = ROOT / "scripts" / "run_browser_capability_completion.mjs"
CSP_META = '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; base-uri \'none\'; connect-src \'none\'; form-action \'none\'; frame-src \'none\'; img-src data:; media-src data:; object-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'">'


BASE_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; connect-src 'none'; form-action 'none'; frame-src 'none'; img-src data:; media-src data:; object-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'"><title>Capability check</title>
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

PERMANENT_SHADOW_NO_FOCUS_HTML = BASE_HTML.replace(
    "button:focus-visible,input:focus-visible{outline:3px solid #176b5b}",
    "input,button{box-shadow:0 0 0 2px #176b5b}*:focus{outline:none}",
)


class BrowserCompletionContractTests(unittest.TestCase):
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

    def test_permanent_shadow_is_not_a_keyboard_focus_indicator(self):
        temporary, completed, report = self.run_browser(
            PERMANENT_SHADOW_NO_FOCUS_HTML
        )
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "keyboard focus produced no visual style change",
            report["failures"],
        )
        self.assertFalse(report["interaction"]["focusStyleChanged"])


class BrowserCompletionWrapperTests(unittest.TestCase):
    def setUp(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node unavailable")

    def run_stubbed_wrapper(
        self,
        stub_source: str,
        *,
        environment: dict[str, str] | None = None,
        timeout: int = 10,
    ):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name) / "wrapper path ✓ with spaces"
        root.mkdir()
        wrapper = root / BROWSER_PATH.name
        shutil.copy2(BROWSER_PATH, wrapper)
        (root / "run_browser_capability.mjs").write_text(
            stub_source,
            encoding="utf-8",
        )
        evidence = root / "evidence"
        completed = subprocess.run(
            [
                "node",
                str(wrapper),
                "--root",
                str(root),
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
            timeout=timeout,
            env={**os.environ, **(environment or {})},
        )
        return temporary, completed, evidence

    def test_wrapper_decodes_base_script_path_with_spaces_and_unicode(self):
        stub = """import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
const args=process.argv.slice(2);const output=args[args.indexOf('--output-dir')+1];
await mkdir(output,{recursive:true});await writeFile(join(output,'browser-report.json'),JSON.stringify({schemaVersion:1,status:'passed',failures:[]}));
"""
        temporary, completed, evidence = self.run_stubbed_wrapper(stub)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        report = json.loads((evidence / "browser-report.json").read_text())
        self.assertEqual("passed", report["status"])

    def test_wrapper_preserves_base_diagnostics_when_exit_disagrees(self):
        stub = """import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
const args=process.argv.slice(2);const output=args[args.indexOf('--output-dir')+1];
await mkdir(output,{recursive:true});await writeFile(join(output,'browser-report.json'),JSON.stringify({schemaVersion:1,status:'passed',failures:[]}));
process.stdout.write('stub stdout\\n');process.stderr.write('stub stderr\\n');process.exitCode=3;
"""
        temporary, completed, evidence = self.run_stubbed_wrapper(stub)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        report = json.loads((evidence / "browser-report.json").read_text())
        failure = "\n".join(report["failures"])
        self.assertIn("base browser probe exited 3", failure)
        self.assertIn("stub stdout", failure)
        self.assertIn("stub stderr", failure)

    def test_wrapper_timeout_terminates_browser_descendants(self):
        stub = """import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
const args=process.argv.slice(2);const output=args[args.indexOf('--output-dir')+1];
await mkdir(output,{recursive:true});
const marker=join(output,'grandchild-terminated');
const childSource=`const {writeFileSync}=require('node:fs');process.on('SIGTERM',()=>{writeFileSync(${JSON.stringify(marker)},'terminated');process.exit(0)});setInterval(()=>{},1000);`;
const child=spawn(process.execPath,['-e',childSource],{stdio:'ignore'});
await writeFile(join(output,'grandchild.pid'),String(child.pid));
await new Promise(()=>{});
"""
        temporary, completed, evidence = self.run_stubbed_wrapper(
            stub,
            environment={
                "DESIGN_STUDIO_BROWSER_COMPLETION_TIMEOUT_MS": "250",
            },
            timeout=5,
        )
        self.addCleanup(temporary.cleanup)

        self.assertEqual(2, completed.returncode)
        deadline = time.monotonic() + 5
        while (
            not (evidence / "grandchild-terminated").is_file()
            and time.monotonic() < deadline
        ):
            time.sleep(0.05)
        self.assertTrue((evidence / "grandchild-terminated").is_file())
        report = json.loads((evidence / "browser-report.json").read_text())
        self.assertEqual("blocked", report["status"])
        self.assertIn("timed out", report["error"].lower())

    def test_failure_fallback_still_emits_status_when_report_cannot_be_written(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            blocked_parent = root / "not-a-directory"
            blocked_parent.write_text("sentinel", encoding="utf-8")
            output = blocked_parent / "evidence"
            completed = subprocess.run(
                [
                    "node",
                    str(BROWSER_PATH),
                    "--root",
                    str(root),
                    "--output-dir",
                    str(output),
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
            )

        self.assertEqual(1, completed.returncode)
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
        self.assertEqual("failed", payload["status"])
        self.assertIn("failed to persist failure report", completed.stderr)


if __name__ == "__main__":
    unittest.main()
