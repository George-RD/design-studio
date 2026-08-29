---
name: create
description: Create or overhaul a distinctive frontend through isolated direction, implementation, mechanical preflight, blind evaluation, bounded iteration and design-system capture.
argument-hint: "<prompt> | --overhaul <path-or-url> [--goals <text>] [--budget quick|standard|ambitious|<n>] <prompt>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
  - WebFetch
  - WebSearch
---

# Design Studio: Create

This file is an optional Claude Code adapter over the canonical Agent Skill in `skills/design-studio/`.

Load `skills/design-studio/SKILL.md`, `skills/design-studio/invocation.md` and `skills/design-studio/runtime-contract.md`. Map `$ARGUMENTS` to the Studio inputs defined by the skill, use Claude Code's `Agent` tool as the host implementation of `isolated_subagents`, and delegate execution to `skills/design-studio/workflow.yaml` through that shared runtime contract.

The adapter contributes invocation metadata only; the installed skill owns design methods, workflow decisions and deterministic runtime behavior.
