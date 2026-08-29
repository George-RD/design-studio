# Installed runtime helpers

This directory contains deterministic helpers that ship with the Design Studio Agent Skill. `../runtime-contract.md` remains the stable interface; these files are internal implementations behind that seam.

## Runtime policy

- Helpers use the Node standard library only. No install-time package dependency is required; CI validates the runtime contract with Node 24 on Linux, macOS and Windows.
- Helpers use Node path, file and process APIs rather than shell-specific command syntax.
- The host supplies file access, shell, browser automation and optional page rendering. A helper may validate/normalize facts from those capabilities; it does not own a host, renderer or workflow policy.
- Repository-only research/capability tooling stays outside the installed runtime.

## Mechanical preflight

`mechanical/index.mjs` implements `mechanical_preflight`. It accepts current source/browser/page-artifact evidence, evaluates the supported deterministic rules, applies exact authority-backed waivers and writes one normalized current snapshot.

Run from the installed skill root:

```text
node runtime/mechanical/index.mjs input.json mechanical-findings.json
```

With no paths it reads JSON from standard input and writes JSON to standard output. Exit `0` means a valid snapshot, exit `2` means invalid supplied evidence/JSON, and exit `1` is reserved for unexpected runtime errors.

### Evidence boundary

The helper deliberately does not launch Chrome, launch a document renderer, install a detector, discover an application, paginate source or infer visual quality. The host gathers facts from the actual current target. Missing evidence is an incomplete pass with exact reason, never a clean pass. Visual judgement remains with source-blind Evaluator.

For a completed source pass provide page title/language, heading-order/primary-heading facts, motion/reduced-motion facts, and explicit failures for semantic controls, names, alt text, landmarks, focus, placeholder links and debug controls.

For each completed browser pass provide requested/actual viewport, scroll/client width, motion/reduced-motion facts, and explicit failures for contrast, clipping, keyboard, focus, touch size, resources and fatal console errors.

For each completed `pageArtifacts` pass provide:

- `target`, `completed: true`, positive `pageCount`;
- `pageSize` with non-empty `name` and positive numeric `widthMm`/`heightMm`;
- failure arrays `printableAreaOverflowFailures`, `clippedContentFailures`, `furnitureFailures`, `printContrastFailures`.

An incomplete page-artifact pass needs only target, `completed:false` and exact `reason`. Physical page facts may come from PDF/document metadata or another host capability; the helper does not care which renderer produced them.

Each explicit failure carries `location`, `value` and human-readable `evidence`. Stable finding identity derives from rule ID, target, normalized location and relevant value; wording/timestamps do not alter the signature.

A waiver exactly matches that identity and names `authority` plus `reason`. A previous snapshot is comparison evidence only: findings absent now are `notReproduced`, not carried into the current open set.

## Migration boundary

The page-artifact extension is additive to schema version 1: existing source/browser inputs and snapshot IDs remain unchanged when no page-artifact passes are supplied. It does not turn a renderer into installed runtime or alter the frozen historical benchmark harness.

Issue #42 remains a separate reliability question for repository research gating. Future helpers should be added only when a supported runtime operation needs bounded deterministic behavior cheaper/clearer to own here than in every host adapter.
