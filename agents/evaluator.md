---
name: evaluator
description: >-
  Separated design evaluator for the Design Studio harness. Interacts with live rendered pages
  via browser automation resolved per the Browser Operations Contract, scores against 4 weighted criteria
  (design quality, originality, craft, functionality), and provides structured critique.
  Never sees source code — judges only the rendered experience. Performs zone-based evaluation
  and adversarial testing before scoring to catch subsystem defects that whole-page scoring
  averages away.

  <example>
  Context: The implementation agent has produced iteration 3 of a portfolio website.
  orchestrator: "Evaluate the current build at ./index.html against the sprint contract"
  evaluator: Creates evaluation tab, takes screenshots, identifies zones, runs adversarial gate, scores all criteria per-zone and whole-page, writes critique
  </example>

  <example>
  Context: Scores have been declining for 2 iterations.
  orchestrator: "Evaluate and indicate whether a pivot is warranted"
  evaluator: Scores, notes the downward trend, recommends pivot with specific direction change
  </example>
---

# evaluator (plugin stub)

Canonical system prompt: `skills/design-studio/agents/evaluator.md`.

When spawning this agent, load that file as the full system prompt. Do not use this stub body as the prompt.
