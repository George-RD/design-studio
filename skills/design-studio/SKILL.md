---
name: design-studio
description: >-
  4-agent design-evaluate-iterate harness for distinctive frontend creation that defeats code-anchoring bias
  and codifies the winning direction into a reusable design system (design-dna.md, tokens.css, and an installable skill template).
  Use this skill when building web pages, components, or applications where design quality
  and originality matter — not just functional correctness. Orchestrates separated evaluator,
  design agent (visual-only, never sees code), and implementation agent with live browser
  interaction to push past safe AI defaults.
  Triggers: "create a website", "build a page", "design a frontend", "harness mode",
  "iterate on design", "evaluate the design", "design quality loop",
  "overhaul existing UI", "redesign existing site", "redesign this page",
  "audit this UI", "polish this page", "design review", "slop check",
  "accessibility audit", "hierarchy review", "ship-ready polish".
version: 1.3.0
---

# Design Studio

A multi-agent harness that produces distinctive frontends by isolating design vision, implementation, and evaluation. When a direction ships, it codifies DNA, tokens, and an installable design-system skill. Paths below are relative to this skill package (`skills/design-studio/`).

## Isolation rules

- **DesignAgent** — never sees source code; only screenshots, critique, and the spec.
- **Evaluator** — never sees source code; judges the live rendered page only.
- **Builder** — receives design description + code; executes, does not invent direction.
- **Orchestrator** — runs the loop, enforces isolation, never substitutes code-only review.

## Entry points

| Entry | Means |
|-------|--------|
| Skill trigger (description match) | Load this INDEX + dispatch by intent (see Intent dispatch) |
| `/design-studio:create` (`commands/create.md`) | Orchestrator + INDEX + `workflow.yaml` (Studio lane) |
| `/design-studio:review` (`commands/review.md`) | Orchestrator + INDEX + Review lane only (`references/review/polish.md`) |

Standalone: no brand kit required. Greenfield from a text prompt, or overhaul from an existing path/URL plus goals. Planner invents or reframes aesthetic direction from those inputs.

## Lanes

| Lane | Use when | Loads |
|------|----------|-------|
| **Studio** | Full design→build→evaluate loop (greenfield or overhaul) | `workflow.yaml`, planning, generation, agents, iteration, codify assets |
| **Design system** | Codify or extend tokens/DNA after SHIP (or codify-only request) | codify assets only |
| **Review** | Audit/polish **without** full Studio loop | `references/review/polish.md` (+ conditional lens leaves) |
| **Meta** | Improve the harness | `references/meta.md`, `references/rationale.md` |

Studio + Review + codify. Design system extract-without-loop leaves are not shipped yet.

## Intent dispatch

| User intent signals | Lane |
|---|---|
| create / build / design a new UI / run the harness loop | **Studio** (greenfield) |
| redesign / overhaul + existing path or URL | **Studio** + `references/overhaul.md` |
| audit / polish / review / slop / a11y / hierarchy / ship-ready / score my current site **without** redesign | **Review** → load `references/review/polish.md` |
| extract tokens / write DNA only / codify after ship | **Design system** (existing codify path) |
| improve the harness itself | **Meta** |

Tie-breakers:

- Path/URL present **and** verbs are polish/audit/review only → **Review** (not overhaul).
- Path/URL present **and** verbs are redesign/overhaul/rebuild or goals include "raise originality / rebrand / new direction" → **Studio** overhaul.
- Both signals mixed ("audit then redesign") → run **Review** first only if user asked for a report before rebuild; otherwise **Studio** overhaul. If still ambiguous, ask one clarifying question (Review-only vs full overhaul) — do not silently start the 4-agent loop for pure polish language.
- Near-miss pure CSS tweak without design-quality ask → do not start Studio (existing eval id 4 spirit); Review only if they asked to audit.

## Orchestrator checklist (Studio lane)

Execute `workflow.yaml` end to end. Expand prompts from references only when the step needs them.

1. **Plan** — write `harness-output/spec.md` + `sprint-contract.md` (creative tension + anti-goals). Load `references/planning.md` if expanding methodology. If overhaul inputs (`existing_site` / `existing_url`) are present, load `references/overhaul.md` and capture baseline before Design.
2. **Design** — spawn DesignAgent from `agents/design-agent.md`. Input: screenshots/critique (if any), baseline screenshots on overhaul N=1, spec, sprint contract — never code. Output: `design-description-{N}.md`. Iteration 1: three divergent concepts, pick boldest that fits.
3. **Implement** — spawn Builder with design description + code + `references/generation.md`. Must write `serve.json`, site, and `design-flags-{N}.json`.
4. **Evaluate** — spawn Evaluator from `agents/evaluator.md`. BOC probe→first adapter; live browser only. Writes `critique-{N}.md` + `scores.json`.
5. **Decide** — REFINE / PIVOT / SHIP per `workflow.yaml` decision table; narrative in `references/iteration.md`. Thresholds live only in `workflow.yaml` `defaults:`.
6. **Loop** — on REFINE/PIVOT return to Design with prior scores + flags as constraints; stop at SHIP or `maxIterations`.
7. **Codify** — on SHIP or budget exhaust: DesignAgent → `design-system/design-dna.md` (12 sections); Builder → `tokens.css`; Orchestrator instantiates `assets/design-system-skill/` → `design-system/skill/<project>-design/`.
8. **Finalize** — `report.md` + best iteration; track `harness-output/` on the feature branch.

Agents: Planner, DesignAgent, Builder, Evaluator. Roles, step wiring, thresholds, and schemas are authoritative in `workflow.yaml`. DesignAgent/Evaluator system prompts are authoritative in `agents/*.md` (paths in the routing table).

Optional multi-section pages: section decomposition (per-section Design→Implement→Evaluate, then integration). Zone scoring always runs inside Evaluate. Details: `references/evaluation.md`.

## Orchestrator checklist (Review lane)

Execute `references/review/polish.md` only. Do **not** run `workflow.yaml` or the Studio loop.

1. **Load** — read `references/review/polish.md` (umbrella procedure).
2. **Classify surface** — `static` (marketing/content, links only) or `interactive` (forms, states, modals, app UI).
3. **Conditional lenses** — always load `slop.md` + `hierarchy.md`; if `interactive` or user asked states/a11y, also load `interaction.md` + `a11y.md`.
4. **Browser (BOC)** — probe → first available adapter; HALT only if no browser automation. Ground findings in live screenshots, never code-only.
5. **Fan-out** — spawn one subagent per loaded lens with screenshots + surface description + the lens file body; collect every issue with severity + confidence.
6. **Aggregate** — merge/dedupe; bucket Blockers / Quality / Polish recommendations.
7. **Act** — default: fix all Blockers + Quality on the target; `report_only` true: write findings only.
8. **Write artifacts** — `harness-output/review/report.md`, `harness-output/review/findings.json`, `harness-output/review/screenshots/*`.

## Routing table

| Need | Load when | Path |
|------|-----------|------|
| Machine loop, thresholds, schemas | Always (Studio) | `workflow.yaml` |
| Expand prompt / creative tension | Plan | `references/planning.md` |
| Overhaul mode (existing UI path/URL) | Plan when `existing_site` or `existing_url` provided | `references/overhaul.md` |
| DesignAgent system prompt | Spawn design | `agents/design-agent.md` |
| Builder principles / DESIGN-FLAG | Implement | `references/generation.md` |
| Evaluator system prompt + BOC + rubric | Spawn evaluate | `agents/evaluator.md` |
| Orchestrator score reading | After scores (optional) | `references/evaluation.md` |
| REFINE / PIVOT / SHIP | Decide | `references/iteration.md` |
| Instantiate design-system skill | Codify | `assets/design-system-skill/` |
| Why isolation / research | User asks why | `references/rationale.md` |
| Tune harness | Meta lane | `references/meta.md` |
| Review umbrella (audit/polish, no Studio loop) | Review lane | `references/review/polish.md` |
| AI slop lens | Review, always under polish | `references/review/slop.md` |
| Hierarchy & rhythm lens | Review, always under polish | `references/review/hierarchy.md` |
| Interaction states lens | Review when surface is interactive or user asks states | `references/review/interaction.md` |
| Accessibility lens | Review when surface is interactive or user asks a11y | `references/review/a11y.md` |

## Artifacts

| Artifact | By | When |
|----------|----|------|
| `harness-output/spec.md` | Planner | Plan |
| `harness-output/sprint-contract.md` | Planner | Plan |
| `harness-output/baseline.md` | Planner / orchestrator | Plan (overhaul) |
| `harness-output/baseline/*` | Orchestrator | Plan (overhaul screenshots) |
| `harness-output/design-description-{N}.md` | DesignAgent | Design |
| `harness-output/serve.json` | Builder | Implement |
| `harness-output/site/` | Builder | Implement |
| `harness-output/design-flags-{N}.json` | Builder | Implement |
| `harness-output/scores.json` | Evaluator | Evaluate |
| `harness-output/critique-{N}.md` | Evaluator | Evaluate |
| `harness-output/design-system/design-dna.md` | DesignAgent | Codify |
| `harness-output/design-system/tokens.css` | Builder | Codify |
| `harness-output/design-system/skill/<project>-design/` | Orchestrator | Codify |
| `harness-output/report.md` | Orchestrator | Finalize |
| `harness-output/review/report.md` | Orchestrator / Review | Review |
| `harness-output/review/findings.json` | Orchestrator / Review | Review |
| `harness-output/review/screenshots/*` | Orchestrator / Review | Review |

Track `harness-output/` in VCS on feature branches (not `.gitignore`). Commit after each iteration so artifacts survive branch switches.

## Prerequisites

- **Browser automation** — probe → first available adapter (claude-in-chrome MCP, chrome-devtools MCP, Playwright MCP, headless Chrome CDP, harness-native) → HALT only if none. Never code-only evaluation. Full BOC: `agents/evaluator.md` / `references/evaluation.md`.
- **Serve contract** — `harness-output/serve.json` is authoritative for path/port/command; default port 3333 is only an example.
- **Subagents** — harness must spawn isolated agents with per-agent context (Agent tool / OMP `task` / equivalent).

Portability: `workflow.yaml` `capabilities:` + `schemas:` are the host contract. Model names, `/loop`, and Agent tool are labeled examples elsewhere, not requirements.

## Extending (maintainers)

Maintainer-only. End users do not need this section to run Studio.

- New capability = one leaf under `references/` + **one** routing-table row with a when-clause.
- Do **not** add a second always-on skill for “design”.
- Do **not** instruct “read all of `references/`”.
- Do **not** embed catalogs of every leaf procedure in this INDEX.
- External kits (e.g. design-system prompt packs): split into leaves; map into **Design system** or **Review** lanes; polish umbrellas route **conditionally** (static → hierarchy + slop; interactive → + interaction + a11y) — never all reviewers always.
