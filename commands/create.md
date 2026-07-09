---
name: create
description: Create a distinctive frontend using the generate-evaluate-iterate harness. Greenfield from a prompt, or overhaul an existing UI path/URL, with separated evaluation.
argument-hint: "<prompt> | --overhaul <path-or-url> [--goals <text>] <prompt>"
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

You are the **harness orchestrator**. Run the full design→build→evaluate loop for the user's prompt. Do not restate isolation rules, BOC, thresholds, or the full loop narrative here — load the skill.

## Input

`$ARGUMENTS` — orchestrator parses shapes (not a real CLI):

- **Greenfield:** `<description of the frontend to build>`
- **Overhaul:** `--overhaul <path-or-url> [--goals <constraints>] <prompt>`
  - Map path → Plan input `existing_site`; URL → `existing_url`; `--goals` → `overhaul_goals`; remainder → `user_prompt`.
  - Skill-trigger prose that names an existing path/URL counts as overhaul the same way.
  - If `$ARGUMENTS` is clearly audit/polish-only with no create/overhaul intent, stop and direct the orchestrator to the Review lane (`skills/design-studio/references/review/polish.md` or `/design-studio:review`) instead of starting `workflow.yaml`.

## Execute

1. Read `skills/design-studio/SKILL.md` (INDEX + routing table).
2. If overhaul inputs are present, also load `skills/design-studio/references/overhaul.md` and pass `existing_site` / `existing_url` / `overhaul_goals` into Plan.
3. Execute `skills/design-studio/workflow.yaml` (thresholds, schemas, step prompts, decide table).
4. **DesignAgent** system prompt: `skills/design-studio/agents/design-agent.md`.
5. **Evaluator** system prompt: `skills/design-studio/agents/evaluator.md`.
6. **Builder**: harness subagent + principles from `skills/design-studio/references/generation.md`.
7. Expand plan/decide methodology only when needed: `skills/design-studio/references/planning.md`, `skills/design-studio/references/iteration.md`.

Spawn agents via your harness subagent mechanism with **per-agent context isolation**. Paths above are repo-root.

## Loop control (Claude example)

If the host supports a recurring loop (e.g. Claude Code `/loop`), use it to repeat Design → Implement → Evaluate until SHIP or `maxIterations` from `workflow.yaml` `defaults:`. Otherwise the orchestrator polls the decide step and terminates on SHIP / budget exhaust → codify → finalize.

Cancel the loop when the decision is SHIP or iterations hit the cap; then run codify and finalize per the workflow.
