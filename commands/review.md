---
name: review
description: Optional Claude Code command adapter for canonical Design Studio review and polish work.
argument-hint: "<path-or-url> [constraints] | --report-only <path-or-url> | --mechanical-only <path-or-url>"
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

# Design Studio: Review

This file is an optional Claude Code adapter over the canonical Agent Skill in `skills/design-studio/`.

Load `skills/design-studio/SKILL.md`, `skills/design-studio/invocation.md`, `skills/design-studio/design-intent-contract.json`, `skills/design-studio/references/design-intent.md` and `skills/design-studio/runtime-contract.md`. Map `$ARGUMENTS` to one validated Design Intent before loading Review execution authority. Use Claude Code's `Agent` tool as the host implementation of `isolated_subagents`, then delegate `polish` to `skills/design-studio/references/review/polish.md` through the shared runtime contract.

The adapter contributes invocation metadata only; the installed skill owns Design Intent, review behavior, routing and deterministic runtime semantics.
