# Iteration Module

The refine/pivot/ship decision framework, convergence detection, and iteration management.

## Decision Framework

After each evaluation, the orchestrator must decide: **REFINE**, **PIVOT**, or **SHIP**.

This is a mechanical decision based on score data, not a judgment call. The framework removes ambiguity.

### Decision Table

| Condition | Decision | Rationale |
|-----------|----------|-----------|
| Originality ≤ 4 after iteration 2 | **PIVOT** | Template pattern detected early — CSS refinement won't fix a structural problem |
| All 4 criteria ≥ 7.0 | **SHIP** | Quality threshold met |
| Weighted average improved ≥ 0.5 from last iteration | **REFINE** | Trajectory is positive |
| Weighted average within ±0.5 for 2 consecutive iterations AND weighted avg ≥ 6.5 | **SHIP** | Converged at acceptable quality |
| Weighted average within ±0.5 for 2 consecutive iterations AND weighted avg < 6.5 | **PIVOT** | Converged at unacceptable quality |
| Weighted average declined for 2 consecutive iterations | **PIVOT** | Direction is failing |
| Weighted average < 5.0 after iteration 3 | **PIVOT** | Not improving fast enough |
| Iteration count = maxIterations | **SHIP** | Budget exhausted — deliver best iteration |
| Iteration 1 (no prior data) | **REFINE** | Always refine after first evaluation (unless quality threshold already met) |

### Rule Priority

Rules are evaluated top-to-bottom. The first matching rule wins. The early pivot trigger (originality ≤ 4 after iteration 2) is checked first because it catches structural problems before the harness wastes iterations on CSS polish. The quality threshold (all 4 criteria ≥ 7.0 → SHIP) is checked second and overrides all remaining rules, including the iteration 1 default.

### Tie-Breaking

When conditions conflict (e.g., one criterion is ≥ 7.0 but the weighted average declined):
1. The quality threshold rule (all ≥ 7.0) takes absolute priority
2. Weighted average trend takes priority over individual criteria
3. PIVOT takes priority over REFINE when quality is below convergenceThreshold (6.5)
4. SHIP takes priority over REFINE when the user has waited 6+ iterations

### Originality Urgency

Originality is the canary in the coal mine. A design that scores well on craft and functionality but poorly on originality is executing well on the wrong idea — more iterations will polish the surface without fixing the core problem.

**Aggressive PIVOT triggers for originality:**

| Condition | Decision |
|-----------|----------|
| Originality ≤ 4 after iteration 2 | **PIVOT** — template pattern detected early |
| Originality ≤ 5 after iteration 4 | **PIVOT** — direction is fundamentally conventional |
| Originality stagnant (±0.5) for 2 iterations while below 6 | **PIVOT** — refinement is not reaching originality |

If originality hasn't crossed 5.0 by iteration 3, the direction is likely wrong, not the execution. The explicit PIVOT trigger fires at iteration 4 (originality ≤ 5) — iteration 3 is a warning signal. CSS tweaks, spacing adjustments, and hover states cannot transform a generic layout into a distinctive one.

**Originality overrides trajectory.** When originality is below 5, it overrides positive trajectory in other criteria. A rising weighted average driven by craft and functionality improvements masks the real problem — the design looks and feels like every other AI-generated page.

A well-executed generic design (craft 8, originality 4) is worse than a rough distinctive one (craft 5, originality 7). The harness can always polish craft in later iterations, but it cannot inject originality into a fundamentally conventional structure through refinement alone.

### Scores Validation

Before applying the decision table, validate `harness-output/scores.json`:
1. File exists and parses as valid JSON
2. All four score fields present: `designQuality`, `originality`, `craft`, `functionality`
3. All scores are numbers in the 0-10 range
4. `weightedAverage` matches the formula: `(designQuality*2 + originality*2 + craft + functionality) / 6`
5. If validation fails, the orchestrator must re-run the evaluator rather than making a decision on bad data

### Selecting the Best Iteration

When SHIP is triggered, deliver the iteration with the highest weighted average, not necessarily the most recent one. Later iterations sometimes regress as the Design Agent reaches for more ambitious directions that the Implementation Agent struggles to execute cleanly.

See also: [Best Iteration Tracking](#best-iteration-tracking) for the full tracking and delivery protocol.

## Convergence Detection

Convergence means the evaluate-design-implement loop is no longer producing meaningful improvement. Signals:

1. **Score plateau** — Weighted average changes < 0.5 for 2+ iterations
2. **Critique repetition** — The evaluator raises the same issues across iterations
3. **Diminishing returns** — Small score improvements require increasingly complex changes
4. **Oscillation** — Scores alternate up/down without net progress
5. **Zone score stagnation** — A specific zone stays below 5 (score < 5) on any criterion for 2+ consecutive iterations. This triggers mandatory zone-focused critique: the evaluator must produce a dedicated critique entry for that zone with specific, actionable fixes. If zone stagnation persists after 3 iterations, escalate to a zone-level rework (redesign that zone from scratch while preserving the rest of the page). This is distinct from a global PIVOT, which restarts the entire aesthetic direction.
6. **Persistent gate-cap stagnation** — If the same zone is hard-capped at exactly 5 by adversarial gate failures for 2+ consecutive iterations, this also triggers mandatory zone-level rework. Gate-capped zones cannot improve through aesthetic refinement alone — the underlying technical defect must be resolved first. This escalation path is distinct from score stagnation (signal 5) because the root cause is a gate failure, not a scoring plateau.

When convergence is detected AND weighted average ≥ 6.5, SHIP. Below 6.5, PIVOT.

### Plateau Detection

The harness must detect when iterations are spinning without progress and intervene mechanically.

**Score plateau:** If the weighted average changes < 0.5 for 2 or more consecutive iterations, trigger a decision:
- If weighted average ≥ 6.5 → SHIP (converged at acceptable quality)
- If weighted average < 6.5 → PIVOT (stuck at unacceptable quality)

**Critique repetition:** If the evaluator raises the same top-3 issues for 2 or more consecutive iterations, they are not being addressed. The orchestrator must:
1. Flag this for review — the Design Agent may need a more explicit instruction
2. Escalate the unaddressed critique as a mandatory change, not a suggestion
3. If the same issues persist after escalation, PIVOT — the current direction cannot resolve them

**Regression alert:** Track the best-ever weighted average across all iterations (not just the previous one). If the current iteration scores lower than the best iteration for 2 or more consecutive rounds:
- Alert that quality is degrading from peak
- Consider shipping the best iteration rather than continuing
- This prevents complexity creep where later iterations add ambition but lose coherence

**Oscillation:** If scores alternate up/down for 3+ iterations without net improvement (the trendline slope is near zero), the harness has converged. Apply convergence rules: SHIP if ≥ 6.5, PIVOT if below.

## Zone Evaluation vs Section Decomposition

Two complementary systems operate at different levels within the harness:

- **Zone-based evaluation** = per-visual-component scoring within a single evaluation pass. Always on. The evaluator identifies zones (header, hero, content sections, graphs/charts, sidebar, footer), captures each at 2x zoom, and scores independently. Catches text overlaps, graph clipping, sidebar overflow, and other subsystem problems that full-page scoring averages away.

- **Section decomposition** = per-section creative isolation with separate design-then-implement-then-evaluate cycles. Optional, for multi-section pages. Protects creative freedom by preventing the design agent from anchoring to adjacent sections.

These are **complementary**: zone-based evaluation runs within every evaluation pass (including during section decomposition). Section decomposition controls the creative loop granularity — how many design-implement-evaluate cycles happen and at what scope. Zone evaluation controls scoring granularity — how finely the evaluator examines a single rendered output.

## Pivot Mechanics

A PIVOT is a complete aesthetic restart. This is the harness's most powerful tool — it's what produces the breakthrough designs (like the blog's Dutch art museum example where iteration 10 abandoned a dark landing page for a 3D spatial gallery experience).

In the 3-agent architecture, PIVOT means:
- The **Design Agent** receives a fresh creative brief with explicit instruction to abandon the current visual direction
- The **Implementation Agent** receives a completely new design description — no code is carried forward
- The **Evaluator** scores the new direction from scratch but retains awareness of prior direction failures

### Pre-Pivot Preservation

Before a PIVOT, the orchestrator MUST preserve the current best iteration's artifacts:
1. Copy the current frontend files to `harness-output/iterations/iter-{N}/` (HTML, CSS, JS)
2. The `scores.json` already tracks all iterations — verify the `bestIteration` field is correct
3. **Commit all `harness-output/` artifacts** before starting the pivot — this creates a VCS checkpoint that survives branch/change switches and can be restored if the pivot direction is worse
4. On SHIP, the orchestrator delivers the files from the best-scoring iteration, which may be a pre-pivot version

This prevents the "overwrite and regress" failure where a pivot produces worse results than the prior direction and the best work is lost. The VCS commit in step 3 is especially critical — without it, jj working-copy switches or git branch operations can wipe the pre-pivot state entirely.

### What Changes on PIVOT

- Aesthetic direction (new mood, new color palette, new typography)
- Layout structure (new spatial composition)
- Interaction model (new animation approach, new navigation pattern)

### What Persists on PIVOT

- The spec's feature requirements
- The sprint contract's functional criteria
- Lessons from the failed direction (what didn't work and why)
- All previous iteration artifacts (preserved in `harness-output/iterations/`)

### Pivot Prompt Template

When generating the PIVOT instruction for the Design Agent:

```text
PIVOT INSTRUCTION:

The previous approach — [describe the failed direction] — scored [X.X/10] weighted
average after [N] iterations. Key failures:
- [specific failure 1]
- [specific failure 2]

ABANDON the previous direction entirely. Do not salvage code, layouts, or color choices.

NEW DIRECTION: Choose a fundamentally different aesthetic. If the previous attempt was
[characteristic], try [opposite characteristic].

RETAIN: All features from the spec. The sprint contract criteria still apply.

LESSON: The previous attempt failed because [root cause]. The new direction should
explicitly address this.
```

## Refine Mechanics

A REFINE is a targeted improvement pass. The Design Agent receives the evaluator's critique and revises its design description within the current direction. The Implementation Agent then executes the updated design description.

### Refine Priority

The Design Agent should address critique points in order of:

1. **Design quality issues** (highest weight, most impact on score)
2. **Originality issues** (highest weight)
3. **Craft issues** (lower weight but quick to fix)
4. **Functionality issues** (lower weight, usually already decent)

### Refine Anti-Pattern: Regression

The most common failure during refinement is regressing previously-good elements while fixing new ones. The Implementation Agent should:
- Note what the evaluator praised before making changes
- Test that praised elements still work after changes
- Make surgical edits, not wholesale rewrites, during REFINE

## Iteration Budget

### Defaults

| Setting | Value | Rationale |
|---------|-------|-----------|
| maxIterations | 8 | Balances quality with time/cost. Blog found 5-15 was typical. |
| minIterations | 2 | Always do at least one evaluate-refine cycle |
| pivotBudget | 2 | Maximum number of full pivots before forced SHIP |

### Loop Automation

When using `/loop` to automate iteration cycles, the loop must be canceled when:
- Decision framework returns **SHIP** (quality threshold met or acceptable convergence)
- **maxIterations** reached — ship the best-scoring iteration
- **pivotBudget** exhausted — ship the best-scoring iteration across all pivots

Each iteration's output should include the current iteration number, weighted average, decision, and whether the loop should continue. The orchestrator (or `/loop` body) is responsible for calling `/loop cancel` or stopping execution when a termination condition is met.

### Cost Awareness

Each iteration involves:
- Design Agent: ~$1-3 per iteration
- Implementation Agent: ~$5-12 depending on complexity
- Evaluator agent: ~$2-5
- Total harness run (6 iterations): ~$50-120

For simple components, reduce maxIterations to 4. For full-page ambitious designs, allow up to 12.

## Score Tracking

Maintain `harness-output/scores.json` across all iterations:

```json
{
  "config": {
    "maxIterations": 8,
    "shipThreshold": 7.0,
    "convergenceThreshold": 6.5,
    "slowProgressThreshold": 5.0
  },
  "iterations": [
    {
      "iteration": 1,
      "timestamp": "2026-03-29T12:00:00Z",
      "scores": {
        "designQuality": 5,
        "originality": 4,
        "craft": 6,
        "functionality": 7
      },
      "weightedAverage": 5.17,
      "decision": "REFINE",
      "pivoted": false,
      "keyIssues": ["generic layout", "template typography"]
    },
    {
      "iteration": 2,
      "timestamp": "2026-03-29T12:15:00Z",
      "scores": {
        "designQuality": 6,
        "originality": 5,
        "craft": 7,
        "functionality": 7
      },
      "weightedAverage": 6.0,
      "decision": "REFINE",
      "pivoted": false,
      "keyIssues": ["improved but still conventional layout"]
    }
  ],
  "bestIteration": 2,
  "currentDecision": "REFINE",
  "pivotsUsed": 0
}
```

## Best Iteration Tracking

The orchestrator must track and preserve the best-scoring iteration across the entire harness run, including across pivots. This prevents complexity creep from degrading quality in later iterations.

### Tracking Rules

1. After every evaluation, compare the current iteration's weighted average to `bestIteration` in `scores.json`
2. Update `bestIteration` if the current iteration scores higher
3. Every iteration's artifacts are preserved in `harness-output/iterations/iter-{N}/` regardless of whether it's the best

### SHIP Delivery Protocol

When SHIP is triggered:
1. Identify the best-scoring iteration across all iterations and all pivots
2. If the best iteration is the latest iteration, deliver it directly
3. If the best iteration is NOT the latest iteration, deliver the best one and include a note in the harness report:
   - Which iteration was shipped and its weighted average
   - Why the latest iteration was not shipped (e.g., "iterations 6-8 added complexity that reduced coherence")
   - The score trajectory showing where peak quality occurred
4. The delivered files come from `harness-output/iterations/iter-{N}/` for the best iteration

### Why This Matters

Without best-iteration tracking, the harness suffers from a common failure mode: early iterations establish a strong direction, middle iterations polish it to peak quality, and late iterations over-engineer it back down. Shipping the latest iteration by default means shipping degraded work when the best version existed 2-3 iterations ago.

## Section-by-Section Decomposition

For multi-section pages, the harness can decompose design work by section to protect creative freedom and break through originality plateaus.

### Why Decompose by Section

This is NOT about managing context — modern models can hold full pages. Section decomposition exists to **protect creative freedom**.

Each section gets its own creative moment, unconstrained by adjacent sections. The Design Agent sees ONLY the target section's screenshot, not the full page. This prevents the **anchoring effect** where one section's style constrains all others — a hero with a dark gradient subtly pushes every subsequent section toward dark themes, even when a light section would create better rhythm.

### Section Decomposition Workflow

```text
Phase A: Section-level design (iterate per section)
  Section 1 (Hero): Design Agent → Implementation Agent → Evaluator → loop
  Section 2 (Content): Design Agent → Implementation Agent → Evaluator → loop
  Section 3 (Features): Design Agent → Implementation Agent → Evaluator → loop
  ...each section reaches quality threshold independently

Phase B: Integration pass (full page)
  Design Agent sees FULL page screenshot → checks narrative flow, rhythm, cohesion
  Implementation Agent harmonizes transitions between sections
  Evaluator scores the full page as a unified experience
```

Phase A runs the full REFINE/PIVOT/SHIP decision framework per section. Each section has its own iteration count, score history, and pivot budget. Phase B is a lighter pass (typically 2-3 iterations) focused on cohesion rather than individual section quality.

### When to Use Section Decomposition

- Multi-section pages (3+ distinct content areas)
- Full-page designs where layout is critical
- When originality scores are stuck — decomposing often breaks through plateaus by giving each section a fresh creative start
- Pages where different sections serve fundamentally different purposes (hero vs. social proof vs. CTA)

### When NOT to Decompose

- Single-component builds (a card, a modal, a navbar)
- Pages with 1-2 simple sections
- Integration/polish passes (these need full-page view by definition)
- When the page has a single unified visual concept that would be broken by sectional design

### Section Isolation Rules

Each section's Design Agent receives ONLY:
- Section screenshot (cropped from the live page)
- Section evaluator critique (for REFINE cycles — the evaluator's feedback on this section specifically)
- Section spec (content, purpose, interaction requirements)
- Brand brief (colors, typography, voice)

Each section's Design Agent does NOT see:
- Other sections' code or implementation details
- Other sections' evaluator critique
- Full page context or screenshots of other sections

**Exception:** The Phase B integration pass agent sees the full page — this is the only point where cross-section context is available. The integration agent's job is to harmonize transitions, ensure narrative flow, and resolve any visual conflicts between independently-designed sections.
