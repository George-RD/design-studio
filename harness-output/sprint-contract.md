# Design Studio Website Redesign — Sprint Contract

## Project
Redesign the `docs/index.html` landing page for the Design Studio Claude Code plugin so that the site itself looks like the work of a design studio, not a generic AI-tool landing page.

## Target
- Single file: `docs/index.html` (vanilla HTML/CSS/JS, no build step)
- Existing assets `poster.jpg` and `video-720p.mp4` remain in use
- No new dependencies or frameworks

## Quality Thresholds

Use the four criteria from the Design Studio evaluation rubric:

| Criterion | Weight | Minimum Acceptable | Ship Target |
|-----------|--------|-------------------|-------------|
| Design Quality | 2× | 6 | 7 |
| Originality | 2× | 5 | 7 |
| Craft | 1× | 6 | 7 |
| Functionality | 1× | 6 | 7 |

Weighted average formula:
```
weightedAvg = (designQuality * 2 + originality * 2 + craft + functionality) / 6
```

## Ship Conditions (any of the following)
- All four criteria ≥ 7.0
- Weighted average ≥ 6.5 AND scores have plateaued within ±0.5 for two consecutive iterations

## Hard Pivot Conditions
- Originality ≤ 4 after iteration 2
- Weighted average < 5.0 after iteration 3
- Weighted average declined for 2 consecutive iterations
- Converged within ±0.5 for two iterations but weighted average < 6.5

## Max Iterations
- 6 iterations for this single-page redesign.

## Adversarial Gate (mandatory before scoring)
For every evaluation pass, check and document pass/fail:
1. **Viewport Boundary Audit** at 1440px — no horizontal scroll, no content overflow.
2. **Text Readability Sweep** — all body text ≥ 16px effective, contrast ≥ 4.5:1, no overlapping text.
3. **Interaction Completeness** — every hover/decorative element has a purpose; all clickable targets have adequate size (≥ 44×44px).
4. **Overflow Stress Test** at 390px width — no horizontal scroll, no clipped content, readable mobile layout.

Gate failures hard-cap Craft and Functionality at 5 for the affected zone.

## Zone Definitions
Evaluate each zone independently and enforce zone floors:
1. Header / navigation
2. Hero
3. Problem / manifesto
4. Process diagram
5. Video / proof
6. Differentiators
7. Scoring rubric
8. Install / CTA
9. Footer

Page-level Craft = min(whole-page Craft, lowest zone Craft). Page-level Functionality = min(whole-page Functionality, lowest zone Functionality).

## Anti-Patterns (originality ceiling)
The following automatically cap Originality at 4 regardless of execution quality:
- Centered hero section with heading + subtitle + CTA button
- Purple/blue gradient hero background
- 3–4 column card grid of features
- System-only font stack with no distinctive typeface
- Generic SaaS landing page rhythm (hero → feature grid → CTA footer)

## Deliverables
- Updated `docs/index.html`
- `harness-output/spec.md`
- `harness-output/sprint-contract.md`
- `harness-output/design-description-{N}.md` per iteration
- `harness-output/critique-{N}.md` per iteration
- `harness-output/scores.json` per iteration
- Final `harness-output/report.md`
