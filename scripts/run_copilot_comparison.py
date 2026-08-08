#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from html import unescape
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
from typing import Any, Sequence
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


class ContractError(RuntimeError):
    """Raised when a comparison lane violates the frozen benchmark contract."""


DIRECTOR_GUIDANCE = "skills/design-studio/agents/design-agent.md"
BUILDER_GUIDANCE = "skills/design-studio/references/generation.md"
DIRECT_HEADINGS = (
    "THESIS",
    "FIRST VIEWPORT",
    "VISITOR PATH",
    "VISUAL WORLD",
    "TYPOGRAPHY",
    "COLOUR",
    "SPATIAL RHYTHM",
    "MOTION",
    "INTERACTION STATES",
    "RESPONSIVE BEHAVIOUR",
    "SIGNATURE MOMENT",
    "ANTI-GOALS",
)
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
URL_ATTRIBUTES = {
    "action",
    "background",
    "cite",
    "data",
    "formaction",
    "href",
    "poster",
    "src",
}
NETWORK_RELEVANT_TAGS = {
    "audio",
    "embed",
    "form",
    "iframe",
    "img",
    "link",
    "object",
    "script",
    "source",
    "style",
    "track",
    "video",
}
REQUIRED_CSP_DIRECTIVES = {
    "default-src": ("'none'",),
    "base-uri": ("'none'",),
    "connect-src": ("'none'",),
    "form-action": ("'none'",),
    "frame-src": ("'none'",),
    "object-src": ("'none'",),
}
SAFE_CSP_SOURCE_TOKENS = {
    "'none'",
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'",
    "'unsafe-hashes'",
    "'report-sample'",
    "data:",
    "blob:",
}
NETWORK_API_PATTERNS = {
    "fetch": re.compile(r"(?<![\w$])fetch\s*\(", re.IGNORECASE),
    "XMLHttpRequest": re.compile(r"\bXMLHttpRequest\b", re.IGNORECASE),
    "WebSocket": re.compile(r"\bWebSocket\s*\(", re.IGNORECASE),
    "EventSource": re.compile(r"\bEventSource\s*\(", re.IGNORECASE),
    "sendBeacon": re.compile(r"\bsendBeacon\s*\(", re.IGNORECASE),
    "window.open": re.compile(r"\bwindow\s*\.\s*open\s*\(", re.IGNORECASE),
    "location.assign": re.compile(r"\blocation\s*\.\s*assign\s*\(", re.IGNORECASE),
    "location.replace": re.compile(r"\blocation\s*\.\s*replace\s*\(", re.IGNORECASE),
    "location write": re.compile(
        r"\b(?:window\s*\.\s*)?(?:document\s*\.\s*)?location(?:\s*\.\s*href)?\s*=",
        re.IGNORECASE,
    ),
}
CSS_ESCAPE = re.compile(r"\\([0-9a-fA-F]{1,6})(?:\s)?|\\(.)", re.DOTALL)
CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE | re.DOTALL)
CSS_IMPORT = re.compile(r"@import\s+(['\"])(.*?)\1", re.IGNORECASE | re.DOTALL)
MARKDOWN_HEADING = re.compile(r"(?m)^#{1,6}[ \t]+([A-Z][A-Z0-9 -]*?)[ \t]*$")


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


def _require_path(value: Any, label: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{label} must be pathlib.Path")
    return value


def _safe_input_file(run_dir: Path, value: Any, label: str) -> Path:
    _require_path(run_dir, "run_dir")
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


def _run_receipt(run_dir: Path) -> dict[str, Any]:
    _require_path(run_dir, "run_dir")
    run_path = run_dir / "run.json"
    if run_path.is_symlink() or not run_path.is_file():
        raise ContractError(f"run receipt is missing or unsafe: {run_path}")
    return _load_json(run_path, "run receipt")


def resolve_lane_contract(run_dir: Path) -> dict[str, str]:
    run = _run_receipt(run_dir)
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
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ContractError(f"guidance file is not UTF-8: {relative_value}") from exc
        files.append(
            {"path": relative.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        )
        sections.append(f"--- GUIDANCE {relative.as_posix()} ---\n{text}")
    return {"source": source, "revision": revision, "files": files, "content": "\n\n".join(sections)}


def _fixture_context(run_dir: Path) -> dict[str, Any]:
    fixture = _load_json(_safe_input_file(run_dir, "fixture.json", "fixture"), "fixture")
    brief_name = fixture.get("brief", "brief.md")
    acceptance_name = fixture.get("acceptance", "acceptance.json")
    brief_path = _safe_input_file(run_dir, brief_name, "brief")
    acceptance_path = _safe_input_file(run_dir, acceptance_name, "acceptance")
    brief = brief_path.read_text(encoding="utf-8")
    acceptance = _load_json(acceptance_path, "acceptance")
    prompt_material = (
        brief.encode("utf-8")
        + b"\0"
        + json.dumps(acceptance, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return {
        "fixture": fixture,
        "brief": brief,
        "acceptance": acceptance,
        "promptSha256": hashlib.sha256(prompt_material).hexdigest(),
    }


def _expected_direction_assignment(run_dir: Path, iteration: int = 1) -> dict[str, Any]:
    if not isinstance(iteration, int) or iteration < 1:
        raise ContractError("direction assignment iteration must be a positive integer")
    lane = resolve_lane_contract(run_dir)
    if lane["workflow"] != "design-studio":
        raise ContractError(f"lane {lane['id']} does not use Design Studio direction assignment")
    run = _run_receipt(run_dir)
    run_id = run.get("runId")
    if not isinstance(run_id, str) or not run_id.strip():
        raise ContractError("run receipt has no non-empty runId")
    context = _fixture_context(run_dir)
    seed_material = f"{run_id}\n{context['promptSha256']}\n{iteration}".encode("utf-8")
    digest = hashlib.sha256(seed_material).digest()
    fixture = context["fixture"]
    return {
        "schemaVersion": 1,
        "runId": run_id,
        "fixture": {"id": fixture.get("id"), "version": fixture.get("version")},
        "iteration": iteration,
        "promptSha256": context["promptSha256"],
        "selectionMethod": "sha256-mod-3",
        "seedDigest": hashlib.sha256(seed_material).hexdigest(),
        "assignedIndex": int.from_bytes(digest[:8], "big") % 3 + 1,
    }


def prepare_direction_assignment(run_dir: Path, iteration: int = 1) -> dict[str, Any]:
    expected = _expected_direction_assignment(run_dir, iteration)
    evidence_dir = run_dir / "evidence"
    if evidence_dir.is_symlink() or not evidence_dir.is_dir():
        raise ContractError(f"evidence directory is missing or unsafe: {evidence_dir}")
    assignment_path = evidence_dir / "direction-assignment.json"
    if assignment_path.is_symlink():
        raise ContractError("direction assignment must not be a symlink")
    if assignment_path.exists():
        recorded = _load_json(assignment_path, "direction assignment")
        if recorded != expected:
            raise ContractError("direction assignment does not match immutable run metadata")
        return recorded

    try:
        with assignment_path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(expected, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        recorded = _load_json(assignment_path, "direction assignment")
        if recorded != expected:
            raise ContractError("direction assignment changed during creation")
        return recorded
    return expected


def _source_tree(run_dir: Path) -> dict[str, Any]:
    work = run_dir / "work"
    if work.is_symlink() or not work.is_dir():
        raise ContractError(f"source tree is missing or unsafe: {work}")
    files: list[dict[str, Any]] = []
    sections: list[str] = []
    for path in sorted(work.rglob("*")):
        if path.is_symlink():
            raise ContractError(f"source tree may not contain symlinks: {path}")
        if not path.is_file():
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ContractError(f"source tree file is not UTF-8: {path}") from exc
        relative = path.relative_to(work).as_posix()
        files.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        sections.append(f"--- SOURCE {relative} ---\n{text}")
    return {"files": files, "content": "\n\n".join(sections) if sections else "(greenfield)"}


def build_director_packet(repo_root: Path, run_dir: Path, design_revision: str) -> dict[str, Any]:
    lane = resolve_lane_contract(run_dir)
    if lane["workflow"] != "design-studio":
        raise ContractError(f"lane {lane['id']} does not use the Design Studio Director")
    prepare_direction_assignment(run_dir)
    context = _fixture_context(run_dir)
    return {
        "role": "source-blind-visual-director-explore",
        "lane": lane,
        "brief": context["brief"],
        "acceptance": context["acceptance"],
        "guidance": _guidance(repo_root, (DIRECTOR_GUIDANCE,), "George-RD/design-studio", design_revision),
        "instructions": (
            "Return exactly three equally specified, materially different direction objects "
            "with IDs direction-1, direction-2 and direction-3 in that order. Do not rank or "
            "select them. You have no source-code access and no assignment data."
        ),
    }


def _validate_direction_candidates(directions: Sequence[dict[str, Any]]) -> None:
    if len(directions) != 3 or any(not isinstance(item, dict) for item in directions):
        raise ContractError("director must return exactly three direction objects")
    ids = [item.get("id") for item in directions]
    expected = ["direction-1", "direction-2", "direction-3"]
    if ids != expected:
        raise ContractError(f"director direction IDs must be exactly {expected}")


def select_direction(directions: Sequence[dict[str, Any]], run_dir: Path) -> dict[str, Any]:
    _require_path(run_dir, "run_dir")
    _validate_direction_candidates(directions)
    assignment = prepare_direction_assignment(run_dir)
    assigned_index = assignment["assignedIndex"]
    assignment_path = run_dir / "evidence" / "direction-assignment.json"
    return {
        "selectionMethod": "precommitted-run-assignment",
        "assignment": "evidence/direction-assignment.json",
        "assignmentSha256": hashlib.sha256(assignment_path.read_bytes()).hexdigest(),
        "assignedIndex": assigned_index,
        "direction": directions[assigned_index - 1],
    }


def build_direct_packet(
    repo_root: Path,
    run_dir: Path,
    selected_direction: dict[str, Any],
    design_revision: str,
) -> dict[str, Any]:
    lane = resolve_lane_contract(run_dir)
    if lane["workflow"] != "design-studio":
        raise ContractError(f"lane {lane['id']} does not use the Design Studio Director")
    if not isinstance(selected_direction, dict):
        raise ContractError("selected direction must be an object")
    assignment = prepare_direction_assignment(run_dir)
    expected_id = f"direction-{assignment['assignedIndex']}"
    if selected_direction.get("id") != expected_id:
        raise ContractError(
            f"Direct pass must expand the precommitted candidate {expected_id}"
        )
    context = _fixture_context(run_dir)
    heading_list = ", ".join(DIRECT_HEADINGS)
    return {
        "role": "source-blind-visual-director-direct",
        "lane": lane,
        "brief": context["brief"],
        "acceptance": context["acceptance"],
        "guidance": _guidance(repo_root, (DIRECTOR_GUIDANCE,), "George-RD/design-studio", design_revision),
        "selectedDirection": selected_direction,
        "instructions": (
            "Expand only the selected candidate into design-description.md. Use exactly these "
            f"non-empty headings in order: {heading_list}. Keep the contract source-free: no "
            "CSS properties, selectors, DOM terms, framework names or code snippets."
        ),
    }


def validate_design_description(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError("design-description.md must be a non-empty string")
    matches = list(MARKDOWN_HEADING.finditer(value))
    headings = tuple(match.group(1).strip() for match in matches)
    if headings != DIRECT_HEADINGS:
        raise ContractError(
            "design-description.md headings must be exactly " + ", ".join(DIRECT_HEADINGS)
        )
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(value)
        if not value[match.end() : end].strip():
            raise ContractError(f"design-description.md section is empty: {headings[index]}")
    return value.strip()


def build_builder_packet(
    repo_root: Path,
    run_dir: Path,
    design_description: Any,
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
    direct_contract = validate_design_description(design_description)
    return {
        "role": "source-aware-builder",
        "lane": lane,
        "brief": context["brief"],
        "acceptance": context["acceptance"],
        "guidance": _guidance(repo_root, (BUILDER_GUIDANCE,), "George-RD/design-studio", design_revision),
        "designDescription": direct_contract,
        "baselineSource": _source_tree(run_dir),
        "mechanicalProvider": mechanical_provider,
        "outputContract": context["fixture"].get("outputContract"),
        "instructions": (
            "Implement only design-description.md as complete static local files. Include a "
            "durable CSP that blocks every external connection and navigation surface. Use no "
            "external network assets or build step."
        ),
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
        "instructions": (
            "Apply the pinned Impeccable method and return complete static local files. Include "
            "a durable CSP that blocks every external connection and navigation surface. No "
            "Design Studio guidance or external network assets."
        ),
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


def _decode_css_escapes(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        hexadecimal = match.group(1)
        if hexadecimal is not None:
            codepoint = int(hexadecimal, 16)
            if codepoint == 0 or codepoint > 0x10FFFF:
                return "\ufffd"
            return chr(codepoint)
        return match.group(2) or ""

    return CSS_ESCAPE.sub(replace, value)


def _normalized_reference(value: str) -> str:
    decoded = _decode_css_escapes(unescape(value)).strip().strip("'\"")
    return re.sub(r"[\x00-\x20\x7f]+", "", decoded)


def _validate_reference(
    value: str,
    *,
    source_path: str,
    bundle_paths: set[str],
    context: str,
) -> None:
    normalized = _normalized_reference(value)
    if not normalized or normalized.startswith("#"):
        return
    lowered = normalized.lower()
    if lowered.startswith("data:"):
        return
    try:
        parsed = urlsplit(normalized)
    except ValueError as exc:
        raise ContractError(f"generated output contains an invalid URL in {context}: {value!r}") from exc
    if normalized.startswith("//") or parsed.scheme or parsed.netloc:
        raise ContractError(f"generated output contains an external reference in {context}: {value!r}")
    if not parsed.path:
        return
    if parsed.path.startswith("/") or "\\" in parsed.path:
        raise ContractError(f"generated output contains an absolute local reference in {context}: {value!r}")
    source_parent = PurePosixPath(source_path).parent.as_posix()
    joined = posixpath.normpath(posixpath.join(source_parent, parsed.path))
    if joined == ".." or joined.startswith("../") or joined.startswith("/"):
        raise ContractError(f"generated output reference escapes the bundle in {context}: {value!r}")
    if joined.endswith("/"):
        joined = f"{joined}index.html"
    if joined not in bundle_paths:
        raise ContractError(
            f"generated output references a missing local file in {context}: {joined}"
        )


def _parse_csp(value: str) -> dict[str, tuple[str, ...]]:
    directives: dict[str, tuple[str, ...]] = {}
    for raw_directive in value.split(";"):
        parts = raw_directive.strip().split()
        if not parts:
            continue
        name = parts[0].lower()
        if name in directives:
            raise ContractError(f"content security policy repeats directive: {name}")
        directives[name] = tuple(token.lower() for token in parts[1:])
    return directives


def _validate_csp(value: str) -> None:
    directives = _parse_csp(value)
    for name, expected in REQUIRED_CSP_DIRECTIVES.items():
        if directives.get(name) != expected:
            raise ContractError(
                f"index.html CSP must declare {name} {' '.join(expected)}"
            )
    for name, tokens in directives.items():
        if name != "default-src" and not name.endswith("-src"):
            continue
        for token in tokens:
            safe_hash = token.startswith(("'nonce-", "'sha256-", "'sha384-", "'sha512-"))
            if token not in SAFE_CSP_SOURCE_TOKENS and not safe_hash:
                raise ContractError(
                    f"index.html CSP permits a non-local source in {name}: {token}"
                )


def _split_srcset(value: str) -> list[str]:
    if _normalized_reference(value).lower().startswith("data:"):
        return [value]
    references: list[str] = []
    for candidate in value.split(","):
        stripped = candidate.strip()
        if stripped:
            references.append(stripped.split()[0])
    return references


class _BundleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.csp_values: list[str] = []
        self.references: list[tuple[str, str]] = []
        self.styles: list[str] = []
        self.scripts: list[str] = []
        self.resource_before_csp = False
        self._style_depth = 0
        self._script_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        attributes = {name.lower(): value or "" for name, value in attrs}
        is_csp = (
            tag_name == "meta"
            and attributes.get("http-equiv", "").strip().lower() == "content-security-policy"
        )
        if is_csp:
            self.csp_values.append(attributes.get("content", ""))
        elif tag_name in NETWORK_RELEVANT_TAGS and not self.csp_values:
            self.resource_before_csp = True

        if tag_name == "meta" and attributes.get("http-equiv", "").strip().lower() == "refresh":
            match = re.search(r"(?i)\burl\s*=\s*(.+)$", attributes.get("content", ""))
            if match:
                self.references.append(("meta refresh", match.group(1).strip()))
        for name, value in attributes.items():
            if name in URL_ATTRIBUTES:
                self.references.append((f"<{tag_name}> {name}", value))
            elif name == "srcset":
                for reference in _split_srcset(value):
                    self.references.append((f"<{tag_name}> srcset", reference))
            elif name == "style":
                self.styles.append(value)
        if tag_name == "style":
            self._style_depth += 1
        if tag_name == "script" and not attributes.get("src"):
            self._script_depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if tag_name == "style" and self._style_depth:
            self._style_depth -= 1
        if tag_name == "script" and self._script_depth:
            self._script_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._style_depth:
            self.styles.append(data)
        if self._script_depth:
            self.scripts.append(data)


def _validate_javascript(content: str, source_path: str) -> None:
    decoded = unescape(content)
    found = [name for name, pattern in NETWORK_API_PATTERNS.items() if pattern.search(decoded)]
    if found:
        raise ContractError(
            f"generated JavaScript can initiate network access in {source_path}: {', '.join(found)}"
        )


def _validate_css(
    content: str,
    *,
    source_path: str,
    bundle_paths: set[str],
) -> None:
    decoded = _decode_css_escapes(unescape(content))
    references = [match.group(2) for match in CSS_URL.finditer(decoded)]
    references.extend(match.group(2) for match in CSS_IMPORT.finditer(decoded))
    for reference in references:
        _validate_reference(
            reference,
            source_path=source_path,
            bundle_paths=bundle_paths,
            context=f"CSS {source_path}",
        )


def _validate_html(
    content: str,
    *,
    source_path: str,
    bundle_paths: set[str],
) -> None:
    parser = _BundleHTMLParser()
    try:
        parser.feed(content)
        parser.close()
    except Exception as exc:
        raise ContractError(f"generated HTML is invalid in {source_path}: {exc}") from exc
    if len(parser.csp_values) != 1:
        raise ContractError(f"{source_path} must contain exactly one Content-Security-Policy meta tag")
    if parser.resource_before_csp:
        raise ContractError(f"{source_path} loads or executes content before its CSP is active")
    _validate_csp(parser.csp_values[0])
    for context, reference in parser.references:
        _validate_reference(
            reference,
            source_path=source_path,
            bundle_paths=bundle_paths,
            context=f"{source_path} {context}",
        )
    for style in parser.styles:
        _validate_css(style, source_path=source_path, bundle_paths=bundle_paths)
    for script in parser.scripts:
        _validate_javascript(script, source_path)


def _validate_svg(
    content: str,
    *,
    source_path: str,
    bundle_paths: set[str],
) -> None:
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise ContractError(f"generated SVG is invalid in {source_path}: {exc}") from exc
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1].lower()
        for raw_name, value in element.attrib.items():
            name = raw_name.rsplit("}", 1)[-1].lower()
            if name in URL_ATTRIBUTES:
                _validate_reference(
                    value,
                    source_path=source_path,
                    bundle_paths=bundle_paths,
                    context=f"{source_path} <{tag}> {name}",
                )
            elif name == "style":
                _validate_css(value, source_path=source_path, bundle_paths=bundle_paths)
        if tag == "style" and element.text:
            _validate_css(element.text, source_path=source_path, bundle_paths=bundle_paths)
        if tag == "script" and element.text:
            _validate_javascript(element.text, source_path)


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
        seen.add(path)
        total += len(content.encode("utf-8"))
        validated.append({"path": path, "content": content})
    if "index.html" not in seen:
        raise ContractError("generated output must include index.html")
    if total > MAX_BYTES:
        raise ContractError(f"generated output exceeds {MAX_BYTES} UTF-8 bytes")

    for item in validated:
        path = item["path"]
        content = item["content"]
        suffix = PurePosixPath(path).suffix.lower()
        if suffix == ".html":
            _validate_html(content, source_path=path, bundle_paths=seen)
        elif suffix == ".css":
            _validate_css(content, source_path=path, bundle_paths=seen)
        elif suffix == ".js":
            _validate_javascript(content, path)
        elif suffix == ".svg":
            _validate_svg(content, source_path=path, bundle_paths=seen)
    return validated
