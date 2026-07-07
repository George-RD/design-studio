# Design Studio

A 4-agent design-evaluate-iterate harness for Claude Code that produces distinctive, production-grade frontends by defeating code-anchoring bias.

## How It Works

Design Studio splits frontend creation into four isolated agents, mirroring how real design studios work:

| Agent | Role | Why Separated |
|-------|------|---------------|
| **Planner** | Expands your prompt into a full spec with creative tensions | Prevents cascading errors from vague requirements |
| **Design Agent** | Creates visual direction from screenshots + critique — never sees code | Code-anchoring bias: seeing existing code constrains creative vision |
| **Implementation Agent** | Faithfully translates design descriptions into working code | Executes the vision without second-guessing creative direction |
| **Evaluator** | Interacts with the live rendered page via Chrome MCP, scores against 4 weighted criteria | Cannot be "captured" by implementation confidence; judges only the user experience |

The loop: **Plan → Design → Implement → Evaluate → Decide (REFINE/PIVOT/SHIP) → Loop**.

Each iteration pushes past safe AI defaults. The evaluator uses zone-based scoring and an adversarial testing gate to catch subsystem defects that whole-page scoring averages away.

## Prerequisites

- **Claude Code** installed and authenticated
- **Chrome browser** with the `claude-in-chrome` MCP server running (required for live visual evaluation)

## Installation

### From the Community Marketplace

```bash
claude plugin marketplace add anthropics/claude-plugins-community
claude plugin install design-studio
```

### From GitHub (direct)

```bash
claude plugin install https://github.com/George-RD/design-studio
```

### From a local directory (for development)

```bash
claude --plugin-dir ./design-studio
```

After installing, run `/reload-plugins` in Claude Code to load the plugin.

## Quick Start

```
/design-studio:create a landing page for a boutique coffee roastery
```

The harness will:
1. **Plan** — Expand your prompt into a full spec with aesthetic direction and creative tension
2. **Design** — The Design Agent creates a prose design description (never sees code)
3. **Implement** — The Implementation Agent builds the frontend from the design description
4. **Evaluate** — The Evaluator interacts with the live page via Chrome MCP, scores against 4 criteria, and writes structured critique
5. **Decide** — REFINE (improve current direction), PIVOT (abandon and reimagine), or SHIP (quality threshold met)
6. **Loop** — Repeat until convergence (typically 5-8 iterations)

All artifacts write to `harness-output/` in your working directory.

## Commands

| Command | Description |
|---------|-------------|
| `/design-studio:create <prompt>` | Run the full harness loop to build a frontend |

## Architecture

```
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

## Scoring Criteria

The evaluator scores on 4 criteria with weighted averages:

| Criterion | Weight | What It Measures |
|-----------|--------|------------------|
| Design Quality | 2x | Cohesion, mood, intentionality |
| Originality | 2x | Custom decisions vs template defaults |
| Craft | 1x | Typography, spacing, alignment, responsive |
| Functionality | 1x | Can users accomplish their goals? |

Design quality and originality are weighted higher because Claude already performs well on technical competence by default.

## Methodology

Based on the Anthropic Labs blog post "Harness design for long-running application development" (Rajasekaran, March 2026), extended with:

- **4-agent architecture** — Splits the original Generator into a Design Agent (visual-only, never sees code) and Implementation Agent (faithful executor), defeating code-anchoring bias
- **Zone-based evaluation** — Per-visual-component scoring at 2x zoom prevents subsystem defects from hiding behind a passing whole-page score
- **Adversarial testing gate** — Mandatory pre-scoring technical checks (overflow, readability, interactions, responsive) that hard-cap scores on failure
- **Section decomposition** — Per-section creative isolation for multi-section pages, protecting each section's creative freedom

## License

MIT
