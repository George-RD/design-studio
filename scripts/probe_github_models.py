#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import struct
import sys
from typing import Any, Callable, Iterable, Sequence
import urllib.error
import urllib.request
import zlib


CATALOG_URL = "https://models.github.ai/catalog/models"
INFERENCE_URL = "https://models.github.ai/inference/chat/completions"
API_VERSION = "2026-03-10"
DEFAULT_PREFERRED_MODELS = (
    "openai/gpt-4.1",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
)
BLOCKED_HTTP_STATUSES = {401, 403, 404, 408, 429}
REPORT_SCHEMA_VERSION = 1


class ProbeContractError(RuntimeError):
    """Raised when a response cannot prove the required capability contract."""


class ApiRequestError(RuntimeError):
    """A sanitized API failure safe to persist as probe evidence."""

    def __init__(
        self,
        *,
        status: int | None,
        method: str,
        url: str,
        body: Any,
    ) -> None:
        self.status = status
        self.method = method
        self.url = url
        self.body = body
        status_text = "transport error" if status is None else f"HTTP {status}"
        super().__init__(f"{method} {url} failed with {status_text}")


Requester = Callable[..., Any]
Clock = Callable[[], str]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def decode_json_or_text(raw: bytes) -> Any:
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text[:4000]}


def request_json(
    *,
    method: str,
    url: str,
    token: str,
    api_version: str,
    payload: Any = None,
) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": api_version,
        "User-Agent": "design-studio-github-models-capability-probe",
    }
    data: bytes | None = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return decode_json_or_text(response.read())
    except urllib.error.HTTPError as exc:
        raise ApiRequestError(
            status=exc.code,
            method=method,
            url=url,
            body=decode_json_or_text(exc.read()),
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ApiRequestError(
            status=None,
            method=method,
            url=url,
            body={"message": f"{type(exc).__name__}: {exc}"},
        ) from exc


def normalize_catalog(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict) and isinstance(value.get("models"), list):
        value = value["models"]
    if not isinstance(value, list):
        raise ProbeContractError("catalog response must be an array of models")

    models: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            models.append(item)
    if not models:
        raise ProbeContractError("catalog response contains no model objects")
    return models


def supports_required_modalities(model: dict[str, Any]) -> bool:
    inputs = set(model.get("supported_input_modalities") or [])
    outputs = set(model.get("supported_output_modalities") or [])
    return {"text", "image"}.issubset(inputs) and "text" in outputs


def choose_model(
    catalog: Iterable[dict[str, Any]],
    *,
    preferred: Sequence[str] = DEFAULT_PREFERRED_MODELS,
) -> dict[str, Any]:
    eligible = {
        model.get("id"): model
        for model in catalog
        if isinstance(model.get("id"), str) and supports_required_modalities(model)
    }
    for model_id in preferred:
        if model_id in eligible:
            return eligible[model_id]
    if eligible:
        return eligible[sorted(eligible)[0]]
    raise ProbeContractError(
        "catalog exposes no text-and-image input model with text output"
    )


def structured_response_format(
    *,
    name: str,
    properties: dict[str, Any],
    required: list[str],
) -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


def build_text_payload(model_id: str) -> dict[str, Any]:
    return {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Return the capability probe receipt. Set probe to "
                    "'github-models' and status to 'ok'."
                ),
            }
        ],
        "temperature": 0,
        "max_tokens": 80,
        "response_format": structured_response_format(
            name="design_studio_structured_text_probe",
            properties={
                "probe": {"type": "string", "enum": ["github-models"]},
                "status": {"type": "string", "enum": ["ok"]},
            },
            required=["probe", "status"],
        ),
    }


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def build_split_color_png(*, width: int = 96, height: int = 48) -> bytes:
    if width < 2 or height < 1:
        raise ValueError("image dimensions must be at least 2x1")
    split = width // 2
    rows = bytearray()
    for _ in range(height):
        rows.append(0)
        for x in range(width):
            rows.extend((255, 0, 0) if x < split else (0, 0, 255))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
        + png_chunk(b"IEND", b"")
    )


def build_vision_payload(model_id: str, image: bytes) -> dict[str, Any]:
    image_url = "data:image/png;base64," + base64.b64encode(image).decode("ascii")
    return {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "This image has two solid vertical halves. Return the "
                            "lowercase basic English color on the left and on the right."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url, "detail": "low"},
                    },
                ],
            }
        ],
        "temperature": 0,
        "max_tokens": 80,
        "response_format": structured_response_format(
            name="design_studio_vision_probe",
            properties={
                "leftColor": {"type": "string"},
                "rightColor": {"type": "string"},
            },
            required=["leftColor", "rightColor"],
        ),
    }


def parse_completion_json(response: Any, label: str) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise ProbeContractError(f"{label} response must be an object")
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ProbeContractError(f"{label} response has no choices")
    first = choices[0]
    if not isinstance(first, dict) or not isinstance(first.get("message"), dict):
        raise ProbeContractError(f"{label} response has no assistant message")
    content = first["message"].get("content")
    if not isinstance(content, str) or not content.strip():
        raise ProbeContractError(f"{label} response content must be a non-empty string")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ProbeContractError(
            f"{label} response content is not structured JSON: {exc}"
        ) from exc
    if not isinstance(parsed, dict):
        raise ProbeContractError(f"{label} structured content must be an object")
    return parsed


def validate_text_result(value: dict[str, Any]) -> None:
    expected = {"probe": "github-models", "status": "ok"}
    if value != expected:
        raise ProbeContractError(
            f"structured-text probe returned unexpected content: {value!r}"
        )


def validate_vision_result(value: dict[str, Any]) -> None:
    normalized = {
        key: item.strip().lower() if isinstance(item, str) else item
        for key, item in value.items()
    }
    expected = {"leftColor": "red", "rightColor": "blue"}
    if normalized != expected:
        raise ProbeContractError(
            f"vision probe returned unexpected content: {value!r}"
        )


def classify_api_status(status: int | None) -> str:
    return "blocked" if status in BLOCKED_HTTP_STATUSES else "failed"


def usage_from(response: Any) -> Any:
    if isinstance(response, dict) and isinstance(response.get("usage"), dict):
        return response["usage"]
    return None


def selected_model_receipt(model: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": model.get("id"),
        "name": model.get("name"),
        "version": model.get("version"),
        "registry": model.get("registry"),
        "capabilities": model.get("capabilities") or [],
        "supportedInputModalities": model.get("supported_input_modalities") or [],
        "supportedOutputModalities": model.get("supported_output_modalities") or [],
        "limits": model.get("limits") or {},
    }


def request_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    receipt = dict(payload)
    messages = []
    for message in payload.get("messages", []):
        if not isinstance(message, dict):
            continue
        copied = dict(message)
        content = copied.get("content")
        if isinstance(content, list):
            redacted_content = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                copied_item = dict(item)
                image_url = copied_item.get("image_url")
                if isinstance(image_url, dict) and isinstance(image_url.get("url"), str):
                    copied_item["image_url"] = {
                        **image_url,
                        "url": "data:image/png;base64,<stored-as-probe-image.png>",
                    }
                redacted_content.append(copied_item)
            copied["content"] = redacted_content
        messages.append(copied)
    receipt["messages"] = messages
    return receipt


def error_receipt(error: Exception, step: str) -> dict[str, Any]:
    if isinstance(error, ApiRequestError):
        return {
            "step": step,
            "kind": "api",
            "httpStatus": error.status,
            "method": error.method,
            "url": error.url,
            "body": error.body,
            "message": str(error),
        }
    return {
        "step": step,
        "kind": "contract",
        "httpStatus": None,
        "message": f"{type(error).__name__}: {error}",
    }


def run_probe(
    *,
    token: str,
    output_dir: Path,
    requester: Requester = request_json,
    preferred_models: Sequence[str] = DEFAULT_PREFERRED_MODELS,
    catalog_url: str = CATALOG_URL,
    inference_url: str = INFERENCE_URL,
    api_version: str = API_VERSION,
    now: Clock = utc_now,
) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "status": "running",
        "startedAt": now(),
        "finishedAt": None,
        "apiVersion": api_version,
        "endpoints": {
            "catalog": catalog_url,
            "inference": inference_url,
        },
        "model": None,
        "checks": {
            "catalog": {"status": "pending"},
            "structuredText": {"status": "pending"},
            "vision": {"status": "pending"},
        },
        "error": None,
    }

    if not isinstance(token, str) or not token.strip():
        report["status"] = "blocked"
        report["error"] = {
            "step": "authentication",
            "kind": "configuration",
            "httpStatus": None,
            "message": "GITHUB_TOKEN is required for the capability probe",
        }
        report["finishedAt"] = now()
        write_json(output_dir / "capability-report.json", report)
        return report

    current_step = "catalog"
    try:
        catalog_response = requester(
            method="GET",
            url=catalog_url,
            token=token,
            api_version=api_version,
        )
        write_json(output_dir / "catalog-response.json", catalog_response)
        catalog = normalize_catalog(catalog_response)
        selected = choose_model(catalog, preferred=preferred_models)
        report["model"] = selected_model_receipt(selected)
        report["checks"]["catalog"] = {
            "status": "passed",
            "modelCount": len(catalog),
            "selectedModel": selected.get("id"),
        }

        current_step = "structuredText"
        text_payload = build_text_payload(str(selected["id"]))
        write_json(
            output_dir / "structured-text-request.json",
            request_receipt(text_payload),
        )
        text_response = requester(
            method="POST",
            url=inference_url,
            token=token,
            api_version=api_version,
            payload=text_payload,
        )
        write_json(output_dir / "structured-text-response.json", text_response)
        text_result = parse_completion_json(text_response, "structured-text")
        validate_text_result(text_result)
        report["checks"]["structuredText"] = {
            "status": "passed",
            "result": text_result,
            "usage": usage_from(text_response),
        }

        current_step = "vision"
        image = build_split_color_png()
        (output_dir / "probe-image.png").write_bytes(image)
        vision_payload = build_vision_payload(str(selected["id"]), image)
        write_json(
            output_dir / "vision-request.json",
            request_receipt(vision_payload),
        )
        vision_response = requester(
            method="POST",
            url=inference_url,
            token=token,
            api_version=api_version,
            payload=vision_payload,
        )
        write_json(output_dir / "vision-response.json", vision_response)
        vision_result = parse_completion_json(vision_response, "vision")
        validate_vision_result(vision_result)
        report["checks"]["vision"] = {
            "status": "passed",
            "result": vision_result,
            "usage": usage_from(vision_response),
        }
        report["status"] = "passed"
    except (ApiRequestError, ProbeContractError) as error:
        status = (
            classify_api_status(error.status)
            if isinstance(error, ApiRequestError)
            else "failed"
        )
        report["status"] = status
        report["checks"][current_step] = {
            "status": status,
            "message": str(error),
        }
        report["error"] = error_receipt(error, current_step)
        write_json(output_dir / f"{current_step}-error.json", report["error"])
    except Exception as error:
        report["status"] = "failed"
        report["checks"][current_step] = {
            "status": "failed",
            "message": f"{type(error).__name__}: {error}",
        }
        report["error"] = error_receipt(error, current_step)
        write_json(output_dir / f"{current_step}-error.json", report["error"])

    report["finishedAt"] = now()
    write_json(output_dir / "capability-report.json", report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Probe whether GitHub Actions can provide the text, strict structured-output "
            "and vision capabilities required by the Milestone 0 comparison harness."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("harness-output") / "benchmarks" / "milestone-0" / "model-capability",
    )
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help="Preferred model ID. Repeat to define fallback order.",
    )
    parser.add_argument("--catalog-url", default=CATALOG_URL)
    parser.add_argument("--inference-url", default=INFERENCE_URL)
    parser.add_argument("--api-version", default=API_VERSION)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_probe(
        token=os.environ.get("GITHUB_TOKEN", ""),
        output_dir=args.output_dir,
        preferred_models=tuple(args.models or DEFAULT_PREFERRED_MODELS),
        catalog_url=args.catalog_url,
        inference_url=args.inference_url,
        api_version=args.api_version,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "model": (report.get("model") or {}).get("id"),
                "report": str((args.output_dir / "capability-report.json").resolve()),
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
