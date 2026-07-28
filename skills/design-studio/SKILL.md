---
name: design-studio
description: >-
  Multi-agent frontend design harness for new surfaces, full redesigns and high-value visual iteration.
  Separates product framing, visual direction, implementation and blind browser evaluation; preserves
  immutable iterations; optionally consumes Impeccable detector output; and documents the shipped visual
  system. Use for websites, landing pages, product screens and interactive experiences where originality
  and design quality justify a structured loop. Use the Review lane for audit/polish without redesign.
version: 1.4.0
---

# Design Studio

Design Studio protects creative judgment from implementation anchoring. It is an orchestration system, not a catalog of style prompts.

## Non-negotiable boundaries

| Role | May see source | May see prior scores | Owns decisions |
|---|---:|---:|---:|
| Planner | yes | no | scope and success criteria only |
| Visual Director | no | no; critique summaries only | visual proposals only |
| Builder | yes | no | implementation only |
| Evaluator | no | no | observations and scores only |
| Orchestrator | as needed | yes | SELECT / REFINE / PIVOT / SHIP / HALT |

- The Visual Director never receives HTML, CSS, JSX, component names, selectors or implementation diffs.
- The Evaluator never receives source, implementation effort, the intended design description or prior scores. It judges the current render against product and surface success criteria.
- The Builder does not choose a safer visual direction. It may add semantics, accessibility, responsive behaviour and required states even when the art direction did not spell them out.
- The Orchestrator is the sole decision owner. A score file written by an Evaluator must not contain a workflow decision.

## Lanes

| Lane | Use when | Authority |
|---|---|---|
| **Studio** | New surface or material redesign | `workflow.yaml` |
| **Review** | Audit/polish without a new visual world | `references/review/polish.md` |
| **Design system** | Codify the selected build or extend an existing system | Codify step in `workflow.yaml` |
| **Meta** | Improve the harness itself | `references/meta.md` plus run traces |

### Routing

- Create/build/design a page or product surface → **Studio**.
- Redesign/overhaul/rebuild an existing path or URL → **Studio**, with baseline capture.
- Audit/polish/slop/a11y/hierarchy/ship-readiness without redesign → **Review**.
- A single component, narrow CSS correction, or change a skilled designer would complete quickly → ordinary implementation or **Review**, not the full loop.
- Extract tokens/design DNA from an accepted build → **Design system**.

When the request mixes audit and redesign, Studio owns the task unless the user explicitly asked for a report before any rebuild.

## Context model

Load `references/context.md` before planning.

- `PRODUCT.md` is durable product truth: users, purpose, positioning, capabilities, constraints, real evidence and brand commitments.
- `DESIGN.md` is the current proven visual system. It is authority for extensions; during a requested redesign it is evidence and an anti-reference unless the user says to preserve it.
- `harness-output/runs/<run-id>/surface-brief.md` contains only the current surface's mode, job, action, content/proof and constraints.
- `harness-output/runs/<run-id>/iterations/<n>/direction/selected-direction.md` records the chosen source-free visual thesis for that iteration; regular iteration evaluation does not receive it. Final selection copies the winning iteration’s summary to `finish/selected-direction.md` for the fresh fidelity review.

Inspect before asking. Ask only for material gaps. Mark unattended inferences as assumptions. Never fabricate customers, prices, benchmarks, capabilities or testimonials.

## Studio execution

Run `workflow.yaml` end to end.

1. **Context and Plan** — resolve product truth, classify the surface as `persuade`, `operate`, `read` or `experience`, capture a baseline for overhauls, define success criteria and select a finite iteration budget.
2. **Explore** — Visual Director produces three viable, materially different directions without ranking them. All must fit the truth and constraints.
3. **Select** — an exact pinned direction wins first; explicit unattended requests never trigger a question; otherwise the user selects when an answer mechanism is available or the Orchestrator uses a reproducible seed. Record the choice in `direction-selection.json` and its source-free visual summary in that iteration’s `selected-direction.md`. The Visual Director does not pick its own winner.
4. **Direct** — Visual Director expands the selected direction into a visual contract: thesis, first viewport, visitor path, visual world, type, colour, rhythm, motion, responsive behaviour and signature interaction.
5. **Build** — Builder implements into the current immutable iteration directory and writes `serve.json` plus `design-flags.json`. It never commits or overwrites another iteration.
6. **Mechanical preflight** — run `references/quality-gates.md`. Prefer Impeccable's deterministic detector when available; otherwise use the browser-computed fallback. Mechanical checks may block craft/functionality but never assign visual quality or originality.
7. **Blind evaluation** — Evaluator interacts with the live render at verified desktop and mobile viewports, captures zones, tests states and writes `observation.json` plus `critique.md`. It emits no workflow decision.
8. **Decide** — Orchestrator applies the ordered decision table to history and budget. REFINE creates a new iteration and copies the chosen direction metadata forward; PIVOT creates a new iteration with a materially different direction and its own preserved summary; SHIP moves to tiered final selection.
9. **Finish** — floor-passing, mechanically clean iterations outrank higher averages with a failed criterion. Final selection copies the winning iteration’s direction summary to `finish/selected-direction.md`; a fresh evaluator reviews that summary with the original brief and live render. Apply at most one correction batch. Serve and verify the corrected copy through its own rewritten `corrected-serve.json`; accept it only when findings resolve and no material or mechanical regression remains. If either correction viewport is unavailable, record an unevaluated correction verdict with null scores rather than fabricating a comparison.
10. **Codify** — copy the selected build to `harness-output/site/`; document `DESIGN.md`, design DNA and tokens from the built result; write `report.md`.

## Budget selection

The Planner recommends one class; the user or explicit command can override it.

| Class | Iterations | Use |
|---|---:|---|
| quick | 2 | focused surface or straightforward page |
| standard | 4 | ambitious page or product screen |
| ambitious | 6 | complex experience, many states or high visual risk |

The budget covers builds, not every screenshot. A PIVOT consumes an iteration. An explicit numeric budget is clamped to 1–8. Budget exhaustion selects the best available result and labels it `best_available` when it did not meet the ship floor.

## Artifacts

Every run is immutable below `harness-output/runs/<run-id>/`.

```text
run.json
spec.md
sprint-contract.md
surface-brief.md
scores.json
baseline/
iterations/<n>/
  direction/directions.md
  direction/direction-selection.json
  direction/selected-direction.md
  direction/design-description.md
  site/
  serve.json
  design-flags.json
  mechanical-findings.json
  screenshots/
  observation.json
  critique.md
finish/
  selection.json
  selected-site/
  selected-serve.json
  selected-direction.md
  corrected-site/          # only when correction runs
  corrected-serve.json     # only when correction runs
  correction-verdict.json  # only when correction runs
  final-tree.json
```

Only after selection may the Orchestrator replace the compatibility output at `harness-output/site/`. Never depend on git history to recover an earlier iteration.

## Review lane

Execute `references/review/polish.md` without `workflow.yaml`.

- Deterministic checks own source/computed facts such as exact contrast, overflow and token misuse.
- Visual lenses own visible hierarchy, composition, rhythm and generated-template feel.
- With no browser, or when either required viewport cannot be reached, return `visual_status: unverified` and the mechanical report. Do not return a browser-grounded readiness verdict.
- With a browser, run one inspection batch, apply one grouped fix batch when requested, and confirm once.

## Quality semantics

- **The brief wins.** A user-pinned aesthetic or system is not penalised merely because a detector knows the pattern. Use a documented waiver where appropriate.
- **Common is not automatically bad.** A common component can be correct for an operational task; it simply does not create originality by itself.
- **Redesign replaces; refinement preserves.** Preserve product truth, content, behaviour and explicit brand commitments. Do not average the old and new visual worlds together.
- **Mechanics are a floor, not a direction.** Passing deterministic rules does not make a page distinctive.
- **Finish from evidence.** Record the design system after the final build, not before the implementation proves it.

## Required references

| Need | File |
|---|---|
| Product/design/surface context | `references/context.md` |
| Machine workflow, paths and decisions | `workflow.yaml` |
| Visual Director prompt | `agents/design-agent.md` |
| Builder constraints | `references/generation.md` |
| Mechanical gate and Impeccable integration | `references/quality-gates.md` |
| Blind visual evaluation | `agents/evaluator.md` |
| Review-only audit | `references/review/polish.md` |
| Overhaul baseline | `references/overhaul.md` |
| Harness tuning | `references/meta.md` |

## Prerequisites and degradation

Studio requires file I/O, isolated subagents, a runnable target and browser automation. Verify requested viewport widths with `window.innerWidth` or the adapter equivalent.

- No browser in **Studio**: preserve the build and mechanical report, mark the iteration unevaluated and HALT before a visual decision.
- No browser or missing required viewport in **Review**: return mechanical findings with visual status `unverified`.
- No Impeccable: use the fallback gate and record `detector: fallback`.
- No user answer mechanism: use the deterministic selection rule and record the seed.
- No image generation: present directions as equal text cards; do not fabricate visual comps.

## Extending the harness

- Add a capability as one focused leaf plus one routing row; do not create another always-on design skill.
- Keep style examples out of always-loaded prompts unless the user's brief names them.
- Keep scoring language about qualities, not favoured aesthetics.
- Version `SKILL.md`, `workflow.yaml`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and eval metadata together.
- After a material model upgrade, test whether each layer still improves outcomes before retaining its cost.
