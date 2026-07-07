# Meta Module

How to improve the harness itself. Lessons from the Anthropic blog on tuning, removing scaffolding, and adapting to model improvements.

## The Core Meta-Principle

> "The space of interesting harness combinations doesn't shrink as models improve. Instead, it moves, and the interesting work for AI engineers is to keep finding the next novel combination."

The harness is not a fixed system. It should be periodically re-evaluated: which components are still load-bearing? Which can be removed? What new capabilities can be added?

## Lesson 1: Criteria Wording Steers Generation

The specific language in the scoring rubric shapes what gets created. This is both a tool and a risk.

**How it works:** When the evaluator uses phrases like "museum quality" or "editorial sophistication," the generator unconsciously steers toward those aesthetic reference points. The rubric's vocabulary becomes a hidden style guide.

**The risk:** Overly specific aesthetic language causes convergence. If the rubric says "museum quality," every iteration trends toward gallery-white minimalism. If it says "playful and whimsical," everything gets rounded corners and pastel gradients.

**How to tune:**
- Keep criteria descriptions about QUALITIES (cohesion, distinctiveness, craft) not AESTHETICS (museum-like, editorial, brutalist)
- Let the spec define the aesthetic direction. The rubric should judge execution quality, not style preference.
- If you notice multiple harness runs producing visually similar outputs, audit the rubric for style-prescriptive language.

## Lesson 2: Evaluator Tuning is the Hardest Part

The evaluator is the weakest link. Common failure patterns and their fixes:

### Failure: Identify-Then-Rationalize

**Pattern:** Evaluator finds a real issue, then talks itself into accepting it.

**Fix:** Add explicit instruction: "If you identify a problem, it IS a problem. Score it. Do not explain why it might be acceptable."

### Failure: Superficial Interaction

**Pattern:** Evaluator takes a screenshot and writes critique from the static image without actually using the page.

**Fix:** Require specific interaction evidence in the critique: "I clicked [element] and [result happened]." No interaction evidence = incomplete evaluation.

### Failure: Stable High Scores on Mediocre Work

**Pattern:** Evaluator gives 7-8 to work that's merely functional and clean but not distinctive.

**Fix:** Calibration examples. Show the evaluator what a 5, 7, and 9 look like. Anchor: "A 5 is a clean Bootstrap template. A 7 is a custom-designed professional site. A 9 is award-winning design."

### How to Diagnose Evaluator Issues

Read the evaluator's critique logs across multiple runs. Look for:
- Score inflation (averages consistently above 7 on first iterations)
- Vague critique (no specific element references)
- Missing interaction evidence (no "I clicked X" statements)
- Criteria conflation (functionality score mirrors design quality)
- Consistent failure to catch obvious issues visible in screenshots

## Lesson 3: Remove Non-Load-Bearing Scaffolding

The blog's key architectural lesson: systematically remove components one at a time to find which are truly load-bearing.

### What was removed from the original harness

| Component | Removed? | Why |
|-----------|----------|-----|
| Sprint decomposition | Yes (with Opus 4.6) | Model can sustain coherent long builds without decomposition |
| Multiple build rounds | No | Single builds still miss issues the evaluator catches |
| Planner agent | No | Specs prevent cascading errors from vague prompts |
| Evaluator agent | No | Separated evaluation is the core innovation — always load-bearing |
| Sprint contracts | No | Without success criteria, evaluation drifts |

### How to test if a component is load-bearing

1. Run the full harness on a representative prompt. Record output quality.
2. Remove one component. Run the same prompt.
3. Compare outputs. If quality drops noticeably, the component is load-bearing.
4. Repeat for each component.

Do this on every major model upgrade. What was load-bearing on one model version may be unnecessary on the next.

### Current recommendations (Opus 4.6 era)

> **Maintenance note:** These recommendations are model-era-specific and should be re-evaluated on each major model upgrade. What is load-bearing on Opus 4.6 may be unnecessary or insufficient on future models.

- **Keep:** Planner, separated evaluator, live Chrome browser interaction (claude-in-chrome MCP), scoring rubric, zone-based evaluation, adversarial gate, iteration loop
- **Optional:** Sprint contracts (can simplify to just the spec for simple pages)
- **Remove:** Sprint decomposition within the Implementation Agent (Opus 4.6 sustains coherent long builds)

## Lesson 4: Match Evaluator Investment to Task Difficulty

The evaluator adds cost and time. Its value depends on how far the task sits beyond the model's reliable solo capability boundary.

| Task Complexity | Evaluator Value | Recommendation |
|----------------|-----------------|----------------|
| Single component (button, card, form) | LOW | Skip the harness. Solo generation is sufficient. |
| Single page, straightforward | MEDIUM | Run 2-3 iterations. Evaluator catches the worst generic patterns. |
| Full page, ambitious design | HIGH | Full harness, 5-8 iterations. This is where the harness shines. |
| Multi-page application | HIGH | Full harness per page, plus cross-page consistency checks. |

**Rule of thumb:** If a skilled human designer could do it in under an hour, the harness probably isn't worth the overhead. If it would take a designer a full day, the harness will meaningfully improve quality.

## Lesson 5: Complexity Creep Across Iterations

Later iterations tend toward more ambitious, complex implementations. This is often good (the Dutch museum 3D gallery example) but can introduce bugs in deeply nested features.

**Symptoms:**
- JavaScript errors in late iterations that weren't present in early ones
- Responsive breakpoints that worked simply now break with complex CSS
- Animations that layer and create performance issues
- Features that the evaluator didn't specifically request

**Mitigation:**
- The evaluator should check for REGRESSIONS, not just improvements
- If functionality score drops while design quality rises, flag the trade-off explicitly
- The Implementation Agent should test its own code before handing off (basic sanity, not self-evaluation)
- Set a complexity ceiling in the spec: "This should work as a single HTML file with inline CSS and JS under 500 lines"

## Lesson 6: Code-Anchoring Bias

The most impactful discovery from real-world testing: reading existing code before generating new designs anchors the LLM's creativity to "what can I tweak" instead of "what should this look like."

**Evidence:**
- In a real website overhaul: 3 iterations of CSS-only tweaks despite instructions to "make the hero asymmetric." The single-agent generator kept adjusting margins and padding instead of reimagining the layout — because the existing HTML structure was in its context.
- Research confirmation: arXiv:2412.06593 proves that anchoring bias in LLMs is systematic, and stronger models are MORE consistently influenced (not less). This is counterintuitive — better models are better at anchoring, not better at resisting it.
- arXiv:2408.09121 shows that as more code tokens accumulate in context, LLMs pay progressively less attention to user prompts — a phenomenon the paper calls "attention dilution." Design intent gets diluted by implementation details.

**Fix:** Separate creative decisions (Design Agent, works from screenshots only) from implementation (Implementation Agent, executes design descriptions into code). This mirrors how design studios actually work: art director creates the vision without caring about current CSS, developer implements it.

**Why this is load-bearing:** Unlike sprint decomposition (which Opus 4.6 made optional), the design/implementation split addresses a fundamental cognitive limitation, not a context-window limitation. Anchoring bias does not shrink with larger context windows — it gets worse because more code means more anchor material. This separation should be maintained regardless of model improvements.

## Lesson 7: Decomposition Serves Different Purposes for Code vs Design

The blog post simplified decomposition for Opus 4.6 because the model could hold more context. But for design work, decomposition is not about context management — it is about protecting creative freedom.

When a Design Agent sees the full page (all sections already built), it anchors to the existing visual pattern. Each subsequent section becomes a variation of what came before. This produces coherent but monotonous pages where every section shares the same rhythm.

Section decomposition for design means each section gets its own creative moment, unconstrained by adjacent sections. The hero section does not see the features section. The pricing section does not see the testimonials. Only after all sections are independently designed does an integration pass ensure coherence.

This is the opposite of the code decomposition trade-off:
- **Code decomposition** was removed because the model could handle it in one pass — decomposition added overhead without quality gain.
- **Design decomposition** should be kept because its value comes from creative isolation, not context management. Even a model with infinite context would benefit from not seeing adjacent sections while designing.

**Recommendation:** Keep section decomposition as an option for multi-section pages even as models improve. Re-evaluate only if anchoring bias itself is solved at the model level.

## Lesson 8: Holistic Scoring Masks Subsystem Problems

Zone-by-zone evaluation at component level catches text overlaps, graph clipping, sidebar overflow that full-page scoring averages away. A page can score 7 overall while its footer is clipped, its sidebar overflows on mobile, and its graph labels are unreadable. Zone-based evaluation with per-zone scoring and zone-minimum enforcement prevents these masked failures.

**How it works:** After the full-page screenshot, the evaluator identifies visual zones (header, hero, content sections, graphs/charts, sidebar, footer), captures each at 2x zoom, and scores independently. The final craft and functionality scores use the minimum of whole-page and worst-zone scores.

## Lesson 9: Evaluators Miss What They Don't Try To Break

Without explicit "try to break it" requirements, evaluators optimize for visual impression and miss rendering bugs. The adversarial testing gate addresses this by requiring specific destructive checks before scoring:

- Scroll all containers to check for hidden overflow
- Resize through breakpoints to check for layout collapse
- Read console messages for JavaScript errors
- Click every interactive element to verify behavior

Gate failures impose hard score caps, making it impossible to ship technically broken implementations with high visual scores. This is a forcing function — the evaluator cannot skip adversarial checks because the scoring system depends on them.

**Diagnostic sign:** If you see high design quality and originality scores (7+) paired with user-reported bugs after shipping, the adversarial gate checks are insufficient. Add more destructive test patterns.

## Applying Meta-Learnings

When tuning this harness:

1. **Read the traces.** Review `harness-output/critique-{N}.md` and `harness-output/design-description-{N}.md` files from real runs. Where did the evaluator fail to catch issues? Where did the Design Agent anchor to previous patterns despite not seeing code?
2. **Audit the rubric.** Look for style-prescriptive language that might cause convergence across runs.
3. **Test component removal.** After a model upgrade, run the same prompt with and without each component. Note: the Design Agent / Implementation Agent split should be tested last — it is expected to remain load-bearing regardless of model improvements.
4. **Calibrate scoring.** If first-iteration scores average above 6.5 across multiple runs, the rubric is too lenient.
5. **Track pivot success rate.** If pivots rarely produce better designs than continued refinement, the pivot threshold may be too aggressive.
6. **Monitor design description quality.** If design descriptions are vague or implementation-flavored ("add padding", "change the CSS"), the Design Agent may be receiving implementation context through some channel. Audit what is being passed to it.
