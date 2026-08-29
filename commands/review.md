---
name: review
description: Audit and polish an existing UI through deterministic preflight plus browser-grounded visual review, without starting the full create loop.
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

This command is a Claude Code adapter over the canonical Agent Skill.

Load `skills/design-studio/SKILL.md` and `skills/design-studio/references/invocation.md`. Map `$ARGUMENTS` to the Review inputs defined there, using Claude Code's `Agent` tool as the host implementation of `isolated_subagents`, then execute `skills/design-studio/references/review/polish.md` only.

Do not execute `workflow.yaml`, create design directions, score originality, or return REFINE/PIVOT/SHIP. Review ends with a readiness verdict, and the skill remains the authority for degradation behavior when browser automation is unavailable.
