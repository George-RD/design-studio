from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "comparison_agent.py"


def load_agent():
    spec = importlib.util.spec_from_file_location("comparison_agent", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load comparison agent from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeRequester:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, *, method, url, token, api_version, payload=None):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "token": token,
                "api_version": api_version,
                "payload": payload,
            }
        )
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def completion(content, usage=None):
    value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": json.dumps(content),
                }
            }
        ]
    }
    if usage is not None:
        value["usage"] = usage
    return value


def direction(name: str):
    return {
        "name": name,
        "thesis": f"{name} thesis",
        "visualWorld": f"{name} world",
        "materials": [f"{name} material"],
        "palette": ["#101010", "#f0f0f0"],
        "typography": f"{name} typography",
        "composition": f"{name} composition",
        "signatureInteraction": f"{name} interaction",
        "responsiveStrategy": f"{name} responsive",
        "risks": [f"{name} risk"],
        "proof": f"{name} proof",
    }


def file_bundle(index_content="<!doctype html><title>Generated</title>"):
    return {
        "files": [
            {"path": "index.html", "content": index_content},
            {"path": "styles.css", "content": "body { margin: 0; }"},
        ],
        "assumptions": ["No external assets are required."],
        "implementationSummary": "Created a static benchmark surface.",
    }


class ComparisonAgentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.agent = load_agent()

    def make_environment(
        self,
        *,
        lane="design-studio-current",
        fixture_kind="new-marketing-surface",
        status="prepared",
    ):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        repo = root / "repo"
        impeccable = root / "impeccable"
        run = root / "run"

        files = {
            repo / "skills/design-studio/agents/design-agent.md": "DIRECTOR_GUIDANCE",
            repo / "skills/design-studio/references/generation.md": "BUILDER_GUIDANCE",
            repo / "skills/design-studio/agents/evaluator.md": "EVALUATOR_GUIDANCE",
            impeccable / "skill/SKILL.src.md": "IMPECCABLE_CORE",
            impeccable / "skill/reference/new-work.md": "IMPECCABLE_NEW_WORK",
            impeccable / "skill/reference/craft-floor.md": "IMPECCABLE_CRAFT_FLOOR",
            impeccable / "skill/reference/operate.md": "IMPECCABLE_OPERATE",
            impeccable / "skill/reference/polish.md": "IMPECCABLE_POLISH",
            impeccable / "skill/reference/audit.md": "IMPECCABLE_AUDIT",
            impeccable / "skill/reference/overdrive.md": "IMPECCABLE_OVERDRIVE",
            impeccable / "skill/reference/animate.md": "IMPECCABLE_ANIMATE",
        }
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

        (impeccable / "package.json").write_text(
            json.dumps({"name": "impeccable", "version": "3.5.0"})
        )

        (run / "input").mkdir(parents=True)
        (run / "work").mkdir()
        (run / "output").mkdir()
        (run / "evidence").mkdir()
        (run / "input/brief.md").write_text("BRIEF_SENTINEL")
        (run / "input/acceptance.json").write_text(
            json.dumps(
                {
                    "mustDeliver": ["A complete surface."],
                    "mustNot": ["External network access."],
                    "functionalChecks": [
                        {
                            "id": "local",
                            "action": "Open the page.",
                            "expected": "The page renders locally.",
                        }
                    ],
                    "evaluationFocus": ["clarity"],
                }
            )
        )
        (run / "input/fixture.json").write_text(
            json.dumps(
                {
                    "id": "fixture-a",
                    "version": 1,
                    "kind": fixture_kind,
                    "brief": "brief.md",
                    "acceptance": "acceptance.json",
                    "baseline": ["input/index.html"],
                    "viewports": ["1440x900", "390x844"],
                    "outputContract": {
                        "entrypoint": "index.html",
                        "mustRunWithoutBuildStep": True,
                        "externalNetworkRequired": False,
                    },
                }
            )
        )
        (run / "work/index.html").write_text("SOURCE_SENTINEL")
        (run / "run.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "runId": "run-001",
                    "status": status,
                    "fixture": {
                        "id": "fixture-a",
                        "version": 1,
                        "kind": fixture_kind,
                    },
                    "lane": {"id": lane},
                    "tool": {"name": "comparison-agent", "version": "1"},
                }
            )
        )
        return temporary, repo, impeccable, run

    def test_design_studio_director_packet_is_source_blind(self) -> None:
        temporary, repo, impeccable, run = self.make_environment()
        self.addCleanup(temporary.cleanup)

        packet = self.agent.build_director_packet(
            repo_root=repo,
            run_dir=run,
            design_studio_revision="design-sha",
        )
        serialized = json.dumps(packet)

        self.assertIn("DIRECTOR_GUIDANCE", serialized)
        self.assertIn("BRIEF_SENTINEL", serialized)
        self.assertNotIn("SOURCE_SENTINEL", serialized)
        self.assertNotIn("BUILDER_GUIDANCE", serialized)
        self.assertNotIn("IMPECCABLE_CORE", serialized)
        self.assertFalse(packet["boundary"]["canAccessSource"])
        self.assertEqual([], packet["boundary"]["sourcePaths"])
        self.assertEqual(
            ["skills/design-studio/agents/design-agent.md"],
            [item["path"] for item in packet["guidance"]["files"]],
        )

    def test_design_studio_builder_packet_gets_direction_and_source_only(self) -> None:
        temporary, repo, impeccable, run = self.make_environment()
        self.addCleanup(temporary.cleanup)

        packet = self.agent.build_design_studio_builder_packet(
            repo_root=repo,
            run_dir=run,
            selected_direction=direction("Assigned"),
            design_studio_revision="design-sha",
            mechanical_provider="fallback",
        )
        serialized = json.dumps(packet)

        self.assertIn("BUILDER_GUIDANCE", serialized)
        self.assertIn("SOURCE_SENTINEL", serialized)
        self.assertIn("Assigned", serialized)
        self.assertIn("BRIEF_SENTINEL", serialized)
        self.assertNotIn("DIRECTOR_GUIDANCE", serialized)
        self.assertNotIn("IMPECCABLE_CORE", serialized)
        self.assertTrue(packet["boundary"]["canAccessSource"])
        self.assertEqual(["index.html"], packet["boundary"]["sourcePaths"])
        self.assertEqual("fallback", packet["mechanicalProvider"])

    def test_enabled_lane_does_not_smuggle_impeccable_guidance_into_builder(self) -> None:
        temporary, repo, impeccable, run = self.make_environment(
            lane="design-studio-impeccable"
        )
        self.addCleanup(temporary.cleanup)

        packet = self.agent.build_design_studio_builder_packet(
            repo_root=repo,
            run_dir=run,
            selected_direction=direction("Assigned"),
            design_studio_revision="design-sha",
            mechanical_provider="impeccable",
        )
        serialized = json.dumps(packet)

        self.assertNotIn("IMPECCABLE_CORE", serialized)
        self.assertEqual("impeccable", packet["mechanicalProvider"])

    def test_impeccable_packet_uses_fixture_specific_pinned_guidance(self) -> None:
        temporary, repo, impeccable, run = self.make_environment(
            lane="impeccable-alone",
            fixture_kind="review-and-polish",
        )
        self.addCleanup(temporary.cleanup)

        packet = self.agent.build_impeccable_builder_packet(
            impeccable_root=impeccable,
            run_dir=run,
            impeccable_revision="impeccable-sha",
        )
        serialized = json.dumps(packet)

        self.assertIn("IMPECCABLE_CORE", serialized)
        self.assertIn("IMPECCABLE_POLISH", serialized)
        self.assertIn("IMPECCABLE_AUDIT", serialized)
        self.assertIn("IMPECCABLE_CRAFT_FLOOR", serialized)
        self.assertIn("SOURCE_SENTINEL", serialized)
        self.assertNotIn("DIRECTOR_GUIDANCE", serialized)
        self.assertEqual("3.5.0", packet["guidance"]["packageVersion"])
        self.assertEqual("impeccable-sha", packet["guidance"]["revision"])

    def test_direction_selection_is_deterministic_and_requires_three(self) -> None:
        directions = [direction("A"), direction("B"), direction("C")]

        first = self.agent.select_direction(directions, "fixture-a:v1")
        second = self.agent.select_direction(directions, "fixture-a:v1")

        self.assertEqual(first, second)
        self.assertIn(first["selectedIndex"], {0, 1, 2})
        self.assertEqual(directions[first["selectedIndex"]], first["direction"])
        with self.assertRaisesRegex(self.agent.AgentContractError, "exactly three"):
            self.agent.select_direction(directions[:2], "fixture-a:v1")

    def test_role_source_receipts_include_hashes(self) -> None:
        temporary, repo, impeccable, run = self.make_environment()
        self.addCleanup(temporary.cleanup)

        packet = self.agent.build_director_packet(
            repo_root=repo,
            run_dir=run,
            design_studio_revision="design-sha",
        )
        receipt = packet["guidance"]["files"][0]

        self.assertEqual(64, len(receipt["sha256"]))
        self.assertEqual(len("DIRECTOR_GUIDANCE".encode()), receipt["bytes"])

    def test_file_bundle_materialization_rejects_unsafe_paths_atomically(self) -> None:
        unsafe_paths = ["../escape.html", "/absolute.html", "nested\\escape.html", ".secret"]
        for unsafe in unsafe_paths:
            with self.subTest(path=unsafe), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / "output"
                output.mkdir()
                bundle = file_bundle()
                bundle["files"].append({"path": unsafe, "content": "bad"})

                with self.assertRaises(self.agent.AgentContractError):
                    self.agent.materialize_file_bundle(bundle, output)

                self.assertEqual([], list(output.iterdir()))

    def test_file_bundle_rejects_duplicates_missing_entrypoint_and_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "output"
            output.mkdir()
            duplicate = file_bundle()
            duplicate["files"].append({"path": "index.html", "content": "duplicate"})
            with self.assertRaisesRegex(self.agent.AgentContractError, "duplicate"):
                self.agent.materialize_file_bundle(duplicate, output)

            missing = file_bundle()
            missing["files"] = [{"path": "styles.css", "content": "body{}"}]
            with self.assertRaisesRegex(self.agent.AgentContractError, "index.html"):
                self.agent.materialize_file_bundle(missing, output)

            (output / "existing.txt").write_text("do not replace")
            with self.assertRaisesRegex(self.agent.AgentContractError, "must be empty"):
                self.agent.materialize_file_bundle(file_bundle(), output)
            self.assertEqual("do not replace", (output / "existing.txt").read_text())

    def test_file_bundle_rejects_external_network_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            output.mkdir()
            bundle = file_bundle(
                '<!doctype html><script src="https://cdn.example.test/app.js"></script>'
            )

            with self.assertRaisesRegex(self.agent.AgentContractError, "external network"):
                self.agent.materialize_file_bundle(bundle, output)

            self.assertEqual([], list(output.iterdir()))

    def test_file_bundle_enforces_total_size_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            output.mkdir()
            bundle = file_bundle("x" * (self.agent.MAX_TOTAL_OUTPUT_BYTES + 1))

            with self.assertRaisesRegex(self.agent.AgentContractError, "size limit"):
                self.agent.materialize_file_bundle(bundle, output)

    def test_structured_call_preserves_sanitized_receipts_and_usage(self) -> None:
        requester = FakeRequester(
            [
                completion(
                    file_bundle(),
                    usage={"prompt_tokens": 100, "completion_tokens": 50},
                )
            ]
        )
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary)
            result = self.agent.call_structured_role(
                role="builder",
                model="openai/gpt-4.1",
                token="secret-token",
                packet={"role": "builder", "instructions": "Build it."},
                schema=self.agent.file_bundle_schema(),
                evidence_dir=evidence,
                requester=requester,
            )

            self.assertEqual(file_bundle(), result["content"])
            self.assertEqual(
                {"prompt_tokens": 100, "completion_tokens": 50}, result["usage"]
            )
            self.assertTrue((evidence / "builder-request.json").is_file())
            self.assertTrue((evidence / "builder-response.json").is_file())
            saved = "\n".join(path.read_text() for path in evidence.glob("*.json"))
            self.assertNotIn("secret-token", saved)

    def test_run_generation_impeccable_alone_writes_output_and_report(self) -> None:
        temporary, repo, impeccable, run = self.make_environment(
            lane="impeccable-alone"
        )
        self.addCleanup(temporary.cleanup)
        requester = FakeRequester(
            [completion(file_bundle(), usage={"prompt_tokens": 10, "completion_tokens": 20})]
        )

        report = self.agent.run_generation(
            repo_root=repo,
            impeccable_root=impeccable,
            run_dir=run,
            lane_id="impeccable-alone",
            model="openai/gpt-4.1",
            token="secret-token",
            design_studio_revision="design-sha",
            impeccable_revision="impeccable-sha",
            requester=requester,
        )

        self.assertTrue((run / "output/index.html").is_file())
        self.assertEqual("generated", report["status"])
        self.assertEqual(["builder"], report["roles"])
        self.assertEqual("impeccable", report["mechanicalProvider"])
        self.assertTrue((run / "evidence/agent/generation-report.json").is_file())
        serialized_request = json.dumps(requester.calls[0]["payload"])
        self.assertIn("IMPECCABLE_CORE", serialized_request)
        self.assertIn("SOURCE_SENTINEL", serialized_request)

    def test_run_generation_design_studio_separates_director_and_builder(self) -> None:
        temporary, repo, impeccable, run = self.make_environment()
        self.addCleanup(temporary.cleanup)
        requester = FakeRequester(
            [
                completion({"directions": [direction("A"), direction("B"), direction("C")]}),
                completion(file_bundle()),
            ]
        )

        report = self.agent.run_generation(
            repo_root=repo,
            impeccable_root=impeccable,
            run_dir=run,
            lane_id="design-studio-current",
            model="openai/gpt-4.1",
            token="secret-token",
            design_studio_revision="design-sha",
            impeccable_revision="impeccable-sha",
            requester=requester,
        )

        self.assertEqual(["director", "builder"], report["roles"])
        director_request = json.dumps(requester.calls[0]["payload"])
        builder_request = json.dumps(requester.calls[1]["payload"])
        self.assertIn("BRIEF_SENTINEL", director_request)
        self.assertNotIn("SOURCE_SENTINEL", director_request)
        self.assertIn("SOURCE_SENTINEL", builder_request)
        self.assertNotIn("DIRECTOR_GUIDANCE", builder_request)
        self.assertTrue((run / "evidence/agent/selected-direction.json").is_file())

    def test_run_generation_rejects_lane_and_state_mismatch(self) -> None:
        temporary, repo, impeccable, run = self.make_environment()
        self.addCleanup(temporary.cleanup)

        with self.assertRaisesRegex(self.agent.AgentContractError, "lane mismatch"):
            self.agent.run_generation(
                repo_root=repo,
                impeccable_root=impeccable,
                run_dir=run,
                lane_id="impeccable-alone",
                model="openai/gpt-4.1",
                token="secret-token",
                design_studio_revision="design-sha",
                impeccable_revision="impeccable-sha",
                requester=FakeRequester([]),
            )

        (run / "run.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "runId": "run-001",
                    "status": "complete",
                    "fixture": {"id": "fixture-a", "version": 1},
                    "lane": {"id": "design-studio-current"},
                }
            )
        )
        with self.assertRaisesRegex(self.agent.AgentContractError, "prepared"):
            self.agent.run_generation(
                repo_root=repo,
                impeccable_root=impeccable,
                run_dir=run,
                lane_id="design-studio-current",
                model="openai/gpt-4.1",
                token="secret-token",
                design_studio_revision="design-sha",
                impeccable_revision="impeccable-sha",
                requester=FakeRequester([]),
            )


if __name__ == "__main__":
    unittest.main()
