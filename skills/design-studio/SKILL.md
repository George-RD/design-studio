---
name: design-studio
description: >-
  Multi-agent frontend design workflow for new surfaces, full redesigns and high-value visual iteration.
  Separates product framing, visual direction, implementation and blind browser evaluation; roots the target
  before work starts; preserves immutable iterations; resumes from recorded evidence; and documents the
  accepted visual system. Use Review for audit or polish without redesign.
version: 1.5.0
---

# Design Studio

Design Studio is a portable design-engineering method kernel. Keep the always-loaded layer small: lifecycle, source-visibility boundaries, routing, evidence and acceptance authority live here; specialist methods load only when their signals match.

## Role boundaries

| Role | May see source | May see prior scores | Owns |
|---|---:|---:|---|
| Planner | yes | no | scope and success criteria |
| Visual Director | no | no | visual proposals and selected visual contract |
| Builder | yes | no | implementation fidelity |
| Evaluator | no | no | observations and scores |
| Orchestrator | as needed | yes | SELECT / REFINE / PIVOT / SHIP / HALT |

- Visual Director never receives HTML, CSS, JSX, component names, selectors, implementation diffs or an unattended assignment index.
- Evaluator never receives source, implementation effort, the full design description or prior scores.
- Builder may add semantics, accessibility, responsive behaviour and required states, but may not replace the selected direction with a safer one.
- Orchestrator is the sole decision owner. Reviewer or evaluator output cannot accept, pivot or ship a build.

## Load and route

1. Load `invocation.md` to map host inputs and isolated roles.
2. Load `workflow.yaml` for lifecycle, schemas, paths, budgets and decisions.
3. Load `runtime-contract.md`, `references/context.md` and `references/runtime-integrity.md` for deterministic operations and current run truth.
4. Read `method-router.json`. Match the current task, surface, interaction and evidence signals, then load only the smallest matching leaf set.
5. Never load every review or specialist leaf by default. A later signal may add a leaf; it does not make the full catalog ambient context.

`method-router.json` is routing data, not another method authority. Canonical ownership remains in `docs/method-authority-map.json`.

## Lanes

| Lane | Trigger | Execution authority |
|---|---|---|
| **Studio** | new surface, material redesign or replacement visual world | `workflow.yaml` |
| **Review** | audit or polish while preserving the current visual world | routed `references/review/polish.md` |
| **Design system** | codify or extend an accepted system | codify step in `workflow.yaml` and the design-system template |
| **Meta** | improve Design Studio itself | routed `references/meta.md` plus run evidence |

A narrow component/CSS correction does not require a full Studio run. When audit and redesign are mixed, Studio owns unless the user explicitly asks for report-only review first.

## Studio kernel

Execute `workflow.yaml` end to end.

- Root the repository, runnable app and governing context before planning; probe real capabilities rather than assuming them.
- Keep product truth, copy authority, current surface strategy and proven visual authority separate.
- Before unattended direction generation, commit the deterministic candidate assignment and keep it hidden from Visual Director.
- Generate genuinely different, equally viable directions; the user or precommitted assignment selects. Builder then implements the selected source-free contract.
- Run local deterministic mechanical evidence before blind browser evaluation. Mechanics are a floor, never an aesthetic score.
- Evaluator interacts with the live render at required viewports without source or prior scores. Orchestrator alone applies the workflow decision table.
- Preserve every evaluated build and evidence record. Finish chooses the strongest eligible build, verifies the final tree and records acceptance before codification.

The brief wins. Redesign replaces the visual world while preserving confirmed product truth, behaviour and explicit commitments; refinement preserves the established world.

## Review kernel

Review never runs the Studio create loop. Route through `references/review/polish.md`, then add only the lenses whose signals match. Reviewers report evidence first; implementation receives one bounded fix plan. Missing browser evidence produces `visual_status: unverified`, not a clean visual verdict.

## Evidence and acceptance

- `roots.json` and `capabilities.json` are operational truth.
- `events.jsonl` is the append-only recovery source; resume validates artifacts before trusting completion.
- `PRODUCT.md` stores confirmed durable product truth. `COPY.md` stores durable language rules when present. `DESIGN.md` stores a proven visual system only after acceptance.
- Mechanical snapshots are complete current-state evidence. Missing evidence is explicit and never converted into pass.
- Only `finish/acceptance.json` proves which final tree became authoritative. Directory existence or a high score is not acceptance.

## Degradation

Studio needs file I/O, shell access and isolated roles. A visual decision also needs a runnable target and browser automation.

- No browser or runnable target in Studio: keep one build and mechanical evidence, then halt without a visual winner.
- Missing either required viewport in Review: return mechanical/partial evidence with visual status `unverified`.
- No user-answer mechanism: use the precommitted deterministic assignment.
- No image generation: use equally specified text directions; never fabricate comps.
- Missing evidence or a failed deterministic operation is recorded with its exact reason.

## Method ownership and intake

Design Studio has no upstream design-method runtime dependency. Pinned research sources, dispositions and exact revisions live in `docs/method-sources.json` and `docs/method-authority-map.json`.

- `adapt-local` methods are available only through the local leaf named in `method-router.json`.
- `observe` and `reject` entries are research evidence, not permission to copy or ambient guidance.
- Do not import another command taxonomy, prompt library or fallback runtime around the local kernel.
- Growth Arsenal owns offer, positioning, persuasion strategy and authoritative copy. Design Studio consumes approved composition artifacts through its local copy boundary; it does not reproduce Growth Arsenal methods.

A new method must name a reusable gap, fit an existing authority or justify a new one, pin source/licence when external, adapt the smallest coherent slice, record modifications and prove benefit with an eval, contract test or dogfood evidence.
