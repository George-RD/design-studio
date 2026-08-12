#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from typing import Any, Sequence


TIMEOUT_EXIT_CODE = 124
DEFAULT_KILL_GRACE_SECONDS = 5.0


def _positive_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{label} must be a positive number of seconds")
    return float(value)


def _command_parts(command: Sequence[str]) -> list[str]:
    parts = [str(part) for part in command]
    if not parts or any(not part for part in parts):
        raise ValueError("command must contain at least one non-empty argument")
    return parts


def _terminate_process_tree(
    process: subprocess.Popen[Any],
    *,
    kill_grace_seconds: float,
) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    else:
        process.terminate()

    try:
        process.wait(timeout=kill_grace_seconds)
        return
    except subprocess.TimeoutExpired:
        pass

    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
    else:
        process.kill()
    process.wait()


def run_with_deadline(
    command: Sequence[str],
    *,
    timeout_seconds: float,
    kill_grace_seconds: float = DEFAULT_KILL_GRACE_SECONDS,
) -> int:
    argv = _command_parts(command)
    timeout_seconds = _positive_number(timeout_seconds, "timeout")
    kill_grace_seconds = _positive_number(kill_grace_seconds, "kill grace")
    process = subprocess.Popen(
        argv,
        start_new_session=os.name == "posix",
    )
    try:
        return process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        _terminate_process_tree(
            process,
            kill_grace_seconds=kill_grace_seconds,
        )
        print(
            "ERROR command exceeded the shared elapsed-time budget of "
            f"{timeout_seconds:g} seconds",
            file=sys.stderr,
        )
        return TIMEOUT_EXIT_CODE
    except BaseException:
        _terminate_process_tree(
            process,
            kill_grace_seconds=kill_grace_seconds,
        )
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one command under a terminal elapsed-time deadline."
    )
    parser.add_argument("--timeout-seconds", required=True, type=float)
    parser.add_argument(
        "--kill-grace-seconds",
        type=float,
        default=DEFAULT_KILL_GRACE_SECONDS,
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    try:
        return run_with_deadline(
            command,
            timeout_seconds=args.timeout_seconds,
            kill_grace_seconds=args.kill_grace_seconds,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 127 if isinstance(exc, OSError) else 2


if __name__ == "__main__":
    raise SystemExit(main())
