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
version: 1.0.0
---

# Design Studio

A multi-agent harness that produces distinctive, production-grade frontends by separating design vision from code implementation and evaluation. Four specialized agents — Planner, Evaluator, Design Agent, and Implementation Agent — each operate in isolation to defeat code-anchoring bias and push past safe AI defaults. When a direction ships, the harness codifies it into a reusable design system: `design-dna.md`, `tokens.css`, and an installable skill template.

## Why This Exists

Without this harness, AI-generated frontends converge on safe, predictable layouts — technically functional but visually unremarkable. Three problems cause this:

1. **Self-evaluation is broken for subjective tasks.** When an agent evaluates its own design, it confidently praises mediocre output. No binary correctness check exists for "is this design good?"
2. **Code-anchoring kills creativity.** An LLM that sees the current implementation before redesigning will tweak CSS instead of imagining a better layout. The strongest models are the most consistently anchored.
3. **Single-agent loops reward incrementalism.** The same model proposes, implements, and scores; it has no incentive to take creative risks.

The harness fixes all three by splitting the creative process into isolated agents: an evaluator that judges only the rendered output, a design agent that creates visual direction without ever seeing code, and an implementation agent that faithfully executes design descriptions into working code. This mirrors how design studios actually work — art directors create the vision, developers implement it.

## Code-Anchoring Bias

The most important architectural insight behind the 4-agent split. Research confirms that reading existing code before generating new designs anchors the LLM's creativity. The model shifts from "what should this look like?" to "what can I change in the existing implementation?" — producing incremental CSS tweaks instead of bold redesigns.

- **arXiv:2412.06593** — Demonstrates that anchoring bias in LLMs is systematic, and stronger models are MORE consistently influenced (not less). The fix is preventing exposure to the anchor entirely.
- **arXiv:2410.02837** — Finds that separating critique generation from implementation improves both quality and originality; the design-evaluate loop is a direct application.
- **arXiv:2501.03259** — Shows that self-evaluation in LLMs is unreliable for aesthetic tasks; external judges are essential.
- **HClaude Code** — An AI-native creative tool that uses multiple Claude instances with specific roles to break design loops. The Design Studio harness generalizes this pattern to any frontend project.

The fix: the Design Agent never sees code. It receives only screenshots, the evaluator's visual critique, and the spec. Its output is a design description — a prose document describing what the page should look like, not how to implement it. The Implementation Agent then receives this description alongside the existing code and faithfully executes it.

## Architecture

```text
┌─────────┐     ┌─────────────┐     ┌──────────┐     ┌───────────┐
│ Planner │────▶│  Design Agent │──▶│ Builder  │──▶│ Evaluator │
└─────────┘     └─────────────┘     └──────────┘     └─────┬─────┘
                                                             │
                              ┌──────────────────────────────┘
                              ▼
                       ┌────────────┐
                       │   Decide   │
                       └─────┬──────┘
                             │
            REFINE/PIVOT ────┴──── SHIP
                 │                    │
                 ▼                    ▼
            Design Agent           Codify
                                  (design-dna.md,
                                   tokens.css,
                                   skill template)
                                     │
                                     ▼
                                  Finalize
```

Four agents, each with a distinct role:

| Agent | Role | Why Separated |
|-------|------|---------------|
| **Planner** | Expands the user's terse prompt into a full spec with creative tension and anti-goals. | Sets the creative frame without anchoring to any implementation. |
| **Design Agent** | Writes prose art-director briefs describing layout, type, color, rhythm, motion, and atmosphere. | Never sees code; produces visual direction independent of what is implementable. |
| **Implementation Agent (Builder)** | Executes the design description into working code. | Receives code and design separately; forced to translate rather than invent. |
| **Evaluator** | Serves the rendered page, captures screenshots, runs an adversarial gate, and scores the output. | Judges only the visual result; cannot be swayed by implementation effort. |

In `workflow.yaml` the Implementation Agent is referred to as `Builder`, the Design Agent as `DesignAgent`, and the other two agents as `Planner` and `Evaluator`. This keeps the machine-readable definition aligned with the architecture while giving orchestrators a deterministic role roster.

## The Workflow

```text
Plan ──▶ Design ──▶ Implement ──▶ Evaluate ──▶ Decide
                              ▲                   │
                              └────── Loop ───────┘
                                       │
                                       SHIP
                                        ▼
                                     Codify
                                        ▼
                                     Finalize
```

### Machine-readable workflow definition

The full iteration loop is encoded in `skills/design-studio/workflow.yaml`. It defines, for each step:

- The responsible agent (`Planner`, `DesignAgent`, `Builder`, `Evaluator`, or `orchestrator`).
- Required inputs and isolated context.
- The exact prompt each agent receives.
- Outputs and termination conditions that drive the next step.
- The decision table, loop control, and the new `codify` step that runs before finalize when the design ships or the budget exhausts.
- A `capabilities` block describing what a host harness must provide and a `schemas` block defining the exact `scores.json` structure.

An OMP or any other harness can run this workflow deterministically by:

1. **Parsing** `workflow.yaml` to load the agent roster, default thresholds (`shipThreshold`, `convergenceThreshold`, `slowProgressThreshold`, `maxIterations`), and step list.
2. **Spawning agents** using the harness's subagent mechanism (e.g., Claude Code Agent tool, OMP `task` tool, or equivalent) with the system prompts in `agents/` and the per-step prompts in `workflow.yaml`.
3. **Enforcing isolation** — never passing code to the Design Agent or Evaluator.
4. **Driving the loop** until the decision framework returns `SHIP`, `PIVOT`, or `maxIterations` is reached, then running the `codify` step before finalizing.

Because the prompts, agent boundaries, and decision rules are all declared in one file, every compliant harness produces the same sequence of steps and the same decision outcomes for the same inputs.

### Step 1: Plan

The planner takes a 1-4 sentence user prompt and produces:

- **harness-output/spec.md** -- Full product specification: purpose, audience, features, technical stack, aesthetic direction with creative tensions. Scope and high-level design, NOT granular implementation details (avoiding cascading errors).
- **harness-output/sprint-contract.md** -- Testable success criteria and explicit anti-goals for the evaluator.

The planner must specify a **creative tension** — not just an aesthetic label. A single label ("brutalist", "editorial") produces recognizable but generic output. A creative tension forces original solutions: "Brutalist WITH ornamental flourishes", "Minimalist BUT textural and warm." See `modules/planning.md` for the creative tension methodology.

The planner identifies opportunities to weave ambitious features throughout the spec — AI features, animations, spatial experiences, interactive elements. The planner biases toward distinctiveness, not safety.

See `modules/planning.md` for the planning methodology.

### Step 2: Design

The **Design Agent** — a separate agent that never sees code — receives:
- Screenshots from the evaluator (desktop + mobile + zone captures) — on iteration 1, no screenshots exist yet; the spec's aesthetic direction and creative tension serve as the creative seed
- The evaluator's structured critique from the previous iteration
- The planner's spec and sprint contract

On **iteration 1**, the Design Agent works from the spec alone — no evaluation data exists yet. It MUST produce three divergent one-paragraph concept directions, select the boldest viable one, and expand only the winner into the full description (record the two rejected concepts in one line each at the top of `design-description-1.md`). On subsequent iterations, it works from real evaluation feedback.

The Design Agent produces a **prose design description** — natural-language specification of layout geometry, typography direction, color relationships, spatial rhythm, motion intent, and atmospheric qualities. It thinks like an art director reviewing comps, not a developer reading code.

This separation defeats code-anchoring bias: research shows that when generative models see existing implementations before creating, they anchor to "what can I tweak" instead of "what should this be" — and stronger models are MORE affected.

The Design Agent writes to `harness-output/design-description-{N}.md`.

See `modules/generation.md` for design and implementation principles.

### Step 3: Implement

The **Implementation Agent** receives:
- The Design Agent's prose design description (from step 2)
- The planner's spec and sprint contract
- The existing code (if REFINE) or a fresh start (if PIVOT)

The Implementation Agent faithfully translates the design description into working code — HTML/CSS/JS, React, Vue, or whatever the spec calls for. It does NOT second-guess the Design Agent's creative decisions. It self-commits via git after each implementation pass.

See `modules/generation.md` for implementation guidance.

### Step 4: Evaluate Live

The evaluator — a **separate agent** — interacts with the live rendered page using browser automation per the Browser Operations Contract:

1. **Serve the page** (dev server, file server, or inject into harness)
2. **Capture full-page screenshots** at the configured viewports (default 1440px and 390px)
3. **Identify visual zones** and capture each at 2x zoom
4. **Run the adversarial gate** before scoring: overflow checks, overlap checks, responsive breakage, console errors, broken interactions
5. **Score** against the four rubric criteria and record `gateFailures` and `actualViewports` in `harness-output/scores.json`: designQuality, originality, craft, functionality

The evaluator does NOT see any code. It sees only the rendered output, the spec, the sprint contract, and the design description (if one exists from the prior iteration). This prevents sympathy for implementation effort and forces judgment based solely on the user experience.

See `modules/evaluation.md` for the scoring rubric and evaluation protocol.

### Step 5: Decide

The decision uses scores from step 4, which evaluated the code JUST BUILT in step 3. SHIP means the current version met the threshold — no untested changes exist between evaluation and the decision.

Based on score trends across iterations:

| Pattern | Decision | Action |
|---------|----------|--------|
| Originality ≤ 4 at iteration ≥ 2 | **PIVOT** | Template pattern detected; refinements won't fix structural unoriginality. |
| Originality ≤ 5 at iteration ≥ 4 | **PIVOT** | Direction is fundamentally conventional. |
| Originality stagnates (< 6) for 2 iterations | **PIVOT** | Refinement is not reaching originality. |
| All criteria ≥ 7.0 | **SHIP** | Quality threshold met; overrides all other rules. |
| Weighted average improved ≥ 0.5 | **REFINE** | Positive trajectory; continue current direction. |
| Weighted average plateau ≥ 6.5 for 2+ iterations | **SHIP** | Converged at acceptable quality. |
| Weighted average plateau < 6.5 for 2+ iterations | **PIVOT** | Converged at unacceptable quality. |
| Weighted average < 5.0 at iteration ≥ 3 | **PIVOT** | Not improving fast enough. |
| Weighted average declines 2 iterations in a row | **PIVOT** | Direction is failing. |
| Iteration 1 (unless threshold met) | **REFINE** | First iteration always refines. |
| Iteration ≥ maxIterations | **SHIP** | Budget exhausted; deliver the best-scoring iteration. |

See `modules/iteration.md` for the decision framework.

The decision routes differently across the agents:
- **REFINE**: The Design Agent receives the critique and screenshots with instruction to improve the current direction. The Implementation Agent then executes the updated design description.
- **PIVOT**: The Design Agent invents a fresh visual direction that differs from ALL previously attempted concepts, the Implementation Agent starts from a clean state, and the evaluator begins scoring the new direction.
- **SHIP**: The orchestrator runs the **Codify** step (Step 7), then **Finalize** (Step 8).

### Step 6: Loop

Return to step 2 (Design) with the decision and critique. The agents receive:
- On REFINE: the critique + instruction to improve the current direction
- On PIVOT: the critique + instruction to invent a fresh direction

The loop continues until SHIP is reached or `maxIterations` is exhausted. The default maximum is 8 iterations (increase to 12 for ambitious full-page designs). The source blog reports 5-15 iterations as typical for complex designs.

**Automation:** If your harness has a recurring-loop command (e.g., Claude Code `/loop 3m ...`), use it to automate the cycle; otherwise the orchestrator repeats Design → Implement → Evaluate until a terminate condition. The loop should auto-cancel when the decision framework returns SHIP or max iterations are reached.

See `commands/create.md` for interval recommendations per cycle type.

### Step 7: Codify

When the decision is SHIP or the iteration budget is exhausted, the orchestrator runs the `codify` step BEFORE finalize. This extracts a reusable design system from the winning iteration, in strict isolation:

1. **DesignAgent** writes `harness-output/design-system/design-dna.md` from the winning design description, spec, and critique history (still never seeing code). Required sections in order:
   - Name & essence
   - Principles (numbered)
   - Aesthetic & creative tension
   - Colour language
   - Typography
   - Spatial rhythm
   - Signature motif(s)
   - Motion
   - Voice & tone
   - Applying the system
   - Anti-goals
   - Provenance
2. **Builder** extracts `harness-output/design-system/tokens.css` from the shipped site. This is the canonical design-token file; the site references the same values, and any repo copy is a vendored consumer synced from this master.
3. **Orchestrator** instantiates `templates/design-system-skill/` into `harness-output/design-system/skill/<project>-design/` by filling placeholders and copying `design-dna.md` + `tokens.css` in, producing an installable, harness-portable design-system skill.

### Step 8: Finalize

Deliver:
- The final frontend code (the best-scoring iteration)
- `harness-output/design-system/design-dna.md`
- `harness-output/design-system/tokens.css`
- `harness-output/design-system/skill/<project>-design/` (the installable design-system skill)
- `harness-output/report.md` — iteration history, decisions, pivots, final scores, and design-system deliverable summary

If the best-scoring iteration is not the latest, the report explains why.

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
| `harness-output/design-system/design-dna.md` | Design Agent | Step 7 (Codify) |
| `harness-output/design-system/tokens.css` | Builder | Step 7 (Codify) |
| `harness-output/design-system/skill/<project>-design/` | Orchestrator | Step 7 (Codify) |
| `harness-output/report.md` | Orchestrator | Step 8 |

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

- **Browser automation** — required for live evaluation. The evaluator must satisfy the Browser Operations Contract using any available adapter: claude-in-chrome MCP, chrome-devtools MCP, Playwright MCP, Headless Chrome CDP fallback, or a harness-native browser tool (e.g., OMP's `browser` tool). At evaluation start, probe availability with a harmless call (tab context/list), use the first available adapter for the whole pass, and never mix adapters mid-pass. HALT only if NO browser automation exists at all. NEVER fall back to code-only review. See `modules/evaluation.md` for the full contract.
- **File server** (`npx serve` or framework dev server) — required to render pages. The evaluator must verify the server is responding (retry navigation 3 times with 2s delays) before proceeding. Kill the server process after each evaluation cycle to avoid port conflicts across iterations.

## Harness Portability

`workflow.yaml` is the harness-neutral source of truth: it declares agents, prompts, inputs, outputs, transitions, loop control, capabilities, and the exact `scores.json` schema. Any harness that can provide the required capabilities can run the same workflow.

Claude Code specifics are labeled examples with generic equivalents:
- **Agent tool** → your harness's subagent mechanism (Claude Code Agent tool, OMP `task` tool, or equivalent). Spawn agents with per-agent context isolation.
- **`/loop`** → if your harness has a recurring-loop command (e.g., Claude Code `/loop 3m ...`); otherwise the orchestrator repeats Design → Implement → Evaluate until a terminate condition.
- **`agents/*.md`** → usable directly as subagent system prompts in any harness; copy or reference them as system prompts for the corresponding subagent mechanism.

Port 3333 stays the default static-file-server port, but `harness-output/serve.json` is authoritative for each iteration.

## Configuration

These are defaults the orchestrator should respect. They are documented here as the authoritative source — the decision framework in `modules/iteration.md` references these thresholds.

| Setting | Default | Description |
|---------|---------|-------------|
| `maxIterations` | 8 | Maximum generate-evaluate loops (increase to 12 for ambitious designs) |
| `shipThreshold` | 7.0 | All criteria must meet this score for auto-ship |
| `convergenceThreshold` | 6.5 | Weighted avg must meet this for plateau-SHIP (below this, plateau triggers PIVOT) |
| `slowProgressThreshold` | 5.0 | Weighted avg below this after iteration 3 triggers PIVOT |
| `viewports` | `[1440, 390]` | Pixel widths for evaluation screenshots (see Browser Operations Contract) |
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

Detailed knowledge is in `modules/`, and the executable workflow is encoded in `workflow.yaml`:

- **planning.md** — Prompt expansion, spec structure, sprint contract format, creative tensions
- **evaluation.md** — Scoring rubric, live evaluation protocol, zone-based evaluation, adversarial gate, evaluator failure modes
- **iteration.md** — Decision framework, convergence detection, pivot mechanics, score tracking
- **generation.md** — Implementation agent principles, design description execution, anti-patterns
- **meta.md** — How to improve the harness itself, lessons from real-world tuning
- **workflow.yaml** — Machine-readable workflow definition: agents, prompts, inputs/outputs, transitions, loop constraints, capabilities, schemas, and the codify step
