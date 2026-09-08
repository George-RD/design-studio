from __future__ import annotations

import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "skills/design-studio/runtime/design-authority/index.mjs"
FIXTURE = ROOT / "test/fixtures/design-authority"


class DesignAuthorityProfileTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.design = self.root / "DESIGN.md"
        shutil.copy2(FIXTURE / "DESIGN.md", self.design)

    def invoke(self, *args):
        return subprocess.run(
            ["node", str(RUNTIME), *map(str, args)],
            text=True, encoding="utf-8", capture_output=True, timeout=15,
        )

    def mutate_profile(self, change):
        parts = self.design.read_text().split("---", 2)
        profile = json.loads(parts[1])
        change(profile)
        self.design.write_text("---\n" + json.dumps(profile, indent=2) + "\n---" + parts[2])

    def materialize_consumers(self):
        output = self.root / "exports.json"
        result = self.invoke("export", self.design, output)
        self.assertEqual(0, result.returncode, result.stderr)
        exported = json.loads(output.read_text(encoding="utf-8"))
        tokens = self.root / "tokens.css"
        tokens.write_text(exported["tokensCss"], encoding="utf-8")
        skill = self.root / "project-design"
        (skill / "assets").mkdir(parents=True)
        (skill / "DESIGN.md").write_text(exported["design"], encoding="utf-8")
        (skill / "assets/tokens.css").write_text(exported["tokensCss"], encoding="utf-8")
        (skill / "SKILL.md").write_text("# Project design\nRead [Portable authority](DESIGN.md).\n", encoding="utf-8")
        shutil.copy2(FIXTURE / "design-dna.md", skill / "design-dna.md")
        return tokens, skill

    def test_export_stdout_and_receipt_explicitly_leave_acceptance_unverified(self):
        """Successful derivation is not an acceptance decision in either interface."""
        output = self.root / "receipt.json"
        result = self.invoke("export", self.design, output)
        self.assertEqual(0, result.returncode, result.stderr)
        summary = json.loads(result.stdout)
        receipt = json.loads(output.read_text(encoding="utf-8"))
        self.assertIs(False, summary.get("acceptanceVerified"))
        self.assertIs(False, receipt["acceptanceVerified"])
        self.assertEqual(receipt["authorityDigest"], summary["authorityDigest"])

    def test_imported_runtime_does_not_execute_cli_for_eval_or_stdin(self):
        """The portable public API remains importable without CLI side effects."""
        program = (
            f"import {{ inspectDesignAuthority }} from {json.dumps(RUNTIME.as_uri())}; "
            "console.log(JSON.stringify(inspectDesignAuthority('# Legacy')));"
        )
        for args, source in [(["--eval", program], None), (["-"], program)]:
            with self.subTest(args=args[0]):
                result = subprocess.run(
                    ["node", "--input-type=module", *args], input=source,
                    text=True, encoding="utf-8", capture_output=True, timeout=15,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stderr)
                self.assertEqual({"status": "legacy-unprofiled", "acceptanceVerified": False},
                                 json.loads(result.stdout))

    def test_actual_exported_files_and_linked_dna_match_the_profile(self):
        tokens, skill = self.materialize_consumers()
        result = self.invoke("check", self.design, tokens, skill)
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual("verified-parity", report["status"])
        self.assertEqual([], report["findings"])
        self.assertFalse(report["acceptanceVerified"])

    def test_drift_checks_consumer_contents_not_a_cached_receipt(self):
        tokens, skill = self.materialize_consumers()
        original = {p: p.read_bytes() for p in [tokens, skill / "assets/tokens.css", skill / "DESIGN.md", skill / "design-dna.md", skill / "SKILL.md"]}
        cases = [
            (tokens, "#14222e", "#ffffff", "token-value-drift"),
            (skill / "assets/tokens.css", "0.5rem", "1rem", "token-value-drift"),
            (skill / "DESIGN.md", '"action.primary"', '"action.destructive"', "semantic-role-drift"),
            (skill / "DESIGN.md", '"fixture-authority"', '"different-run"', "provenance-drift"),
            (skill / "DESIGN.md", '"#f5f2ea"', '"#dddddd"', "token-value-drift"),
            (skill / "design-dna.md", "#", "##", "provenance-drift"),
            (skill / "SKILL.md", "(DESIGN.md)", "(other.md)", "authority-pointer-missing"),
            (skill / "SKILL.md", "(DESIGN.md)", "(/DESIGN.md)", "authority-pointer-missing"),
            (skill / "SKILL.md", "(DESIGN.md)", "(.DESIGN.md)", "authority-pointer-missing"),
        ]
        for path, before, after, rule in cases:
            with self.subTest(path=path.name, rule=rule):
                for target, content in original.items():
                    target.write_bytes(content)
                path.write_text(path.read_text(encoding="utf-8").replace(before, after), encoding="utf-8")
                result = self.invoke("check", self.design, tokens, skill)
                self.assertEqual(2, result.returncode, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual("parity-failed", report["status"])
                self.assertIn(rule, [finding["ruleId"] for finding in report["findings"]])

    def test_parity_requires_an_active_authority_link_not_an_example(self):
        """Hidden examples and comments cannot stand in for the usable index pointer."""
        tokens, skill = self.materialize_consumers()
        pointer = "[Portable authority](DESIGN.md)"
        invalid = [
            f"```md\n{pointer}\n```\n",
            f"~~~md\n{pointer}\n~~~\n",
            f"```md\n```junk\n{pointer}\n",
            f"<!-- {pointer} -->",
            f"<!--\n{pointer}\n-->",
            f"`{pointer}`",
            f"`` {pointer} ``",
            f"`example\n{pointer}\nend`",
            f"    {pointer}",
            f"\t{pointer}",
            "![Portable authority](DESIGN.md)",
            "![Example [Portable authority](DESIGN.md)](screenshot.png)",
            "\\[Portable authority](DESIGN.md)",
            "Portable authority](DESIGN.md)",
            "[](DESIGN.md)",
        ]
        for index, text in enumerate(invalid):
            with self.subTest(index=index):
                (skill / "SKILL.md").write_text(text, encoding="utf-8")
                result = self.invoke("check", self.design, tokens, skill)
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn("authority-pointer-missing", [f["ruleId"] for f in json.loads(result.stdout)["findings"]])
        for text in [
            "Read [Portable authority](./DESIGN.md#overview).",
            f"<!-- example\n```\n-->\nRead {pointer}.\n",
            f"```md\n<!--\n```\nRead {pointer}.",
            f"```md\n{pointer}\n```\nRead {pointer}.",
            f"`unclosed literal\nRead {pointer}.",
            f"```md <!--\nexample\n```\nRead {pointer}.",
            f"A literal `<!--` marker. Read {pointer}.",
            "Read [`DESIGN.md`](DESIGN.md).",
        ]:
            with self.subTest(valid=text):
                (skill / "SKILL.md").write_text(text, encoding="utf-8")
                result = self.invoke("check", self.design, tokens, skill)
                self.assertEqual(0, result.returncode, result.stderr)

    def test_missing_consumers_are_incomplete_not_a_clean_result(self):
        tokens, skill = self.materialize_consumers()
        (skill / "DESIGN.md").unlink()
        result = self.invoke("check", self.design, tokens, skill)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("consumer-missing", [f["ruleId"] for f in json.loads(result.stdout)["findings"]])

    def test_legacy_readability_does_not_claim_new_profile_or_acceptance(self):
        self.design.write_text("# Existing accepted system\nUse the recorded DNA and tokens.\n", encoding="utf-8")
        before = self.design.read_bytes()
        result = self.invoke("inspect", self.design)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("legacy-unprofiled", json.loads(result.stdout)["status"])
        self.assertFalse(json.loads(result.stdout)["acceptanceVerified"])
        self.assertEqual(2, self.invoke("export", self.design, self.root / "out.json").returncode)
        self.assertFalse((self.root / "out.json").exists())
        self.assertEqual(before, self.design.read_bytes())

    def test_inspection_never_downgrades_a_broken_local_profile_to_legacy(self):
        self.mutate_profile(lambda p: p.pop("provenance"))
        result = self.invoke("inspect", self.design)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_inspection_checks_header_declarations_without_scanning_legacy_guidance(self):
        """Damaged declarations fail; profile examples in legacy prose do not."""
        cases = [
            ('{"pro\\u0066ile":"design-studio\\/design-authority",', True),
            ('{"profile" "unknown/authority"}', True),
            ('{"pro\\u0066ile" "unknown/authority"}', True),
            ('profile: unknown/authority', True),
            ('{"name":"Legacy"}', False),
            ('name: Legacy', False),
            ('{"name":"Legacy",', False),
            ('{"notes":"design-studio/design-authority"}', False),
            ('{"metadata":{"profile":"user"}}', False),
            ('{"name":"profile",', False),
            ('{"notes":"Mention {profile in a string",', False),
        ]
        body = '\n# Legacy guidance\nAn optional design-studio/design-authority profile is documented here.\n'
        for header, declared in cases:
            with self.subTest(header=header):
                guidance = '\n# Existing guidance\n' if declared else body
                self.design.write_text('---\n' + header + '\n---' + guidance, encoding="utf-8")
                before = self.design.read_bytes()
                result = self.invoke("inspect", self.design)
                self.assertEqual(2 if declared else 0, result.returncode, result.stderr)
                if declared:
                    self.assertEqual("", result.stdout)
                else:
                    self.assertEqual("legacy-unprofiled", json.loads(result.stdout)["status"])
                    self.assertFalse(json.loads(result.stdout)["acceptanceVerified"])
                self.assertEqual(before, self.design.read_bytes())
        # A missing closing delimiter cannot hide even an unknown declaration.
        self.design.write_text('---\n{"pro\\u0066ile":"unknown/authority"}\n', encoding="utf-8")
        result = self.invoke("inspect", self.design)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_installed_runtime_is_self_contained_and_accepts_portable_newlines(self):
        isolated = self.root / "installed-skill"
        shutil.copytree(ROOT / "skills/design-studio", isolated)
        runtime = isolated / "runtime/design-authority/index.mjs"
        self.design.write_bytes(self.design.read_bytes().replace(b"\n", b"\r\n"))
        result = subprocess.run(["node", str(runtime), "export", str(self.design), str(self.root / "crlf.json")],
                                cwd=self.root, capture_output=True, text=True, encoding="utf-8", timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue((self.root / "crlf.json").is_file(), result.stdout)
        output = json.loads((self.root / "crlf.json").read_text(encoding="utf-8"))
        self.assertNotIn("\r", output["tokensCss"])
        self.assertNotIn("\r", output["design"])

    def test_export_runs_when_installed_directory_has_a_filesystem_alias(self):
        """A symlink or Windows junction must not turn a CLI run into a no-op."""
        installed = self.root / "installed skill"
        shutil.copytree(ROOT / "skills/design-studio", installed)
        alias = self.root / "aliased skill"
        link = subprocess.run(
            ["node", "--input-type=module", "-e",
             "import { symlinkSync } from 'node:fs'; "
             "symlinkSync(process.argv[1], process.argv[2], 'junction');",
             str(installed), str(alias)],
            capture_output=True, text=True, encoding="utf-8", timeout=15,
        )
        self.assertEqual(0, link.returncode, link.stderr)
        output = self.root / "aliased-export.json"
        result = subprocess.run(
            ["node", str(alias / "runtime/design-authority/index.mjs"),
             "export", str(self.design), str(output)],
            cwd=self.root, capture_output=True, text=True, encoding="utf-8", timeout=15,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(output.is_file(), "Successful export must create the requested receipt")
        self.assertEqual("derived", json.loads(result.stdout)["status"])
        self.assertFalse(json.loads(output.read_text(encoding="utf-8"))["acceptanceVerified"])

    def test_export_does_not_overwrite_an_existing_evidence_file(self):
        output = self.root / "existing.json"
        output.write_text("existing evidence", encoding="utf-8")
        result = self.invoke("export", self.design, output)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("existing evidence", output.read_text(encoding="utf-8"))

    def test_optional_document_rules_are_linked_without_becoming_token_authority(self):
        document = '{"pageRule": "Keep table headers on each page"}\n'
        sha = hashlib.sha256(document.encode("utf-8")).hexdigest()
        self.mutate_profile(lambda p: p["links"].update(documentVisualContract={
            "path": "harness-output/design-system/document-visual-contract.json", "sha256": sha,
        }))
        tokens, skill = self.materialize_consumers()
        missing = self.invoke("check", self.design, tokens, skill)
        self.assertEqual(2, missing.returncode)
        (skill / "document-visual-contract.json").write_text(document, encoding="utf-8")
        self.assertEqual(0, self.invoke("check", self.design, tokens, skill).returncode)
        (skill / "document-visual-contract.json").write_text(document.replace("each", "first"), encoding="utf-8")
        changed = self.invoke("check", self.design, tokens, skill)
        self.assertEqual(2, changed.returncode)
        self.assertIn("provenance-drift", [f["ruleId"] for f in json.loads(changed.stdout)["findings"]])

    def test_escaped_unknown_profile_declaration_cannot_downgrade_to_legacy(self):
        self.mutate_profile(lambda p: p.update(profile="unknown/authority"))
        self.design.write_text(self.design.read_text(encoding="utf-8").replace('"profile":', '"pro\\u0066ile":'), encoding="utf-8")
        result = self.invoke("inspect", self.design)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_broken_semantic_relationship_is_invalid_not_a_literal_css_value(self):
        self.mutate_profile(lambda p: p["tokens"]["color.action"].update(value="{color.missing}"))
        result = self.invoke("validate", self.design)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("unresolved token reference", result.stderr)
        self.assertEqual("", result.stdout)

    def test_exports_deterministic_css_including_theme_alias_relationships(self):
        output = self.root / "derived.json"
        result = self.invoke("export", self.design, output)
        self.assertEqual(0, result.returncode, result.stderr)
        derived = json.loads(output.read_text())
        self.assertEqual(
            ":root {\n"
            "  --color-action: var(--color-ink);\n"
            "  --color-ink: #14222e;\n"
            "  --space-control: var(--space-unit);\n"
            "  --space-unit: 0.5rem;\n"
            "}\n\n"
            '[data-theme="dark"] {\n'
            "  --color-action: var(--color-ink);\n"
            "  --color-ink: #f5f2ea;\n"
            "  --space-control: var(--space-unit);\n"
            "  --space-unit: 0.5rem;\n"
            "}\n",
            derived["tokensCss"],
        )
        self.assertEqual("action.primary", derived["tokenRoles"]["color.action"]["role"])
        self.assertEqual("color.ink", derived["tokenRoles"]["color.action"]["reference"])
        self.assertEqual(self.design.read_text(), derived["design"])
        self.assertFalse(derived["acceptanceVerified"])

    def test_invalid_profiles_are_rejected_before_export(self):
        cases = {
            "missing provenance": lambda p: p.pop("provenance"),
            "empty name": lambda p: p.update(name=" "),
            "missing guidance link": lambda p: p.update(links={}),
            "unverified source": lambda p: p["provenance"]["acceptance"].update(sha256="unknown"),
            "missing source paths": lambda p: p["provenance"].update(sourceTokenPaths=[]),
            "invalid iteration": lambda p: p["provenance"].update(acceptedIteration=True),
            "unknown top-level field": lambda p: p.update(variants={}),
            "empty tokens": lambda p: p.update(tokens={}),
            "unsafe CSS name": lambda p: p["tokens"]["color.action"].update(css="--a; color:red"),
            "duplicate CSS name": lambda p: p["tokens"]["color.action"].update(css="--color-ink"),
            "CSS injection": lambda p: p["tokens"]["color.ink"].update(value="#fff; color:red"),
            "untracked CSS dependency": lambda p: p["tokens"]["color.ink"].update(value="var(--outside)"),
            "unbalanced function": lambda p: p["tokens"]["color.ink"].update(value="rgb(1 2 3"),
            "unbalanced quote": lambda p: p["tokens"]["color.ink"].update(value='"unfinished'),
            "implicit inheritance": lambda p: p["tokens"]["color.ink"].update(value="inherit"),
            "unknown type": lambda p: p["tokens"]["color.ink"].update(type="untyped"),
            "cross-type alias": lambda p: p["tokens"]["color.action"].update(value="{space.unit}"),
            "base cycle": lambda p: p["tokens"]["color.ink"].update(value="{color.action}"),
            "theme cycle": lambda p: p["themes"]["dark"].update({"color.ink": "{color.action}"}),
            "unknown theme token": lambda p: p["themes"]["dark"].update({"color.missing": "#fff"}),
            "unsafe theme selector": lambda p: p.update(themes={'dark"] *': {"color.ink": "#fff"}}),
            "non-object token": lambda p: p["tokens"].update({"color.ink": None}),
            "unknown token field": lambda p: p["tokens"]["color.ink"].update(source="invented"),
            "non-string value": lambda p: p["tokens"]["color.ink"].update(value=5),
            "escaping source path": lambda p: p["links"]["designDna"].update(path="../other.md"),
        }
        for name, change in cases.items():
            with self.subTest(name=name):
                shutil.copy2(FIXTURE / "DESIGN.md", self.design)
                self.mutate_profile(change)
                output = self.root / ("invalid-" + name.replace(" ", "-")) / "derived.json"
                result = self.invoke("export", self.design, output)
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertFalse(output.exists())
                self.assertFalse(output.parent.exists())

    def test_literal_subset_rejects_resource_functions_before_writing_outputs(self):
        """URL-capable and unknown functions are not portable local token literals."""
        invalid = [
            'image-set("https://example.com/a.png" 1x)',
            '-webkit-image-set("https://example.com/a.png" 1x)',
            'IMAGE-SET("local.png" 1x)',
            'image("local.png", red)',
            'cross-fade(image("local.png"), linear-gradient(red, blue))',
            'src("https://example.com/a.png")',
            'future-resource("local.png")',
            'color(--external-profile 1 0 0)',
        ]
        original = self.design.read_bytes()
        for index, value in enumerate(invalid):
            for themed in [False, True]:
                with self.subTest(value=value, themed=themed):
                    self.design.write_bytes(original)
                    if themed:
                        self.mutate_profile(lambda p: p["themes"]["dark"].update({"color.ink": value}))
                    else:
                        self.mutate_profile(lambda p: p["tokens"]["color.ink"].update(value=value))
                    output = self.root / f"rejected-{index}-{themed}" / "receipt.json"
                    before = self.design.read_bytes()
                    result = self.invoke("export", self.design, output)
                    self.assertEqual(2, result.returncode, result.stderr)
                    self.assertFalse(output.parent.exists())
                    self.assertEqual(before, self.design.read_bytes())
        for value in [
            'rgb(20 30 40 / 0.5)', 'oklch(65% 0.15 230)',
            'color(display-p3 1 0 0)', 'color-mix(in srgb, red 25%, blue)',
            'linear-gradient(45deg, rgb(1 2 3), #fff)',
            'clamp(1rem, calc(2vw + 1rem), 3rem)', 'calc(100% - (2 * 1rem))',
            'cubic-bezier(0.2, 0, 0, 1)',
            '"Image(set)", sans-serif',
        ]:
            with self.subTest(literal=value):
                self.design.write_bytes(original)
                self.mutate_profile(lambda p: p["tokens"]["color.ink"].update(value=value))
                result = self.invoke("validate", self.design)
                self.assertEqual(0, result.returncode, result.stderr)

    def test_required_human_guidance_is_not_satisfied_by_code_fences(self):
        self.design.write_text(self.design.read_text().replace(
            "## Application guidance", "```md\n## Application guidance\n```"
        ))
        result = self.invoke("validate", self.design)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("Application guidance", result.stderr)

    def test_comments_do_not_supply_or_hide_required_guidance(self):
        """Only rendered prose outside comments and fenced examples satisfies guidance."""
        original = self.design.read_text(encoding="utf-8")
        header, body = original.rsplit("\n---", 1)
        headings = ["Overview", "Application guidance", "Anti-goals", "Ownership boundaries"]
        hidden_bodies = [
            "\n".join(f"## {heading}\n<!-- TODO -->\n" for heading in headings),
            "\n".join(f"## {heading}\n<!--\nTODO\n-->\n" for heading in headings),
            "<!--\n" + body + "\n-->",
            "<!--\n```\n-->\n" + body + "\n<!--\n```\n-->",
        ]
        # The final case has real prose between comments and must remain valid;
        # delimiters inside comments cannot change the surrounding fence state.
        for index, candidate in enumerate(hidden_bodies):
            with self.subTest(index=index):
                self.design.write_text(header + "\n---\n" + candidate, encoding="utf-8")
                result = self.invoke("validate", self.design)
                self.assertEqual(0 if index == 3 else 2, result.returncode, result.stderr)
        self.design.write_text(header + "\n---\n```md\n<!--\n```\n" + body, encoding="utf-8")
        result = self.invoke("validate", self.design)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_invalid_closing_fences_cannot_expose_hidden_guidance(self):
        """Only a same-kind, long-enough fence followed by whitespace can close."""
        original = self.design.read_text(encoding="utf-8")
        header, body = original.rsplit("\n---", 1)
        for opening, closing in [("```md", "```junk"), ("~~~md", "~~~junk"),
                                 ("````md", "```"), ("```md", "~~~"),
                                 ("```md", "```<!-- not whitespace -->")]:
            with self.subTest(opening=opening, closing=closing):
                self.design.write_text(header + "\n---\n" + opening + "\nexample\n" +
                                       closing + "\n" + body, encoding="utf-8")
                result = self.invoke("validate", self.design)
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn("Overview", result.stderr)
        for opening, closing in [("```md", "````  "), ("~~~md", "~~~\t")]:
            with self.subTest(valid_closing=closing):
                self.design.write_text(header + "\n---\n" + opening + "\nexample\n" +
                                       closing + "\n" + body, encoding="utf-8")
                result = self.invoke("validate", self.design)
                self.assertEqual(0, result.returncode, result.stderr)

    def test_duplicate_json_keys_are_not_silently_resolved_by_order(self):
        self.design.write_text(self.design.read_text().replace(
            '"schemaVersion": 1,', '"schemaVersion": 1, "schemaVersion": 1,'
        ))
        result = self.invoke("validate", self.design)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("duplicate JSON key", result.stderr)

    def test_validate_preserves_supplied_profile_and_reports_explicit_lineage(self):
        before = self.design.read_bytes()
        result = self.invoke("validate", self.design)
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual("valid-profile", report["status"])
        self.assertEqual("fixture-authority", report["provenance"]["runId"])
        self.assertEqual(2, report["provenance"]["acceptedIteration"])
        self.assertEqual(4, report["tokenCount"])
        self.assertFalse(report["acceptanceVerified"])
        self.assertEqual(before, self.design.read_bytes())


if __name__ == "__main__":
    unittest.main()
