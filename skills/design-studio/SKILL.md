---
name: design-studio
description: >-
  Multi-agent visual design workflow for new surfaces, redesigns, page-based artifacts and high-value
  iteration. Separates product framing, visual direction, implementation and blind rendered evaluation;
  preserves immutable iterations; resumes from evidence; and codifies accepted visual systems.
version: 1.6.0
---

# Design Studio

Design Studio is a portable design-engineering method kernel. Keep the always-loaded layer small: lifecycle, source-visibility boundaries, routing, evidence and acceptance authority live here; specialist methods load only when their signals match.

## Role boundaries

| Role | May see source | May see prior scores | Owns |
|---|---:|---:|---|
| Planner | yes | no | scope and success criteria |
| Visual Director | no | no | visual proposals and selected visual contract |
| Builder | yes | no | implementation fidelity |
| Evaluator | no | no | rendered observations and scores |
| Orchestrator | as needed | yes | SELECT / REFINE / PIVOT / SHIP / HALT |

- Visual Director never receives HTML, CSS, JSX, component names, selectors, implementation diffs or an unattended assignment index.
- Evaluator never receives source, implementation effort, the full design description or prior scores. For documents, renderer identity and build metadata are also excluded.
- Builder may add semantics, accessibility, responsive or pagination behaviour and required states, but may not replace the selected direction with a safer one.
- Orchestrator is the sole decision owner. Reviewer or evaluator output cannot accept, pivot or ship a build.

## Load and route

1. Load `invocation.md` to map host inputs and isolated roles.
2. Load `workflow.yaml` for the interactive Studio lifecycle, shared schemas, paths, budgets and decisions.
3. Load `runtime-contract.md`, `references/context.md` and `references/runtime-integrity.md` for deterministic operations and current run truth.
4. Read `method-router.json`. For each route, every populated signal dimension is required; match at least one current value in each populated dimension, then load the union of `leaves` from matching routes. If a matching route declares `procedure`, execute that progressively disclosed lane procedure after its leaves.
5. Never load every review or specialist method by default. Later evidence may add a method; it does not make the full catalog ambient context.

`method-router.json` is routing data, not another method authority. Repository authority-map/ADR paths are provenance metadata only; an installed run does not depend on repository docs being present.

When context discovery identifies compatible role-scoped composition artifacts, emit `composition-artifacts`; the routed copy boundary applies `composition-contract.json` without making another skill a runtime dependency.

## Required references

- `invocation.md`
- `workflow.yaml`
- `runtime-contract.md`
- `method-router.json`
- `references/context.md`
- `references/runtime-integrity.md`
- Conditional Document procedure: `references/document/document.md`

The first six entries form the installed kernel. The Document procedure and specialist methods are conditional.

## Lanes

| Lane | Trigger | Execution authority |
|---|---|---|
| **Studio** | new interactive surface, material redesign or replacement visual world | `workflow.yaml` |
| **Review** | audit or polish while preserving an interactive visual world | routed `references/review/polish.md` |
| **Document** | quote, invoice, SOW, proposal, report, brief, print/PDF or other paginated artifact | routed `references/document/document.md` |
| **Design system** | codify or extend an accepted system | Studio codify step or accepted Document contract |
| **Meta** | improve Design Studio itself | routed `references/meta.md` plus run evidence |

A narrow component/CSS correction does not require Studio. A report that is an interactive application remains Studio/Review; a report intended as pages, PDF or print is a paginated artifact. When audit and redesign are mixed, the create lane owns unless the user explicitly asks for report-only review first.

## Studio kernel

Execute `workflow.yaml` end to end.

- Root the repository, runnable app and governing context before planning; probe real capabilities rather than assuming them.
- Keep product truth, copy authority, current surface strategy and proven visual authority separate.
- Before unattended generation, commit the deterministic candidate assignment and hide it from Visual Director.
- Generate genuinely different viable directions; user choice or precommitted assignment selects. Builder implements the selected source-free contract.
- Run local deterministic mechanical evidence before blind browser evaluation. Mechanics are a floor, never an aesthetic score.
- Evaluator interacts with the live render at required viewports without source or prior scores. Orchestrator alone applies decisions.
- Preserve every evaluated build and evidence record. Finish chooses the strongest eligible build, verifies the final tree and records acceptance before codification.

The brief wins. Redesign replaces the visual world while preserving confirmed product truth, behaviour and explicit commitments; refinement preserves the established world.

## Document kernel

Execute only `references/document/document.md`; do not force page artifacts through the browser viewport graph. The lane reuses the same roots, capability, assignment, mechanical-snapshot, evidence, acceptance and source-isolation primitives, but evaluates a complete ordered set of rendered pages.

- A4 is the default page contract; Letter and explicit physical sizes are supported without binding the visual model to a renderer.
- Visual Director and Evaluator may receive rendered page images, never document source, renderer identity or implementation rationale.
- Document review loads hierarchy and generated-specificity methods plus document-only pagination, table, furniture and print lenses. Interaction and motion review do not apply.
- Rendering/export is an optional host capability. Without complete rendered-page evidence, creation preserves one build and halts unselected; review reports visual status unverified.
- Only an accepted Document run may emit `harness-output/design-system/document-visual-contract.json` for downstream document-generation skills.

## Review kernel

Review never runs the Studio create loop. Route through `references/review/polish.md`, then add only lenses whose signals match. Reviewers report evidence first; implementation receives one bounded fix plan. Missing rendered evidence produces `visual_status: unverified`, not a clean visual verdict.

## Evidence and acceptance

- `roots.json` and `capabilities.json` are operational truth; `events.jsonl` is append-only recovery truth.
- `PRODUCT.md` stores confirmed durable product truth. `COPY.md` stores durable language rules when present. `DESIGN.md` stores a proven visual system only after acceptance.
- Mechanical snapshots are complete current-state evidence. Missing evidence is explicit and never converted into pass.
- Only an acceptance receipt proves which final tree or paginated artifact became authoritative. Directory existence or a high score is not acceptance.

## Degradation

All create lanes need file I/O, shell access and isolated roles. Interactive visual decisions additionally need a runnable target plus browser automation; Document visual decisions need a host-supplied page renderer or existing complete rendered artifact.

- No browser/runnable target in Studio: keep one build and mechanical evidence, then halt without a visual winner.
- Missing required interactive viewport in Review: return partial evidence with visual status `unverified`.
- Missing complete rendered pages in Document: never infer page quality from source; use the Document failure contract.
- No user-answer mechanism: use the precommitted deterministic assignment.
- No image generation: use equally specified text directions; never fabricate comps.
- Missing evidence or failed deterministic operation is recorded with its exact reason.

## Method ownership and intake

Design Studio has no upstream design-method runtime dependency. Repository-level source pins and dispositions live in `docs/method-sources.json` and `docs/method-authority-map.json`; adopted methods carry the provenance needed by the installed skill.

- `adapt-local` methods are available only through their routed local method.
- `observe` and `reject` entries are research evidence, not permission to copy or ambient guidance.
- Do not import another command taxonomy, prompt library or fallback runtime around the local kernel.
- Growth Arsenal owns offer, positioning, persuasion strategy and authoritative copy when composed. Design Studio consumes approved role-scoped artifacts through its local boundary and does not reproduce those methods.
- Document production/rendering, meeting interpretation, business voice, commercial/accounting truth and binding-term decisions remain adjacent authorities. The Document lane owns only visual page-system intent, rendered-page judgement and its reusable visual contract.

A new method must name a reusable gap, fit an existing authority or justify a new one, pin source/licence when external, adapt the smallest coherent slice, record modifications and prove benefit with an eval, contract test or dogfood evidence.
