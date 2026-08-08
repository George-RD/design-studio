from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_copilot_cli_agent_capability_gate.py"


def load_module():
    module_name = "run_copilot_cli_tool_receipt_turns_test"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def assistant_turn_start(turn_id: str) -> dict[str, object]:
    return {
        "type": "assistant.turn_start",
        "data": {"turnId": turn_id},
    }


def assistant_turn_end(turn_id: str) -> dict[str, object]:
    return {
        "type": "assistant.turn_end",
        "data": {"turnId": turn_id},
    }


def tool_events(
    tool_name: str,
    path: Path,
    call_id: str,
    *,
    turn_id: str | None,
) -> list[dict[str, object]]:
    start_data: dict[str, object] = {
        "toolCallId": call_id,
        "toolName": tool_name,
        "arguments": {"path": str(path)},
    }
    complete_data: dict[str, object] = {
        "toolCallId": call_id,
        "toolName": tool_name,
        "success": True,
    }
    if turn_id is not None:
        start_data["turnId"] = turn_id
        complete_data["turnId"] = turn_id
    return [
        {"type": "tool.execution_start", "data": start_data},
        {"type": "tool.execution_complete", "data": complete_data},
    ]


class CopilotCliToolReceiptTurnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_builder_reads_can_span_turns_before_the_first_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            events: list[dict[str, object]] = []
            for turn_id, path, call_id in (
                ("turn-17", workspace / "brief.md", "read-brief"),
                ("turn-18", workspace / "direction.json", "read-direction"),
                ("turn-19", workspace / "baseline.css", "read-baseline"),
            ):
                events.append(assistant_turn_start(turn_id))
                events.extend(
                    tool_events(
                        "view",
                        path,
                        call_id,
                        turn_id=turn_id,
                    )
                )
                events.append(assistant_turn_end(turn_id))
            events.append(assistant_turn_start("turn-20"))
            events.extend(
                tool_events(
                    "create",
                    workspace / "index.html",
                    "write-index",
                    turn_id="turn-20",
                )
            )
            events.append(assistant_turn_end("turn-20"))

            receipt = self.module.validate_role_tool_receipt(
                "builder",
                events,
                workspace,
            )

        self.assertEqual(
            ["baseline.css", "brief.md", "direction.json"],
            receipt["read"],
        )
        self.assertEqual(["index.html"], receipt["written"])

    def test_tool_events_without_turn_ids_inherit_the_active_assistant_turn(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            events: list[dict[str, object]] = []
            for turn_id, path, call_id in (
                ("alpha", workspace / "brief.md", "read-brief"),
                ("beta", workspace / "direction.json", "read-direction"),
                ("gamma", workspace / "baseline.css", "read-baseline"),
            ):
                events.append(assistant_turn_start(turn_id))
                events.extend(
                    tool_events(
                        "view",
                        path,
                        call_id,
                        turn_id=None,
                    )
                )
                events.append(assistant_turn_end(turn_id))
            events.append(assistant_turn_start("delta"))
            events.extend(
                tool_events(
                    "create",
                    workspace / "index.html",
                    "write-index",
                    turn_id=None,
                )
            )
            events.append(assistant_turn_end("delta"))

            receipt = self.module.validate_role_tool_receipt(
                "builder",
                events,
                workspace,
            )

        self.assertEqual("alpha", receipt["calls"][0]["turnId"])
        self.assertEqual("delta", receipt["calls"][-1]["turnId"])

    def test_first_assistant_turn_must_contain_the_required_operation(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            events: list[dict[str, object]] = [
                assistant_turn_start("empty-first-turn"),
                assistant_turn_end("empty-first-turn"),
                assistant_turn_start("second-turn"),
                *tool_events(
                    "view",
                    workspace / "brief.md",
                    "read-brief",
                    turn_id="second-turn",
                ),
                *tool_events(
                    "view",
                    workspace / "direction.json",
                    "read-direction",
                    turn_id="second-turn",
                ),
                *tool_events(
                    "view",
                    workspace / "baseline.css",
                    "read-baseline",
                    turn_id="second-turn",
                ),
                *tool_events(
                    "create",
                    workspace / "index.html",
                    "write-index",
                    turn_id="second-turn",
                ),
                assistant_turn_end("second-turn"),
            ]

            with self.assertRaisesRegex(
                self.module.core.ContractError,
                "required first-turn tool use",
            ):
                self.module.validate_role_tool_receipt(
                    "builder",
                    events,
                    workspace,
                )

    def test_builder_still_requires_all_reads_to_complete_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            events: list[dict[str, object]] = [
                assistant_turn_start("first"),
                *tool_events(
                    "view",
                    workspace / "brief.md",
                    "read-brief",
                    turn_id="first",
                ),
                assistant_turn_end("first"),
                assistant_turn_start("second"),
                *tool_events(
                    "create",
                    workspace / "index.html",
                    "write-index",
                    turn_id="second",
                ),
                assistant_turn_end("second"),
                assistant_turn_start("third"),
                *tool_events(
                    "view",
                    workspace / "direction.json",
                    "read-direction",
                    turn_id="third",
                ),
                *tool_events(
                    "view",
                    workspace / "baseline.css",
                    "read-baseline",
                    turn_id="third",
                ),
                assistant_turn_end("third"),
            ]

            with self.assertRaisesRegex(
                self.module.core.ContractError,
                "reads completed before writing",
            ):
                self.module.validate_role_tool_receipt(
                    "builder",
                    events,
                    workspace,
                )


if __name__ == "__main__":
    unittest.main()
