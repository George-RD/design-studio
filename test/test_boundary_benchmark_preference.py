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
LANES = (
    "impeccable-alone",
    "design-studio-current",
    "design-studio-impeccable",
)


def load_preference_runner():
    spec = importlib.util.spec_from_file_location(
        "run_boundary_benchmark_preference_test",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load preference runner from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class BoundaryBenchmarkPreferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preference = load_preference_runner()

    def make_matrix(
        self,
    ) -> tuple[tempfile.TemporaryDirectory[str], Path, Path, dict[str, Path]]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        output_root = root / "harness-output" / "benchmarks" / "milestone-0"
        matrix_dir = output_root / "matrices" / "m0-001"
        matrix_dir.mkdir(parents=True)
        matrix_path = matrix_dir / "matrix.json"
        fixture = {"id": "marketing-surface", "version": 1}
        suite = {
            "id": "design-studio-boundary",
            "version": 1,
            "lockDigest": "fixture-lock",
            "protocolDigest": "protocol",
        }
        runs: list[dict[str, object]] = []
        run_dirs: dict[str, Path] = {}

        for index, lane in enumerate(LANES, start=1):
            run_id = f"m0-001-marketing-surface-{lane}"
            run_dir = output_root / "marketing-surface" / lane / run_id
            run_dirs[lane] = run_dir
            (run_dir / "input").mkdir(parents=True)
            (run_dir / "output").mkdir()
            (run_dir / "evidence").mkdir()
            (run_dir / "input" / "brief.md").write_text("Build the same frozen brief.\n")
            (run_dir / "input" / "fixture.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "acceptance": "acceptance.json",
                        "outputContract": {"entrypoint": "index.html"},
                    }
                )
            )
            (run_dir / "input" / "acceptance.json").write_text(
                json.dumps(
                    {
                        "functionalChecks": [
                            {
                                "id": "mobile-overflow",
                                "action": "Render at 390x844.",
                                "expected": "No horizontal overflow.",
                            }
                        ],
                        "evaluationFocus": ["visual distinctiveness", "offer clarity"],
                    }
                )
            )
            (run_dir / "output" / "index.html").write_text(
                f"<!doctype html><title>Submission {index}</title>"
            )
            result = {
                "runId": run_id,
                "suite": suite,
                "fixture": fixture,
                "lane": {"id": lane},
                "tool": {
                    "name": f"tool-{index}",
                    "version": "1.0",
                    "source": f"source-{index}",
                },
                "taskClarity": {"score": index, "evidence": f"clarity-{index}"},
                "originality": {"score": 5 + index, "evidence": f"originality-{index}"},
                "functionalDefects": [],
                "elapsedSeconds": float(index * 10),
                "tokenCost": {
                    "status": "measured",
                    "inputTokens": index * 100,
                    "outputTokens": index * 200,
                },
                "toolCost": {
                    "status": "measured",
                    "amount": float(index),
                    "currency": "USD",
                },
                "failedSteps": [],
                "recoveryEffort": {"minutes": 0, "actions": []},
                "output": {
                    "root": "output",
                    "entrypoint": "index.html",
                    "treeManifest": {
                        "algorithm": "sha256",
                        "files": self.preference.runner.tree_manifest(run_dir / "output"),
                    },
                },
            }
            (run_dir / "evidence" / "result.json").write_text(json.dumps(result))
            (run_dir / "run.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "runId": run_id,
                        "status": "complete",
                        "suite": suite,
                        "fixture": fixture,
                        "lane": {"id": lane},
                        "tool": result["tool"],
                        "result": "evidence/result.json",
                    }
                )
            )
            runs.append(
                {
                    "fixture": fixture,
                    "lane": {"id": lane},
                    "runId": run_id,
                    "runDir": run_dir.relative_to(output_root).as_posix(),
                }
            )

        matrix_path.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "matrixId": "m0-001",
                    "status": "active",
                    "suite": suite,
                    "runs": runs,
                }
            )
        )
        return temporary, matrix_path, output_root, run_dirs

    def prepare(self, matrix_path: Path) -> Path:
        with mock.patch.object(self.preference.runner, "validate_run", return_value=None), mock.patch.object(
            self.preference,
            "_shuffled_entries",
            side_effect=lambda entries: list(entries),
        ):
            return self.preference.prepare_comparison(
                matrix_path=matrix_path,
                fixture_id="marketing-surface",
                comparison_id="cmp-001",
            )

    def review(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "rubricVersion": 1,
            "reviewer": "blind-reviewer-1",
            "ranking": [["B"], ["A", "C"]],
            "rationale": "B is the most coherent outcome; A and C are tied overall.",
            "evidence": {
                label: {
                    "summary": f"Visible outcome evidence for {label}.",
                    "intentionalitySpecificity": (
                        f"{label} shows brief-specific hierarchy rather than interchangeable template choices."
                    ),
                    "interactionPolish": f"Interaction evidence for {label}.",
                    "scopeDiscipline": f"Scope evidence for {label}.",
                }
                for label in ("A", "B", "C")
            },
        }

    def test_prepare_anonymizes_three_complete_lane_outputs_and_receipts_review_tree(self):
        temporary, matrix_path, _output_root, run_dirs = self.make_matrix()
        self.addCleanup(temporary.cleanup)

        comparison_path = self.prepare(matrix_path)
        comparison_dir = comparison_path.parent
        review_manifest = json.loads((comparison_dir / "review" / "manifest.json").read_text())
        private_mapping = json.loads((comparison_dir / "private" / "assignment.json").read_text())

        self.assertEqual(["A", "B", "C"], [item["label"] for item in review_manifest["submissions"]])
        self.assertEqual(
            ["intentionalitySpecificity", "interactionPolish", "scopeDiscipline", "visibleOutcome"],
            [dimension["id"] for dimension in review_manifest["rubric"]["dimensions"]],
        )
        public_payload = json.dumps(review_manifest, sort_keys=True)
        for lane in LANES:
            self.assertNotIn(lane, public_payload)
        self.assertNotIn("tool-", public_payload)
        self.assertNotIn("runId", public_payload)
        self.assertEqual(set(LANES), {entry["lane"]["id"] for entry in private_mapping["assignments"].values()})

        for label, lane in zip(("A", "B", "C"), LANES):
            self.assertEqual(
                (run_dirs[lane] / "output" / "index.html").read_text(),
                (comparison_dir / "review" / "submissions" / label / "index.html").read_text(),
            )

        receipt = json.loads(comparison_path.read_text())
        self.assertEqual("prepared", receipt["status"])
        self.assertEqual(
            self.preference.runner.tree_manifest(comparison_dir / "review"),
            receipt["reviewTreeManifest"]["files"],
        )

    def test_prepare_rejects_any_lane_that_is_not_complete(self):
        temporary, matrix_path, _output_root, run_dirs = self.make_matrix()
        self.addCleanup(temporary.cleanup)
        run_path = run_dirs["design-studio-current"] / "run.json"
        run = json.loads(run_path.read_text())
        run["status"] = "awaiting-evidence"
        run_path.write_text(json.dumps(run))

        with mock.patch.object(self.preference.runner, "validate_run", return_value=None):
            with self.assertRaisesRegex(self.preference.ContractError, "must be complete"):
                self.preference.prepare_comparison(
                    matrix_path=matrix_path,
                    fixture_id="marketing-surface",
                    comparison_id="cmp-incomplete",
                )

    def test_complete_locks_blind_review_before_revealing_preference_and_aggregates_metrics(self):
        temporary, matrix_path, _output_root, _run_dirs = self.make_matrix()
        self.addCleanup(temporary.cleanup)
        comparison_path = self.prepare(matrix_path)
        comparison_dir = comparison_path.parent
        review_path = Path(temporary.name) / "review.json"
        review_path.write_text(json.dumps(self.review()))

        with mock.patch.object(self.preference.runner, "validate_run", return_value=None):
            result_path = self.preference.complete_comparison(
                comparison_path=comparison_path,
                review_path=review_path,
            )

        result = json.loads(result_path.read_text())
        preserved_review = json.loads((comparison_dir / "evidence" / "blind-review.json").read_text())
        self.assertEqual(self.review(), preserved_review)
        self.assertEqual("recorded", result["outputPreference"]["status"])
        self.assertEqual(["B"], result["outputPreference"]["winnerLabels"])
        self.assertEqual(
            "design-studio-current",
            result["outputPreference"]["ranking"][0]["lanes"][0],
        )
        self.assertEqual(
            {
                "taskClarity",
                "originality",
                "functionalDefects",
                "elapsedSeconds",
                "tokenCost",
                "toolCost",
                "failedSteps",
                "recoveryEffort",
            },
            set(result["laneMetrics"]["design-studio-current"]),
        )
        receipt = json.loads(comparison_path.read_text())
        self.assertEqual("complete", receipt["status"])
        self.assertEqual("evidence/result.json", receipt["result"])

    def test_complete_rejects_tampered_blind_submission_before_review_is_preserved(self):
        temporary, matrix_path, _output_root, _run_dirs = self.make_matrix()
        self.addCleanup(temporary.cleanup)
        comparison_path = self.prepare(matrix_path)
        comparison_dir = comparison_path.parent
        (comparison_dir / "review" / "submissions" / "A" / "index.html").write_text("tampered")
        review_path = Path(temporary.name) / "review.json"
        review_path.write_text(json.dumps(self.review()))

        with self.assertRaisesRegex(self.preference.ContractError, "review packet changed"):
            self.preference.complete_comparison(
                comparison_path=comparison_path,
                review_path=review_path,
            )
        self.assertFalse((comparison_dir / "evidence" / "blind-review.json").exists())

    def test_complete_requires_each_blind_label_exactly_once_in_ranking_and_evidence(self):
        temporary, matrix_path, _output_root, _run_dirs = self.make_matrix()
        self.addCleanup(temporary.cleanup)
        comparison_path = self.prepare(matrix_path)
        bad_review = self.review()
        bad_review["ranking"] = [["A"], ["A"], ["C"]]
        review_path = Path(temporary.name) / "bad-review.json"
        review_path.write_text(json.dumps(bad_review))

        with self.assertRaisesRegex(self.preference.ContractError, "ranking must cover"):
            self.preference.complete_comparison(
                comparison_path=comparison_path,
                review_path=review_path,
            )

    def test_validate_detects_private_mapping_mutation_after_completion(self):
        temporary, matrix_path, _output_root, _run_dirs = self.make_matrix()
        self.addCleanup(temporary.cleanup)
        comparison_path = self.prepare(matrix_path)
        comparison_dir = comparison_path.parent
        review_path = Path(temporary.name) / "review.json"
        review_path.write_text(json.dumps(self.review()))
        with mock.patch.object(self.preference.runner, "validate_run", return_value=None):
            self.preference.complete_comparison(
                comparison_path=comparison_path,
                review_path=review_path,
            )

        mapping_path = comparison_dir / "private" / "assignment.json"
        mapping = json.loads(mapping_path.read_text())
        mapping["assignments"]["A"]["lane"]["id"] = "tampered-lane"
        mapping_path.write_text(json.dumps(mapping))

        with self.assertRaisesRegex(self.preference.ContractError, "assignment receipt changed"):
            self.preference.validate_comparison(comparison_path)


if __name__ == "__main__":
    unittest.main()
