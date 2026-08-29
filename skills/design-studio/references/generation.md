# Builder contract

## Purpose

Translate the selected source-free visual contract into a working surface without silently changing the design direction.

## Triggers

Load for `studio-build`, REFINE implementation, or any rendered UI change whose job is to preserve an accepted direction.

## Required context

Use `roots.json`, the current `design-description.md`, product truth, sprint/surface constraints, copy baseline, current source substrate, and existing `DESIGN.md` only when extending or refining that proven system. On PIVOT, do not reuse abandoned visual structure merely because it is convenient.

## Outputs and handoff

Write the current iteration's runnable `site/`, validated `serve.json`, and `design-flags.json`. For every material visual instruction record `implemented`, `equivalent` with reason, or `blocked` with evidence. Hand the finished iteration to mechanical preflight; do not self-score aesthetics.

## Authority boundary

Builder chooses technical means, not a different design. Visual Director owns the visual contract, `workflow.yaml` owns iteration paths/transitions, and product/copy authorities own factual claims. Accessibility and state completeness are implementation obligations, not permission to invent a new visual world.

## Failure behavior

Do not mutate prior iterations, self-commit, silently soften signature choices, invent claims, or substitute generic decoration for required assets. If the selected direction is technically blocked, preserve the closest safe behaviour and record the exact constraint in `design-flags.json`.

## Evaluation hooks

Before handoff: run the project build/tests from the recorded app root; validate `serve.json`; check every design flag against the render; exercise primary interactions and reachable states; inspect desktop/mobile for obvious breakage; verify reduced motion; remove debug controls and placeholder claims.

## Procedure

Preserve semantic landmarks, keyboard reachability, visible focus, responsive recomposition, required loading/empty/error/disabled/success states, honest demo labels, recoverable errors and performance safeguards. Keep design tokens in one canonical source. Verify remote assets and provide fallbacks. Earlier iteration trees remain immutable evidence.
