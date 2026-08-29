---
name: review
description: Optional Claude Code command adapter for invoking the canonical Design Studio review workflow.
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

Load `skills/design-studio/SKILL.md`, `skills/design-studio/invocation.md` and `skills/design-studio/runtime-contract.md`. Map `$ARGUMENTS` to the Review inputs defined by the skill, use Claude Code's `Agent` tool as the host implementation of `isolated_subagents`, and delegate execution to `skills/design-studio/references/review/polish.md` through that shared runtime contract.

The adapter contributes invocation metadata only; the installed skill owns review behavior, routing and deterministic runtime semantics.
