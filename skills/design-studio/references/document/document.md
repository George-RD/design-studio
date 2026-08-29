# Paginated document lane

## Purpose

Own visual direction, page-system design, source-blind rendered-page evaluation and reusable visual codification for professional paginated artifacts. The lane is renderer-neutral: it describes visual intent and constraints that HTML-to-PDF, DOCX/PDF, native PDF or later renderers may implement without making any renderer authoritative.

## Triggers

Load when `task` is `document-create` or `document-review` and `surface` is `paginated-artifact`. Typical signals are quote, invoice, SOW, proposal, report, executive brief, print deliverable or PDF intended for page-based reading.

Do not route an interactive dashboard/report here merely because it can export PDF. Page/print intent, pagination and repeated page furniture are the differentiators.

## Required context

- confirmed document purpose, audience and structured content;
- existing `DESIGN.md`, tokens or brand truth when available;
- explicit page size, otherwise A4 (`210 × 297 mm`); Letter (`215.9 × 279.4 mm`) is the next standard preset; custom sizes require physical dimensions;
- required metadata/furniture such as document ID, date, version, status, confidentiality, page number, signatures or payment/acceptance zones;
- print/grayscale constraints and any existing accepted `document-visual-contract.json`;
- roots/capability evidence and an optional host-supplied `page_artifact_rendering` capability.

Structured content is evidence, not permission to reinterpret it. Said/agreed/proposed status, business voice, accounting truth and binding commercial/legal terms remain outside this lane.

## Procedure

### 1. Root and probe

Reuse `resolve_roots`, `probe_capabilities`, `prepare_direction_assignment`, `mechanical_preflight`, acceptance and event semantics from `runtime-contract.md`. Generic required capabilities remain `file_io`, `shell` and `isolated_subagents`.

For page work, probe `page_artifact_rendering` separately. It may be an existing rendered PDF/page set or a host/downstream renderer that can produce a complete ordered page artifact plus page images. Record renderer identity only in Orchestrator/Builder operational evidence; never include it in Visual Director or Evaluator context.

Use the existing evaluation-plan vocabulary:

- `full`: complete rendered-page evidence can be produced and inspected;
- `build-once-unselected`: a create request can produce source/artifact work but complete rendered-page judgement is unavailable; preserve one build and halt without a visual winner;
- `mechanical-review`: a review may return deterministic evidence with `visual_status: unverified` when page images cannot be inspected.

### 2. Define the page brief

Preserve structured content and product truth. Define physical page size/printable area/margin intent; column/grid geometry; typography roles; colour/ink/paper and grayscale behavior; spacing/rhythm; required furniture; table/totals/note/callout/signature/payment/figure recipes; pagination priorities; and representative QA cases.

A4 is default, not a universal aesthetic. Letter/custom variants preserve the same semantic system while adapting geometry.

### 3. Direct without source

Use `agents/design-agent.md` in paginated-document mode. Visual Director receives structured role/content summaries, existing visual truth and rendered pages when reviewing, but no document source, renderer metadata or implementation rationale.

For unattended create work, commit candidate assignment before direction generation and keep it hidden. Produce three materially different page-system directions unless an exact direction is pinned. Differences should include at least three of grid, typography, furniture, density/rhythm, table grammar and material/ink logic.

### 4. Build and render

Builder may see source and the selected source-free page contract. It implements in the downstream/native document substrate, then asks the host renderer to produce the immutable current artifact. Renderer-specific snippets/adapters may exist as implementation evidence but never enter the accepted visual contract.

Rendered handoff contains one ordered artifact identity; verified page count/physical sizes; a complete ordered page-image set; current `page-artifact` mechanical facts; and no renderer identity/source for Evaluator.

### 5. Evaluate complete pages

Use `agents/evaluator.md` `## Document contract`. Inspect the whole ordered artifact, then material pages/zones at closer scale.

Reuse only the medium-agnostic methods `references/review/hierarchy.md` and `references/review/slop.md`, then load all four Document lenses: `pagination.md`, `tables.md`, `furniture.md`, `print.md`.

Do not load the interaction/motion review method for a static page artifact. Accessibility checks are limited to applicable legibility/contrast and available semantic document evidence; do not invent browser-only focus, target or motion findings.

Evaluator returns evidence/scores only. Orchestrator applies REFINE/PIVOT/SHIP/HALT ownership. A missing page, unverified physical size or incomplete page-image set makes the pass `unevaluated`.

### 6. Accept and codify

A visual winner requires complete rendered-page evidence, a current mechanical snapshot, no unresolved blocking page defect and an acceptance receipt naming the immutable artifact/tree used.

After acceptance, Visual Director/Orchestrator assemble the proposed renderer-neutral contract from accepted evidence. Publish it through the stable runtime operation `publish_document_visual_contract`, supplying the accepted proposed contract and target output path. The operation validates the required v1 shape and writes the actual downstream artifact. A validation failure blocks publication.

`document-visual-contract.schema.json` remains the declarative schema authority. The runtime implementation enforces its required operational subset without synthesizing design values; concrete helper language/path mapping belongs to the runtime implementation layer, not this procedure authority.

The contract contains, where applicable: page sizes/printable area/margins/grid; typography roles/scale/leading/tracking/fallbacks; colour/ink/paper and grayscale constraints; spacing/rhythm; title/metadata/header/footer/page-number/status/version/confidentiality furniture; reusable table/totals/scope-row/note/callout/divider/signature/payment/figure recipes; pagination rules; intentional variants; and QA criteria/representative rendered fixtures.

Optional implementation adapters may sit beside the contract but are subordinate examples. A downstream document-generation skill should be able to load the JSON plus referenced assets/tokens and reproduce the approved aesthetic without rerunning creative direction.

## Outputs and handoff

Creation/review produces durable page evidence, lens findings and acceptance result. Accepted work additionally publishes `harness-output/design-system/document-visual-contract.json`. Handoff is that contract plus approved structured content and referenced assets/tokens, not internal critique or renderer implementation.

## Authority boundary

Design Studio owns visual page-system intent, page composition, rendered-page visual evaluation and the Document Visual Contract. It does not own transcript interpretation, business voice, whether terms were agreed, accounting records, legal/tax truth, or the document renderer/generator. Adjacent skills may supply confirmed structured content and consume the accepted visual contract.

## Failure behavior

- No complete rendered pages: creation preserves at most one build and halts unselected; review returns `visual_status: unverified`.
- Incomplete page set, unknown page order or unverifiable physical size: Evaluator writes `unevaluated` with exact gap.
- Renderer/source leak into source-blind context: record isolation breach and restart the affected pass with clean context.
- Mechanical page evidence unavailable: record an incomplete `page-artifact` pass; never convert absence to clean.
- Contract validation/publication fails: do not publish downstream visual authority.

## Evaluation hooks

For each evaluated artifact record page count/size, per-page evidence, affected page/zone, lens, severity, confidence, finding status and score impact. Repository dogfood evidence for issue #64 is validation evidence only and is not an installed runtime dependency.
