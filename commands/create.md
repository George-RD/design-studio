---
name: create
description: Create a distinctive frontend using the generate-evaluate-iterate harness. Takes a prompt describing what to build and runs the full harness loop with separated evaluation.
argument-hint: "<description of the frontend to build>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
  - WebFetch
  - WebSearch
---

# Design Studio: Create

You are the **harness orchestrator**. Your job is to run the full generate-evaluate-iterate loop to produce a distinctive, production-grade frontend from the user's prompt.

## Input

The user's prompt: `$ARGUMENTS`

## Execution

Follow the workflow defined in the `design-studio` skill (SKILL.md). Execute each phase:

### Phase 1: Plan

Expand the user's prompt into a full specification. Write:
- `harness-output/spec.md` — Product spec with purpose, audience, features, stack, and aesthetic direction
- `harness-output/sprint-contract.md` — Testable success criteria the evaluator will use

Be ambitious in the spec. Identify opportunities for distinctive design choices, unexpected interactions, and memorable moments. Do not play it safe.

### Phase 2-6: Design-Implement-Evaluate Loop

For each iteration:

1. **Design**: Spawn the `design-agent` (from this plugin's agents/) to:
   - Receive the evaluator's screenshots (desktop + mobile + zone captures) and structured critique — on iteration 1, no evaluation data exists yet; the spec's aesthetic direction and creative tension serve as the creative seed
   - Receive the spec and sprint contract — NOT the source code
   - Produce a **prose design description** (`harness-output/design-description-{N}.md`) specifying layout geometry, typography direction, color relationships, spatial rhythm, motion intent, and atmospheric qualities
   - The Design Agent never sees code — this isolation defeats code-anchoring bias

2. **Implement**: Spawn an implementation agent (`run_in_background: false`) to build/update the frontend. The implementation agent receives:
   - The Design Agent's prose design description (from step 1)
   - The existing code (or empty on first pass)
   - The spec and sprint contract
   - The `generation.md` module principles
   - Any `designFlags` from the previous iteration's critique (see step 3 output contract)
   - It faithfully translates the design description into working code

   **Implementation output contract:** The implementation agent MUST produce:
   - The built/updated frontend code
   - A `harness-output/serve.json` manifest so the evaluator knows how to serve and access the page:
     ```json
     { "type": "static|vite|next", "path": "./harness-output/site", "command": "npx serve ./harness-output/site -l 3333", "port": 3333 }
     ```
     The evaluator reads `serve.json` to start the server and navigate to the correct URL. Without this contract, the handoff fails nondeterministically across stacks.
   - Any `/* DESIGN-FLAG: ... */` comments placed inline in the code where a design instruction was unimplementable or ambiguous (per `generation.md` protocol)
   - A `harness-output/design-flags-{N}.json` manifest listing all DESIGN-FLAGs emitted during this iteration:
     ```json
     {
       "designFlags": [
         {"note": "/* DESIGN-FLAG: particle dissolve effect not achievable in pure CSS */", "location": "hero.tsx:42"}
       ]
     }
     ```
     The orchestrator reads this manifest after implementation completes and passes the flags to the Design Agent as explicit implementation constraints in the next iteration's input (step 1). This keeps the evaluator free from scanning source code — it remains visual-only.

3. **Evaluate**: Spawn the `evaluator` agent (from this plugin's agents/) to:
   - Serve the page and take Chrome MCP screenshots (`mcp__claude-in-chrome__computer`, `mcp__claude-in-chrome__navigate`, `mcp__claude-in-chrome__resize_window`)
   - **Full-page screenshot** at 1440px and 390px widths
   - **Zone identification** — identify visual zones (header, hero, content sections, graphs/charts, sidebar, footer)
   - **Per-zone zoomed screenshots** — capture each zone at 2x zoom for detailed evaluation
   - **Adversarial gate** — run mandatory pre-scoring technical checks: text overflow/clipping, element overlap, responsive breakage, console errors (`mcp__claude-in-chrome__read_console_messages`), broken interactions. Gate failures hard-cap scores.
   - **Per-zone scoring** — score each zone against the 4 criteria. Zones scoring below 6 on any criterion trigger mandatory critique entries.
   - **Whole-page scoring** — score the full page, then apply zone minimums: craft and functionality use min(whole-page, worst-zone).
   - Interact with the live page — click, scroll, hover, test navigation
   - Write structured critique to `harness-output/critique-{N}.md` (including zone-specific issues)
   - Write scores to `harness-output/scores.json`
   - The evaluator does NOT scan source code or extract DESIGN-FLAGs — that responsibility belongs to the Implementation Agent (see step 2 output contract). The evaluator judges only the rendered visual experience.

   The evaluator agent has Chrome MCP tool access via its agent definition (`agents/evaluator.md`) — it uses `claude-in-chrome` MCP tools directly for all browser interaction (screenshots, navigation, resize, interaction testing, console checking). The orchestrator spawns the evaluator via the Agent tool; the evaluator's own tool access includes all `mcp__claude-in-chrome__*` tools.

4. **Decide**: Apply the iteration decision framework from `iteration.md`:
   - REFINE if scores are improving
   - PIVOT if stuck below threshold
   - SHIP if scores meet threshold or plateau at acceptable level

   Because Evaluate (step 3) scores the code JUST BUILT in Implement (step 2), the decision always reflects the current state. SHIP means the evaluated version met the threshold — no untested changes exist.

5. **Loop** back to Design, or proceed to Finalize.

### Automated Iteration with /loop

For hands-off iteration, use the `/loop` command to run the Design-Implement-Evaluate cycle on a recurring interval:

```bash
/loop 3m Design the next iteration using the design-agent with the critique, implement the design description, evaluate the current build at harness-output/site, then apply the decision framework. Report the iteration number, weighted score, and decision (REFINE/PIVOT/SHIP).
```

**Cancel conditions** — the loop MUST be canceled (`/loop cancel` or Ctrl+C) when any of these criteria are met:
- **SHIP**: All 4 criteria ≥ 7.0, or converged at weighted avg ≥ 6.5
- **Max iterations reached**: Default 8 (12 for ambitious designs)
- **Pivot budget exhausted**: Default 2 full pivots — ship the best-scoring iteration
- **User interrupt**: The user wants to review or redirect

**Recommended intervals by cycle type:**
| Cycle | Interval | Rationale |
|-------|----------|-----------|
| Full-page iteration | 3-5m | Each cycle involves 3 agent spawns |
| Section decomposition (per section) | 2-3m | Smaller scope, faster cycles |
| Integration pass | 3m | Full-page evaluation but lighter design pass |
| CodeRabbit review polling | 2m | Waiting for external review |

**Loop body should always:**
1. Read `harness-output/scores.json` for the current state
2. Run one complete Design → Implement → Evaluate cycle
3. Apply the decision framework from `iteration.md`
4. Report: iteration N, weighted avg, decision, and whether to continue or cancel
5. If decision is SHIP → cancel the loop and proceed to Finalize

### Phase 7: Finalize

Write `harness-output/report.md` summarizing:
- Iteration count and duration
- Score progression across iterations
- Key decisions (pivots, refinements)
- Final scores
- What made the final design distinctive

Present the final output to the user with a brief summary of the journey.

## Version Control

`harness-output/` MUST be tracked by version control (git/jj), NOT gitignored. This serves two purposes:

1. **Survives VCS operations.** When jj switches working copies or git switches branches, tracked files are preserved in each change/branch. Gitignored files get wiped — losing all iteration state mid-loop.
2. **Tracks progression.** Committed artifacts let you review the design journey: how scores evolved, what pivots looked like, which iteration produced the best work.

### Per-Iteration Commits

After each Design → Implement → Evaluate cycle, the orchestrator MUST commit the `harness-output/` artifacts:

```text
harness: iteration N — [REFINE|PIVOT|SHIP] (weighted avg X.X)
```

This creates a progression trail: each commit captures the spec, design description, implementation, critique, and scores for that iteration. You can diff between iterations to see exactly what changed.

### Excluding from Main Branch

Harness artifacts are development-time progression records — they should not be merged to the main branch. Before creating a PR:

- **jj:** Use `jj split` to separate `harness-output/` into its own change that stays on the working branch but is not included in the PR's bookmark
- **git:** Remove `harness-output/` from the final commit(s) before pushing the PR branch, or add it to `.gitignore` only on the main branch

The shipped frontend code (the final `harness-output/site/` contents) should be moved to its permanent location in the project before the PR. The harness artifacts (specs, critiques, scores, design descriptions) stay on the feature branch as a record.

## Important

- **Never skip the evaluator.** The entire point of this harness is separated evaluation.
- **Never pass code to the Design Agent.** The entire point of the 4-agent split is defeating code-anchoring bias. If the Design Agent sees code, it will anchor to implementation details instead of thinking visually.
- **The evaluator must use Chrome browser automation** (claude-in-chrome MCP) to interact with the live page. Code review alone cannot judge design quality. The evaluator needs access to: `mcp__claude-in-chrome__computer`, `mcp__claude-in-chrome__navigate`, `mcp__claude-in-chrome__resize_window`, `mcp__claude-in-chrome__read_page`, `mcp__claude-in-chrome__javascript_tool`, `mcp__claude-in-chrome__read_console_messages`, `mcp__claude-in-chrome__tabs_context_mcp`, `mcp__claude-in-chrome__tabs_create_mcp`.
- **Zone evaluation is mandatory.** The evaluator must identify zones and score per-zone, not just whole-page. The adversarial gate must run before scoring.
- **Respect pivot decisions.** When the framework says pivot, the Design Agent must abandon the current visual approach entirely — not make incremental tweaks. The Implementation Agent starts from scratch.
- **Track scores across iterations.** The decision framework depends on score trends, not individual scores.
- **The Implementation Agent executes faithfully.** It does not second-guess the Design Agent's creative choices. If the design description says "break the grid," the implementation breaks the grid.
