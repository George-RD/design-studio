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

    def test_director_packet_is_source_blind(self) -> None:
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        packet = self.runner.build_director_packet(repo, run, "design-sha")
        serialized = json.dumps(packet)
        self.assertIn("PUBLIC_BRIEF", serialized)
        self.assertIn("DIRECTOR_GUIDANCE", serialized)
        self.assertNotIn("PRIVATE_SOURCE", serialized)
        self.assertNotIn("BUILDER_GUIDANCE", serialized)
        self.assertNotIn("IMPECCABLE_CORE", serialized)

    def test_builder_packet_receives_selected_direction_and_source(self) -> None:
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        packet = self.runner.build_builder_packet(
            repo,
            run,
            {"concept": "Assigned", "palette": "Stone", "layout": "Editorial", "interaction": "Quiet"},
            "design-sha",
            "fallback",
        )
        serialized = json.dumps(packet)
        self.assertIn("PRIVATE_SOURCE", serialized)
        self.assertIn("BUILDER_GUIDANCE", serialized)
        self.assertIn("Assigned", serialized)
        self.assertNotIn("DIRECTOR_GUIDANCE", serialized)
        self.assertNotIn("IMPECCABLE_CORE", serialized)
        self.assertEqual("fallback", packet["mechanicalProvider"])

    def test_enabled_design_studio_lane_does_not_receive_impeccable_guidance(self) -> None:
        temporary, repo, impeccable, run = self.make_run("design-studio-impeccable")
        self.addCleanup(temporary.cleanup)
        packet = self.runner.build_builder_packet(
            repo,
            run,
            {"concept": "Assigned", "palette": "Stone", "layout": "Editorial", "interaction": "Quiet"},
            "design-sha",
            "impeccable",
        )
        self.assertNotIn("IMPECCABLE_CORE", json.dumps(packet))
        self.assertEqual("impeccable", packet["mechanicalProvider"])

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

    def test_direction_selection_is_deterministic(self) -> None:
        directions = [
            {"concept": "A", "palette": "A", "layout": "A", "interaction": "A"},
            {"concept": "B", "palette": "B", "layout": "B", "interaction": "B"},
            {"concept": "C", "palette": "C", "layout": "C", "interaction": "C"},
        ]
        first = self.runner.select_direction(directions, "fixture-a:run-1")
        second = self.runner.select_direction(directions, "fixture-a:run-1")
        self.assertEqual(first, second)
        self.assertIn(first["selectedIndex"], (0, 1, 2))

    def test_output_bundle_rejects_escape_and_external_network(self) -> None:
        with self.assertRaises(self.runner.ContractError):
            self.runner.validate_bundle({"files": [{"path": "../escape.html", "content": "x"}]})
        with self.assertRaises(self.runner.ContractError):
            self.runner.validate_bundle(
                {"files": [{"path": "index.html", "content": "<script src='https://example.com/x.js'></script>"}]}
            )

    def test_output_bundle_requires_index_and_is_bounded(self) -> None:
        with self.assertRaises(self.runner.ContractError):
            self.runner.validate_bundle({"files": [{"path": "styles.css", "content": "body{}"}]})
        valid = self.runner.validate_bundle(
            {"files": [{"path": "index.html", "content": "<!doctype html><title>ok</title>"}]}
        )
        self.assertEqual(["index.html"], [item["path"] for item in valid])


if __name__ == "__main__":
    unittest.main()
