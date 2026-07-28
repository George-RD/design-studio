---
description: Initialize durable product, design, and surface context without changing the interface
argument-hint: [project path or surface]
---

# Initialize Design Studio context

Prepare the target project for repeatable design work. Do not edit the product interface in this command.

## Procedure

1. Resolve the target project and read its README, product copy, routes, theme/tokens, representative components, and any existing design documentation.
2. Distinguish verified product truth from inference. Mark unresolved facts `Unknown`; do not invent commercial claims, capabilities, customers, metrics, or audience details.
3. Create or repair `.design-studio/PRODUCT.md` using `skills/design-studio/assets/context/PRODUCT.md.template`.
4. Determine whether the product has an established visual world:
   - when coherent and inspectable, document it in `.design-studio/DESIGN.md` with provenance;
   - when fragmented, document confirmed traits and unresolved conflicts;
   - when absent, leave `DESIGN.md` as a non-canonical placeholder rather than inventing a world.
5. For each surface explicitly requested, create `.design-studio/surfaces/<slug>.md` with its mode, visitor success, change semantics, important states, protected behavior, and acceptance criteria.
6. Report the evidence used, contradictions found, files written, and decisions still requiring the user.

## Guardrails

- Existing coherent implementation is evidence even when no design document exists.
- Do not rewrite product truth to fit the current UI.
- Do not describe a one-off page composition as a global design principle.
- Do not make `replace` the default. Ambiguous surfaces default to `preserve`.
- This command may document defects or drift, but it does not fix them.

Read `skills/design-studio/references/context.md` and `skills/design-studio/references/modes.md` before writing context.
