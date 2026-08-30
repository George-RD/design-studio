# Design Studio roadmap

This file maps Design Studio's current product state and frontier. GitHub Issues are authoritative for executable specs, tickets, blockers, and completion.

## Current product state

Design Studio v1.7 is a portable design-engineering Agent Skill with one curated method kernel and one supported runtime seam.

- `skills/design-studio/` is the canonical product; standard Agent Skills installation is the canonical distribution path.
- Studio, Review, and Document are first-class lanes over the same source-boundary, evidence, and acceptance model.
- Deterministic helpers remain implementation details behind `skills/design-studio/runtime-contract.md`.
- Claude Code files are an optional thin adapter; a standalone public CLI remains deferred.
- Growth Arsenal remains an independent skill that composes through neutral artifacts.
- Historical benchmark and capability harnesses remain repository evidence, not installed runtime.

The architecture is governed by [ADR 0002](docs/decisions/0002-owned-method-kernel.md), [ADR 0003](docs/decisions/0003-claude-adapter-and-deferred-cli.md), and [ADR 0004](docs/decisions/0004-installer-compatibility-proof.md).

## Current frontier

The bounded v1.7 contraction is governed by [#74](https://github.com/George-RD/design-studio/issues/74). [#75](https://github.com/George-RD/design-studio/issues/75) and [#76](https://github.com/George-RD/design-studio/issues/76) remain linked implementation context, while [#77](https://github.com/George-RD/design-studio/issues/77) remains linked release context. The remaining executable release closure is tracked by [#78](https://github.com/George-RD/design-studio/issues/78). This map does not restate those issue checklists or determine their completion.

Prepared release evidence remains in [`docs/releases/v1.7.0.md`](docs/releases/v1.7.0.md) under the acceptance rules recorded there and in the governing issues.

## Maintenance frontier

After release closure, product work is maintenance- and evidence-driven. Promote architecture or method work only when a supported workflow has a concrete failure class, repeated evidence shows avoidable rework or weak decisions, or a meaningful ecosystem/upstream change can affect a supported contract. Every promoted change needs a bounded acceptance test before implementation.

External method intake remains selective and provenance-backed. The feedback-to-eval loop turns recurring dogfood failures into explicit criteria before they justify kernel changes. **Historical research and capability maintenance** remains evidence, not an executable roadmap: the [Milestone 0 ownership inventory](benchmarks/milestone-0/OWNERSHIP_INVENTORY.md), benchmark fixtures, comparison harnesses, and migration records stay available, while fixed-brief comparison is optional research, not a release gate.

See GitHub Issues for the current queue and `docs/agents/work-selection.md` for selection rules.
