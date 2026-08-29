# Runtime distribution boundary

**Status:** Authoritative for issue #49  
**Governing spec:** [#43](https://github.com/George-RD/design-studio/issues/43)  
**Governing decision:** [ADR 0002](decisions/0002-owned-method-kernel.md)  
**Machine-readable boundary:** [`runtime-surface.json`](../runtime-surface.json)

Design Studio has one canonical installed product: the Agent Skill under `skills/design-studio/`. The stable deterministic interface is [`runtime-contract.md`](../skills/design-studio/runtime-contract.md). A supported run may use only behavior carried by that installed skill plus capabilities supplied by the host.

## Installed runtime

`skills/design-studio/**` is the installed runtime. It contains the skill router, workflow, source-blind roles, references, eval contract and stable runtime contract.

Any deterministic executable helper that a supported run later needs must ship under `skills/design-studio/runtime/` and implement the operations defined by the stable runtime contract. There are no such helper files today. The migration inventory found no current repository script family that should be promoted wholesale into the product runtime.

## Optional adapters

The root `.claude-plugin/`, `agents/` and `commands/` trees are compatibility surfaces. They may translate host-specific invocation into the canonical skill, but they are not part of a standard Agent Skills installation and may not depend on repository-only research tooling.

## Repository-only tooling

The root `scripts/`, `benchmarks/`, `test/` and `.github/` trees are repository research, evidence, test and CI support. Existing entrypoints remain in place so historical research and CI stay runnable, but a supported Design Studio run or adapter must not import, execute or shell into them.

Historical Milestone 0 comparison evidence remains available under `benchmarks/milestone-0/`. Its status is research evidence for targeted questions, not a release gate and not an installed-runtime dependency.

## Enforcement

The boundary is protected at two observable seams:

1. `test/support/validate_clean_install.py` scans the complete installed skill and optional adapters and rejects positive execution/import dependencies on repository-only roots.
2. `.github/workflows/validate-agent-skill-install.yml` installs Design Studio through the pinned standard Agent Skills CLI and verifies the resulting skill package does not contain repository-only or Claude-only surfaces.

`runtime-surface.json` is the single machine-readable classification used by repository validation. `ROADMAP.md` remains a map to issue state rather than duplicating this implementation contract.

## Downstream constraint

Issue #50 may reorganise only deterministic behavior that a supported run actually needs. It must not absorb benchmark, capability-probe or comparison machinery merely because similar code already exists in the repository, and it must not rewrite stable Python or Node code solely for uniformity.
