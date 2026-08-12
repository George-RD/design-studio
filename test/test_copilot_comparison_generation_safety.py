from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "run_copilot_comparison_matrix_generation.py"
DESIGN_REVISION = "d" * 40
IMPECCABLE_REVISION = "e" * 40
MODEL = "test-model"
RUN_TIMEOUT_SECONDS = 360


def load_generation_runner():
    spec = importlib.util.spec_from_file_location(
        "run_copilot_comparison_matrix_generation_safety_test", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load matrix generation runner from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CopilotComparisonGenerationSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generation = load_generation_runner()

    def make_repo(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        shutil.copytree(REPO_ROOT / "benchmarks", root / "benchmarks")
        shutil.copytree(REPO_ROOT / "skills", root / "skills")
        scripts = root / "scripts"
        scripts.mkdir()
        for name in (
            "run_boundary_benchmark.py",
            "run_boundary_benchmark_matrix.py",
            "run_copilot_comparison.py",
            "run_copilot_comparison_lane.py",
            "run_copilot_cli_agent_capability.py",
            "validate_benchmark_fixtures.py",
        ):
            shutil.copy2(REPO_ROOT / "scripts" / name, scripts / name)
        deadline_source = REPO_ROOT / "scripts" / "run_with_deadline.py"
        deadline_target = scripts / "run_with_deadline.py"
        if deadline_source.is_file():
            shutil.copy2(deadline_source, deadline_target)
        else:
            deadline_target.write_text("", encoding="utf-8")

        impeccable = root / "vendor" / "impeccable"
        for path, text in {
            impeccable / "package.json": json.dumps(
                {"name": "impeccable", "version": "3.5.0"}
            ),
            impeccable / "skill/SKILL.src.md": "IMPECCABLE_CORE",
            impeccable / "skill/reference/new-work.md": "IMPECCABLE_NEW",
            impeccable / "skill/reference/operate.md": "IMPECCABLE_OPERATE",
            impeccable / "skill/reference/polish.md": "IMPECCABLE_POLISH",
            impeccable / "skill/reference/audit.md": "IMPECCABLE_AUDIT",
            impeccable / "skill/reference/overdrive.md": "IMPECCABLE_OVERDRIVE",
            impeccable / "skill/reference/animate.md": "IMPECCABLE_ANIMATE",
            impeccable / "skill/reference/craft-floor.md": "IMPECCABLE_CRAFT",
            impeccable / "cli/bin/cli.js": "#!/usr/bin/env node\n",
        }.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        output_root = root / "harness-output" / "benchmarks" / "milestone-0"
        return temporary, root, impeccable, output_root

    @staticmethod
    def revision_resolver(path: Path) -> str:
        return IMPECCABLE_REVISION if path.name == "impeccable" else DESIGN_REVISION

    @staticmethod
    def fake_subprocess(calls, *, missing_report: bool = False):
        def run(argv, *, cwd, env, stdout, stderr, check):
            del stdout, stderr, check
            run_dir = Path(env["DESIGN_BENCHMARK_RUN_DIR"])
            lane = env["DESIGN_BENCHMARK_LANE"]
            calls.append(
                {
                    "argv": list(argv),
                    "cwd": cwd,
                    "runDir": run_dir,
                    "fixture": env["DESIGN_BENCHMARK_FIXTURE"],
                    "lane": lane,
                }
            )
            (run_dir / "output" / "index.html").write_text(
                "<!doctype html><title>generated</title>", encoding="utf-8"
            )
            if not missing_report:
                role_names = (
                    ("impeccable",)
                    if lane == "impeccable-alone"
                    else ("explore", "direct", "builder")
                )
                roles = {
                    role: {
                        "status": "passed",
                        "requestedModel": MODEL,
                        "resolvedModel": MODEL,
                    }
                    for role in role_names
                }
                (run_dir / "evidence" / "generation-report.json").write_text(
                    json.dumps(
                        {
                            "schemaVersion": 1,
                            "runId": env["DESIGN_BENCHMARK_RUN_ID"],
                            "status": "generated",
                            "lane": {"id": lane},
                            "roles": roles,
                        }
                    ),
                    encoding="utf-8",
                )
            return SimpleNamespace(returncode=0)

        return run

    def generate(self, calls, *, missing_report: bool = False, **kwargs):
        temporary, root, impeccable, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        with mock.patch.object(
            self.generation.benchmark.subprocess,
            "run",
            side_effect=self.fake_subprocess(calls, missing_report=missing_report),
        ):
            result = self.generation.generate_matrix(
                repo_root=root,
                output_root=output_root,
                matrix_id="m0-safe-001",
                impeccable_root=impeccable,
                design_revision=DESIGN_REVISION,
                impeccable_revision=IMPECCABLE_REVISION,
                fixture_id=kwargs.pop("fixture", "marketing-surface"),
                lane_id=kwargs.pop("lane", "design-studio-current"),
                copilot_bin="copilot",
                copilot_version="1.0.74",
                model=MODEL,
                node_bin="node",
                continue_on_error=kwargs.pop("continue_on_error", False),
                run_timeout_seconds=kwargs.pop(
                    "run_timeout_seconds", RUN_TIMEOUT_SECONDS
                ),
                revision_resolver=self.revision_resolver,
                **kwargs,
            )
        return result, root, output_root

    def test_all_runs_share_one_recorded_elapsed_budget(self) -> None:
        calls = []
        summary, _, _ = self.generate(
            calls,
            fixture="all",
            lane="all",
            continue_on_error=True,
        )

        self.assertEqual("generated", summary["status"])
        self.assertEqual(
            RUN_TIMEOUT_SECONDS,
            summary["executionPolicy"]["maximumElapsedSecondsPerRun"],
        )
        self.assertEqual(12, len(calls))
        for call in calls:
            command = call["argv"]
            timeout_index = command.index("--timeout-seconds")
            self.assertEqual(str(RUN_TIMEOUT_SECONDS), command[timeout_index + 1])
            separator = command.index("--")
            self.assertIn("run_with_deadline.py", command[1])
            self.assertIn("run_copilot_comparison_lane.py", command[separator + 2])

    def test_post_execution_validation_failure_is_terminal(self) -> None:
        calls = []
        summary, _, _ = self.generate(calls, missing_report=True)

        self.assertEqual("failed", summary["status"])
        run_dir = calls[0]["runDir"]
        run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        self.assertEqual("failed", run["status"])
        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual("generation-validation", events[-1]["step"])
        self.assertEqual("failed", events[-1]["status"])
        self.generation.benchmark.validate_run(run_dir)
        with self.assertRaisesRegex(
            self.generation.ContractError, "must be awaiting-evidence"
        ):
            self.generation.benchmark.complete_run(
                run_dir, run_dir / "unused-evidence.json"
            )


if __name__ == "__main__":
    unittest.main()
