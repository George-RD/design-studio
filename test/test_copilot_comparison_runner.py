from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_copilot_comparison.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_copilot_comparison", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load comparison runner from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CopilotComparisonRunnerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def make_run(self, lane: str = "design-studio-current"):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        run = root / "run"
        repo = root / "repo"
        impeccable = root / "impeccable"
        for directory in (run / "input", run / "work", run / "output", run / "evidence"):
            directory.mkdir(parents=True)
        (run / "input" / "brief.md").write_text("PUBLIC_BRIEF", encoding="utf-8")
        (run / "input" / "acceptance.json").write_text(
            json.dumps({"mustDeliver": ["A usable local page"]}), encoding="utf-8"
        )
        (run / "input" / "fixture.json").write_text(
            json.dumps(
                {
                    "id": "fixture-a",
                    "version": 1,
                    "kind": "new-marketing-surface",
                    "brief": "brief.md",
                    "acceptance": "acceptance.json",
                    "outputContract": {"entrypoint": "index.html"},
                }
            ),
            encoding="utf-8",
        )
        (run / "work" / "index.html").write_text("PRIVATE_SOURCE", encoding="utf-8")
        (run / "run.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "runId": "m0-fixture-a-current",
                    "status": "prepared",
                    "fixture": {"id": "fixture-a", "version": 1},
                    "lane": {"id": lane},
                    "tool": {"name": "design-studio", "version": "1.5.0", "source": "sha"},
                }
            ),
            encoding="utf-8",
        )
        for path, text in {
            repo / "skills/design-studio/agents/design-agent.md": "DIRECTOR_GUIDANCE",
            repo / "skills/design-studio/references/generation.md": "BUILDER_GUIDANCE",
            impeccable / "skill/SKILL.src.md": "IMPECCABLE_CORE",
            impeccable / "skill/reference/new-work.md": "IMPECCABLE_NEW",
            impeccable / "skill/reference/craft-floor.md": "IMPECCABLE_CRAFT",
        }.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (impeccable / "package.json").write_text(
            json.dumps({"name": "impeccable", "version": "3.5.0"}), encoding="utf-8"
        )
        return temporary, repo, impeccable, run

    @staticmethod
    def directions():
        return [
            {"id": f"direction-{index}", "name": name, "concept": name}
            for index, name in enumerate(("A", "B", "C"), start=1)
        ]

    @staticmethod
    def design_description() -> str:
        headings = (
            "THESIS",
            "FIRST VIEWPORT",
            "VISITOR PATH",
            "VISUAL WORLD",
            "TYPOGRAPHY",
            "COLOUR",
            "SPATIAL RHYTHM",
            "MOTION",
            "INTERACTION STATES",
            "RESPONSIVE BEHAVIOUR",
            "SIGNATURE MOMENT",
            "ANTI-GOALS",
        )
        return "\n\n".join(
            f"## {heading}\nSpecific {heading.lower()} contract." for heading in headings
        )

    @staticmethod
    def local_index(body: str = "<main>ok</main>") -> str:
        return f"""<!doctype html>
<html>
<head>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; connect-src 'none'; form-action 'none'; frame-src 'none'; object-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; media-src 'self' data:">
</head>
<body>{body}</body>
</html>"""

    def test_director_is_source_blind_and_assignment_is_precommitted(self) -> None:
        temporary, repo, _, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        packet = self.runner.build_director_packet(repo, run, "design-sha")
        serialized = json.dumps(packet)
        self.assertIn("PUBLIC_BRIEF", serialized)
        self.assertIn("DIRECTOR_GUIDANCE", serialized)
        for forbidden in ("PRIVATE_SOURCE", "BUILDER_GUIDANCE", "assignedIndex", "seedDigest"):
            self.assertNotIn(forbidden, serialized)
        assignment = json.loads(
            (run / "evidence" / "direction-assignment.json").read_text(encoding="utf-8")
        )
        self.assertIn(assignment["assignedIndex"], (1, 2, 3))
        self.assertEqual("m0-fixture-a-current", assignment["runId"])
        self.assertEqual(1, assignment["iteration"])

    def test_selection_uses_precommitted_assignment_and_rejects_tampering(self) -> None:
        temporary, repo, _, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        self.runner.build_director_packet(repo, run, "design-sha")
        selection = self.runner.select_direction(self.directions(), run)
        self.assertEqual(
            f"direction-{selection['assignedIndex']}", selection["direction"]["id"]
        )
        self.assertEqual(selection, self.runner.select_direction(self.directions(), run))
        with self.assertRaises(TypeError):
            self.runner.select_direction(self.directions(), "caller-controlled-seed")

        assignment_path = run / "evidence" / "direction-assignment.json"
        assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
        assignment["assignedIndex"] = 1 if assignment["assignedIndex"] != 1 else 2
        assignment_path.write_text(json.dumps(assignment), encoding="utf-8")
        with self.assertRaises(self.runner.ContractError):
            self.runner.select_direction(self.directions(), run)

    def test_immutable_input_paths_and_fixture_identity_are_enforced(self) -> None:
        temporary, repo, _, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        fixture_path = run / "input" / "fixture.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        fixture["brief"] = "../work/index.html"
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        with self.assertRaises(self.runner.ContractError):
            self.runner.build_director_packet(repo, run, "design-sha")

        temporary_two, repo_two, _, run_two = self.make_run()
        self.addCleanup(temporary_two.cleanup)
        fixture_path = run_two / "input" / "fixture.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        fixture["version"] = 2
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        with self.assertRaises(self.runner.ContractError):
            self.runner.build_director_packet(repo_two, run_two, "design-sha")

    def test_lane_contract_binds_workflow_and_mechanical_provider(self) -> None:
        cases = {
            "design-studio-current": ("design-studio", "fallback"),
            "design-studio-impeccable": ("design-studio", "impeccable"),
            "impeccable-alone": ("impeccable", "impeccable"),
        }
        for lane, expected in cases.items():
            with self.subTest(lane=lane):
                temporary, _, _, run = self.make_run(lane)
                self.addCleanup(temporary.cleanup)
                contract = self.runner.resolve_lane_contract(run)
                self.assertEqual((contract["workflow"], contract["mechanicalProvider"]), expected)

    def test_direct_pass_expands_only_precommitted_candidate_without_source(self) -> None:
        temporary, repo, _, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        self.runner.build_director_packet(repo, run, "design-sha")
        selection = self.runner.select_direction(self.directions(), run)
        packet = self.runner.build_direct_packet(
            repo, run, selection["direction"], "design-sha"
        )
        serialized = json.dumps(packet)
        self.assertIn(selection["direction"]["name"], serialized)
        self.assertIn("DIRECTOR_GUIDANCE", serialized)
        for forbidden in ("PRIVATE_SOURCE", "assignedIndex", "seedDigest"):
            self.assertNotIn(forbidden, serialized)
        self.assertIn("design-description.md", packet["instructions"])

        wrong = self.directions()[(selection["assignedIndex"]) % 3]
        with self.assertRaises(self.runner.ContractError):
            self.runner.build_direct_packet(repo, run, wrong, "design-sha")

    def test_builder_receives_expanded_contract_not_raw_candidate(self) -> None:
        temporary, repo, _, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        description = self.design_description()
        packet = self.runner.build_builder_packet(
            repo, run, description, "design-sha", "fallback"
        )
        serialized = json.dumps(packet)
        self.assertIn("PRIVATE_SOURCE", serialized)
        self.assertIn("BUILDER_GUIDANCE", serialized)
        self.assertEqual(description, packet["designDescription"])
        self.assertNotIn("selectedDirection", packet)
        self.assertEqual("design-studio-current", packet["lane"]["id"])

        for invalid in (self.directions()[0], "## THESIS\nOnly a mood"):
            with self.subTest(invalid=type(invalid).__name__):
                with self.assertRaises(self.runner.ContractError):
                    self.runner.build_builder_packet(
                        repo, run, invalid, "design-sha", "fallback"
                    )
        with self.assertRaises(self.runner.ContractError):
            self.runner.build_builder_packet(
                repo, run, description, "design-sha", "impeccable"
            )

    def test_packet_builders_reject_wrong_lane(self) -> None:
        temporary, repo, impeccable, run = self.make_run("impeccable-alone")
        self.addCleanup(temporary.cleanup)
        for builder in (
            lambda: self.runner.build_director_packet(repo, run, "design-sha"),
            lambda: self.runner.build_direct_packet(
                repo, run, self.directions()[0], "design-sha"
            ),
            lambda: self.runner.build_builder_packet(
                repo, run, self.design_description(), "design-sha", "impeccable"
            ),
        ):
            with self.assertRaises(self.runner.ContractError):
                builder()

        temporary_two, _, impeccable_two, run_two = self.make_run("design-studio-current")
        self.addCleanup(temporary_two.cleanup)
        with self.assertRaises(self.runner.ContractError):
            self.runner.build_impeccable_packet(impeccable_two, run_two, "impeccable-sha")

    def test_enabled_lane_keeps_impeccable_guidance_out_of_builder(self) -> None:
        temporary, repo, _, run = self.make_run("design-studio-impeccable")
        self.addCleanup(temporary.cleanup)
        packet = self.runner.build_builder_packet(
            repo, run, self.design_description(), "design-sha", "impeccable"
        )
        self.assertNotIn("IMPECCABLE_CORE", json.dumps(packet))
        self.assertEqual("impeccable", packet["mechanicalProvider"])

    def test_impeccable_lane_uses_pinned_upstream_guidance(self) -> None:
        temporary, _, impeccable, run = self.make_run("impeccable-alone")
        self.addCleanup(temporary.cleanup)
        packet = self.runner.build_impeccable_packet(impeccable, run, "impeccable-sha")
        serialized = json.dumps(packet)
        self.assertIn("IMPECCABLE_CORE", serialized)
        self.assertIn("IMPECCABLE_NEW", serialized)
        self.assertIn("PRIVATE_SOURCE", serialized)
        self.assertNotIn("DIRECTOR_GUIDANCE", serialized)
        self.assertEqual("3.5.0", packet["guidance"]["packageVersion"])

    def test_bundle_rejects_encoded_external_references_and_dynamic_network_apis(self) -> None:
        encoded_external = self.local_index(
            '<script src="https:&#x2f;&#x2f;example.com/x.js"></script>'
        )
        dynamic_fetch = self.local_index(
            '<script>fetch("https:" + "/" + "/example.com/data")</script>'
        )
        for content in (encoded_external, dynamic_fetch):
            with self.subTest(content=content[-80:]):
                with self.assertRaises(self.runner.ContractError):
                    self.runner.validate_bundle(
                        {"files": [{"path": "index.html", "content": content}]}
                    )

    def test_bundle_requires_durable_csp_index_and_safe_paths(self) -> None:
        invalid_bundles = (
            {"files": [{"path": "../escape.html", "content": "x"}]},
            {"files": [{"path": "styles.css", "content": "body{}"}]},
            {"files": [{"path": "index.html", "content": "<!doctype html><main>ok</main>"}]},
        )
        for bundle in invalid_bundles:
            with self.subTest(bundle=bundle):
                with self.assertRaises(self.runner.ContractError):
                    self.runner.validate_bundle(bundle)

        valid = self.runner.validate_bundle(
            {"files": [{"path": "index.html", "content": self.local_index()}]}
        )
        self.assertEqual(["index.html"], [item["path"] for item in valid])


if __name__ == "__main__":
    unittest.main()
