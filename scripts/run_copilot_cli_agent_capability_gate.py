#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_copilot_cli_agent_capability as core


DEFAULT_MODEL = "claude-sonnet-4.6"
_BASE_CLASSIFIER = core.classify_cli_failure
core.DEFAULT_MODEL = DEFAULT_MODEL


def classify_cli_failure(outcome: core.CommandOutcome) -> str:
    text = f"{outcome.stdout}\n{outcome.stderr}".lower()
    if "model" in text and "not available" in text:
        return "blocked"
    return _BASE_CLASSIFIER(outcome)


core.classify_cli_failure = classify_cli_failure
CommandOutcome = core.CommandOutcome
SOURCE_CANARY = core.SOURCE_CANARY


def run_capability(*args: Any, **kwargs: Any) -> dict[str, Any]:
    kwargs.setdefault("model", DEFAULT_MODEL)
    return core.run_capability(*args, **kwargs)


def main(argv: Sequence[str] | None = None) -> int:
    return core.main(argv)


def __getattr__(name: str) -> Any:
    return getattr(core, name)


if __name__ == "__main__":
    sys.exit(main())
