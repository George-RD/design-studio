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

Load `skills/design-studio/SKILL.md`, then execute `skills/design-studio/references/review/polish.md` only.

Parse `$ARGUMENTS` into:

- `target`: local path or URL.
- `constraints`: remaining text.
- `report_only`: true when `--report-only` is present.
- `mechanical_only`: true when `--mechanical-only` is present.

Do not execute `workflow.yaml`, create design directions, score originality, or return REFINE/PIVOT/SHIP. Review ends with a readiness verdict. If browser automation is unavailable, return a mechanical-only report with visual status `unverified`; never pretend a source scan is a visual judgment.
