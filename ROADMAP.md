# Design Studio roadmap

Design Studio's executable roadmap lives in GitHub Issues. This file is intentionally a **map**, not a second task tracker.

## Direction

Design Studio is becoming a **portable Agent Skill with one curated method kernel and one supported runtime**.

The next phase prioritises simplification:

- standard Agent Skills / `npx skills` installation is the canonical distribution target;
- Claude Code plugin/commands are optional thin adapters, not a second product;
- a standalone CLI is deferred until a concrete need proves it adds value;
- deterministic product tooling sits behind one internal runtime seam;
- product runtime helpers are separated from benchmark/research harnesses;
- external **method intake** is evidence-gated: useful Impeccable and Emil Kowalski methods are selectively consolidated into one non-duplicated local authority and progressively disclosed leaves;
- Growth Arsenal remains an independent offer/copy/business skill and composes with Design Studio through neutral artifacts rather than duplicated methods;
- the **feedback-to-eval loop** remains a learning mechanism, but broad dogfood is evidence rather than a mandatory roadmap phase. Use targeted comparisons only when they resolve a live method-intake uncertainty.

The governing architecture is [ADR 0002: Design Studio owns its method kernel](docs/decisions/0002-owned-method-kernel.md).

## Authoritative spec

- [#43 — Simplify Design Studio into a portable skill kernel](https://github.com/George-RD/design-studio/issues/43)

`#43` contains the user stories, implementation decisions, testing seams and scope boundaries for this roadmap.

## Execution graph

### Baseline complete

- [#44 — Inventory the portable product boundary and migration map](https://github.com/George-RD/design-studio/issues/44) — baseline recorded in [`docs/migration-map.md`](docs/migration-map.md) and [`docs/migration-map.json`](docs/migration-map.json) against pre-change revision `492a874d0a7c935e51395d66f420608a997d9ed3`.
- [#45 — Make the Agent Skill the canonical install and distribution surface](https://github.com/George-RD/design-studio/issues/45) — canonical Agent Skill install surface merged and verified.
- [#46 — Establish one stable internal runtime seam before script reorganisation](https://github.com/George-RD/design-studio/issues/46) — stable runtime seam and follow-up review fixes merged and verified.
- [#47 — Consolidate external design guidance into one method authority map](https://github.com/George-RD/design-studio/issues/47) — concept ownership, provenance, intake dispositions, domain boundaries and routing are recorded in [`docs/method-authority-map.json`](docs/method-authority-map.json) and [`docs/method-authority-map.md`](docs/method-authority-map.md).
- [#48 — Define a modular Design Studio ↔ Growth Arsenal composition contract](https://github.com/George-RD/design-studio/issues/48) — neutral role-scoped artifact ownership, precedence/staleness rules and prompt-order-independent composition are defined in [`skills/design-studio/composition-contract.json`](skills/design-studio/composition-contract.json) and its installed reference.
- [#49 — Separate shipped runtime helpers from benchmark and research tooling](https://github.com/George-RD/design-studio/issues/49) — current distribution boundary, clean-install dependency checks and real Agent Skill package proof are recorded in [`docs/runtime-boundary.md`](docs/runtime-boundary.md) and [`runtime-surface.json`](runtime-surface.json).
- [#50 — Normalize product runtime script families behind the shared seam](https://github.com/George-RD/design-studio/issues/50) — the first shipped helper is the standard-library-only local mechanical runtime; historical browser/capability/benchmark families remain repository-only and the old environment-dependent detector branch is removed.
- [#51 — Route curated design methods through progressive-disclosure leaves](https://github.com/George-RD/design-studio/issues/51) — signal-based routing, bounded leaf contracts, seven provenance-backed local method adaptations and compatibility-stub retirement are implemented through [`skills/design-studio/method-router.json`](skills/design-studio/method-router.json).

The migration map classifies the pre-change product boundary. The method authority map resolves that inventory into the current one-authority-per-concept contract without making external repositories runtime dependencies. The runtime boundary records the current installed/adaptor/repository-only split without changing the frozen migration baseline.

### Next ready roadmap item

- [#52 — Reduce Claude Code integration to a thin adapter and defer the standalone CLI](https://github.com/George-RD/design-studio/issues/52) — dependencies #45, #50 and #51 are complete; composition #48 is complete, so adapter contraction is the next item in milestone order.

### Runtime simplification

- [#49 — Separate shipped runtime helpers from benchmark and research tooling](https://github.com/George-RD/design-studio/issues/49) — complete; runtime/research dependency boundary is enforced without moving historical tooling
- [#50 — Normalize product runtime script families behind the shared seam](https://github.com/George-RD/design-studio/issues/50) — complete; local mechanical evidence is behind the shared seam and research-only capability/browser runners remain outside the installed product

### Method consolidation and modular composition

- [#51 — Route curated design methods through progressive-disclosure leaves](https://github.com/George-RD/design-studio/issues/51) — complete; one signal router exposes bounded local authorities and adopted method slices without upstream runtime dependencies
- [#48 — Define a modular Design Studio ↔ Growth Arsenal composition contract](https://github.com/George-RD/design-studio/issues/48) — complete; role/scope/state and provenance identify product/copy/design authority without prompt-order or filename collisions
- [Growth Arsenal #34 — Make Growth Arsenal a portable Agent Skill and compose cleanly with Design Studio](https://github.com/George-RD/growth-arsenal/issues/34) — inventory/packaging work can continue; final composition adoption is unblocked by Design Studio #48 after this change merges

### Adapter contraction and release proof

- [#52 — Reduce Claude Code integration to a thin adapter and defer the standalone CLI](https://github.com/George-RD/design-studio/issues/52) — dependencies #45, #50 and #51 are complete; next in milestone order after #48
- [#53 — Prove the portable v1.6 path and contract legacy surfaces](https://github.com/George-RD/design-studio/issues/53) — blocked by #52; #48 is complete

## Dependency sketch

```text
#44 inventory
 ├─> #45 canonical Agent Skill install ─────────────────────────┐
 ├─> #46 runtime seam ─> #49 runtime/research split ─> #50 script normalisation ─┐
 │                    └───────────────────────────────> #51 method leaves ────────┤
 └─> #47 method authority ─> #51 method leaves ──────────────────────────────────┤
                         └─> #48 Growth Arsenal contract ─────────────────────────┤

#45 + #50 + #51 ─> #52 thin Claude adapter / CLI deferral ───────────────────────┤
#48 + #52 ─> #53 portable v1.6 proof                                             │
                                                                                  ▼
                                                                                v1.6
```

## Non-blocking maintenance

- [#42 — Harden the capability gate against timing and safe self-inspection flakes](https://github.com/George-RD/design-studio/issues/42) remains a separate repository-research reliability issue. #50 reviewed the overlap and did not promote its browser-launch, capability-gate or timing machinery into the installed runtime.

## Planning and implementation discipline

Repo-owned Matt Pocock engineering skills are installed under `.agents/skills/`, based on reviewed source revision `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`.

Use:

1. `to-spec` for durable feature/spec synthesis;
2. `to-tickets` for dependency-aware tracer bullets;
3. `implement` with `tdd` at agreed seams for behavioral code changes;
4. `codebase-design` when the runtime interface/seam itself is being shaped;
5. `code-review` against both repository standards and the originating issue/spec.

GitHub Issues are authoritative for completion and blockers. Do not mirror active issue checkboxes back into this file.

## Historical evidence

The earlier milestone roadmap, Impeccable boundary experiment, frozen fixtures, blind comparison transaction and Horaxon dogfood evidence remain in repository history and benchmark/research artifacts. ADR 0002 supersedes the required-Impeccable runtime direction.

The following archived Milestone 0 markers are retained only as historical evidence contracts for the existing benchmark tests. **They are not executable roadmap items and must not be used to select work:**

- [x] Inventory every Design Studio step, reference, schema and check. Evidence: `benchmarks/milestone-0/OWNERSHIP_INVENTORY.md`.
- [x] Identify workflows that only reproduce an Impeccable command and record the old delegate/delete disposition.
- [x] Controlled source-blind agent, browser and evidence capability gates.
- [ ] Run the same fixed briefs through: retained as an **optional research comparison, not a release gate**.
- [ ] Confirm the smallest differentiated product: superseded by #43's portable-kernel outcome and #53's release proof.

Retain that evidence when useful, but do not run historical comparisons or continue dogfood solely to advance old roadmap checkboxes.
