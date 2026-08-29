# Mechanical quality gate

## Purpose

Own deterministic source, browser and paginated-artifact facts before blind visual judgement and after corrections. Mechanical evidence can block Craft/Functionality but never choose a visual direction or assign aesthetic quality.

## Triggers

Load for `mechanical-preflight`, post-fix confirmation, finish confirmation, interactive Review, or the Document lane when current computed facts are required.

## Required context

The host supplies current source facts, zero or more browser passes and zero or more `pageArtifacts` passes.

Completed source evidence uses `pageTitle`, `language`, `headingOrderValid`, `primaryHeadingCount`, `motionPresent`, `reducedMotionHandled` and failure arrays `semanticControlFailures`, `accessibleNameFailures`, `altTextFailures`, `landmarkFailures`, `focusVisibilityFailures`, `placeholderLinkFailures`, `debugControlFailures`.

Completed browser evidence uses `requestedViewport`, `actualViewport`, `scrollWidth`, `clientWidth`, `motionPresent`, `reducedMotionVerified` and `contrastFailures`, `clippedContentFailures`, `keyboardFailures`, `focusFailures`, `touchTargetFailures`, `resourceFailures`, `fatalConsoleErrors`.

Completed page-artifact evidence uses `pageCount`, physical `pageSize` (`name`, `widthMm`, `heightMm`) and `printableAreaOverflowFailures`, `clippedContentFailures`, `furnitureFailures`, `printContrastFailures`. Each explicit failure carries `location`, `value` and human-readable `evidence`.

## Outputs and handoff

Invoke the stable runtime operation `mechanical_preflight` with the current evidence and applicable constraints. It writes the canonical current `mechanical-findings.json` defined by `runtime-contract.md`.

Hand that snapshot to Evaluator/Review/Document evaluation and later acceptance. External detector availability must not change the supported rule set or result semantics; renderer availability must not change those semantics either. Concrete helper language/path mapping belongs to the runtime implementation layer, not this method authority.

## Authority boundary

This gate owns objective evidence: source metadata/semantics, accessible names/focus/reduced motion, viewport/overflow/contrast/clipping/keyboard/touch/resource facts, and page-artifact geometry/printable-area/clipping/required-furniture/print-contrast facts.

Visual hierarchy, generic-template feel, page-break quality, table scanability, furniture composition, design-system quality and aesthetic judgement belong to routed visual evaluation methods. The helper does not launch a browser/renderer or decide whether A4 is aesthetically appropriate.

## Failure behavior

An unavailable source/browser/page-artifact pass is `completed: false` with an exact reason, never an empty clean result. Missing required interactive viewports prevents a Studio winner; missing complete rendered pages prevents a Document winner. Review returns visual status `unverified` when its rendered evidence is incomplete. A deterministic helper failure is recorded rather than replaced with an environment-dependent runtime.

## Evaluation hooks

Every invocation is a complete current snapshot. Stable finding identity derives from rule, target, normalized location and relevant value. Current findings are `open` or `waived`; previous findings absent now become `not-reproduced` comparison evidence. A waiver matches only exact rule/target/location/value and names current authority plus reason. Open primary findings cap affected Craft/Functionality under the active lane contract.

## Source provenance

Adopted local method slice: `pbakaus/impeccable` at revision `63b04e2530f5c7b41ea83c133daab24f34912456`, Apache-2.0. This is provenance only; the upstream project is not required at runtime.

Design Studio adapts the repeatable technical-check and explicit finding/severity model only. Page-artifact rules are local Design Studio extensions for #64. The local helper, evidence schema, signatures, waiver semantics and rule set are Design Studio implementations; no upstream CLI, prompt library or renderer source is vendored.
