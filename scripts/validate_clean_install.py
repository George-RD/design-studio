#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


SKILL_ROOT = Path("skills") / "design-studio"
GENERIC_REQUIRED_CAPABILITIES = {"file_io", "shell", "isolated_subagents"}
INSTALL_FACING_FILES = (
    SKILL_ROOT / "SKILL.md",
    SKILL_ROOT / "workflow.yaml",
    Path("README.md"),
    Path("docs") / "index.html",
    Path(".claude-plugin") / "plugin.json",
    Path(".claude-plugin") / "marketplace.json",
)
EXTERNAL_DESIGN_SKILLS = ("impeccable", "emil kowalski", "growth arsenal")
INVOCATION_TOKENS = {
    "--overhaul",
    "--goals",
    "--budget",
    "--report-only",
    "--mechanical-only",
    "existing_target",
    "overhaul_goals",
    "budget_override",
    "isolated_subagents",
    "Planner",
    "VisualDirector",
    "Builder",
    "Evaluator",
    "Orchestrator",
}


def read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text()
    except FileNotFoundError:
        errors.append(f"missing file: {path}")
        return ""


def parse_required_references(skill_text: str) -> list[str]:
    marker = "## Required references"
    if marker not in skill_text:
        return []
    section = skill_text.split(marker, 1)[1]
    section = re.split(r"\n##\s+", section, maxsplit=1)[0]
    return re.findall(r"`([^`]+)`", section)


def path_is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def external_dependency_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        lower = re.sub(r"\s+", " ", line.lower())
        if not any(term in lower for term in EXTERNAL_DESIGN_SKILLS):
            continue
        if any(
            phrase in lower
            for phrase in (
                "not required",
                "does not require",
                "do not require",
                "no external",
                "optional",
                "when available",
                "research input",
                "research source",
            )
        ):
            continue
        if any(
            phrase in lower
            for phrase in (
                " is required",
                " required to ",
                "must install",
                "requires ",
                "require ",
                "prerequisite",
            )
        ):
            errors.append(
                f"external design-skill dependency in {path}:{line_number}: {line.strip()}"
            )
    return errors


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    skill_root = root / SKILL_ROOT
    skill_path = skill_root / "SKILL.md"
    workflow_path = skill_root / "workflow.yaml"
    invocation_path = skill_root / "references" / "invocation.md"

    skill_text = read_text(skill_path, errors)
    workflow_text = read_text(workflow_path, errors)

    if skill_text:
        if not skill_text.startswith("---\n"):
            errors.append("SKILL.md is missing YAML frontmatter")
        frontmatter = skill_text.split("---", 2)[1] if skill_text.count("---") >= 2 else ""
        name_match = re.search(r"^name:\s*(\S+)\s*$", frontmatter, re.M)
        if name_match is None or name_match.group(1) != "design-studio":
            errors.append("SKILL.md frontmatter must declare name: design-studio")
        if re.search(r"^description:\s*(?:>|>-|\S)", frontmatter, re.M) is None:
            errors.append("SKILL.md frontmatter must declare a non-empty description")

        references = parse_required_references(skill_text)
        if not references:
            errors.append("SKILL.md is missing its Required references contract")
        if "references/invocation.md" not in references:
            errors.append("SKILL.md must route to references/invocation.md")

        for reference in references:
            if reference.startswith(("commands/", "../commands/", "../../commands/", ".claude-plugin/")):
                errors.append(f"plugin-only surface reference from SKILL.md: {reference}")
                continue
            resolved = skill_root / reference
            if not path_is_inside(resolved, skill_root):
                errors.append(f"required reference escapes the skill package: {reference}")
                continue
            if not resolved.is_file():
                errors.append(f"missing required reference: {reference}")

    if workflow_text:
        procedure_paths = re.findall(r"^\s*procedure:\s*([^\s#]+)\s*$", workflow_text, re.M)
        for procedure in procedure_paths:
            resolved = skill_root / procedure
            if not path_is_inside(resolved, skill_root):
                errors.append(f"workflow procedure escapes the skill package: {procedure}")
            elif not resolved.is_file():
                errors.append(f"missing workflow procedure: {procedure}")

        capability_match = re.search(r"^\s*required:\s*\[([^\]]*)\]", workflow_text, re.M)
        if capability_match is None:
            errors.append("workflow.yaml is missing capabilities.required")
        else:
            capabilities = {
                item.strip().strip("'\"")
                for item in capability_match.group(1).split(",")
                if item.strip()
            }
            if capabilities != GENERIC_REQUIRED_CAPABILITIES:
                errors.append(
                    "capabilities.required must be exactly the host-generic set "
                    f"{sorted(GENERIC_REQUIRED_CAPABILITIES)}; got {sorted(capabilities)}"
                )

    invocation_text = read_text(invocation_path, errors)
    if invocation_text:
        missing_tokens = sorted(token for token in INVOCATION_TOKENS if token not in invocation_text)
        if missing_tokens:
            errors.append(f"invocation contract is missing required host/run tokens: {missing_tokens}")

    if skill_root.is_dir():
        for path in skill_root.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(errors="replace")
            for marker in ("commands/", "../commands/", "../../commands/", ".claude-plugin/"):
                if marker in text:
                    errors.append(
                        f"plugin-only surface dependency inside installed skill: {path.relative_to(root)} contains {marker!r}"
                    )

    for relative in INSTALL_FACING_FILES:
        path = root / relative
        text = read_text(path, errors)
        if text:
            errors.extend(external_dependency_errors(relative, text))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the portable Design Studio Agent Skill install contract.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    args = parser.parse_args()

    errors = validate(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        print(f"\nClean-install validation failed with {len(errors)} error(s).")
        return 1

    print("Clean Agent Skill install contract passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
