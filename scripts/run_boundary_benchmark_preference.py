#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import secrets
import shutil
import sys
import tempfile
from typing import Any, Sequence


SCRIPT_PATH = Path(__file__).resolve()
RUNNER_PATH = SCRIPT_PATH.with_name("run_boundary_benchmark.py")
COMPARISON_SCHEMA_VERSION = 1
REVIEW_SCHEMA_VERSION = 1
RUBRIC_VERSION = 1
COMPARISON_ID_MAX_LENGTH = 48
BLIND_LABELS = ("A", "B", "C")
METRIC_KEYS = (
    "taskClarity",
    "originality",
    "functionalDefects",
    "elapsedSeconds",
    "tokenCost",
    "toolCost",
    "failedSteps",
    "recoveryEffort",
)
REVIEW_EVIDENCE_KEYS = (
    "summary",
    "intentionalitySpecificity",
    "interactionPolish",
    "scopeDiscipline",
)


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_boundary_benchmark_for_preference",
        RUNNER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark runner: {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = _load_runner()
ContractError = runner.ContractError


def _require_comparison_id(value: str) -> str:
    comparison_id = runner.require_nonempty_string(value, "comparison ID")
    if len(comparison_id) > COMPARISON_ID_MAX_LENGTH or not runner.RUN_ID_PATTERN.fullmatch(
        comparison_id
    ):
        raise ContractError(
            "comparison ID must use the benchmark run-ID character set and be at most "
            f"{COMPARISON_ID_MAX_LENGTH} characters"
        )
    return comparison_id


def _matrix_location(matrix_path: Path) -> tuple[dict[str, Any], Path]:
    matrix_path = matrix_path.resolve()
    receipt = runner.load_json(matrix_path, "benchmark matrix")
    if receipt.get("schemaVersion") != 1:
        raise ContractError("benchmark matrix schemaVersion must be 1")
    matrix_id = runner.require_nonempty_string(receipt.get("matrixId"), "matrix ID")
    if matrix_path.parent.name != matrix_id or matrix_path.parent.parent.name != "matrices":
        raise ContractError("benchmark matrix path does not match its matrix ID")
    output_root = matrix_path.parents[2]
    if matrix_path != output_root / "matrices" / matrix_id / "matrix.json":
        raise ContractError("benchmark matrix path does not match its output root")
    return receipt, output_root


def _fixture_entries(matrix: dict[str, Any], fixture_id: str) -> list[dict[str, Any]]:
    runs = matrix.get("runs")
    if not isinstance(runs, list):
        raise ContractError("benchmark matrix runs must be an array")
    entries = [
        entry
        for entry in runs
        if isinstance(entry, dict)
        and isinstance(entry.get("fixture"), dict)
        and entry["fixture"].get("id") == fixture_id
    ]
    if len(entries) != len(BLIND_LABELS):
        raise ContractError(
            f"fixture {fixture_id} must have exactly {len(BLIND_LABELS)} comparison lanes"
        )
    lane_ids: list[str] = []
    for entry in entries:
        lane = entry.get("lane")
        if not isinstance(lane, dict):
            raise ContractError("benchmark matrix lane entry must be an object")
        lane_ids.append(runner.require_nonempty_string(lane.get("id"), "lane.id"))
    if len(set(lane_ids)) != len(BLIND_LABELS):
        raise ContractError(f"fixture {fixture_id} comparison lanes must be unique")
    return entries


def _load_completed_entry(
    *,
    output_root: Path,
    matrix_suite: Any,
    entry: dict[str, Any],
) -> dict[str, Any]:
    run_dir = runner.ensure_inside(
        output_root,
        output_root / runner.require_nonempty_string(entry.get("runDir"), "matrix runDir"),
        "matrix run",
    )
    if not run_dir.is_dir():
        raise ContractError(f"benchmark matrix run is missing: {entry.get('runDir')}")
    runner.validate_run(run_dir)
    run = runner.load_json(run_dir / "run.json", "matrix run manifest")
    if run.get("status") != "complete":
        raise ContractError(
            f"comparison lane {entry.get('lane', {}).get('id')} must be complete; "
            f"current status is {run.get('status')}"
        )
    if run.get("runId") != entry.get("runId"):
        raise ContractError("completed run does not match the matrix run ID")
    run_fixture = run.get("fixture")
    if not isinstance(run_fixture, dict) or {
        "id": run_fixture.get("id"),
        "version": run_fixture.get("version"),
    } != entry.get("fixture"):
        raise ContractError("completed run does not match the matrix fixture")
    run_lane = run.get("lane")
    if not isinstance(run_lane, dict) or run_lane.get("id") != entry.get("lane", {}).get("id"):
        raise ContractError("completed run does not match the matrix lane")
    if run.get("suite") != matrix_suite:
        raise ContractError("completed run does not match the matrix suite provenance")

    result_path = run_dir / "evidence" / "result.json"
    result = runner.load_json(result_path, "completed lane result")
    for key in ("runId", "suite", "fixture", "lane", "tool"):
        if result.get(key) != run.get(key):
            raise ContractError(f"completed lane result does not match run metadata: {key}")
    output = result.get("output")
    if not isinstance(output, dict):
        raise ContractError("completed lane result output must be an object")
    tree_receipt = output.get("treeManifest")
    if not isinstance(tree_receipt, dict) or tree_receipt.get("algorithm") != "sha256":
        raise ContractError("completed lane result has no valid output tree receipt")
    expected_files = tree_receipt.get("files")
    actual_files = runner.tree_manifest(run_dir / "output")
    if expected_files != actual_files:
        raise ContractError("completed lane output differs from its result receipt")
    entrypoint = runner.require_nonempty_string(output.get("entrypoint"), "output entrypoint")
    entrypoint_path = runner.ensure_inside(
        run_dir / "output", run_dir / "output" / entrypoint, "output entrypoint"
    )
    if not entrypoint_path.is_file():
        raise ContractError(f"completed lane entrypoint is missing: {entrypoint}")

    fixture_manifest = runner.load_json(run_dir / "input" / "fixture.json", "fixture manifest")
    acceptance_name = runner.require_nonempty_string(
        fixture_manifest.get("acceptance"), "fixture.acceptance"
    )
    acceptance_path = runner.ensure_inside(
        run_dir / "input",
        run_dir / "input" / acceptance_name,
        "fixture acceptance",
    )
    if not acceptance_path.is_file():
        raise ContractError(f"fixture acceptance contract is missing: {acceptance_name}")
    brief_path = run_dir / "input" / "brief.md"
    if not brief_path.is_file():
        raise ContractError("fixture brief is missing")

    return {
        "entry": entry,
        "runDir": run_dir,
        "run": run,
        "result": result,
        "resultPath": result_path,
        "entrypoint": entrypoint,
        "briefPath": brief_path,
        "acceptancePath": acceptance_path,
    }


def _shuffled_entries(entries: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    shuffled = list(entries)
    secrets.SystemRandom().shuffle(shuffled)
    return shuffled


def _rubric() -> dict[str, Any]:
    return {
        "version": RUBRIC_VERSION,
        "instruction": (
            "Review only the visible rendered outcomes and interactions. Do not infer authorship, "
            "tooling or lane identity, and do not use source provenance when ranking submissions."
        ),
        "dimensions": [
            {
                "id": "intentionalitySpecificity",
                "prompt": (
                    "Does the outcome feel deliberately shaped for this brief rather than assembled "
                    "from interchangeable template choices? Cite concrete visual or interaction evidence."
                ),
            },
            {
                "id": "interactionPolish",
                "prompt": "Are interactions, states and transitions clear, coherent and appropriately polished?",
            },
            {
                "id": "scopeDiscipline",
                "prompt": "Does the outcome solve the brief without unsupported invention or decorative detours?",
            },
            {
                "id": "visibleOutcome",
                "prompt": "Which outcome is strongest overall when judged only from the rendered result?",
            },
        ],
    }


def _same_context(completed: Sequence[dict[str, Any]]) -> tuple[Path, Path, dict[str, Any]]:
    first = completed[0]
    brief_digest = runner.sha256(first["briefPath"])
    acceptance_digest = runner.sha256(first["acceptancePath"])
    fixture = first["run"]["fixture"]
    for item in completed[1:]:
        if item["run"]["fixture"] != fixture:
            raise ContractError("comparison runs do not share the same fixture metadata")
        if runner.sha256(item["briefPath"]) != brief_digest:
            raise ContractError("comparison runs do not share the same frozen brief")
        if runner.sha256(item["acceptancePath"]) != acceptance_digest:
            raise ContractError("comparison runs do not share the same acceptance contract")
    return first["briefPath"], first["acceptancePath"], fixture


def prepare_comparison(
    *,
    matrix_path: Path,
    fixture_id: str,
    comparison_id: str,
) -> Path:
    comparison_id = _require_comparison_id(comparison_id)
    fixture_id = runner.require_nonempty_string(fixture_id, "fixture ID")
    matrix, output_root = _matrix_location(matrix_path)
    entries = _fixture_entries(matrix, fixture_id)
    completed = [
        _load_completed_entry(
            output_root=output_root,
            matrix_suite=matrix.get("suite"),
            entry=entry,
        )
        for entry in entries
    ]
    brief_path, acceptance_path, fixture = _same_context(completed)
    acceptance = runner.load_json(acceptance_path, "fixture acceptance contract")

    comparisons_root = output_root / "comparisons"
    comparison_dir = comparisons_root / comparison_id
    if comparison_dir.exists():
        raise ContractError(f"benchmark comparison already exists: {comparison_dir}")
    comparisons_root.mkdir(parents=True, exist_ok=True)
    temporary_dir = Path(tempfile.mkdtemp(prefix=f".{comparison_id}-", dir=comparisons_root))
    try:
        review_dir = temporary_dir / "review"
        context_dir = review_dir / "context"
        submissions_dir = review_dir / "submissions"
        private_dir = temporary_dir / "private"
        context_dir.mkdir(parents=True)
        submissions_dir.mkdir()
        private_dir.mkdir()
        shutil.copy2(brief_path, context_dir / "brief.md")
        shutil.copy2(acceptance_path, context_dir / "acceptance.json")

        assignments: dict[str, Any] = {}
        public_submissions: list[dict[str, Any]] = []
        for label, item in zip(BLIND_LABELS, _shuffled_entries(completed)):
            target = submissions_dir / label
            shutil.copytree(item["runDir"] / "output", target)
            copied_manifest = runner.tree_manifest(target)
            if copied_manifest != item["result"]["output"]["treeManifest"]["files"]:
                raise ContractError(f"blind submission {label} differs while copying")
            assignments[label] = {
                "runId": item["run"]["runId"],
                "runDir": item["entry"]["runDir"],
                "lane": item["run"]["lane"],
                "tool": item["run"]["tool"],
                "resultDigest": runner.sha256(item["resultPath"]),
            }
            public_submissions.append(
                {
                    "label": label,
                    "entrypoint": f"submissions/{label}/{item['entrypoint']}",
                    "treeManifest": {"algorithm": "sha256", "files": copied_manifest},
                }
            )

        review_manifest = {
            "schemaVersion": COMPARISON_SCHEMA_VERSION,
            "comparisonId": comparison_id,
            "fixture": fixture,
            "context": {
                "brief": "context/brief.md",
                "briefDigest": runner.sha256(context_dir / "brief.md"),
                "acceptance": "context/acceptance.json",
                "acceptanceDigest": runner.sha256(context_dir / "acceptance.json"),
                "evaluationFocus": acceptance.get("evaluationFocus", []),
            },
            "rubric": _rubric(),
            "submissions": public_submissions,
        }
        runner.atomic_write_json(review_dir / "manifest.json", review_manifest)
        assignment = {
            "schemaVersion": COMPARISON_SCHEMA_VERSION,
            "comparisonId": comparison_id,
            "fixture": fixture,
            "assignments": assignments,
        }
        assignment_path = private_dir / "assignment.json"
        runner.atomic_write_json(assignment_path, assignment)
        comparison = {
            "schemaVersion": COMPARISON_SCHEMA_VERSION,
            "comparisonId": comparison_id,
            "status": "prepared",
            "createdAt": runner.utc_now(),
            "fixture": fixture,
            "matrix": {
                "matrixId": matrix.get("matrixId"),
                "path": matrix_path.resolve().relative_to(output_root).as_posix(),
                "digest": runner.sha256(matrix_path),
            },
            "reviewManifest": "review/manifest.json",
            "reviewTreeManifest": {
                "algorithm": "sha256",
                "files": runner.tree_manifest(review_dir),
            },
            "assignment": "private/assignment.json",
            "assignmentDigest": runner.sha256(assignment_path),
            "result": None,
        }
        runner.atomic_write_json(temporary_dir / "comparison.json", comparison)
        temporary_dir.replace(comparison_dir)
    except BaseException:
        shutil.rmtree(temporary_dir, ignore_errors=True)
        if comparisons_root.exists():
            try:
                comparisons_root.rmdir()
            except OSError:
                pass
        raise
    return comparison_dir / "comparison.json"


def _load_comparison(comparison_path: Path) -> tuple[dict[str, Any], Path, Path]:
    comparison_path = comparison_path.resolve()
    receipt = runner.load_json(comparison_path, "benchmark comparison")
    if receipt.get("schemaVersion") != COMPARISON_SCHEMA_VERSION:
        raise ContractError(
            f"benchmark comparison schemaVersion must be {COMPARISON_SCHEMA_VERSION}"
        )
    comparison_id = _require_comparison_id(receipt.get("comparisonId"))
    comparison_dir = comparison_path.parent
    if comparison_path != comparison_dir / "comparison.json" or comparison_dir.name != comparison_id:
        raise ContractError("benchmark comparison path does not match its comparison ID")
    if comparison_dir.parent.name != "comparisons":
        raise ContractError("benchmark comparison must live under the comparisons directory")
    output_root = comparison_dir.parent.parent
    return receipt, comparison_dir, output_root


def _validate_prepared_artifacts(
    receipt: dict[str, Any], comparison_dir: Path, output_root: Path
) -> None:
    review_receipt = receipt.get("reviewTreeManifest")
    if not isinstance(review_receipt, dict) or review_receipt.get("algorithm") != "sha256":
        raise ContractError("comparison has no valid review tree receipt")
    if runner.tree_manifest(comparison_dir / "review") != review_receipt.get("files"):
        raise ContractError("review packet changed after prepare")

    assignment_rel = runner.require_nonempty_string(receipt.get("assignment"), "assignment path")
    assignment_path = runner.ensure_inside(
        comparison_dir,
        comparison_dir / assignment_rel,
        "assignment receipt",
    )
    if runner.sha256(assignment_path) != receipt.get("assignmentDigest"):
        raise ContractError("assignment receipt changed after prepare")

    matrix = receipt.get("matrix")
    if not isinstance(matrix, dict):
        raise ContractError("comparison matrix receipt must be an object")
    matrix_path = runner.ensure_inside(
        output_root,
        output_root / runner.require_nonempty_string(matrix.get("path"), "matrix path"),
        "comparison matrix",
    )
    if runner.sha256(matrix_path) != matrix.get("digest"):
        raise ContractError("benchmark matrix changed after comparison prepare")


def _load_assignment(receipt: dict[str, Any], comparison_dir: Path) -> dict[str, Any]:
    assignment_path = runner.ensure_inside(
        comparison_dir,
        comparison_dir / receipt["assignment"],
        "assignment receipt",
    )
    assignment = runner.load_json(assignment_path, "blind assignment")
    if assignment.get("schemaVersion") != COMPARISON_SCHEMA_VERSION:
        raise ContractError("blind assignment schemaVersion is invalid")
    if assignment.get("comparisonId") != receipt.get("comparisonId"):
        raise ContractError("blind assignment comparison ID does not match")
    if assignment.get("fixture") != receipt.get("fixture"):
        raise ContractError("blind assignment fixture does not match")
    assignments = assignment.get("assignments")
    if not isinstance(assignments, dict) or set(assignments) != set(BLIND_LABELS):
        raise ContractError("blind assignment must cover labels A, B and C exactly")
    lane_ids: set[str] = set()
    for label in BLIND_LABELS:
        value = assignments[label]
        if not isinstance(value, dict):
            raise ContractError(f"blind assignment {label} must be an object")
        runner.require_nonempty_string(value.get("runId"), f"assignment {label}.runId")
        runner.require_nonempty_string(value.get("runDir"), f"assignment {label}.runDir")
        lane = value.get("lane")
        tool = value.get("tool")
        if not isinstance(lane, dict) or not isinstance(tool, dict):
            raise ContractError(f"blind assignment {label} lane and tool must be objects")
        lane_id = runner.require_nonempty_string(lane.get("id"), f"assignment {label}.lane.id")
        if lane_id in lane_ids:
            raise ContractError("blind assignment repeats a lane")
        lane_ids.add(lane_id)
        runner.require_nonempty_string(value.get("resultDigest"), f"assignment {label}.resultDigest")
    return assignment


def validate_review(review: dict[str, Any]) -> dict[str, Any]:
    if review.get("schemaVersion") != REVIEW_SCHEMA_VERSION:
        raise ContractError(f"review.schemaVersion must be {REVIEW_SCHEMA_VERSION}")
    if review.get("rubricVersion") != RUBRIC_VERSION:
        raise ContractError(f"review.rubricVersion must be {RUBRIC_VERSION}")
    runner.require_nonempty_string(review.get("reviewer"), "review.reviewer")
    runner.require_nonempty_string(review.get("rationale"), "review.rationale")

    ranking = review.get("ranking")
    if not isinstance(ranking, list) or not ranking:
        raise ContractError("review.ranking must be a non-empty array of rank groups")
    flattened: list[str] = []
    for index, group in enumerate(ranking):
        if not isinstance(group, list) or not group:
            raise ContractError(f"review.ranking[{index}] must be a non-empty array")
        if any(label not in BLIND_LABELS for label in group):
            raise ContractError(f"review.ranking[{index}] contains an unknown blind label")
        flattened.extend(group)
    if len(flattened) != len(BLIND_LABELS) or set(flattened) != set(BLIND_LABELS):
        raise ContractError("review ranking must cover blind labels A, B and C exactly once")

    evidence = review.get("evidence")
    if not isinstance(evidence, dict) or set(evidence) != set(BLIND_LABELS):
        raise ContractError("review evidence must cover blind labels A, B and C exactly")
    for label in BLIND_LABELS:
        item = evidence[label]
        if not isinstance(item, dict):
            raise ContractError(f"review.evidence.{label} must be an object")
        if set(item) != set(REVIEW_EVIDENCE_KEYS):
            raise ContractError(
                f"review.evidence.{label} must contain exactly {sorted(REVIEW_EVIDENCE_KEYS)}"
            )
        for key in REVIEW_EVIDENCE_KEYS:
            runner.require_nonempty_string(item.get(key), f"review.evidence.{label}.{key}")
    return review


def _source_results(
    *,
    receipt: dict[str, Any],
    comparison_dir: Path,
    output_root: Path,
    assignment: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    assignments = assignment["assignments"]
    revealed: dict[str, Any] = {}
    lane_metrics: dict[str, dict[str, Any]] = {}
    matrix_path = output_root / receipt["matrix"]["path"]
    matrix = runner.load_json(matrix_path, "benchmark matrix")
    matrix_suite = matrix.get("suite")

    for label in BLIND_LABELS:
        mapped = assignments[label]
        run_dir = runner.ensure_inside(
            output_root,
            output_root / mapped["runDir"],
            "assigned comparison run",
        )
        runner.validate_run(run_dir)
        run = runner.load_json(run_dir / "run.json", "assigned run manifest")
        if run.get("status") != "complete":
            raise ContractError(f"assigned run {label} is no longer complete")
        if run.get("runId") != mapped["runId"] or run.get("lane") != mapped["lane"]:
            raise ContractError(f"assigned run {label} no longer matches its private mapping")
        if run.get("tool") != mapped["tool"] or run.get("suite") != matrix_suite:
            raise ContractError(f"assigned run {label} provenance no longer matches")
        result_path = run_dir / "evidence" / "result.json"
        if runner.sha256(result_path) != mapped["resultDigest"]:
            raise ContractError(f"assigned run {label} result changed after prepare")
        result = runner.load_json(result_path, f"assigned result {label}")
        lane_id = mapped["lane"]["id"]
        metrics: dict[str, Any] = {}
        for key in METRIC_KEYS:
            if key not in result:
                raise ContractError(f"assigned result {label} is missing metric {key}")
            metrics[key] = result[key]
        lane_metrics[lane_id] = metrics
        revealed[label] = {
            "runId": mapped["runId"],
            "lane": mapped["lane"],
            "tool": mapped["tool"],
        }
    return revealed, lane_metrics


def complete_comparison(*, comparison_path: Path, review_path: Path) -> Path:
    receipt, comparison_dir, output_root = _load_comparison(comparison_path)
    if receipt.get("status") != "prepared":
        raise ContractError(
            f"comparison must be prepared before completion; current status is {receipt.get('status')}"
        )
    _validate_prepared_artifacts(receipt, comparison_dir, output_root)
    review = validate_review(runner.load_json(review_path.resolve(), "blind review"))

    evidence_dir = comparison_dir / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    preserved_review_path = evidence_dir / "blind-review.json"
    if preserved_review_path.exists():
        preserved = runner.load_json(preserved_review_path, "preserved blind review")
        if preserved != review:
            raise ContractError("a different blind review is already preserved for this comparison")
    else:
        runner.atomic_write_json(preserved_review_path, review)

    # Provenance is intentionally loaded only after the blind review is durably preserved.
    assignment = _load_assignment(receipt, comparison_dir)
    revealed, lane_metrics = _source_results(
        receipt=receipt,
        comparison_dir=comparison_dir,
        output_root=output_root,
        assignment=assignment,
    )
    ranking = [
        {
            "rank": rank,
            "labels": group,
            "lanes": [revealed[label]["lane"]["id"] for label in group],
        }
        for rank, group in enumerate(review["ranking"], start=1)
    ]
    result = {
        "schemaVersion": COMPARISON_SCHEMA_VERSION,
        "comparisonId": receipt["comparisonId"],
        "fixture": receipt["fixture"],
        "matrix": receipt["matrix"],
        "completedAt": runner.utc_now(),
        "blindReview": {
            "path": "evidence/blind-review.json",
            "digest": runner.sha256(preserved_review_path),
            "reviewer": review["reviewer"],
            "rubricVersion": review["rubricVersion"],
        },
        "outputPreference": {
            "status": "recorded",
            "winnerLabels": review["ranking"][0],
            "winnerLanes": [revealed[label]["lane"]["id"] for label in review["ranking"][0]],
            "ranking": ranking,
            "rationale": review["rationale"],
        },
        "revealedAssignments": revealed,
        "laneMetrics": lane_metrics,
    }
    result_path = evidence_dir / "result.json"
    runner.atomic_write_json(result_path, result)
    receipt["status"] = "complete"
    receipt["completedAt"] = result["completedAt"]
    receipt["reviewDigest"] = result["blindReview"]["digest"]
    receipt["result"] = "evidence/result.json"
    runner.atomic_write_json(comparison_path.resolve(), receipt)
    return result_path


def validate_comparison(comparison_path: Path) -> dict[str, Any]:
    receipt, comparison_dir, output_root = _load_comparison(comparison_path)
    if receipt.get("status") not in {"prepared", "complete"}:
        raise ContractError(f"unknown comparison status: {receipt.get('status')}")
    _validate_prepared_artifacts(receipt, comparison_dir, output_root)
    if receipt.get("status") == "prepared":
        if receipt.get("result") is not None:
            raise ContractError("prepared comparison may not point to a result")
        return {
            "schemaVersion": COMPARISON_SCHEMA_VERSION,
            "comparisonId": receipt["comparisonId"],
            "status": "prepared",
        }

    preserved_review_path = comparison_dir / "evidence" / "blind-review.json"
    review = validate_review(runner.load_json(preserved_review_path, "preserved blind review"))
    review_digest = runner.sha256(preserved_review_path)
    if receipt.get("reviewDigest") != review_digest:
        raise ContractError("preserved blind review changed after completion")
    assignment = _load_assignment(receipt, comparison_dir)
    revealed, lane_metrics = _source_results(
        receipt=receipt,
        comparison_dir=comparison_dir,
        output_root=output_root,
        assignment=assignment,
    )
    if receipt.get("result") != "evidence/result.json":
        raise ContractError("completed comparison does not point to its result receipt")
    result = runner.load_json(comparison_dir / "evidence" / "result.json", "comparison result")
    expected_ranking = [
        {
            "rank": rank,
            "labels": group,
            "lanes": [revealed[label]["lane"]["id"] for label in group],
        }
        for rank, group in enumerate(review["ranking"], start=1)
    ]
    expected_preference = {
        "status": "recorded",
        "winnerLabels": review["ranking"][0],
        "winnerLanes": [revealed[label]["lane"]["id"] for label in review["ranking"][0]],
        "ranking": expected_ranking,
        "rationale": review["rationale"],
    }
    if result.get("outputPreference") != expected_preference:
        raise ContractError("comparison output preference differs from the preserved blind review")
    if result.get("revealedAssignments") != revealed:
        raise ContractError("comparison revealed assignments differ from the private mapping")
    if result.get("laneMetrics") != lane_metrics:
        raise ContractError("comparison lane metrics differ from completed lane results")
    blind_review = result.get("blindReview")
    if not isinstance(blind_review, dict) or blind_review.get("digest") != review_digest:
        raise ContractError("comparison result does not receipt the preserved blind review")
    for key in ("comparisonId", "fixture", "matrix"):
        if result.get(key) != receipt.get(key):
            raise ContractError(f"comparison result metadata differs from receipt: {key}")
    return {
        "schemaVersion": COMPARISON_SCHEMA_VERSION,
        "comparisonId": receipt["comparisonId"],
        "status": "complete",
        "winnerLanes": expected_preference["winnerLanes"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare, complete and validate blind Milestone 0 output-preference comparisons."
    )
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    prepare = subparsers.add_parser(
        "prepare",
        help="Create an anonymized A/B/C review packet from three completed fixture lanes.",
    )
    prepare.add_argument("--matrix", type=Path, required=True)
    prepare.add_argument("--fixture", required=True)
    prepare.add_argument("--comparison-id", required=True)

    complete = subparsers.add_parser(
        "complete",
        help="Lock blind review evidence, reveal provenance and aggregate lane metrics.",
    )
    complete.add_argument("--comparison", type=Path, required=True)
    complete.add_argument("--review", type=Path, required=True)

    validate = subparsers.add_parser("validate", help="Validate a blind comparison receipt.")
    validate.add_argument("--comparison", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command_name == "prepare":
            print(
                prepare_comparison(
                    matrix_path=args.matrix,
                    fixture_id=args.fixture,
                    comparison_id=args.comparison_id,
                )
            )
            return 0
        if args.command_name == "complete":
            print(
                complete_comparison(
                    comparison_path=args.comparison,
                    review_path=args.review,
                )
            )
            return 0
        if args.command_name == "validate":
            print(json.dumps(validate_comparison(args.comparison), sort_keys=True))
            return 0
    except ContractError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
