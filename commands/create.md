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

Run the Studio lane from `skills/design-studio/SKILL.md` and `skills/design-studio/workflow.yaml`.

Parse `$ARGUMENTS` into:

- `user_prompt`: the remaining request.
- `existing_site`: local path after `--overhaul`, when present.
- `existing_url`: URL after `--overhaul`, when present.
- `overhaul_goals`: text after `--goals`, when present.
- `budget_override`: `quick`, `standard`, `ambitious`, or an explicit integer after `--budget`; the workflow clamps it to the supported range.

Rules:

1. Audit/polish-only language routes to `/design-studio:review`; do not start Studio.
2. Load existing `PRODUCT.md`, `DESIGN.md`, and the relevant surface brief before asking questions.
3. Execute the workflow end to end. Do not collapse Visual Director, Builder and Evaluator into one context.
4. Preserve every iteration under its immutable run directory. Never ask an agent to self-commit.
5. The Evaluator writes observations and scores only. The Orchestrator alone writes decisions.
6. On completion, run the bounded finish pass on the selected build, copy the accepted final tree to `harness-output/site/`, then codify and report.
