#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_MODEL_RECEIPT = (
    REPO_ROOT
    / "benchmarks"
    / "milestone-0"
    / "evidence"
    / "github-models-capability.json"
)
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from boundary_agent_builder import (
    default_browser_runner,
    run_builder,
    validate_output,
)
from boundary_agent_tools import (
    AgentContractError,
    BrowserRunner,
    Clock,
    REPORT_SCHEMA_VERSION,
    Requester,
    SOURCE_CANARY,
    WorkspaceTools,
    aggregate_usage,
    choose_agent_model,
    models,
    require_text,
    usage_receipt,
    utc_now,
    write_json,
)


def load_verified_model_receipt(path: Path) -> dict[str, Any]:
    receipt_path = path.resolve()
    try:
        raw = receipt_path.read_bytes()
    except OSError as exc:
        raise AgentContractError(
            f"cannot read verified model receipt: {receipt_path}"
        ) from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AgentContractError(
            f"verified model receipt is invalid JSON: {exc}"
        ) from exc
    if (
        not isinstance(value, dict)
        or value.get("schemaVersion") != 1
        or value.get("status") != "passed"
    ):
        raise AgentContractError(
            "verified model receipt must be a passed capability report with schemaVersion 1"
        )
    probe = value.get("probe")
    if not isinstance(probe, dict):
        raise AgentContractError(
            "verified model receipt is missing probe evidence"
        )
    checks = probe.get("checks")
    if not isinstance(checks, dict):
        raise AgentContractError(
            "verified model receipt is missing capability checks"
        )
    for check_name in ("structuredText", "vision"):
        check = checks.get(check_name)
        if not isinstance(check, dict) or check.get("status") != "passed":
            raise AgentContractError(
                f"verified model receipt lacks passed {check_name} evidence"
            )
    model = probe.get("model")
    if not isinstance(model, dict):
        raise AgentContractError(
            "verified model receipt is missing model metadata"
        )
    capabilities = model.get("capabilities")
    if (
        not isinstance(capabilities, list)
        or "tool-calling" not in capabilities
    ):
        raise AgentContractError(
            "verified model receipt does not prove tool-calling capability"
        )
    inputs = model.get("supportedInputModalities")
    outputs = model.get("supportedOutputModalities")
    if (
        not isinstance(inputs, list)
        or not {"text", "image"}.issubset(set(inputs))
    ):
        raise AgentContractError(
            "verified model receipt does not prove text-and-image input"
        )
    if not isinstance(outputs, list) or "text" not in outputs:
        raise AgentContractError(
            "verified model receipt does not prove text output"
        )
    normalized = {
        "id": require_text(
            model.get("id"), "verified model receipt model.id"
        ),
        "name": model.get("name"),
        "version": model.get("version"),
        "registry": model.get("registry"),
        "capabilities": capabilities,
        "supported_input_modalities": inputs,
        "supported_output_modalities": outputs,
        "limits": model.get("limits")
        if isinstance(model.get("limits"), dict)
        else {},
    }
    try:
        source_path = receipt_path.relative_to(
            REPO_ROOT.resolve()
        ).as_posix()
    except ValueError:
        source_path = receipt_path.name
    return {
        "model": normalized,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "sourcePath": source_path,
        "verifiedAt": value.get("verifiedAt"),
        "workflow": value.get("workflow")
        if isinstance(value.get("workflow"), dict)
        else None,
    }


def invoke_structured(
    *,
    requester: Requester,
    token: str,
    payload: dict[str, Any],
    evidence_dir: Path,
    stem: str,
    api_version: str,
    inference_url: str,
) -> tuple[dict[str, Any], dict[str, int] | None]:
    write_json(
        evidence_dir / f"{stem}-request.json",
        models.request_receipt(payload),
    )
    response = requester(
        method="POST",
        url=inference_url,
        token=token,
        api_version=api_version,
        payload=payload,
    )
    write_json(evidence_dir / f"{stem}-response.json", response)
    value = models.parse_completion_json(response, stem)
    return value, usage_receipt(response)


def director_payload(model_id: str, brief: str) -> dict[str, Any]:
    return {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a source-blind visual director. You receive "
                    "product intent only, never source code. Return one "
                    "coherent direction for a small production interface."
                ),
            },
            {"role": "user", "content": brief},
        ],
        "temperature": 0,
        "max_tokens": 500,
        "response_format": models.structured_response_format(
            name="design_studio_source_blind_direction",
            properties={
                "concept": {"type": "string"},
                "palette": {"type": "string"},
                "layout": {"type": "string"},
                "interaction": {"type": "string"},
            },
            required=["concept", "palette", "layout", "interaction"],
        ),
    }


def validate_direction(value: dict[str, Any]) -> dict[str, str]:
    expected = ("concept", "palette", "layout", "interaction")
    if set(value) != set(expected):
        raise AgentContractError(
            f"direction keys must be exactly {list(expected)}"
        )
    return {
        key: require_text(value.get(key), f"direction.{key}")
        for key in expected
    }


def evaluator_payload(
    model_id: str, brief: str, screenshot: bytes
) -> dict[str, Any]:
    image_url = "data:image/png;base64," + base64.b64encode(
        screenshot
    ).decode("ascii")
    return {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a source-blind visual evaluator. Judge only the "
                    "supplied brief and rendered screenshot. You do not "
                    "receive source code, implementation history, tool "
                    "transcripts, or prior scores."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"{brief}\n\nThe screenshot was captured after "
                            "successful local form submission. Report only "
                            "what is visibly supported."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url, "detail": "low"},
                    },
                ],
            },
        ],
        "temperature": 0,
        "max_tokens": 350,
        "response_format": models.structured_response_format(
            name="design_studio_source_blind_evaluation",
            properties={
                "titleVisible": {"type": "boolean"},
                "formVisible": {"type": "boolean"},
                "successVisible": {"type": "boolean"},
                "layoutUsable": {"type": "boolean"},
                "sourceCanaryVisible": {"type": "boolean"},
                "summary": {"type": "string"},
            },
            required=[
                "titleVisible",
                "formVisible",
                "successVisible",
                "layoutUsable",
                "sourceCanaryVisible",
                "summary",
            ],
        ),
    }


def validate_evaluation(value: dict[str, Any]) -> dict[str, Any]:
    expected_keys = {
        "titleVisible",
        "formVisible",
        "successVisible",
        "layoutUsable",
        "sourceCanaryVisible",
        "summary",
    }
    if set(value) != expected_keys:
        raise AgentContractError(
            f"evaluation keys must be exactly {sorted(expected_keys)}"
        )
    for key in (
        "titleVisible",
        "formVisible",
        "successVisible",
        "layoutUsable",
        "sourceCanaryVisible",
    ):
        if not isinstance(value.get(key), bool):
            raise AgentContractError(f"evaluation.{key} must be boolean")
    require_text(value.get("summary"), "evaluation.summary")
    failures = [
        key
        for key in (
            "titleVisible",
            "formVisible",
            "successVisible",
            "layoutUsable",
        )
        if not value[key]
    ]
    if value["sourceCanaryVisible"]:
        failures.append("sourceCanaryVisible")
    if failures:
        raise AgentContractError(
            f"source-blind evaluator rejected visible contract: {failures}"
        )
    return value


def contains_canary(path: Path) -> bool:
    return SOURCE_CANARY in path.read_text(
        encoding="utf-8", errors="ignore"
    )


def run_capability(
    *,
    token: str,
    output_root: Path,
    requester: Requester = models.request_json,
    browser_runner: BrowserRunner = default_browser_runner,
    preferred_models: Sequence[str] = models.DEFAULT_PREFERRED_MODELS,
    catalog_url: str = models.CATALOG_URL,
    model_receipt_path: Path | None = None,
    inference_url: str = models.INFERENCE_URL,
    api_version: str = models.API_VERSION,
    now: Clock = utc_now,
) -> dict[str, Any]:
    output_root = output_root.resolve()
    work_dir = output_root / "work"
    site_dir = output_root / "site"
    evidence_dir = output_root / "evidence"
    work_dir.mkdir(parents=True, exist_ok=True)
    site_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "baseline.css").write_text(
        ":root { --capability-accent: #176b5b; "
        "--capability-surface: #f4f1e8; }\n"
        f"/* {SOURCE_CANARY} */\n",
        encoding="utf-8",
    )
    brief = (
        "Create a calm, compact capability-check page. It needs a clear "
        "title, a one-field form, a local success state, visible focus, "
        "reduced-motion support, and a mobile layout that does not overflow. "
        "Use no external assets or network calls."
    )
    report: dict[str, Any] = {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "status": "running",
        "startedAt": now(),
        "finishedAt": None,
        "apiVersion": api_version,
        "model": None,
        "checks": {
            "modelReceipt": {"status": "pending"},
            "director": {"status": "pending"},
            "builder": {"status": "pending"},
            "browser": {"status": "pending"},
            "sourceIsolation": {"status": "pending"},
            "evaluator": {"status": "pending"},
        },
        "usage": None,
        "error": None,
    }
    if not isinstance(token, str) or not token.strip():
        report["status"] = "blocked"
        report["error"] = {
            "step": "authentication",
            "kind": "configuration",
            "message": "GITHUB_TOKEN is required",
        }
        report["finishedAt"] = now()
        write_json(output_root / "capability-report.json", report)
        return report

    current_step = "modelReceipt"
    usage: list[dict[str, int] | None] = []
    try:
        if model_receipt_path is not None:
            receipt = load_verified_model_receipt(model_receipt_path)
            selected = receipt["model"]
            model_id = str(selected["id"])
            report["model"] = models.selected_model_receipt(selected)
            report["checks"]["modelReceipt"] = {
                "status": "passed",
                "source": "verified-receipt",
                "path": receipt["sourcePath"],
                "sha256": receipt["sha256"],
                "verifiedAt": receipt["verifiedAt"],
                "workflow": receipt["workflow"],
                "selectedModel": model_id,
            }
        else:
            catalog = requester(
                method="GET",
                url=catalog_url,
                token=token,
                api_version=api_version,
            )
            write_json(evidence_dir / "catalog-response.json", catalog)
            normalized = models.normalize_catalog(catalog)
            selected = choose_agent_model(normalized, preferred_models)
            model_id = str(selected["id"])
            report["model"] = models.selected_model_receipt(selected)
            report["checks"]["modelReceipt"] = {
                "status": "passed",
                "source": "live-catalog",
                "modelCount": len(normalized),
                "selectedModel": model_id,
            }

        current_step = "director"
        direction_value, direction_usage = invoke_structured(
            requester=requester,
            token=token,
            payload=director_payload(model_id, brief),
            evidence_dir=evidence_dir,
            stem="director",
            api_version=api_version,
            inference_url=inference_url,
        )
        usage.append(direction_usage)
        direction = validate_direction(direction_value)
        report["checks"]["director"] = {
            "status": "passed",
            "direction": direction,
            "usage": direction_usage,
        }

        current_step = "builder"
        workspace = WorkspaceTools(work_dir, site_dir)
        builder = run_builder(
            requester=requester,
            token=token,
            model_id=model_id,
            brief=brief,
            direction=direction,
            workspace=workspace,
            evidence_dir=evidence_dir,
            api_version=api_version,
            inference_url=inference_url,
        )
        usage.append(builder.get("usage"))
        output_contract = validate_output(site_dir)
        report["checks"]["builder"] = {
            "status": "passed",
            "turns": builder["turns"],
            "readPaths": builder["readPaths"],
            "writePaths": builder["writePaths"],
            "usage": builder.get("usage"),
            "output": output_contract,
        }

        current_step = "browser"
        browser = browser_runner(site_dir, evidence_dir)
        report["checks"]["browser"] = {
            "status": "passed",
            "viewport": browser.get("viewport"),
            "interaction": browser.get("interaction"),
            "network": browser.get("network"),
            "screenshot": "evidence/browser/browser-after-submit.png",
        }

        current_step = "sourceIsolation"
        director_request = evidence_dir / "director-request.json"
        screenshot_path = (
            evidence_dir / "browser" / "browser-after-submit.png"
        )
        if not screenshot_path.is_file():
            raise AgentContractError(
                "browser evidence is missing the evaluator screenshot"
            )
        evaluation_request = evaluator_payload(
            model_id, brief, screenshot_path.read_bytes()
        )
        write_json(
            evidence_dir / "evaluator-request.json",
            models.request_receipt(evaluation_request),
        )
        isolation = {
            "directorRequestCanaryAbsent": not contains_canary(
                director_request
            ),
            "evaluatorRequestCanaryAbsent": SOURCE_CANARY
            not in json.dumps(models.request_receipt(evaluation_request)),
            "builderReadCanarySource": "baseline.css"
            in workspace.read_paths,
            "outputCanaryAbsent": SOURCE_CANARY
            not in (site_dir / "index.html").read_text(encoding="utf-8"),
        }
        if not all(isolation.values()):
            raise AgentContractError(
                f"source isolation proof failed: {isolation}"
            )
        report["checks"]["sourceIsolation"] = {
            "status": "passed",
            **isolation,
        }

        current_step = "evaluator"
        evaluation_response = requester(
            method="POST",
            url=inference_url,
            token=token,
            api_version=api_version,
            payload=evaluation_request,
        )
        write_json(
            evidence_dir / "evaluator-response.json",
            evaluation_response,
        )
        evaluation_usage = usage_receipt(evaluation_response)
        usage.append(evaluation_usage)
        evaluation = validate_evaluation(
            models.parse_completion_json(
                evaluation_response, "evaluator"
            )
        )
        report["checks"]["evaluator"] = {
            "status": "passed",
            "evaluation": evaluation,
            "usage": evaluation_usage,
        }
        report["usage"] = aggregate_usage(usage)
        report["status"] = "passed"
    except (
        models.ApiRequestError,
        models.ProbeContractError,
        AgentContractError,
    ) as error:
        status = (
            models.classify_api_status(error.status)
            if isinstance(error, models.ApiRequestError)
            else "failed"
        )
        report["status"] = status
        report["checks"][current_step] = {
            "status": status,
            "message": str(error),
        }
        report["error"] = (
            models.error_receipt(error, current_step)
            if isinstance(
                error,
                (models.ApiRequestError, models.ProbeContractError),
            )
            else {
                "step": current_step,
                "kind": "contract",
                "httpStatus": None,
                "message": f"{type(error).__name__}: {error}",
            }
        )
        report["usage"] = aggregate_usage(usage)
    except Exception as error:
        report["status"] = "failed"
        report["checks"][current_step] = {
            "status": "failed",
            "message": f"{type(error).__name__}: {error}",
        }
        report["error"] = {
            "step": current_step,
            "kind": "unexpected",
            "httpStatus": None,
            "message": f"{type(error).__name__}: {error}",
        }
        report["usage"] = aggregate_usage(usage)

    report["finishedAt"] = now()
    write_json(output_root / "capability-report.json", report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prove controlled file tools, Chromium interaction and "
            "source-blind role isolation for the Milestone 0 comparison "
            "runner."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=(
            Path("harness-output")
            / "benchmarks"
            / "milestone-0"
            / "agent-capability"
        ),
    )
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help=(
            "Preferred GitHub Models ID. Repeat for fallback order when "
            "using --live-catalog."
        ),
    )
    parser.add_argument(
        "--model-receipt",
        type=Path,
        default=DEFAULT_MODEL_RECEIPT,
        help="Previously verified GitHub Models capability receipt.",
    )
    parser.add_argument(
        "--live-catalog",
        action="store_true",
        help=(
            "Resolve a model from the live catalog instead of the verified "
            "receipt."
        ),
    )
    parser.add_argument("--catalog-url", default=models.CATALOG_URL)
    parser.add_argument("--inference-url", default=models.INFERENCE_URL)
    parser.add_argument("--api-version", default=models.API_VERSION)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_capability(
        token=os.environ.get("GITHUB_TOKEN", ""),
        output_root=args.output_dir,
        preferred_models=tuple(
            args.models or models.DEFAULT_PREFERRED_MODELS
        ),
        catalog_url=args.catalog_url,
        model_receipt_path=(
            None if args.live_catalog else args.model_receipt
        ),
        inference_url=args.inference_url,
        api_version=args.api_version,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "model": (report.get("model") or {}).get("id"),
                "report": str(
                    (
                        args.output_dir / "capability-report.json"
                    ).resolve()
                ),
            },
            sort_keys=True,
        )
    )
    if report["status"] == "passed":
        return 0
    if report["status"] == "blocked":
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
