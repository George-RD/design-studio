# Review: AI slop lens

Scan a rendered web surface for visual tropes that read "AI default" rather than "designed." Use this leaf during the Review lane when the polish umbrella loads it. Findings feed `harness-output/review/findings.json` and `report.md`.

## When to use

Load this leaf when the Review lane runs on any rendered surface: local HTML, a served site, or captured screenshots. It is always loaded under `polish.md`.

## Not when

Do not load this leaf alone for interactive-states or accessibility audits. Those are separate lenses (`interaction.md`, `a11y.md`). Do not run this as a "create new UI" step; slop is a review lens, not a generation brief.

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| `surface` | yes | Local path, URL, or screenshots under `harness-output/review/screenshots/` |
| `surface_class` | no | `static` or `interactive`, classified by polish.md |
| `constraints` | no | Explicit brand or tone constraints that excuse a given trope |

## Rules

Each rule is positive-first: the default to reach for, then the detection pattern. At review time, scan for detections and report every one with confidence plus severity. Filtering happens at aggregation in polish.md.

1. **Gradients - flat or subtle, on-tone.** Detect: rainbow or 3+ stop gradients; saturated purple-pink or cyan-on-dark blends on heroes, buttons, or large surfaces; decorative gradient text on metrics or headings. Web tells: purple-gradient SaaS hero, mesh-blob gradient background, gradient text on stat numbers.

2. **Emoji - functional or brand-driven only.** Detect: emoji prepending headlines, buttons, or list items; emoji used as bullets. Replace with real icons (inline SVG, icon font) or typographic hierarchy. A children's product may use playful glyphs only if they trace to the brand voice consistently.

3. **Cards - one separation strategy.** Detect: rounded-corner plus colored-left-border as the default card style; cards nested inside cards; grids of visually identical icon-plus-heading-plus-text cards (three-identical-cards). Web tells: radius plus shadow card soup, every section a bordered tile.

4. **Glassmorphism and blur - purposeful only.** Detect: `backdrop-blur`, translucent overlays, or glow used decoratively everywhere rather than for genuine layering (e.g. a sticky nav over content, a modal scrim).

5. **Type - chosen with intent.** Detect: bare default stacks (Inter or Roboto everywhere with no scale personality) when the product's tone calls for a voice. Keep system fonts only when deliberate. Web tells: `font-family: Inter, sans-serif` set globally with no heading contrast.

6. **Color - toned neutrals.** Detect: exact `#FFFFFF` or `#000000` used as page or text color. Tint neutrals toward the palette.

7. **Color provenance.** Every color traces to a token or harmonious palette. Detect: five slightly different blues or grays invented inline (e.g. `color: #2a6df0` next to `color: #2b6ef1`).

8. **Spacing - snap to a 4/8pt scale.** Detect: `padding: 7px`, `gap: 13px`, magic numbers off-scale; off-grid section rhythm.

9. **House styles - deliberate or absent.** Detect the warm-editorial combo absent a brand reason: cream `#F4F1EA`-family backgrounds plus serif display plus italic accents plus terracotta or amber. Also the 2024-AI combo: dark bg plus cyan or purple plus glow. Any one element can be deliberate; the full combo, unclaimed, is template default. Also flag the dark-mode-neon template: pure black bg, neon accent, glow text.

10. **Motion - confident easing.** Detect: bounce or elastic easing on everything (e.g. `cubic-bezier` overshoot springs on non-playful surfaces); prefer ease-out curves. Playful products may bounce, but chosen, tuned, and consistent.

## UX slop

- Missing states: loading, empty, error, offline.
- Empty states that say "nothing here" instead of guiding the user's next action.
- Every button styled primary; no action hierarchy.
- Heading restates the intro text; filler copy that says nothing.
- Modals as the lazy default for every interaction.

## Output

Report detections grouped by category. For each detection record:

| Field | Value |
|-------|-------|
| `lens` | `slop` |
| `severity` | `blocker` / `quality` / `polish` (use `quality` for template-default combos, `polish` for subtle) |
| `confidence` | `high` / `medium` / `low` |
| `summary` | one line describing the trope and where |
| `evidence` | screenshot region or selector |
| `status` | `open` (or `fixed` if Review applied a fix) |

Flag judgment calls for the owner. Note where a trope is excused by an explicit brand constraint. Do not self-censor "minor" detections; aggregation in polish.md deduplicates and ranks.

Note: other platforms (e.g. native SwiftUI) may show these same tropes via `LinearGradient` or `RoundedRectangle` fills. The web surface is the target here.
