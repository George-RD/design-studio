# Durable project context

Design Studio runs should improve a product without repeatedly rediscovering what the product is. The target project may keep three small, versioned context artifacts under `.design-studio/`:

```text
.design-studio/
  PRODUCT.md
  DESIGN.md
  surfaces/
    <surface-slug>.md
```

These files are product memory, not generated documentation for its own sake. Keep them short enough to read at the start of every relevant run.

## Ownership

| Artifact | Owns | Must not own |
|---|---|---|
| `PRODUCT.md` | Audience, product mechanism, verified claims, capabilities, constraints, terminology, platform, content/assets | Route-specific layout or temporary campaign choices |
| `DESIGN.md` | The durable visual world: principles, palette roles, typography roles, spatial logic, interaction character, reusable motifs, anti-goals | One page's conversion strategy or unresolved concepts |
| `surfaces/<slug>.md` | The surface mode, visitor success, content order, important states, constraints, change semantics, acceptance criteria | Product-wide facts duplicated from `PRODUCT.md` |

## Load order

At the start of Studio or Review:

1. Read `PRODUCT.md` when it exists.
2. Read `DESIGN.md` when it exists.
3. Read the matching surface brief when it exists.
4. Inspect one representative source of incumbent visual truth: tokens, theme, a core component, or a rendered baseline.
5. Resolve contradictions in this order: explicit current user instruction, verified product truth, surface brief, durable design context, incumbent implementation.

A filename is not authority by itself. If `DESIGN.md` is stale and the live product has a coherent newer system, record the conflict; do not silently overwrite either source.

## Missing context

### Missing `PRODUCT.md`

For a new surface or replacement-world request, the Planner creates `.design-studio/PRODUCT.md` from supplied and inspectable facts. Unknown facts stay marked `Unknown`; commercial claims, customers, prices, benchmarks, and capabilities are never invented.

For a narrow Review or local refinement, missing product context does not block work. Record the gap in the report and proceed with the existing surface as limited evidence.

### Missing `DESIGN.md`

Missing `DESIGN.md` does not mean greenfield. Decide whether a coherent visual world already exists in code and assets.

- **Established world:** document it before making a durable extension.
- **Incomplete world:** preserve confirmed traits and propose only the missing rules.
- **No authority or explicit replacement:** the DesignAgent may create a candidate world.

A candidate world is written under `harness-output/context-proposal/DESIGN.md`. Promote it to `.design-studio/DESIGN.md` only after a `SHIP` decision. A `HOLD` result never becomes durable design truth.

### Missing surface brief

Create `.design-studio/surfaces/<slug>.md` before Design. It must name:

- surface and route;
- mode: `persuade`, `operate`, `read`, or `experience`;
- visitor success;
- change semantics: `preserve`, `extend`, or `replace`;
- required content, states, and constraints;
- acceptance criteria and protected behavior.

## Change semantics

- **Preserve:** keep identity, behavior, factual copy, and everything outside the requested scope. Make a local improvement.
- **Extend:** inherit the existing world and add a surface, component, or state that belongs to it. Do not run a new-world concept round.
- **Replace:** preserve product truth, content, function, native affordances, and explicit constraints; treat the old look as evidence and anti-reference, not visual authority.

When the request is ambiguous between preserve and replace, ask one question before a large build. When unattended execution is required, default to preserve and state that assumption.

## Promotion rules

- `PRODUCT.md` may be corrected whenever verified product facts change.
- Surface briefs may evolve during a run, but the final version must describe what actually shipped.
- `DESIGN.md` changes only when the shipped result establishes a durable system change.
- Review-only work never rewrites `DESIGN.md` as a side effect.
- A failed or unevaluated run writes proposals and reports, not canonical context.
