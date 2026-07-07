---
name: design-studio
description: >-
  4-agent design-evaluate-iterate harness for distinctive frontend creation that defeats code-anchoring bias.
  Use this skill when building web pages, components, or applications where design quality
  and originality matter — not just functional correctness. Orchestrates separated evaluator,
  design agent (visual-only, never sees code), and implementation agent with live browser
  interaction to push past safe AI defaults.
  Triggers: "create a website", "build a page", "design a frontend", "harness mode",
  "iterate on design", "evaluate the design", "design quality loop".
version: 1.0.0
---

# Design Studio

A multi-agent harness that produces distinctive, production-grade frontends by separating design vision from code implementation and evaluation. Four specialized agents — Planner, Evaluator, Design Agent, and Implementation Agent — each operate in isolation to defeat code-anchoring bias and push past safe AI defaults.

## Why This Exists

Without this harness, AI-generated frontends converge on safe, predictable layouts — technically functional but visually unremarkable. Three problems cause this:

1. **Self-evaluation is broken for subjective tasks.** When an agent evaluates its own design, it confidently praises mediocre output. No binary correctness check exists for "is this design good?"
2. **Without iteration pressure, the agent plays it safe.** One-shot generation gravitates toward template aesthetics, generic fonts, and stock layouts.
3. **Code-anchoring bias kills creativity.** When an LLM reads existing code before generating new designs, its creativity anchors to "what can I tweak in this CSS" instead of "what should this look like." Stronger models are MORE consistently affected (arXiv:2412.06593). As more code is generated, the model's attention is diluted away from user prompts toward existing code patterns (arXiv:2408.09121).

The harness fixes all three by splitting the creative process into isolated agents: an evaluator that judges only the rendered output, a design agent that creates visual direction without ever seeing code, and an implementation agent that faithfully executes design descriptions into working code. This mirrors how design studios actually work — art directors create the vision, developers implement it.

## Code-Anchoring Bias

The most important architectural insight behind the 4-agent split. Research confirms that reading existing code before generating new designs anchors the LLM's creativity. The model shifts from "what should this look like?" to "what can I change in the existing implementation?" — producing incremental CSS tweaks instead of bold redesigns.

- **arXiv:2412.06593** — Demonstrates that anchoring bias in LLMs is systematic, and stronger models are MORE consistently influenced (not less). The fix is preventing exposure to the anchor entirely.
- **arXiv:2408.09121** — Shows that as more code tokens accumulate in context, LLM attention is diluted — the model pays progressively less attention to user instructions as code tokens accumulate. Design intent gets diluted by implementation details.
- **Real-world evidence** — In real website iterations, a single-agent approach produced 3 consecutive rounds of CSS-only tweaks despite explicit instructions to "make the hero asymmetric and break the grid."

The fix: the Design Agent never sees code. It receives only screenshots, the evaluator's visual critique, and the spec. Its output is a design description — a prose document describing what the page should look like, not how to implement it. The Implementation Agent then receives this description alongside the existing code and faithfully executes it.

## Architecture

```text
USER PROMPT
  │
  ▼
┌─────────┐     spec + sprint contract + creative tensions
│ PLANNER │ ───────────────────────────────────────────────►
└─────────┘
  │
  ▼
┌────────────────┐  screenshots + critique  ┌───────────┐
│ IMPLEMENTATION │ ◄──── design desc. ───── │  DESIGN   │
│     AGENT      │                          │   AGENT   │
│  (sees code)   │                          │ (no code) │
└────────────────┘                          └───────────┘
  │          ▲                                    ▲
  │          │                                    │
  │    rendered page                     screenshots + critique
  │    (Chrome MCP)                               │
  │          │                              ┌───────────┐
  │          └───────────────────────────── │ EVALUATOR │
  │                                         │ (separate │
  │          iterate (refine or pivot)       │  agent)   │
  │          ◄──────────────────────────── └───────────┘
  │
  ▼
FINAL OUTPUT + evaluation report
```

Four agents, each with a distinct role:

| Agent | Role | Why Separated |
|-------|------|---------------|
| **Planner** | Expands terse prompt into full spec with creative tensions | Prevents cascading errors from vague requirements |
| **Evaluator** | Interacts with live page via Chrome browser automation (claude-in-chrome MCP), scores against 4 criteria with zone-based evaluation | Cannot be "captured" by implementation confidence; judges only rendered output |
| **Design Agent** | Receives screenshots + critique + spec, outputs design description (prose, not code). Never sees code. | Code-anchoring bias: seeing existing code constrains creative vision (stronger models are MORE affected) |
| **Implementation Agent** | Receives design description + existing code, outputs working frontend | Faithfully executes the design vision without second-guessing creative direction |

## The Workflow

```text
STEP  PHASE           AGENT            OUTPUT                                     MODULE
────  ─────           ─────            ──────                                     ──────
 1    Plan            Planner          harness-output/spec.md + sprint-contract.md   planning.md
 2    Design          Design Agent     harness-output/design-description-N.md        generation.md
 3    Implement       Impl. Agent      harness-output/site/ (HTML + CSS + JS)        generation.md
 4    Evaluate Live   Evaluator        harness-output/scores.json + critique-N.md    evaluation.md
 5    Decide          Orchestr.        REFINE, PIVOT, or SHIP                        iteration.md
 6    Loop            → step 2         (up to N iterations)                          iteration.md
 7    Finalize        Orchestr.        harness-output/report.md                      —
```

### Step 1: Plan

The planner takes a 1-4 sentence user prompt and produces:

- **harness-output/spec.md** -- Full product specification: purpose, audience, features, technical stack, aesthetic direction with creative tensions. Scope and high-level design, NOT granular implementation details (avoiding cascading errors).
- **harness-output/sprint-contract.md** -- Negotiated success criteria. What "done" looks like in testable terms. The evaluator will use these criteria alongside the scoring rubric.

The planner must specify a **creative tension** — not just an aesthetic label. A single label ("brutalist", "editorial") produces recognizable but generic output. A creative tension forces original solutions: "Brutalist WITH ornamental flourishes", "Minimalist BUT textural and warm." See `modules/planning.md` for the creative tension methodology.

The planner identifies opportunities to weave ambitious features throughout the spec — AI features, animations, spatial experiences, interactive elements. The planner biases toward distinctiveness, not safety.

See `modules/planning.md` for the planning methodology.

### Step 2: Design

The **Design Agent** — a separate agent that never sees code — receives:
- Screenshots from the evaluator (desktop + mobile + zone captures) — on iteration 1, no screenshots exist yet; the spec's aesthetic direction and creative tension serve as the creative seed
- The evaluator's structured critique (empty on iteration 1)
- The spec and sprint contract
- The decision to REFINE the current direction or PIVOT to a new one (REFINE on iteration 1)

On **iteration 1**, the Design Agent works from the spec alone — no evaluation data exists yet. It produces the initial design description from the planner's aesthetic direction and creative tension. On subsequent iterations, it works from real evaluation feedback.

The Design Agent produces a **prose design description** — natural-language specification of layout geometry, typography direction, color relationships, spatial rhythm, motion intent, and atmospheric qualities. It thinks like an art director reviewing comps, not a developer reading code.

This separation defeats code-anchoring bias: research shows that when generative models see existing implementations before creating, they anchor to "what can I tweak" instead of "what should this be" — and stronger models are MORE affected.

The Design Agent writes to `harness-output/design-description-{N}.md`.

See `modules/generation.md` for design and implementation principles.

### Step 3: Implement

The **Implementation Agent** receives:
- The Design Agent's prose design description (from step 2)
- The existing code (from the previous iteration, or empty on first pass)
- The spec and sprint contract

The Implementation Agent faithfully translates the design description into working code — HTML/CSS/JS, React, Vue, or whatever the spec calls for. It does NOT second-guess the Design Agent's creative decisions. It self-commits via git after each implementation pass.

See `modules/generation.md` for implementation guidance.

### Step 4: Evaluate Live

The evaluator — a **separate agent** — interacts with the live rendered page using Chrome browser automation (claude-in-chrome MCP):

1. **Serve the page** (dev server, file server, or inject into harness)
2. **Full-page screenshot** at 1440px and 390px widths
3. **Zone identification** — identify visual zones (header, hero, content sections, graphs/charts, sidebar, footer) from the full-page screenshot
4. **Per-zone zoomed screenshots** — capture each zone at 2x zoom for detailed evaluation
5. **Adversarial gate** — mandatory pre-scoring technical checks: text overflow/clipping, element overlap, responsive breakage, console errors, broken interactions. Gate failures hard-cap scores (e.g., text clipping caps craft at 5).
6. **Per-zone scoring** — score each zone against the 4 criteria independently. Zones scoring below 6 on any criterion trigger mandatory critique entries.
7. **Whole-page scoring** — score the full page, then apply zone minimums: craft and functionality scores use the minimum of whole-page score and worst zone score.
8. **Interact** — click buttons, scroll, hover over elements, test navigation
9. **Compare** the rendered result against the design description (on iterations 2+)
10. **Critique** — structured, actionable VISUAL critique with specific references to what to change, including zone-specific issues

The evaluator does NOT see any code. It sees only the rendered output, the spec, the sprint contract, and the design description (if one exists from the prior iteration). This prevents sympathy for implementation effort and forces judgment based solely on the user experience.

See `modules/evaluation.md` for the scoring rubric and evaluation protocol.

### Step 5: Decide

The decision uses scores from step 4, which evaluated the code JUST BUILT in step 3. SHIP means the current version met the threshold — no untested changes exist between evaluation and the decision.

Based on score trends across iterations:

| Pattern | Decision | Action |
|---------|----------|--------|
| Originality ≤ 4 after iteration 2 | **PIVOT** | Template pattern detected early — refinement won't fix structural problems |
| All criteria ≥ 7.0 | **SHIP** | Quality threshold met (overrides all other rules) |
| Scores improving (≥ 0.5 gain) | **REFINE** | Design Agent refines current direction using critique; Implementation Agent executes |
| Scores plateauing (within ±0.5 for 2+ rounds) AND weighted avg ≥ 6.5 | **SHIP** | Converged at acceptable quality |
| Scores plateauing (within ±0.5 for 2+ rounds) AND weighted avg < 6.5 | **PIVOT** | Converged at unacceptable quality |
| Weighted avg < 5.0 after iteration 3 | **PIVOT** | Not improving fast enough |
| Scores declining for 2 consecutive iterations | **PIVOT** | Direction is failing |
| Iteration 1 (no prior data) | **REFINE** | Always refine after first evaluation (unless quality threshold already met) |
| Max iterations reached | **SHIP** | Deliver best-scoring iteration (not necessarily the latest) |

See `modules/iteration.md` for the decision framework.

The decision routes differently across the agents:
- **REFINE**: The Design Agent receives the critique and screenshots with instruction to improve the current direction. The Implementation Agent then executes the updated design description.
- **PIVOT**: The Design Agent receives the critique with instruction to abandon and reimagine from scratch. The Implementation Agent starts from a blank slate.
- **SHIP**: Proceed to finalize.

### Step 6: Loop

Return to step 2 (Design) with the decision and critique. The agents receive:
- On REFINE: the critique + instruction to improve the current direction
- On PIVOT: the critique + instruction to abandon and reimagine from scratch

Default maximum: 8 iterations (increase to 12 for ambitious full-page designs). The source blog reports 5-15 iterations as typical for complex designs.

**Automation:** The iteration loop can be automated using `/loop` (e.g., `/loop 3m` with the cycle prompt). The loop should auto-cancel when the decision framework returns SHIP or max iterations are reached. See `commands/create.md` for interval recommendations per cycle type.

### Step 7: Finalize

Deliver:
- The final frontend code (the best-scoring iteration)
- **report.md** — Iteration history with scores, decisions, and key pivots
- **scores.json** — Structured scoring data across all iterations

## Artifacts

All artifacts write to the working directory or a `harness-output/` subdirectory:

| Artifact | Written by | When |
|----------|-----------|------|
| `harness-output/spec.md` | Planner | Step 1 |
| `harness-output/sprint-contract.md` | Planner | Step 1 |
| `harness-output/design-description-{N}.md` | Design Agent | Each step 2 |
| `harness-output/serve.json` | Impl. Agent | Each step 3 |
| `harness-output/site/` | Impl. Agent | Each step 3 |
| `harness-output/scores.json` | Evaluator | Each step 4 |
| `harness-output/critique-{N}.md` | Evaluator | Each step 4 |
| `harness-output/report.md` | Orchestrator | Step 7 |

### Version Control

`harness-output/` MUST be tracked by version control — do NOT add it to `.gitignore`. Tracking serves two purposes:

1. **Survives VCS operations.** jj working-copy switches and git branch checkouts wipe untracked/ignored files. Tracked artifacts persist in each change/branch.
2. **Tracks progression.** Committed iterations create a reviewable design journey — score evolution, pivot decisions, what worked and what didn't.

The orchestrator commits artifacts after each iteration cycle (see `commands/create.md` for the commit protocol). Harness artifacts are excluded from main-branch PRs — they stay on feature branches as development records.

## Section Decomposition Mode

The harness supports two modes of operation:

### Full-Page Mode (Default)

The Design Agent creates a single design description for the entire page. The Implementation Agent builds the whole page from that description. Best for:
- Single-section pages (hero-only, landing pages)
- Pages where cross-section visual coherence is the primary concern
- Simple layouts with 1-3 sections

### Section Decomposition Mode (Recommended for Multi-Section Pages)

Each section cycles through Design → Implement → Evaluate independently before an integration pass. Best for:
- Multi-section pages (5+ sections)
- Pages where each section has a distinct purpose (hero, features, testimonials, pricing)
- Ambitious designs where each section should have its own creative moment

**Section mode workflow:**
1. Planner identifies sections and their purposes in the spec
2. For each section (in visual order):
   a. Design Agent creates a design description for JUST that section (receives: section spec and brand brief only — no adjacent section screenshots, to prevent cross-section anchoring)
   b. Implementation Agent builds that section
   c. Evaluator scores that section in isolation
3. Integration pass: Evaluator reviews the full composed page for cross-section coherence
4. Design Agent creates an integration design description addressing any coherence issues
5. Implementation Agent applies integration fixes
6. Normal iteration loop continues on the full page

Section decomposition is not about context management — it is about **protecting creative freedom**. Each section gets its own creative moment unconstrained by the implementation of adjacent sections. This remains valuable even as model context windows grow, because the constraint is cognitive (anchoring to what exists nearby) not technical (running out of tokens).

## Standalone Usage

The harness works standalone without any brand toolkit. For standalone use:
- Prompt the `/design-studio:create` command with your requirements
- The planner generates the spec and aesthetic direction from scratch
- No brand artifacts needed — the Design Agent chooses its own creative direction

## Prerequisites

- **Chrome browser automation** (claude-in-chrome MCP) — required for live evaluation. The evaluator must verify Chrome MCP availability before starting: `mcp__claude-in-chrome__tabs_context_mcp` should return the current browser state. If Chrome MCP is unavailable, HALT — do not fall back to code-only review. The entire harness depends on live visual evaluation; code-only review cannot judge design quality or originality, making the loop meaningless.
- **File server** (`npx serve` or framework dev server) — required to render pages. The evaluator must verify the server is responding (retry navigation 3 times with 2s delays) before proceeding. Kill the server process after each evaluation cycle to avoid port conflicts across iterations.

## Configuration

These are defaults the orchestrator should respect. They are documented here as the authoritative source — the decision framework in `modules/iteration.md` references these thresholds.

| Setting | Default | Description |
|---------|---------|-------------|
| `maxIterations` | 8 | Maximum generate-evaluate loops (increase to 12 for ambitious designs) |
| `shipThreshold` | 7.0 | All criteria must meet this score for auto-ship |
| `convergenceThreshold` | 6.5 | Weighted avg must meet this for plateau-SHIP (below this, plateau triggers PIVOT) |
| `slowProgressThreshold` | 5.0 | Weighted avg below this after iteration 3 triggers PIVOT |
| `viewports` | `[1440, 390]` | Pixel widths for Chrome MCP screenshots |
| `humanReview` | `false` | Pause for human approval after planning and before shipping |
| `zoneEvaluation` | `true` | Per-zone zoomed evaluation (always on — catches subsystem issues that full-page scoring averages away) |
| `adversarialGate` | `true` | Mandatory pre-scoring technical checks that hard-cap scores on failure |

## Zone-Based Evaluation vs Section Decomposition

Two complementary systems operate at different levels:

- **Zone-based evaluation** = per-visual-component scoring within a single evaluation pass. Always on. The evaluator identifies zones (header, hero, content sections, graphs/charts, sidebar, footer), captures each at 2x zoom, and scores independently. Catches text overlaps, graph clipping, sidebar overflow, and other subsystem problems that full-page scoring averages away.

- **Section decomposition** = per-section creative isolation with separate design-then-implement-then-evaluate cycles. Optional, for multi-section pages. Protects creative freedom by preventing the design agent from anchoring to adjacent sections.

These are **complementary**: zone-based evaluation runs within every evaluation pass (including during section decomposition). Section decomposition controls the creative loop granularity; zone evaluation controls scoring granularity.

## Adversarial Testing Gate

Before scoring, the evaluator runs a mandatory adversarial gate — a set of "try to break it" technical checks:

1. **Text overflow/clipping** — scroll all containers, check for hidden overflow text
2. **Element overlap** — check for overlapping elements that obscure content
3. **Responsive breakage** — resize to 390px, check for horizontal scrollbars, broken layouts
4. **Console errors** — check browser console for JS errors, failed resource loads
5. **Broken interactions** — click every interactive element, verify expected behavior

Gate failures impose hard score caps (e.g., text clipping caps craft at 5, console errors cap functionality at 5). This prevents evaluators from optimizing for visual impression while missing rendering bugs.

## Modules

Detailed knowledge is in `modules/`:
- **planning.md** — Prompt expansion, spec structure, sprint contract format, creative tensions
- **evaluation.md** — Scoring rubric, live evaluation protocol, zone-based evaluation, adversarial gate, evaluator failure modes
- **iteration.md** — Decision framework, convergence detection, pivot mechanics, score tracking
- **generation.md** — Implementation agent principles, design description execution, anti-patterns
- **meta.md** — How to improve the harness itself, lessons from real-world tuning
