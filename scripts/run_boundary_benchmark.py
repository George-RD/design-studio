#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Sequence


SUITE_ROOT = Path("benchmarks") / "milestone-0"
DEFAULT_OUTPUT_ROOT = Path("harness-output") / "benchmarks" / "milestone-0"
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
RUN_SCHEMA_VERSION = 1
EVIDENCE_KEYS = {
    "schemaVersion",
    "taskClarity",
    "originality",
    "functionalDefects",
    "tokenCost",
    "toolCost",
    "failedSteps",
    "recoveryEffort",
    "acceptanceChecks",
}
COST_STATUSES = {"measured", "estimated", "unavailable"}
CHECK_STATUSES = {"pass", "fail", "blocked"}
DEFECT_SEVERITIES = {"primary", "advisory"}


class ContractError(RuntimeError):
    """Raised when benchmark evidence would violate the frozen run contract."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path, label: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise ContractError(f"{label or path} is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"{label or path} contains invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{label or path} must contain a JSON object")
    return value


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(payload)
    temporary.replace(path)


def read_events(run_dir: Path) -> list[dict[str, Any]]:
    events_path = run_dir / "events.jsonl"
    if not events_path.exists():
        return []

    events: list[dict[str, Any]] = []
    for expected_sequence, raw_line in enumerate(events_path.read_text().splitlines(), start=1):
        if not raw_line.strip():
            raise ContractError(f"event journal contains a blank line at sequence {expected_sequence}")
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ContractError(
                f"event journal contains invalid JSON at sequence {expected_sequence}: {exc}"
            ) from exc
        if not isinstance(event, dict):
            raise ContractError(f"event journal entry {expected_sequence} must be an object")
        if event.get("sequence") != expected_sequence:
            raise ContractError(
                f"event sequence is invalid: expected {expected_sequence}, "
                f"got {event.get('sequence')}"
            )
        for key in ("at", "step", "status", "message"):
            if not isinstance(event.get(key), str) or not event[key].strip():
                raise ContractError(
                    f"event journal entry {expected_sequence}.{key} must be a non-empty string"
                )
        artifact_paths = event.get("artifactPaths")
        if not isinstance(artifact_paths, list) or any(
            not isinstance(path, str) or not path for path in artifact_paths
        ):
            raise ContractError(
                f"event journal entry {expected_sequence}.artifactPaths must be an array of strings"
            )
        events.append(event)
    return events


def append_event(
    run_dir: Path,
    *,
    step: str,
    status: str,
    message: str,
    artifact_paths: Sequence[str] = (),
) -> None:
    events_path = run_dir / "events.jsonl"
    sequence = len(read_events(run_dir)) + 1
    event = {
        "sequence": sequence,
        "at": utc_now(),
        "step": step,
        "status": status,
        "artifactPaths": list(artifact_paths),
        "message": message,
    }
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def validate_fixture_suite(repo_root: Path) -> list[str]:
    validator_path = Path(__file__).resolve().with_name("validate_benchmark_fixtures.py")
    spec = importlib.util.spec_from_file_location("validate_benchmark_fixtures_for_run", validator_path)
    if spec is None or spec.loader is None:
        raise ContractError(f"cannot load fixture validator: {validator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate(repo_root)


def tree_manifest(root: Path) -> dict[str, str]:
    if not root.is_dir():
        raise ContractError(f"tree is missing: {root}")
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ContractError(f"benchmark trees may not contain symlinks: {path}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = sha256(path)
    return files


def ensure_inside(root: Path, candidate: Path, label: str) -> Path:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    if not resolved_candidate.is_relative_to(resolved_root):
        raise ContractError(f"{label} escapes its allowed root: {candidate}")
    return resolved_candidate


def find_fixture(manifest: dict[str, Any], fixture_id: str) -> dict[str, Any]:
    for entry in manifest.get("fixtures", []):
        if isinstance(entry, dict) and entry.get("id") == fixture_id:
            return entry
    raise ContractError(f"unknown fixture: {fixture_id}")


def find_lane(manifest: dict[str, Any], lane_id: str) -> dict[str, Any]:
    for entry in manifest.get("comparisonLanes", []):
        if isinstance(entry, dict) and entry.get("id") == lane_id:
            return entry
    raise ContractError(f"unknown comparison lane: {lane_id}")


def require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value


def prepare_run(
    *,
    repo_root: Path,
    output_root: Path,
    fixture_id: str,
    lane_id: str,
    run_id: str,
    tool: dict[str, Any],
) -> Path:
    repo_root = repo_root.resolve()
    output_root = output_root.resolve()
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ContractError(
            "run ID must start with an alphanumeric character and contain only "
            "letters, numbers, dot, underscore or hyphen (maximum 64 characters)"
        )

    suite_errors = validate_fixture_suite(repo_root)
    if suite_errors:
        preview = "; ".join(suite_errors[:5])
        suffix = "" if len(suite_errors) <= 5 else f"; plus {len(suite_errors) - 5} more"
        raise ContractError(f"fixture suite is invalid: {preview}{suffix}")

    suite_root = repo_root / SUITE_ROOT
    manifest = load_json(suite_root / "manifest.json", "suite manifest")
    fixture_entry = find_fixture(manifest, fixture_id)
    lane_entry = find_lane(manifest, lane_id)

    tool_record = {
        "name": require_nonempty_string(tool.get("name"), "tool.name"),
        "version": require_nonempty_string(tool.get("version"), "tool.version"),
        "source": require_nonempty_string(tool.get("source"), "tool.source"),
    }

    fixture_manifest_relative = require_nonempty_string(fixture_entry.get("path"), "fixture path")
    fixture_manifest_path = ensure_inside(
        suite_root,
        suite_root / fixture_manifest_relative,
        "fixture manifest",
    )
    fixture_dir = fixture_manifest_path.parent
    fixture = load_json(fixture_manifest_path, f"{fixture_id} fixture manifest")

    lane_dir = output_root / fixture_id / lane_id
    run_dir = lane_dir / run_id
    if run_dir.exists():
        raise ContractError(f"benchmark run already exists: {run_dir}")

    lane_dir.mkdir(parents=True, exist_ok=True)
    temporary_dir = Path(tempfile.mkdtemp(prefix=f".{run_id}-", dir=lane_dir))
    try:
        input_dir = temporary_dir / "input"
        work_dir = temporary_dir / "work"
        output_dir = temporary_dir / "output"
        evidence_dir = temporary_dir / "evidence"
        shutil.copytree(fixture_dir, input_dir)
        work_dir.mkdir()
        output_dir.mkdir()
        evidence_dir.mkdir()

        baseline = fixture.get("baseline", [])
        if not isinstance(baseline, list):
            raise ContractError(f"{fixture_id} baseline must be an array")
        for relative_value in baseline:
            relative = Path(require_nonempty_string(relative_value, "baseline path"))
            source = ensure_inside(input_dir, input_dir / relative, "baseline source")
            if not source.is_file():
                raise ContractError(f"baseline source is missing: {relative_value}")
            target_relative = Path(*relative.parts[1:]) if relative.parts and relative.parts[0] == "input" else relative
            if not target_relative.parts:
                raise ContractError(f"baseline target is invalid: {relative_value}")
            target = ensure_inside(work_dir, work_dir / target_relative, "baseline target")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        input_manifest = tree_manifest(input_dir)
        prepared_at = utc_now()
        run = {
            "schemaVersion": RUN_SCHEMA_VERSION,
            "runId": run_id,
            "status": "prepared",
            "preparedAt": prepared_at,
            "suite": {
                "id": manifest.get("suite"),
                "version": manifest.get("version"),
                "frozenAt": manifest.get("frozenAt"),
                "lockAlgorithm": "sha256",
                "lockDigest": sha256(suite_root / "fixture-lock.json"),
            },
            "fixture": {
                "id": fixture_id,
                "version": fixture.get("version"),
                "kind": fixture.get("kind"),
                "title": fixture.get("title"),
            },
            "lane": {
                "id": lane_id,
                "purpose": lane_entry.get("purpose"),
            },
            "tool": tool_record,
            "inputManifest": {
                "algorithm": "sha256",
                "files": input_manifest,
            },
            "paths": {
                "input": "input",
                "work": "work",
                "output": "output",
                "evidence": "evidence",
                "events": "events.jsonl",
            },
            "execution": None,
            "result": None,
        }
        atomic_write_json(temporary_dir / "run.json", run)
        append_event(
            temporary_dir,
            step="prepare",
            status="prepared",
            message="Frozen fixture copied into an isolated benchmark run.",
            artifact_paths=["run.json", "input", "work"],
        )
        temporary_dir.replace(run_dir)
    except BaseException:
        shutil.rmtree(temporary_dir, ignore_errors=True)
        raise

    return run_dir


def load_run(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    run = load_json(run_dir / "run.json", "run manifest")
    if run.get("schemaVersion") != RUN_SCHEMA_VERSION:
        raise ContractError(
            f"unsupported run schema: {run.get('schemaVersion')}; expected {RUN_SCHEMA_VERSION}"
        )
    return run


def validate_event_state(run_dir: Path, run: dict[str, Any]) -> list[dict[str, Any]]:
    events = read_events(run_dir)
    if not events:
        raise ContractError("event journal must contain at least one event")

    expected_last_status = {
        "prepared": "prepared",
        "running": "started",
        "awaiting-evidence": "succeeded",
        "failed": "failed",
        "complete": "completed",
    }.get(run.get("status"))
    if expected_last_status is None:
        raise ContractError(f"unknown run status: {run.get('status')}")
    if events[-1].get("status") != expected_last_status:
        raise ContractError(
            "event journal does not match run state: "
            f"status {run.get('status')} requires final event {expected_last_status}, "
            f"got {events[-1].get('status')}"
        )
    return events


def save_run(run_dir: Path, run: dict[str, Any]) -> None:
    atomic_write_json(run_dir / "run.json", run)


def validate_run_input(run_dir: Path, run: dict[str, Any]) -> None:
    expected = run.get("inputManifest", {}).get("files")
    if not isinstance(expected, dict):
        raise ContractError("run manifest has no valid input tree receipt")
    actual = tree_manifest(run_dir / "input")
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        unexpected = sorted(set(actual) - set(expected))
        changed = sorted(
            path for path in set(expected) & set(actual) if expected[path] != actual[path]
        )
        details = []
        if missing:
            details.append(f"missing={missing}")
        if unexpected:
            details.append(f"unexpected={unexpected}")
        if changed:
            details.append(f"changed={changed}")
        raise ContractError(f"input tree changed after prepare: {', '.join(details)}")


def execution_environment(run_dir: Path, run: dict[str, Any]) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "DESIGN_BENCHMARK_RUN_DIR": str(run_dir),
            "DESIGN_BENCHMARK_INPUT_DIR": str(run_dir / "input"),
            "DESIGN_BENCHMARK_WORK_DIR": str(run_dir / "work"),
            "DESIGN_BENCHMARK_OUTPUT_DIR": str(run_dir / "output"),
            "DESIGN_BENCHMARK_EVIDENCE_DIR": str(run_dir / "evidence"),
            "DESIGN_BENCHMARK_BRIEF": str(run_dir / "input" / "brief.md"),
            "DESIGN_BENCHMARK_ACCEPTANCE": str(run_dir / "input" / "acceptance.json"),
            "DESIGN_BENCHMARK_FIXTURE": run["fixture"]["id"],
            "DESIGN_BENCHMARK_LANE": run["lane"]["id"],
            "DESIGN_BENCHMARK_RUN_ID": run["runId"],
        }
    )
    return environment


def execute_run(run_dir: Path, command: Sequence[str]) -> int:
    run_dir = run_dir.resolve()
    run = load_run(run_dir)
    if run.get("status") != "prepared":
        raise ContractError(
            f"run must be prepared before execution; current status is {run.get('status')}"
        )
    validate_event_state(run_dir, run)
    validate_run_input(run_dir, run)

    argv = [str(part) for part in command]
    if not argv or any(not part for part in argv):
        raise ContractError("execution command must contain at least one non-empty argument")
    if any((run_dir / "output").iterdir()):
        raise ContractError("output directory must be empty before execution")

    started_at = utc_now()
    started_monotonic = time.monotonic()
    run["status"] = "running"
    run["executionStartedAt"] = started_at
    save_run(run_dir, run)
    append_event(
        run_dir,
        step="execute",
        status="started",
        message="Lane command started.",
        artifact_paths=["evidence/stdout.log", "evidence/stderr.log"],
    )

    stdout_path = run_dir / "evidence" / "stdout.log"
    stderr_path = run_dir / "evidence" / "stderr.log"
    exit_code: int | None = None
    launch_error: str | None = None

    try:
        with stdout_path.open("wb") as stdout_handle, stderr_path.open("wb") as stderr_handle:
            completed = subprocess.run(
                argv,
                cwd=run_dir / "work",
                env=execution_environment(run_dir, run),
                stdout=stdout_handle,
                stderr=stderr_handle,
                check=False,
            )
        exit_code = completed.returncode
    except BaseException as exc:
        launch_error = f"{type(exc).__name__}: {exc}"

    finished_at = utc_now()
    elapsed_seconds = round(time.monotonic() - started_monotonic, 6)
    execution = {
        "schemaVersion": 1,
        "command": argv,
        "workingDirectory": "work",
        "startedAt": started_at,
        "finishedAt": finished_at,
        "elapsedSeconds": elapsed_seconds,
        "exitCode": exit_code,
        "launchError": launch_error,
        "stdout": "evidence/stdout.log",
        "stderr": "evidence/stderr.log",
        "environmentContract": [
            "DESIGN_BENCHMARK_RUN_DIR",
            "DESIGN_BENCHMARK_INPUT_DIR",
            "DESIGN_BENCHMARK_WORK_DIR",
            "DESIGN_BENCHMARK_OUTPUT_DIR",
            "DESIGN_BENCHMARK_EVIDENCE_DIR",
            "DESIGN_BENCHMARK_BRIEF",
            "DESIGN_BENCHMARK_ACCEPTANCE",
            "DESIGN_BENCHMARK_FIXTURE",
            "DESIGN_BENCHMARK_LANE",
            "DESIGN_BENCHMARK_RUN_ID",
        ],
    }
    atomic_write_json(run_dir / "evidence" / "execution.json", execution)
    run["execution"] = "evidence/execution.json"
    run["executionFinishedAt"] = finished_at

    if launch_error is not None:
        run["status"] = "failed"
        save_run(run_dir, run)
        append_event(
            run_dir,
            step="execute",
            status="failed",
            message=f"Lane command could not start: {launch_error}",
            artifact_paths=["evidence/execution.json", "evidence/stdout.log", "evidence/stderr.log"],
        )
        raise ContractError(f"lane command could not start: {launch_error}")

    if exit_code == 0:
        run["status"] = "awaiting-evidence"
        save_run(run_dir, run)
        append_event(
            run_dir,
            step="execute",
            status="succeeded",
            message="Lane command exited successfully; completion evidence is still required.",
            artifact_paths=["evidence/execution.json", "output"],
        )
    else:
        run["status"] = "failed"
        save_run(run_dir, run)
        append_event(
            run_dir,
            step="execute",
            status="failed",
            message=f"Lane command exited with status {exit_code}.",
            artifact_paths=["evidence/execution.json", "evidence/stdout.log", "evidence/stderr.log", "output"],
        )

    return int(exit_code)


def validate_score(value: Any, label: str, minimum: int, maximum: int) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    score = value.get("score")
    if isinstance(score, bool) or not isinstance(score, int) or not minimum <= score <= maximum:
        raise ContractError(f"{label}.score must be an integer from {minimum} to {maximum}")
    require_nonempty_string(value.get("evidence"), f"{label}.evidence")
    return value


def validate_token_cost(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("tokenCost must be an object")
    status = value.get("status")
    if status not in COST_STATUSES:
        raise ContractError(f"tokenCost.status must be one of {sorted(COST_STATUSES)}")
    input_tokens = value.get("inputTokens")
    output_tokens = value.get("outputTokens")
    if status == "unavailable":
        if input_tokens is not None or output_tokens is not None:
            raise ContractError("unavailable tokenCost must use null token counts")
        require_nonempty_string(value.get("reason"), "tokenCost.reason")
    else:
        for token_value, label in ((input_tokens, "inputTokens"), (output_tokens, "outputTokens")):
            if isinstance(token_value, bool) or not isinstance(token_value, int) or token_value < 0:
                raise ContractError(f"tokenCost.{label} must be a non-negative integer")
    return value


def validate_tool_cost(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("toolCost must be an object")
    status = value.get("status")
    if status not in COST_STATUSES:
        raise ContractError(f"toolCost.status must be one of {sorted(COST_STATUSES)}")
    amount = value.get("amount")
    currency = value.get("currency")
    if status == "unavailable":
        if amount is not None or currency is not None:
            raise ContractError("unavailable toolCost must use null amount and currency")
        require_nonempty_string(value.get("reason"), "toolCost.reason")
    else:
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0:
            raise ContractError("toolCost.amount must be a non-negative number")
        require_nonempty_string(currency, "toolCost.currency")
    return value


def validate_evidence(run_dir: Path, evidence: dict[str, Any]) -> dict[str, Any]:
    if "outputPreference" in evidence:
        raise ContractError("outputPreference is comparison-level evidence and may not be set by a lane")
    missing = sorted(EVIDENCE_KEYS - set(evidence))
    if missing:
        raise ContractError(f"evidence is missing keys: {missing}")
    if evidence.get("schemaVersion") != 1:
        raise ContractError("evidence.schemaVersion must be 1")

    validate_score(evidence.get("taskClarity"), "taskClarity", 1, 5)
    validate_score(evidence.get("originality"), "originality", 1, 10)
    validate_token_cost(evidence.get("tokenCost"))
    validate_tool_cost(evidence.get("toolCost"))

    defects = evidence.get("functionalDefects")
    if not isinstance(defects, list):
        raise ContractError("functionalDefects must be an array")
    defect_ids: set[str] = set()
    for index, defect in enumerate(defects):
        if not isinstance(defect, dict):
            raise ContractError(f"functionalDefects[{index}] must be an object")
        defect_id = require_nonempty_string(defect.get("id"), f"functionalDefects[{index}].id")
        if defect_id in defect_ids:
            raise ContractError(f"duplicate functional defect id: {defect_id}")
        defect_ids.add(defect_id)
        if defect.get("severity") not in DEFECT_SEVERITIES:
            raise ContractError(
                f"functionalDefects[{index}].severity must be one of {sorted(DEFECT_SEVERITIES)}"
            )
        require_nonempty_string(defect.get("evidence"), f"functionalDefects[{index}].evidence")

    failed_steps = evidence.get("failedSteps")
    if not isinstance(failed_steps, list):
        raise ContractError("failedSteps must be an array")
    for index, failed_step in enumerate(failed_steps):
        if not isinstance(failed_step, dict):
            raise ContractError(f"failedSteps[{index}] must be an object")
        require_nonempty_string(failed_step.get("step"), f"failedSteps[{index}].step")
        require_nonempty_string(failed_step.get("evidence"), f"failedSteps[{index}].evidence")

    recovery = evidence.get("recoveryEffort")
    if not isinstance(recovery, dict):
        raise ContractError("recoveryEffort must be an object")
    minutes = recovery.get("minutes")
    if isinstance(minutes, bool) or not isinstance(minutes, (int, float)) or minutes < 0:
        raise ContractError("recoveryEffort.minutes must be a non-negative number")
    actions = recovery.get("actions")
    if not isinstance(actions, list) or any(not isinstance(action, str) or not action.strip() for action in actions):
        raise ContractError("recoveryEffort.actions must be an array of non-empty strings")

    fixture = load_json(run_dir / "input" / "fixture.json", "run fixture manifest")
    acceptance_path = run_dir / "input" / require_nonempty_string(
        fixture.get("acceptance"), "fixture.acceptance"
    )
    acceptance = load_json(acceptance_path, "run acceptance contract")
    expected_checks = {
        check.get("id")
        for check in acceptance.get("functionalChecks", [])
        if isinstance(check, dict) and isinstance(check.get("id"), str)
    }
    checks = evidence.get("acceptanceChecks")
    if not isinstance(checks, list):
        raise ContractError("acceptanceChecks must be an array")
    observed_checks: set[str] = set()
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            raise ContractError(f"acceptanceChecks[{index}] must be an object")
        check_id = require_nonempty_string(check.get("id"), f"acceptanceChecks[{index}].id")
        if check_id in observed_checks:
            raise ContractError(f"duplicate acceptance check id: {check_id}")
        observed_checks.add(check_id)
        if check.get("status") not in CHECK_STATUSES:
            raise ContractError(
                f"acceptanceChecks[{index}].status must be one of {sorted(CHECK_STATUSES)}"
            )
        require_nonempty_string(check.get("evidence"), f"acceptanceChecks[{index}].evidence")
    if observed_checks != expected_checks:
        raise ContractError(
            "acceptanceChecks must cover the frozen contract exactly; "
            f"expected {sorted(expected_checks)}, got {sorted(observed_checks)}"
        )

    output_contract = fixture.get("outputContract")
    if not isinstance(output_contract, dict):
        raise ContractError("fixture.outputContract must be an object")
    entrypoint = Path(require_nonempty_string(output_contract.get("entrypoint"), "output entrypoint"))
    output_root = run_dir / "output"
    output_path = ensure_inside(output_root, output_root / entrypoint, "output entrypoint")
    if not output_path.is_file():
        raise ContractError(f"required output entrypoint is missing: {entrypoint.as_posix()}")

    return evidence


def complete_run(run_dir: Path, evidence_path: Path) -> Path:
    run_dir = run_dir.resolve()
    evidence_path = evidence_path.resolve()
    run = load_run(run_dir)
    if run.get("status") != "awaiting-evidence":
        raise ContractError(
            "run must be awaiting-evidence before completion; "
            f"current status is {run.get('status')}"
        )
    validate_event_state(run_dir, run)
    validate_run_input(run_dir, run)

    execution = load_json(run_dir / "evidence" / "execution.json", "execution receipt")
    if execution.get("exitCode") != 0 or execution.get("launchError") is not None:
        raise ContractError("only a successful execution can be completed")

    evidence = validate_evidence(run_dir, load_json(evidence_path, "lane evidence"))
    raw_evidence_path = run_dir / "evidence" / "lane-evidence.json"
    atomic_write_json(raw_evidence_path, evidence)
    result = {
        **evidence,
        "runId": run["runId"],
        "suite": run["suite"],
        "fixture": run["fixture"],
        "lane": run["lane"],
        "tool": run["tool"],
        "command": execution["command"],
        "elapsedSeconds": execution["elapsedSeconds"],
        "rawEvidence": "evidence/lane-evidence.json",
        "outputPreference": {
            "status": "comparison-level",
            "reason": "pending blind comparison",
        },
        "output": {
            "root": "output",
            "entrypoint": load_json(run_dir / "input" / "fixture.json")["outputContract"]["entrypoint"],
            "treeManifest": {
                "algorithm": "sha256",
                "files": tree_manifest(run_dir / "output"),
            },
        },
        "completedAt": utc_now(),
    }
    result_path = run_dir / "evidence" / "result.json"
    atomic_write_json(result_path, result)

    run["status"] = "complete"
    run["result"] = "evidence/result.json"
    run["completedAt"] = result["completedAt"]
    save_run(run_dir, run)
    append_event(
        run_dir,
        step="complete",
        status="completed",
        message="Lane evidence and output contract validated.",
        artifact_paths=["evidence/lane-evidence.json", "evidence/result.json", "output"],
    )
    return result_path


def validate_run(run_dir: Path) -> None:
    run_dir = run_dir.resolve()
    run = load_run(run_dir)
    validate_event_state(run_dir, run)
    validate_run_input(run_dir, run)
    status = run.get("status")

    execution: dict[str, Any] | None = None
    if status in {"awaiting-evidence", "failed", "complete"}:
        execution = load_json(run_dir / "evidence" / "execution.json", "execution receipt")
        if run.get("execution") != "evidence/execution.json":
            raise ContractError("run manifest does not point to the execution receipt")

    if status == "complete":
        if execution is None or execution.get("exitCode") != 0 or execution.get("launchError") is not None:
            raise ContractError("completed run does not have a successful execution receipt")

        result = load_json(run_dir / "evidence" / "result.json", "result receipt")
        raw_evidence = load_json(
            run_dir / "evidence" / "lane-evidence.json",
            "preserved lane evidence",
        )
        validate_evidence(run_dir, raw_evidence)

        if run.get("result") != "evidence/result.json":
            raise ContractError("run manifest does not point to the result receipt")
        if result.get("rawEvidence") != "evidence/lane-evidence.json":
            raise ContractError("result receipt does not point to preserved lane evidence")
        for key in EVIDENCE_KEYS:
            if result.get(key) != raw_evidence.get(key):
                raise ContractError(f"result receipt differs from preserved lane evidence: {key}")

        expected_metadata = {
            "runId": run.get("runId"),
            "suite": run.get("suite"),
            "fixture": run.get("fixture"),
            "lane": run.get("lane"),
            "tool": run.get("tool"),
            "command": execution.get("command"),
            "elapsedSeconds": execution.get("elapsedSeconds"),
        }
        for key, expected in expected_metadata.items():
            if result.get(key) != expected:
                raise ContractError(f"result receipt {key} does not match run evidence")

        if result.get("outputPreference") != {
            "status": "comparison-level",
            "reason": "pending blind comparison",
        }:
            raise ContractError("result receipt has an invalid comparison preference state")

        output = result.get("output")
        if not isinstance(output, dict):
            raise ContractError("result receipt output must be an object")
        receipt_manifest = output.get("treeManifest")
        if not isinstance(receipt_manifest, dict) or receipt_manifest.get("algorithm") != "sha256":
            raise ContractError("result receipt has no valid output tree manifest")
        expected_output_files = receipt_manifest.get("files")
        if not isinstance(expected_output_files, dict):
            raise ContractError("result receipt output tree files must be an object")
        actual_output_files = tree_manifest(run_dir / "output")
        if actual_output_files != expected_output_files:
            missing = sorted(set(expected_output_files) - set(actual_output_files))
            unexpected = sorted(set(actual_output_files) - set(expected_output_files))
            changed = sorted(
                path
                for path in set(expected_output_files) & set(actual_output_files)
                if expected_output_files[path] != actual_output_files[path]
            )
            raise ContractError(
                "output tree changed after completion: "
                f"missing={missing}, unexpected={unexpected}, changed={changed}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare, execute and complete frozen Milestone 0 comparison runs."
    )
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    prepare = subparsers.add_parser("prepare", help="Create an isolated run from a frozen fixture.")
    prepare.add_argument("--root", type=Path, default=Path.cwd())
    prepare.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    prepare.add_argument("--fixture", required=True)
    prepare.add_argument("--lane", required=True)
    prepare.add_argument("--run-id", required=True)
    prepare.add_argument("--tool-name", required=True)
    prepare.add_argument("--tool-version", required=True)
    prepare.add_argument("--tool-source", required=True)

    execute = subparsers.add_parser("execute", help="Run one lane command inside a prepared run.")
    execute.add_argument("--run-dir", type=Path, required=True)
    execute.add_argument("lane_command", nargs=argparse.REMAINDER)

    complete = subparsers.add_parser(
        "complete", help="Validate lane evidence and mark a successful run complete."
    )
    complete.add_argument("--run-dir", type=Path, required=True)
    complete.add_argument("--evidence", type=Path, required=True)

    validate = subparsers.add_parser("validate", help="Validate an existing run receipt.")
    validate.add_argument("--run-dir", type=Path, required=True)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command_name == "prepare":
            output_root = args.output_root
            if not output_root.is_absolute():
                output_root = args.root / output_root
            run_dir = prepare_run(
                repo_root=args.root,
                output_root=output_root,
                fixture_id=args.fixture,
                lane_id=args.lane,
                run_id=args.run_id,
                tool={
                    "name": args.tool_name,
                    "version": args.tool_version,
                    "source": args.tool_source,
                },
            )
            print(run_dir)
            return 0

        if args.command_name == "execute":
            command = list(args.lane_command)
            if command and command[0] == "--":
                command = command[1:]
            return execute_run(args.run_dir, command)

        if args.command_name == "complete":
            result_path = complete_run(args.run_dir, args.evidence)
            print(result_path)
            return 0

        if args.command_name == "validate":
            validate_run(args.run_dir)
            print("Benchmark run contract passed.")
            return 0
    except ContractError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
