from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "run_boundary_benchmark_matrix.py"


def load_matrix_runner():
    spec = importlib.util.spec_from_file_location(
        "run_boundary_benchmark_matrix_test",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load matrix runner from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def lane_tools() -> dict[str, dict[str, str]]:
    return {
        "impeccable-alone": {
            "name": "impeccable",
            "version": "0.1.0-test",
            "source": "pbakaus/impeccable@test-revision",
        },
        "design-studio-current": {
            "name": "design-studio",
            "version": "1.5.0-test",
            "source": "George-RD/design-studio@test-revision",
        },
        "design-studio-impeccable": {
            "name": "design-studio+impeccable",
            "version": "1.5.0-test+0.1.0-test",
            "source": "George-RD/design-studio@test-revision + pbakaus/impeccable@test-revision",
        },
    }


class BoundaryBenchmarkMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = load_matrix_runner()

    def make_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        shutil.copytree(REPO_ROOT / "benchmarks", root / "benchmarks")
        scripts = root / "scripts"
        scripts.mkdir()
        for name in (
            "run_boundary_benchmark.py",
            "run_boundary_benchmark_matrix.py",
            "validate_benchmark_fixtures.py",
        ):
            shutil.copy2(REPO_ROOT / "scripts" / name, scripts / name)
        output_root = root / "harness-output" / "benchmarks" / "milestone-0"
        return temporary, root, output_root

    def test_prepare_matrix_creates_every_fixture_lane_pair_with_shared_provenance(self):
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)

        matrix_path = self.matrix.prepare_matrix(
            repo_root=root,
            output_root=output_root,
            matrix_id="m0-001",
            lane_tools=lane_tools(),
        )

        receipt = json.loads(matrix_path.read_text())
        manifest = json.loads(
            (root / "benchmarks" / "milestone-0" / "manifest.json").read_text()
        )
        expected_pairs = {
            (fixture["id"], lane["id"])
            for fixture in manifest["fixtures"]
            for lane in manifest["comparisonLanes"]
        }
        actual_pairs = {
            (entry["fixture"]["id"], entry["lane"]["id"])
            for entry in receipt["runs"]
        }

        self.assertEqual(expected_pairs, actual_pairs)
        self.assertEqual(12, len(receipt["runs"]))
        self.assertEqual("prepared", receipt["status"])
        self.assertEqual("m0-001", receipt["matrixId"])
        self.assertNotIn("repositoryRoot", receipt)
        self.assertNotIn("outputRoot", receipt)
        self.assertEqual(set(lane_tools()), set(receipt["tools"]))
        shared_suite = receipt["suite"]
        shared_harness = receipt["harness"]
        for entry in receipt["runs"]:
            run_dir = output_root / entry["runDir"]
            run = json.loads((run_dir / "run.json").read_text())
            self.assertEqual(shared_suite, run["suite"])
            self.assertEqual(shared_harness["laneHarness"], run["harness"])
            self.assertEqual(entry["runId"], run["runId"])
            self.assertEqual(entry["lane"]["id"], run["lane"]["id"])
            self.assertEqual(receipt["tools"][entry["lane"]["id"]], run["tool"])

        summary = self.matrix.validate_matrix(matrix_path)
        self.assertEqual("prepared", summary["status"])
        self.assertEqual({"prepared": 12}, summary["runStatuses"])

    def test_prepare_matrix_rejects_incomplete_or_extra_lane_tools_before_writing(self):
        for mutation in ("missing", "extra"):
            with self.subTest(mutation=mutation):
                temporary, root, output_root = self.make_repo()
                self.addCleanup(temporary.cleanup)
                tools = lane_tools()
                if mutation == "missing":
                    tools.pop("design-studio-current")
                else:
                    tools["unknown-lane"] = {
                        "name": "unknown",
                        "version": "1",
                        "source": "local",
                    }

                with self.assertRaisesRegex(
                    self.matrix.ContractError,
                    "lane tool configuration",
                ):
                    self.matrix.prepare_matrix(
                        repo_root=root,
                        output_root=output_root,
                        matrix_id="m0-invalid",
                        lane_tools=tools,
                    )

                self.assertFalse(output_root.exists())

    def test_prepare_matrix_preflights_all_run_collisions_without_partial_creation(self):
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        collision = (
            output_root
            / "review-polish"
            / "design-studio-impeccable"
            / "m0-002-review-polish-design-studio-impeccable"
        )
        collision.mkdir(parents=True)
        sentinel = collision / "sentinel.txt"
        sentinel.write_text("keep")

        with self.assertRaisesRegex(self.matrix.ContractError, "already exists"):
            self.matrix.prepare_matrix(
                repo_root=root,
                output_root=output_root,
                matrix_id="m0-002",
                lane_tools=lane_tools(),
            )

        self.assertEqual("keep", sentinel.read_text())
        self.assertFalse((output_root / "matrices" / "m0-002").exists())
        created_run_manifests = list(output_root.glob("*/*/m0-002-*/run.json"))
        self.assertEqual([], created_run_manifests)

    def test_prepare_matrix_rolls_back_runs_when_later_preparation_fails(self):
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        original = self.matrix.runner.prepare_run
        calls = 0

        def fail_third(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise self.matrix.runner.ContractError("synthetic preparation failure")
            return original(**kwargs)

        with mock.patch.object(self.matrix.runner, "prepare_run", side_effect=fail_third):
            with self.assertRaisesRegex(self.matrix.ContractError, "synthetic"):
                self.matrix.prepare_matrix(
                    repo_root=root,
                    output_root=output_root,
                    matrix_id="m0-003",
                    lane_tools=lane_tools(),
                )

        self.assertEqual([], list(output_root.glob("*/*/m0-003-*/run.json")))
        self.assertFalse((output_root / "matrices" / "m0-003").exists())

    def test_validate_matrix_rejects_missing_or_retargeted_runs(self):
        for mutation in ("missing", "retargeted"):
            with self.subTest(mutation=mutation):
                temporary, root, output_root = self.make_repo()
                self.addCleanup(temporary.cleanup)
                matrix_path = self.matrix.prepare_matrix(
                    repo_root=root,
                    output_root=output_root,
                    matrix_id=f"m0-{mutation}",
                    lane_tools=lane_tools(),
                )
                receipt = json.loads(matrix_path.read_text())
                run_dir = output_root / receipt["runs"][0]["runDir"]
                if mutation == "missing":
                    shutil.rmtree(run_dir)
                else:
                    run = json.loads((run_dir / "run.json").read_text())
                    run["lane"]["id"] = "design-studio-current"
                    (run_dir / "run.json").write_text(json.dumps(run, indent=2))

                with self.assertRaisesRegex(
                    self.matrix.ContractError,
                    "missing|does not match",
                ):
                    self.matrix.validate_matrix(matrix_path)


    def test_example_lane_tools_cover_every_lane_with_exact_revision_placeholders(self):
        tools = self.matrix.load_lane_tools(
            REPO_ROOT / "benchmarks" / "milestone-0" / "lane-tools.example.json"
        )

        self.assertEqual(set(lane_tools()), set(tools))
        for lane_id, tool in tools.items():
            with self.subTest(lane=lane_id):
                self.assertEqual({"name", "version", "source"}, set(tool))
                self.assertIn("<", tool["version"])
                self.assertIn("@<exact-revision>", tool["source"])

    def test_matrix_id_must_keep_generated_run_ids_within_run_contract(self):
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)

        with self.assertRaisesRegex(self.matrix.ContractError, "matrix ID|run ID"):
            self.matrix.prepare_matrix(
                repo_root=root,
                output_root=output_root,
                matrix_id="x" * 64,
                lane_tools=lane_tools(),
            )

        self.assertFalse(output_root.exists())


if __name__ == "__main__":
    unittest.main()
