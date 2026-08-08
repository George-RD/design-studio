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
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "milestone-0-comparison-generation.yml"
DESIGN_REVISION = "d" * 40
IMPECCABLE_REVISION = "e" * 40
MISMATCH_REVISION = "c" * 40
AUTO_MODEL = "auto"
EXPLICIT_MODEL = "fixed-model"
DIRECTOR_MODEL = "claude-haiku-4.5"
BUILDER_MODEL = "gpt-5-mini"


def load_generation_runner():
    spec = importlib.util.spec_from_file_location(
        "run_copilot_comparison_matrix_generation_test", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load matrix generation runner from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CopilotComparisonMatrixGenerationTests(unittest.TestCase):
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
    def default_resolved_models(lane: str) -> dict[str, str]:
        if lane == "impeccable-alone":
            return {"impeccable": BUILDER_MODEL}
        return {
            "explore": DIRECTOR_MODEL,
            "direct": DIRECTOR_MODEL,
            "builder": BUILDER_MODEL,
        }

    def fake_subprocess(
        self,
        calls,
        *,
        status="generated",
        missing_report=False,
        requested_model=AUTO_MODEL,
        resolved_models: dict[str, str] | None = None,
    ):
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
            if status == "generated":
                (run_dir / "output" / "index.html").write_text(
                    "<!doctype html><title>generated</title>", encoding="utf-8"
                )
                if not missing_report:
                    concrete = resolved_models or self.default_resolved_models(lane)
                    roles = {
                        role: {
                            "status": "passed",
                            "requestedModel": requested_model,
                            "resolvedModel": resolved,
                        }
                        for role, resolved in concrete.items()
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
            (run_dir / "evidence" / "generation-report.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "runId": env["DESIGN_BENCHMARK_RUN_ID"],
                        "status": status,
                        "error": {"message": f"synthetic {status}"},
                    }
                ),
                encoding="utf-8",
            )
            return SimpleNamespace(returncode=2 if status == "blocked" else 1)

        return run

    def generate(
        self,
        *,
        fixture="marketing-surface",
        lane="design-studio-current",
        **kwargs,
    ):
        temporary, root, impeccable, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        result = self.generation.generate_matrix(
            repo_root=root,
            output_root=output_root,
            matrix_id="m0-live-001",
            impeccable_root=impeccable,
            design_revision=DESIGN_REVISION,
            impeccable_revision=IMPECCABLE_REVISION,
            fixture_id=fixture,
            lane_id=lane,
            copilot_bin="copilot",
            copilot_version="1.0.74",
            model=kwargs.pop("model", AUTO_MODEL),
            node_bin="node",
            continue_on_error=kwargs.pop("continue_on_error", False),
            revision_resolver=self.revision_resolver,
            **kwargs,
        )
        return result, root, impeccable, output_root

    def test_build_lane_tools_binds_versions_and_actual_git_revisions(self) -> None:
        temporary, root, impeccable, _ = self.make_repo()
        self.addCleanup(temporary.cleanup)
        tools = self.generation.build_lane_tools(
            repo_root=root,
            impeccable_root=impeccable,
            design_revision=DESIGN_REVISION,
            impeccable_revision=IMPECCABLE_REVISION,
            revision_resolver=self.revision_resolver,
        )
        self.assertEqual(
            {
                "name": "design-studio",
                "version": "1.5.0",
                "source": f"George-RD/design-studio@{DESIGN_REVISION}",
            },
            tools["design-studio-current"],
        )
        self.assertEqual("3.5.0", tools["impeccable-alone"]["version"])
        self.assertEqual(
            "1.5.0+3.5.0", tools["design-studio-impeccable"]["version"]
        )
        self.assertEqual(
            f"George-RD/design-studio@{DESIGN_REVISION} + "
            f"pbakaus/impeccable@{IMPECCABLE_REVISION}",
            tools["design-studio-impeccable"]["source"],
        )

    def test_revision_mismatch_fails_before_matrix_creation(self) -> None:
        temporary, root, impeccable, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        with self.assertRaisesRegex(self.generation.ContractError, "revision"):
            self.generation.generate_matrix(
                repo_root=root,
                output_root=output_root,
                matrix_id="m0-bad-revision",
                impeccable_root=impeccable,
                design_revision=MISMATCH_REVISION,
                impeccable_revision=IMPECCABLE_REVISION,
                fixture_id="marketing-surface",
                lane_id="design-studio-current",
                model=AUTO_MODEL,
                revision_resolver=self.revision_resolver,
            )
        self.assertFalse(output_root.exists())

    def test_invalid_selection_fails_before_matrix_creation(self) -> None:
        temporary, root, impeccable, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        with self.assertRaisesRegex(self.generation.ContractError, "selection"):
            self.generation.generate_matrix(
                repo_root=root,
                output_root=output_root,
                matrix_id="m0-bad-input",
                impeccable_root=impeccable,
                design_revision=DESIGN_REVISION,
                impeccable_revision=IMPECCABLE_REVISION,
                fixture_id="unknown-fixture",
                lane_id="design-studio-current",
                model=AUTO_MODEL,
                revision_resolver=self.revision_resolver,
            )
        self.assertFalse(output_root.exists())

    def test_auto_policy_requires_the_verified_capability_receipt(self) -> None:
        temporary, root, impeccable, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        receipt_path = (
            root
            / "benchmarks"
            / "milestone-0"
            / "evidence"
            / "copilot-cli-agent-capability.json"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["executionSurface"]["version"] = "different-version"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaisesRegex(self.generation.ContractError, "capability"):
            self.generation.generate_matrix(
                repo_root=root,
                output_root=output_root,
                matrix_id="m0-unverified-auto",
                impeccable_root=impeccable,
                design_revision=DESIGN_REVISION,
                impeccable_revision=IMPECCABLE_REVISION,
                fixture_id="marketing-surface",
                lane_id="design-studio-current",
                model=AUTO_MODEL,
                copilot_version="1.0.74",
                revision_resolver=self.revision_resolver,
            )
        self.assertFalse(output_root.exists())

    def test_single_selection_records_role_specific_auto_resolution(self) -> None:
        calls = []
        with mock.patch.object(
            self.generation.benchmark.subprocess,
            "run",
            side_effect=self.fake_subprocess(calls),
        ):
            summary, root, _, output_root = self.generate()

        self.assertEqual("generated", summary["status"])
        self.assertEqual("auto-per-role", summary["modelPolicy"]["mode"])
        self.assertEqual(AUTO_MODEL, summary["modelPolicy"]["requestedModel"])
        self.assertTrue(summary["modelPolicy"]["capabilityReceipt"].endswith(
            "copilot-cli-agent-capability.json"
        ))
        self.assertEqual({"generated": 1}, summary["runStatuses"])
        self.assertEqual(
            self.default_resolved_models("design-studio-current"),
            summary["runs"][0]["resolvedModels"],
        )
        self.assertEqual(1, len(calls))
        self.assertEqual("marketing-surface", calls[0]["fixture"])
        self.assertEqual("design-studio-current", calls[0]["lane"])
        self.assertEqual((calls[0]["runDir"] / "work").resolve(), calls[0]["cwd"])
        command = calls[0]["argv"]
        self.assertEqual(sys.executable, command[0])
        self.assertIn("run_copilot_comparison_lane.py", command[1])
        self.assertIn(DESIGN_REVISION, command)
        self.assertIn(IMPECCABLE_REVISION, command)
        self.assertIn(AUTO_MODEL, command)
        self.assertNotIn("GITHUB_TOKEN", " ".join(command))

        matrix_path = output_root / "matrices" / "m0-live-001" / "matrix.json"
        self.assertEqual(
            12, len(json.loads(matrix_path.read_text(encoding="utf-8"))["runs"])
        )
        matrix_summary = self.generation.matrix.validate_matrix(
            matrix_path, repo_root=root
        )
        self.assertEqual("active", matrix_summary["status"])
        self.assertEqual(
            {"awaiting-evidence": 1, "prepared": 11},
            matrix_summary["runStatuses"],
        )
        self.assertEqual(
            summary,
            json.loads(
                (output_root / "matrices" / "m0-live-001" / "generation.json").read_text(
                    encoding="utf-8"
                )
            ),
        )

    def test_all_selection_runs_the_full_frozen_matrix_in_order(self) -> None:
        calls = []
        with mock.patch.object(
            self.generation.benchmark.subprocess,
            "run",
            side_effect=self.fake_subprocess(calls),
        ):
            summary, _, _, _ = self.generate(
                fixture="all", lane="all", continue_on_error=True
            )
        self.assertEqual("generated", summary["status"])
        self.assertEqual(12, len(calls))
        observed = [(call["fixture"], call["lane"]) for call in calls]
        self.assertEqual(summary["selectedPairs"], [list(pair) for pair in observed])
        for entry in summary["runs"]:
            self.assertEqual(
                self.default_resolved_models(entry["lane"]), entry["resolvedModels"]
            )

    def test_blocked_run_is_preserved_and_stops_when_requested(self) -> None:
        calls = []
        with mock.patch.object(
            self.generation.benchmark.subprocess,
            "run",
            side_effect=self.fake_subprocess(calls, status="blocked"),
        ):
            summary, _, _, output_root = self.generate(
                fixture="all", lane="design-studio-current"
            )
        self.assertEqual("blocked", summary["status"])
        self.assertEqual({"blocked": 1, "not-run": 3}, summary["runStatuses"])
        self.assertEqual(1, len(calls))
        report = summary["runs"][0]
        self.assertEqual("blocked", report["status"])
        self.assertEqual(2, report["exitCode"])
        self.assertTrue(report["generationReport"].endswith("generation-report.json"))
        self.assertTrue(
            (output_root / "matrices" / "m0-live-001" / "generation.json").is_file()
        )

    def test_missing_or_nonconcrete_auto_receipt_invalidates_success(self) -> None:
        cases = (
            ({"missing_report": True}, "generation report"),
            (
                {
                    "resolved_models": {
                        "explore": AUTO_MODEL,
                        "direct": DIRECTOR_MODEL,
                        "builder": BUILDER_MODEL,
                    }
                },
                "concrete resolved model",
            ),
        )
        for fake_options, expected_error in cases:
            with self.subTest(fake_options=fake_options):
                calls = []
                with mock.patch.object(
                    self.generation.benchmark.subprocess,
                    "run",
                    side_effect=self.fake_subprocess(calls, **fake_options),
                ):
                    summary, _, _, _ = self.generate()
                self.assertEqual("failed", summary["status"])
                self.assertEqual({"failed": 1}, summary["runStatuses"])
                self.assertIn(expected_error, summary["runs"][0]["error"])

    def test_explicit_model_still_requires_exact_resolution(self) -> None:
        calls = []
        with mock.patch.object(
            self.generation.benchmark.subprocess,
            "run",
            side_effect=self.fake_subprocess(
                calls,
                requested_model=EXPLICIT_MODEL,
                resolved_models={
                    "explore": "different-model",
                    "direct": EXPLICIT_MODEL,
                    "builder": EXPLICIT_MODEL,
                },
            ),
        ):
            summary, _, _, _ = self.generate(model=EXPLICIT_MODEL)
        self.assertEqual("failed", summary["status"])
        self.assertIn("different-model", summary["runs"][0]["error"])

    def test_dispatch_workflow_defaults_to_verified_full_matrix_execution(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertIn('COPILOT_CLI_VERSION: "1.0.74"', workflow)
        self.assertIn(
            'IMPECCABLE_REVISION: "aee6ce9352b842217b3f57c78296a7a4fa35a7f3"',
            workflow,
        )
        self.assertIn("copilot-requests: write", workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("--fixture", workflow)
        self.assertIn("--lane", workflow)
        self.assertIn("--continue-on-error", workflow)
        self.assertIn("Verified Copilot model policy", workflow)
        self.assertGreaterEqual(workflow.count("default: all"), 2)
        self.assertIn("default: auto", workflow)
        self.assertIn("default: true", workflow)


if __name__ == "__main__":
    unittest.main()
