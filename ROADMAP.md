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

The current product boundary is governed by [ADR 0002](docs/decisions/0002-owned-method-kernel.md), [ADR 0003](docs/decisions/0003-claude-adapter-and-deferred-cli.md), and [ADR 0004](docs/decisions/0004-installer-compatibility-proof.md).

## Current executable frontier

The bounded v1.7 contraction is governed by [#74](https://github.com/George-RD/design-studio/issues/74). [#77](https://github.com/George-RD/design-studio/issues/77) owns the remaining repository metadata and publication work. [#78](https://github.com/George-RD/design-studio/issues/78) closes the release after #77, exact-head validation, and the `v1.7.0` tag/GitHub Release are complete.

Prepared release evidence remains in [`docs/releases/v1.7.0.md`](docs/releases/v1.7.0.md). GitHub issue state, labels, and blockers determine executable work; this map does not restate their checklists.

## Promoted next phase: intent-aware design composition

A concrete supported-workflow failure class has been promoted under [#88](https://github.com/George-RD/design-studio/issues/88): ad hoc intent selection and manual Design Studio plus Growth Arsenal stacking cause repeated discovery, inconsistent ordering, excess activated context, and unclear design-system effects.

[ADR 0005](docs/decisions/0005-intent-router-and-website-composition.md) records the next-phase direction:

- one Design Intent seam classifies create, extend, polish, overhaul, document-create, and document-review before lane procedures load;
- Design Studio remains the single design front door while Growth Arsenal stays an independent optional owner of offer, positioning, and commercial copy;
- shared audience evidence and approved role-scoped artifacts replace prompt-order composition;
- accepted work declares whether it establishes, preserves, extends, replaces, extracts, or does not affect durable visual authority;
- branch-specific procedures and specialist methods load only after intent routing;
- the settled instruction system receives a writing-for-agents pruning pass before release proof.

GitHub issues under #88 are the implementation graph. All product-behaviour work in that graph is blocked by [#78](https://github.com/George-RD/design-studio/issues/78), so v1.7 release closure remains first. The bounded target is v1.8.0 with exact-head workflow, composition, design-system, install, and release evidence.

## Evidence-driven frontier

After the active bounded release graph closes, product work returns to maintenance- and evidence-driven intake. Promote architecture or method work only when a supported workflow has a concrete failure class, repeated evidence shows avoidable rework or weak decisions, or a meaningful ecosystem/upstream change can affect a supported contract. Every promoted change needs a bounded acceptance test before implementation.

External method intake remains selective and provenance-backed. The feedback-to-eval loop turns recurring dogfood failures into explicit criteria before they justify kernel changes. **Historical research and capability maintenance** remains evidence, not an executable roadmap: the [Milestone 0 ownership inventory](benchmarks/milestone-0/OWNERSHIP_INVENTORY.md), benchmark fixtures, comparison harnesses, and migration records stay available, while fixed-brief comparison is optional research, not a release gate.

See GitHub Issues for the current queue and `docs/agents/work-selection.md` for selection rules.
