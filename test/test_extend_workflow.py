"""Extend execution contracts at the validated Design Intent / workflow seam."""

import json
from pathlib import Path
import subprocess
import unittest

from jsonschema import Draft202012Validator
import yaml

from test_method_kernel_routing import matching_route_ids


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/design-studio"


def workflow_contract():
    return yaml.safe_load((SKILL / "workflow.yaml").read_text(encoding="utf-8"))["workflow"]


class ExtendWorkflowTests(unittest.TestCase):
    def test_validated_extension_is_an_executable_studio_mode(self):
        contract = json.loads((SKILL / "design-intent-contract.json").read_text())
        intent = next(case["result"] for case in contract["classificationExamples"]
                      if case["id"] == "accepted-world-new-route")
        result = subprocess.run(
            ["node", str(SKILL / "runtime/design-intent/index.mjs")],
            input=json.dumps(intent), text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        validated = json.loads(result.stdout)
        self.assertEqual(validated["designMode"], "extend")
        self.assertIn(
            validated["designMode"],
            workflow_contract()["schemas"]["runManifest"]["properties"]["mode"]["enum"],
            "A validated extension must execute without being recast as greenfield or overhaul",
        )

    def test_extension_routes_to_bounded_exploration_not_replacement_worlds(self):
        router = json.loads((SKILL / "method-router.json").read_text())
        self.assertEqual(
            {"extend"},
            matching_route_ids(router, {"task": {"studio-extend"}, "surface": {"operate"}}),
        )
        route = next(row for row in router["routes"] if row["id"] == "extend")
        self.assertEqual("workflow.yaml", route["procedure"])
        self.assertEqual(["references/extend.md"], route["leaves"])
        workflow = workflow_contract()
        policy = workflow["modePolicies"]["extend"]
        self.assertEqual(0, policy["pivotBudget"])
        self.assertEqual({"default": 1, "maximum": 3}, policy["candidateCount"])
        steps = {step["id"]: step for step in workflow["steps"]}
        self.assertEqual("extension_preflight", steps["plan"]["next"])
        self.assertEqual("mode == extend", steps["extension_preflight"]["when"])
        self.assertEqual("baseline", steps["extension_preflight"]["otherwise"])
        self.assertEqual(
            [{"when": "mode == extend", "next": "explore_extension"},
             {"when": "default", "next": "explore_direction"}],
            steps["prepare_direction_assignment"]["branches"],
        )
        self.assertNotIn("next", steps["prepare_direction_assignment"])
        self.assertEqual("check_extension_direction", steps["explore_extension"]["next"])
        self.assertEqual("select_direction", steps["check_extension_direction"]["branches"][1]["next"])
        self.assertEqual("references/extend.md", steps["explore_extension"]["procedure"])
        self.assertIn("extend-bounded", workflow["schemas"]["directionAssignment"]["properties"]["mode"]["enum"])

    def test_accepted_extension_cannot_enter_global_codification(self):
        workflow = workflow_contract()
        steps = {step["id"]: step for step in workflow["steps"]}
        self.assertEqual(
            [{"when": "acceptance.status == accepted and mode == extend", "next": "complete_extension"},
             {"when": "mode == extend", "next": "reject_extension"},
             {"when": "acceptance.status == accepted", "next": "codify"},
             {"when": "default", "next": "halt"}],
            steps["accept"]["branches"],
        )
        preserved = {"design", "designDna", "tokens", "designSystemSkill", "DESIGN.md"}
        self.assertNotIn("outputs", steps["complete_extension"], "Completion must not require a delta for preserve")
        self.assertEqual(
            "modePolicies.extend.completion[finishAcceptance.systemEffect].outputs",
            steps["complete_extension"].get("outputsFrom"),
        )
        for policy in workflow["modePolicies"]["extend"]["completion"].values():
            self.assertTrue(preserved.isdisjoint(policy["outputs"]))
        self.assertEqual("report", steps["complete_extension"]["next"])
        self.assertEqual("halt", steps["reject_extension"]["next"])
        self.assertEqual(["extensionResult"], steps["reject_extension"]["outputs"])
        effects = workflow["modePolicies"]["extend"]["completion"]
        self.assertNotIn("proposedSystemDelta", effects["preserve"]["outputs"])
        self.assertIn("proposedSystemDelta", effects["extend"]["outputs"])
        result = workflow["schemas"]["extensionResult"]
        self.assertTrue({"status", "systemEffect", "requestedSystemEffect", "authorityUnchanged",
                         "acceptancePath", "proposedSystemDelta", "escalationPath"}.issubset(result["required"]))
        self.assertEqual(["preserve", "extend", "none"], result["properties"]["systemEffect"]["enum"])
        delta = workflow["schemas"]["proposedSystemDelta"]
        self.assertEqual("proposed", delta["properties"]["status"]["const"])
        self.assertTrue({"authorityRevision", "reusableRule", "rationale", "acceptancePath", "evidence"}.issubset(delta["required"]))

    def test_extension_escalation_is_explicit_and_precedes_shipping(self):
        steps = {step["id"]: step for step in workflow_contract()["steps"]}
        decisions = steps["decide"]["orderedDecisionTable"]
        escalate = next(row for row in decisions if row["decision"] == "ESCALATE")
        self.assertLess(decisions.index(escalate), next(i for i, row in enumerate(decisions) if row["decision"] == "SHIP"))
        self.assertIn("mode == extend", escalate["when"])
        self.assertIn("explicit user intent or recorded incompatibility evidence", escalate["when"])
        for row in decisions:
            if row["decision"] == "PIVOT":
                self.assertIn("mode != extend", row["when"])
        self.assertEqual("escalate_extension", steps["decide"]["transitions"]["ESCALATE"])
        self.assertEqual("halted", steps["escalate_extension"]["termination"])
        self.assertTrue({"extensionEscalation", "nextDesignIntent", "extensionResult"}.issubset(steps["escalate_extension"]["outputs"]))
        self.assertNotIn("compatibilitySite", steps["escalate_extension"]["outputs"])

    def test_extension_evaluation_receives_only_source_free_inherited_constraints(self):
        steps = {step["id"]: step for step in workflow_contract()["steps"]}
        for step_id in ("evaluate", "finish_review"):
            with self.subTest(step=step_id):
                self.assertIn("extensionVisualConstraints when extend", steps[step_id]["inputs"])
                for value in ("source", "raw design-system files", "extensionAuthorityManifest"):
                    self.assertIn(value, steps[step_id]["explicitlyExcluded"])
        self.assertIn("implementation effort", steps["evaluate"]["explicitlyExcluded"])
        self.assertIn("prior scores", steps["evaluate"]["explicitlyExcluded"])

    def test_end_to_end_scenarios_preserve_authority_and_bound_the_handoff(self):
        """Validate supplied intents and declared complete paths, not generated UI quality."""
        fixture_root = ROOT / "test/fixtures/extend"
        cases = sorted(fixture_root.glob("*/fixture.json"))
        self.assertEqual(4, len(cases))
        workflow = workflow_contract()
        steps = {step["id"]: step for step in workflow["steps"]}
        protected = set(workflow["modePolicies"]["extend"]["preservedAuthorities"])
        seen = set()
        for path in cases:
            case = json.loads(path.read_text())
            with self.subTest(case=case["id"]):
                seen.add(case["id"])
                result = subprocess.run(
                    ["node", str(SKILL / "runtime/design-intent/index.mjs")],
                    input=json.dumps(case["designIntent"]), text=True, capture_output=True, timeout=15,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                intent = json.loads(result.stdout)
                self.assertEqual("extend", intent["designMode"])
                self.assertEqual("accepted-design-system", intent["visualAuthority"])
                self.assertEqual(["workflow.yaml"], intent["selectedProcedures"])
                self.assertTrue((path.parent / case["acceptedAuthority"]).is_file())
                self.assertEqual("synthetic-contract-fixture", case["evidenceKind"])
                self.assertTrue(case["request"].strip())
                self.assertEqual(
                    {"thesis", "tokenRoles", "controlGrammar", "responsiveLogic", "antiGoals"},
                    set(case["inheritedConstraints"]),
                )
                for constraint in case["inheritedConstraints"].values():
                    self.assertTrue(constraint)
                expected = case["expected"]
                route = expected["stepPath"]
                self.assertEqual("initialise", route[0])
                self.assertNotIn("explore_direction", route)
                self.assertNotIn("prepare_pivot_iteration", route)
                self.assertNotIn("codify", route)
                for before, after in zip(route, route[1:]):
                    step = steps[before]
                    destinations = {step.get("next"), step.get("otherwise")}
                    destinations.update(step.get("transitions", {}).values())
                    destinations.update(branch["next"] for branch in step.get("branches", []))
                    self.assertIn(after, destinations, (case["id"], before, after))
                self.assertIn(steps[route[-1]]["termination"], ("complete", "halted"))
                if expected["status"] == "accepted":
                    self.assertIn("evaluate", route)
                    self.assertIn("accept", route)
                    policy = workflow["modePolicies"]["extend"]["completion"][expected["systemEffect"]]
                    self.assertEqual(expected["publicationState"], policy["publicationState"])
                    self.assertEqual(expected["outputs"], policy["outputs"])
                    self.assertTrue(protected.isdisjoint(policy["outputs"]))
                else:
                    self.assertEqual(expected["outputs"], steps["escalate_extension"]["outputs"])
                    self.assertEqual("escalate_extension", route[-1])
                    self.assertNotIn("build", route)
                    self.assertTrue(case["incompatibilityEvidence"])
                    self.assertEqual("none", expected["systemEffect"])
                    next_intent = subprocess.run(
                        ["node", str(SKILL / "runtime/design-intent/index.mjs")],
                        input=json.dumps(case["nextDesignIntent"]), text=True, capture_output=True, timeout=15,
                    )
                    self.assertEqual(0, next_intent.returncode, next_intent.stderr)
                    self.assertEqual("overhaul", json.loads(next_intent.stdout)["designMode"])
                    self.assertNotEqual(intent, json.loads(next_intent.stdout))
        self.assertEqual({"new-page", "reusable-pattern", "one-off-component", "incompatible-extension"}, seen)

    def test_extension_can_ship_only_with_inherited_constraint_evidence(self):
        workflow = workflow_contract()
        steps = {step["id"]: step for step in workflow["steps"]}
        evidence = workflow["schemas"]["extensionConstraintEvidence"]
        self.assertEqual(["pass", "fail", "unverified"], evidence["properties"]["status"]["enum"])
        self.assertTrue({"status", "evidence", "violations"}.issubset(evidence["required"]))
        quality_ship = next(row for row in steps["decide"]["orderedDecisionTable"]
                            if row["terminationReason"] == "quality-floor-met")
        self.assertIn("accepted-world constraints pass", quality_ship["when"])
        self.assertIn("extensionConstraintEvidence", steps["evaluate"]["outputs"])
        self.assertIn("extensionConstraintEvidence when extend", steps["decide"]["inputs"])
        self.assertIn("extensionConstraintEvidence when extend", steps["finish_select"]["inputs"])
        self.assertIn("finishSelectedConstraintEvidence when extend", steps["accept"]["inputs"])
        self.assertIn("finishCorrectedConstraintEvidence when extend and corrected tree exists", steps["accept"]["inputs"])

    def test_finish_constraints_are_fresh_and_bound_to_the_selected_or_corrected_tree(self):
        workflow = workflow_contract()
        steps = {step["id"]: step for step in workflow["steps"]}
        evidence = workflow["schemas"]["extensionConstraintEvidence"]
        self.assertTrue({"treePath", "treeManifest"}.issubset(evidence["required"]))
        self.assertIn("finishSelectedConstraintEvidence", steps["finish_review"]["outputs"])
        self.assertIn("finishCorrectedConstraintEvidence", steps["finish_fix"]["outputs"])
        self.assertIn("finishCorrectedConstraintEvidence when extend", steps["finish_correction_decide"]["inputs"])
        correction_guard = steps["finish_correction_decide"]["branches"][0]["when"]
        self.assertIn("finishCorrectedConstraintEvidence.status == pass", correction_guard)
        self.assertIn("receipt matches the corrected tree", correction_guard)
        self.assertNotIn("extensionConstraintEvidence when extend", steps["accept"]["inputs"])
        for name in ("finishSelectedConstraintEvidence", "finishCorrectedConstraintEvidence"):
            self.assertIn("/finish/", workflow["paths"][name])
            self.assertNotIn("{N}", workflow["paths"][name])

    def test_multiple_local_candidates_require_a_nonblank_recorded_question(self):
        schema = workflow_contract()["schemas"]["extensionScope"]
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        base = {key: "fixture" for key in schema["required"]}
        base["requestedSystemEffect"] = "preserve"
        for count in (1, 2, 3):
            for question in (None, "", "   ", "Compare tab placement"):
                with self.subTest(candidateCount=count, localQuestion=question):
                    scope = dict(base, candidateCount=count, localQuestion=question)
                    expected = count == 1 or bool(question and question.strip())
                    self.assertEqual(expected, validator.is_valid(scope))

    def test_no_eligible_extension_has_a_rejection_edge_before_finish_review(self):
        steps = {step["id"]: step for step in workflow_contract()["steps"]}
        select = steps["finish_select"]
        self.assertNotIn("next", select, "Selection failure must not fall through to review")
        self.assertEqual(
            [{"when": "mode == extend and no eligible iteration remains", "next": "reject_extension"},
             {"when": "eligible iteration selected and finish artifacts valid", "next": "finish_review"},
             {"when": "default", "next": "halt"}],
            select["branches"],
        )
        self.assertEqual("halt", steps["reject_extension"]["next"])
        self.assertEqual(["extensionResult"], steps["reject_extension"]["outputs"])

    def test_changed_authority_rejects_before_any_publication_action(self):
        steps = {step["id"]: step for step in workflow_contract()["steps"]}
        publication = steps["complete_extension"]
        self.assertEqual(
            "accepted final-tree proof and immediate authority recheck pass",
            publication.get("when"),
            "Publication needs a current entry guard, not only an earlier accepted receipt",
        )
        self.assertEqual("reject_extension", publication["otherwise"])
        self.assertEqual("report", publication["next"])
        self.assertEqual(["extensionResult"], steps[publication["otherwise"]]["outputs"])

    def test_extension_authority_is_checked_before_resuming_or_publishing(self):
        workflow = workflow_contract()
        manifest = workflow["schemas"]["extensionAuthorityManifest"]
        self.assertTrue({"authorityRevision", "entries"}.issubset(manifest["required"]))
        entry = manifest["properties"]["entries"]["items"]
        self.assertEqual(["file", "directory", "absent"], entry["properties"]["kind"]["enum"])
        self.assertTrue({"path", "kind", "sha256", "members"}.issubset(entry["required"]))
        steps = {step["id"]: step for step in workflow["steps"]}
        self.assertIn("extensionAuthorityManifest when extend", steps["resume_validate"]["inputs"])
        self.assertIn("extensionAuthorityManifest", steps["complete_extension"]["inputs"])
        preflight = steps["extension_preflight"]
        self.assertEqual("halt", preflight["branches"][0]["next"])
        self.assertIn("missing or stale or conflicting", preflight["branches"][0]["when"])


if __name__ == "__main__":
    unittest.main()
