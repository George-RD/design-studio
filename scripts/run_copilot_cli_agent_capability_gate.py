#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any, Sequence


BASE_PATH = Path(__file__).resolve().with_name(
    "run_copilot_cli_agent_capability_gate_base.py"
)
BASE_MODULE_NAME = "run_copilot_cli_agent_capability_gate_base"
if BASE_MODULE_NAME in sys.modules:
    base = sys.modules[BASE_MODULE_NAME]
else:
    spec = importlib.util.spec_from_file_location(BASE_MODULE_NAME, BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load capability gate base from {BASE_PATH}")
    base = importlib.util.module_from_spec(spec)
    sys.modules[BASE_MODULE_NAME] = base
    spec.loader.exec_module(base)

for _name in dir(base):
    if _name.startswith("__") or _name in {"main", "validate_role_tool_receipt"}:
        continue
    globals()[_name] = getattr(base, _name)

core = base.core


def validate_role_tool_receipt(
    role: str,
    events: list[dict[str, Any]],
    workspace: Path,
) -> dict[str, Any]:
    read_tools = {"read", "view"}
    write_tools = {"create", "edit", "apply_patch"}
    allowed_tools = read_tools | write_tools
    role_contracts = {
        "director": {
            "reads": set(),
            "self_inspection_reads": set(),
            "writes": {"direction.json"},
            "first_turn": {"write"},
        },
        "builder": {
            "reads": {"brief.md", "direction.json", "baseline.css"},
            "self_inspection_reads": {".", "index.html"},
            "writes": {"index.html"},
            "first_turn": {"read"},
        },
        "evaluator": {
            "reads": set(),
            "self_inspection_reads": set(),
            "writes": {"evaluation.json"},
            "first_turn": {"write"},
        },
    }
    contract = role_contracts.get(role)
    if contract is None:
        raise core.ContractError(f"unknown capability role: {role}")

    first_turn_id: str | None = None
    for event_index, event in enumerate(events):
        if event.get("type") != "assistant.turn_start":
            continue
        data = event.get("data")
        if not isinstance(data, dict):
            raise core.ContractError(
                f"{role} assistant turn event {event_index} has no data object"
            )
        first_turn_id = str(data.get("turnId", "")).strip()
        if not first_turn_id:
            raise core.ContractError(
                f"{role} assistant turn event {event_index} has no turnId"
            )
        break
    has_assistant_turns = first_turn_id is not None

    starts: dict[str, dict[str, Any]] = {}
    completed: set[str] = set()
    successful_calls: list[dict[str, Any]] = []
    active_turn_id: str | None = None
    for event_index, event in enumerate(events):
        event_type = event.get("type")
        if event_type in {"assistant.turn_start", "assistant.turn_end"}:
            data = event.get("data")
            if not isinstance(data, dict):
                raise core.ContractError(
                    f"{role} assistant turn event {event_index} has no data object"
                )
            turn_id = str(data.get("turnId", "")).strip()
            if not turn_id:
                raise core.ContractError(
                    f"{role} assistant turn event {event_index} has no turnId"
                )
            if event_type == "assistant.turn_start":
                if active_turn_id is not None:
                    raise core.ContractError(
                        f"{role} assistant turn {turn_id} started before turn "
                        f"{active_turn_id} ended"
                    )
                active_turn_id = turn_id
            else:
                if active_turn_id is None:
                    raise core.ContractError(
                        f"{role} assistant turn {turn_id} ended without a start"
                    )
                if turn_id != active_turn_id:
                    raise core.ContractError(
                        f"{role} assistant turn ended as {turn_id} after starting "
                        f"as {active_turn_id}"
                    )
                active_turn_id = None
            continue
        if event_type not in {"tool.execution_start", "tool.execution_complete"}:
            continue
        data = event.get("data")
        if not isinstance(data, dict):
            raise core.ContractError(
                f"{role} tool receipt event {event_index} has no data object"
            )
        call_id = data.get("toolCallId")
        if not isinstance(call_id, str) or not call_id.strip():
            raise core.ContractError(
                f"{role} tool receipt event {event_index} has no toolCallId"
            )
        call_id = call_id.strip()

        if event_type == "tool.execution_start":
            if call_id in starts:
                raise core.ContractError(
                    f"{role} tool receipt repeats call ID {call_id}"
                )
            tool_name = str(data.get("toolName", "")).strip().lower()
            if tool_name not in allowed_tools:
                raise core.ContractError(
                    f"{role} tool receipt used unsupported tool {tool_name!r}"
                )
            relative = base._workspace_relative_path(
                workspace,
                base._operation_path(data.get("arguments")),
            )
            if relative is None:
                raise core.ContractError(
                    f"{role} tool receipt path escaped the trusted role workspace"
                )

            operation = "read" if tool_name in read_tools else "write"
            read_kind: str | None = None
            if operation == "read":
                if relative in contract["reads"]:
                    read_kind = "seed"
                elif relative in contract["self_inspection_reads"]:
                    read_kind = "self-inspection"
                else:
                    raise core.ContractError(
                        f"{role} tool receipt attempted unauthorized read: {relative}"
                    )
            elif relative not in contract["writes"]:
                raise core.ContractError(
                    f"{role} tool receipt attempted unauthorized write: {relative}"
                )

            explicit_turn_id = str(data.get("turnId", "")).strip()
            if has_assistant_turns and active_turn_id is None:
                raise core.ContractError(
                    f"{role} tool receipt call {call_id} occurred outside an assistant turn"
                )
            if (
                explicit_turn_id
                and active_turn_id is not None
                and explicit_turn_id != active_turn_id
            ):
                raise core.ContractError(
                    f"{role} tool receipt call {call_id} changed the active turn"
                )
            turn_id = explicit_turn_id or active_turn_id
            if not turn_id:
                raise core.ContractError(
                    f"{role} tool receipt call {call_id} cannot be associated "
                    "with an assistant turn"
                )
            if first_turn_id is None:
                first_turn_id = turn_id
            starts[call_id] = {
                "id": call_id,
                "tool": tool_name,
                "operation": operation,
                "path": relative,
                "readKind": read_kind,
                "turnId": turn_id,
                "startIndex": event_index,
            }
            continue

        if call_id not in starts:
            raise core.ContractError(
                f"{role} tool receipt completed unknown call {call_id}"
            )
        if call_id in completed:
            raise core.ContractError(
                f"{role} tool receipt completed call {call_id} more than once"
            )
        start = starts[call_id]
        complete_tool = str(data.get("toolName", "")).strip().lower()
        if complete_tool and complete_tool != start["tool"]:
            raise core.ContractError(
                f"{role} tool receipt changed tool for call {call_id}"
            )
        complete_turn = str(data.get("turnId", "")).strip()
        if complete_turn and complete_turn != start["turnId"]:
            raise core.ContractError(
                f"{role} tool receipt changed turn for call {call_id}"
            )
        if has_assistant_turns and active_turn_id != start["turnId"]:
            raise core.ContractError(
                f"{role} tool receipt completed call {call_id} outside its assistant turn"
            )
        if data.get("success") is not True:
            raise core.ContractError(
                f"{role} tool receipt call {call_id} did not succeed"
            )
        completed.add(call_id)
        successful_calls.append({**start, "completeIndex": event_index})

    incomplete = sorted(set(starts) - completed)
    if incomplete:
        raise core.ContractError(
            f"{role} tool receipt has incomplete calls: {incomplete}"
        )
    if not successful_calls:
        raise core.ContractError(
            f"{role} tool receipt contains no successful calls"
        )

    seed_reads = {
        call["path"]
        for call in successful_calls
        if call["operation"] == "read" and call["readKind"] == "seed"
    }
    self_inspection_reads = {
        call["path"]
        for call in successful_calls
        if (
            call["operation"] == "read"
            and call["readKind"] == "self-inspection"
        )
    }
    writes = {
        call["path"]
        for call in successful_calls
        if call["operation"] == "write"
    }
    if seed_reads != contract["reads"] or writes != contract["writes"]:
        raise core.ContractError(
            f"{role} tool receipt does not match the role contract: "
            f"reads={sorted(seed_reads)}, writes={sorted(writes)}"
        )

    if role == "builder":
        first_turn_has_seed_read = any(
            call["operation"] == "read"
            and call["readKind"] == "seed"
            and call["turnId"] == first_turn_id
            for call in successful_calls
        )
        if not first_turn_has_seed_read:
            raise core.ContractError(
                f"{role} tool receipt does not prove required first-turn tool use"
            )
    else:
        first_turn_operations = {
            call["operation"]
            for call in successful_calls
            if call["turnId"] == first_turn_id
        }
        if not contract["first_turn"].issubset(first_turn_operations):
            raise core.ContractError(
                f"{role} tool receipt does not prove required first-turn tool use"
            )

    if role == "builder":
        seed_read_completions = [
            call["completeIndex"]
            for call in successful_calls
            if call["operation"] == "read" and call["readKind"] == "seed"
        ]
        write_starts = [
            call["startIndex"]
            for call in successful_calls
            if call["operation"] == "write"
        ]
        if (
            not seed_read_completions
            or not write_starts
            or max(seed_read_completions) >= min(write_starts)
        ):
            raise core.ContractError(
                "builder tool receipt does not prove all required reads "
                "completed before writing"
            )

    return {
        "read": sorted(seed_reads | self_inspection_reads),
        "seedRead": sorted(seed_reads),
        "selfInspectionRead": sorted(self_inspection_reads),
        "written": sorted(writes),
        "calls": successful_calls,
    }


base.validate_role_tool_receipt = validate_role_tool_receipt


def main(argv: Sequence[str] | None = None) -> int:
    return base.main(argv)


if __name__ == "__main__":
    sys.exit(main())
