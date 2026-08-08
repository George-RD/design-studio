#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import tempfile
import threading
import time
from typing import Any, Callable, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
BROWSER_SCRIPT = SCRIPT_DIR / "run_browser_capability.mjs"
REPORT_SCHEMA_VERSION = 1
SOURCE_CANARY = "DESIGN_STUDIO_PRIVATE_SOURCE_CANARY_6f3b9d2a"
DEFAULT_COPILOT_VERSION = "1.0.74"
DEFAULT_MODEL = "gpt-5.4"
MAX_AI_CREDITS = 30
COMMAND_TIMEOUT_SECONDS = 360
BROWSER_TIMEOUT_SECONDS = 90
MAX_STDOUT_BYTES = 4_000_000
MAX_STDERR_BYTES = 1_000_000
MAX_JSONL_EVENTS = 10_000
MAX_JSONL_LINE_BYTES = 1_000_000
OUTPUT_LIMIT_EXIT_CODE = 125

COPILOT_ENV_ALLOWLIST = frozenset(
    {
        "ALL_PROXY",
        "CI",
        "GITHUB_ACTION",
        "GITHUB_ACTIONS",
        "GITHUB_ACTOR",
        "GITHUB_API_URL",
        "GITHUB_EVENT_NAME",
        "GITHUB_GRAPHQL_URL",
        "GITHUB_JOB",
        "GITHUB_REF",
        "GITHUB_REF_NAME",
        "GITHUB_REPOSITORY",
        "GITHUB_RUN_ATTEMPT",
        "GITHUB_RUN_ID",
        "GITHUB_RUN_NUMBER",
        "GITHUB_SERVER_URL",
        "GITHUB_SHA",
        "GITHUB_WORKFLOW",
        "GITHUB_WORKSPACE",
        "HOME",
        "HOSTNAME",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "LANG",
        "LC_ALL",
        "LOGNAME",
        "NODE_EXTRA_CA_CERTS",
        "NO_COLOR",
        "NO_PROXY",
        "PATH",
        "RUNNER_ARCH",
        "RUNNER_ENVIRONMENT",
        "RUNNER_NAME",
        "RUNNER_OS",
        "RUNNER_TEMP",
        "RUNNER_TOOL_CACHE",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "TEMP",
        "TERM",
        "TMP",
        "TMPDIR",
        "USER",
        "XDG_CACHE_HOME",
        "XDG_CONFIG_HOME",
    }
)


class ContractError(RuntimeError):
    """Raised when capability evidence violates the accepted contract."""


class CapabilityBlocked(RuntimeError):
    """Raised when infrastructure or account policy prevents a valid test."""


@dataclass(frozen=True)
class CommandOutcome:
    exit_code: int
    stdout: str
    stderr: str


CommandRunner = Callable[..., CommandOutcome]
BrowserRunner = Callable[[Path, Path], dict[str, Any]]
Clock = Callable[[], str]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"{label} is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{label} must contain a JSON object")
    return value


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def _coerce_subprocess_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _capture_stream_bounded(
    stream: Any,
    *,
    limit: int,
    destination: bytearray,
    exceeded: threading.Event,
) -> None:
    try:
        while True:
            chunk = stream.read(65_536)
            if not chunk:
                return
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8", errors="replace")
            remaining = max(0, limit - len(destination))
            if remaining:
                destination.extend(chunk[:remaining])
            if len(chunk) > remaining:
                exceeded.set()
    finally:
        try:
            stream.close()
        except Exception:
            pass


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
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
        process.wait(timeout=1)
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


def default_command_runner(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str],
) -> CommandOutcome:
    try:
        process = subprocess.Popen(
            [str(part) for part in argv],
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name == "posix",
        )
    except OSError as error:
        return CommandOutcome(
            exit_code=127,
            stdout="",
            stderr=f"Copilot CLI could not start: {type(error).__name__}: {error}",
        )

    if process.stdout is None or process.stderr is None:
        _terminate_process_tree(process)
        return CommandOutcome(
            exit_code=127,
            stdout="",
            stderr="Copilot CLI did not expose stdout and stderr pipes",
        )

    stdout_bytes = bytearray()
    stderr_bytes = bytearray()
    stdout_exceeded = threading.Event()
    stderr_exceeded = threading.Event()
    readers = [
        threading.Thread(
            target=_capture_stream_bounded,
            kwargs={
                "stream": process.stdout,
                "limit": MAX_STDOUT_BYTES,
                "destination": stdout_bytes,
                "exceeded": stdout_exceeded,
            },
            daemon=True,
        ),
        threading.Thread(
            target=_capture_stream_bounded,
            kwargs={
                "stream": process.stderr,
                "limit": MAX_STDERR_BYTES,
                "destination": stderr_bytes,
                "exceeded": stderr_exceeded,
            },
            daemon=True,
        ),
    ]
    for reader in readers:
        reader.start()

    deadline = time.monotonic() + COMMAND_TIMEOUT_SECONDS
    timed_out = False
    output_exceeded = False
    while process.poll() is None:
        if stdout_exceeded.is_set() or stderr_exceeded.is_set():
            output_exceeded = True
            _terminate_process_tree(process)
            break
        if time.monotonic() >= deadline:
            timed_out = True
            _terminate_process_tree(process)
            break
        time.sleep(0.02)

    try:
        exit_code = process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _terminate_process_tree(process)
        exit_code = process.wait()
    for reader in readers:
        reader.join(timeout=5)

    stdout = bytes(stdout_bytes).decode("utf-8", errors="replace")
    stderr = bytes(stderr_bytes).decode("utf-8", errors="replace")
    if timed_out:
        timeout_message = (
            f"Copilot CLI timed out after {COMMAND_TIMEOUT_SECONDS} seconds"
        )
        stderr = f"{stderr.rstrip()}\n{timeout_message}\n" if stderr else timeout_message
        return CommandOutcome(exit_code=124, stdout=stdout, stderr=stderr)
    if output_exceeded or stdout_exceeded.is_set() or stderr_exceeded.is_set():
        streams = []
        if stdout_exceeded.is_set():
            streams.append(f"stdout>{MAX_STDOUT_BYTES} bytes")
        if stderr_exceeded.is_set():
            streams.append(f"stderr>{MAX_STDERR_BYTES} bytes")
        message = "Copilot CLI output limit exceeded: " + ", ".join(streams)
        stderr = f"{stderr.rstrip()}\n{message}\n" if stderr else message
        return CommandOutcome(
            exit_code=OUTPUT_LIMIT_EXIT_CODE,
            stdout=stdout,
            stderr=stderr,
        )
    return CommandOutcome(
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
    )


def default_browser_runner(site_dir: Path, evidence_dir: Path) -> dict[str, Any]:
    browser_dir = evidence_dir / "browser"
    browser_dir.mkdir(parents=True, exist_ok=True)
    try:
        completed = subprocess.run(
            [
                "node",
                str(BROWSER_SCRIPT),
                "--root",
                str(site_dir),
                "--output-dir",
                str(browser_dir),
                "--entrypoint",
                "index.html",
                "--width",
                "390",
                "--height",
                "844",
                "--forbidden-text",
                SOURCE_CANARY,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=BROWSER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        stdout = _coerce_subprocess_text(
            getattr(error, "stdout", None) or getattr(error, "output", None)
        )
        stderr = _coerce_subprocess_text(getattr(error, "stderr", None))
        (browser_dir / "stdout.log").write_text(stdout, encoding="utf-8")
        (browser_dir / "stderr.log").write_text(stderr, encoding="utf-8")
        raise CapabilityBlocked(
            f"browser probe timed out after {BROWSER_TIMEOUT_SECONDS} seconds"
        ) from error

    (browser_dir / "stdout.log").write_text(
        completed.stdout,
        encoding="utf-8",
    )
    (browser_dir / "stderr.log").write_text(
        completed.stderr,
        encoding="utf-8",
    )
    report = load_json_object(
        browser_dir / "browser-report.json",
        "browser report",
    )
    status = report.get("status")
    if status == "blocked":
        raise CapabilityBlocked(require_text(report.get("error"), "browser error"))
    if completed.returncode != 0 or status != "passed":
        failures = report.get("failures")
        raise ContractError(
            f"browser capability failed: {failures or report.get('error')}"
        )
    return report


def parse_jsonl(text: str, label: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        if len(raw_line.encode("utf-8")) > MAX_JSONL_LINE_BYTES:
            raise ContractError(
                f"{label} line {line_number} exceeds "
                f"{MAX_JSONL_LINE_BYTES} bytes"
            )
        if len(events) >= MAX_JSONL_EVENTS:
            raise ContractError(
                f"{label} exceeds {MAX_JSONL_EVENTS} JSON events"
            )
        try:
            value = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ContractError(
                f"{label} line {line_number} is not JSON: {exc}"
            ) from exc
        if not isinstance(value, dict):
            raise ContractError(
                f"{label} line {line_number} must be a JSON object"
            )
        events.append(value)
    if not events:
        raise ContractError(f"{label} contains no JSON events")
    return events


def classify_cli_failure(outcome: CommandOutcome) -> str:
    text = f"{outcome.stdout}\n{outcome.stderr}".lower()
    blocked_markers = (
        "copilot requests permission",
        "not authenticated",
        "authentication",
        "copilot access",
        "billing",
        "policy",
        "rate limit",
        "temporarily unavailable",
        "service unavailable",
        "quota",
        "ai credit",
        "credits exhausted",
        "timed out",
        "timeout",
    )
    return "blocked" if any(marker in text for marker in blocked_markers) else "failed"


def ensure_command_output_bounds(outcome: CommandOutcome) -> None:
    stdout_bytes = len(outcome.stdout.encode("utf-8"))
    stderr_bytes = len(outcome.stderr.encode("utf-8"))
    if stdout_bytes > MAX_STDOUT_BYTES:
        raise ContractError(
            f"Copilot CLI stdout exceeds {MAX_STDOUT_BYTES} bytes"
        )
    if stderr_bytes > MAX_STDERR_BYTES:
        raise ContractError(
            f"Copilot CLI stderr exceeds {MAX_STDERR_BYTES} bytes"
        )


def safe_persist_output(path: Path, text: str, token: str) -> None:
    if token and token in text:
        path.write_text(
            text.replace(token, "<redacted-token>"),
            encoding="utf-8",
        )
        raise ContractError(
            f"{path.name} attempted to persist the authentication token"
        )
    path.write_text(text, encoding="utf-8")


def reset_directory(path: Path, label: str) -> None:
    if path.is_symlink():
        raise ContractError(f"{label} must not be a symlink: {path}")
    if path.exists():
        if not path.is_dir():
            raise ContractError(f"{label} must be a directory: {path}")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=False)


def prepare_output_directories(
    output_root: Path,
) -> tuple[Path, Path, Path]:
    if output_root.is_symlink():
        raise ContractError("capability output root must not be a symlink")
    output_root.mkdir(parents=True, exist_ok=True)
    output_root = output_root.resolve()
    workspaces = output_root / "workspaces"
    evidence_dir = output_root / "evidence"
    site_dir = output_root / "site"

    version_bytes: bytes | None = None
    version_path = evidence_dir / "copilot-version.txt"
    if version_path.is_symlink():
        raise ContractError("copilot version evidence must not be a symlink")
    if version_path.is_file():
        version_bytes = version_path.read_bytes()

    reset_directory(workspaces, "workspace root")
    reset_directory(evidence_dir, "evidence root")
    reset_directory(site_dir, "published site root")
    if version_bytes is not None:
        (evidence_dir / "copilot-version.txt").write_bytes(version_bytes)
    return workspaces, evidence_dir, site_dir


def publish_file_no_follow(source: Path, destination: Path, label: str) -> None:
    if source.is_symlink() or not source.is_file():
        raise ContractError(f"{label} source must be a regular file: {source}")
    parent = destination.parent
    if parent.is_symlink() or not parent.is_dir():
        raise ContractError(f"{label} destination directory is unsafe: {parent}")
    if destination.is_symlink():
        raise ContractError(f"{label} destination is a symlink: {destination}")
    if destination.exists() and not destination.is_file():
        raise ContractError(
            f"{label} destination must be a regular file: {destination}"
        )

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(source.read_bytes())
            handle.flush()
            os.fsync(handle.fileno())
        if destination.is_symlink():
            raise ContractError(
                f"{label} destination became a symlink: {destination}"
            )
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_exact_workspace_files(
    root: Path,
    expected: set[str],
    label: str,
) -> list[str]:
    actual: set[str] = set()
    for path in root.rglob("*"):
        relative_path = path.relative_to(root)
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ContractError(
                f"{label} contains a symlink: {relative_path}"
            )
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ContractError(
                f"{label} contains an unsupported file type: {relative_path}"
            )
        actual.add(relative_path.as_posix())
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ContractError(
            f"{label} file boundary changed: "
            f"missing={missing}, unexpected={unexpected}"
        )
    return sorted(actual)


def snapshot_file_digests(
    root: Path,
    names: set[str],
    label: str,
) -> dict[str, str]:
    digests: dict[str, str] = {}
    for name in sorted(names):
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ContractError(f"{label} is not a regular file: {name}")
        digests[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def require_unchanged_file_digests(
    root: Path,
    expected: dict[str, str],
    label: str,
) -> None:
    current = snapshot_file_digests(root, set(expected), label)
    changed = sorted(
        name for name, digest in expected.items() if current.get(name) != digest
    )
    if changed:
        raise ContractError(f"{label} changed: {changed}")


def validate_direction(path: Path) -> dict[str, str]:
    value = load_json_object(path, "director direction")
    expected = {"concept", "palette", "layout", "interaction"}
    if set(value) != expected:
        raise ContractError(
            f"direction keys must be exactly {sorted(expected)}"
        )
    return {
        key: require_text(value.get(key), f"direction.{key}")
        for key in sorted(expected)
    }


_CSS_URL = re.compile(
    r"url\(\s*(?P<quote>['\"]?)(?P<value>.*?)(?P=quote)\s*\)",
    re.IGNORECASE | re.DOTALL,
)
_CSS_IMPORT = re.compile(
    r"@import\s+(?:url\(\s*)?(?P<quote>['\"]?)(?P<value>[^'\"\s;)]+)(?P=quote)",
    re.IGNORECASE,
)

_REQUIRED_NO_NETWORK_CSP = {
    "default-src": ("'none'",),
    "base-uri": ("'none'",),
    "connect-src": ("'none'",),
    "form-action": ("'none'",),
    "frame-src": ("'none'",),
    "img-src": ("data:",),
    "media-src": ("data:",),
    "object-src": ("'none'",),
    "script-src": ("'unsafe-inline'",),
    "style-src": ("'unsafe-inline'",),
}
_ALLOWED_EXTRA_CSP = {
    "child-src": ("'none'",),
    "font-src": ("'none'",),
    "manifest-src": ("'none'",),
    "navigate-to": ("'none'",),
    "prefetch-src": ("'none'",),
    "worker-src": ("'none'",),
}

_NETWORK_API_PATTERNS = {
    "fetch": re.compile(r"(?<![\w$])fetch\s*\(", re.IGNORECASE),
    "XMLHttpRequest": re.compile(r"\bXMLHttpRequest\b", re.IGNORECASE),
    "WebSocket": re.compile(r"\bWebSocket\s*\(", re.IGNORECASE),
    "EventSource": re.compile(r"\bEventSource\s*\(", re.IGNORECASE),
    "sendBeacon": re.compile(r"\bsendBeacon\s*\(", re.IGNORECASE),
    "window.open": re.compile(r"\bwindow\s*\.\s*open\s*\(", re.IGNORECASE),
    "location.assign": re.compile(
        r"\b(?:window\s*\.\s*)?location\s*\.\s*assign\s*\(",
        re.IGNORECASE,
    ),
    "location.replace": re.compile(
        r"\b(?:window\s*\.\s*)?location\s*\.\s*replace\s*\(",
        re.IGNORECASE,
    ),
    "location.href assignment": re.compile(
        r"\b(?:window\s*\.\s*)?location\s*\.\s*href\s*=(?!=)",
        re.IGNORECASE,
    ),
    "location assignment": re.compile(
        r"\b(?:window\s*\.\s*)?location\s*=(?!=)",
        re.IGNORECASE,
    ),
    "history.pushState": re.compile(
        r"\bhistory\s*\.\s*pushState\s*\(",
        re.IGNORECASE,
    ),
    "history.replaceState": re.compile(
        r"\bhistory\s*\.\s*replaceState\s*\(",
        re.IGNORECASE,
    ),
}


def _parse_content_security_policy(
    content: str,
) -> dict[str, tuple[str, ...]] | None:
    directives: dict[str, tuple[str, ...]] = {}
    for raw_directive in content.split(";"):
        parts = raw_directive.strip().lower().split()
        if not parts:
            continue
        name = parts[0]
        if name in directives:
            return None
        directives[name] = tuple(parts[1:])
    return directives


def _has_durable_no_network_policy(content: str) -> bool:
    directives = _parse_content_security_policy(content)
    if directives is None:
        return False
    if not all(
        directives.get(name) == expected
        for name, expected in _REQUIRED_NO_NETWORK_CSP.items()
    ):
        return False
    allowed_names = set(_REQUIRED_NO_NETWORK_CSP) | set(_ALLOWED_EXTRA_CSP)
    if set(directives) - allowed_names:
        return False
    return all(
        directives.get(name) == expected
        for name, expected in _ALLOWED_EXTRA_CSP.items()
        if name in directives
    )


def _inline_reference(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        not normalized
        or normalized.startswith("#")
        or normalized.startswith("data:")
        or normalized == "about:blank"
    )


def _css_references(text: str) -> list[str]:
    values = [match.group("value").strip() for match in _CSS_URL.finditer(text)]
    values.extend(
        match.group("value").strip() for match in _CSS_IMPORT.finditer(text)
    )
    return values


def _srcset_candidates(value: str) -> list[str]:
    candidates: list[str] = []
    position = 0
    length = len(value)
    while position < length:
        while position < length and (
            value[position].isspace() or value[position] == ","
        ):
            position += 1
        if position >= length:
            break

        start = position
        is_data = value[position : position + 5].lower() == "data:"
        if is_data:
            while position < length and not value[position].isspace():
                position += 1
            candidate = value[start:position]
            separator_attached = candidate.endswith(",")
            candidate = candidate.rstrip(",")
        else:
            while (
                position < length
                and not value[position].isspace()
                and value[position] != ","
            ):
                position += 1
            candidate = value[start:position]
            separator_attached = False

        if candidate:
            candidates.append(candidate)
        if separator_attached:
            continue

        while position < length and value[position] != ",":
            position += 1
        if position < length:
            position += 1
    return candidates


class CapabilityHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.elements_by_id: dict[str, tuple[str, dict[str, str | None]]] = {}
        self.duplicate_ids: set[str] = set()
        self.has_submit = False
        self.has_viewport = False
        self.has_meta_refresh = False
        self.content_security_policies: list[str] = []
        self.resource_references: list[tuple[str, str]] = []
        self._style_depth = 0
        self._style_chunks: list[str] = []

    def _record_reference(self, context: str, value: str | None) -> None:
        if value is None:
            return
        candidate = value.strip()
        if candidate and not _inline_reference(candidate):
            self.resource_references.append((context, candidate))

    @staticmethod
    def _attribute_text(
        values: dict[str, str | None],
        name: str,
        default: str = "",
    ) -> str:
        value = values.get(name, default)
        return value if isinstance(value, str) else ""

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        tag = tag.lower()
        values = {name.lower(): value for name, value in attrs}
        element_id = values.get("id")
        if element_id:
            if element_id in self.elements_by_id:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)
            self.elements_by_id[element_id] = (tag, values)
        if (
            tag == "button"
            and self._attribute_text(values, "type", "submit").lower()
            == "submit"
        ):
            self.has_submit = True
        if (
            tag == "input"
            and self._attribute_text(values, "type", "text").lower()
            == "submit"
        ):
            self.has_submit = True
        if (
            tag == "meta"
            and self._attribute_text(values, "name").lower() == "viewport"
        ):
            self.has_viewport = True
        if (
            tag == "meta"
            and self._attribute_text(values, "http-equiv").lower()
            == "refresh"
        ):
            self.has_meta_refresh = True
        if (
            tag == "meta"
            and self._attribute_text(values, "http-equiv").lower()
            == "content-security-policy"
            and values.get("content")
        ):
            self.content_security_policies.append(values["content"].strip())

        for attribute in (
            "action",
            "background",
            "data",
            "formaction",
            "manifest",
            "poster",
            "src",
        ):
            self._record_reference(
                f"{tag}[{attribute}]",
                values.get(attribute),
            )
        if "href" in values:
            self._record_reference(f"{tag}[href]", values.get("href"))
        if "srcset" in values and values["srcset"]:
            for candidate in _srcset_candidates(values["srcset"]):
                self._record_reference(f"{tag}[srcset]", candidate)
        if "style" in values and values["style"]:
            for reference in _css_references(values["style"]):
                self._record_reference(f"{tag}[style]", reference)
        if tag == "style":
            self._style_depth += 1

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() == "style":
            self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self._style_depth:
            self._style_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "style" or not self._style_depth:
            return
        self._style_depth -= 1
        if self._style_depth == 0:
            style = "".join(self._style_chunks)
            self._style_chunks.clear()
            for reference in _css_references(style):
                self._record_reference("style[url]", reference)


def validate_site(path: Path) -> dict[str, Any]:
    try:
        file_stat = path.lstat()
    except FileNotFoundError as exc:
        raise ContractError("builder did not produce index.html") from exc
    if not stat.S_ISREG(file_stat.st_mode):
        raise ContractError("builder index.html is not a regular file")
    if file_stat.st_size > 200_000:
        raise ContractError("index.html exceeds the 200 KB capability limit")
    text = path.read_text(encoding="utf-8")
    if len(text.encode("utf-8")) > 200_000:
        raise ContractError("index.html exceeds the 200 KB capability limit")
    if SOURCE_CANARY in text:
        raise ContractError("index.html leaked the private source canary")
    parser = CapabilityHtmlParser()
    parser.feed(text)
    required_ids = {
        "capability-form",
        "capability-name",
        "capability-success",
    }
    missing_ids = sorted(required_ids - parser.ids)
    if missing_ids:
        raise ContractError(
            f"index.html is missing required IDs: {missing_ids}"
        )
    if parser.duplicate_ids:
        raise ContractError(
            f"index.html contains duplicate required IDs: {sorted(parser.duplicate_ids)}"
        )
    input_element = parser.elements_by_id.get("capability-name")
    input_tag, input_attrs = input_element or (None, {})
    input_type = str(input_attrs.get("type") or "text").lower()
    if input_tag != "input" or input_type != "text":
        raise ContractError(
            "index.html capability-name is not a text input"
        )
    if not parser.has_submit:
        raise ContractError("index.html has no submit control")
    if not parser.has_viewport:
        raise ContractError("index.html has no viewport declaration")
    if parser.has_meta_refresh:
        raise ContractError(
            "index.html contains forbidden meta refresh navigation"
        )
    if len(parser.content_security_policies) != 1 or not _has_durable_no_network_policy(
        parser.content_security_policies[0]
    ):
        raise ContractError(
            "index.html has no durable no-network content security policy"
        )
    network_apis = [
        name
        for name, pattern in _NETWORK_API_PATTERNS.items()
        if pattern.search(text)
    ]
    if network_apis:
        raise ContractError(
            "index.html contains forbidden network API or navigation API use: "
            + ", ".join(network_apis)
        )
    if parser.resource_references:
        formatted = [
            f"{context}={value!r}"
            for context, value in parser.resource_references[:8]
        ]
        raise ContractError(
            "index.html is not self-contained; resource references: "
            + ", ".join(formatted)
        )
    return {
        "entrypoint": "index.html",
        "bytes": len(text.encode("utf-8")),
        "requiredIds": sorted(required_ids),
        "textInputContract": True,
        "durableNetworkPolicy": True,
        "networkApisAbsent": True,
        "resourceReferencesAbsent": True,
        "sourceCanaryAbsent": True,
        "singleFile": True,
    }


def validate_evaluation(path: Path) -> dict[str, Any]:
    value = load_json_object(path, "evaluator result")
    expected = {
        "titleVisible",
        "formVisible",
        "successVisible",
        "layoutUsable",
        "sourceCanaryVisible",
        "summary",
    }
    if set(value) != expected:
        raise ContractError(
            f"evaluation keys must be exactly {sorted(expected)}"
        )
    for key in (
        "titleVisible",
        "formVisible",
        "successVisible",
        "layoutUsable",
        "sourceCanaryVisible",
    ):
        if not isinstance(value.get(key), bool):
            raise ContractError(f"evaluation.{key} must be boolean")
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
        raise ContractError(
            f"source-blind evaluator rejected visible contract: {failures}"
        )
    return value


def director_prompt(brief: str) -> str:
    return f"""You are a source-blind visual director. You have no source-code access.

Public brief:
{brief}

Create exactly one file named direction.json in the current directory. It must be valid JSON with exactly these non-empty string keys: concept, palette, layout, interaction. Do not create or read any other file. Do not use markdown fences. Finish only after direction.json exists."""


def builder_prompt() -> str:
    return """You are the implementation Builder in an isolated workspace.
Read only brief.md, direction.json, and baseline.css. Create exactly one new file named index.html and no other file.

The page must be a complete self-contained HTML document with inline CSS and JavaScript, no external assets, no network calls, and no build step. Use the supplied design direction and the baseline CSS variables without copying private comments.

Required behavioral contract:
- form id: capability-form
- labeled text input id: capability-name
- success region id: capability-success, initially empty and not visible
- submit control with type=submit
- include this exact durable no-network policy in the head: <meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; connect-src 'none'; form-action 'none'; frame-src 'none'; img-src data:; media-src data:; object-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'">
- do not call fetch, XMLHttpRequest, WebSocket, EventSource, sendBeacon, or window.open
- local submission prevents navigation, preserves the entered value, and reveals exact text: Capability complete
- visible keyboard focus
- responsive at 390x844 without horizontal overflow
- a real prefers-reduced-motion path that removes non-essential transition or animation duration

Finish only after index.html exists."""


def evaluator_prompt(brief: str) -> str:
    return f"""You are a source-blind visual evaluator. Judge only this public brief and the attached post-submission screenshot. You have no source code, implementation history, tool transcript, or prior score.

Public brief:
{brief}

Create exactly one file named evaluation.json in the current directory. It must be valid JSON with exactly these keys:
- titleVisible: boolean
- formVisible: boolean; true when both the labeled text input and submit button remain visibly present after submission
- successVisible: boolean
- layoutUsable: boolean
- sourceCanaryVisible: boolean
- summary: non-empty string grounded only in the screenshot

Do not infer that successful submission removed controls when they remain visible. Do not create or read any other file. Finish only after evaluation.json exists."""


def build_role_command(
    *,
    copilot_bin: str,
    cwd: Path,
    prompt: str,
    model: str,
    available_tools: str,
    allow_tools: str,
    deny_tools: str,
    attachment: Path | None = None,
) -> list[str]:
    command = [
        copilot_bin,
        "-C",
        str(cwd),
        "--prompt",
        prompt,
        f"--model={model}",
        "--output-format=json",
        "--no-ask-user",
        "--no-custom-instructions",
        "--disable-builtin-mcps",
        "--no-remote",
        "--no-remote-export",
        "--no-auto-update",
        "--no-color",
        "--no-bash-env",
        "--no-experimental",
        f"--max-ai-credits={MAX_AI_CREDITS}",
        f"--available-tools={available_tools}",
        f"--allow-tool={allow_tools}",
        f"--deny-tool={deny_tools}",
    ]
    if attachment is not None:
        command.extend(["--attachment", str(attachment)])
    return command


def build_role_environment(token: str, copilot_home: Path) -> dict[str, str]:
    environment = {
        key: value
        for key in sorted(COPILOT_ENV_ALLOWLIST)
        if isinstance((value := os.environ.get(key)), str)
    }
    environment.update(
        {
            "GITHUB_TOKEN": token,
            "COPILOT_HOME": str(copilot_home),
            "COPILOT_AUTO_UPDATE": "false",
        }
    )
    return environment


def invoke_role(
    *,
    role: str,
    workspace: Path,
    evidence_dir: Path,
    token: str,
    copilot_bin: str,
    model: str,
    prompt: str,
    available_tools: str,
    allow_tools: str,
    deny_tools: str,
    command_runner: CommandRunner,
    attachment: Path | None = None,
) -> dict[str, Any]:
    copilot_home = evidence_dir / "copilot-home" / role
    copilot_home.mkdir(parents=True, exist_ok=True)
    command = build_role_command(
        copilot_bin=copilot_bin,
        cwd=workspace,
        prompt=prompt,
        model=model,
        available_tools=available_tools,
        allow_tools=allow_tools,
        deny_tools=deny_tools,
        attachment=attachment,
    )
    environment = build_role_environment(token, copilot_home)
    write_json(
        evidence_dir / f"{role}.command.json",
        {
            "argv": command,
            "workingDirectory": f"workspaces/{role}",
            "environmentContract": sorted(environment),
        },
    )
    outcome = command_runner(command, cwd=workspace, env=environment)
    ensure_command_output_bounds(outcome)
    stdout_path = evidence_dir / f"{role}.stdout.jsonl"
    stderr_path = evidence_dir / f"{role}.stderr.log"
    safe_persist_output(stdout_path, outcome.stdout, token)
    safe_persist_output(stderr_path, outcome.stderr, token)
    if outcome.exit_code != 0:
        status = classify_cli_failure(outcome)
        message = (
            outcome.stderr.strip()
            or outcome.stdout.strip()
            or f"exit {outcome.exit_code}"
        )
        if status == "blocked":
            raise CapabilityBlocked(
                f"{role} Copilot CLI was blocked: {message[:1000]}"
            )
        raise ContractError(
            f"{role} Copilot CLI failed: {message[:1000]}"
        )
    events = parse_jsonl(outcome.stdout, f"{role} Copilot JSONL")
    return {
        "status": "passed",
        "eventCount": len(events),
        "stdout": f"evidence/{role}.stdout.jsonl",
        "stderr": f"evidence/{role}.stderr.log",
        "command": f"evidence/{role}.command.json",
    }


def _contains_text_bytes(path: Path, text: str) -> bool:
    return text.encode("utf-8") in path.read_bytes()


def scan_for_token(root: Path, token: str) -> None:
    if not token:
        return
    encoded = token.encode("utf-8")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ContractError(
                f"capability output contains a symlink: {path.relative_to(root)}"
            )
        if path.is_file() and encoded in path.read_bytes():
            raise ContractError(
                f"authentication token persisted in {path.relative_to(root)}"
            )


def _merge_failed_check(
    report: dict[str, Any],
    step: str,
    message: str,
    status: str,
) -> None:
    existing = report.get("checks", {}).get(step)
    details = dict(existing) if isinstance(existing, dict) else {}
    details.update({"status": status, "message": message})
    report["checks"][step] = details


def run_capability(
    *,
    token: str,
    output_root: Path,
    copilot_bin: str = "copilot",
    copilot_version: str = DEFAULT_COPILOT_VERSION,
    model: str = DEFAULT_MODEL,
    command_runner: CommandRunner = default_command_runner,
    browser_runner: BrowserRunner = default_browser_runner,
    now: Clock = utc_now,
) -> dict[str, Any]:
    output_root = output_root.expanduser()
    workspaces, evidence_dir, site_dir = prepare_output_directories(
        output_root
    )
    output_root = output_root.resolve()

    report: dict[str, Any] = {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "status": "running",
        "startedAt": now(),
        "finishedAt": None,
        "executionSurface": {
            "name": "github-copilot-cli",
            "version": copilot_version,
            "model": model,
            "maxAiCreditsPerRole": MAX_AI_CREDITS,
            "authentication": "github-actions-token",
            "permission": "copilot-requests: write",
            "environmentPolicy": "explicit-allowlist",
        },
        "checks": {
            "director": {"status": "pending"},
            "builder": {"status": "pending"},
            "browser": {"status": "pending"},
            "sourceIsolation": {"status": "pending"},
            "evaluator": {"status": "pending"},
        },
        "error": None,
    }
    if not isinstance(token, str) or not token.strip():
        report["status"] = "blocked"
        report["error"] = {
            "step": "authentication",
            "kind": "copilot-auth",
            "message": (
                "GITHUB_TOKEN is required for the Copilot CLI capability gate"
            ),
        }
        report["finishedAt"] = now()
        write_json(output_root / "capability-report.json", report)
        return report

    brief = (
        "Create a calm, compact capability-check page with a clear title, "
        "a one-field form, a local success state, visible focus, "
        "reduced-motion support, and a mobile layout that does not overflow. "
        "Use no external assets or network calls."
    )
    current_step = "director"
    try:
        director_dir = workspaces / "director"
        director_dir.mkdir(parents=True, exist_ok=True)
        director_result = invoke_role(
            role="director",
            workspace=director_dir,
            evidence_dir=evidence_dir,
            token=token,
            copilot_bin=copilot_bin,
            model=model,
            prompt=director_prompt(brief),
            available_tools="edit",
            allow_tools="write",
            deny_tools="read,shell,url,memory",
            command_runner=command_runner,
        )
        direction = validate_direction(director_dir / "direction.json")
        director_files = ensure_exact_workspace_files(
            director_dir,
            {"direction.json"},
            "director workspace",
        )
        report["checks"]["director"] = {
            **director_result,
            "files": director_files,
            "direction": direction,
        }

        current_step = "builder"
        builder_dir = workspaces / "builder"
        builder_dir.mkdir(parents=True, exist_ok=True)
        (builder_dir / "brief.md").write_text(
            brief + "\n",
            encoding="utf-8",
        )
        write_json(builder_dir / "direction.json", direction)
        (builder_dir / "baseline.css").write_text(
            ":root { --capability-accent: #176b5b; "
            "--capability-surface: #f4f1e8; }\n"
            f"/* {SOURCE_CANARY} */\n",
            encoding="utf-8",
        )
        builder_seed_names = {"brief.md", "direction.json", "baseline.css"}
        builder_seed_digests = snapshot_file_digests(
            builder_dir,
            builder_seed_names,
            "builder source input",
        )
        report["checks"]["builder"] = {
            "status": "running",
            "sourceInputDigests": builder_seed_digests,
        }
        builder_result = invoke_role(
            role="builder",
            workspace=builder_dir,
            evidence_dir=evidence_dir,
            token=token,
            copilot_bin=copilot_bin,
            model=model,
            prompt=builder_prompt(),
            available_tools="view,edit",
            allow_tools="read,write",
            deny_tools="shell,url,memory",
            command_runner=command_runner,
        )
        require_unchanged_file_digests(
            builder_dir,
            builder_seed_digests,
            "builder source inputs",
        )
        site_contract = validate_site(builder_dir / "index.html")
        builder_files = ensure_exact_workspace_files(
            builder_dir,
            {"brief.md", "direction.json", "baseline.css", "index.html"},
            "builder workspace",
        )
        publish_file_no_follow(
            builder_dir / "index.html",
            site_dir / "index.html",
            "published site",
        )
        report["checks"]["builder"] = {
            **builder_result,
            "files": builder_files,
            "output": site_contract,
        }

        current_step = "browser"
        browser = browser_runner(site_dir, evidence_dir)
        screenshot_path = evidence_dir / "browser" / "browser-after-submit.png"
        if screenshot_path.is_symlink() or not screenshot_path.is_file():
            raise ContractError(
                "browser evidence is missing a regular browser-after-submit.png"
            )
        report["checks"]["browser"] = {
            "status": "passed",
            "viewport": browser.get("viewport"),
            "interaction": browser.get("interaction"),
            "network": browser.get("network"),
            "screenshot": "evidence/browser/browser-after-submit.png",
        }

        current_step = "sourceIsolation"
        interaction = browser.get("interaction")
        rendered_canary_absent = (
            isinstance(interaction, dict)
            and interaction.get("forbiddenTextVisible") is False
        )
        isolation = {
            "directorHasNoSource": not (
                director_dir / "baseline.css"
            ).exists(),
            "builderReadCanarySource": (
                builder_result.get("readBaselineCss") is True
            ),
            "outputCanaryAbsent": not _contains_text_bytes(
                site_dir / "index.html",
                SOURCE_CANARY,
            ),
            "renderedCanaryAbsent": rendered_canary_absent,
        }
        isolation_passed = all(isolation.values())
        report["checks"]["sourceIsolation"] = {
            "status": "passed" if isolation_passed else "failed",
            **isolation,
        }
        if not isolation_passed:
            raise ContractError(
                f"source isolation proof failed: {isolation}"
            )

        current_step = "evaluator"
        evaluator_dir = workspaces / "evaluator"
        evaluator_dir.mkdir(parents=True, exist_ok=True)
        evaluator_screenshot = evaluator_dir / "browser-after-submit.png"
        publish_file_no_follow(
            screenshot_path,
            evaluator_screenshot,
            "evaluator screenshot",
        )
        attachment_canary_absent = not _contains_text_bytes(
            evaluator_screenshot,
            SOURCE_CANARY,
        )
        report["checks"]["sourceIsolation"].update(
            {
                "evaluatorHasNoSource": not (
                    evaluator_dir / "baseline.css"
                ).exists(),
                "evaluatorRequestCanaryAbsent": attachment_canary_absent,
            }
        )
        if not attachment_canary_absent:
            report["checks"]["sourceIsolation"]["status"] = "failed"
            raise ContractError(
                "evaluator attachment contains the private source canary"
            )

        evaluator_result = invoke_role(
            role="evaluator",
            workspace=evaluator_dir,
            evidence_dir=evidence_dir,
            token=token,
            copilot_bin=copilot_bin,
            model=model,
            prompt=evaluator_prompt(brief),
            available_tools="edit",
            allow_tools="write",
            deny_tools="read,shell,url,memory",
            command_runner=command_runner,
            attachment=evaluator_screenshot,
        )
        evaluation = validate_evaluation(
            evaluator_dir / "evaluation.json"
        )
        evaluator_files = ensure_exact_workspace_files(
            evaluator_dir,
            {"browser-after-submit.png", "evaluation.json"},
            "evaluator workspace",
        )
        evaluator_command = evidence_dir / "evaluator.command.json"
        evaluator_request_canary_absent = not _contains_text_bytes(
            evaluator_command,
            SOURCE_CANARY,
        ) and all(
            not _contains_text_bytes(path, SOURCE_CANARY)
            for path in evaluator_dir.rglob("*")
            if path.is_file()
        )
        report["checks"]["sourceIsolation"].update(
            {
                "evaluatorHasNoSource": not (
                    evaluator_dir / "baseline.css"
                ).exists(),
                "evaluatorRequestCanaryAbsent": (
                    evaluator_request_canary_absent
                ),
            }
        )
        if not evaluator_request_canary_absent:
            report["checks"]["sourceIsolation"]["status"] = "failed"
            raise ContractError(
                "evaluator request or workspace contains the private source canary"
            )
        report["checks"]["evaluator"] = {
            **evaluator_result,
            "files": evaluator_files,
            "evaluation": evaluation,
        }
        scan_for_token(output_root, token)
        report["status"] = "passed"
    except CapabilityBlocked as error:
        report["status"] = "blocked"
        _merge_failed_check(
            report,
            current_step,
            str(error),
            "blocked",
        )
        report["error"] = {
            "step": current_step,
            "kind": "capability-blocked",
            "message": str(error),
        }
    except ContractError as error:
        report["status"] = "failed"
        _merge_failed_check(
            report,
            current_step,
            str(error),
            "failed",
        )
        report["error"] = {
            "step": current_step,
            "kind": "contract",
            "message": str(error),
        }
    except Exception as error:
        report["status"] = "failed"
        message = f"{type(error).__name__}: {error}"
        _merge_failed_check(
            report,
            current_step,
            message,
            "failed",
        )
        report["error"] = {
            "step": current_step,
            "kind": "unexpected",
            "message": message,
        }

    report["finishedAt"] = now()
    write_json(output_root / "capability-report.json", report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prove a constrained Copilot CLI execution surface for the "
            "Design Studio Milestone 0 comparison runner."
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
    parser.add_argument("--copilot-bin", default="copilot")
    parser.add_argument(
        "--copilot-version",
        default=DEFAULT_COPILOT_VERSION,
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_capability(
        token=os.environ.get("GITHUB_TOKEN", ""),
        output_root=args.output_dir,
        copilot_bin=args.copilot_bin,
        copilot_version=args.copilot_version,
        model=args.model,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "surface": report["executionSurface"]["name"],
                "version": report["executionSurface"]["version"],
                "model": report["executionSurface"]["model"],
                "report": str(
                    (args.output_dir / "capability-report.json").resolve()
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
