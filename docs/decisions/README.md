# Architecture decisions

| ADR | Status | Current meaning |
|---|---|---|
| [0001: Make Impeccable the required design foundation](0001-impeccable-foundation.md) | Superseded | Historical boundary research and migration assumptions from the external-foundation direction. |
| [0002: Design Studio owns its method kernel](0002-owned-method-kernel.md) | Accepted | One supported local runtime, evidence-gated method intake, progressive disclosure and dogfood learning. |

When records conflict, the newest accepted ADR that explicitly supersedes an earlier record is authoritative.

## Derived architecture maps

- [Portable product migration map](../migration-map.md) — authoritative issue #44 baseline derived from ADR 0002. It classifies current product/adaptor surfaces, script families, method overlaps, protected behavior and historical evidence without introducing a new architecture decision.
