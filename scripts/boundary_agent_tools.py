#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any, Callable, Iterable, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import probe_github_models as models


REPORT_SCHEMA_VERSION = 1
SOURCE_CANARY = "DESIGN_STUDIO_SOURCE_CANARY_7f3ad95c"
ALLOWED_TEXT_SUFFIXES = {".css", ".html", ".js", ".json", ".md", ".svg", ".txt"}
MAX_FILE_BYTES = 240_000
MAX_OUTPUT_FILES = 16
MAX_OUTPUT_BYTES = 900_000
DEFAULT_MAX_BUILDER_TURNS = 6

Requester = Callable[..., Any]
Clock = Callable[[], str]
BrowserRunner = Callable[[Path, Path], dict[str, Any]]


class AgentContractError(RuntimeError):
    """Raised when an agent step violates the capability contract."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentContractError(f"{label} must be a non-empty string")
    return value


def safe_relative_path(value: Any, label: str = "path") -> PurePosixPath:
    text = require_text(value, label)
    if "\\" in text:
        raise AgentContractError(f"{label} must use forward slashes")
    candidate = PurePosixPath(text)
    if candidate.is_absolute() or not candidate.parts or any(part in {"", ".", ".."} for part in candidate.parts):
        raise AgentContractError(f"{label} must be a safe relative path")
    suffix = Path(candidate.name).suffix.lower()
    if suffix not in ALLOWED_TEXT_SUFFIXES:
        raise AgentContractError(f"{label} uses unsupported file type: {suffix or '<none>'}")
    return candidate


def ensure_no_symlink(root: Path, relative: PurePosixPath, label: str) -> Path:
    root = root.resolve()
    current = root
    for part in relative.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise AgentContractError(f"{label} may not traverse a symlink: {relative.as_posix()}")
    resolved = current.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise AgentContractError(f"{label} escapes its allowed root: {relative.as_posix()}")
    return current


class WorkspaceTools:
    def __init__(self, work_dir: Path, output_dir: Path) -> None:
        self.work_dir = work_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.read_paths: list[str] = []
        self.write_paths: list[str] = []

    def definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_work_files",
                    "description": "List readable text files in the isolated starting work tree.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_work_file",
                    "description": "Read one UTF-8 text file from the isolated starting work tree.",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_output_file",
                    "description": "Write one UTF-8 text file into the isolated final output tree.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["path", "content"],
                        "additionalProperties": False,
                    },
                },
            },
        ]

    def list_work_files(self) -> dict[str, Any]:
        files = []
        for path in sorted(self.work_dir.rglob("*")):
            if path.is_symlink():
                raise AgentContractError(f"work tree contains a symlink: {path.relative_to(self.work_dir)}")
            if path.is_file() and path.suffix.lower() in ALLOWED_TEXT_SUFFIXES:
                files.append(path.relative_to(self.work_dir).as_posix())
        return {"files": files}

    def read_work_file(self, path: Any) -> dict[str, Any]:
        relative = safe_relative_path(path, "read_work_file.path")
        target = ensure_no_symlink(self.work_dir, relative, "read_work_file.path")
        if not target.is_file():
            raise AgentContractError(f"work file does not exist: {relative.as_posix()}")
        size = target.stat().st_size
        if size > MAX_FILE_BYTES:
            raise AgentContractError(f"work file exceeds {MAX_FILE_BYTES} bytes: {relative.as_posix()}")
        content = target.read_text(encoding="utf-8")
        self.read_paths.append(relative.as_posix())
        return {"path": relative.as_posix(), "content": content}

    def write_output_file(self, path: Any, content: Any) -> dict[str, Any]:
        relative = safe_relative_path(path, "write_output_file.path")
        text = require_text(content, "write_output_file.content")
        encoded = text.encode("utf-8")
        if len(encoded) > MAX_FILE_BYTES:
            raise AgentContractError(f"output file exceeds {MAX_FILE_BYTES} bytes: {relative.as_posix()}")
        target = ensure_no_symlink(self.output_dir, relative, "write_output_file.path")
        existing_files = [item for item in self.output_dir.rglob("*") if item.is_file()]
        existing_size = target.stat().st_size if target.is_file() else 0
        projected_count = len(existing_files) + (0 if target.is_file() else 1)
        projected_bytes = sum(item.stat().st_size for item in existing_files) - existing_size + len(encoded)
        if projected_count > MAX_OUTPUT_FILES:
            raise AgentContractError(f"output tree exceeds {MAX_OUTPUT_FILES} files")
        if projected_bytes > MAX_OUTPUT_BYTES:
            raise AgentContractError(f"output tree exceeds {MAX_OUTPUT_BYTES} bytes")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(target)
        if relative.as_posix() not in self.write_paths:
            self.write_paths.append(relative.as_posix())
        return {"path": relative.as_posix(), "bytes": len(encoded)}

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "list_work_files":
            if arguments:
                raise AgentContractError("list_work_files accepts no arguments")
            return self.list_work_files()
        if name == "read_work_file":
            return self.read_work_file(arguments.get("path"))
        if name == "write_output_file":
            return self.write_output_file(arguments.get("path"), arguments.get("content"))
        raise AgentContractError(f"unknown workspace tool: {name}")


def choose_agent_model(catalog: Iterable[dict[str, Any]], preferred: Sequence[str]) -> dict[str, Any]:
    eligible = {
        model.get("id"): model
        for model in catalog
        if isinstance(model.get("id"), str)
        and {"text", "image"}.issubset(set(model.get("supported_input_modalities") or []))
        and "text" in set(model.get("supported_output_modalities") or [])
        and "tool-calling" in set(model.get("capabilities") or [])
    }
    for model_id in preferred:
        if model_id in eligible:
            return eligible[model_id]
    if eligible:
        return eligible[sorted(eligible)[0]]
    raise AgentContractError(
        "catalog exposes no text-and-image input model with text output and tool-calling"
    )


def assistant_message(response: Any, label: str) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise AgentContractError(f"{label} response must be an object")
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AgentContractError(f"{label} response has no choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise AgentContractError(f"{label} response has no assistant message")
    return message


def parse_tool_arguments(value: Any, label: str) -> dict[str, Any]:
    if isinstance(value, dict):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise AgentContractError(f"{label} contains invalid JSON: {exc}") from exc
    else:
        raise AgentContractError(f"{label} must be a JSON object or encoded JSON object")
    if not isinstance(parsed, dict):
        raise AgentContractError(f"{label} must decode to an object")
    return parsed


def normalize_tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    raw_calls = message.get("tool_calls")
    if raw_calls is None:
        return []
    if not isinstance(raw_calls, list):
        raise AgentContractError("assistant tool_calls must be an array")
    calls: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_calls):
        if not isinstance(raw, dict):
            raise AgentContractError(f"assistant tool_calls[{index}] must be an object")
        call_id = require_text(raw.get("id"), f"assistant tool_calls[{index}].id")
        function = raw.get("function")
        if not isinstance(function, dict):
            raise AgentContractError(f"assistant tool_calls[{index}].function must be an object")
        name = require_text(function.get("name"), f"assistant tool_calls[{index}].function.name")
        arguments = parse_tool_arguments(
            function.get("arguments", {}),
            f"assistant tool_calls[{index}].function.arguments",
        )
        calls.append({"id": call_id, "type": "function", "name": name, "arguments": arguments, "raw": raw})
    return calls


def usage_receipt(response: Any) -> dict[str, int] | None:
    usage = models.usage_from(response)
    if not isinstance(usage, dict):
        return None
    receipt: dict[str, int] = {}
    aliases = {
        "prompt_tokens": "promptTokens",
        "completion_tokens": "completionTokens",
        "total_tokens": "totalTokens",
    }
    for source, target in aliases.items():
        value = usage.get(source)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            receipt[target] = value
    return receipt or None


def aggregate_usage(receipts: Iterable[dict[str, int] | None]) -> dict[str, int] | None:
    total: dict[str, int] = {}
    for receipt in receipts:
        if not receipt:
            continue
        for key, value in receipt.items():
            total[key] = total.get(key, 0) + value
    return total or None
