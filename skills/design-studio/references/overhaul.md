# Overhaul mode

Studio path for "I have an existing UI; put it through a design overhaul." Still the Studio lane — not a second skill, not a Review-only audit.

Full procedure lives here. INDEX routes here when overhaul inputs are present.

## When to use

Use overhaul when the user provides an existing UI **path** and/or **URL** plus goals (keep IA, rebrand, raise originality, mobile-first, etc.).

Use greenfield when there is only a text prompt (optional brand brief) and no existing site.

## Inputs

| Input | Required | Notes |
|-------|----------|--------|
| `user_prompt` | yes | Product intent and overhaul goals in natural language |
| `existing_site` | one of site/url | Local path to an existing UI tree |
| `existing_url` | one of site/url | Live or static URL to capture |
| `overhaul_goals` | no | Explicit constraints (keep structure, rebrand only, …) |
| `brand_brief` | no | Same optional brand kit as greenfield |

Mode is **overhaul** when `existing_site` or `existing_url` is present; otherwise **greenfield**.

## Greenfield vs overhaul

| | Greenfield | Overhaul |
|---|------------|----------|
| Plan inputs | prompt (+ brand) | prompt + path and/or URL (+ goals, brand) |
| Baseline | none | `harness-output/baseline.md` + screenshots when possible |
| Design iter 1 | three concepts from spec only | three concepts from spec + **baseline screenshots** (never source) |
| Builder N=1 | empty `site/` | may seed from existing tree / `harness-output/site/` |
| Isolation | DesignAgent never sees code | unchanged — renders + intent only |

## Plan responsibilities

1. Detect mode from inputs.
2. Write `harness-output/spec.md` and `harness-output/sprint-contract.md` as usual.
3. On overhaul, expand against the **existing product** (purpose, zones, constraints) — do not invent a greenfield product that ignores the seed.
4. Write anti-goals that reject "polish the current template" and "safe incremental restyle."
5. Write `harness-output/baseline.md` recording:
   - `mode: overhaul`
   - `existing_site` and/or `existing_url`
   - `overhaul_goals` if provided
   - `baseline_screenshots` paths (or why capture failed)
   - whether the tree was seeded into `harness-output/site/` and `serve.json` status
6. **Baseline capture before Design iter 1** (orchestrator may execute; Planner records paths):
   - If `existing_site`: seed into `harness-output/site/` when serveable; write `harness-output/serve.json`.
   - If `existing_url`: open via Browser Operations Contract (BOC).
   - Capture desktop 1440 and mobile 390 under `harness-output/baseline/` (e.g. `desktop-1440.png`, `mobile-390.png`).
   - If capture is impossible: record the reason in `baseline.md` and continue.

Never paste HTML/CSS/JS into DesignAgent inputs. Source paths stay for Builder/orchestrator only.

## DesignAgent rules

- Receive: spec, sprint contract, optional brand brief, **baseline screenshots** (N=1 overhaul), later-iteration screenshots/critique.
- Never receive: source trees, HTML, CSS, JS, or implementation instructions.
- Treat the baseline as the **thing to beat**, not a tweak target. Iteration 1 still produces **three divergent concepts**, picks the boldest that fits the sprint contract, and expands only the winner.
- Visual/experiential language only.

## Builder seed rules

- N=1 overhaul: may start from seeded `harness-output/site/` (or recorded `existing_site`) when present.
- Still execute the DesignAgent description **faithfully** — seed is substrate, not design authority.
- REFINE (N>1): preserve and revise existing code as today.
- PIVOT: abandon the implementation and rebuild; keep only product requirements from the spec.

## Isolation (who sees what)

| Agent | Sees baseline screenshots | Sees existing source | Sees design description |
|-------|---------------------------|----------------------|-------------------------|
| Planner / orchestrator | yes (capture) | paths only for seed/serve | no |
| DesignAgent | yes | **no** | writes it |
| Builder | no (optional) | yes when seeded / refining | yes |
| Evaluator | live render only | **no** | optional context |

## Failure modes

| Situation | Action |
|-----------|--------|
| No browser automation | Record in `baseline.md`; proceed without screenshots; DesignAgent uses overhaul brief only |
| URL only (no local tree) | Capture screenshots; Builder starts fresh unless user later provides a tree |
| Path only, not serveable | Record seed path; skip screenshots or capture if another adapter can open files; Builder may still copy seed on N=1 |
| Capture partial (one viewport) | Record `actual` paths; mark missing viewport; Design continues |

## Routing

Load this leaf at Plan when `existing_site` or `existing_url` is provided (skill trigger or `/design-studio:create` overhaul shape). Workflow thresholds, isolation, and decision table stay in `../workflow.yaml`.
