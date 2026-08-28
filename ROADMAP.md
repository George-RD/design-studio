# Design Studio roadmap

Design Studio's executable roadmap lives in GitHub Issues. This file is intentionally a **map**, not a second task tracker.

## Direction

Design Studio is becoming a **portable Agent Skill with one owned method kernel and one supported runtime**.

The next phase prioritises simplification:

- standard Agent Skills / `npx skills` installation is the canonical distribution target;
- Claude Code plugin/commands are optional thin adapters, not a second product;
- a standalone CLI is deferred until a concrete need proves it adds value;
- deterministic product tooling sits behind one internal runtime seam;
- product runtime helpers are separated from benchmark/research harnesses;
- useful Impeccable and Emil Kowalski methods are selectively consolidated into one non-duplicated local authority and progressively disclosed leaves;
- Growth Arsenal remains an independent offer/copy/business skill and composes with Design Studio through neutral artifacts rather than duplicated methods;
- broad dogfood is evidence, not a mandatory roadmap phase. Use targeted comparisons only when they resolve a live method-intake uncertainty.

The governing architecture is [ADR 0002: Design Studio owns its method kernel](docs/decisions/0002-owned-method-kernel.md).

## Authoritative spec

- [#43 — Simplify Design Studio into a portable skill kernel](https://github.com/George-RD/design-studio/issues/43)

`#43` contains the user stories, implementation decisions, testing seams and scope boundaries for this roadmap.

## Execution graph

### Frontier

- [#44 — Inventory the portable product boundary and migration map](https://github.com/George-RD/design-studio/issues/44)

This is the first implementation ticket. It freezes the baseline and classifies the current surfaces, script families and method ownership before behavior changes.

### Parallel work after #44

- [#45 — Make the Agent Skill the canonical install and distribution surface](https://github.com/George-RD/design-studio/issues/45) — blocked by #44
- [#46 — Establish one stable internal runtime seam before script reorganisation](https://github.com/George-RD/design-studio/issues/46) — blocked by #44
- [#47 — Consolidate external design guidance into one method authority map](https://github.com/George-RD/design-studio/issues/47) — blocked by #44

### Runtime simplification

- [#49 — Separate shipped runtime helpers from benchmark and research tooling](https://github.com/George-RD/design-studio/issues/49) — blocked by #46
- [#50 — Normalize product runtime script families behind the shared seam](https://github.com/George-RD/design-studio/issues/50) — blocked by #46 and #49

### Method consolidation and modular composition

- [#51 — Route curated design methods through progressive-disclosure leaves](https://github.com/George-RD/design-studio/issues/51) — blocked by #46 and #47
- [#48 — Define a modular Design Studio ↔ Growth Arsenal composition contract](https://github.com/George-RD/design-studio/issues/48) — blocked by #47
- [Growth Arsenal #34 — Make Growth Arsenal a portable Agent Skill and compose cleanly with Design Studio](https://github.com/George-RD/growth-arsenal/issues/34) — can start with inventory; final composition is blocked by Design Studio #48

### Adapter contraction and release proof

- [#52 — Reduce Claude Code integration to a thin adapter and defer the standalone CLI](https://github.com/George-RD/design-studio/issues/52) — blocked by #45, #46, #50 and #51
- [#53 — Prove the portable v1.6 path and contract legacy surfaces](https://github.com/George-RD/design-studio/issues/53) — blocked by #45, #48, #50, #51 and #52

## Dependency sketch

```text
#44 inventory
 ├─> #45 canonical Agent Skill install ────────────────┐
 ├─> #46 runtime seam ─> #49 runtime/research split ─> #50 script normalisation ─┐
 │                    └───────────────────────────────> #51 method leaves ───────┤
 └─> #47 method authority ─> #51 method leaves ─────────────────────────────────┤
                         └─> #48 Growth Arsenal contract ─────────────────────────┤

#45 + #46 + #50 + #51 ─> #52 thin Claude adapter / CLI deferral ────────────────┤
#45 + #48 + #50 + #51 + #52 ─> #53 portable v1.6 proof                         │
                                                                                ▼
                                                                              v1.6
```

## Non-blocking maintenance

- [#42 — Harden the capability gate against timing and safe self-inspection flakes](https://github.com/George-RD/design-studio/issues/42) remains a separate reliability issue. #50 must decide whether any of that gate belongs to the shipped runtime; research-only reliability work should not silently expand the portable product.

## Planning and implementation discipline

Repo-owned Matt Pocock engineering skills are installed under `.agents/skills/`, pinned to source revision `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`.

Use:

1. `to-spec` for durable feature/spec synthesis;
2. `to-tickets` for dependency-aware tracer bullets;
3. `implement` with `tdd` at agreed seams for behavioral code changes;
4. `codebase-design` when the runtime interface/seam itself is being shaped;
5. `code-review` against both repository standards and the originating issue/spec.

GitHub Issues are authoritative for completion and blockers. Do not mirror issue checkboxes back into this file.

## Historical evidence

The earlier milestone roadmap, Impeccable boundary experiment, frozen fixtures, blind comparison transaction and Horaxon dogfood evidence remain in repository history and benchmark/research artifacts. ADR 0002 supersedes the required-Impeccable runtime direction.

Retain that evidence when useful, but do not run historical comparisons or continue dogfood solely to advance old roadmap checkboxes.