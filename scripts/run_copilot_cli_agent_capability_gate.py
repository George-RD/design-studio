#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_copilot_cli_agent_capability as core


DEFAULT_MODEL = "auto"
_BASE_CLASSIFIER = core.classify_cli_failure
_BASE_INVOKE_ROLE = core.invoke_role
_BASE_RUN_CAPABILITY = core.run_capability
core.DEFAULT_MODEL = DEFAULT_MODEL


def classify_cli_failure(outcome: core.CommandOutcome) -> str:
    text = f"{outcome.stdout}\n{outcome.stderr}".lower()
    if "model" in text and "not available" in text:
        return "blocked"
    return _BASE_CLASSIFIER(outcome)


def write_trusted_workspace_config(copilot_home: Path, workspace: Path) -> Path:
    config_path = copilot_home.resolve() / "config.json"
    if config_path.exists():
        raise core.ContractError(
            f"Copilot role config already exists: {config_path}"
        )
    copilot_home.mkdir(parents=True, exist_ok=True)
    payload = {"trustedFolders": [str(workspace.resolve())]}
    config_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return config_path


def _model_value(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in (
            "model",
            "modelId",
            "model_id",
            "selectedModel",
            "chosenModel",
        ):
            candidate = value.get(key)
            if (
                isinstance(candidate, str)
                and candidate.strip()
                and candidate.strip().lower() != "auto"
            ):
                return candidate.strip()
        for key in ("data", "session", "metadata", "usage"):
            if key in value:
                candidate = _model_value(value[key])
                if candidate:
                    return candidate
    elif isinstance(value, list):
        for item in value:
            candidate = _model_value(item)
            if candidate:
                return candidate
    return None


def resolved_model_from_events(events: list[dict[str, Any]], role: str) -> str:
    for event in reversed(events):
        event_type = str(event.get("type", "")).lower()
        if "session" in event_type or "idle" in event_type:
            candidate = _model_value(event)
            if candidate:
                return candidate
    for event in reversed(events):
        candidate = _model_value(event)
        if candidate:
            return candidate
    raise core.ContractError(
        f"{role} JSONL contains no resolved model receipt"
    )


def validate_resolved_models(role_models: dict[str, str]) -> str:
    required = {"director", "builder", "evaluator"}
    if set(role_models) != required:
        raise core.ContractError(
            f"resolved model receipt must cover exactly {sorted(required)}"
        )
    unique = set(role_models.values())
    if len(unique) != 1:
        raise core.ContractError(
            "Copilot auto selection resolved different models by role: "
            f"{role_models}"
        )
    return next(iter(unique))


def role_tool_set(role: str) -> str:
    if role in {"director", "evaluator"}:
        return "create"
    if role == "builder":
        return "view,create,edit,apply_patch"
    raise core.ContractError(f"unknown Copilot capability role: {role}")


def invoke_role(*args: Any, **kwargs: Any) -> dict[str, Any]:
    role = kwargs.get("role")
    evidence_dir = kwargs.get("evidence_dir")
    workspace = kwargs.get("workspace")
    if (
        not isinstance(role, str)
        or not isinstance(evidence_dir, Path)
        or not isinstance(workspace, Path)
    ):
        raise core.ContractError(
            "role invocation lacks workspace evidence context"
        )
    copilot_home = evidence_dir / "copilot-home" / role
    write_trusted_workspace_config(copilot_home, workspace)

    kwargs["available_tools"] = role_tool_set(role)
    prompt = kwargs.get("prompt")
    if isinstance(prompt, str):
        kwargs["prompt"] = (
            f"{prompt}\n\nUse the create tool when the required output file "
            "does not already exist."
        )

    result = _BASE_INVOKE_ROLE(*args, **kwargs)
    stdout_path = evidence_dir / f"{role}.stdout.jsonl"
    events = core.parse_jsonl(
        stdout_path.read_text(encoding="utf-8"),
        f"{role} Copilot JSONL",
    )
    result["resolvedModel"] = resolved_model_from_events(events, role)
    result["trustedWorkspace"] = str(workspace.resolve())
    result["availableTools"] = kwargs["available_tools"].split(",")
    return result


def run_capability(*args: Any, **kwargs: Any) -> dict[str, Any]:
    kwargs.setdefault("model", DEFAULT_MODEL)
    report = _BASE_RUN_CAPABILITY(*args, **kwargs)
    if report.get("status") == "passed":
        checks = report.get("checks")
        if not isinstance(checks, dict):
            raise core.ContractError("capability report has no checks object")
        role_models = {
            role: checks.get(role, {}).get("resolvedModel")
            for role in ("director", "builder", "evaluator")
        }
        if any(
            not isinstance(value, str) or not value
            for value in role_models.values()
        ):
            raise core.ContractError(
                "capability report lacks resolved model evidence: "
                f"{role_models}"
            )
        resolved = validate_resolved_models(role_models)
        surface = report.get("executionSurface")
        if not isinstance(surface, dict):
            raise core.ContractError(
                "capability report has no execution surface"
            )
        surface["requestedModel"] = kwargs["model"]
        surface["resolvedModel"] = resolved
        surface["model"] = resolved
        output_root = kwargs.get("output_root")
        if not isinstance(output_root, Path):
            raise core.ContractError(
                "capability run lacks an output root"
            )
        core.write_json(
            output_root.resolve() / "capability-report.json", report
        )
    return report


core.classify_cli_failure = classify_cli_failure
core.invoke_role = invoke_role
core.run_capability = run_capability
CommandOutcome = core.CommandOutcome
SOURCE_CANARY = core.SOURCE_CANARY


def main(argv: Sequence[str] | None = None) -> int:
    return core.main(argv)


def __getattr__(name: str) -> Any:
    return getattr(core, name)


if __name__ == "__main__":
    sys.exit(main())
