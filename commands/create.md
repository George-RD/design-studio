---
name: create
description: Create a distinctive frontend using the generate-evaluate-iterate harness. Takes a prompt describing what to build and runs the full harness loop with separated evaluation.
argument-hint: "<description of the frontend to build>"
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

`$ARGUMENTS`

## Execute

1. Read `skills/design-studio/SKILL.md` (INDEX + routing table).
2. Execute `skills/design-studio/workflow.yaml` (thresholds, schemas, step prompts, decide table).
3. **DesignAgent** system prompt: `skills/design-studio/agents/design-agent.md`.
4. **Evaluator** system prompt: `skills/design-studio/agents/evaluator.md`.
5. **Builder**: harness subagent + principles from `skills/design-studio/references/generation.md`.
6. Expand plan/decide methodology only when needed: `skills/design-studio/references/planning.md`, `skills/design-studio/references/iteration.md`.

Spawn agents via your harness subagent mechanism with **per-agent context isolation**. Paths above are repo-root.

## Loop control (Claude example)

If the host supports a recurring loop (e.g. Claude Code `/loop`), use it to repeat Design → Implement → Evaluate until SHIP or `maxIterations` from `workflow.yaml` `defaults:`. Otherwise the orchestrator polls the decide step and terminates on SHIP / budget exhaust → codify → finalize.

Cancel the loop when the decision is SHIP or iterations hit the cap; then run codify and finalize per the workflow.
