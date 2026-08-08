#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Sequence


class ContractError(RuntimeError):
    """Raised when a comparison lane violates the frozen benchmark contract."""


DIRECTOR_GUIDANCE = "skills/design-studio/agents/design-agent.md"
BUILDER_GUIDANCE = "skills/design-studio/references/generation.md"
LANE_CONTRACTS = {
    "impeccable-alone": {
        "workflow": "impeccable",
        "mechanicalProvider": "impeccable",
    },
    "design-studio-current": {
        "workflow": "design-studio",
        "mechanicalProvider": "fallback",
    },
    "design-studio-impeccable": {
        "workflow": "design-studio",
        "mechanicalProvider": "impeccable",
    },
}
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
ALLOWED_SUFFIXES = {".html", ".css", ".js", ".json", ".svg", ".txt"}
MAX_FILES = 24
MAX_BYTES = 750_000
EXTERNAL_NETWORK = re.compile(r"(?:https?:)?//[A-Za-z0-9]", re.IGNORECASE)


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"{label} is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be a JSON object")
    return value


def _safe_input_file(run_dir: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ContractError(f"{label} must be a non-empty POSIX path")
    relative = PurePosixPath(value)
    if (
        relative.is_absolute()
        or not relative.parts
        or ".." in relative.parts
        or any(part.startswith(".") for part in relative.parts)
    ):
        raise ContractError(f"{label} path is unsafe: {value}")

    input_root = run_dir / "input"
    if input_root.is_symlink() or not input_root.is_dir():
        raise ContractError(f"immutable input tree is missing or unsafe: {input_root}")
    candidate = input_root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ContractError(f"{label} path contains a symlink: {value}")
    if not candidate.is_file():
        raise ContractError(f"{label} is missing or unsafe: {value}")
    try:
        candidate.resolve().relative_to(input_root.resolve())
    except (OSError, ValueError) as exc:
        raise ContractError(f"{label} escapes the immutable input tree: {value}") from exc
    return candidate


def resolve_lane_contract(run_dir: Path) -> dict[str, str]:
    run_path = run_dir / "run.json"
    if run_path.is_symlink() or not run_path.is_file():
        raise ContractError(f"run receipt is missing or unsafe: {run_path}")
    run = _load_json(run_path, "run receipt")
    fixture = _load_json(_safe_input_file(run_dir, "fixture.json", "fixture"), "fixture")

    lane_value = run.get("lane")
    lane_id = lane_value.get("id") if isinstance(lane_value, dict) else None
    if not isinstance(lane_id, str) or lane_id not in LANE_CONTRACTS:
        raise ContractError(f"unsupported comparison lane: {lane_id!r}")

    run_fixture = run.get("fixture")
    if not isinstance(run_fixture, dict):
        raise ContractError("run receipt fixture identity is missing")
    expected_identity = (fixture.get("id"), fixture.get("version"))
    recorded_identity = (run_fixture.get("id"), run_fixture.get("version"))
    if recorded_identity != expected_identity:
        raise ContractError(
            "run receipt fixture identity does not match immutable input: "
            f"recorded={recorded_identity!r} input={expected_identity!r}"
        )

    return {"id": lane_id, **LANE_CONTRACTS[lane_id]}


def _guidance(root: Path, paths: Sequence[str], source: str, revision: str) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    sections: list[str] = []
    for relative_value in paths:
        relative = PurePosixPath(relative_value)
        if relative.is_absolute() or ".." in relative.parts:
            raise ContractError(f"unsafe guidance path: {relative_value}")
        path = root.joinpath(*relative.parts)
        if path.is_symlink() or not path.is_file():
            raise ContractError(f"guidance file is missing or unsafe: {relative_value}")
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        files.append(
            {"path": relative.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        )
        sections.append(f"--- GUIDANCE {relative.as_posix()} ---\n{text}")
    return {"source": source, "revision": revision, "files": files, "content": "\n\n".join(sections)}


def _fixture_context(run_dir: Path) -> dict[str, Any]:
    fixture = _load_json(_safe_input_file(run_dir, "fixture.json", "fixture"), "fixture")
    brief_name = fixture.get("brief", "brief.md")
    acceptance_name = fixture.get("acceptance", "acceptance.json")
    brief = _safe_input_file(run_dir, brief_name, "brief").read_text(encoding="utf-8")
    acceptance = _load_json(
        _safe_input_file(run_dir, acceptance_name, "acceptance"),
        "acceptance",
    )
    return {"fixture": fixture, "brief": brief, "acceptance": acceptance}


def _source_tree(run_dir: Path) -> dict[str, Any]:
    work = run_dir / "work"
    files: list[dict[str, Any]] = []
    sections: list[str] = []
    for path in sorted(work.rglob("*")):
        if path.is_symlink():
            raise ContractError(f"source tree may not contain symlinks: {path}")
        if not path.is_file():
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        relative = path.relative_to(work).as_posix()
        files.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        sections.append(f"--- SOURCE {relative} ---\n{text}")
    return {"files": files, "content": "\n\n".join(sections) if sections else "(greenfield)"}


def build_director_packet(repo_root: Path, run_dir: Path, design_revision: str) -> dict[str, Any]:
    lane = resolve_lane_contract(run_dir)
    if lane["workflow"] != "design-studio":
        raise ContractError(f"lane {lane['id']} does not use the Design Studio Director")
    context = _fixture_context(run_dir)
    return {
        "role": "source-blind-visual-director",
        "lane": lane,
        "brief": context["brief"],
        "acceptance": context["acceptance"],
        "guidance": _guidance(repo_root, (DIRECTOR_GUIDANCE,), "George-RD/design-studio", design_revision),
        "instructions": "Return exactly three materially different visual directions. Do not rank or select them. You have no source-code access.",
    }


def build_builder_packet(
    repo_root: Path,
    run_dir: Path,
    selected_direction: dict[str, Any],
    design_revision: str,
    mechanical_provider: str,
) -> dict[str, Any]:
    lane = resolve_lane_contract(run_dir)
    if lane["workflow"] != "design-studio":
        raise ContractError(f"lane {lane['id']} does not use the Design Studio Builder")
    if mechanical_provider != lane["mechanicalProvider"]:
        raise ContractError(
            f"lane {lane['id']} requires mechanical provider "
            f"{lane['mechanicalProvider']!r}, not {mechanical_provider!r}"
        )
    context = _fixture_context(run_dir)
    return {
        "role": "source-aware-builder",
        "lane": lane,
        "brief": context["brief"],
        "acceptance": context["acceptance"],
        "guidance": _guidance(repo_root, (BUILDER_GUIDANCE,), "George-RD/design-studio", design_revision),
        "selectedDirection": selected_direction,
        "baselineSource": _source_tree(run_dir),
        "mechanicalProvider": mechanical_provider,
        "outputContract": context["fixture"].get("outputContract"),
        "instructions": "Implement only the assigned direction as complete static local files. No external network assets or build step.",
    }


def build_impeccable_packet(impeccable_root: Path, run_dir: Path, impeccable_revision: str) -> dict[str, Any]:
    lane = resolve_lane_contract(run_dir)
    if lane["workflow"] != "impeccable":
        raise ContractError(f"lane {lane['id']} does not use the standalone Impeccable workflow")
    context = _fixture_context(run_dir)
    kind = str(context["fixture"].get("kind"))
    if kind not in IMPECCABLE_GUIDANCE_BY_KIND:
        raise ContractError(f"unsupported fixture kind for Impeccable: {kind}")
    package = _load_json(impeccable_root / "package.json", "Impeccable package")
    if package.get("name") != "impeccable" or not isinstance(package.get("version"), str):
        raise ContractError("Impeccable package identity is invalid")
    guidance = _guidance(
        impeccable_root,
        IMPECCABLE_GUIDANCE_BY_KIND[kind],
        "pbakaus/impeccable",
        impeccable_revision,
    )
    guidance["packageVersion"] = package["version"]
    return {
        "role": "impeccable-builder",
        "lane": lane,
        "brief": context["brief"],
        "acceptance": context["acceptance"],
        "guidance": guidance,
        "baselineSource": _source_tree(run_dir),
        "outputContract": context["fixture"].get("outputContract"),
        "instructions": "Apply the pinned Impeccable method and return complete static local files. No Design Studio guidance.",
    }


def select_direction(directions: Sequence[dict[str, Any]], seed: str) -> dict[str, Any]:
    if len(directions) != 3 or any(not isinstance(item, dict) for item in directions):
        raise ContractError("director must return exactly three direction objects")
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    index = int.from_bytes(digest[:8], "big") % 3
    return {
        "selectionMethod": "sha256-mod-3",
        "seedDigest": hashlib.sha256(seed.encode("utf-8")).hexdigest(),
        "selectedIndex": index,
        "direction": directions[index],
    }


def _validate_path(value: Any) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ContractError("generated file path must be a non-empty POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or any(part.startswith(".") for part in path.parts):
        raise ContractError(f"generated file path is unsafe: {value}")
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ContractError(f"generated file type is unsupported: {value}")
    return path


def validate_bundle(bundle: dict[str, Any]) -> list[dict[str, str]]:
    if not isinstance(bundle, dict) or set(bundle) != {"files"}:
        raise ContractError("file bundle must contain exactly files")
    files = bundle.get("files")
    if not isinstance(files, list) or not files or len(files) > MAX_FILES:
        raise ContractError(f"file bundle must contain 1-{MAX_FILES} files")
    validated: list[dict[str, str]] = []
    seen: set[str] = set()
    total = 0
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "content"}:
            raise ContractError("each generated file must contain exactly path and content")
        path = _validate_path(item.get("path")).as_posix()
        content = item.get("content")
        if not isinstance(content, str):
            raise ContractError(f"generated file must be text: {path}")
        if path in seen:
            raise ContractError(f"duplicate generated path: {path}")
        if EXTERNAL_NETWORK.search(content):
            raise ContractError(f"generated output requires external network access: {path}")
        seen.add(path)
        total += len(content.encode("utf-8"))
        validated.append({"path": path, "content": content})
    if "index.html" not in seen:
        raise ContractError("generated output must include index.html")
    if total > MAX_BYTES:
        raise ContractError(f"generated output exceeds {MAX_BYTES} UTF-8 bytes")
    return validated
