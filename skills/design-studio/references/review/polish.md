# Review: Polish pass

Audit and polish an existing UI for ship-readiness without running the full Design Studio create/overhaul loop. This is the Review lane orchestrator. It loads conditional lens leaves, grounds findings in the live render, fixes what is cheap and local, and writes a review report. It does NOT plan, generate, or codify.

## When to use

Use this pass when the user wants an audit, polish, ship-gate, or slop/a11y/hierarchy/states check of a surface they already have, without a redesign or overhaul. Triggers include: "audit this UI", "polish this page", "design review", "slop check", "accessibility audit", "hierarchy review", "ship-ready polish".

The surface is anything rendered: a local HTML/CSS/JS path, a served site, a live URL, or an already-running `harness-output/serve.json`.

## Not when

Do NOT use this pass for:

- "create / build / design a new UI" — that is the Studio lane (`workflow.yaml` loop).
- "redesign / overhaul / rebuild" — that is the Studio lane with `references/overhaul.md`, even if the user also has an existing path. A pure audit with no rebuild intent stays here.
- "extract tokens / write DNA only" — that is the Design system path (existing codify assets flow).

If the user says "audit then redesign", run Review first only if they explicitly asked for a report before the rebuild. Otherwise route to Studio overhaul and ask one clarifying question if still ambiguous. Do not silently start the 4-agent loop for pure polish language.

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| `target` | yes | Local path, URL, or running `harness-output/serve.json` for the surface to review |
| `constraints` | no | User-specified focus (e.g. "mobile only", "check contrast") |
| `report_only` | no | When `true`, write findings only and apply no fixes (default `false`) |

## Serve and browser

Reuse the Studio serve contract when the target is a local site:

1. If `harness-output/serve.json` is present, use it as the running surface.
2. Else, serve the given local path (e.g. `npx serve ./<path> -l 3333`) or open the given URL in a dedicated review tab.
3. Capture screenshots before any lens fan-out (see Artifacts for viewports).

**Browser Operations Contract (BOC).** All review is grounded in the live render. Resolve the browser adapter at runtime:

- Probe for any available adapter (claude-in-chrome MCP, chrome-devtools MCP, Playwright MCP, headless Chrome CDP, or harness-native) with a harmless call.
- Use the first adapter that responds.
- HALT only if no browser automation is available at all. Record the halt in `report.md` and stop. Never fall back to a code-only review — design quality and accessibility cannot be judged from source alone.

This is the same BOC rule as the Studio evaluator (`agents/evaluator.md`) and INDEX Prerequisites. Review is a live-render audit, not a grep over CSS.

## Classify surface once

Decide the surface class a single time, before fan-out. Every lens reads this classification:

- `static` — marketing, landing, or content pages with no meaningful interactive widgets beyond links (no forms, no stateful buttons, no modals, no menus, no multi-step flow).
- `interactive` — forms, buttons with state, modals, menus, tabs, app UI, or any multi-step flow.

## Conditional lens load (hard rule)

Never load all lenses always. Load per this rule:

- **Always:** `slop.md` + `hierarchy.md`.
- **If `interactive` OR the user asked about states / a11y / keyboard:** also load `interaction.md` + `a11y.md`.
- **If `static` AND the user only asked for visual polish:** skip `interaction.md` + `a11y.md` unless they explicitly ask.

This keeps static visual-only reviews fast and keeps interactive reviews honest. The lens leaf paths are relative to this skill package:

| Lens | Path | Load |
|------|------|------|
| AI slop | `references/review/slop.md` | always |
| Hierarchy & rhythm | `references/review/hierarchy.md` | always |
| Interaction states | `references/review/interaction.md` | conditional |
| Accessibility | `references/review/a11y.md` | conditional |

## Fan-out

Spawn one subagent per loaded lens (parallel where the harness allows; sequential otherwise). Give each subagent:

1. The screenshots captured above (desktop 1440 + mobile 390).
2. `surface_description` — what the surface is, its primary goal, and the `surface_class` (static / interactive).
3. The single lens file body (read the lens file and pass its contents as the procedure).
4. The instruction to report **every** issue with `confidence` and `severity` — no self-censoring of "minor" findings.

Each lens subagent returns findings in the shared schema (see Artifacts). Do not have a lens subagent edit the surface; lens subagents report, the orchestrator acts (below).

If a single a11y subagent covers all four a11y sections, that is acceptable — `a11y.md` is one leaf with four sections, not four agents.

## Aggregate

Merge findings from all lens subagents into one list. Dedupe overlaps: when two findings describe the same defect, keep one and let the **highest severity win**. Map each finding into one of three buckets:

1. **Blockers** — accessibility failures (contrast, keyboard, focus, labels), broken interaction, primary CTA invisible or unusable within 5 seconds.
2. **Quality** — slop tropes, broken hierarchy or rhythm, missing or wrong interaction states, weak but non-blocking a11y.
3. **Polish recommendations** — subtler improvements (easing, spacing tuning, strategic variation).

## Act

- Default (`report_only` false): fix all **Blockers** and **Quality** on the target surface. Apply **Polish recommendations** only when cheap and local (e.g. a token swap, a one-line spacing fix). Flag judgment calls for the owner rather than guessing.
- `report_only` true: write findings only. Apply no edits.

Fixes are applied to the served source where the surface lives (local path or `harness-output/site/`). Never invent a new design direction; this is audit-and-fix, not generate.

## Artifacts

Always write these under `harness-output/review/`:

- `report.md` — verdict (`ready` | `ready_with_nits` | `hold`), the surface class, the lenses run, findings grouped by bucket (Blockers / Quality / Polish), and fixes applied (if any). Verdict rule: `ready` = no Blockers and no Quality; `ready_with_nits` = Quality fixed or only Polish remain; `hold` = any open Blocker.
- `findings.json` — structured list, one object per finding:

```json
{
  "id": "slop-1",
  "lens": "slop | hierarchy | interaction | a11y",
  "severity": "blocker | quality | polish",
  "confidence": "high | medium | low",
  "summary": "one-line description of the issue",
  "evidence": "screenshot path + region, or viewport that shows it",
  "status": "open | fixed | wont_fix"
}
```

- `screenshots/` — desktop 1440 (`desktop-1440.png`) and mobile 390 (`mobile-390.png`) captures used for grounding. If no browser adapter was available, this directory is empty and `report.md` records the HALT per BOC.

## Termination

Write the report and findings, then stop. Do NOT run `workflow.yaml` loop, do NOT spawn DesignAgent, do NOT pass Builder design-flags, do NOT consult `scores.json` decision table, and do NOT codify assets. Review is a standalone audit path, not a step inside Studio.

## Temptation stop

- Do not call this path "the Evaluate step of Studio". It is not. Studio's Evaluator scores against originality floors and writes `scores.json`/`critique-{N}.md`; Review writes `harness-output/review/*` and reports a ship verdict.
- Do not produce `REFINE`, `PIVOT`, or `SHIP`. Those are Studio loop decisions. Review ends at the report.
