#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
from typing import Any, Callable, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from probe_github_models import (  # noqa: E402
    API_VERSION,
    INFERENCE_URL,
    parse_completion_json,
    request_json,
    request_receipt,
    structured_response_format,
    usage_from,
    write_json,
)


LANES = {
    "impeccable-alone",
    "design-studio-current",
    "design-studio-impeccable",
}
DESIGN_STUDIO_DIRECTOR_PATH = "skills/design-studio/agents/design-agent.md"
DESIGN_STUDIO_BUILDER_PATH = "skills/design-studio/references/generation.md"
IMPECCABLE_GUIDANCE_BY_KIND = {
    "new-marketing-surface": (
        "skill/SKILL.src.md",
        "skill/reference/new-work.md",
        "skill/reference/craft-floor.md",
    ),
    "existing-product-overhaul": (
        "skill/SKILL.src.md",
        "skill/reference/new-work.md",
        "skill/reference/operate.md",
        "skill/reference/craft-floor.md",
    ),
    "review-and-polish": (
        "skill/SKILL.src.md",
        "skill/reference/polish.md",
        "skill/reference/audit.md",
        "skill/reference/craft-floor.md",
    ),
    "new-visually-ambitious-experience": (
        "skill/SKILL.src.md",
        "skill/reference/new-work.md",
        "skill/reference/overdrive.md",
        "skill/reference/animate.md",
        "skill/reference/craft-floor.md",
    ),
}
ALLOWED_OUTPUT_SUFFIXES = {
    ".html",
    ".css",
    ".js",
    ".json",
    ".svg",
    ".txt",
}
MAX_OUTPUT_FILES = 24
MAX_TOTAL_OUTPUT_BYTES = 750_000
EXTERNAL_NETWORK_PATTERN = re.compile(
    r"(?:https?:)?//[A-Za-z0-9]",
    flags=re.IGNORECASE,
)


class AgentContractError(RuntimeError):
    """Raised when a comparison role or generated artifact violates the run contract."""


Requester = Callable[..., Any]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise AgentContractError(f"{label} is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AgentContractError(f"{label} contains invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise AgentContractError(f"{label} must contain a JSON object")
    return value


def ensure_inside(root: Path, candidate: Path, label: str) -> Path:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    if not resolved_candidate.is_relative_to(resolved_root):
        raise AgentContractError(f"{label} escapes its allowed root: {candidate}")
    return resolved_candidate


def source_guidance(
    *,
    root: Path,
    paths: Sequence[str],
    source: str,
    revision: str,
    package_version: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    files: list[dict[str, Any]] = []
    sections: list[str] = []
    for relative_value in paths:
        relative = PurePosixPath(relative_value)
        if relative.is_absolute() or ".." in relative.parts:
            raise AgentContractError(f"unsafe guidance path: {relative_value}")
        path = ensure_inside(root, root / Path(*relative.parts), "guidance path")
        if not path.is_file() or path.is_symlink():
            raise AgentContractError(f"guidance file is missing or unsafe: {relative_value}")
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AgentContractError(f"guidance file is not UTF-8 text: {relative_value}") from exc
        files.append(
            {
                "path": relative.as_posix(),
                "sha256": sha256_bytes(raw),
                "bytes": len(raw),
            }
        )
        sections.append(f"--- GUIDANCE {relative.as_posix()} ---\n{text}")
    receipt: dict[str, Any] = {
        "source": source,
        "revision": revision,
        "files": files,
        "content": "\n\n".join(sections),
    }
    if package_version is not None:
        receipt["packageVersion"] = package_version
    return receipt


def fixture_context(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    fixture = load_json_object(run_dir / "input" / "fixture.json", "fixture manifest")
    brief_path = run_dir / "input" / str(fixture.get("brief", "brief.md"))
    acceptance_path = run_dir / "input" / str(
        fixture.get("acceptance", "acceptance.json")
    )
    try:
        brief = brief_path.read_text()
    except FileNotFoundError as exc:
        raise AgentContractError(f"fixture brief is missing: {brief_path}") from exc
    acceptance = load_json_object(acceptance_path, "fixture acceptance contract")
    return {
        "fixture": fixture,
        "brief": brief,
        "acceptance": acceptance,
    }


def collect_source_tree(work_dir: Path) -> dict[str, Any]:
    work_dir = work_dir.resolve()
    files: list[dict[str, Any]] = []
    sections: list[str] = []
    for path in sorted(work_dir.rglob("*")):
        if path.is_symlink():
            raise AgentContractError(f"source tree may not contain symlinks: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(work_dir).as_posix()
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AgentContractError(f"source file is not UTF-8 text: {relative}") from exc
        files.append(
            {
                "path": relative,
                "sha256": sha256_bytes(raw),
                "bytes": len(raw),
            }
        )
        sections.append(f"--- SOURCE {relative} ---\n{text}")
    return {
        "files": files,
        "content": "\n\n".join(sections) if sections else "(greenfield: no baseline files)",
    }


def build_director_packet(
    *,
    repo_root: Path,
    run_dir: Path,
    design_studio_revision: str,
) -> dict[str, Any]:
    context = fixture_context(run_dir)
    guidance = source_guidance(
        root=repo_root,
        paths=(DESIGN_STUDIO_DIRECTOR_PATH,),
        source="George-RD/design-studio",
        revision=design_studio_revision,
    )
    return {
        "role": "source-blind-visual-director",
        "boundary": {
            "canAccessSource": False,
            "sourcePaths": [],
            "forbiddenInputs": [
                "baseline source code",
                "builder reasoning",
                "other lane outputs",
            ],
        },
        "guidance": guidance,
        "brief": context["brief"],
        "acceptance": context["acceptance"],
        "fixture": {
            "id": context["fixture"].get("id"),
            "version": context["fixture"].get("version"),
            "kind": context["fixture"].get("kind"),
            "viewports": context["fixture"].get("viewports"),
        },
        "instructions": (
            "Propose exactly three materially different visual directions. Do not rank "
            "them and do not select one. Make each direction implementation-ready and "
            "specific to the supplied brief. Do not assume access to source code."
        ),
    }


def build_design_studio_builder_packet(
    *,
    repo_root: Path,
    run_dir: Path,
    selected_direction: dict[str, Any],
    design_studio_revision: str,
    mechanical_provider: str,
) -> dict[str, Any]:
    context = fixture_context(run_dir)
    guidance = source_guidance(
        root=repo_root,
        paths=(DESIGN_STUDIO_BUILDER_PATH,),
        source="George-RD/design-studio",
        revision=design_studio_revision,
    )
    source_tree = collect_source_tree(run_dir / "work")
    return {
        "role": "source-aware-builder",
        "boundary": {
            "canAccessSource": True,
            "sourcePaths": [item["path"] for item in source_tree["files"]],
            "forbiddenInputs": [
                "other direction candidates",
                "evaluator reasoning",
                "other lane outputs",
            ],
        },
        "guidance": guidance,
        "mechanicalProvider": mechanical_provider,
        "brief": context["brief"],
        "acceptance": context["acceptance"],
        "selectedDirection": selected_direction,
        "baselineSource": source_tree,
        "outputContract": context["fixture"].get("outputContract"),
        "instructions": (
            "Implement the assigned direction as complete static local files. Preserve "
            "declared behavior and element IDs. Return every required file in the strict "
            "file bundle. Do not use external network assets, package installs, build "
            "steps, data URLs, base64 blobs, or fabricated claims."
        ),
    }


def impeccable_paths_for_kind(kind: str) -> tuple[str, ...]:
    try:
        return IMPECCABLE_GUIDANCE_BY_KIND[kind]
    except KeyError as exc:
        raise AgentContractError(f"unsupported fixture kind for Impeccable: {kind}") from exc


def build_impeccable_builder_packet(
    *,
    impeccable_root: Path,
    run_dir: Path,
    impeccable_revision: str,
) -> dict[str, Any]:
    context = fixture_context(run_dir)
    kind = str(context["fixture"].get("kind"))
    package = load_json_object(impeccable_root / "package.json", "Impeccable package")
    if package.get("name") != "impeccable":
        raise AgentContractError("Impeccable checkout package name is invalid")
    package_version = package.get("version")
    if not isinstance(package_version, str) or not package_version:
        raise AgentContractError("Impeccable package version is missing")
    guidance = source_guidance(
        root=impeccable_root,
        paths=impeccable_paths_for_kind(kind),
        source="pbakaus/impeccable",
        revision=impeccable_revision,
        package_version=package_version,
    )
    source_tree = collect_source_tree(run_dir / "work")
    return {
        "role": "impeccable-builder",
        "boundary": {
            "canAccessSource": True,
            "sourcePaths": [item["path"] for item in source_tree["files"]],
            "forbiddenInputs": [
                "Design Studio guidance",
                "other lane outputs",
            ],
        },
        "guidance": guidance,
        "brief": context["brief"],
        "acceptance": context["acceptance"],
        "baselineSource": source_tree,
        "outputContract": context["fixture"].get("outputContract"),
        "instructions": (
            "Apply the pinned Impeccable method to build or polish the requested static "
            "surface. Return every required file in the strict file bundle. Do not use "
            "external network assets, package installs, build steps, data URLs, base64 "
            "blobs, or fabricated claims."
        ),
    }


def direction_schema() -> dict[str, Any]:
    direction_properties = {
        "name": {"type": "string"},
        "thesis": {"type": "string"},
        "visualWorld": {"type": "string"},
        "materials": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "palette": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 2,
        },
        "typography": {"type": "string"},
        "composition": {"type": "string"},
        "signatureInteraction": {"type": "string"},
        "responsiveStrategy": {"type": "string"},
        "risks": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "proof": {"type": "string"},
    }
    return {
        "type": "object",
        "properties": {
            "directions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": direction_properties,
                    "required": list(direction_properties),
                    "additionalProperties": False,
                },
                "minItems": 3,
                "maxItems": 3,
            }
        },
        "required": ["directions"],
        "additionalProperties": False,
    }


def file_bundle_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                    "additionalProperties": False,
                },
                "minItems": 1,
                "maxItems": MAX_OUTPUT_FILES,
            },
            "assumptions": {
                "type": "array",
                "items": {"type": "string"},
            },
            "implementationSummary": {"type": "string"},
        },
        "required": ["files", "assumptions", "implementationSummary"],
        "additionalProperties": False,
    }


def select_direction(
    directions: Sequence[dict[str, Any]],
    seed: str,
) -> dict[str, Any]:
    if len(directions) != 3:
        raise AgentContractError("director must return exactly three directions")
    if any(not isinstance(item, dict) for item in directions):
        raise AgentContractError("every direction must be an object")
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    index = int.from_bytes(digest[:8], "big") % 3
    return {
        "selectionMethod": "sha256-mod-3",
        "seedDigest": hashlib.sha256(seed.encode("utf-8")).hexdigest(),
        "selectedIndex": index,
        "direction": directions[index],
    }


def validate_output_path(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise AgentContractError("generated file path must be a non-empty string")
    if "\\" in value:
        raise AgentContractError(f"generated file path must use POSIX separators: {value}")
    relative = PurePosixPath(value)
    if relative.is_absolute() or value.startswith("/") or ".." in relative.parts:
        raise AgentContractError(f"generated file path escapes output root: {value}")
    if any(part in {"", "."} or part.startswith(".") for part in relative.parts):
        raise AgentContractError(f"generated hidden or ambiguous path is not allowed: {value}")
    if relative.suffix.lower() not in ALLOWED_OUTPUT_SUFFIXES:
        raise AgentContractError(f"generated file type is not allowed: {value}")
    return relative


def validate_file_bundle(bundle: dict[str, Any]) -> list[tuple[PurePosixPath, str]]:
    if not isinstance(bundle, dict):
        raise AgentContractError("generated file bundle must be an object")
    if set(bundle) != {"files", "assumptions", "implementationSummary"}:
        raise AgentContractError("generated file bundle has unexpected or missing fields")
    files = bundle.get("files")
    assumptions = bundle.get("assumptions")
    summary = bundle.get("implementationSummary")
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_OUTPUT_FILES:
        raise AgentContractError(
            f"generated file bundle must contain 1 to {MAX_OUTPUT_FILES} files"
        )
    if not isinstance(assumptions, list) or any(
        not isinstance(item, str) for item in assumptions
    ):
        raise AgentContractError("generated assumptions must be an array of strings")
    if not isinstance(summary, str) or not summary.strip():
        raise AgentContractError("implementationSummary must be a non-empty string")

    normalized: list[tuple[PurePosixPath, str]] = []
    seen: set[str] = set()
    total_bytes = 0
    for index, item in enumerate(files):
        if not isinstance(item, dict) or set(item) != {"path", "content"}:
            raise AgentContractError(
                f"generated files[{index}] must contain only path and content"
            )
        relative = validate_output_path(item.get("path"))
        relative_value = relative.as_posix()
        if relative_value in seen:
            raise AgentContractError(f"duplicate generated file path: {relative_value}")
        seen.add(relative_value)
        content = item.get("content")
        if not isinstance(content, str):
            raise AgentContractError(f"generated file content must be text: {relative_value}")
        if EXTERNAL_NETWORK_PATTERN.search(content):
            raise AgentContractError(
                f"generated output requires external network access: {relative_value}"
            )
        raw = content.encode("utf-8")
        total_bytes += len(raw)
        if total_bytes > MAX_TOTAL_OUTPUT_BYTES:
            raise AgentContractError(
                f"generated file bundle exceeds {MAX_TOTAL_OUTPUT_BYTES}-byte size limit"
            )
        normalized.append((relative, content))
    if "index.html" not in seen:
        raise AgentContractError("generated file bundle must contain index.html")
    return normalized


def materialize_file_bundle(bundle: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    if not output_dir.is_dir():
        raise AgentContractError(f"output directory is missing: {output_dir}")
    if any(output_dir.iterdir()):
        raise AgentContractError("output directory must be empty before generation")
    normalized = validate_file_bundle(bundle)

    temporary = Path(tempfile.mkdtemp(prefix=".generated-", dir=output_dir.parent))
    try:
        receipts: list[dict[str, Any]] = []
        for relative, content in normalized:
            target = ensure_inside(temporary, temporary / Path(*relative.parts), "output file")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            raw = target.read_bytes()
            receipts.append(
                {
                    "path": relative.as_posix(),
                    "sha256": sha256_bytes(raw),
                    "bytes": len(raw),
                }
            )
        output_dir.rmdir()
        temporary.replace(output_dir)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {
        "algorithm": "sha256",
        "files": receipts,
        "totalBytes": sum(item["bytes"] for item in receipts),
    }


def call_structured_role(
    *,
    role: str,
    model: str,
    token: str,
    packet: dict[str, Any],
    schema: dict[str, Any],
    evidence_dir: Path,
    requester: Requester = request_json,
) -> dict[str, Any]:
    if not token:
        raise AgentContractError("GITHUB_TOKEN is required for comparison generation")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are one isolated role in a controlled design benchmark. Follow "
                    "only the supplied packet. Return only the requested strict JSON."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(packet, sort_keys=True),
            },
        ],
        "temperature": 0.6 if role == "director" else 0.2,
        "max_tokens": 16_000,
        "response_format": structured_response_format(
            name=f"design_studio_{role.replace('-', '_')}",
            properties=schema["properties"],
            required=schema["required"],
        ),
    }
    # Preserve additionalProperties/min/max constraints from the complete schema.
    payload["response_format"]["json_schema"]["schema"] = schema
    write_json(evidence_dir / f"{role}-request.json", request_receipt(payload))
    response = requester(
        method="POST",
        url=INFERENCE_URL,
        token=token,
        api_version=API_VERSION,
        payload=payload,
    )
    write_json(evidence_dir / f"{role}-response.json", response)
    content = parse_completion_json(response, role)
    return {
        "content": content,
        "usage": usage_from(response),
    }


def run_generation(
    *,
    repo_root: Path,
    impeccable_root: Path,
    run_dir: Path,
    lane_id: str,
    model: str,
    token: str,
    design_studio_revision: str,
    impeccable_revision: str,
    requester: Requester = request_json,
) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    repo_root = repo_root.resolve()
    impeccable_root = impeccable_root.resolve()
    if lane_id not in LANES:
        raise AgentContractError(f"unsupported comparison lane: {lane_id}")
    run = load_json_object(run_dir / "run.json", "run manifest")
    recorded_lane = (run.get("lane") or {}).get("id")
    if recorded_lane != lane_id:
        raise AgentContractError(
            f"lane mismatch: run records {recorded_lane!r}, requested {lane_id!r}"
        )
    if run.get("status") != "prepared":
        raise AgentContractError(
            f"comparison generation requires a prepared run; got {run.get('status')!r}"
        )
    output_dir = run_dir / "output"
    if not output_dir.is_dir() or any(output_dir.iterdir()):
        raise AgentContractError("prepared run output directory must exist and be empty")

    evidence_dir = run_dir / "evidence" / "agent"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    role_receipts: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None

    if lane_id == "impeccable-alone":
        mechanical_provider = "impeccable"
        builder_packet = build_impeccable_builder_packet(
            impeccable_root=impeccable_root,
            run_dir=run_dir,
            impeccable_revision=impeccable_revision,
        )
    else:
        mechanical_provider = (
            "impeccable" if lane_id == "design-studio-impeccable" else "fallback"
        )
        director_packet = build_director_packet(
            repo_root=repo_root,
            run_dir=run_dir,
            design_studio_revision=design_studio_revision,
        )
        director_result = call_structured_role(
            role="director",
            model=model,
            token=token,
            packet=director_packet,
            schema=direction_schema(),
            evidence_dir=evidence_dir,
            requester=requester,
        )
        directions = director_result["content"].get("directions")
        if not isinstance(directions, list):
            raise AgentContractError("director response has no directions array")
        context = fixture_context(run_dir)
        seed = (
            f"{context['fixture'].get('id')}:v{context['fixture'].get('version')}:"
            f"{run.get('runId')}"
        )
        selected = select_direction(directions, seed)
        write_json(evidence_dir / "selected-direction.json", selected)
        role_receipts.append(
            {
                "role": "director",
                "boundary": director_packet["boundary"],
                "guidance": {
                    key: value
                    for key, value in director_packet["guidance"].items()
                    if key != "content"
                },
                "usage": director_result["usage"],
            }
        )
        builder_packet = build_design_studio_builder_packet(
            repo_root=repo_root,
            run_dir=run_dir,
            selected_direction=selected["direction"],
            design_studio_revision=design_studio_revision,
            mechanical_provider=mechanical_provider,
        )

    builder_result = call_structured_role(
        role="builder",
        model=model,
        token=token,
        packet=builder_packet,
        schema=file_bundle_schema(),
        evidence_dir=evidence_dir,
        requester=requester,
    )
    output_manifest = materialize_file_bundle(
        builder_result["content"],
        output_dir,
    )
    role_receipts.append(
        {
            "role": "builder",
            "boundary": builder_packet["boundary"],
            "guidance": {
                key: value
                for key, value in builder_packet["guidance"].items()
                if key != "content"
            },
            "usage": builder_result["usage"],
        }
    )

    report = {
        "schemaVersion": 1,
        "status": "generated",
        "runId": run.get("runId"),
        "fixture": run.get("fixture"),
        "lane": lane_id,
        "model": model,
        "roles": [item["role"] for item in role_receipts],
        "roleReceipts": role_receipts,
        "mechanicalProvider": mechanical_provider,
        "selectedDirection": selected,
        "outputManifest": output_manifest,
        "nextRequiredEvidence": [
            "browser screenshots",
            "functional interaction checks",
            "mechanical findings",
            "source-blind visual evaluation",
        ],
    }
    write_json(evidence_dir / "generation-report.json", report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate one isolated Milestone 0 comparison lane output."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate")
    generate.add_argument("--run-dir", type=Path)
    generate.add_argument("--repo-root", type=Path, default=SCRIPT_DIR.parent)
    generate.add_argument("--impeccable-root", type=Path, required=True)
    generate.add_argument("--lane", choices=sorted(LANES))
    generate.add_argument("--model", default="openai/gpt-4.1")
    generate.add_argument("--design-studio-revision", required=True)
    generate.add_argument("--impeccable-revision", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_dir = args.run_dir or Path(os.environ.get("DESIGN_BENCHMARK_RUN_DIR", ""))
    lane = args.lane or os.environ.get("DESIGN_BENCHMARK_LANE", "")
    try:
        report = run_generation(
            repo_root=args.repo_root,
            impeccable_root=args.impeccable_root,
            run_dir=run_dir,
            lane_id=lane,
            model=args.model,
            token=os.environ.get("GITHUB_TOKEN", ""),
            design_studio_revision=args.design_studio_revision,
            impeccable_revision=args.impeccable_revision,
        )
    except AgentContractError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": report["status"],
                "lane": report["lane"],
                "roles": report["roles"],
                "outputFiles": len(report["outputManifest"]["files"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
