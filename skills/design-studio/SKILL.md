---
name: design-studio
description: >-
  Portable design-engineering Agent Skill for Studio, Review and paginated Document work. Separates
  product framing, source-blind visual direction and evaluation, implementation and deterministic evidence.
version: 1.7.0
---

# Design Studio

Design Studio is a portable design-engineering kernel. Lifecycle, source boundaries, routing, evidence and acceptance stay small here; specialist methods load only when signals match.

## Role boundaries

| Role | Source | Prior scores | Owns |
|---|---:|---:|---|
| Planner | yes | no | scope and success criteria |
| Visual Director | no | no | visual directions and selected visual contract |
| Builder | yes | no | implementation fidelity |
| Evaluator | no | no | rendered observations and scores |
| Orchestrator | as needed | yes | SELECT / REFINE / PIVOT / SHIP / HALT |

- Visual Director never receives HTML, CSS, JSX, selectors, implementation diffs or the unattended assignment index.
- Evaluator never receives source, implementation effort, full design description or prior scores. Document evaluation also excludes renderer identity/build metadata.
- Builder implements the selected direction; it may not quietly replace it with a safer one.
- Orchestrator is the sole decision owner. Evaluators/reviewers provide evidence, not workflow decisions.

## Load and route

1. Load `invocation.md` for host input mapping and isolated-role rules.
2. Load `workflow.yaml` for the interactive Studio lifecycle and shared schemas/budgets/decisions.
3. Load `runtime-contract.md`, `references/context.md` and `references/runtime-integrity.md` for deterministic operations and run truth.
4. Read `method-router.json`. Every populated signal dimension on a route is required; load the union of matching `leaves`. If the route declares `procedure`, run that progressively disclosed procedure after its leaves.
5. Never load the full specialist catalog by default.

`method-router.json` is routing data, not method authority. Repository ADR/authority-map paths are provenance metadata only; installed runs do not depend on repository docs.

## Required references

- `invocation.md`
- `workflow.yaml`
- `runtime-contract.md`
- `method-router.json`
- `references/context.md`
- `references/runtime-integrity.md`
- Conditional Document procedure: `references/document/document.md`

The first six entries are the installed kernel. Document and specialist methods are conditional.

## Lanes

| Lane | Trigger | Authority |
|---|---|---|
| **Studio** | new interactive surface or material redesign | `workflow.yaml` |
| **Review** | audit/polish while preserving an interactive visual world | routed `references/review/polish.md` |
| **Document** | quote, invoice, SOW, proposal, report, brief, print/PDF or other paginated artifact | routed `references/document/document.md` |
| **Design system** | codify an accepted system | Studio codify or accepted Document contract |
| **Meta** | improve Design Studio | routed `references/meta.md` |

An interactive report remains Studio/Review even if it can export PDF. Page/print intent and pagination route to Document. A narrow component/CSS correction does not require Studio.

## Studio

Execute `workflow.yaml` end to end.

- Prove repository/app/context roots and actual capabilities before planning.
- Separate product truth, copy authority and proven visual authority.
- Commit unattended candidate assignment before direction generation and hide it from Visual Director.
- Generate materially different viable directions; user choice or precommitted assignment selects.
- Builder implements the source-free direction. Local mechanical evidence runs before blind browser evaluation.
- Evaluator uses required live viewports without source/prior scores. Orchestrator alone decides.
- Preserve evaluated builds/evidence. Acceptance names the final tree before codification.

The brief wins. Redesign replaces the visual world while preserving confirmed truth/behaviour; refinement preserves the established world.

## Document

Execute `references/document/document.md`; do not force pages through the browser viewport graph. Reuse the same root, capability, assignment, mechanical-snapshot, evidence, decision and acceptance primitives over complete ordered rendered pages.

- A4 is default; Letter and explicit physical sizes are supported without binding the visual model to a renderer.
- Visual Director/Evaluator may receive rendered page images, never document source, renderer identity or implementation rationale.
- Reuse hierarchy and generated-specificity methods, then the Document pagination, table, furniture and print lenses. Interaction/motion review does not apply.
- Rendering/export is optional host capability. Without complete page evidence, creation preserves one build and halts unselected; review returns visual status unverified.
- Accepted Document work may emit `harness-output/design-system/document-visual-contract.json` for downstream document-generation skills.

Design Studio owns visual page-system intent and rendered-page judgement. It does not own transcript interpretation, business voice, accounting truth, binding commercial/legal terms or the renderer/generator.

## Review

Review does not run the Studio create loop. Route through `references/review/polish.md`, then add only matching lenses. Reviewers report evidence first; implementation receives one bounded fix plan. Missing rendered evidence is `unverified`, not a clean verdict.

## Evidence and degradation

- `roots.json`/`capabilities.json` are operational truth; `events.jsonl` is append-only recovery truth.
- `PRODUCT.md` stores confirmed product truth; `COPY.md` durable language rules; `DESIGN.md` only proven accepted visual authority.
- Mechanical snapshots are complete current-state evidence. Missing evidence is explicit, never a pass.
- Acceptance, not directory existence or a high score, proves authority.

All create lanes need file I/O, shell and isolated roles. Interactive visual decisions additionally need a runnable target/browser; Document decisions need complete rendered page evidence from an existing artifact or host-supplied renderer.

- Missing browser in Studio: one build + mechanical evidence, then halt without winner.
- Missing interactive viewport in Review: partial evidence, visual status unverified.
- Missing complete pages in Document: never infer quality from source; follow the Document failure contract.
- No user-answer mechanism: use precommitted deterministic assignment.
- No image generation: use equally specified text directions.
- Any failed/missing operation is recorded with exact reason.

## Method ownership

Design Studio has no upstream design-method runtime dependency. Adopted external ideas live as routed local methods with provenance; observation/rejection records are research evidence only. Do not import another command taxonomy, prompt library or fallback runtime.

Growth Arsenal remains outside this method kernel and may provide approved role-scoped offer/copy artifacts through the composition boundary. A new method must name a reusable gap, fit or justify authority, pin external source/licence when relevant, adapt the smallest coherent slice and prove benefit with an eval/contract/dogfood result.
