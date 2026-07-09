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
  "iterate on design", "evaluate the design", "design quality loop".
version: 1.1.0
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
| Skill trigger (description match) | Load this INDEX + execute `workflow.yaml` |
| `/design-studio:create` (`commands/create.md`) | Same: orchestrator + INDEX + `workflow.yaml` |

Standalone: no brand kit required. Planner invents aesthetic direction from the user prompt.

## Lanes

| Lane | Use when | v1 loads | Future leaves (not in this package yet) |
|------|----------|----------|----------------------------------------|
| **Studio** | Full design→build→evaluate loop | workflow, planning, generation, agents, iteration, codify assets | — |
| **Design system** | Codify or extend tokens/DNA/components | codify assets only | RESERVED — add leaves under `references/` only when a domain task needs them |
| **Review** | Audit without full studio loop | none yet (Evaluator only inside Studio) | RESERVED — add leaves under `references/review/` with conditional fan-out when audit-only lands |
| **Meta** | Improve the harness | `references/meta.md`, `references/rationale.md` | — |

## Orchestrator checklist (Studio lane)

Execute `workflow.yaml` end to end. Expand prompts from references only when the step needs them.

1. **Plan** — write `harness-output/spec.md` + `sprint-contract.md` (creative tension + anti-goals). Load `references/planning.md` if expanding methodology.
2. **Design** — spawn DesignAgent from `agents/design-agent.md`. Input: screenshots/critique (if any), spec, sprint contract — never code. Output: `design-description-{N}.md`. Iteration 1: three divergent concepts, pick boldest that fits.
3. **Implement** — spawn Builder with design description + code + `references/generation.md`. Must write `serve.json`, site, and `design-flags-{N}.json`.
4. **Evaluate** — spawn Evaluator from `agents/evaluator.md`. BOC probe→first adapter; live browser only. Writes `critique-{N}.md` + `scores.json`.
5. **Decide** — REFINE / PIVOT / SHIP per `workflow.yaml` decision table; narrative in `references/iteration.md`. Thresholds live only in `workflow.yaml` `defaults:`.
6. **Loop** — on REFINE/PIVOT return to Design with prior scores + flags as constraints; stop at SHIP or `maxIterations`.
7. **Codify** — on SHIP or budget exhaust: DesignAgent → `design-system/design-dna.md` (12 sections); Builder → `tokens.css`; Orchestrator instantiates `assets/design-system-skill/` → `design-system/skill/<project>-design/`.
8. **Finalize** — `report.md` + best iteration; track `harness-output/` on the feature branch.

Agents: Planner, DesignAgent, Builder, Evaluator. Roles and prompts are authoritative in `workflow.yaml`.

Optional multi-section pages: section decomposition (per-section Design→Implement→Evaluate, then integration). Zone scoring always runs inside Evaluate. Details: `references/evaluation.md`.

## Routing table

| Need | Load when | Path |
|------|-----------|------|
| Machine loop, thresholds, schemas | Always (Studio) | `workflow.yaml` |
| Expand prompt / creative tension | Plan | `references/planning.md` |
| DesignAgent system prompt | Spawn design | `agents/design-agent.md` |
| Builder principles / DESIGN-FLAG | Implement | `references/generation.md` |
| Evaluator system prompt + BOC + rubric | Spawn evaluate | `agents/evaluator.md` |
| Orchestrator score reading | After scores (optional) | `references/evaluation.md` |
| REFINE / PIVOT / SHIP | Decide | `references/iteration.md` |
| Instantiate design-system skill | Codify | `assets/design-system-skill/` |
| Why isolation / research | User asks why | `references/rationale.md` |
| Tune harness | Meta lane | `references/meta.md` |
| Future design-system leaves | Domain task (reserved) | `references/<domain>.md` |
| Future review leaves | Audit-only (reserved) | `references/review/<name>.md` |

## Artifacts

| Artifact | By | When |
|----------|----|------|
| `harness-output/spec.md` | Planner | Plan |
| `harness-output/sprint-contract.md` | Planner | Plan |
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

Track `harness-output/` in VCS on feature branches (not `.gitignore`). Commit after each iteration so artifacts survive branch switches.

## Prerequisites

- **Browser automation** — probe → first available adapter (claude-in-chrome MCP, chrome-devtools MCP, Playwright MCP, headless Chrome CDP, harness-native) → HALT only if none. Never code-only evaluation. Full BOC: `agents/evaluator.md` / `references/evaluation.md`.
- **Serve contract** — `harness-output/serve.json` is authoritative for path/port/command; default port 3333 is only an example.
- **Subagents** — harness must spawn isolated agents with per-agent context (Agent tool / OMP `task` / equivalent).

Portability: `workflow.yaml` `capabilities:` + `schemas:` are the host contract. Model names, `/loop`, and Agent tool are labeled examples elsewhere, not requirements.

## Extending (single entry point)

- New capability = one leaf under `references/` (or `references/review/`) + **one** routing-table row with a when-clause.
- Do **not** add a second always-on skill for “design”.
- Do **not** instruct “read all of `references/`”.
- Do **not** embed catalogs of every leaf procedure in this INDEX.
- External kits (e.g. design-system prompt packs): split into leaves; map into **Design system** or **Review** lanes; polish umbrellas route **conditionally** (static → hierarchy + slop; interactive → + interaction + a11y) — never all reviewers always.
