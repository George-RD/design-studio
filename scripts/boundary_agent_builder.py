#!/usr/bin/env python3
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from boundary_agent_tools import (
    AgentContractError,
    DEFAULT_MAX_BUILDER_TURNS,
    MAX_FILE_BYTES,
    SOURCE_CANARY,
    Requester,
    WorkspaceTools,
    aggregate_usage,
    assistant_message,
    models,
    normalize_tool_calls,
    usage_receipt,
    write_json,
)

SCRIPT_DIR = Path(__file__).resolve().parent


def run_builder(
    *,
    requester: Requester,
    token: str,
    model_id: str,
    brief: str,
    direction: dict[str, str],
    workspace: WorkspaceTools,
    evidence_dir: Path,
    api_version: str,
    inference_url: str,
    max_turns: int = DEFAULT_MAX_BUILDER_TURNS,
) -> dict[str, Any]:
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are the Builder. You may inspect the isolated work tree through tools and may write only to "
                "the isolated output tree. Implement the selected direction faithfully. Never reproduce comments or "
                "canary text from source files in the deliverable."
            ),
        },
        {
            "role": "user",
            "content": (
                f"{brief}\n\nSelected visual direction:\n{json.dumps(direction, sort_keys=True)}\n\n"
                "Capability contract:\n"
                "1. Read baseline.css before implementation.\n"
                "2. Write one self-contained index.html with inline CSS and JavaScript and no external requests.\n"
                "3. Include a form #capability-form, input #capability-name, and success region "
                "#capability-success.\n"
                "4. Local submit must preserve the entered name, prevent navigation, reveal exact text "
                "'Capability complete', and work at 390px without horizontal overflow.\n"
                "5. Support visible focus and prefers-reduced-motion.\n"
                "Use the tools; do not return the file only in chat."
            ),
        },
    ]
    usage: list[dict[str, int] | None] = []
    tool_events: list[dict[str, Any]] = []
    final_text: str | None = None

    def persist_tool_events() -> None:
        write_json(
            evidence_dir / "builder-tool-events.json",
            {"schemaVersion": 1, "events": tool_events},
        )

    persist_tool_events()
    for turn in range(1, max_turns + 1):
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 3500,
            "tools": workspace.definitions(),
            "tool_choice": "required" if turn == 1 else "auto",
        }
        write_json(
            evidence_dir / f"builder-turn-{turn:02d}-request.json",
            models.request_receipt(payload),
        )
        response = requester(
            method="POST",
            url=inference_url,
            token=token,
            api_version=api_version,
            payload=payload,
        )
        write_json(
            evidence_dir / f"builder-turn-{turn:02d}-response.json", response
        )
        usage.append(usage_receipt(response))
        message = assistant_message(response, f"builder turn {turn}")
        calls = normalize_tool_calls(message)
        assistant_entry: dict[str, Any] = {
            "role": "assistant",
            "content": message.get("content") or "",
        }
        if calls:
            assistant_entry["tool_calls"] = [call["raw"] for call in calls]
        messages.append(assistant_entry)

        if calls:
            for call in calls:
                try:
                    result = workspace.execute(call["name"], call["arguments"])
                    event = {
                        "turn": turn,
                        "id": call["id"],
                        "name": call["name"],
                        "arguments": call["arguments"],
                        "status": "passed",
                        "result": result,
                    }
                    tool_content = json.dumps(
                        {"ok": True, "result": result}, sort_keys=True
                    )
                except AgentContractError as error:
                    event = {
                        "turn": turn,
                        "id": call["id"],
                        "name": call["name"],
                        "arguments": call["arguments"],
                        "status": "failed",
                        "error": str(error),
                    }
                    tool_content = json.dumps(
                        {"ok": False, "error": str(error)}, sort_keys=True
                    )
                tool_events.append(event)
                persist_tool_events()
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": tool_content,
                    }
                )
            continue

        content = message.get("content")
        if isinstance(content, str) and content.strip():
            final_text = content.strip()
            break
        raise AgentContractError(
            f"builder turn {turn} returned neither tool calls nor final text"
        )
    else:
        raise AgentContractError(f"builder exceeded {max_turns} turns")

    persist_tool_events()
    if "baseline.css" not in workspace.read_paths:
        raise AgentContractError("builder did not read required baseline.css")
    if "index.html" not in workspace.write_paths:
        raise AgentContractError("builder did not write required index.html")
    if any(event["status"] != "passed" for event in tool_events):
        raise AgentContractError("builder produced one or more rejected tool calls")
    return {
        "finalText": final_text,
        "turns": len({event["turn"] for event in tool_events})
        + (1 if final_text is not None else 0),
        "toolEvents": tool_events,
        "readPaths": workspace.read_paths,
        "writePaths": workspace.write_paths,
        "usage": aggregate_usage(usage),
    }


class OutputContractParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.text: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        for name, value in attrs:
            if name.lower() == "id" and isinstance(value, str):
                self.ids.add(value)

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.text.append(data.strip())


def validate_output(output_dir: Path) -> dict[str, Any]:
    entry = output_dir / "index.html"
    if not entry.is_file():
        raise AgentContractError("builder output is missing index.html")
    html = entry.read_text(encoding="utf-8")
    if len(html.encode("utf-8")) > MAX_FILE_BYTES:
        raise AgentContractError("index.html exceeds the capability size limit")
    parser = OutputContractParser()
    parser.feed(html)
    required_ids = {
        "capability-form",
        "capability-name",
        "capability-success",
    }
    missing_ids = sorted(required_ids - parser.ids)
    if missing_ids:
        raise AgentContractError(
            f"index.html is missing required element IDs: {missing_ids}"
        )
    if "Capability complete" not in html:
        raise AgentContractError(
            "index.html is missing the exact success-state text"
        )
    lower = html.lower()
    forbidden = [
        r"https?://",
        r"<script[^>]+src\s*=",
        r"<link[^>]+href\s*=",
    ]
    present = [pattern for pattern in forbidden if re.search(pattern, lower)]
    if present:
        raise AgentContractError(
            f"index.html contains external dependency patterns: {present}"
        )
    if SOURCE_CANARY in html:
        raise AgentContractError("source canary leaked into builder output")
    return {
        "entrypoint": "index.html",
        "bytes": entry.stat().st_size,
        "selfContained": True,
        "sourceCanaryAbsent": True,
    }


def default_browser_runner(
    output_dir: Path, evidence_dir: Path
) -> dict[str, Any]:
    command = [
        "node",
        str(SCRIPT_DIR / "run_browser_capability.mjs"),
        "--root",
        str(output_dir),
        "--output-dir",
        str(evidence_dir / "browser"),
        "--entrypoint",
        "index.html",
        "--width",
        "390",
        "--height",
        "844",
    ]
    completed = subprocess.run(
        command, capture_output=True, text=True, check=False
    )
    (evidence_dir / "browser-stdout.log").write_text(
        completed.stdout, encoding="utf-8"
    )
    (evidence_dir / "browser-stderr.log").write_text(
        completed.stderr, encoding="utf-8"
    )
    report_path = evidence_dir / "browser" / "browser-report.json"
    if not report_path.is_file():
        raise AgentContractError(
            "browser probe did not produce browser-report.json"
        )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise AgentContractError("browser report must be an object")
    if completed.returncode == 2 or report.get("status") == "blocked":
        raise models.ApiRequestError(
            status=None,
            method="BROWSER",
            url="local-chromium",
            body={
                "message": report.get("error")
                or "browser capability blocked"
            },
        )
    if completed.returncode != 0 or report.get("status") != "passed":
        raise AgentContractError(
            f"browser capability failed: {report.get('failures') or report.get('error')}"
        )
    return report
