---
name: design-studio
description: >-
  Multi-agent frontend design workflow for new surfaces, full redesigns and high-value visual iteration.
  Separates product framing, visual direction, implementation and blind browser evaluation; roots the target
  before work starts; preserves immutable iterations; resumes from recorded evidence; and documents the
  accepted visual system. Use Review for audit or polish without redesign.
version: 1.5.0
---

# Design Studio

Design Studio protects visual judgement from implementation anchoring. It is a controlled workflow, not a style prompt collection.

## Non-negotiable boundaries

| Role | May see source | May see prior scores | Owns decisions |
|---|---:|---:|---:|
| Planner | yes | no | scope and success criteria only |
| Visual Director | no | no | visual proposals only |
| Builder | yes | no | implementation only |
| Evaluator | no | no | observations and scores only |
| Orchestrator | as needed | yes | SELECT / REFINE / PIVOT / SHIP / HALT |

- Visual Director never receives HTML, CSS, JSX, component names, selectors, implementation diffs or an unattended assignment index.
- Evaluator never receives source, implementation effort, the full design description or prior scores. It judges the live render against product and surface success criteria.
- Builder may add semantics, accessibility, responsive behaviour and required states. It may not replace the selected direction with a safer one.
- Orchestrator is the sole decision owner. Evaluator output cannot contain a workflow decision.

## Lanes

| Lane | Use when | Authority |
|---|---|---|
| **Studio** | New surface or material redesign | `workflow.yaml` |
| **Review** | Audit or polish without a new visual world | `references/review/polish.md` |
| **Design system** | Codify the selected build or extend a proven system | Codify step in `workflow.yaml` |
| **Meta** | Improve the workflow itself | `references/meta.md` plus run traces |

### Routing

- Create, build or redesign a page or product surface: **Studio**.
- Overhaul an existing path or URL: **Studio**, with baseline capture.
- Audit, polish, slop, accessibility, hierarchy or ship readiness without redesign: **Review**.
- A single component or narrow CSS correction: ordinary implementation or **Review**, not a full Studio run.
- Extract tokens and design DNA from an accepted build: **Design system**.

When a request mixes audit and redesign, Studio owns the task unless the user explicitly asks for a report first.

## Context and run integrity

Load `references/invocation.md` to map host input and isolated roles. Then load `references/context.md` and `references/runtime-integrity.md` before planning.

- `roots.json` records repository, app and context roots with evidence.
- `capabilities.json` records the browser, runnable target, detector, question and copy tools that actually exist.
- `events.jsonl` is the append-only step journal used for resume.
- `PRODUCT.md` is durable product truth.
- `COPY.md` is optional durable voice, claim and terminology guidance.
- `DESIGN.md` is the proven visual system. It is authority for extensions; during an explicit redesign it is evidence and an anti-reference unless the user says to preserve it.
- `surface-brief.md` holds only the current surface job, action, content, proof and constraints.
- `selected-direction.md` is the source-free visual contract summary for one iteration.

Inspect before asking. Ask only for material gaps. Mark unattended inferences as assumptions. Never invent customers, prices, benchmarks, capabilities or testimonials.

## Studio execution

Run `workflow.yaml` end to end.

1. **Root and probe**: resolve repository, app and context roots; probe required and optional tools before spending an iteration.
2. **Plan**: confirm product truth, classify the surface as `persuade`, `operate`, `read` or `experience`, capture a baseline for overhauls and choose a finite build budget.
3. **Assign**: for unattended work, commit a reproducible seed and candidate slot before directions are generated. Keep both hidden from Visual Director.
4. **Explore and select**: Visual Director produces three equally specified, materially different directions. A pinned direction, the user or the precommitted slot selects one.
5. **Direct and build**: Visual Director writes the source-free contract. Builder implements it in a new immutable iteration and records fidelity evidence.
6. **Mechanical preflight**: use `references/quality-gates.md`. Each scan is a complete current snapshot. Mechanical checks can block craft or functionality but never assign visual quality.
7. **Blind evaluation**: Evaluator interacts with the live page at verified desktop and mobile viewports, captures zones and records observations and scores without a workflow decision.
8. **Decide**: Orchestrator applies the ordered decision table. REFINE keeps the world. PIVOT replaces it. SHIP moves to tiered final selection.
9. **Finish and accept**: eligible, mechanically clean iterations outrank higher averages with a failed criterion. A fresh reviewer checks the selected result. Apply at most one correction batch, then write an acceptance receipt for the final tree.
10. **Codify**: copy the accepted build to `harness-output/site/`; write `DESIGN.md`, design DNA, tokens and the report from final evidence.

## Budget selection

| Class | Builds | Use |
|---|---:|---|
| quick | 2 | focused surface or straightforward page |
| standard | 4 | ambitious page or product screen |
| ambitious | 6 | complex experience, many states or high visual risk |

An explicit budget is clamped to 1–8. A PIVOT consumes a build. Budget exhaustion selects the best available result and labels it honestly.

When Studio starts without a runnable browser target, it records the limitation, reduces the budget to one build, runs mechanical preflight and halts without selecting a visual winner.

## Resume

A run resumes only by explicit run ID or an already active run root.

- Validate completed event receipts and their artifacts.
- Continue from the first incomplete or invalidated step.
- Never rerun a completed build in the same iteration.
- Never infer completion from a directory that merely exists.
- Preserve failed and superseded evidence.

## Artifacts

Every run is immutable below `harness-output/runs/<run-id>/`.

```text
run.json
roots.json
capabilities.json
events.jsonl
spec.md
sprint-contract.md
surface-brief.md
scores.json
baseline/
iterations/<n>/
  direction/direction-assignment.json
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
  acceptance.json
```

Only after acceptance may Orchestrator replace `harness-output/site/`. Git history is not the iteration store.

## Review lane

Execute `references/review/polish.md` without `workflow.yaml`.

- Resolve roots and probe the runnable target first.
- Deterministic checks own source and browser-computed facts such as exact contrast, overflow and token drift.
- Visual lenses own visible hierarchy, composition, rhythm and generated-template feel.
- With no browser, or when either required viewport cannot be reached, return `visual_status: unverified` and the mechanical report.
- With a browser, run one inspection batch, apply one grouped fix batch when requested and confirm once.

## Quality semantics

- **The brief wins.** A pinned aesthetic or system is not penalised merely because a detector recognises the pattern. Use a documented waiver.
- **Common is not automatically bad.** A familiar component can be correct for an operational task; it simply does not create originality by itself.
- **Redesign replaces; refinement preserves.** Preserve product truth, copy claims, behaviour and explicit brand commitments. Do not average old and new visual worlds together.
- **Mechanics are a floor, not a direction.** Zero detector findings do not make a page distinctive.
- **Findings are current.** A rerun replaces the current open set. History may explain a resolution, but it cannot keep a fixed problem open.
- **Finish from evidence.** Record the design system after the final build proves it.

## Required references

| Need | File |
|---|---|
| Host input mapping and isolated-role invocation | `references/invocation.md` |
| Product, copy, design and surface context | `references/context.md` |
| Roots, capabilities, resume, assignment and acceptance | `references/runtime-integrity.md` |
| Machine workflow, paths and decisions | `workflow.yaml` |
| Visual Director prompt | `agents/design-agent.md` |
| Builder constraints | `references/generation.md` |
| Mechanical gate and Impeccable integration | `references/quality-gates.md` |
| Customer-facing copy changes | `references/copy.md` |
| Blind visual evaluation | `agents/evaluator.md` |
| Review-only audit | `references/review/polish.md` |
| Overhaul baseline | `references/overhaul.md` |
| Workflow tuning | `references/meta.md` |

## Prerequisites and degradation

Studio needs file I/O, shell access and isolated subagents. A complete visual decision also needs a runnable target and browser automation. Verify requested viewport widths with `window.innerWidth` or the adapter equivalent.

- No browser or runnable target in Studio: preserve one build and current mechanical snapshot, then halt unselected.
- No browser or missing required viewport in Review: return mechanical evidence with visual status `unverified`.
- No Impeccable: use the fallback gate and record `detector: fallback`.
- No user answer mechanism: use the precommitted deterministic assignment.
- No image generation: present equal text directions; do not fabricate comps.
- No `business-copy-style`: apply `references/copy.md` and record `copyWorkflow: local-rules`.

## Extending the workflow

- Add a capability as one focused leaf plus one routing row. Do not create another always-loaded design skill.
- Keep style examples out of always-loaded prompts unless the brief names them.
- Keep scoring language about qualities, not favoured aesthetics.
- Version `SKILL.md`, `workflow.yaml`, plugin metadata and eval metadata together.
- After a material model change, test whether each layer still improves outcomes before retaining its cost.
