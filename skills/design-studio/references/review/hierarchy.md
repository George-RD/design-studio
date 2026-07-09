# Review: Hierarchy & rhythm lens

Audit a UI's visual hierarchy (what the eye sees first, second, third) and rhythm (repetition with strategic variation). These two qualities separate intentional design from generated output. Review per screen for hierarchy, the whole surface for rhythm.

This is a lens leaf. It always runs under `references/review/polish.md`. The orchestrator fans it out as a subagent with the live render, never as a code-only pass.

## When to use

Use this lens whenever the Review lane classifies the surface (interactive or static) and runs a polish pass. It loads unconditionally under `polish.md` alongside the slop lens.

## Not when

Do not use this lens to verify token files or design-system conformance. Token-conformance is a separate gate. Hierarchy here is judged from the rendered page, not from source. A screen can use every token correctly and still fail hierarchy.

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| `screenshots` | yes | Desktop 1440 and mobile 390 captures from the live render |
| `surface_description` | yes | What the surface is and its primary goal |
| `lens_file` | yes | This file body |
| `constraints` | no | User-specified focus (e.g. "mobile only") |

## Framing

Judge hierarchy and rhythm from the rendered screenshots. Do not open the CSS or token files to decide whether hierarchy is correct. Conformance to a token scale is a different check owned elsewhere. A surface can be token-perfect and still fail the eye. Report what the eye actually does.

Severity guidance:

- `blocker`: primary CTA invisible, or competing signals make the screen unusable within 5 seconds.
- `quality`: hierarchy or rhythm is weak, flat, reversed, or monotonous.
- `polish`: subtle tuning of scale, spacing, or variation.

Report every issue with confidence and severity. Filter nothing as "too minor". Aggregation in `polish.md` buckets and deduplicates.

## Hierarchy (per screen)

1. **Primary, secondary, tertiary.** State what the eye lands on first, second, third. If you cannot tell from the screenshot, hierarchy is broken.
2. **Size.** Headings clearly larger than body. Primary action more prominent than secondary. Flag equally important content at very different sizes, and different-importance content at identical sizes (flat).
3. **Color.** Primary actions in saturated brand color. Secondary neutral. De-emphasized muted. Flag everything one color (no signal) and loudest color on least-important (reversed signal).
4. **Weight.** Headlines bold, body regular, captions light. Flag everything bold and everything regular.
5. **Position.** Eyes start top-leading (LTR). Prime real estate holds the most important content. Flag primary actions buried bottom-trailing or below the fold.
6. **Density.** Loose spacing signals "pay attention". Tight signals "supporting". Flag important content crammed while filler breathes.
7. **5-second test.** A first-time visitor knows what to look at and what to do within 5 seconds.

## Rhythm (whole surface / flow)

1. **Spacing scale.** All padding and spacing snap to one scale (4 or 8px multiples). List the implicit scale in use. Flag outliers.
2. **Type scale.** Flag arbitrary sizes off the established ramp.
3. **Repetition.** Cards, rows, blocks share padding, gaps, structure. Flag near-duplicates that differ subtly. Identical or deliberately different, nothing between.
4. **Strategic variation.** Long screens or flows break the pattern occasionally (background shift, full-bleed moment, centered CTA). Flag total uniformity (monotony) and every-section-different (chaos).
5. **Palette discipline.** 3 to 5 colors plus tints and shades. Flag 8 or more distinct hues or multiple near-identical grays or blues.
6. **Section structure.** Sections distinguishable, consistently so. One separation strategy, not four.
7. **Alignment.** Flag off-grid elements. Inconsistent margins rather than intentional offset.

## Fixes

- Random spacing or sizes: snap to the scale. Define one if missing.
- Flat hierarchy: add contrast. Bigger headline, more prominent primary, consistently neutral body.
- Reversed hierarchy: swap the signals. Mute the loud-unimportant, elevate the buried-primary.
- Monotony: one strategic break. Chaos: consolidate to the strongest pattern.
- Ambiguous: lean toward stronger hierarchy. Too-strong dials back more easily than too-weak dials up.

## Output

Report each issue as a finding for `harness-output/review/findings.json`:

- `id`: stable identifier (e.g. `hier-1`)
- `lens`: `hierarchy`
- `severity`: `blocker` | `quality` | `polish`
- `confidence`: `high` | `medium` | `low`
- `summary`: one line describing the problem
- `evidence`: the screenshot region or viewport that shows it
- `status`: `open` (or `fixed` if you applied the fix in this pass)

Do not self-censor "minor" issues. Aggregation in `polish.md` handles dedupe and bucketing.
