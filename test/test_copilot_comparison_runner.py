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
        (run / "input").mkdir(parents=True)
        (run / "work").mkdir()
        (run / "output").mkdir()
        (run / "evidence").mkdir()
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

    def directions(self):
        return [
            {
                "id": "direction-1",
                "name": "A",
                "concept": "A",
                "palette": "A",
                "layout": "A",
                "interaction": "A",
            },
            {
                "id": "direction-2",
                "name": "B",
                "concept": "B",
                "palette": "B",
                "layout": "B",
                "interaction": "B",
            },
            {
                "id": "direction-3",
                "name": "C",
                "concept": "C",
                "palette": "C",
                "layout": "C",
                "interaction": "C",
            },
        ]

    def design_description(self) -> str:
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
        return "\n\n".join(f"## {heading}\nSpecific {heading.lower()} contract." for heading in headings)

    def local_index(self, body: str = "<main>ok</main>") -> str:
        return (
            "<!doctype html><html><head>"
            '<meta http-equiv="Content-Security-Policy" '
            'content="default-src \'none\'; base-uri \'none\'; connect-src \'none\'; '
            'form-action \'none\'; frame-src \'none\'; object-src \'none\'; '
            "script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; font-src 'self' data:; media-src 'self' data:">"
            f"</head><body>{body}</body></html>"
        )

    def test_director_packet_is_source_blind_and_precommits_assignment(self) -> None:
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        packet = self.runner.build_director_packet(repo, run, "design-sha")
        serialized = json.dumps(packet)
        self.assertIn("PUBLIC_BRIEF", serialized)
        self.assertIn("DIRECTOR_GUIDANCE", serialized)
        self.assertNotIn("PRIVATE_SOURCE", serialized)
        self.assertNotIn("BUILDER_GUIDANCE", serialized)
        self.assertNotIn("IMPECCABLE_CORE", serialized)
        self.assertNotIn("assignedIndex", serialized)
        self.assertNotIn("seedDigest", serialized)

        assignment_path = run / "evidence" / "direction-assignment.json"
        self.assertTrue(assignment_path.is_file())
        assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
        self.assertIn(assignment["assignedIndex"], (1, 2, 3))
        self.assertEqual("m0-fixture-a-current", assignment["runId"])
        self.assertEqual(1, assignment["iteration"])

    def test_direction_selection_uses_only_the_precommitted_assignment(self) -> None:
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        self.runner.build_director_packet(repo, run, "design-sha")
        first = self.runner.select_direction(self.directions(), run)
        second = self.runner.select_direction(self.directions(), run)
        self.assertEqual(first, second)
        self.assertEqual(
            f"direction-{first['assignedIndex']}",
            first["direction"]["id"],
        )
        with self.assertRaises(TypeError):
            self.runner.select_direction(self.directions(), "caller-controlled-seed")

    def test_tampered_direction_assignment_is_rejected(self) -> None:
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        self.runner.build_director_packet(repo, run, "design-sha")
        assignment_path = run / "evidence" / "direction-assignment.json"
        assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
        assignment["assignedIndex"] = 1 if assignment["assignedIndex"] != 1 else 2
        assignment_path.write_text(json.dumps(assignment), encoding="utf-8")
        with self.assertRaises(self.runner.ContractError):
            self.runner.select_direction(self.directions(), run)

    def test_fixture_paths_cannot_escape_the_immutable_input_tree(self) -> None:
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        fixture_path = run / "input" / "fixture.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        fixture["brief"] = "../work/index.html"
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        with self.assertRaises(self.runner.ContractError):
            self.runner.build_director_packet(repo, run, "design-sha")

    def test_run_and_fixture_identity_must_match(self) -> None:
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        fixture_path = run / "input" / "fixture.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        fixture["version"] = 2
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        with self.assertRaises(self.runner.ContractError):
            self.runner.build_director_packet(repo, run, "design-sha")

    def test_lane_contract_binds_workflow_and_mechanical_provider(self) -> None:
        cases = {
            "design-studio-current": ("design-studio", "fallback"),
            "design-studio-impeccable": ("design-studio", "impeccable"),
            "impeccable-alone": ("impeccable", "impeccable"),
        }
        for lane, expected in cases.items():
            with self.subTest(lane=lane):
                temporary, repo, impeccable, run = self.make_run(lane)
                self.addCleanup(temporary.cleanup)
                contract = self.runner.resolve_lane_contract(run)
                self.assertEqual(lane, contract["id"])
                self.assertEqual(expected[0], contract["workflow"])
                self.assertEqual(expected[1], contract["mechanicalProvider"])

    def test_packet_builders_reject_the_wrong_lane(self) -> None:
        temporary, repo, impeccable, run = self.make_run("impeccable-alone")
        self.addCleanup(temporary.cleanup)
        with self.assertRaises(self.runner.ContractError):
            self.runner.build_director_packet(repo, run, "design-sha")
        with self.assertRaises(self.runner.ContractError):
            self.runner.build_direct_packet(repo, run, self.directions()[0], "design-sha")
        with self.assertRaises(self.runner.ContractError):
            self.runner.build_builder_packet(
                repo,
                run,
                self.design_description(),
                "design-sha",
                "impeccable",
            )

        temporary_two, repo_two, impeccable_two, run_two = self.make_run("design-studio-current")
        self.addCleanup(temporary_two.cleanup)
        with self.assertRaises(self.runner.ContractError):
            self.runner.build_impeccable_packet(impeccable_two, run_two, "impeccable-sha")

    def test_direct_packet_expands_selection_without_source_or_assignment(self) -> None:
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        self.runner.build_director_packet(repo, run, "design-sha")
        selection = self.runner.select_direction(self.directions(), run)
        packet = self.runner.build_direct_packet(
            repo,
            run,
            selection["direction"],
            "design-sha",
        )
        serialized = json.dumps(packet)
        self.assertIn(selection["direction"]["name"], serialized)
        self.assertIn("DIRECTOR_GUIDANCE", serialized)
        self.assertNotIn("PRIVATE_SOURCE", serialized)
        self.assertNotIn("assignedIndex", serialized)
        self.assertNotIn("seedDigest", serialized)
        self.assertIn("design-description.md", packet["instructions"])

    def test_builder_packet_receives_expanded_design_contract_and_source(self) -> None:
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        description = self.design_description()
        packet = self.runner.build_builder_packet(
            repo,
            run,
            description,
            "design-sha",
            "fallback",
        )
        serialized = json.dumps(packet)
        self.assertIn("PRIVATE_SOURCE", serialized)
        self.assertIn("BUILDER_GUIDANCE", serialized)
        self.assertIn("THESIS", serialized)
        self.assertNotIn("selectedDirection", packet)
        self.assertNotIn("DIRECTOR_GUIDANCE", serialized)
        self.assertNotIn("IMPECCABLE_CORE", serialized)
        self.assertEqual(description, packet["designDescription"])
        self.assertEqual("fallback", packet["mechanicalProvider"])
        self.assertEqual("design-studio-current", packet["lane"]["id"])

    def test_builder_rejects_raw_candidate_or_incomplete_direct_contract(self) -> None:
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        for invalid in (self.directions()[0], "## THESIS\nOnly a mood"):
            with self.subTest(invalid=type(invalid).__name__):
                with self.assertRaises(self.runner.ContractError):
                    self.runner.build_builder_packet(
                        repo,
                        run,
                        invalid,
                        "design-sha",
                        "fallback",
                    )

    def test_builder_rejects_a_provider_that_disagrees_with_the_lane(self) -> None:
        temporary, repo, impeccable, run = self.make_run("design-studio-current")
        self.addCleanup(temporary.cleanup)
        with self.assertRaises(self.runner.ContractError):
            self.runner.build_builder_packet(
                repo,
                run,
                self.design_description(),
                "design-sha",
                "impeccable",
            )

    def test_enabled_design_studio_lane_does_not_receive_impeccable_guidance(self) -> None:
        temporary, repo, impeccable, run = self.make_run("design-studio-impeccable")
        self.addCleanup(temporary.cleanup)
        packet = self.runner.build_builder_packet(
            repo,
            run,
            self.design_description(),
            "design-sha",
            "impeccable",
        )
        self.assertNotIn("IMPECCABLE_CORE", json.dumps(packet))
        self.assertEqual("impeccable", packet["mechanicalProvider"])
        self.assertEqual("design-studio-impeccable", packet["lane"]["id"])

    def test_impeccable_lane_uses_pinned_upstream_guidance(self) -> None:
        temporary, repo, impeccable, run = self.make_run("impeccable-alone")
        self.addCleanup(temporary.cleanup)
        packet = self.runner.build_impeccable_packet(impeccable, run, "impeccable-sha")
        serialized = json.dumps(packet)
        self.assertIn("IMPECCABLE_CORE", serialized)
        self.assertIn("IMPECCABLE_NEW", serialized)
        self.assertIn("PRIVATE_SOURCE", serialized)
        self.assertNotIn("DIRECTOR_GUIDANCE", serialized)
        self.assertEqual("3.5.0", packet["guidance"]["packageVersion"])
        self.assertEqual("impeccable-alone", packet["lane"]["id"])

    def test_output_bundle_rejects_escape_and_static_external_references(self) -> None:
        with self.assertRaises(self.runner.ContractError):
            self.runner.validate_bundle({"files": [{"path": "../escape.html", "content": "x"}]})
        encoded_external = self.local_index(
            '<script src="https:&#x2f;&#x2f;example.com/x.js"></script>'
        )
        with self.assertRaises(self.runner.ContractError):
            self.runner.validate_bundle(
                {"files": [{"path": "index.html", "content": encoded_external}]}
            )

    def test_output_bundle_rejects_network_apis_even_with_dynamic_urls(self) -> None:
        dynamic_fetch = self.local_index(
            '<script>fetch("https:" + "/" + "/example.com/data")</script>'
        )
        with self.assertRaises(self.runner.ContractError):
            self.runner.validate_bundle(
                {"files": [{"path": "index.html", "content": dynamic_fetch}]}
            )

    def test_output_bundle_requires_a_durable_no_network_policy(self) -> None:
        with self.assertRaises(self.runner.ContractError):
            self.runner.validate_bundle(
                {"files": [{"path": "index.html", "content": "<!doctype html><main>ok</main>"}]}
            )

    def test_output_bundle_requires_index_and_is_bounded(self) -> None:
        with self.assertRaises(self.runner.ContractError):
            self.runner.validate_bundle({"files": [{"path": "styles.css", "content": "body{}"}]})
        valid = self.runner.validate_bundle(
            {"files": [{"path": "index.html", "content": self.local_index()}]}
        )
        self.assertEqual(["index.html"], [item["path"] for item in valid])


if __name__ == "__main__":
    unittest.main()
