"""Installed authority boundary and schema contracts for #92; no lifecycle migration."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from jsonschema import Draft202012Validator
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/design-studio"
PROFILE = SKILL / "references/design-authority"


class DesignAuthorityContractTests(unittest.TestCase):
    def test_schema_and_runtime_agree_on_fixture_and_structural_rejections(self):
        schema = json.loads((PROFILE / "design-authority.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        fixture = (ROOT / "test/fixtures/design-authority/DESIGN.md").read_text(encoding="utf-8")
        parts = fixture.split("---", 2)
        profile = json.loads(parts[1])
        validator.validate(profile)
        cases = [
            lambda p: p.pop("links"),
            lambda p: p["tokens"]["color.ink"].update(type="unknown"),
            lambda p: p["provenance"].update(acceptedIteration=True),
            lambda p: p["links"]["designDna"].update(path="../escape.md"),
            lambda p: p.update(extra="unknown"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            for index, change in enumerate(cases):
                with self.subTest(case=index):
                    candidate = copy.deepcopy(profile)
                    change(candidate)
                    self.assertTrue(list(validator.iter_errors(candidate)))
                    path = Path(tmp) / "DESIGN.md"
                    path.write_text("---\n" + json.dumps(candidate) + "\n---" + parts[2], encoding="utf-8")
                    result = subprocess.run(["node", str(SKILL / "runtime/design-authority/index.mjs"), "validate", str(path)],
                                            capture_output=True, text=True, encoding="utf-8", timeout=15)
                    self.assertEqual(2, result.returncode, result.stderr)

    def test_profile_loads_at_codification_not_on_the_universal_hot_path(self):
        workflow = yaml.safe_load((SKILL / "workflow.yaml").read_text(encoding="utf-8"))["workflow"]
        steps = {step["id"]: step for step in workflow["steps"]}
        actions = "\n".join(steps["codify"]["actions"])
        self.assertIn("references/design-authority/profile.md", actions)
        for operation in ["validate_design_authority", "derive_design_authority", "check_design_authority_parity"]:
            self.assertIn(operation, actions)
            self.assertIn(f"`{operation}`", (SKILL / "runtime-contract.md").read_text(encoding="utf-8"))
        contract = json.loads((SKILL / "method-router.json").read_text(encoding="utf-8"))
        self.assertNotIn("references/design-authority/profile.md", contract["coreAuthorities"])
        self.assertNotIn("runtime/design-authority", (PROFILE / "profile.md").read_text(encoding="utf-8"))

    def test_codification_requires_verified_parity_before_completion(self):
        """No failure, missing receipt, or unknown parity state may reach report."""
        workflow = yaml.safe_load((SKILL / "workflow.yaml").read_text(encoding="utf-8"))["workflow"]
        steps = {step["id"]: step for step in workflow["steps"]}
        codify = steps["codify"]
        self.assertNotIn("next", codify)
        self.assertEqual(
            [{"when": "designAuthorityParity.status == verified-parity", "next": "publish_codification"},
             {"when": "default", "next": "halt"}],
            codify["branches"],
        )
        self.assertIn("designAuthorityParity", codify["outputs"])
        self.assertEqual("harness-output/runs/{runId}/finish/design-authority-parity.json",
                         workflow["paths"]["designAuthorityParity"])
        self.assertEqual("halted", steps["halt"]["termination"])
        self.assertEqual("report", steps["complete_extension"]["next"],
                         "Expand-stage verification must not migrate extension authority")

    def test_codification_stages_consumers_before_any_accepted_output_is_replaced(self):
        """Parity failure cannot reach the only step allowed to publish outputs."""
        workflow = yaml.safe_load((SKILL / "workflow.yaml").read_text(encoding="utf-8"))["workflow"]
        steps = {step["id"]: step for step in workflow["steps"]}
        self.assertEqual("harness-output/runs/{runId}/finish/design-authority-stage/",
                         workflow["paths"]["designAuthorityStage"])
        self.assertEqual({"designAuthorityStage", "designAuthorityParity"}, set(steps["codify"]["outputs"]))
        publish = steps["publish_codification"]
        self.assertNotIn("next", publish)
        self.assertEqual(
            [{"when": "designAuthorityPublication.status == published", "next": "report"},
             {"when": "default", "next": "halt"}],
            publish["branches"],
        )
        self.assertIn("designAuthorityPublication", publish["outputs"])
        self.assertEqual("harness-output/runs/{runId}/finish/design-authority-publication.json",
                         workflow["paths"]["designAuthorityPublication"])
        stage_actions = "\n".join(steps["codify"]["actions"])
        publish_actions = "\n".join(publish["actions"])
        self.assertIn("only inside designAuthorityStage", stage_actions)
        self.assertIn("accepted outputs untouched", stage_actions)
        self.assertIn("rollback", publish_actions)
        self.assertIn("check_design_authority_parity", publish_actions)
        self.assertIn("halt before writing", publish_actions)

    def test_generated_skill_links_profile_and_keeps_separate_dna_and_page_rules(self):
        template = (SKILL / "assets/design-system-skill/SKILL.md.template").read_text(encoding="utf-8")
        for reference in ["[DESIGN.md](DESIGN.md)", "assets/tokens.css", "design-dna.md", "document-visual-contract.json"]:
            self.assertIn(reference, template)
        self.assertNotIn('"tokens":', template)
        self.assertNotIn('"provenance":', template)

    def test_external_format_is_exactly_pinned_and_locally_owned(self):
        registry = json.loads((ROOT / "docs/method-sources.json").read_text(encoding="utf-8"))
        source = next(item for item in registry["sources"] if item["id"] == "google-labs-code/design.md")
        self.assertEqual("9bf8eae67128b6cc55ad9bf86665767deb4c11cd", source["revision"])
        self.assertEqual("Apache-2.0", source["license"])
        self.assertFalse(source["runtimeDependency"])
        self.assertEqual("adapt-local", source["currentDisposition"])
        historical = json.loads((ROOT / "docs/migration-map.json").read_text(encoding="utf-8"))
        baseline = next(item for item in historical["conceptMap"] if item["id"] == "design-system-codification")
        self.assertNotIn("google-labs-code/design.md", [item["source"] for item in baseline["externalOverlaps"]])
        profile = (PROFILE / "profile.md").read_text(encoding="utf-8")
        self.assertIn(source["revision"], profile)
        self.assertIn("legacy-unprofiled", profile)
        self.assertIn("no lifecycle migration or authority deletion", profile)

    def test_runtime_and_schema_contracts_have_existing_ci_owners(self):
        portability = (ROOT / ".github/workflows/runtime-portability.yml").read_text(encoding="utf-8")
        contracts = (ROOT / ".github/workflows/design-intent-contract.yml").read_text(encoding="utf-8")
        self.assertIn("test_design_authority_profile.py", portability)
        self.assertIn("test_design_authority_contract.py", contracts)


if __name__ == "__main__":
    unittest.main()
