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

This command is a Claude Code adapter over the canonical Agent Skill.

Load `skills/design-studio/SKILL.md`, `skills/design-studio/invocation.md` and `skills/design-studio/references/runtime-contract.md`. Map `$ARGUMENTS` to the Studio inputs defined there, using Claude Code's `Agent` tool as the host implementation of `isolated_subagents`, then execute `skills/design-studio/workflow.yaml` end to end through the shared runtime contract.

Do not add command-specific workflow logic, deterministic operations or a second quality mode. The skill owns routing and role boundaries; the runtime contract owns deterministic operation and failure semantics; the workflow owns iteration, evaluation and acceptance order.
