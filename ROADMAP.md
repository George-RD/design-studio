# Design Studio roadmap

Design Studio's executable roadmap lives in GitHub Issues. This file is intentionally a **map**, not a second task tracker.

## Current product state

Design Studio v1.7 is a portable design-engineering Agent Skill with one curated local method kernel and one supported internal runtime seam.

- `skills/design-studio/` is the canonical product and standard Agent Skills / `npx skills` installation is the canonical distribution path.
- Studio, Review and Document are first-class lanes over the same source-boundary, evidence and acceptance model.
- Deterministic helpers remain implementation details behind `skills/design-studio/runtime-contract.md`.
- Claude Code commands/plugin files are an optional thin adapter; a standalone public CLI remains deferred.
- Growth Arsenal remains an independent offer/copy/business skill and composes through neutral artifacts rather than duplicated methods.
- Historical benchmark and capability harnesses remain repository evidence/research, not installed product runtime.

The method/runtime architecture is governed by [ADR 0002: Design Studio owns its method kernel](docs/decisions/0002-owned-method-kernel.md). The adapter/CLI boundary is governed by [ADR 0003: Keep Claude Code as an adapter and defer the public CLI](docs/decisions/0003-claude-adapter-and-deferred-cli.md). Installer compatibility semantics are governed by [ADR 0004](docs/decisions/0004-installer-compatibility-proof.md).

## v1.7 contraction and release closure

[#74 — Harden the post-roadmap product boundary for v1.7](https://github.com/George-RD/design-studio/issues/74) is the governing spec for this bounded contraction.

- [#75 — runtime-seam contraction](https://github.com/George-RD/design-studio/issues/75) — merged; routed methods depend on stable runtime operations rather than concrete helper paths.
- [#76 — public Agent Skills installation proof](https://github.com/George-RD/design-studio/issues/76) — merged; pinned reproducible installation remains blocking while latest-installer drift is advisory.
- [#77 — v1.7 versioning, metadata and public positioning](https://github.com/George-RD/design-studio/issues/77) — repository-owned version authority, README/product positioning and release-candidate evidence are merged. External repository description/topics and final release publication remain part of release closure.
- [#78 — close v1.7 with release proof and maintenance mode](https://github.com/George-RD/design-studio/issues/78) — current release-closure issue. It owns final exact-head verification, the `v1.7.0` tag/GitHub Release, repository metadata verification and closure of the parent sequence.

The prepared release evidence is in [`docs/releases/v1.7.0.md`](docs/releases/v1.7.0.md). It must remain **Prepared**, not Accepted, until #78's publication and exact-head gates are complete.

## Maintenance frontier

After #78 closes, normal product work is maintenance/evidence-driven intake rather than another broad architecture milestone.

New architecture or method work is promoted to the product roadmap only when at least one trigger exists:

- a **concrete failure class** in a supported workflow;
- **repeated evidence** that the current method/runtime produces avoidable rework, weak decisions or recovery failures;
- a **meaningful ecosystem/upstream change** that can affect a supported install, runtime or method contract.

Every promoted change also needs a **bounded acceptance test** before implementation. A new source, method, helper, adapter or public interface is not justified by novelty or convenience alone. ADR 0002 and ADR 0003 revisit triggers remain the architecture-level guardrails.

External method intake stays selective and provenance-backed. Useful changes from Impeccable, Emil Kowalski's skills or other sources are evaluated against a named failure/capability gap and adopted only when the smallest coherent local intervention has evidence.

**Historical research and capability maintenance** remains explicitly separate from normal product roadmap work. Benchmark fixtures, source-blind comparison harnesses, browser/capability reliability work and old migration evidence may be maintained when needed, but they do not become product roadmap work unless a supported product contract is affected.

## Work selection

GitHub Issues are authoritative for completion, blockers and the next executable item.

1. Continue an existing open or draft implementation before starting competing work.
2. Otherwise select an explicitly ready, unblocked implementation issue.
3. If there is no ready issue, `/implement` must stop cleanly. Do not invent product work, reopen historical milestones or promote research maintenance without a bounded ticket.

Planning and implementation use the repository-owned skills under `.agents/skills/`: `to-spec`, `to-tickets`, `codebase-design`, `implement`, `tdd` and `code-review` as appropriate.

## Historical evidence

The pre-v1.7 migration map, v1.6 release record, frozen Milestone 0 fixtures, Impeccable boundary experiments, blind comparison transactions and Horaxon dogfood evidence remain available in repository history and their existing docs/benchmark locations. They are evidence, not an active execution graph.

The following Milestone 0 markers are retained only as frozen benchmark compatibility evidence. They are **not executable roadmap items**:

- [x] Inventory every Design Studio step, reference, schema and check. Evidence: `benchmarks/milestone-0/OWNERSHIP_INVENTORY.md`.
- [x] Identify workflows that only reproduce an Impeccable command and preserve their historical disposition.
- [ ] Run the same fixed briefs through: optional research comparison only, not a release gate.
- [ ] Confirm the smallest differentiated product: superseded by the owned-kernel product and v1.7 release proof.
