#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Sequence


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[1]
BENCHMARK_PATH = SCRIPT_PATH.with_name("run_boundary_benchmark.py")
MATRIX_PATH = SCRIPT_PATH.with_name("run_boundary_benchmark_matrix.py")
SUMMARY_SCHEMA_VERSION = 1
ALL = "all"
DEFAULT_RUN_TIMEOUT_SECONDS = 360
TIMEOUT_EXIT_CODE = 124


def _load_module(name: str, path: Path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


benchmark = _load_module("run_boundary_benchmark_for_matrix_generation", BENCHMARK_PATH)
matrix = _load_module("run_boundary_benchmark_matrix_for_generation", MATRIX_PATH)
ContractError = benchmark.ContractError
RevisionResolver = Callable[[Path], str]
RunExecutor = Callable[[Path, Sequence[str]], int]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _require_directory(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise ContractError(f"{label} must be a regular directory: {path}")
    return path.resolve()


def _require_revision(value: Any, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{7,64}", value):
        raise ContractError(f"{label} must be an exact hexadecimal revision")
    return value


def _require_model(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError("comparison generation requires an explicit model")
    model = value.strip()
    if model.lower() == "auto":
        raise ContractError(
            "comparison generation requires an explicit model; auto is only admissible for capability probing"
        )
    return model


def _require_run_timeout(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ContractError("run timeout must be a positive integer number of seconds")
    return value


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def git_revision(root: Path) -> str:
    root = _require_directory(root, "revision root")
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise ContractError(f"cannot resolve git revision for {root}: {message}")
    return _require_revision(
        completed.stdout.strip(), f"resolved revision for {root}"
    )


def _frontmatter_version(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ContractError(f"Design Studio skill manifest is missing or unsafe: {path}")
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ContractError("Design Studio skill manifest has no frontmatter")
    closing = text.find("\n---\n", 4)
    if closing < 0:
        raise ContractError("Design Studio skill manifest frontmatter is not closed")
    frontmatter = text[4:closing]
    matches = re.findall(r"(?m)^version:\s*([^\s#]+)\s*$", frontmatter)
    if len(matches) != 1:
        raise ContractError("Design Studio skill manifest must declare one version")
    return matches[0]


def _impeccable_version(root: Path) -> str:
    package = benchmark.load_json(root / "package.json", "Impeccable package")
    if package.get("name") != "impeccable":
        raise ContractError("Impeccable package name is invalid")
    return _require_text(package.get("version"), "Impeccable package version")


def _verify_revision(
    root: Path,
    expected: str,
    *,
    label: str,
    revision_resolver: RevisionResolver,
) -> str:
    expected = _require_revision(expected, f"{label} revision")
    actual = revision_resolver(root)
    if not isinstance(actual, str) or actual != expected:
        raise ContractError(
            f"{label} revision mismatch: expected {expected!r}, resolved {actual!r}"
        )
    return expected


def build_lane_tools(
    *,
    repo_root: Path,
    impeccable_root: Path,
    design_revision: str,
    impeccable_revision: str,
    revision_resolver: RevisionResolver = git_revision,
) -> dict[str, dict[str, str]]:
    repo_root = _require_directory(repo_root, "repository root")
    impeccable_root = _require_directory(impeccable_root, "Impeccable root")
    design_revision = _verify_revision(
        repo_root,
        design_revision,
        label="Design Studio",
        revision_resolver=revision_resolver,
    )
    impeccable_revision = _verify_revision(
        impeccable_root,
        impeccable_revision,
        label="Impeccable",
        revision_resolver=revision_resolver,
    )
    design_version = _frontmatter_version(
        repo_root / "skills" / "design-studio" / "SKILL.md"
    )
    impeccable_version = _impeccable_version(impeccable_root)
    design_source = f"George-RD/design-studio@{design_revision}"
    impeccable_source = f"pbakaus/impeccable@{impeccable_revision}"
    return {
        "impeccable-alone": {
            "name": "impeccable",
            "version": impeccable_version,
            "source": impeccable_source,
        },
        "design-studio-current": {
            "name": "design-studio",
            "version": design_version,
            "source": design_source,
        },
        "design-studio-impeccable": {
            "name": "design-studio+impeccable",
            "version": f"{design_version}+{impeccable_version}",
            "source": f"{design_source} + {impeccable_source}",
        },
    }


def _manifest(repo_root: Path) -> dict[str, Any]:
    return benchmark.load_json(
        repo_root / benchmark.SUITE_ROOT / "manifest.json",
        "suite manifest",
    )


def _selection_ids(repo_root: Path) -> tuple[list[str], list[str]]:
    manifest = _manifest(repo_root)
    fixture_entries = manifest.get("fixtures")
    lane_entries = manifest.get("comparisonLanes")
    if not isinstance(fixture_entries, list) or not isinstance(lane_entries, list):
        raise ContractError("suite manifest fixtures and comparisonLanes must be arrays")
    fixtures = [
        benchmark.require_nonempty_string(entry.get("id"), "fixture.id")
        for entry in fixture_entries
        if isinstance(entry, dict)
    ]
    lanes = [
        benchmark.require_nonempty_string(entry.get("id"), "lane.id")
        for entry in lane_entries
        if isinstance(entry, dict)
    ]
    if len(fixtures) != len(fixture_entries) or len(lanes) != len(lane_entries):
        raise ContractError("suite manifest contains invalid fixture or lane entries")
    return fixtures, lanes


def validate_selection(
    repo_root: Path,
    fixture_id: str,
    lane_id: str,
) -> tuple[str, str]:
    fixtures, lanes = _selection_ids(repo_root)
    if fixture_id != ALL and fixture_id not in fixtures:
        raise ContractError(
            f"fixture selection must be one of {fixtures + [ALL]}; got {fixture_id!r}"
        )
    if lane_id != ALL and lane_id not in lanes:
        raise ContractError(
            f"lane selection must be one of {lanes + [ALL]}; got {lane_id!r}"
        )
    return fixture_id, lane_id


def _selected_runs(
    receipt: dict[str, Any],
    fixture_id: str,
    lane_id: str,
) -> list[dict[str, Any]]:
    runs = receipt.get("runs")
    if not isinstance(runs, list):
        raise ContractError("benchmark matrix runs must be an array")
    selected: list[dict[str, Any]] = []
    for entry in runs:
        if not isinstance(entry, dict):
            raise ContractError("benchmark matrix contains a non-object run entry")
        fixture = entry.get("fixture")
        lane = entry.get("lane")
        if not isinstance(fixture, dict) or not isinstance(lane, dict):
            raise ContractError("benchmark matrix run has no fixture or lane identity")
        if fixture_id != ALL and fixture.get("id") != fixture_id:
            continue
        if lane_id != ALL and lane.get("id") != lane_id:
            continue
        selected.append(entry)
    if not selected:
        raise ContractError("matrix selection resolved to no runs")
    return selected


def build_lane_command(
    *,
    repo_root: Path,
    impeccable_root: Path,
    run_dir: Path,
    design_revision: str,
    impeccable_revision: str,
    copilot_bin: str,
    copilot_version: str,
    model: str,
    node_bin: str,
    run_timeout_seconds: int = DEFAULT_RUN_TIMEOUT_SECONDS,
) -> list[str]:
    model = _require_model(model)
    run_timeout_seconds = _require_run_timeout(run_timeout_seconds)
    values = {
        "copilot_bin": copilot_bin,
        "copilot_version": copilot_version,
        "node_bin": node_bin,
    }
    for label, value in values.items():
        _require_text(value, label)

    lane_script = repo_root / "scripts" / "run_copilot_comparison_lane.py"
    if lane_script.is_symlink() or not lane_script.is_file():
        raise ContractError(f"Copilot lane runner is missing or unsafe: {lane_script}")
    deadline_script = repo_root / "scripts" / "run_with_deadline.py"
    if deadline_script.is_symlink() or not deadline_script.is_file():
        raise ContractError(
            f"comparison deadline runner is missing or unsafe: {deadline_script}"
        )

    lane_command = [
        sys.executable,
        str(lane_script.resolve()),
        "--repo-root",
        str(repo_root.resolve()),
        "--impeccable-root",
        str(impeccable_root.resolve()),
        "--run-dir",
        str(run_dir.resolve()),
        "--design-revision",
        design_revision,
        "--impeccable-revision",
        impeccable_revision,
        "--copilot-bin",
        copilot_bin,
        "--copilot-version",
        copilot_version,
        "--model",
        model,
        "--node-bin",
        node_bin,
    ]
    return [
        sys.executable,
        str(deadline_script.resolve()),
        "--timeout-seconds",
        str(run_timeout_seconds),
        "--",
        *lane_command,
    ]


def _relative(output_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(output_root.resolve()).as_posix()
    except (OSError, ValueError) as exc:
        raise ContractError(f"artifact escapes matrix output root: {path}") from exc


def _generation_report(run_dir: Path) -> tuple[Path, dict[str, Any]]:
    path = run_dir / "evidence" / "generation-report.json"
    if path.is_symlink() or not path.is_file():
        raise ContractError(f"generation report is missing or unsafe: {path}")
    return path, benchmark.load_json(path, "generation report")


def _validate_role_models(
    run: dict[str, Any],
    report: dict[str, Any],
    expected_model: str,
) -> str:
    lane = run.get("lane")
    lane_id = lane.get("id") if isinstance(lane, dict) else None
    expected_roles = (
        {"impeccable"}
        if lane_id == "impeccable-alone"
        else {"explore", "direct", "builder"}
    )
    roles = report.get("roles")
    if not isinstance(roles, dict) or set(roles) != expected_roles:
        got = sorted(roles) if isinstance(roles, dict) else None
        raise ContractError(
            "generation report does not contain the exact expected role model receipts: "
            f"expected={sorted(expected_roles)}, got={got}"
        )
    for role in sorted(expected_roles):
        receipt = roles.get(role)
        if not isinstance(receipt, dict) or receipt.get("status") != "passed":
            raise ContractError(f"generation role {role!r} has no passed receipt")
        requested = receipt.get("requestedModel")
        resolved = receipt.get("resolvedModel")
        if requested != expected_model or resolved != expected_model:
            raise ContractError(
                f"generation role {role!r} requested {requested!r} and resolved {resolved!r}; "
                f"the frozen comparison requires {expected_model!r}"
            )
    return expected_model


def _validate_generated_run(
    run_dir: Path,
    expected_run_id: str,
    expected_model: str,
) -> tuple[Path, dict[str, Any], list[str], str]:
    run = benchmark.load_json(run_dir / "run.json", "generated run manifest")
    if run.get("runId") != expected_run_id:
        raise ContractError("generated run manifest does not match the selected run ID")
    if run.get("status") != "awaiting-evidence":
        raise ContractError(
            "successful generation must leave the benchmark run awaiting-evidence; "
            f"got {run.get('status')!r}"
        )
    report_path, report = _generation_report(run_dir)
    if report.get("runId") != expected_run_id or report.get("status") != "generated":
        raise ContractError("generation report does not prove a generated selected run")
    resolved_model = _validate_role_models(run, report, expected_model)
    fixture = benchmark.load_json(
        run_dir / "input" / "fixture.json", "generated run fixture"
    )
    output_contract = fixture.get("outputContract")
    if not isinstance(output_contract, dict):
        raise ContractError("generated run fixture has no output contract")
    entrypoint = benchmark.require_nonempty_string(
        output_contract.get("entrypoint"), "output entrypoint"
    )
    output_root = run_dir / "output"
    output_path = benchmark.ensure_inside(
        output_root,
        output_root / entrypoint,
        "generated output entrypoint",
    )
    if not output_path.is_file() or output_path.is_symlink():
        raise ContractError(f"generated output entrypoint is missing or unsafe: {entrypoint}")
    files = sorted(benchmark.tree_manifest(output_root))
    if not files:
        raise ContractError("generated output tree is empty")
    benchmark.validate_run(run_dir)
    return report_path, report, files, resolved_model


def _terminalize_validation_failure(run_dir: Path, message: str) -> None:
    run = benchmark.load_run(run_dir)
    status = run.get("status")
    if status == "failed":
        benchmark.validate_run(run_dir)
        return
    if status != "awaiting-evidence":
        raise ContractError(
            "cannot terminalize generation validation from run state "
            f"{status!r}"
        )

    failed_at = utc_now()
    run["status"] = "failed"
    run["generationValidationFailedAt"] = failed_at
    benchmark.save_run(run_dir, run)
    artifact_paths = ["evidence/execution.json", "output"]
    report_path = run_dir / "evidence" / "generation-report.json"
    if report_path.is_file() and not report_path.is_symlink():
        artifact_paths.append("evidence/generation-report.json")
    benchmark.append_event(
        run_dir,
        step="generation-validation",
        status="failed",
        message=message,
        artifact_paths=artifact_paths,
    )
    benchmark.validate_run(run_dir)


def _classify_nonzero(
    run_dir: Path,
    *,
    exit_code: int,
    run_timeout_seconds: int,
) -> tuple[str, Path | None, str]:
    report_path = run_dir / "evidence" / "generation-report.json"
    if report_path.is_file() and not report_path.is_symlink():
        report = benchmark.load_json(report_path, "failed generation report")
        status = "blocked" if report.get("status") == "blocked" else "failed"
        error = report.get("error")
        message = error.get("message") if isinstance(error, dict) else None
        if not isinstance(message, str) or not message.strip():
            message = f"lane command reported {report.get('status')!r}"
        return status, report_path, message.strip()
    if exit_code == TIMEOUT_EXIT_CODE:
        return (
            "failed",
            None,
            f"lane exceeded the shared {run_timeout_seconds}-second elapsed budget",
        )
    return "failed", None, "lane command exited without a generation report"


def _summary_status(statuses: Counter[str]) -> str:
    if statuses.get("failed"):
        return "failed"
    if statuses.get("blocked"):
        return "blocked"
    if statuses.get("not-run"):
        return "partial"
    if statuses and statuses.get("generated") == sum(statuses.values()):
        return "generated"
    return "active"


def _write_summary(path: Path, summary: dict[str, Any]) -> None:
    summary["runStatuses"] = dict(
        sorted(Counter(entry["status"] for entry in summary["runs"]).items())
    )
    summary["status"] = _summary_status(Counter(summary["runStatuses"]))
    summary["updatedAt"] = utc_now()
    benchmark.atomic_write_json(path, summary)


def _terminalize_selected_awaiting_runs(
    *,
    output_root: Path,
    summary: dict[str, Any],
    message: str,
) -> None:
    for result in summary["runs"]:
        run_dir = benchmark.ensure_inside(
            output_root,
            output_root / result["runDir"],
            "selected matrix run",
        )
        run = benchmark.load_run(run_dir)
        if run.get("status") != "awaiting-evidence":
            continue
        _terminalize_validation_failure(run_dir, message)
        result["status"] = "failed"
        result["error"] = message


def generate_matrix(
    *,
    repo_root: Path,
    output_root: Path,
    matrix_id: str,
    impeccable_root: Path,
    design_revision: str,
    impeccable_revision: str,
    fixture_id: str,
    lane_id: str,
    model: str,
    copilot_bin: str = "copilot",
    copilot_version: str = "1.0.74",
    node_bin: str = "node",
    continue_on_error: bool = False,
    run_timeout_seconds: int = DEFAULT_RUN_TIMEOUT_SECONDS,
    revision_resolver: RevisionResolver = git_revision,
    run_executor: RunExecutor | None = None,
) -> dict[str, Any]:
    repo_root = _require_directory(repo_root, "repository root")
    impeccable_root = _require_directory(impeccable_root, "Impeccable root")
    output_root = output_root.resolve()
    model = _require_model(model)
    run_timeout_seconds = _require_run_timeout(run_timeout_seconds)
    fixture_id, lane_id = validate_selection(repo_root, fixture_id, lane_id)
    tools = build_lane_tools(
        repo_root=repo_root,
        impeccable_root=impeccable_root,
        design_revision=design_revision,
        impeccable_revision=impeccable_revision,
        revision_resolver=revision_resolver,
    )
    matrix_path = matrix.prepare_matrix(
        repo_root=repo_root,
        output_root=output_root,
        matrix_id=matrix_id,
        lane_tools=tools,
    )
    receipt = benchmark.load_json(matrix_path, "prepared benchmark matrix")
    selected = _selected_runs(receipt, fixture_id, lane_id)
    matrix_dir = matrix_path.parent
    summary_path = matrix_dir / "generation.json"
    if summary_path.exists() or summary_path.is_symlink():
        raise ContractError(f"matrix generation summary already exists: {summary_path}")
    executor = run_executor or benchmark.execute_run
    summary: dict[str, Any] = {
        "schemaVersion": SUMMARY_SCHEMA_VERSION,
        "matrixId": matrix_id,
        "status": "active",
        "startedAt": utc_now(),
        "updatedAt": None,
        "finishedAt": None,
        "matrix": _relative(output_root, matrix_path),
        "model": model,
        "executionPolicy": {
            "maximumElapsedSecondsPerRun": run_timeout_seconds,
            "timeoutExitCode": TIMEOUT_EXIT_CODE,
            "deadlineRunner": "scripts/run_with_deadline.py",
        },
        "selection": {
            "fixture": fixture_id,
            "lane": lane_id,
            "continueOnError": bool(continue_on_error),
        },
        "selectedPairs": [
            [entry["fixture"]["id"], entry["lane"]["id"]]
            for entry in selected
        ],
        "revisions": {
            "designStudio": design_revision,
            "impeccable": impeccable_revision,
        },
        "tools": tools,
        "runs": [
            {
                "runId": entry["runId"],
                "fixture": entry["fixture"]["id"],
                "lane": entry["lane"]["id"],
                "runDir": entry["runDir"],
                "maximumElapsedSeconds": run_timeout_seconds,
                "status": "not-run",
                "exitCode": None,
                "execution": None,
                "generationReport": None,
                "resolvedModel": None,
                "outputFiles": [],
                "error": None,
            }
            for entry in selected
        ],
        "runStatuses": {"not-run": len(selected)},
        "matrixValidation": None,
    }
    _write_summary(summary_path, summary)

    for index, (planned, result) in enumerate(zip(selected, summary["runs"])):
        run_dir = benchmark.ensure_inside(
            output_root,
            output_root / planned["runDir"],
            "selected matrix run",
        )
        command = build_lane_command(
            repo_root=repo_root,
            impeccable_root=impeccable_root,
            run_dir=run_dir,
            design_revision=design_revision,
            impeccable_revision=impeccable_revision,
            copilot_bin=copilot_bin,
            copilot_version=copilot_version,
            model=model,
            node_bin=node_bin,
            run_timeout_seconds=run_timeout_seconds,
        )
        result["status"] = "running"
        _write_summary(summary_path, summary)
        try:
            exit_code = executor(run_dir, command)
            if isinstance(exit_code, bool) or not isinstance(exit_code, int):
                raise ContractError("benchmark run executor returned a non-integer exit code")
            result["exitCode"] = exit_code
            execution_path = run_dir / "evidence" / "execution.json"
            if execution_path.is_file() and not execution_path.is_symlink():
                result["execution"] = _relative(output_root, execution_path)
            if exit_code == 0:
                report_path, _report, output_files, resolved_model = (
                    _validate_generated_run(run_dir, planned["runId"], model)
                )
                result["status"] = "generated"
                result["generationReport"] = _relative(output_root, report_path)
                result["resolvedModel"] = resolved_model
                result["outputFiles"] = output_files
            else:
                status, report_path, message = _classify_nonzero(
                    run_dir,
                    exit_code=exit_code,
                    run_timeout_seconds=run_timeout_seconds,
                )
                result["status"] = status
                result["generationReport"] = (
                    _relative(output_root, report_path) if report_path else None
                )
                result["error"] = message
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            if result.get("exitCode") == 0:
                try:
                    _terminalize_validation_failure(
                        run_dir,
                        "Zero-exit generation failed validation: " + error,
                    )
                except Exception as terminal_error:
                    error += (
                        "; terminalization failed: "
                        f"{type(terminal_error).__name__}: {terminal_error}"
                    )
            result["status"] = "failed"
            result["error"] = error
        _write_summary(summary_path, summary)
        if result["status"] in {"blocked", "failed"} and not continue_on_error:
            for remaining in summary["runs"][index + 1 :]:
                remaining["status"] = "not-run"
                remaining["error"] = "not attempted after the first blocked or failed run"
            break

    try:
        summary["matrixValidation"] = matrix.validate_matrix(
            matrix_path, repo_root=repo_root
        )
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        summary["matrixValidation"] = {"status": "failed", "error": error}
        terminal_message = "Matrix validation failed after generation: " + error
        try:
            _terminalize_selected_awaiting_runs(
                output_root=output_root,
                summary=summary,
                message=terminal_message,
            )
        except Exception as terminal_error:
            terminal_message += (
                "; terminalization failed: "
                f"{type(terminal_error).__name__}: {terminal_error}"
            )
        if not any(entry["status"] == "failed" for entry in summary["runs"]):
            summary["runs"][0]["status"] = "failed"
            summary["runs"][0]["error"] = terminal_message

    summary["finishedAt"] = utc_now()
    _write_summary(summary_path, summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare the frozen Milestone 0 matrix and execute an explicit subset "
            "through the Copilot lane runner."
        )
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--output-root", type=Path, default=benchmark.DEFAULT_OUTPUT_ROOT
    )
    parser.add_argument("--matrix-id", required=True)
    parser.add_argument("--impeccable-root", type=Path, required=True)
    parser.add_argument("--design-revision", required=True)
    parser.add_argument("--impeccable-revision", required=True)
    parser.add_argument("--fixture", default="marketing-surface")
    parser.add_argument("--lane", default="design-studio-current")
    parser.add_argument("--copilot-bin", default="copilot")
    parser.add_argument("--copilot-version", default="1.0.74")
    parser.add_argument("--model", required=True)
    parser.add_argument("--node-bin", default="node")
    parser.add_argument(
        "--run-timeout-seconds",
        type=int,
        default=DEFAULT_RUN_TIMEOUT_SECONDS,
    )
    parser.add_argument("--continue-on-error", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_root = args.output_root
    if not output_root.is_absolute():
        output_root = args.root / output_root
    try:
        summary = generate_matrix(
            repo_root=args.root,
            output_root=output_root,
            matrix_id=args.matrix_id,
            impeccable_root=args.impeccable_root,
            design_revision=args.design_revision,
            impeccable_revision=args.impeccable_revision,
            fixture_id=args.fixture,
            lane_id=args.lane,
            model=args.model,
            copilot_bin=args.copilot_bin,
            copilot_version=args.copilot_version,
            node_bin=args.node_bin,
            continue_on_error=args.continue_on_error,
            run_timeout_seconds=args.run_timeout_seconds,
        )
    except ContractError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(summary, sort_keys=True))
    if summary["status"] == "generated":
        return 0
    if summary["status"] == "blocked":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
