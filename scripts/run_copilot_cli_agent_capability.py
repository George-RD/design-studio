#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Callable, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
BROWSER_SCRIPT = SCRIPT_DIR / "run_browser_capability.mjs"
REPORT_SCHEMA_VERSION = 1
SOURCE_CANARY = "DESIGN_STUDIO_PRIVATE_SOURCE_CANARY_6f3b9d2a"
DEFAULT_COPILOT_VERSION = "1.0.74"
DEFAULT_MODEL = "gpt-5.4"
MAX_AI_CREDITS = 30


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
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def default_command_runner(argv: Sequence[str], *, cwd: Path, env: dict[str, str]) -> CommandOutcome:
    completed = subprocess.run(
        [str(part) for part in argv],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=360,
    )
    return CommandOutcome(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def default_browser_runner(site_dir: Path, evidence_dir: Path) -> dict[str, Any]:
    browser_dir = evidence_dir / "browser"
    browser_dir.mkdir(parents=True, exist_ok=True)
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
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    (browser_dir / "stdout.log").write_text(completed.stdout, encoding="utf-8")
    (browser_dir / "stderr.log").write_text(completed.stderr, encoding="utf-8")
    report = load_json_object(browser_dir / "browser-report.json", "browser report")
    status = report.get("status")
    if status == "blocked":
        raise CapabilityBlocked(require_text(report.get("error"), "browser error"))
    if completed.returncode != 0 or status != "passed":
        failures = report.get("failures")
        raise ContractError(f"browser capability failed: {failures or report.get('error')}")
    return report


def parse_jsonl(text: str, label: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            value = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ContractError(f"{label} line {line_number} is not JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ContractError(f"{label} line {line_number} must be a JSON object")
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
    )
    return "blocked" if any(marker in text for marker in blocked_markers) else "failed"


def safe_persist_output(path: Path, text: str, token: str) -> None:
    if token and token in text:
        path.write_text(text.replace(token, "<redacted-token>"), encoding="utf-8")
        raise ContractError(f"{path.name} attempted to persist the authentication token")
    path.write_text(text, encoding="utf-8")


def ensure_exact_workspace_files(root: Path, expected: set[str], label: str) -> list[str]:
    actual: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ContractError(f"{label} contains a symlink: {path.relative_to(root)}")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ContractError(
            f"{label} file boundary changed: missing={missing}, unexpected={unexpected}"
        )
    return sorted(actual)


def validate_direction(path: Path) -> dict[str, str]:
    value = load_json_object(path, "director direction")
    expected = {"concept", "palette", "layout", "interaction"}
    if set(value) != expected:
        raise ContractError(f"direction keys must be exactly {sorted(expected)}")
    return {key: require_text(value.get(key), f"direction.{key}") for key in sorted(expected)}


class CapabilityHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.has_submit = False
        self.has_viewport = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.add(element_id)
        if tag == "button" and values.get("type", "submit").lower() == "submit":
            self.has_submit = True
        if tag == "input" and values.get("type", "text").lower() == "submit":
            self.has_submit = True
        if tag == "meta" and values.get("name", "").lower() == "viewport":
            self.has_viewport = True


def validate_site(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ContractError("builder did not produce index.html") from exc
    if len(text.encode("utf-8")) > 200_000:
        raise ContractError("index.html exceeds the 200 KB capability limit")
    if SOURCE_CANARY in text:
        raise ContractError("index.html leaked the private source canary")
    parser = CapabilityHtmlParser()
    parser.feed(text)
    required_ids = {"capability-form", "capability-name", "capability-success"}
    missing_ids = sorted(required_ids - parser.ids)
    if missing_ids:
        raise ContractError(f"index.html is missing required IDs: {missing_ids}")
    if not parser.has_submit:
        raise ContractError("index.html has no submit control")
    if not parser.has_viewport:
        raise ContractError("index.html has no viewport declaration")
    return {
        "entrypoint": "index.html",
        "bytes": len(text.encode("utf-8")),
        "requiredIds": sorted(required_ids),
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
        raise ContractError(f"evaluation keys must be exactly {sorted(expected)}")
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
        for key in ("titleVisible", "formVisible", "successVisible", "layoutUsable")
        if not value[key]
    ]
    if value["sourceCanaryVisible"]:
        failures.append("sourceCanaryVisible")
    if failures:
        raise ContractError(f"source-blind evaluator rejected visible contract: {failures}")
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
    write_json(
        evidence_dir / f"{role}.command.json",
        {
            "argv": command,
            "workingDirectory": f"workspaces/{role}",
            "environmentContract": ["GITHUB_TOKEN", "COPILOT_HOME"],
        },
    )
    environment = os.environ.copy()
    environment.update(
        {
            "GITHUB_TOKEN": token,
            "COPILOT_HOME": str(copilot_home),
            "COPILOT_AUTO_UPDATE": "false",
        }
    )
    outcome = command_runner(command, cwd=workspace, env=environment)
    stdout_path = evidence_dir / f"{role}.stdout.jsonl"
    stderr_path = evidence_dir / f"{role}.stderr.log"
    safe_persist_output(stdout_path, outcome.stdout, token)
    safe_persist_output(stderr_path, outcome.stderr, token)
    if outcome.exit_code != 0:
        status = classify_cli_failure(outcome)
        message = outcome.stderr.strip() or outcome.stdout.strip() or f"exit {outcome.exit_code}"
        if status == "blocked":
            raise CapabilityBlocked(f"{role} Copilot CLI was blocked: {message[:1000]}")
        raise ContractError(f"{role} Copilot CLI failed: {message[:1000]}")
    events = parse_jsonl(outcome.stdout, f"{role} Copilot JSONL")
    return {
        "status": "passed",
        "eventCount": len(events),
        "stdout": f"evidence/{role}.stdout.jsonl",
        "stderr": f"evidence/{role}.stderr.log",
        "command": f"evidence/{role}.command.json",
    }


def scan_for_token(root: Path, token: str) -> None:
    if not token:
        return
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            if token in path.read_text(encoding="utf-8", errors="ignore"):
                raise ContractError(f"authentication token persisted in {path.relative_to(root)}")


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
    output_root = output_root.resolve()
    workspaces = output_root / "workspaces"
    evidence_dir = output_root / "evidence"
    site_dir = output_root / "site"
    for directory in (workspaces, evidence_dir, site_dir):
        directory.mkdir(parents=True, exist_ok=True)

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
            "message": "GITHUB_TOKEN is required for the Copilot CLI capability gate",
        }
        report["finishedAt"] = now()
        write_json(output_root / "capability-report.json", report)
        return report

    brief = (
        "Create a calm, compact capability-check page with a clear title, a one-field form, "
        "a local success state, visible focus, reduced-motion support, and a mobile layout "
        "that does not overflow. Use no external assets or network calls."
    )
    current_step = "director"
    try:
        director_dir = workspaces / "director"
        director_dir.mkdir()
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
            director_dir, {"direction.json"}, "director workspace"
        )
        report["checks"]["director"] = {
            **director_result,
            "files": director_files,
            "direction": direction,
        }

        current_step = "builder"
        builder_dir = workspaces / "builder"
        builder_dir.mkdir()
        (builder_dir / "brief.md").write_text(brief + "\n", encoding="utf-8")
        write_json(builder_dir / "direction.json", direction)
        (builder_dir / "baseline.css").write_text(
            ":root { --capability-accent: #176b5b; --capability-surface: #f4f1e8; }\n"
            f"/* {SOURCE_CANARY} */\n",
            encoding="utf-8",
        )
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
        site_contract = validate_site(builder_dir / "index.html")
        builder_files = ensure_exact_workspace_files(
            builder_dir,
            {"brief.md", "direction.json", "baseline.css", "index.html"},
            "builder workspace",
        )
        shutil.copy2(builder_dir / "index.html", site_dir / "index.html")
        report["checks"]["builder"] = {
            **builder_result,
            "files": builder_files,
            "output": site_contract,
        }

        current_step = "browser"
        browser = browser_runner(site_dir, evidence_dir)
        screenshot_path = evidence_dir / "browser" / "browser-after-submit.png"
        if not screenshot_path.is_file():
            raise ContractError("browser evidence is missing browser-after-submit.png")
        report["checks"]["browser"] = {
            "status": "passed",
            "viewport": browser.get("viewport"),
            "interaction": browser.get("interaction"),
            "network": browser.get("network"),
            "screenshot": "evidence/browser/browser-after-submit.png",
        }

        current_step = "sourceIsolation"
        isolation = {
            "directorHasNoSource": not (director_dir / "baseline.css").exists(),
            "builderReadCanarySource": SOURCE_CANARY in (builder_dir / "baseline.css").read_text(encoding="utf-8"),
            "outputCanaryAbsent": SOURCE_CANARY not in (site_dir / "index.html").read_text(encoding="utf-8"),
        }
        if not all(isolation.values()):
            raise ContractError(f"source isolation proof failed: {isolation}")
        report["checks"]["sourceIsolation"] = {"status": "passed", **isolation}

        current_step = "evaluator"
        evaluator_dir = workspaces / "evaluator"
        evaluator_dir.mkdir()
        evaluator_screenshot = evaluator_dir / "browser-after-submit.png"
        shutil.copy2(screenshot_path, evaluator_screenshot)
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
        evaluation = validate_evaluation(evaluator_dir / "evaluation.json")
        evaluator_files = ensure_exact_workspace_files(
            evaluator_dir,
            {"browser-after-submit.png", "evaluation.json"},
            "evaluator workspace",
        )
        evaluator_request = json.loads(
            (evidence_dir / "evaluator.command.json").read_text(encoding="utf-8")
        )
        serialized_request = json.dumps(evaluator_request)
        if SOURCE_CANARY in serialized_request:
            raise ContractError("evaluator command leaked the private source canary")
        report["checks"]["evaluator"] = {
            **evaluator_result,
            "files": evaluator_files,
            "evaluation": evaluation,
        }
        report["checks"]["sourceIsolation"].update(
            {
                "evaluatorHasNoSource": not (evaluator_dir / "baseline.css").exists(),
                "evaluatorRequestCanaryAbsent": True,
            }
        )
        scan_for_token(output_root, token)
        report["status"] = "passed"
    except CapabilityBlocked as error:
        report["status"] = "blocked"
        report["checks"][current_step] = {"status": "blocked", "message": str(error)}
        report["error"] = {
            "step": current_step,
            "kind": "copilot-auth",
            "message": str(error),
        }
    except ContractError as error:
        report["status"] = "failed"
        report["checks"][current_step] = {"status": "failed", "message": str(error)}
        report["error"] = {
            "step": current_step,
            "kind": "contract",
            "message": str(error),
        }
    except Exception as error:
        report["status"] = "failed"
        report["checks"][current_step] = {
            "status": "failed",
            "message": f"{type(error).__name__}: {error}",
        }
        report["error"] = {
            "step": current_step,
            "kind": "unexpected",
            "message": f"{type(error).__name__}: {error}",
        }

    report["finishedAt"] = now()
    write_json(output_root / "capability-report.json", report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prove a constrained Copilot CLI execution surface for the Design Studio "
            "Milestone 0 comparison runner."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("harness-output") / "benchmarks" / "milestone-0" / "agent-capability",
    )
    parser.add_argument("--copilot-bin", default="copilot")
    parser.add_argument("--copilot-version", default=DEFAULT_COPILOT_VERSION)
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
