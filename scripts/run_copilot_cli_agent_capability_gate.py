#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Sequence


CORE_PATH = Path(__file__).resolve().with_name(
    "run_copilot_cli_agent_capability.py"
)
CORE_MODULE_NAME = "run_copilot_cli_agent_capability"
if CORE_MODULE_NAME in sys.modules:
    core = sys.modules[CORE_MODULE_NAME]
else:
    spec = importlib.util.spec_from_file_location(CORE_MODULE_NAME, CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load capability core from {CORE_PATH}")
    core = importlib.util.module_from_spec(spec)
    sys.modules[CORE_MODULE_NAME] = core
    spec.loader.exec_module(core)


CommandOutcome = core.CommandOutcome
ContractError = core.ContractError
CapabilityBlocked = core.CapabilityBlocked
SOURCE_CANARY = core.SOURCE_CANARY
DEFAULT_COPILOT_VERSION = core.DEFAULT_COPILOT_VERSION
DEFAULT_MODEL = "auto"


def _remember_original(attribute: str, current: Any) -> Any:
    marker = f"_design_studio_agent_gate_original_{attribute}"
    if not hasattr(core, marker):
        setattr(core, marker, current)
    return getattr(core, marker)


_BASE_WRITE_JSON = _remember_original(
    "write_json",
    core.write_json,
)
_BASE_CLASSIFIER = _remember_original(
    "classify_cli_failure",
    core.classify_cli_failure,
)
_BASE_INVOKE_ROLE = _remember_original(
    "invoke_role",
    core.invoke_role,
)
_BASE_RUN_CAPABILITY = _remember_original(
    "run_capability",
    core.run_capability,
)
_BASE_DIRECTOR_PROMPT = _remember_original(
    "director_prompt",
    core.director_prompt,
)
_BASE_BUILDER_PROMPT = _remember_original(
    "builder_prompt",
    core.builder_prompt,
)
_DIRECTOR_RETRY_ACTIVE = False


def director_prompt(brief: str) -> str:
    prompt = _BASE_DIRECTOR_PROMPT(brief)
    if not _DIRECTOR_RETRY_ACTIVE:
        return prompt
    return (
        f"{prompt}\n\n"
        "Retry after invalid structured output: write direction.json as strict JSON "
        "only, with exactly the concept, palette, layout and interaction keys. "
        "Every value must be a non-empty string. Do not add Markdown or prose."
    )


def builder_prompt() -> str:
    prompt = _BASE_BUILDER_PROMPT()
    prompt = prompt.replace(
        "- local submission prevents navigation, preserves the entered value, and reveals exact text: Capability complete",
        "- local submission prevents navigation and preserves the entered value\n"
        "- Keep the form, label, input and submit control visible after submission\n"
        "- on submit, set its textContent to exactly Capability complete, with no icon or additional text inside that region",
    )
    return prompt


def classify_cli_failure(outcome: CommandOutcome) -> str:
    text = f"{outcome.stdout}\n{outcome.stderr}".lower()
    model_blockers = (
        "model is not available",
        "model \"",
        "unsupported model",
        "no models available",
        "cannot use model",
    )
    if any(marker in text for marker in model_blockers):
        return "blocked"
    return _BASE_CLASSIFIER(outcome)


def write_json_no_follow(path: Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    parent = path.parent
    if parent.is_symlink() or not parent.is_dir():
        raise core.ContractError(f"JSON destination directory is unsafe: {parent}")
    if path.is_symlink():
        raise core.ContractError(f"JSON destination must not be a symlink: {path}")
    if path.exists() and not path.is_file():
        raise core.ContractError(f"JSON destination must be a regular file: {path}")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink():
            raise core.ContractError(
                f"JSON destination became a symlink before replacement: {path}"
            )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_trusted_workspace_config(home: Path, workspace: Path) -> Path:
    home.mkdir(parents=True, exist_ok=True)
    config_path = home / "config.json"
    if config_path.exists() or config_path.is_symlink():
        raise core.ContractError(
            f"Copilot trusted-workspace config already exists: {config_path}"
        )
    core.write_json(
        config_path,
        {"trustedFolders": [str(workspace.resolve())]},
    )
    return config_path


def _model_values(events: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for event in events:
        data = event.get("data")
        if not isinstance(data, dict):
            continue
        candidates = [
            data.get("chosenModel"),
            data.get("model"),
        ]
        for candidate in candidates:
            if (
                isinstance(candidate, str)
                and candidate.strip()
                and candidate.strip().lower() != "auto"
            ):
                values.append(candidate.strip())
    return values


def resolved_model_from_events(
    events: list[dict[str, Any]],
    role: str,
) -> str:
    values = _model_values(events)
    unique = list(dict.fromkeys(values))
    if not unique:
        raise core.ContractError(
            f"{role} Copilot evidence contains no resolved model"
        )
    if len(unique) != 1:
        raise core.ContractError(
            f"{role} Copilot evidence records different models: {unique}"
        )
    return unique[0]


def validate_resolved_models(
    models: dict[str, str],
    *,
    requested_model: str,
) -> dict[str, str]:
    expected_roles = {"director", "builder", "evaluator"}
    if set(models) != expected_roles:
        raise core.ContractError(
            "resolved-model evidence must cover director, builder and evaluator"
        )
    normalized = {
        role: core.require_text(model, f"resolved model for {role}")
        for role, model in models.items()
    }
    requested = core.require_text(requested_model, "requested model")
    if requested.lower() != "auto":
        mismatched = {
            role: model
            for role, model in normalized.items()
            if model != requested
        }
        if mismatched:
            raise core.ContractError(
                f"requested model {requested!r} was not honored by every role: "
                f"{mismatched}"
            )
    return normalized


def _workspace_relative_path(
    workspace: Path,
    value: Any,
) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    try:
        resolved = candidate.resolve(strict=False)
        relative = resolved.relative_to(workspace.resolve())
    except (OSError, ValueError):
        return None
    return relative.as_posix()


def successful_file_views(
    events: list[dict[str, Any]],
    workspace: Path,
) -> list[str]:
    starts: dict[str, str | None] = {}
    successful: set[str] = set()
    for event in events:
        event_type = event.get("type")
        data = event.get("data")
        if not isinstance(data, dict):
            continue
        call_id = data.get("toolCallId")
        if not isinstance(call_id, str) or not call_id:
            continue
        if event_type == "tool.execution_start":
            tool_name = str(data.get("toolName", "")).strip().lower()
            if tool_name not in {"read", "view"}:
                continue
            arguments = data.get("arguments")
            path_value = arguments.get("path") if isinstance(arguments, dict) else None
            starts[call_id] = _workspace_relative_path(workspace, path_value)
        elif (
            event_type == "tool.execution_complete"
            and data.get("success") is True
            and call_id in starts
        ):
            relative = starts[call_id]
            if relative is None:
                raise core.ContractError(
                    "successful Copilot file view escaped the trusted role workspace"
                )
            successful.add(relative)
    return sorted(successful)


def _role_tools(role: str) -> tuple[str, list[str]]:
    if role in {"director", "evaluator"}:
        return "create", ["create"]
    if role == "builder":
        tools = ["view", "create", "edit", "apply_patch"]
        return ",".join(tools), tools
    raise core.ContractError(f"unknown capability role: {role}")


def invoke_role(*args: Any, **kwargs: Any) -> dict[str, Any]:
    role = kwargs.get("role")
    workspace = kwargs.get("workspace")
    evidence_dir = kwargs.get("evidence_dir")
    if not isinstance(role, str):
        raise core.ContractError("capability role is missing")
    if not isinstance(workspace, Path) or not isinstance(evidence_dir, Path):
        raise core.ContractError(
            f"{role} workspace or evidence directory is invalid"
        )

    copilot_home = evidence_dir / "copilot-home" / role
    trusted_config = write_trusted_workspace_config(
        copilot_home,
        workspace,
    )
    available_tools, available_tool_list = _role_tools(role)
    delegated = dict(kwargs)
    delegated["available_tools"] = available_tools
    result = _BASE_INVOKE_ROLE(*args, **delegated)

    events = core.parse_jsonl(
        (evidence_dir / f"{role}.stdout.jsonl").read_text(
            encoding="utf-8"
        ),
        f"{role} Copilot JSONL",
    )
    resolved_model = resolved_model_from_events(events, role)
    read_files = successful_file_views(events, workspace)
    result.update(
        {
            "availableTools": available_tool_list,
            "readFiles": read_files,
            "resolvedModel": resolved_model,
            "trustedWorkspace": str(workspace.resolve()),
            "trustedWorkspaceConfig": str(
                trusted_config.relative_to(evidence_dir.parent)
            ),
        }
    )
    if role == "builder":
        result["readBaselineCss"] = "baseline.css" in read_files
    return result


def _redact_token(value: Any, token: str) -> Any:
    if not token:
        return value
    if isinstance(value, str):
        return value.replace(token, "<redacted-token>")
    if isinstance(value, list):
        return [_redact_token(item, token) for item in value]
    if isinstance(value, dict):
        return {
            key: _redact_token(item, token)
            for key, item in value.items()
        }
    return value


def scrub_token_files(output_root: Path, token: str) -> list[str]:
    if not token or not output_root.exists():
        return []
    encoded = token.encode("utf-8")
    replacement = b"<redacted-token>"
    scrubbed: list[str] = []
    for path in sorted(output_root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        data = path.read_bytes()
        if encoded not in data:
            continue
        sanitized = data.replace(encoded, replacement)
        flags = os.O_WRONLY | os.O_TRUNC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags)
        try:
            with os.fdopen(descriptor, "wb", closefd=True) as handle:
                handle.write(sanitized)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise
        scrubbed.append(path.relative_to(output_root).as_posix())
    return scrubbed


def _persist_credential_failure(
    report: dict[str, Any],
    output_root: Path,
    scrubbed_files: list[str],
) -> dict[str, Any]:
    report["status"] = "failed"
    report.setdefault("checks", {})["credentialIsolation"] = {
        "status": "failed",
        "scrubbedFiles": scrubbed_files,
    }
    report["error"] = {
        "step": "credentialIsolation",
        "kind": "credential-leak",
        "message": "credential material was scrubbed from capability evidence",
    }
    core.write_json(output_root / "capability-report.json", report)
    return report


def _persist_model_failure(
    report: dict[str, Any],
    output_root: Path,
    error: core.ContractError,
) -> dict[str, Any]:
    message = str(error)
    report["status"] = "failed"
    report.setdefault("checks", {})["resolvedModel"] = {
        "status": "failed",
        "message": message,
    }
    report["error"] = {
        "step": "resolvedModel",
        "kind": "contract",
        "message": message,
    }
    core.write_json(output_root / "capability-report.json", report)
    return report


def classify_blocker_kind(step: Any, message: Any) -> str:
    step_text = str(step or "").strip().lower()
    text = str(message or "").strip().lower()
    if step_text == "authentication" or any(
        marker in text
        for marker in (
            "not authenticated",
            "authentication",
            "github_token",
            "copilot requests permission",
        )
    ):
        return "copilot-auth"
    if "model" in text and any(
        marker in text
        for marker in (
            "not available",
            "unsupported",
            "no models",
            "cannot use",
        )
    ):
        return "model-unavailable"
    if "rate limit" in text:
        return "rate-limit"
    if any(marker in text for marker in ("ai credit", "credits exhausted", "quota")):
        return "credit-exhausted"
    if "browser" in step_text or any(
        marker in text for marker in ("chrome", "chromium", "browser probe")
    ):
        return "browser-timeout" if "timed out" in text or "timeout" in text else "browser-unavailable"
    if any(marker in text for marker in ("policy", "billing", "copilot access")):
        return "copilot-policy"
    if "timed out" in text or "timeout" in text:
        return "copilot-timeout"
    if any(
        marker in text
        for marker in (
            "temporarily unavailable",
            "service unavailable",
        )
    ):
        return "service-unavailable"
    return "capability-blocked"


def normalize_blocked_report(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("status") != "blocked":
        return report
    error = report.get("error")
    if not isinstance(error, dict):
        return report
    error["kind"] = classify_blocker_kind(
        error.get("step"),
        error.get("message"),
    )
    return report


def _retryable_director_failure(report: dict[str, Any]) -> bool:
    if report.get("status") != "failed":
        return False
    error = report.get("error")
    if not isinstance(error, dict):
        return False
    if error.get("step") != "director" or error.get("kind") != "contract":
        return False
    message = str(error.get("message", "")).lower()
    return any(
        marker in message
        for marker in (
            "director direction is missing",
            "director direction is invalid json",
            "director direction must contain a json object",
            "direction keys must be exactly",
            "direction.concept must be a non-empty string",
            "direction.palette must be a non-empty string",
            "direction.layout must be a non-empty string",
            "direction.interaction must be a non-empty string",
        )
    )


def _capture_director_attempt(output_root: Path) -> dict[str, bytes]:
    required_sources = {
        "director.attempt-1.command.json": output_root
        / "evidence"
        / "director.command.json",
        "director.attempt-1.stdout.jsonl": output_root
        / "evidence"
        / "director.stdout.jsonl",
        "director.attempt-1.stderr.log": output_root
        / "evidence"
        / "director.stderr.log",
    }
    captured: dict[str, bytes] = {}
    for destination_name, source in required_sources.items():
        if source.is_symlink() or not source.is_file():
            raise core.ContractError(
                f"cannot preserve Director retry evidence: {source} is not a regular file"
            )
        captured[destination_name] = source.read_bytes()

    direction = output_root / "workspaces" / "director" / "direction.json"
    if direction.is_symlink():
        raise core.ContractError(
            f"cannot preserve Director retry evidence: {direction} is a symlink"
        )
    if direction.exists():
        if not direction.is_file():
            raise core.ContractError(
                f"cannot preserve Director retry evidence: {direction} is not a regular file"
            )
        captured["director.attempt-1.direction.json"] = direction.read_bytes()
    return captured


def _restore_director_attempt(
    output_root: Path,
    captured: dict[str, bytes],
) -> None:
    evidence_dir = output_root / "evidence"
    if evidence_dir.is_symlink() or not evidence_dir.is_dir():
        raise core.ContractError(
            "cannot restore Director retry evidence into an unsafe evidence root"
        )
    for name, content in captured.items():
        destination = evidence_dir / name
        if destination.exists() or destination.is_symlink():
            raise core.ContractError(
                f"Director retry evidence destination already exists: {destination}"
            )
        destination.write_bytes(content)


def _run_core_with_director_retry(
    *args: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    first_report = _BASE_RUN_CAPABILITY(*args, **kwargs)
    if not _retryable_director_failure(first_report):
        return first_report

    output_root_value = kwargs.get("output_root")
    if not isinstance(output_root_value, Path):
        raise core.ContractError(
            "output_root is required to preserve Director retry evidence"
        )
    output_root = output_root_value.expanduser().resolve()
    captured = _capture_director_attempt(output_root)

    global _DIRECTOR_RETRY_ACTIVE
    _DIRECTOR_RETRY_ACTIVE = True
    try:
        report = _BASE_RUN_CAPABILITY(*args, **kwargs)
    finally:
        _DIRECTOR_RETRY_ACTIVE = False

    _restore_director_attempt(output_root, captured)
    director_check = report.setdefault("checks", {}).setdefault("director", {})
    if not isinstance(director_check, dict):
        raise core.ContractError("Director check must be an object")
    director_check["attemptCount"] = 2
    core.write_json(output_root / "capability-report.json", report)
    return report


def run_capability(*args: Any, **kwargs: Any) -> dict[str, Any]:
    report = _run_core_with_director_retry(*args, **kwargs)
    output_root_value = kwargs.get("output_root")
    if not isinstance(output_root_value, Path):
        raise core.ContractError(
            "output_root is required to persist model evidence"
        )
    output_root = output_root_value.expanduser().resolve()
    token = kwargs.get("token", "")
    if not isinstance(token, str):
        token = ""
    report_had_token = bool(
        token and token in json.dumps(report, sort_keys=True, default=str)
    )
    report = _redact_token(report, token)
    scrubbed_files = scrub_token_files(output_root, token)
    if report_had_token and "capability-report.json" not in scrubbed_files:
        scrubbed_files.append("capability-report.json")
    if scrubbed_files:
        return _persist_credential_failure(
            report,
            output_root,
            scrubbed_files,
        )
    report = normalize_blocked_report(report)
    if report.get("status") != "passed":
        core.write_json(output_root / "capability-report.json", report)
        return report

    try:
        models = {
            role: core.require_text(
                report.get("checks", {}).get(role, {}).get(
                    "resolvedModel"
                ),
                f"checks.{role}.resolvedModel",
            )
            for role in ("director", "builder", "evaluator")
        }
        requested_model = kwargs.get("model", DEFAULT_MODEL)
        resolved_models = validate_resolved_models(
            models,
            requested_model=requested_model,
        )
    except core.ContractError as error:
        return _persist_model_failure(report, output_root, error)

    surface = report.setdefault("executionSurface", {})
    surface["requestedModel"] = requested_model
    surface["model"] = requested_model
    surface["modelPolicy"] = (
        "auto-per-role"
        if requested_model.lower() == "auto"
        else "explicit"
    )
    surface["resolvedModels"] = resolved_models
    if requested_model.lower() == "auto":
        surface.pop("resolvedModel", None)
    else:
        surface["resolvedModel"] = requested_model
    core.write_json(output_root / "capability-report.json", report)
    return report


core.DEFAULT_MODEL = DEFAULT_MODEL
core.BROWSER_SCRIPT = Path(__file__).resolve().with_name(
    "run_browser_capability_completion.mjs"
)
core.write_json = write_json_no_follow
core.director_prompt = director_prompt
core.builder_prompt = builder_prompt
core.classify_cli_failure = classify_cli_failure
core.invoke_role = invoke_role
core.run_capability = run_capability


def main(argv: Sequence[str] | None = None) -> int:
    return core.main(argv)


if __name__ == "__main__":
    sys.exit(main())
