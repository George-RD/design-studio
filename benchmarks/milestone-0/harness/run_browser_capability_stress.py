#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[3]
BROWSER_SCRIPT = ROOT / "scripts" / "run_browser_capability.mjs"
DEFAULT_EXPECTED_URL = "https://example.invalid/delayed.png"
DEFAULT_RUN_COUNT = 3
DEFAULT_TIMEOUT_SECONDS = 90


class StressContractError(RuntimeError):
    pass


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repeat the delayed external-request browser capability scenario."
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--entrypoint", default="index.html")
    parser.add_argument("--width", type=int, default=390)
    parser.add_argument("--height", type=int, default=844)
    parser.add_argument("--run-count", type=int, default=DEFAULT_RUN_COUNT)
    parser.add_argument("--expected-url", default=DEFAULT_EXPECTED_URL)
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
    )
    args = parser.parse_args(argv)
    if args.run_count < 1 or args.run_count > 20:
        raise StressContractError("--run-count must be from 1 to 20")
    if args.timeout_seconds < 1 or args.timeout_seconds > 300:
        raise StressContractError("--timeout-seconds must be from 1 to 300")
    return args


def _read_report(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise StressContractError(f"browser report is not an object: {path}")
    if not isinstance(value.get("schemaVersion"), int):
        raise StressContractError(
            f"browser report has no integer schemaVersion: {path}"
        )
    if value.get("status") not in {"passed", "failed", "blocked"}:
        raise StressContractError(
            f"browser report has invalid status: {path}"
        )
    return value


def run_attempt(
    *,
    index: int,
    root: Path,
    output_dir: Path,
    entrypoint: str,
    width: int,
    height: int,
    expected_url: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    attempt_dir = output_dir / f"attempt-{index:02d}"
    attempt_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "node",
        str(BROWSER_SCRIPT),
        "--root",
        str(root),
        "--output-dir",
        str(attempt_dir),
        "--entrypoint",
        entrypoint,
        "--width",
        str(width),
        "--height",
        str(height),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired as error:
        return {
            "index": index,
            "exitCode": None,
            "status": "blocked",
            "phase": "stress-timeout",
            "timing": {},
            "urlObserved": False,
            "urlBlocked": False,
            "contractPassed": False,
            "error": f"browser attempt timed out after {timeout_seconds}s",
            "stdout": (error.stdout or "")[-2000:],
            "stderr": (error.stderr or "")[-2000:],
        }

    report_path = attempt_dir / "browser-report.json"
    if not report_path.is_file():
        return {
            "index": index,
            "exitCode": completed.returncode,
            "status": "blocked",
            "phase": "missing-report",
            "timing": {},
            "urlObserved": False,
            "urlBlocked": False,
            "contractPassed": False,
            "error": "browser attempt did not create browser-report.json",
            "stdout": completed.stdout[-2000:],
            "stderr": completed.stderr[-2000:],
        }

    try:
        report = _read_report(report_path)
    except (OSError, ValueError, json.JSONDecodeError, StressContractError) as error:
        return {
            "index": index,
            "exitCode": completed.returncode,
            "status": "blocked",
            "phase": "invalid-report",
            "timing": {},
            "urlObserved": False,
            "urlBlocked": False,
            "contractPassed": False,
            "error": f"{type(error).__name__}: {error}",
            "stdout": completed.stdout[-2000:],
            "stderr": completed.stderr[-2000:],
        }
    network = report.get("network")
    if not isinstance(network, dict):
        network = {}
    external = network.get("externalRequests")
    blocked = network.get("blockedRequests")
    external_urls = external if isinstance(external, list) else []
    blocked_urls = blocked if isinstance(blocked, list) else []
    url_observed = expected_url in external_urls
    url_blocked = expected_url in blocked_urls
    contract_passed = bool(
        completed.returncode == 1
        and report.get("status") == "failed"
        and url_observed
        and url_blocked
    )
    return {
        "index": index,
        "exitCode": completed.returncode,
        "status": report.get("status"),
        "phase": report.get("phase"),
        "timing": report.get("timing")
        if isinstance(report.get("timing"), dict)
        else {},
        "startupRetry": report.get("startupRetry")
        if isinstance(report.get("startupRetry"), dict)
        else {},
        "urlObserved": url_observed,
        "urlBlocked": url_blocked,
        "contractPassed": contract_passed,
        "error": report.get("error"),
    }


def evaluate_attempts(attempts: list[dict[str, Any]]) -> str:
    return (
        "passed"
        if attempts and all(attempt.get("contractPassed") is True for attempt in attempts)
        else "failed"
    )


def build_evidence(
    *,
    attempts: list[dict[str, Any]],
    root: Path,
    expected_url: str,
) -> dict[str, Any]:
    statuses = Counter(str(attempt.get("status", "unknown")) for attempt in attempts)
    return {
        "schemaVersion": 1,
        "status": evaluate_attempts(attempts),
        "verifiedAt": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "workflow": {
            "runner": "scripts/run_browser_capability.mjs",
            "scenario": "delayed-external-request",
            "root": root.as_posix(),
            "expectedUrl": expected_url,
        },
        "checks": {
            "runCount": len(attempts),
            "runStatuses": dict(sorted(statuses.items())),
            "attempts": attempts,
        },
        "scope": {
            "proves": [
                "Repeated cold browser launches classify the delayed external request as an observed failed security contract.",
                "A transient startup block must be recovered by the canonical browser wrapper before the scenario can pass.",
            ],
            "doesNotProve": [
                "Live model-provider availability.",
                "Browser behavior outside the controlled delayed-request capability fixture.",
            ],
        },
    }


def write_evidence(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        root = args.root.expanduser().resolve()
        output_dir = args.output_dir.expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        attempts = [
            run_attempt(
                index=index,
                root=root,
                output_dir=output_dir,
                entrypoint=args.entrypoint,
                width=args.width,
                height=args.height,
                expected_url=args.expected_url,
                timeout_seconds=args.timeout_seconds,
            )
            for index in range(1, args.run_count + 1)
        ]
        evidence = build_evidence(
            attempts=attempts,
            root=root,
            expected_url=args.expected_url,
        )
        evidence_path = output_dir / "browser-stress-evidence.json"
        write_evidence(evidence_path, evidence)
        print(
            json.dumps(
                {
                    "status": evidence["status"],
                    "evidence": str(evidence_path),
                }
            )
        )
        return 0 if evidence["status"] == "passed" else 1
    except (OSError, ValueError, json.JSONDecodeError, StressContractError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
