# Review lane: audit and polish

## Purpose

Improve an existing surface without inventing a replacement visual world. Review separates read-only judgement from a bounded executable fix plan and remains independent of the Studio create loop.

## Triggers

Load for audit, polish, ship-readiness review, or evidence-driven refinement that preserves the incumbent `DESIGN.md`. If the user wants a replacement visual world, route to Studio/overhaul instead.

## Required context

Resolve one target and its primary goal. Load roots/capabilities, `PRODUCT.md`, optional `COPY.md`, current `DESIGN.md`, relevant surface brief and the current local mechanical snapshot. With browser capability, verify desktop/mobile viewports and capture the states needed to support findings.

## Outputs and handoff

1. Classify the surface and scope.
2. Run the local mechanical gate in `../quality-gates.md` when mechanical evidence is routed.
3. When browser-grounded, invoke only the read-only lens leaves already selected by `method-router.json`; this leaf aggregates their evidence and does not maintain a second lens-selection rule.
4. Deduplicate findings by user-visible defect and retain supporting evidence.
5. Produce one bounded fix plan mapping each accepted Blocker/Quality finding to the intended correction and verification evidence.
6. When editing is requested, implementation executes that plan in one grouped batch, then Review reruns the complete mechanical snapshot and recaptures the same viewports once.

Write review evidence under the review output path defined by the runtime contract, including findings, mechanical evidence, screenshots and final verdict.

## Authority boundary

Lens agents are read-only and do not edit, accept, redesign or choose workflow transitions. `method-router.json` alone decides which specialist leaves are loaded. Mechanical facts come from the local deterministic gate. `DESIGN.md` is visual authority in Review. Orchestrator/host owns whether the bounded fix plan is executed; Review owns the final ready/hold/unverified verdict for this lane only.

## Failure behavior

No browser, unreachable required viewport, or `mechanical_only` returns `visual_status: unverified`. Open Blocker or material Quality findings return `hold`. Do not start per-tweak screenshot loops, create competing design directions, or hide an intentional exception; use an exact authority-backed waiver.

## Evaluation hooks

Severity: Blocker prevents the primary task or access; Quality is a material hierarchy/craft/state/specificity defect; Polish is local refinement. `ready` requires browser-grounded evidence with no open Blocker/Quality and cleared/waived primary mechanical findings; `ready_with_nits` leaves Polish only.

## Source provenance

Adopted local method slice: `emilkowalski/skills` at revision `d23d7f88a2e21c9e4b1418c7abe420f5c1052ba7`, MIT. Design Studio adapts only the read-only expert-audit to executable-plan handoff shape. It keeps local lens taxonomy, source-blind evaluation, immutable evidence and decision ownership; it does not copy the upstream animation-plan workflow, source-code recon procedure or executor conventions.
