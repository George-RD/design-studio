from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BROWSER_PATH = ROOT / "scripts" / "run_browser_capability.mjs"
CSP_META = '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; base-uri \'none\'; connect-src \'none\'; form-action \'none\'; frame-src \'none\'; img-src data:; media-src data:; object-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'">'


VALID_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; connect-src 'none'; form-action 'none'; frame-src 'none'; img-src data:; media-src data:; object-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'"><title>Capability check</title>
<style>:root{--accent:#176b5b}*{box-sizing:border-box}body{margin:0;padding:2rem;font-family:system-ui;max-width:42rem}input,button{font:inherit;padding:.75rem}button{transition:transform .2s}button:focus-visible,input:focus-visible{outline:3px solid var(--accent)}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}</style></head>
<body><main><h1>Capability check</h1><form id="capability-form"><label for="capability-name">Name</label><input id="capability-name" name="name"><button type="submit">Complete</button></form><p id="capability-success" hidden>Capability complete</p></main>
<script>document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();document.querySelector('#capability-success').hidden=false;});</script></body></html>"""

EMPTY_SUCCESS_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; connect-src 'none'; form-action 'none'; frame-src 'none'; img-src data:; media-src data:; object-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'"><title>Capability check</title>
<style>*{box-sizing:border-box}body{margin:0;padding:2rem;font-family:system-ui;max-width:42rem}input,button{font:inherit;padding:.75rem}button{transition:transform .2s}button:focus-visible,input:focus-visible{outline:3px solid #176b5b}#capability-success{min-height:1.5em;display:flex;align-items:center}@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}</style></head>
<body><main><h1>Capability check</h1><form id="capability-form"><label for="capability-name">Name</label><input id="capability-name" name="name"><button type="submit">Complete</button></form><p id="capability-success" aria-live="polite"></p></main>
<script>const success=document.querySelector('#capability-success');document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();success.textContent='Capability complete';});</script></body></html>"""

OPACITY_SUCCESS_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; connect-src 'none'; form-action 'none'; frame-src 'none'; img-src data:; media-src data:; object-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'"><title>Capability check</title>
<style>:root{--accent:#176b5b}*{box-sizing:border-box}body{margin:0;padding:2rem;font-family:system-ui;max-width:42rem}input,button{font:inherit;padding:.75rem}button{transition:transform .2s}button:focus-visible,input:focus-visible{outline:3px solid var(--accent)}#capability-success{opacity:0;transition:opacity .2s}#capability-success.visible{opacity:1}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}</style></head>
<body><main><h1>Capability check</h1><form id="capability-form"><label for="capability-name">Name</label><input id="capability-name" name="name"><button type="submit">Complete</button></form><p id="capability-success"></p></main>
<script>document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();const success=document.querySelector('#capability-success');success.textContent='Capability complete';success.classList.add('visible');});</script></body></html>"""


class BrowserCapabilityRegressionTests(unittest.TestCase):
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

    def run_browser(
        self,
        html: str,
        *,
        forbidden_text: str | None = None,
        environment: dict[str, str] | None = None,
        timeout: int = 35,
    ):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        site = root / "site"
        evidence = root / "evidence"
        site.mkdir()
        (site / "index.html").write_text(html, encoding="utf-8")
        command = [
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
        ]
        if forbidden_text is not None:
            command.extend(["--forbidden-text", forbidden_text])
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            env={**os.environ, **(environment or {})},
        )
        self.assertTrue(
            (evidence / "browser-report.json").is_file(),
            completed.stderr + completed.stdout,
        )
        report = json.loads(
            (evidence / "browser-report.json").read_text(encoding="utf-8")
        )
        return temporary, completed, report

    def test_dynamic_external_request_is_blocked_and_fails(self):
        html = VALID_HTML.replace(
            "</script>",
            "new Image().src='https:'+'//example.invalid/pixel.png';</script>",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn("external network request attempted", report["failures"])
        self.assertIn(
            "https://example.invalid/pixel.png",
            report["network"]["externalRequests"],
        )
        self.assertIn(
            "https://example.invalid/pixel.png",
            report["network"]["blockedRequests"],
        )

    def test_delayed_external_request_is_observed_and_blocked(self):
        html = VALID_HTML.replace(
            "</script>",
            "setTimeout(()=>{new Image().src='https:'+'//example.invalid/delayed.png';},900);</script>",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "https://example.invalid/delayed.png",
            report["network"]["externalRequests"],
        )
        self.assertIn(
            "https://example.invalid/delayed.png",
            report["network"]["blockedRequests"],
        )

    def test_websocket_attempt_is_observed_and_blocked(self):
        html = VALID_HTML.replace(
            "</script>",
            "try{new WebSocket('wss:'+'//example.invalid/socket');}catch{}</script>",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "wss://example.invalid/socket",
            report["network"]["externalRequests"],
        )
        self.assertIn(
            "wss://example.invalid/socket",
            report["network"]["blockedRequests"],
        )

    def test_normal_media_submission_request_is_observed_and_blocked(self):
        html = VALID_HTML.replace(
            "document.querySelector('#capability-success').hidden=false;",
            "if(matchMedia('(prefers-reduced-motion: no-preference)').matches){new Image().src='https:'+'//example.invalid/normal-submit.png';}document.querySelector('#capability-success').hidden=false;",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "https://example.invalid/normal-submit.png",
            report["network"]["externalRequests"],
        )
        self.assertIn(
            "https://example.invalid/normal-submit.png",
            report["network"]["blockedRequests"],
        )

    def test_window_open_attempt_is_observed_and_blocked(self):
        html = VALID_HTML.replace(
            "document.querySelector('#capability-success').hidden=false;",
            "window.open('https:'+'//example.invalid/popup');document.querySelector('#capability-success').hidden=false;",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "https://example.invalid/popup",
            report["network"]["externalRequests"],
        )
        self.assertIn(
            "https://example.invalid/popup",
            report["network"]["blockedRequests"],
        )

    def test_target_blank_navigation_is_observed_and_blocked(self):
        html = VALID_HTML.replace(
            "document.querySelector('#capability-success').hidden=false;",
            "const link=document.createElement('a');link.href='https:'+'//example.invalid/target-blank';link.target='_blank';document.body.append(link);link.click();document.querySelector('#capability-success').hidden=false;",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "https://example.invalid/target-blank",
            report["network"]["externalRequests"],
        )
        self.assertIn(
            "https://example.invalid/target-blank",
            report["network"]["blockedRequests"],
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

    def test_motion_introduced_only_for_reduced_users_fails(self):
        html = VALID_HTML.replace(
            "button{transition:transform .2s}",
            "button{transition:none}@keyframes reducedOnly{from{opacity:.9}to{opacity:1}}",
        ).replace(
            "@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}",
            "@media(prefers-reduced-motion:reduce){button{animation:reducedOnly 2s infinite}}",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "reduced-motion path did not suppress active motion",
            report["failures"],
        )
        self.assertEqual(0, report["interaction"]["motion"]["normalMaxMs"])
        self.assertGreater(report["interaction"]["motion"]["reducedMaxMs"], 50)

    def test_motion_introduced_after_submit_for_reduced_users_fails(self):
        html = VALID_HTML.replace(
            "button{transition:transform .2s}",
            "button{transition:none}@keyframes postReduced{from{opacity:.9}to{opacity:1}}",
        ).replace(
            "@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}",
            "@media(prefers-reduced-motion:reduce){body.post-motion{animation:postReduced 2s infinite}}",
        ).replace(
            "document.querySelector('#capability-success').hidden=false;",
            "document.body.classList.add('post-motion');document.querySelector('#capability-success').hidden=false;",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "reduced-motion path did not suppress active motion",
            report["failures"],
        )
        self.assertEqual(
            0,
            report["interaction"]["motion"]["normalPostSubmitMaxMs"],
        )
        self.assertGreater(
            report["interaction"]["motion"]["reducedPostSubmitMaxMs"],
            50,
        )

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

    def test_pseudo_element_success_content_is_visible_before_submission(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "#capability-success{min-height:1.5em;display:flex;align-items:center}",
            "#capability-success{min-height:1.5em;display:flex;align-items:center}"
            "#capability-success::before{content:'Capability complete'}",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "success state was visible before submission",
            report["failures"],
        )
        self.assertTrue(report["interaction"]["successVisibleBefore"])
        self.assertEqual(
            "Capability complete",
            report["interaction"]["successPseudoTextBefore"],
        )

    def test_quoted_pseudo_keyword_is_visible_content(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "#capability-success{min-height:1.5em;display:flex;align-items:center}",
            "#capability-success{min-height:1.5em;display:flex;align-items:center}"
            "#capability-success::before{content:'none'}",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "success state was visible before submission",
            report["failures"],
        )
        self.assertEqual("none", report["interaction"]["successPseudoTextBefore"])

    def test_offscreen_success_state_is_not_visible(self):
        html = VALID_HTML.replace(
            '<p id="capability-success" hidden>',
            '<p id="capability-success" hidden style="position:fixed;top:120vh;width:10rem">',
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "success state did not become visible",
            report["failures"],
        )
        self.assertFalse(report["interaction"]["successVisible"])

    def test_readonly_input_cannot_pass_real_keyboard_entry(self):
        html = VALID_HTML.replace(
            '<input id="capability-name" name="name">',
            '<input id="capability-name" name="name" readonly>',
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "text input did not accept real keyboard input",
            report["failures"],
        )
        self.assertNotEqual("Ada", report["interaction"]["submittedValue"])

    def test_missing_visible_focus_indicator_fails(self):
        html = VALID_HTML.replace(
            "button:focus-visible,input:focus-visible{outline:3px solid var(--accent)}",
            "*:focus{outline:none;box-shadow:none}",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "keyboard focus is not visibly indicated",
            report["failures"],
        )
        self.assertFalse(report["interaction"]["focus"]["visible"])

    def test_horizontal_overflow_before_submission_fails_even_if_handler_hides_it(self):
        html = VALID_HTML.replace(
            "<main>",
            '<main><div id="overflow" style="width:800px;height:1px"></div>',
        ).replace(
            "document.querySelector('#capability-success').hidden=false;",
            "document.querySelector('#overflow').hidden=true;document.querySelector('#capability-success').hidden=false;",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "document has horizontal overflow before submission",
            report["failures"],
        )
        self.assertGreater(
            report["interaction"]["beforeSubmission"]["scrollWidth"],
            report["interaction"]["beforeSubmission"]["clientWidth"],
        )
        self.assertLessEqual(
            report["interaction"]["afterSubmission"]["scrollWidth"],
            report["interaction"]["afterSubmission"]["clientWidth"],
        )


    def test_missing_durable_network_policy_fails(self):
        html = EMPTY_SUCCESS_HTML.replace(CSP_META, "")
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "document lacks a durable no-network content security policy",
            report["failures"],
        )
        self.assertFalse(report["network"]["durablePolicy"])

    def test_keydown_prevention_blocks_real_keyboard_entry(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "<script>",
            "<script>document.querySelector('#capability-name').addEventListener('keydown',event=>{if(event.key.length===1)event.preventDefault()});</script><script>",
            1,
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "text input did not accept real keyboard input",
            report["failures"],
        )
        self.assertNotEqual("Ada", report["interaction"]["submittedValue"])

    def test_non_rendering_focus_style_change_does_not_pass(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "button:focus-visible,input:focus-visible{outline:3px solid #176b5b}",
            "*:focus{outline:none;outline-offset:12px;filter:brightness(100%)}",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "keyboard focus produced no rendered visual change",
            report["failures"],
        )
        self.assertFalse(report["interaction"]["focusStyleChanged"])

    def test_rendered_focus_filter_change_is_accepted(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "button:focus-visible,input:focus-visible{outline:3px solid #176b5b}",
            "button:focus-visible,input:focus-visible{outline:none;filter:brightness(70%)}",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        self.assertTrue(report["interaction"]["focusStyleChanged"])

    def test_transparent_ancestor_hides_form_controls(self):
        html = EMPTY_SUCCESS_HTML.replace(
            '<form id="capability-form">',
            '<div style="opacity:0"><form id="capability-form">',
        ).replace(
            '</form><p id="capability-success"',
            '</form></div><p id="capability-success"',
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "form controls were not visible before submission",
            report["failures"],
        )
        self.assertFalse(report["interaction"]["formVisibleBefore"])

    def test_textarea_cannot_impersonate_the_required_text_input(self):
        html = EMPTY_SUCCESS_HTML.replace(
            '<input id="capability-name" name="name">',
            '<textarea id="capability-name" name="name"></textarea>',
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "capability-name is not a text input",
            report["failures"],
        )
        self.assertFalse(report["interaction"]["textInputContract"])

    def test_empty_visual_label_does_not_count_as_an_accessible_name(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "</style>",
            "label{display:block;min-width:2rem;min-height:1rem}</style>",
        ).replace(
            '<label for="capability-name">Name</label>',
            '<label for="capability-name"></label>',
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "capability-name has no accessible label",
            report["failures"],
        )
        self.assertEqual("", report["interaction"]["inputAccessibleName"])

    def test_timer_success_without_a_trusted_submit_fails(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();success.textContent='Capability complete';});",
            "document.querySelector('#capability-form').addEventListener('submit',event=>event.preventDefault());setTimeout(()=>{success.textContent='Capability complete';},450);",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "success transition was not caused by the trusted submission",
            report["failures"],
        )
        self.assertFalse(report["interaction"]["submission"]["causedSuccess"])

    def test_microtask_success_from_trusted_submit_is_attributed(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();success.textContent='Capability complete';});",
            "document.querySelector('#capability-form').addEventListener('submit',event=>{event.preventDefault();Promise.resolve().then(()=>{success.textContent='Capability complete';});});",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        self.assertTrue(report["interaction"]["submission"]["causedSuccess"])

    def test_keyboard_submit_prevention_cannot_be_bypassed(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "<script>",
            "<script>document.querySelector('button[type=submit]').addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' ')event.preventDefault()});</script><script>",
            1,
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "no trusted keyboard submission was observed",
            report["failures"],
        )
        self.assertFalse(report["interaction"]["submission"]["trustedSubmit"])

    def test_final_state_is_resampled_at_screenshot_time(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "success.textContent='Capability complete';",
            "success.textContent='Capability complete';setTimeout(()=>{success.textContent='';},1600);",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "success state did not remain visible at screenshot time",
            report["failures"],
        )
        self.assertFalse(report["interaction"]["successVisible"])

    def test_runtime_rendered_forbidden_text_fails(self):
        canary = "RUNTIME_VISIBLE_PRIVATE_CANARY_73a6"
        html = EMPTY_SUCCESS_HTML.replace(
            "success.textContent='Capability complete';",
            "success.textContent='Capability complete';const leak=document.createElement('p');leak.textContent=atob('"
            + base64.b64encode(b"RUNTIME_VISIBLE_PRIVATE_CANARY_73a6").decode()
            + "');document.body.append(leak);",
        )
        temporary, completed, report = self.run_browser(
            html,
            forbidden_text=canary,
        )
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn("forbidden text became visible", report["failures"])
        self.assertTrue(report["interaction"]["forbiddenTextVisible"])

    def test_permissive_fetch_directive_override_is_not_durable(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "img-src data:;",
            "img-src data: https:;",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "document lacks a durable no-network content security policy",
            report["failures"],
        )
        self.assertFalse(report["network"]["durablePolicy"])

    def test_web_animations_api_motion_must_be_suppressed_for_reduced_users(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "<script>",
            "<script>document.querySelector('button').animate([{transform:'translateX(0)'},{transform:'translateX(8px)'}],{duration:1000,iterations:Infinity});</script><script>",
            1,
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "reduced-motion path did not suppress active motion",
            report["failures"],
        )
        self.assertGreater(
            report["interaction"]["motion"]["reducedMaxMs"],
            50,
        )

    def test_transient_submission_motion_is_replayed_for_reduced_users(self):
        html = (
            EMPTY_SUCCESS_HTML.replace(
                "button{transition:transform .2s}",
                "button{transition:none}",
            )
            .replace(
                "@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}",
                "@media(prefers-reduced-motion:reduce){}",
            )
            .replace(
                "success.textContent='Capability complete';",
                "success.textContent='Capability complete';"
                "success.animate([{transform:'translateY(12px)'},{transform:'translateY(0)'}],"
                "{duration:400,iterations:1});",
            )
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode)
        self.assertIn(
            "reduced-motion path did not suppress active motion",
            report["failures"],
        )
        self.assertTrue(
            report["interaction"]["motion"]["reducedSubmissionReplayPerformed"]
        )
        self.assertGreater(
            report["interaction"]["motion"]["reducedSubmissionMaxMs"],
            50,
        )

    def test_reduced_motion_replay_runs_dom_content_loaded_handler(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "<script>",
            "<script>document.addEventListener('DOMContentLoaded',()=>{",
            1,
        ).replace(
            "</script></body>",
            "});</script></body>",
            1,
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        self.assertTrue(
            report["interaction"]["motion"]["reducedSubmissionReplayContractPassed"]
        )

    def test_reduced_motion_replay_executes_application_scripts_once(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "<script>",
            "<script>"
            "window.__capabilityInitCount=(window.__capabilityInitCount||0)+1;"
            "if(window.__capabilityInitCount>1){"
            "document.querySelector('#capability-form')?.remove();"
            "}",
            1,
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        self.assertTrue(
            report["interaction"]["motion"]["reducedSubmissionReplayContractPassed"]
        )
        self.assertIsNone(
            report["interaction"]["motion"]["reducedSubmissionReplayError"]
        )

    def test_reduced_motion_replay_error_is_reported_distinctly(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "<script>",
            "<script>"
            "if(matchMedia('(prefers-reduced-motion: reduce)').matches){"
            "document.querySelector('#capability-form')?.remove();"
            "}",
            1,
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(1, completed.returncode, completed.stderr + completed.stdout)
        replay_failures = [
            failure
            for failure in report["failures"]
            if failure.startswith("reduced-motion submission replay did not run:")
        ]
        self.assertEqual(1, len(replay_failures), report["failures"])
        self.assertNotIn(
            "reduced-motion path did not suppress active motion",
            report["failures"],
        )

    def test_page_request_animation_frame_override_cannot_hang_probe(self):
        html = EMPTY_SUCCESS_HTML.replace(
            "<script>",
            "<script>window.requestAnimationFrame=()=>0;</script><script>",
            1,
        )
        temporary, completed, report = self.run_browser(html, timeout=25)
        self.addCleanup(temporary.cleanup)

        self.assertIn(completed.returncode, (0, 1), completed.stderr + completed.stdout)
        self.assertIn(report["status"], ("passed", "failed"))

    def test_parent_focus_within_indicator_is_accepted(self):
        html = EMPTY_SUCCESS_HTML.replace(
            '<form id="capability-form">',
            '<form id="capability-form"><div class="input-shell">',
        ).replace(
            '<button type="submit">',
            '</div><div class="submit-shell"><button type="submit">',
        ).replace(
            '</button></form>',
            '</button></div></form>',
        ).replace(
            "button:focus-visible,input:focus-visible{outline:3px solid #176b5b}",
            "button:focus-visible,input:focus-visible{outline:none}.input-shell:focus-within,.submit-shell:focus-within{outline:3px solid #176b5b}",
        )
        temporary, completed, report = self.run_browser(html)
        self.addCleanup(temporary.cleanup)

        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        self.assertTrue(report["interaction"]["focus"]["visible"])

    def test_invalid_chrome_path_is_reported_as_blocked(self):
        temporary, completed, report = self.run_browser(
            EMPTY_SUCCESS_HTML,
            environment={"CHROME_PATH": "/definitely/missing/design-studio-chrome"},
            timeout=10,
        )
        self.addCleanup(temporary.cleanup)

        self.assertEqual(2, completed.returncode, completed.stderr + completed.stdout)
        self.assertEqual("blocked", report["status"])
        self.assertIn("Chrome", report["error"])


if __name__ == "__main__":
    unittest.main()
