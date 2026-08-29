# Mechanical quality gate

## Purpose

Own deterministic source and browser-computed facts before blind visual judgement and after finish corrections. Mechanical evidence can block craft/functionality but never choose a visual direction or assign aesthetic quality.

## Triggers

Load for `mechanical-preflight`, post-fix confirmation, finish confirmation, or Review when source/browser-computed facts are required.

## Required context

The host supplies current source facts and zero or more browser passes from the actual target. A completed source pass records title/language, heading validity, motion/reduced-motion source handling, and explicit semantic/name/alt/landmark/focus/placeholder/debug failures. A browser pass records requested/actual viewport, overflow measurements, reduced-motion verification, and explicit contrast/clipping/keyboard/focus/touch/resource/console failures.

## Outputs and handoff

Run from the installed skill root:

```text
node runtime/mechanical/index.mjs <input-json> <mechanical-findings-json>
```

The Node-standard-library helper writes the canonical current `mechanical-findings.json`. Hand that snapshot to Evaluator/Review and later acceptance. External detector availability must not change the supported rule set or result semantics.

## Authority boundary

This gate owns objective evidence: document metadata/semantics, accessible names, focus visibility, reduced-motion coverage, viewport match, horizontal overflow, measured contrast/clipping, keyboard reachability, touch targets, resource failures and fatal console errors. Visual hierarchy, generic-template feel, design-system quality and aesthetic judgement belong to routed review/evaluation leaves.

## Failure behavior

An unavailable source/browser pass is `completed: false` with an exact reason, never an empty clean result. Missing a required Studio viewport prevents visual winner selection; Review returns `visual_status: unverified`. A deterministic helper failure is recorded rather than replaced with an environment-dependent alternate runtime.

## Evaluation hooks

Every invocation is a complete current snapshot. Stable finding identity derives from rule, target, normalized location and relevant value. Current findings are `open` or `waived`; previous findings absent now become `not-reproduced` comparison evidence. A waiver matches only the exact rule/target/location/value and names current authority plus reason. Open primary findings cap affected Craft/Functionality as defined by `workflow.yaml`.

## Source provenance

Adopted local method slice: `pbakaus/impeccable` at revision `63b04e2530f5c7b41ea83c133daab24f34912456`, Apache-2.0. Design Studio adapts the repeatable technical-check and explicit finding/severity model only. The local helper, evidence schema, signatures, waiver semantics and rule set are Design Studio implementations; no upstream CLI, command taxonomy, prompt library or source file is required or vendored.
