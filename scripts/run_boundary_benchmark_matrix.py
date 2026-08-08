#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Sequence


SCRIPT_PATH = Path(__file__).resolve()
RUNNER_PATH = SCRIPT_PATH.with_name("run_boundary_benchmark.py")
MATRIX_SCHEMA_VERSION = 1
MATRIX_ID_MAX_LENGTH = 24


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_boundary_benchmark_for_matrix",
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


def _require_matrix_id(value: str) -> str:
    matrix_id = runner.require_nonempty_string(value, "matrix ID")
    if len(matrix_id) > MATRIX_ID_MAX_LENGTH or not runner.RUN_ID_PATTERN.fullmatch(
        matrix_id
    ):
        raise ContractError(
            "matrix ID must use the benchmark run-ID character set and be at most "
            f"{MATRIX_ID_MAX_LENGTH} characters"
        )
    return matrix_id


def _normalize_lane_tools(
    lane_tools: dict[str, dict[str, str]],
    expected_lanes: Sequence[str],
) -> dict[str, dict[str, str]]:
    if not isinstance(lane_tools, dict):
        raise ContractError("lane tool configuration must be an object")
    expected = set(expected_lanes)
    actual = set(lane_tools)
    if actual != expected:
        raise ContractError(
            "lane tool configuration must cover the frozen lanes exactly; "
            f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
        )

    normalized: dict[str, dict[str, str]] = {}
    for lane_id in expected_lanes:
        raw = lane_tools.get(lane_id)
        if not isinstance(raw, dict) or set(raw) != {"name", "version", "source"}:
            raise ContractError(
                f"lane tool configuration for {lane_id} must contain exactly "
                "name, version and source"
            )
        normalized[lane_id] = {
            key: runner.require_nonempty_string(raw.get(key), f"{lane_id}.{key}")
            for key in ("name", "version", "source")
        }
    return normalized


def load_lane_tools(path: Path) -> dict[str, dict[str, str]]:
    value = runner.load_json(path, "lane tool configuration")
    if value.get("schemaVersion") != 1:
        raise ContractError("lane tool configuration schemaVersion must be 1")
    lanes = value.get("lanes")
    if not isinstance(lanes, dict):
        raise ContractError("lane tool configuration lanes must be an object")
    return lanes


def _matrix_entries(
    *,
    repo_root: Path,
    output_root: Path,
    matrix_id: str,
    manifest: dict[str, Any],
    tools: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    suite_root = repo_root / runner.SUITE_ROOT
    fixtures = manifest.get("fixtures")
    lanes = manifest.get("comparisonLanes")
    if not isinstance(fixtures, list) or not fixtures:
        raise ContractError("suite manifest fixtures must be a non-empty array")
    if not isinstance(lanes, list) or not lanes:
        raise ContractError("suite manifest comparisonLanes must be a non-empty array")

    entries: list[dict[str, Any]] = []
    for fixture_entry in fixtures:
        if not isinstance(fixture_entry, dict):
            raise ContractError("suite manifest fixture entry must be an object")
        fixture_id = runner.require_nonempty_string(
            fixture_entry.get("id"), "fixture.id"
        )
        fixture_path = runner.ensure_inside(
            suite_root,
            suite_root
            / runner.require_nonempty_string(
                fixture_entry.get("path"), f"fixture path for {fixture_id}"
            ),
            "fixture manifest",
        )
        fixture = runner.load_json(fixture_path, f"{fixture_id} fixture manifest")
        fixture_version = fixture.get("version")
        if not isinstance(fixture_version, int) or fixture_version < 1:
            raise ContractError(f"fixture {fixture_id} version must be a positive integer")

        for lane_entry in lanes:
            if not isinstance(lane_entry, dict):
                raise ContractError("suite manifest lane entry must be an object")
            lane_id = runner.require_nonempty_string(lane_entry.get("id"), "lane.id")
            run_id = f"{matrix_id}-{fixture_id}-{lane_id}"
            if not runner.RUN_ID_PATTERN.fullmatch(run_id):
                raise ContractError(
                    f"generated run ID violates the run contract: {run_id}"
                )
            run_dir = output_root / fixture_id / lane_id / run_id
            entries.append(
                {
                    "fixture": {"id": fixture_id, "version": fixture_version},
                    "lane": {"id": lane_id},
                    "runId": run_id,
                    "runDir": run_dir.relative_to(output_root).as_posix(),
                    "tool": tools[lane_id],
                }
            )
    return entries


def _remove_empty_parents(path: Path, stop: Path) -> None:
    current = path
    stop = stop.resolve()
    while current.exists() and current.resolve() != stop:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def prepare_matrix(
    *,
    repo_root: Path,
    output_root: Path,
    matrix_id: str,
    lane_tools: dict[str, dict[str, str]],
) -> Path:
    repo_root = repo_root.resolve()
    output_root = output_root.resolve()
    matrix_id = _require_matrix_id(matrix_id)

    suite_errors = runner.validate_fixture_suite(repo_root)
    if suite_errors:
        preview = "; ".join(suite_errors[:5])
        raise ContractError(f"fixture suite is invalid: {preview}")

    suite_root = repo_root / runner.SUITE_ROOT
    manifest = runner.load_json(suite_root / "manifest.json", "suite manifest")
    lanes = manifest.get("comparisonLanes")
    if not isinstance(lanes, list):
        raise ContractError("suite manifest comparisonLanes must be an array")
    lane_ids = [
        runner.require_nonempty_string(entry.get("id"), "lane.id")
        for entry in lanes
        if isinstance(entry, dict)
    ]
    if len(lane_ids) != len(lanes) or len(set(lane_ids)) != len(lane_ids):
        raise ContractError("suite manifest comparison lanes must be unique objects")
    tools = _normalize_lane_tools(lane_tools, lane_ids)

    entries = _matrix_entries(
        repo_root=repo_root,
        output_root=output_root,
        matrix_id=matrix_id,
        manifest=manifest,
        tools=tools,
    )
    matrix_dir = output_root / "matrices" / matrix_id
    matrix_path = matrix_dir / "matrix.json"
    if matrix_dir.exists():
        raise ContractError(f"benchmark matrix already exists: {matrix_dir}")
    collisions = [
        entry["runDir"]
        for entry in entries
        if (output_root / entry["runDir"]).exists()
    ]
    if collisions:
        raise ContractError(
            "benchmark run already exists before matrix preparation: "
            + ", ".join(collisions)
        )

    created_runs: list[Path] = []
    try:
        shared_suite: dict[str, Any] | None = None
        shared_lane_harness: dict[str, Any] | None = None
        for entry in entries:
            run_dir = runner.prepare_run(
                repo_root=repo_root,
                output_root=output_root,
                fixture_id=entry["fixture"]["id"],
                lane_id=entry["lane"]["id"],
                run_id=entry["runId"],
                tool=entry["tool"],
            )
            created_runs.append(run_dir)
            run = runner.load_json(run_dir / "run.json", "prepared run")
            if shared_suite is None:
                shared_suite = run["suite"]
                shared_lane_harness = run["harness"]
            elif run.get("suite") != shared_suite or run.get("harness") != shared_lane_harness:
                raise ContractError(
                    "matrix runs do not share identical suite and lane-harness provenance"
                )

        if shared_suite is None or shared_lane_harness is None:
            raise ContractError("benchmark matrix contains no runs")
        receipt = {
            "schemaVersion": MATRIX_SCHEMA_VERSION,
            "matrixId": matrix_id,
            "status": "prepared",
            "createdAt": runner.utc_now(),
            "suite": shared_suite,
            "harness": {
                "laneHarness": shared_lane_harness,
                "matrixHarness": {
                    "script": str(SCRIPT_PATH.relative_to(Path(__file__).resolve().parents[1])),
                    "scriptDigest": runner.sha256(SCRIPT_PATH),
                },
            },
            "tools": tools,
            "runs": [
                {
                    "fixture": entry["fixture"],
                    "lane": entry["lane"],
                    "runId": entry["runId"],
                    "runDir": entry["runDir"],
                }
                for entry in entries
            ],
        }
        runner.atomic_write_json(matrix_path, receipt)
        return matrix_path
    except Exception:
        for run_dir in reversed(created_runs):
            shutil.rmtree(run_dir, ignore_errors=True)
            _remove_empty_parents(run_dir.parent, output_root)
        shutil.rmtree(matrix_dir, ignore_errors=True)
        _remove_empty_parents(matrix_dir.parent, output_root)
        if output_root.exists():
            _remove_empty_parents(output_root, output_root.parent)
        raise


def _matrix_status(statuses: Counter[str]) -> str:
    total = sum(statuses.values())
    if total == 0:
        raise ContractError("benchmark matrix contains no runs")
    if statuses.get("failed"):
        return "failed"
    if statuses.get("complete") == total:
        return "complete"
    if statuses.get("prepared") == total:
        return "prepared"
    return "active"


def _find_repo_root(matrix_path: Path, explicit_root: Path | None) -> Path:
    if explicit_root is not None:
        root = explicit_root.resolve()
        if not (root / runner.SUITE_ROOT / "manifest.json").is_file():
            raise ContractError(f"repository root has no benchmark suite: {root}")
        return root
    for candidate in matrix_path.parents:
        if (candidate / runner.SUITE_ROOT / "manifest.json").is_file():
            return candidate
    raise ContractError(
        "cannot infer repository root from matrix path; provide --root"
    )


def validate_matrix(
    matrix_path: Path,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    matrix_path = matrix_path.resolve()
    receipt = runner.load_json(matrix_path, "benchmark matrix")
    if receipt.get("schemaVersion") != MATRIX_SCHEMA_VERSION:
        raise ContractError(
            f"benchmark matrix schemaVersion must be {MATRIX_SCHEMA_VERSION}"
        )
    matrix_id = _require_matrix_id(receipt.get("matrixId"))
    repo_root = _find_repo_root(matrix_path, repo_root)
    output_root = matrix_path.parents[2]
    expected_matrix_path = output_root / "matrices" / matrix_id / "matrix.json"
    if matrix_path != expected_matrix_path:
        raise ContractError("benchmark matrix path does not match its output root and ID")

    suite_errors = runner.validate_fixture_suite(repo_root)
    if suite_errors:
        raise ContractError(f"fixture suite is invalid: {'; '.join(suite_errors[:5])}")
    manifest = runner.load_json(
        repo_root / runner.SUITE_ROOT / "manifest.json",
        "suite manifest",
    )
    lane_entries = manifest.get("comparisonLanes")
    if not isinstance(lane_entries, list):
        raise ContractError("suite manifest comparisonLanes must be an array")
    lane_ids = [
        runner.require_nonempty_string(entry.get("id"), "lane.id")
        for entry in lane_entries
        if isinstance(entry, dict)
    ]
    tools = _normalize_lane_tools(receipt.get("tools"), lane_ids)
    expected_entries = _matrix_entries(
        repo_root=repo_root,
        output_root=output_root,
        matrix_id=matrix_id,
        manifest=manifest,
        tools=tools,
    )
    expected_by_pair = {
        (entry["fixture"]["id"], entry["lane"]["id"]): entry
        for entry in expected_entries
    }

    runs = receipt.get("runs")
    if not isinstance(runs, list):
        raise ContractError("benchmark matrix runs must be an array")
    actual_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in runs:
        if not isinstance(entry, dict):
            raise ContractError("benchmark matrix run entry must be an object")
        fixture = entry.get("fixture")
        lane = entry.get("lane")
        if not isinstance(fixture, dict) or not isinstance(lane, dict):
            raise ContractError("benchmark matrix run fixture and lane must be objects")
        pair = (fixture.get("id"), lane.get("id"))
        if pair in actual_by_pair:
            raise ContractError(f"benchmark matrix repeats fixture/lane pair: {pair}")
        actual_by_pair[pair] = entry
    if set(actual_by_pair) != set(expected_by_pair):
        raise ContractError(
            "benchmark matrix does not cover the frozen fixture/lane matrix exactly"
        )

    shared_suite = receipt.get("suite")
    harness = receipt.get("harness")
    if not isinstance(harness, dict) or not isinstance(harness.get("laneHarness"), dict):
        raise ContractError("benchmark matrix harness receipt is invalid")
    statuses: Counter[str] = Counter()
    for pair, expected in expected_by_pair.items():
        entry = actual_by_pair[pair]
        for key in ("fixture", "lane", "runId", "runDir"):
            if entry.get(key) != expected.get(key):
                raise ContractError(
                    f"benchmark matrix run {pair} does not match the frozen plan: {key}"
                )
        run_dir = runner.ensure_inside(
            output_root,
            output_root / entry["runDir"],
            "matrix run",
        )
        if not run_dir.is_dir():
            raise ContractError(f"benchmark matrix run is missing: {entry['runDir']}")
        run = runner.load_json(run_dir / "run.json", "matrix run manifest")
        if run.get("runId") != entry["runId"]:
            raise ContractError(f"benchmark matrix run {pair} does not match its run ID")
        run_fixture = run.get("fixture")
        if not isinstance(run_fixture, dict) or {
            "id": run_fixture.get("id"),
            "version": run_fixture.get("version"),
        } != entry["fixture"]:
            raise ContractError(f"benchmark matrix run {pair} does not match its fixture")
        if run.get("lane", {}).get("id") != entry["lane"]["id"]:
            raise ContractError(f"benchmark matrix run {pair} does not match its lane")
        if run.get("tool") != tools[entry["lane"]["id"]]:
            raise ContractError(f"benchmark matrix run {pair} does not match its tool")
        if run.get("suite") != shared_suite:
            raise ContractError(f"benchmark matrix run {pair} has different suite provenance")
        if run.get("harness") != harness["laneHarness"]:
            raise ContractError(f"benchmark matrix run {pair} has different harness provenance")
        runner.validate_run(run_dir)
        status = run.get("status")
        if not isinstance(status, str):
            raise ContractError(f"benchmark matrix run {pair} has no status")
        statuses[status] += 1

    return {
        "schemaVersion": MATRIX_SCHEMA_VERSION,
        "matrixId": matrix_id,
        "status": _matrix_status(statuses),
        "runCount": sum(statuses.values()),
        "runStatuses": dict(sorted(statuses.items())),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare and validate the complete Milestone 0 fixture-by-lane matrix."
    )
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    prepare = subparsers.add_parser(
        "prepare",
        help="Transactionally prepare all frozen fixture and lane combinations.",
    )
    prepare.add_argument("--root", type=Path, default=Path.cwd())
    prepare.add_argument("--output-root", type=Path, default=runner.DEFAULT_OUTPUT_ROOT)
    prepare.add_argument("--matrix-id", required=True)
    prepare.add_argument("--lane-tools", type=Path, required=True)

    validate = subparsers.add_parser(
        "validate",
        help="Validate matrix coverage, shared provenance and every run receipt.",
    )
    validate.add_argument("--matrix", type=Path, required=True)
    validate.add_argument("--root", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command_name == "prepare":
            output_root = args.output_root
            if not output_root.is_absolute():
                output_root = args.root / output_root
            path = prepare_matrix(
                repo_root=args.root,
                output_root=output_root,
                matrix_id=args.matrix_id,
                lane_tools=load_lane_tools(args.lane_tools),
            )
            print(path)
            return 0
        if args.command_name == "validate":
            print(
                json.dumps(
                    validate_matrix(args.matrix, repo_root=args.root),
                    sort_keys=True,
                )
            )
            return 0
    except ContractError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
