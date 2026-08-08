#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import shutil
import stat
import sys
from typing import Any, Callable, Sequence


SCRIPT_PATH = Path(__file__).resolve()
CONTRACT_PATH = SCRIPT_PATH.with_name("run_copilot_comparison.py")
CAPABILITY_PATH = SCRIPT_PATH.with_name("run_copilot_cli_agent_capability.py")
REPORT_SCHEMA_VERSION = 1
AVAILABLE_TOOLS = "view,create"
ALLOW_TOOLS = "read,write"
DENY_TOOLS = "shell,url,memory"


def _load_module(name: str, path: Path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


contract = _load_module("run_copilot_comparison_for_lane", CONTRACT_PATH)
capability = _load_module("run_copilot_cli_agent_capability_for_lane", CAPABILITY_PATH)
ContractError = contract.ContractError


class CapabilityBlocked(ContractError):
    """Raised when account, model or infrastructure policy blocks a valid run."""


@dataclass(frozen=True)
class RoleInvocation:
    role: str
    run_dir: Path
    workspace: Path
    evidence_dir: Path
    output_name: str
    prompt: str


RoleRunner = Callable[[RoleInvocation], dict[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ContractError(f"JSON destination directory is unsafe: {path.parent}")
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists() or temporary.is_symlink():
        raise ContractError(f"temporary JSON destination already exists: {temporary}")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink():
            raise ContractError(f"JSON destination must not be a symlink: {path}")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"{label} is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be a JSON object")
    return value


def _require_regular_directory(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise ContractError(f"{label} must be a regular directory: {path}")
    return path


def _regular_files(root: Path, label: str) -> set[str]:
    _require_regular_directory(root, label)
    files: set[str] = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ContractError(f"{label} contains a symlink: {relative}")
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ContractError(f"{label} contains an unsupported file type: {relative}")
        files.add(relative)
    return files


def _require_exact_files(root: Path, expected: set[str], label: str) -> list[str]:
    actual = _regular_files(root, label)
    if actual != expected:
        raise ContractError(
            f"{label} file boundary changed: "
            f"missing={sorted(expected - actual)}, unexpected={sorted(actual - expected)}"
        )
    return sorted(actual)


def _sha256(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ContractError(f"file is missing or unsafe: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_text_exclusive(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.exists() or path.is_symlink():
        raise ContractError(f"destination already exists or is unsafe: {path}")
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())


def _write_packet(workspace: Path, packet: dict[str, Any]) -> str:
    packet_path = workspace / "packet.json"
    _write_json(packet_path, packet)
    return _sha256(packet_path)


def _operation_path(arguments: Any) -> Any:
    if not isinstance(arguments, dict):
        return None
    for key in ("path", "filePath", "file_path", "filename"):
        value = arguments.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _workspace_relative_path(workspace: Path, value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    try:
        return candidate.resolve(strict=False).relative_to(workspace.resolve()).as_posix()
    except (OSError, ValueError):
        return None


def _resolved_model(events: list[dict[str, Any]], role: str) -> str:
    models: list[str] = []
    for event in events:
        data = event.get("data")
        if not isinstance(data, dict):
            continue
        for key in ("chosenModel", "resolvedModel", "model"):
            value = data.get(key)
            if (
                isinstance(value, str)
                and value.strip()
                and value.strip().lower() != "auto"
            ):
                models.append(value.strip())
    unique = list(dict.fromkeys(models))
    if not unique:
        raise ContractError(f"{role} Copilot evidence contains no resolved model")
    if len(unique) != 1:
        raise ContractError(f"{role} Copilot evidence records different models: {unique}")
    return unique[0]


def _validate_tool_receipt(
    *,
    role: str,
    events: list[dict[str, Any]],
    workspace: Path,
    output_name: str,
) -> dict[str, Any]:
    read_tools = {"read", "view"}
    write_tools = {"create", "edit", "apply_patch"}
    starts: dict[str, dict[str, Any]] = {}
    completed: set[str] = set()
    successful: list[dict[str, Any]] = []

    for event_index, event in enumerate(events):
        event_type = event.get("type")
        if event_type not in {"tool.execution_start", "tool.execution_complete"}:
            continue
        data = event.get("data")
        if not isinstance(data, dict):
            raise ContractError(f"{role} tool event {event_index} has no data object")
        call_id = data.get("toolCallId")
        if not isinstance(call_id, str) or not call_id.strip():
            raise ContractError(f"{role} tool event {event_index} has no toolCallId")
        call_id = call_id.strip()

        if event_type == "tool.execution_start":
            if call_id in starts:
                raise ContractError(f"{role} repeats tool call ID {call_id}")
            tool = str(data.get("toolName", "")).strip().lower()
            if tool in read_tools:
                operation = "read"
            elif tool in write_tools:
                operation = "write"
            else:
                raise ContractError(f"{role} used unsupported tool {tool!r}")
            relative = _workspace_relative_path(
                workspace,
                _operation_path(data.get("arguments")),
            )
            if relative is None:
                raise ContractError(f"{role} tool call {call_id} escaped its workspace")
            allowed_path = "packet.json" if operation == "read" else output_name
            if relative != allowed_path:
                raise ContractError(
                    f"{role} attempted unauthorized {operation}: {relative}"
                )
            starts[call_id] = {
                "id": call_id,
                "tool": tool,
                "operation": operation,
                "path": relative,
                "startIndex": event_index,
            }
            continue

        if call_id not in starts:
            raise ContractError(f"{role} completed unknown tool call {call_id}")
        if call_id in completed:
            raise ContractError(f"{role} completed tool call {call_id} more than once")
        start = starts[call_id]
        complete_tool = str(data.get("toolName", "")).strip().lower()
        if complete_tool and complete_tool != start["tool"]:
            raise ContractError(f"{role} changed tool for call {call_id}")
        if data.get("success") is not True:
            raise ContractError(f"{role} tool call {call_id} did not succeed")
        completed.add(call_id)
        successful.append({**start, "completeIndex": event_index})

    incomplete = sorted(set(starts) - completed)
    if incomplete:
        raise ContractError(f"{role} has incomplete tool calls: {incomplete}")
    if not successful:
        raise ContractError(f"{role} evidence contains no successful tool calls")

    reads = {call["path"] for call in successful if call["operation"] == "read"}
    writes = {call["path"] for call in successful if call["operation"] == "write"}
    if reads != {"packet.json"} or writes != {output_name}:
        raise ContractError(
            f"{role} tool receipt violates the role boundary: "
            f"reads={sorted(reads)}, writes={sorted(writes)}"
        )
    read_completions = [
        call["completeIndex"] for call in successful if call["operation"] == "read"
    ]
    write_starts = [
        call["startIndex"] for call in successful if call["operation"] == "write"
    ]
    if not read_completions or not write_starts or max(read_completions) >= min(write_starts):
        raise ContractError(f"{role} did not complete packet read before writing")
    return {
        "read": sorted(reads),
        "written": sorted(writes),
        "calls": successful,
    }


def _write_trusted_workspace_config(home: Path, workspace: Path) -> Path:
    if home.is_symlink():
        raise ContractError(f"Copilot home must not be a symlink: {home}")
    home.mkdir(parents=True, exist_ok=False)
    config = home / "config.json"
    _write_json(config, {"trustedFolders": [str(workspace.resolve())]})
    return config


def _scrub_token_tree(root: Path, token: str) -> list[str]:
    if not token or not root.exists():
        return []
    encoded = token.encode("utf-8")
    replacement = b"<redacted-token>"
    scrubbed: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ContractError(f"credential scan found a symlink: {path}")
        if not path.is_file():
            continue
        data = path.read_bytes()
        if encoded not in data:
            continue
        path.write_bytes(data.replace(encoded, replacement))
        scrubbed.append(path.relative_to(root).as_posix())
    return scrubbed


class CopilotRoleRunner:
    def __init__(
        self,
        *,
        token: str,
        copilot_bin: str = "copilot",
        copilot_version: str = capability.DEFAULT_COPILOT_VERSION,
        model: str = "auto",
        command_runner: Callable[..., Any] = capability.default_command_runner,
    ) -> None:
        if not isinstance(token, str) or not token.strip():
            raise CapabilityBlocked("GITHUB_TOKEN is required for Copilot lane generation")
        self.token = token
        self.copilot_bin = copilot_bin
        self.copilot_version = copilot_version
        self.model = model
        self.command_runner = command_runner

    def __call__(self, invocation: RoleInvocation) -> dict[str, Any]:
        workspace = invocation.workspace.resolve()
        evidence_dir = invocation.evidence_dir
        _require_regular_directory(workspace, f"{invocation.role} workspace")
        if evidence_dir.exists() or evidence_dir.is_symlink():
            raise ContractError(
                f"{invocation.role} evidence directory already exists: {evidence_dir}"
            )
        evidence_dir.mkdir(parents=True, exist_ok=False)
        copilot_home = evidence_dir / "copilot-home"
        trusted_config = _write_trusted_workspace_config(copilot_home, workspace)
        command = capability.build_role_command(
            copilot_bin=self.copilot_bin,
            cwd=workspace,
            prompt=invocation.prompt,
            model=self.model,
            available_tools=AVAILABLE_TOOLS,
            allow_tools=ALLOW_TOOLS,
            deny_tools=DENY_TOOLS,
        )
        environment = capability.build_role_environment(self.token, copilot_home)
        _write_json(
            evidence_dir / "command.json",
            {
                "argv": command,
                "copilotVersion": self.copilot_version,
                "workingDirectory": str(workspace),
                "environmentContract": sorted(environment),
                "trustedWorkspaceConfig": str(trusted_config),
            },
        )

        kwargs: dict[str, Any] = {"cwd": workspace, "env": environment}
        try:
            parameters = inspect.signature(self.command_runner).parameters
        except (TypeError, ValueError):
            parameters = {}
        if "timeout_seconds" in parameters:
            kwargs["timeout_seconds"] = capability.COMMAND_TIMEOUT_SECONDS
        outcome = self.command_runner(command, **kwargs)
        if not isinstance(outcome, capability.CommandOutcome):
            raise ContractError(
                f"{invocation.role} command runner returned an invalid outcome"
            )
        try:
            capability.ensure_command_output_bounds(outcome)
            capability.safe_persist_output(
                evidence_dir / "stdout.jsonl", outcome.stdout, self.token
            )
            capability.safe_persist_output(
                evidence_dir / "stderr.log", outcome.stderr, self.token
            )
        except capability.ContractError as exc:
            raise ContractError(str(exc)) from exc

        scrubbed = _scrub_token_tree(invocation.workspace, self.token)
        scrubbed.extend(_scrub_token_tree(evidence_dir, self.token))
        if scrubbed:
            raise ContractError(
                f"{invocation.role} attempted to persist authentication material: {scrubbed}"
            )
        if outcome.exit_code != 0:
            message = outcome.stderr.strip() or outcome.stdout.strip() or str(outcome.exit_code)
            if capability.classify_cli_failure(outcome) == "blocked":
                raise CapabilityBlocked(
                    f"{invocation.role} Copilot CLI was blocked: {message[:1000]}"
                )
            raise ContractError(
                f"{invocation.role} Copilot CLI failed: {message[:1000]}"
            )
        try:
            events = capability.parse_jsonl(
                outcome.stdout, f"{invocation.role} Copilot JSONL"
            )
        except capability.ContractError as exc:
            raise ContractError(str(exc)) from exc
        receipt = _validate_tool_receipt(
            role=invocation.role,
            events=events,
            workspace=workspace,
            output_name=invocation.output_name,
        )
        resolved_model = _resolved_model(events, invocation.role)
        result = {
            "status": "passed",
            "resolvedModel": resolved_model,
            "availableTools": AVAILABLE_TOOLS.split(","),
            "toolReceipt": receipt,
            "command": "command.json",
            "stdout": "stdout.jsonl",
            "stderr": "stderr.log",
        }
        _write_json(evidence_dir / "role-report.json", result)
        return result


def _role_prompt(role: str, output_name: str) -> str:
    if role == "explore":
        task = (
            "Create directions.json as strict JSON with exactly one top-level key, directions. "
            "directions must contain exactly three complete objects with IDs direction-1, "
            "direction-2 and direction-3 in that order."
        )
    elif role == "direct":
        task = (
            "Create design-description.md as plain Markdown using exactly the required headings "
            "from packet.json, in order, with non-empty source-free content under every heading."
        )
    elif role in {"builder", "impeccable"}:
        task = (
            "Create bundle.json as strict JSON with exactly one top-level key, files. Each file "
            "must contain exactly path and content. Include index.html and obey the packet's "
            "local-only output contract."
        )
    else:
        raise ContractError(f"unknown generation role: {role}")
    return (
        f"You are the isolated {role} role for a frozen comparison run. Read packet.json first. "
        f"{task} Read no other file and create exactly {output_name}; do not create any other "
        "file. Do not use Markdown fences around JSON. Finish only after the output exists."
    )


def _prepare_role(
    *,
    generation_root: Path,
    run_dir: Path,
    role: str,
    output_name: str,
    packet: dict[str, Any],
) -> tuple[RoleInvocation, str]:
    role_root = generation_root / "roles" / role
    if role_root.exists() or role_root.is_symlink():
        raise ContractError(f"generation role already exists: {role}")
    workspace = role_root / "workspace"
    workspace.mkdir(parents=True, exist_ok=False)
    packet_digest = _write_packet(workspace, packet)
    invocation = RoleInvocation(
        role=role,
        run_dir=run_dir,
        workspace=workspace,
        evidence_dir=role_root / "evidence",
        output_name=output_name,
        prompt=_role_prompt(role, output_name),
    )
    return invocation, packet_digest


def _invoke_role(
    *,
    generation_root: Path,
    run_dir: Path,
    role: str,
    output_name: str,
    packet: dict[str, Any],
    role_runner: RoleRunner,
) -> tuple[Path, dict[str, Any]]:
    invocation, packet_digest = _prepare_role(
        generation_root=generation_root,
        run_dir=run_dir,
        role=role,
        output_name=output_name,
        packet=packet,
    )
    result = role_runner(invocation)
    if not isinstance(result, dict) or result.get("status") != "passed":
        raise ContractError(f"{role} role did not return a passed receipt")
    _require_exact_files(
        invocation.workspace,
        {"packet.json", output_name},
        f"{role} workspace",
    )
    if _sha256(invocation.workspace / "packet.json") != packet_digest:
        raise ContractError(f"{role} changed packet.json")
    output_path = invocation.workspace / output_name
    role_receipt = {
        **result,
        "workspace": str(invocation.workspace.relative_to(run_dir)),
        "packetSha256": packet_digest,
        "output": output_name,
        "outputSha256": _sha256(output_path),
        "outputBytes": output_path.stat().st_size,
    }
    return output_path, role_receipt


def _parse_directions(path: Path) -> list[dict[str, Any]]:
    value = _load_json(path, "Visual Director exploration")
    if set(value) != {"directions"}:
        raise ContractError("directions.json must contain exactly directions")
    directions = value.get("directions")
    if not isinstance(directions, list):
        raise ContractError("directions.json directions must be an array")
    return directions


def _output_manifest(files: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "path": item["path"],
            "bytes": len(item["content"].encode("utf-8")),
            "sha256": hashlib.sha256(item["content"].encode("utf-8")).hexdigest(),
        }
        for item in files
    ]


def _publish_bundle(
    *,
    generation_root: Path,
    output_dir: Path,
    files: list[dict[str, str]],
) -> list[dict[str, Any]]:
    _require_regular_directory(output_dir, "benchmark output directory")
    if any(output_dir.iterdir()):
        raise ContractError("benchmark output directory must be empty before publication")
    staging = generation_root / "output-staging"
    if staging.exists() or staging.is_symlink():
        raise ContractError(f"output staging path already exists: {staging}")
    staging.mkdir(parents=False, exist_ok=False)
    try:
        for item in files:
            destination = staging.joinpath(*Path(item["path"]).parts)
            _write_text_exclusive(destination, item["content"])
        manifest = _output_manifest(files)
        os.replace(staging, output_dir)
        return manifest
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def _reset_output(output_dir: Path) -> None:
    if output_dir.is_symlink():
        raise ContractError(f"benchmark output directory became a symlink: {output_dir}")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)


def run_generation(
    *,
    repo_root: Path,
    impeccable_root: Path,
    run_dir: Path,
    design_revision: str,
    impeccable_revision: str,
    role_runner: RoleRunner,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    impeccable_root = impeccable_root.resolve()
    run_dir = run_dir.resolve()
    _require_regular_directory(repo_root, "repository root")
    _require_regular_directory(run_dir, "benchmark run directory")
    output_dir = _require_regular_directory(run_dir / "output", "benchmark output directory")
    evidence_dir = _require_regular_directory(run_dir / "evidence", "benchmark evidence directory")
    if any(output_dir.iterdir()):
        raise ContractError("benchmark output directory must be empty before generation")

    run = _load_json(run_dir / "run.json", "benchmark run receipt")
    if run.get("status") != "running":
        raise ContractError(
            f"benchmark run must be running during lane generation; got {run.get('status')!r}"
        )
    lane = contract.resolve_lane_contract(run_dir)
    generation_root = evidence_dir / "generation"
    report_path = evidence_dir / "generation-report.json"
    if generation_root.exists() or generation_root.is_symlink() or report_path.exists():
        raise ContractError("generation evidence already exists for this run")
    generation_root.mkdir(parents=True, exist_ok=False)

    report: dict[str, Any] = {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "runId": run.get("runId"),
        "status": "running",
        "startedAt": utc_now(),
        "lane": lane,
        "revisions": {
            "designStudio": design_revision,
            "impeccable": impeccable_revision,
        },
        "roles": {},
        "selection": None,
        "output": None,
    }
    step = "prepare"
    try:
        bundle: dict[str, Any]
        if lane["workflow"] == "design-studio":
            step = "explore"
            explore_packet = contract.build_director_packet(
                repo_root, run_dir, design_revision
            )
            directions_path, explore_receipt = _invoke_role(
                generation_root=generation_root,
                run_dir=run_dir,
                role="explore",
                output_name="directions.json",
                packet=explore_packet,
                role_runner=role_runner,
            )
            report["roles"]["explore"] = explore_receipt
            selection = contract.select_direction(
                _parse_directions(directions_path), run_dir
            )
            _write_json(generation_root / "selected-direction.json", selection)
            report["selection"] = {
                key: selection[key]
                for key in ("selectionMethod", "assignment", "assignmentSha256", "assignedIndex")
            }

            step = "direct"
            direct_packet = contract.build_direct_packet(
                repo_root,
                run_dir,
                selection["direction"],
                design_revision,
            )
            description_path, direct_receipt = _invoke_role(
                generation_root=generation_root,
                run_dir=run_dir,
                role="direct",
                output_name="design-description.md",
                packet=direct_packet,
                role_runner=role_runner,
            )
            report["roles"]["direct"] = direct_receipt
            design_description = contract.validate_design_description(
                description_path.read_text(encoding="utf-8")
            )

            step = "builder"
            builder_packet = contract.build_builder_packet(
                repo_root,
                run_dir,
                design_description,
                design_revision,
                lane["mechanicalProvider"],
            )
            bundle_path, builder_receipt = _invoke_role(
                generation_root=generation_root,
                run_dir=run_dir,
                role="builder",
                output_name="bundle.json",
                packet=builder_packet,
                role_runner=role_runner,
            )
            report["roles"]["builder"] = builder_receipt
            bundle = _load_json(bundle_path, "Builder bundle")
        elif lane["workflow"] == "impeccable":
            step = "impeccable"
            impeccable_packet = contract.build_impeccable_packet(
                impeccable_root, run_dir, impeccable_revision
            )
            bundle_path, impeccable_receipt = _invoke_role(
                generation_root=generation_root,
                run_dir=run_dir,
                role="impeccable",
                output_name="bundle.json",
                packet=impeccable_packet,
                role_runner=role_runner,
            )
            report["roles"]["impeccable"] = impeccable_receipt
            bundle = _load_json(bundle_path, "Impeccable bundle")
        else:
            raise ContractError(f"unsupported comparison workflow: {lane['workflow']}")

        step = "validate-bundle"
        validated_files = contract.validate_bundle(bundle)
        step = "publish"
        output_manifest = _publish_bundle(
            generation_root=generation_root,
            output_dir=output_dir,
            files=validated_files,
        )
        report["status"] = "generated"
        report["finishedAt"] = utc_now()
        report["output"] = {
            "directory": "output",
            "entrypoint": "index.html",
            "files": output_manifest,
        }
        _write_json(report_path, report)
        return report
    except Exception as exc:
        try:
            _reset_output(output_dir)
        except Exception as cleanup_error:
            exc = ContractError(f"{exc}; output cleanup failed: {cleanup_error}")
        status = "blocked" if isinstance(exc, CapabilityBlocked) else "failed"
        report["status"] = status
        report["finishedAt"] = utc_now()
        report["error"] = {
            "step": step,
            "kind": "capability-blocked" if status == "blocked" else "contract",
            "message": str(exc),
        }
        _write_json(report_path, report)
        if isinstance(exc, ContractError):
            raise
        raise ContractError(f"{step} failed: {type(exc).__name__}: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute one frozen Milestone 0 comparison lane through Copilot CLI."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=SCRIPT_PATH.parents[1],
    )
    parser.add_argument(
        "--impeccable-root",
        type=Path,
        default=os.environ.get("IMPECCABLE_ROOT"),
        required=os.environ.get("IMPECCABLE_ROOT") is None,
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=os.environ.get("DESIGN_BENCHMARK_RUN_DIR"),
        required=os.environ.get("DESIGN_BENCHMARK_RUN_DIR") is None,
    )
    parser.add_argument(
        "--design-revision",
        default=os.environ.get("GITHUB_SHA"),
        required=os.environ.get("GITHUB_SHA") is None,
    )
    parser.add_argument(
        "--impeccable-revision",
        default=os.environ.get("IMPECCABLE_REVISION"),
        required=os.environ.get("IMPECCABLE_REVISION") is None,
    )
    parser.add_argument("--copilot-bin", default="copilot")
    parser.add_argument(
        "--copilot-version",
        default=capability.DEFAULT_COPILOT_VERSION,
    )
    parser.add_argument("--model", default="auto")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        runner = CopilotRoleRunner(
            token=os.environ.get("GITHUB_TOKEN", ""),
            copilot_bin=args.copilot_bin,
            copilot_version=args.copilot_version,
            model=args.model,
        )
        report = run_generation(
            repo_root=args.repo_root,
            impeccable_root=args.impeccable_root,
            run_dir=args.run_dir,
            design_revision=args.design_revision,
            impeccable_revision=args.impeccable_revision,
            role_runner=runner,
        )
    except CapabilityBlocked as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, sort_keys=True))
        return 2
    except ContractError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, sort_keys=True))
        return 1
    print(
        json.dumps(
            {
                "status": report["status"],
                "runId": report["runId"],
                "lane": report["lane"]["id"],
                "report": str((args.run_dir / "evidence" / "generation-report.json").resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
