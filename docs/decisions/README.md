# Architecture decisions

| ADR | Status | Current meaning |
|---|---|---|
| [0001: Make Impeccable the required design foundation](0001-impeccable-foundation.md) | Superseded | Historical boundary research and migration assumptions from the external-foundation direction. |
| [0002: Design Studio owns its method kernel](0002-owned-method-kernel.md) | Accepted | One supported local runtime, evidence-gated method intake, progressive disclosure and dogfood learning. |
| [0003: Keep Claude Code as an adapter and defer the public CLI](0003-claude-adapter-and-deferred-cli.md) | Accepted | Claude Code is optional host integration over the canonical Agent Skill; a CLI waits for evidence and must wrap the same runtime seam. |
| [0004: Prove public installation without making the installer part of the runtime](0004-installer-compatibility-proof.md) | Accepted | Pinned local and public install proofs stay blocking; latest-installer public compatibility is advisory and the installer remains outside the runtime. |
| [0005: Route Design Intent before lane work and compose website strategy through public artifacts](0005-intent-router-and-website-composition.md) | Accepted | Design Studio remains the front door; one intent seam routes lane work, optional Growth Arsenal composition, and accepted design-system effects. Product implementation begins only after v1.7 release closure. |

When records conflict, the newest accepted ADR that explicitly supersedes an earlier record is authoritative.

## Derived architecture maps

- [Portable product migration map](../migration-map.md) — authoritative issue #44 baseline derived from ADR 0002. It classifies current product/adaptor surfaces, script families, method overlaps, protected behavior and historical evidence without introducing a new architecture decision.
- [Design Studio roadmap](../../ROADMAP.md) — lean product-state and frontier map. GitHub Issues remain the executable graph.
