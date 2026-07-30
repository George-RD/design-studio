from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "run_boundary_benchmark.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_boundary_benchmark", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runner from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def complete_evidence(acceptance_path: Path) -> dict:
    acceptance = json.loads(acceptance_path.read_text())
    return {
        "schemaVersion": 1,
        "taskClarity": {
            "score": 4,
            "evidence": "The lane completed without an instruction clarification."
        },
        "originality": {
            "score": 7,
            "evidence": "The output uses a specific visual system rather than a generic template."
        },
        "functionalDefects": [],
        "tokenCost": {
            "status": "unavailable",
            "inputTokens": None,
            "outputTokens": None,
            "reason": "The harness did not expose token accounting."
        },
        "toolCost": {
            "status": "unavailable",
            "currency": None,
            "amount": None,
            "reason": "The harness did not expose monetary cost."
        },
        "failedSteps": [],
        "recoveryEffort": {
            "minutes": 0,
            "actions": []
        },
        "acceptanceChecks": [
            {
                "id": check["id"],
                "status": "pass",
                "evidence": f"Verified {check['id']} in the lane output."
            }
            for check in acceptance["functionalChecks"]
        ]
    }


class BoundaryBenchmarkRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def make_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        shutil.copytree(REPO_ROOT / "benchmarks", root / "benchmarks")
        output_root = root / "harness-output" / "benchmarks" / "milestone-0"
        return temporary, root, output_root

    def prepare(
        self,
        root: Path,
        output_root: Path,
        fixture: str = "marketing-surface",
        lane: str = "impeccable-alone",
        run_id: str = "run-001",
    ) -> Path:
        return self.runner.prepare_run(
            repo_root=root,
            output_root=output_root,
            fixture_id=fixture,
            lane_id=lane,
            run_id=run_id,
            tool={
                "name": "test-harness",
                "version": "1.0.0",
                "source": "local-test",
            },
        )

    def successful_command(self) -> list[str]:
        return [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; import os; "
                "out=Path(os.environ['DESIGN_BENCHMARK_OUTPUT_DIR']); "
                "out.mkdir(parents=True, exist_ok=True); "
                "(out/'index.html').write_text('<!doctype html><title>Result</title>')"
            ),
        ]

    def complete_successfully(self, run_dir: Path) -> Path:
        self.runner.execute_run(run_dir, self.successful_command())
        evidence_path = run_dir / "lane-evidence-input.json"
        evidence_path.write_text(
            json.dumps(complete_evidence(run_dir / "input" / "acceptance.json"), indent=2)
        )
        return self.runner.complete_run(run_dir, evidence_path)

    def test_prepare_rejects_path_traversal_run_id(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)

        with self.assertRaisesRegex(self.runner.ContractError, "run ID"):
            self.prepare(root, output_root, run_id="../escape")

        self.assertFalse((root / "escape").exists())

    def test_prepare_copies_locked_input_and_records_provenance(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)

        run_dir = self.prepare(
            root,
            output_root,
            fixture="product-overhaul",
            lane="design-studio-current",
        )

        run = json.loads((run_dir / "run.json").read_text())
        self.assertEqual("prepared", run["status"])
        self.assertEqual("product-overhaul", run["fixture"]["id"])
        self.assertEqual(1, run["fixture"]["version"])
        self.assertEqual("design-studio-current", run["lane"]["id"])
        self.assertEqual("test-harness", run["tool"]["name"])
        self.assertTrue((run_dir / "input" / "brief.md").is_file())
        self.assertTrue((run_dir / "work" / "index.html").is_file())
        self.assertTrue((run_dir / "work" / "styles.css").is_file())
        self.assertTrue((run_dir / "work" / "app.js").is_file())
        self.assertGreater(len(run["inputManifest"]["files"]), 2)
        self.assertEqual(
            sha256(root / "benchmarks" / "milestone-0" / "RUN_PROTOCOL.md"),
            run["suite"]["protocolDigest"],
        )
        self.assertEqual(sha256(MODULE_PATH), run["harness"]["scriptDigest"])
        self.assertEqual(1, len((run_dir / "events.jsonl").read_text().splitlines()))

    def test_prepare_rejects_missing_protocol(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        (root / "benchmarks" / "milestone-0" / "RUN_PROTOCOL.md").unlink()

        with self.assertRaisesRegex(self.runner.ContractError, "run protocol is missing"):
            self.prepare(root, output_root)

    def test_prepare_rejects_tampered_fixture_without_creating_run(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        brief = root / "benchmarks" / "milestone-0" / "fixtures" / "marketing-surface" / "brief.md"
        brief.write_text(brief.read_text() + "\nTampered.\n")

        with self.assertRaisesRegex(self.runner.ContractError, "fixture suite is invalid"):
            self.prepare(root, output_root)

        self.assertFalse((output_root / "marketing-surface" / "impeccable-alone" / "run-001").exists())

    def test_prepare_refuses_to_overwrite_an_existing_run(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        self.prepare(root, output_root)

        with self.assertRaisesRegex(self.runner.ContractError, "already exists"):
            self.prepare(root, output_root)

    def test_execute_failure_is_terminal_and_preserves_logs(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        run_dir = self.prepare(root, output_root)

        exit_code = self.runner.execute_run(
            run_dir,
            [sys.executable, "-c", "print('lane failed'); raise SystemExit(7)"],
        )

        self.assertEqual(7, exit_code)
        run = json.loads((run_dir / "run.json").read_text())
        self.assertEqual("failed", run["status"])
        execution = json.loads((run_dir / "evidence" / "execution.json").read_text())
        self.assertEqual(7, execution["exitCode"])
        self.assertIn("lane failed", (run_dir / "evidence" / "stdout.log").read_text())
        events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text().splitlines()]
        self.assertEqual(["prepared", "started", "failed"], [event["status"] for event in events])

        with self.assertRaisesRegex(self.runner.ContractError, "must be prepared"):
            self.runner.execute_run(run_dir, self.successful_command())

    def test_successful_execute_waits_for_validated_evidence(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        run_dir = self.prepare(root, output_root)

        exit_code = self.runner.execute_run(run_dir, self.successful_command())

        self.assertEqual(0, exit_code)
        run = json.loads((run_dir / "run.json").read_text())
        self.assertEqual("awaiting-evidence", run["status"])
        self.assertTrue((run_dir / "output" / "index.html").is_file())
        self.assertFalse((run_dir / "evidence" / "result.json").exists())

    def test_complete_rejects_missing_metrics_and_preserves_state(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        run_dir = self.prepare(root, output_root)
        self.runner.execute_run(run_dir, self.successful_command())
        evidence_path = run_dir / "incomplete-evidence.json"
        evidence_path.write_text(json.dumps({"schemaVersion": 1}))

        with self.assertRaisesRegex(self.runner.ContractError, "evidence is missing keys"):
            self.runner.complete_run(run_dir, evidence_path)

        run = json.loads((run_dir / "run.json").read_text())
        self.assertEqual("awaiting-evidence", run["status"])
        self.assertFalse((run_dir / "evidence" / "result.json").exists())

    def test_complete_records_required_metrics_and_measured_duration(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        run_dir = self.prepare(root, output_root)
        self.runner.execute_run(run_dir, self.successful_command())
        evidence_path = run_dir / "lane-evidence.json"
        evidence_path.write_text(
            json.dumps(complete_evidence(run_dir / "input" / "acceptance.json"), indent=2)
        )

        result_path = self.runner.complete_run(run_dir, evidence_path)

        result = json.loads(result_path.read_text())
        run = json.loads((run_dir / "run.json").read_text())
        execution = json.loads((run_dir / "evidence" / "execution.json").read_text())
        self.assertEqual("complete", run["status"])
        self.assertEqual(execution["elapsedSeconds"], result["elapsedSeconds"])
        self.assertEqual("comparison-level", result["outputPreference"]["status"])
        self.assertEqual("pending blind comparison", result["outputPreference"]["reason"])
        self.assertEqual(
            {check["id"] for check in json.loads((run_dir / "input" / "acceptance.json").read_text())["functionalChecks"]},
            {check["id"] for check in result["acceptanceChecks"]},
        )
        events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text().splitlines()]
        self.assertEqual("completed", events[-1]["status"])

    def test_lane_evidence_cannot_set_comparison_preference(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        run_dir = self.prepare(root, output_root)
        self.runner.execute_run(run_dir, self.successful_command())
        evidence = complete_evidence(run_dir / "input" / "acceptance.json")
        evidence["outputPreference"] = {"winner": "self"}
        evidence_path = run_dir / "lane-evidence-input.json"
        evidence_path.write_text(json.dumps(evidence, indent=2))

        with self.assertRaisesRegex(self.runner.ContractError, "comparison-level"):
            self.runner.complete_run(run_dir, evidence_path)

    def test_complete_preserves_raw_lane_evidence(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        run_dir = self.prepare(root, output_root)
        self.runner.execute_run(run_dir, self.successful_command())
        evidence = complete_evidence(run_dir / "input" / "acceptance.json")
        evidence_path = root / "observer-evidence.json"
        evidence_path.write_text(json.dumps(evidence, indent=2))

        result_path = self.runner.complete_run(run_dir, evidence_path)

        result = json.loads(result_path.read_text())
        preserved = json.loads((run_dir / "evidence" / "lane-evidence.json").read_text())
        self.assertEqual(evidence, preserved)
        self.assertEqual("evidence/lane-evidence.json", result["rawEvidence"])

    def test_validate_rejects_output_mutation_after_completion(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        run_dir = self.prepare(root, output_root)
        self.complete_successfully(run_dir)
        (run_dir / "output" / "index.html").write_text("mutated after completion")

        with self.assertRaisesRegex(self.runner.ContractError, "output tree changed"):
            self.runner.validate_run(run_dir)

    def test_validate_rejects_corrupt_event_sequence(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        run_dir = self.prepare(root, output_root)
        event = json.loads((run_dir / "events.jsonl").read_text())
        event["sequence"] = 2
        (run_dir / "events.jsonl").write_text(json.dumps(event) + "\n")

        with self.assertRaisesRegex(self.runner.ContractError, "event sequence"):
            self.runner.validate_run(run_dir)

    def test_complete_rejects_input_mutation_after_prepare(self) -> None:
        temporary, root, output_root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        run_dir = self.prepare(root, output_root)
        self.runner.execute_run(run_dir, self.successful_command())
        (run_dir / "input" / "brief.md").write_text("mutated")
        evidence_path = run_dir / "lane-evidence.json"
        evidence_path.write_text(
            json.dumps(complete_evidence(run_dir / "input" / "acceptance.json"), indent=2)
        )

        with self.assertRaisesRegex(self.runner.ContractError, "input tree changed"):
            self.runner.complete_run(run_dir, evidence_path)

        run = json.loads((run_dir / "run.json").read_text())
        self.assertEqual("awaiting-evidence", run["status"])


if __name__ == "__main__":
    unittest.main()
