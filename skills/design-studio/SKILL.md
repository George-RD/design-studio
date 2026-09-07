---
name: design-studio
description: >-
  Portable design-engineering Agent Skill for Studio, Review and paginated Document work. Separates
  product framing, source-blind visual direction and evaluation, implementation and deterministic evidence.
version: 1.7.0
---

# Design Studio

Design Studio is a portable design-engineering kernel with shared guards and progressively disclosed lane procedures and methods.

## Role boundaries

| Role | Source | Prior scores | Owns |
|---|---:|---:|---|
| Planner | yes | no | scope and success criteria |
| Visual Director | no | no | visual directions and selected visual contract |
| Builder | yes | no | implementation fidelity |
| Evaluator | no | no | rendered observations and scores |
| Orchestrator | as needed | yes | SELECT / REFINE / PIVOT / SHIP / HALT |

- Visual Director never receives HTML, CSS, JSX, selectors, implementation diffs, document source/renderer metadata or the unattended assignment index.
- Evaluator never receives source, implementation effort, full design description or prior scores. Document evaluation also excludes renderer identity/build metadata.
- Builder implements the selected direction; it may not quietly replace it with a safer one.
- Orchestrator is the sole decision owner. Evaluators/reviewers provide evidence, not workflow decisions.

## Load and route

For Studio, Review and Document requests:

1. Load `invocation.md`, `design-intent-contract.json`, `references/design-intent.md`, `runtime-contract.md`, `references/context.md` and `references/runtime-integrity.md`. These are the universal input, authority, source/evidence, recovery, degradation and acceptance guards, not lane procedures.
2. Map host input and current authority evidence to one Design Intent and validate it before loading `workflow.yaml`, a Review/Document procedure or any specialist leaf. Invalid classification blocks lane loading as well as execution.
3. Map the validated result to the existing `task`, `surface`, `interaction` and `evidence` signals, then read `method-router.json`. Keep task signals within the selected lane and current stage; supplementary copy or evidence signals do not change that lane.
4. Resolve the canonical `selectedProcedures` even when no specialist route matches. Every populated signal dimension on a route is required. Before loading, check that every matched route's `procedure` agrees with Design Intent; conflicting signals block until corrected. Then load the selected procedure and the union of matching `leaves`, deduplicating paths.
5. Execute the selected procedure after its required context is loaded. It discloses stage-specific role instructions and references when needed. Never load the full specialist catalog by default.

`method-router.json` is routing data, not method authority. Its `coreAuthorities` is the universal set shared by every lane. Repository ADR/authority-map paths are provenance metadata only; installed runs do not depend on repository docs. Host adapters use this loading contract, not a second loading graph.

## Required references

- `invocation.md`
- `design-intent-contract.json`
- `references/design-intent.md`
- `runtime-contract.md`
- `method-router.json`
- `references/context.md`
- `references/runtime-integrity.md`
- Conditional Studio procedure: `workflow.yaml`
- Conditional Review procedure: `references/review/polish.md`
- Conditional Document procedure: `references/document/document.md`

The first seven entries plus this index form the universal hot path. Lane procedures and methods are conditional; naming their paths does not load them.

## Lanes

| Lane / action | Trigger | Branch authority |
|---|---|---|
| **Studio** | create, extend or overhaul an interactive surface | selected `workflow.yaml`; stage-matched direction/build/overhaul leaves |
| **Review** | audit/polish while preserving an interactive visual world | selected `references/review/polish.md`; matched read-only review lenses |
| **Document** | quote, invoice, SOW, proposal, report, brief, print/PDF or other paginated artifact | selected `references/document/document.md`; hierarchy/specificity and its page-evaluation lenses |
| **Design system** | codify an accepted system | accepted lane's codification authority |
| **Meta** | improve Design Studio | routed `references/meta.md` |

Design Intent owns Studio/Review/Document disambiguation. Meta maintenance uses the existing `meta`/`method-intake` routes directly; codification consumes an accepted lane result, not a new intent. An interactive report remains Studio/Review even if it can export PDF. A narrow component/CSS correction does not require Studio.

## Studio

For a validated Studio intent, execute `workflow.yaml` end to end. It owns planning, precommitted unattended assignment, source-blind direction, source-aware building, mechanical evidence, blind evaluation, immutable iteration and final-tree acceptance before codification. Its specialist leaves load by current stage, not all at activation. The staged `extend` limitation is recorded in `references/design-intent.md`.

## Document

For a validated Document intent, execute `references/document/document.md` without loading the Studio workflow. It owns physical page-system direction, complete ordered rendered-page evaluation, pagination/table/furniture/print lenses and accepted `document-visual-contract.json` publication. Load those lenses at page evaluation, not for an interactive request.

Design Studio owns visual page-system intent and rendered-page judgement. It does not own transcript interpretation, business voice, accounting truth, binding commercial/legal terms or the renderer/generator.

## Review

Review does not run the Studio create loop or load its workflow. Execute the selected `references/review/polish.md`, then add only matching lenses. Reviewers report evidence first; implementation receives one bounded fix plan. Missing rendered evidence is `unverified`, not a clean verdict.

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
