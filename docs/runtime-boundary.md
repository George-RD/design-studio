# Runtime distribution boundary

**Status:** Authoritative from issue #49, updated by #50  
**Governing spec:** [#43](https://github.com/George-RD/design-studio/issues/43)  
**Governing decision:** [ADR 0002](decisions/0002-owned-method-kernel.md)  
**Machine-readable boundary:** [`runtime-surface.json`](../runtime-surface.json)

Design Studio has one canonical installed product: the Agent Skill under `skills/design-studio/`. The stable deterministic interface is [`runtime-contract.md`](../skills/design-studio/runtime-contract.md). A supported run may use only behavior carried by that installed skill plus capabilities supplied by the host.

`runtime-surface.json` records the current distribution invariant. The frozen [`migration-map.json`](migration-map.json) remains the pre-change inventory and provenance baseline; it is not a second current runtime definition.

## Installed runtime

`skills/design-studio/**` is the installed runtime. It contains the skill router, workflow, source-blind roles, references, eval contract, stable runtime contract and any deterministic helpers required by supported operations.

The current helper family is `skills/design-studio/runtime/mechanical/`. It implements the local `mechanical_preflight` evidence contract without launching a browser or depending on an external detector. The host supplies current source/browser facts; the helper validates and normalizes them into the canonical snapshot.

The migration inventory found no historical repository script family that should be promoted wholesale. Future helpers must follow the same rule: extract only deterministic behavior a supported operation actually needs, behind the stable seam and under the installed runtime helper root.

## Optional adapters

The root `.claude-plugin/`, `agents/` and `commands/` trees are compatibility surfaces. They may translate host-specific invocation into the canonical skill, but they are not part of a standard Agent Skills installation and may not depend on repository-only research tooling.

## Repository-only tooling

The root `scripts/`, `benchmarks/`, `test/` and `.github/` trees are repository research, evidence, test and CI support. Existing entrypoints remain in place so historical research and CI stay runnable, but a supported Design Studio run or adapter must not import, execute or shell into them.

Historical Milestone 0 comparison evidence remains available under `benchmarks/milestone-0/`. Its status is research evidence for targeted questions, not a release gate and not an installed-runtime dependency. Issue #42 remains reliability work for the historical capability gate; #50 does not make that gate part of the product runtime.

## Enforcement

The boundary is protected at observable distribution and behavior seams:

1. `test/support/validate_clean_install.py` scans the complete installed skill and optional adapters and rejects positive execution/import dependencies on repository-only roots.
2. `.github/workflows/validate-agent-skill-install.yml` installs Design Studio through the pinned standard Agent Skills CLI and verifies the resulting package contains the shipped runtime helper but no repository-only or Claude-only surfaces.
3. `.github/workflows/runtime-portability.yml` runs the mechanical runtime contract on Linux, macOS and Windows.

`runtime-surface.json` is the single machine-readable current distribution classification used by repository validation. `ROADMAP.md` remains a map to issue state rather than duplicating this implementation contract.

## Normalization rule

#50 normalizes product runtime by responsibility, not by historical host or milestone. The first responsibility extracted is mechanical evidence because supported runs need deterministic snapshot/signature/waiver behavior and the old optional external-detector branch violated ADR 0002.

Browser launching, agent-capability probes, comparison runners, benchmark fixtures and deadline wrappers stay repository-only. Stable Python or Node research code is not rewritten solely for uniformity, and no compatibility shim is added for an entrypoint that was never part of the installed product.
