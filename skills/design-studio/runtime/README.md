# Installed runtime helpers

This directory contains deterministic helpers that ship with the Design Studio Agent Skill. `../runtime-contract.md` remains the stable interface; these files are internal implementations behind that seam.

## Runtime policy

- Helpers use the Node standard library only. No install-time package dependency is required; CI validates the runtime contract with Node 24.
- Helpers use Node path/file/process APIs rather than shell-specific syntax.
- The host supplies file access, shell, browser automation and optional page rendering. Helpers validate/normalize supplied evidence; they do not own a host, renderer or workflow policy.
- Repository-only research/capability tooling stays outside installed runtime.

## Mechanical preflight

`mechanical/index.mjs` implements `mechanical_preflight`. It accepts current source/browser/page-artifact evidence, evaluates deterministic rules, applies exact authority-backed waivers and writes one normalized current snapshot.

```text
node runtime/mechanical/index.mjs input.json mechanical-findings.json
```

With no paths it reads JSON from standard input and writes JSON to standard output. Exit `0` means valid snapshot, exit `2` invalid supplied evidence/JSON, exit `1` unexpected runtime error.

The helper never launches Chrome/a document renderer, installs a detector, discovers an application, paginates source or infers visual quality. Missing evidence is an incomplete pass with exact reason.

For completed `pageArtifacts` provide target, `completed:true`, positive `pageCount`, physical `pageSize {name,widthMm,heightMm}`, and failure arrays `printableAreaOverflowFailures`, `clippedContentFailures`, `furnitureFailures`, `printContrastFailures`. An incomplete page-artifact pass needs target, `completed:false` and exact reason.

Stable finding identity derives from rule ID, target, normalized location and relevant value. Exact authority-backed waivers may suppress current findings; absent previous findings become `notReproduced`, not current open state.

## Document Visual Contract publication

`document-contract/index.mjs` implements `publish_document_visual_contract`. It validates an already accepted proposed v1 contract and writes the actual downstream JSON artifact, creating parent directories when required.

```text
node runtime/document-contract/index.mjs proposed-contract.json harness-output/design-system/document-visual-contract.json
```

The helper requires `surface: paginated-artifact`, `rendererNeutral: true`, a defined default page size, typography/colour/spacing/furniture/component objects, pagination rules and QA arrays. It does not generate design values, inspect business content or embed renderer code. Exit `0` means the artifact was published; exit `2` means invalid contract/JSON.

## Migration boundary

The page-artifact extension is additive to mechanical schema version 1: existing source/browser snapshots remain unchanged when no page passes are supplied. The publication helper is a separate operation and does not turn a renderer into installed runtime or alter the frozen historical benchmark harness.

Issue #42 remains separate repository-research reliability work. Future helpers should exist only for bounded deterministic behavior required by supported runtime operations.
