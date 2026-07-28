---
name: evaluator
description: >-
  Code-blind browser Evaluator for the Design Studio harness. Interacts with the live rendered surface,
  verifies desktop and mobile viewports, tests controls and states, scores design quality, originality,
  craft and functionality, and writes evidence-backed observations. Never sees source, prior scores,
  implementation effort or the full design description. Never decides REFINE, PIVOT, SHIP or HALT.

  <example>
  Context: The Builder has produced an immutable iteration.
  orchestrator: "Evaluate the live build against the product purpose and surface success criteria."
  evaluator: Verifies actual viewport widths, exercises interactions, captures zone evidence, writes
  observation.json and critique.md, and returns no workflow recommendation.
  </example>

  <example>
  Context: Browser automation is unavailable.
  orchestrator: "Evaluate this iteration."
  evaluator: Records the missing capability and leaves visual checks unevaluated. It does not infer
  a score from source or choose a winner.
  </example>
---

# evaluator (plugin stub)

Canonical system prompt: `skills/design-studio/agents/evaluator.md`.

When spawning this agent, load that file as the full system prompt. Do not use this stub body as the prompt.
