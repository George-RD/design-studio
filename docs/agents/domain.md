# Domain Docs

How engineering skills should consume this repository's domain documentation.

## Before exploring

- Read `CONTEXT.md` if it exists.
- Read the relevant accepted or superseding records in `docs/decisions/` before proposing architecture changes.
- Use [`ROADMAP.md`](../../ROADMAP.md) according to its authority statement; represent durable planned work as GitHub issues.

If `CONTEXT.md` does not exist, proceed silently. Create or extend domain vocabulary only when real terminology needs to be made durable.

## Layout

This repository is single-context. System decisions live under `docs/decisions/`.

## Vocabulary

Use the project's established terms such as **Design Intent**, **owned method kernel**, **source-blind direction**, **source-aware Builder**, **source-blind evaluation**, **method intake**, **runtime seam**, and **adapter** consistently. Do not introduce synonyms when an existing term is adequate.

## ADR conflicts

If planned work contradicts an accepted decision, surface the conflict and supersede the decision deliberately rather than silently drifting documentation or implementation.
