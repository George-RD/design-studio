# Paginated document lane

## Purpose

Own visual direction, page-system design, source-blind rendered-page evaluation and reusable visual codification for professional paginated artifacts. The lane is renderer-neutral: it describes visual intent and constraints that HTML→PDF, DOCX/PDF, native PDF or later renderers may implement without making any renderer authoritative.

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

Preserve structured content and product truth. Define:

- physical page size, printable area and margin intent;
- column/grid geometry and alignment anchors;
- typography roles, scale, leading, tracking and fallback intent;
- colour/ink/paper roles, grayscale behavior and print constraints;
- spacing/rhythm tokens;
- document furniture and variant-specific composition requirements;
- table, totals, notes, callout, figure/caption/source-note, acceptance/signature/payment recipes;
- pagination priorities and representative QA cases.

A4 is default, not a universal aesthetic. Letter/custom variants preserve the same semantic system while adapting geometry.

### 3. Direct without source

Use `agents/design-agent.md` in its paginated-document mode. Visual Director receives structured role/content summaries, existing visual truth and rendered pages when reviewing, but no source or renderer metadata.

For unattended create work, commit the candidate assignment before direction generation and keep it hidden. Produce three materially different page-system directions unless an exact direction is pinned. Differences should include at least three of grid, typography, furniture, density/rhythm, table grammar and material/ink logic.

### 4. Build and render

Builder may see source and the selected source-free page contract. It implements in the downstream/native document substrate, then asks the host renderer to produce the immutable current artifact. Renderer-specific snippets or adapters may exist as implementation evidence but never enter the accepted visual contract.

The rendered handoff contains:

- one ordered artifact identity;
- verified page count and physical page sizes;
- a complete ordered page-image set;
- current `page-artifact` mechanical facts;
- no renderer identity or source for Evaluator.

### 5. Evaluate complete pages

Use `agents/evaluator.md` `## Document contract`. Always inspect the whole ordered artifact, then material pages/zones at closer scale.

Reuse only the medium-agnostic methods:

- `references/review/hierarchy.md` for hierarchy, rhythm, density and composition;
- `references/review/slop.md` for generic/synthetic pattern detection and subtraction.

Then load all four document lenses:

- `pagination.md`;
- `tables.md`;
- `furniture.md`;
- `print.md`.

Do not load `references/review/interaction.md` for a static page artifact. Accessibility checks are limited to applicable legibility/contrast and available semantic document evidence; do not invent browser-only focus, target or motion findings.

Evaluator returns evidence and scores only. Orchestrator applies the same REFINE/PIVOT/SHIP/HALT ownership as Studio. A missing page, unverified physical size or incomplete page-image set makes the pass `unevaluated`.

### 6. Accept and codify

A visual winner requires complete rendered-page evidence, a current mechanical snapshot, no unresolved blocking page defect and an explicit acceptance receipt naming the immutable artifact/tree used.

After acceptance, emit:

`harness-output/design-system/document-visual-contract.json`

Validate its shape against `document-visual-contract.schema.json`. The contract is the downstream visual authority and must contain, where applicable:

- page sizes, printable area, margins, grid and column geometry;
- typography roles/scale/leading/tracking/fallbacks;
- colour/ink/paper roles and grayscale/print constraints;
- spacing/rhythm tokens;
- title/metadata/header/footer/page-number/status/version/confidentiality furniture;
- reusable table, totals, scope-row, note/callout, divider, signature/payment and figure/caption/source-note recipes;
- pagination rules for keep-together, orphan/widow behavior, repeated headings, continuation state and break priorities;
- intentional document variants;
- QA criteria and representative rendered fixtures.

Optional implementation adapters may sit beside the contract, but they are subordinate examples. A downstream document-generation skill should be able to load the JSON plus referenced visual assets/tokens and reproduce the approved aesthetic without rerunning creative direction.

## Outputs and handoff

Creation/review produces durable page evidence, lens findings and an acceptance result. Accepted work additionally produces the renderer-neutral Document Visual Contract above. Handoff to document-generation skills is the contract plus approved structured content and referenced assets/tokens, not Design Studio's internal critique or renderer implementation.

## Authority boundary

Design Studio owns visual page-system intent, page composition, rendered-page visual evaluation and the Document Visual Contract. It does not own transcript interpretation, business voice, whether terms were agreed, accounting records, legal/tax truth, or the document renderer/generator. Adjacent skills may supply confirmed structured content and may consume the accepted visual contract.

## Failure behavior

- No complete rendered pages: creation preserves at most one build and halts unselected; review returns `visual_status: unverified`.
- Incomplete page set, unknown page order or unverifiable physical size: Evaluator writes `unevaluated` with the exact gap.
- Renderer/source leak into source-blind context: record an isolation breach and restart the affected Visual Director/Evaluator pass with clean context.
- Mechanical page evidence unavailable: record an incomplete `page-artifact` pass; never convert absence to clean.
- Contract cannot validate: do not publish it downstream as accepted authority.

## Evaluation hooks

For each evaluated artifact record page count/size, per-page evidence, affected page/zone, lens, severity, confidence, finding status and score impact. The Horaxon Foundation Sprint fixture under `test/fixtures/document-artifact/horaxon-foundation-sprint/` is the first end-to-end contract case from `George-RD/horaxon-web#105`.
