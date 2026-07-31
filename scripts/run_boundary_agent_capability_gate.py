#!/usr/bin/env python3
from __future__ import annotations

import sys
from typing import Any, Sequence

import run_boundary_agent_capability as core
from boundary_agent_evaluator_contract import strengthen_evaluator_payload


_BASE_EVALUATOR_PAYLOAD = getattr(
    core, "_DESIGN_STUDIO_BASE_EVALUATOR_PAYLOAD", core.evaluator_payload
)
core._DESIGN_STUDIO_BASE_EVALUATOR_PAYLOAD = _BASE_EVALUATOR_PAYLOAD


def evaluator_payload(
    model_id: str, brief: str, screenshot: bytes
) -> dict[str, Any]:
    return strengthen_evaluator_payload(
        _BASE_EVALUATOR_PAYLOAD(model_id, brief, screenshot)
    )


core.evaluator_payload = evaluator_payload


def main(argv: Sequence[str] | None = None) -> int:
    return core.main(argv)


def __getattr__(name: str) -> Any:
    return getattr(core, name)


if __name__ == "__main__":
    sys.exit(main())
