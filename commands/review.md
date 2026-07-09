---
name: review
description: Audit/polish an existing UI without the full design-studio create loop. Conditional lenses (slop, hierarchy, interaction, a11y).
argument-hint: "<path-or-url> [constraints] | --report-only <path-or-url>"
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

You are the **Review orchestrator**. Run the audit/polish lane for the user's existing UI without the create loop. Do not restate the lens catalog, BOC, or the full loop narrative here — load the leaf.

## Input

`$ARGUMENTS` — orchestrator parses shapes (not a real CLI):

- **Audit/polish:** `<path-or-url> [constraints]`
  - Map path/URL → Review target `target`; remainder → `constraints`.
- **Report only:** `--report-only <path-or-url> [constraints]`
  - Set `report_only: true`; the run writes findings but makes no edits.

## Execute

1. Read `skills/design-studio/SKILL.md` (INDEX + intent dispatch + routing table).
2. Load `skills/design-studio/references/review/polish.md` and run the Review lane only (classify surface, load conditional lenses, browser-ground, fan-out, aggregate, act), with `target`, `constraints`, and `report_only` parsed per Input above.
3. Do **not** execute `skills/design-studio/workflow.yaml` (the Studio create loop). Review is an audit/polish path, not Plan → Design → Build.
4. Paths above are repo-root relative (same convention as `commands/create.md`).

Spawn lens subagents via your harness subagent mechanism with per-lens context isolation.
