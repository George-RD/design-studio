from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "design-studio"
RUNTIME = SKILL_ROOT / "runtime" / "design-intent" / "index.mjs"


class CompositionReadinessTests(unittest.TestCase):
    """Website preflight through the installed validate_design_intent operation (#94)."""

    def intent(self, mode: str = "create", state: str = "missing") -> dict:
        contract = json.loads((SKILL_ROOT / "design-intent-contract.json").read_text(encoding="utf-8"))
        result = copy.deepcopy(next(
            case["result"] for case in contract["classificationExamples"]
            if case["result"]["designMode"] == mode
        ))
        result["compositionState"] = state
        result["composition"] = {
            "project": "fixture-project",
            "strategySensitive": True,
            "growthArsenal": "absent",
            "artifacts": [],
        }
        return result

    def ready_intent(self, mode: str = "create") -> dict:
        intent = self.intent(mode, "ready")
        intent["composition"] = json.loads(
            (ROOT / "test/fixtures/composition-readiness.json").read_text()
        )
        return intent

    def run_intent(self, intent: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["node", str(RUNTIME)], input=json.dumps(intent),
            capture_output=True, text=True, encoding="utf-8", check=False, cwd=ROOT,
        )

    def validate(self, intent: dict) -> dict:
        run = self.run_intent(intent)
        self.assertEqual(0, run.returncode, run.stderr)
        return json.loads(run.stdout)

    def test_empty_website_records_missing_inputs_and_public_next_actions(self) -> None:
        output = self.validate(self.intent())
        receipt = output["composition"]["readiness"]
        self.assertEqual("missing", receipt["state"])
        self.assertFalse(receipt["mayProceed"])
        self.assertEqual({
            "product-truth": "missing", "audience-context": "missing",
            "offer-positioning": "missing", "commercial-copy": "missing",
            "visual-design": "not-applicable",
        }, {key: value["state"] for key, value in receipt["facets"].items()})
        self.assertEqual(
            {"product-truth", "audience-context", "offer-positioning", "commercial-copy"},
            {action["facet"] for action in receipt["actions"]},
        )
        self.assertTrue(all(action["skill"] is None for action in receipt["actions"]))
        self.assertEqual("shared-product-context", receipt["facets"]["audience-context"]["owner"])
        self.assertEqual("workflow.yaml", output["selectedProcedures"][0])

    def test_confirmed_supplied_inputs_are_ready_without_growth_arsenal(self) -> None:
        output = self.validate(self.ready_intent())
        receipt = output["composition"]["readiness"]
        self.assertEqual("ready", receipt["state"])
        self.assertTrue(receipt["mayProceed"])
        self.assertEqual([], receipt["actions"])
        audience = receipt["facets"]["audience-context"]
        self.assertEqual("PRODUCT.md#Users-and-situation", audience["authority"]["path"])
        self.assertEqual("audience-1", audience["authority"]["revision"])
        self.assertEqual(
            ["Compare stock across warehouses before placing an order."],
            [fact["text"] for fact in audience["audience"]["facts"]],
        )
        self.assertEqual(1, len(audience["audience"]["hypotheses"]))
        self.assertEqual(1, len(audience["audience"]["simulations"]))
        self.assertEqual("not-applicable", receipt["facets"]["visual-design"]["state"])
        self.assertEqual(output, self.validate(output), "the recorded receipt must validate again")

    def test_equal_authority_conflicts_cannot_be_resolved_by_input_order(self) -> None:
        intent = self.ready_intent()
        other = copy.deepcopy(intent["composition"]["artifacts"][1])
        other["path"] = "research/other-audience.md"
        other["provenance"]["revision"] = "audience-other"
        intent["composition"]["artifacts"].append(other)
        intent["compositionState"] = "conflicting"
        output = self.validate(intent)
        receipt = output["composition"]["readiness"]
        self.assertEqual("conflicting", receipt["facets"]["audience-context"]["state"])
        self.assertIsNone(receipt["facets"]["audience-context"]["authority"])
        self.assertFalse(receipt["mayProceed"])
        self.assertIn({"facet": "audience-context", "owner": "shared-product-context",
                       "action": "request-user-designation", "skill": None}, receipt["actions"])
        intent["composition"]["artifacts"].reverse()
        self.assertEqual(receipt, self.validate(intent)["composition"]["readiness"])

    def test_explicit_designation_resolves_exact_source_not_filename(self) -> None:
        intent = self.ready_intent()
        other = copy.deepcopy(intent["composition"]["artifacts"][1])
        other["path"] = "AUDIENCE.md"
        other["provenance"]["revision"] = "audience-other"
        intent["composition"]["artifacts"].insert(0, other)
        intent["composition"]["designations"] = [{
            "facet": "audience-context", "path": "PRODUCT.md#Users-and-situation",
            "revision": "audience-1",
            "evidence": [{"kind": "user-designation", "ref": "decisions/audience-1"}],
        }]
        receipt = self.validate(intent)["composition"]["readiness"]
        self.assertTrue(receipt["mayProceed"])
        self.assertEqual("audience-1", receipt["facets"]["audience-context"]["authority"]["revision"])

    def test_changed_audience_revision_stales_dependent_offer_and_copy_only(self) -> None:
        intent = self.ready_intent("extend")
        intent["composition"]["artifacts"][1]["provenance"]["revision"] = "audience-2"
        intent["compositionState"] = "stale"
        receipt = self.validate(intent)["composition"]["readiness"]
        self.assertEqual({
            "product-truth": "ready", "audience-context": "ready",
            "offer-positioning": "stale", "commercial-copy": "stale", "visual-design": "ready",
        }, {key: value["state"] for key, value in receipt["facets"].items()})
        self.assertFalse(receipt["mayProceed"])
        self.assertIn("dependency-changed:audience-context", receipt["facets"]["offer-positioning"]["reasons"])

    def test_staleness_propagates_even_when_direct_revision_did_not_change(self) -> None:
        intent = self.ready_intent("extend")
        intent["composition"]["artifacts"][2]["state"] = "stale"
        intent["compositionState"] = "stale"
        receipt = self.validate(intent)["composition"]["readiness"]
        self.assertEqual("stale", receipt["facets"]["offer-positioning"]["state"])
        self.assertIn("dependency-unready:offer-positioning", receipt["facets"]["commercial-copy"]["reasons"])
        self.assertEqual("ready", receipt["facets"]["visual-design"]["state"])

    def test_dependency_cycle_is_stale_instead_of_recursing_or_assuming_ready(self) -> None:
        intent = self.ready_intent()
        intent["composition"]["artifacts"][0]["provenance"]["dependencies"] = [{
            "facet": "commercial-copy", "path": "approved/home-copy.md", "revision": "copy-1",
        }]
        intent["compositionState"] = "stale"
        receipt = self.validate(intent)["composition"]["readiness"]
        self.assertEqual("stale", receipt["facets"]["product-truth"]["state"])
        self.assertEqual("stale", receipt["facets"]["commercial-copy"]["state"])
        self.assertEqual("ready", receipt["facets"]["audience-context"]["state"])

    def test_available_skill_changes_handoff_not_authority(self) -> None:
        intent = self.intent()
        intent["composition"]["growthArsenal"] = "available"
        receipt = self.validate(intent)["composition"]["readiness"]
        actions = {item["facet"]: item for item in receipt["actions"]}
        self.assertEqual("request-audience-context", actions["audience-context"]["action"])
        self.assertEqual("growth-arsenal", actions["audience-context"]["skill"])
        self.assertEqual("request-approved-offer-copy", actions["commercial-copy"]["action"])
        self.assertIsNone(actions["product-truth"]["skill"])
        self.assertFalse(receipt["mayProceed"])
        ready = self.ready_intent()
        ready["composition"]["growthArsenal"] = "available"
        self.assertEqual([], self.validate(ready)["composition"]["readiness"]["actions"])

    def test_unavailable_skill_records_degraded_path_without_fabrication(self) -> None:
        intent = self.intent()
        intent["composition"]["growthArsenal"] = "unavailable"
        receipt = self.validate(intent)["composition"]["readiness"]
        self.assertEqual("unavailable", receipt["adjacentSkill"])
        self.assertFalse(receipt["mayProceed"])
        self.assertTrue(all(action["skill"] is None for action in receipt["actions"]))

    def test_non_strategy_polish_is_not_blocked_by_missing_commercial_inputs(self) -> None:
        intent = self.ready_intent("polish")
        intent["composition"]["strategySensitive"] = False
        intent["composition"]["artifacts"] = intent["composition"]["artifacts"][4:]
        receipt = self.validate(intent)["composition"]["readiness"]
        self.assertTrue(receipt["mayProceed"])
        self.assertEqual("not-applicable", receipt["facets"]["commercial-copy"]["state"])
        self.assertEqual("ready", receipt["facets"]["visual-design"]["state"])

    def test_malformed_preflight_cannot_bypass_checks(self) -> None:
        for field, value in [("project", ""), ("strategySensitive", "false"),
                             ("strategySensitive", None), ("growthArsenal", "installed"),
                             ("artifacts", {}), ("designations", "first")]:
            with self.subTest(field=field, value=value):
                intent = self.ready_intent()
                intent["composition"][field] = value
                result = self.run_intent(intent)
                self.assertEqual(2, result.returncode)
                self.assertEqual("", result.stdout)
        intent = self.ready_intent()
        intent["composition"]["approved"] = True
        self.assertEqual(2, self.run_intent(intent).returncode)

    def test_designation_requires_current_explicit_evidence(self) -> None:
        for evidence in [[], [{"kind": "simulation", "ref": "persona-1"}]]:
            with self.subTest(evidence=evidence):
                intent = self.ready_intent()
                intent["composition"]["designations"] = [{
                    "facet": "audience-context", "path": "PRODUCT.md#Users-and-situation",
                    "revision": "audience-1", "evidence": evidence,
                }]
                self.assertEqual(2, self.run_intent(intent).returncode)

    def test_copy_without_dependency_provenance_is_not_current_authority(self) -> None:
        for dependencies in [None, [], [{"facet": "invented", "path": "x", "revision": "1"}]]:
            with self.subTest(dependencies=dependencies):
                intent = self.ready_intent()
                intent["composition"]["artifacts"][3]["provenance"]["dependencies"] = dependencies
                intent["compositionState"] = "missing"
                receipt = self.validate(intent)["composition"]["readiness"]
                self.assertEqual("missing", receipt["facets"]["commercial-copy"]["state"])

    def test_wrong_project_scope_state_and_source_names_cannot_grant_authority(self) -> None:
        for update in [{"scope": "growth-arsenal-repository"}, {"state": "candidate"},
                       {"provenance": {"project": "other-project"}},
                       {"provenance": {"evidence": [{"kind": "simulation", "ref": "personas/1"}]}},
                       {"provenance": {"revision": ""}}]:
            with self.subTest(update=update):
                intent = self.ready_intent()
                source = intent["composition"]["artifacts"][0]
                source["producer"] = "growth-arsenal"
                source["mtime"] = "2099-01-01"
                if "provenance" in update:
                    source["provenance"].update(update["provenance"])
                else:
                    source.update(update)
                intent["compositionState"] = "stale"
                receipt = self.validate(intent)["composition"]["readiness"]
                self.assertEqual("missing", receipt["facets"]["product-truth"]["state"])
                self.assertFalse(receipt["mayProceed"])

    def test_audience_simulations_cannot_supply_missing_facts(self) -> None:
        intent = self.ready_intent()
        source = intent["composition"]["artifacts"][1]
        source["provenance"]["audience"] = source["provenance"]["audience"][1:]
        intent["compositionState"] = "stale"
        receipt = self.validate(intent)["composition"]["readiness"]
        self.assertEqual("missing", receipt["facets"]["audience-context"]["state"])
        self.assertIsNone(receipt["facets"]["audience-context"]["authority"])

    def test_forged_readiness_and_manual_ready_state_are_rejected(self) -> None:
        output = self.validate(self.ready_intent())
        output["composition"]["readiness"]["mayProceed"] = False
        self.assertEqual(2, self.run_intent(output).returncode)
        missing = self.intent(state="ready")
        self.assertEqual(2, self.run_intent(missing).returncode)

    def test_one_approved_export_can_supply_offer_and_copy_with_explicit_facets(self) -> None:
        intent = self.ready_intent()
        artifacts = intent["composition"]["artifacts"]
        offer = artifacts[2]
        offer["provenance"]["facets"].append("commercial-copy")
        offer["provenance"]["dependencies"].append({
            "facet": "offer-positioning", "path": offer["path"], "revision": "offer-1",
        })
        del artifacts[3]
        receipt = self.validate(intent)["composition"]["readiness"]
        self.assertTrue(receipt["mayProceed"])
        self.assertEqual(receipt["facets"]["offer-positioning"]["authority"],
                         receipt["facets"]["commercial-copy"]["authority"])

    def test_approved_offer_does_not_implicitly_approve_commercial_copy(self) -> None:
        intent = self.ready_intent()
        del intent["composition"]["artifacts"][3]
        intent["compositionState"] = "missing"
        receipt = self.validate(intent)["composition"]["readiness"]
        self.assertEqual("ready", receipt["facets"]["offer-positioning"]["state"])
        self.assertEqual("missing", receipt["facets"]["commercial-copy"]["state"])

    def test_staged_visual_candidate_cannot_replace_accepted_authority(self) -> None:
        intent = self.ready_intent("extend")
        other = copy.deepcopy(intent["composition"]["artifacts"][4])
        other["state"] = "staged"
        other["provenance"]["revision"] = "visual-2"
        intent["composition"]["artifacts"].insert(0, other)
        receipt = self.validate(intent)["composition"]["readiness"]
        self.assertEqual("visual-1", receipt["facets"]["visual-design"]["authority"]["revision"])
        self.assertTrue(receipt["mayProceed"])

    def test_legacy_classification_examples_still_round_trip_without_preflight(self) -> None:
        contract = json.loads((SKILL_ROOT / "design-intent-contract.json").read_text(encoding="utf-8"))
        for example in contract["classificationExamples"]:
            with self.subTest(example=example["id"]):
                self.assertEqual(example["result"], self.validate(example["result"]))

    def test_document_requests_do_not_acquire_a_website_preflight(self) -> None:
        self.assertEqual(2, self.run_intent(self.ready_intent("document-create")).returncode)

    def test_recorded_receipt_rejects_later_changes_to_upstream_evidence(self) -> None:
        output = self.validate(self.ready_intent())
        output["composition"]["artifacts"][0]["provenance"]["revision"] = "product-2"
        output["compositionState"] = "stale"
        run = self.run_intent(output)
        self.assertEqual(2, run.returncode)
        self.assertIn("readiness does not match", run.stderr)

    def test_stale_source_is_evidence_but_not_current_authority(self) -> None:
        intent = self.ready_intent()
        intent["composition"]["artifacts"][2]["state"] = "stale"
        intent["compositionState"] = "stale"
        facet = self.validate(intent)["composition"]["readiness"]["facets"]["offer-positioning"]
        self.assertIsNone(facet["authority"])
        self.assertEqual("offer-1", facet["staleSource"]["revision"])

    def test_installed_runtime_needs_no_repository_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory) / "copied-skill"
            shutil.copytree(SKILL_ROOT, installed)
            source = Path(directory) / "input-世界.json"
            target = Path(directory) / "output-世界.json"
            intent = self.ready_intent()
            intent["composition"]["artifacts"][1]["provenance"]["audience"][0]["text"] = "庫存 · stock · مخزون"
            source.write_text(json.dumps(intent, ensure_ascii=False), encoding="utf-8")
            run = subprocess.run(["node", str(installed / "runtime/design-intent/index.mjs"),
                                  str(source), str(target)], cwd=directory,
                                 capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(0, run.returncode, run.stderr)
            self.assertEqual("ready", json.loads(target.read_text(encoding="utf-8"))["compositionState"])
            self.assertIn("庫存", target.read_text(encoding="utf-8"))

    def test_missing_installed_contract_is_an_io_failure_not_invalid_user_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory) / "copied-skill"
            shutil.copytree(SKILL_ROOT, installed)
            (installed / "composition-contract.json").unlink()
            run = subprocess.run(["node", str(installed / "runtime/design-intent/index.mjs")],
                                 input=json.dumps(self.ready_intent()), cwd=directory,
                                 capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(1, run.returncode)
            self.assertEqual("", run.stdout)


if __name__ == "__main__":
    unittest.main()
