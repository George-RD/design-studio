# Compatibility reference: evaluation

This path remains for older commands and third-party runners. It is not a second evaluation authority.

The canonical visual evaluator prompt is `../agents/evaluator.md`. The observation schema, viewport requirements, quality floor and workflow transitions are owned by `../workflow.yaml`. Deterministic and source/computed checks are owned by `quality-gates.md`.

Hard boundaries:

- the Evaluator receives the live render, product purpose, surface success criteria and a summary of mechanical findings;
- it does not receive source, the design description, design flags, prior scores, implementation effort or workflow history;
- it writes visual observations, interaction evidence, zone scores and whole-surface scores only;
- it never emits REFINE, PIVOT, SHIP, HALT, best-iteration selection or trend advice;
- it does not infer exact tokens, CSS values, DOM structure or implementation defects from screenshots.

The Orchestrator is the sole decision owner. Do not copy a rubric or decision table into this file: duplication creates drift and can silently restore the previous two-authority workflow.
