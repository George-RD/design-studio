from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "run_boundary_benchmark_preference.py"


def load_preference_runner():
    spec = importlib.util.spec_from_file_location(
        "run_boundary_benchmark_preference_metadata_test",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load preference runner from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class BoundaryBenchmarkPreferenceMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preference = load_preference_runner()

    def test_completed_run_may_contain_richer_fixture_and_lane_metadata_than_matrix_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary) / "harness-output" / "benchmarks" / "milestone-0"
            run_id = "m0-001-marketing-surface-impeccable-alone"
            run_dir = output_root / "marketing-surface" / "impeccable-alone" / run_id
            (run_dir / "input").mkdir(parents=True)
            (run_dir / "output").mkdir()
            (run_dir / "evidence").mkdir()
            (run_dir / "input" / "brief.md").write_text("Frozen brief.\n")
            (run_dir / "input" / "fixture.json").write_text(
                json.dumps({"acceptance": "acceptance.json"})
            )
            (run_dir / "input" / "acceptance.json").write_text(
                json.dumps({"functionalChecks": []})
            )
            (run_dir / "output" / "index.html").write_text("<!doctype html><title>Output</title>")

            suite = {"id": "suite", "version": 1}
            run_fixture = {
                "id": "marketing-surface",
                "version": 1,
                "kind": "new-surface",
                "title": "Marketing surface",
            }
            run_lane = {
                "id": "impeccable-alone",
                "purpose": "Exercise Impeccable without Design Studio orchestration.",
            }
            tool = {"name": "impeccable", "version": "3.5.0", "source": "pinned"}
            run = {
                "schemaVersion": 1,
                "runId": run_id,
                "status": "complete",
                "suite": suite,
                "fixture": run_fixture,
                "lane": run_lane,
                "tool": tool,
                "result": "evidence/result.json",
            }
            (run_dir / "run.json").write_text(json.dumps(run))
            result = {
                "runId": run_id,
                "suite": suite,
                "fixture": run_fixture,
                "lane": run_lane,
                "tool": tool,
                "output": {
                    "entrypoint": "index.html",
                    "treeManifest": {
                        "algorithm": "sha256",
                        "files": self.preference.runner.tree_manifest(run_dir / "output"),
                    },
                },
            }
            (run_dir / "evidence" / "result.json").write_text(json.dumps(result))
            matrix_entry = {
                "fixture": {"id": "marketing-surface", "version": 1},
                "lane": {"id": "impeccable-alone"},
                "runId": run_id,
                "runDir": run_dir.relative_to(output_root).as_posix(),
            }

            with mock.patch.object(self.preference.runner, "validate_run", return_value=None):
                loaded = self.preference._load_completed_entry(
                    output_root=output_root,
                    matrix_suite=suite,
                    entry=matrix_entry,
                )

            self.assertEqual(run_fixture, loaded["run"]["fixture"])
            self.assertEqual(run_lane, loaded["run"]["lane"])


if __name__ == "__main__":
    unittest.main()
