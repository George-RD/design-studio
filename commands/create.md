---
name: create
description: Optional Claude Code command adapter for canonical Design Studio create, extend, or overhaul work.
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

Load `skills/design-studio/SKILL.md`, `skills/design-studio/invocation.md`, `skills/design-studio/design-intent-contract.json`, `skills/design-studio/references/design-intent.md` and `skills/design-studio/runtime-contract.md`. Map `$ARGUMENTS` to one validated Design Intent before loading Studio execution authority. Use Claude Code's `Agent` tool as the host implementation of `isolated_subagents`, then delegate the selected create, extend or overhaul mode to `skills/design-studio/workflow.yaml` through the shared runtime contract.

The adapter contributes invocation metadata only; the installed skill owns Design Intent, design methods, workflow decisions and deterministic runtime behavior.
