# Evaluation Module

The scoring rubric, live evaluation protocol, zone-based evaluation system, adversarial testing gate, and common evaluator failure modes.

> **Sync note:** The scoring rubric, calibration anchors, and failure modes in this module mirror those in `agents/evaluator.md`. This duplication is intentional — the evaluator agent runs in isolation and needs self-contained scoring context, while this module gives the orchestrator the same information for decision-making. **Keep both files in sync when editing scoring criteria.**

## Why Separated Evaluation

Self-evaluation fails for subjective tasks. When a single agent evaluates its own design:
- It has sunk-cost bias toward its implementation choices
- It can see the intent behind the code, not just the rendered result
- It rationalizes problems as intentional design decisions
- It grades inflated — a 5 becomes a 7 because "it's functional"

Separated evaluation fixes this by ensuring the evaluator:
- Never sees the source code
- Has no knowledge of implementation effort
- Judges purely from the user's perspective
- Uses an explicit rubric that resists rationalization

## The Four Criteria

### Design Quality (Weight: 2x)

**Question:** Does the design feel cohesive rather than fragmented?

What to evaluate:
- Do colors, typography, layout, and imagery combine into a single, nameable mood?
- Is there a consistent visual language across the page?
- Do decorative elements reinforce or contradict the mood?
- Does the color palette feel intentional or scattered?
- Is there a clear visual hierarchy that guides the eye?

**Scoring anchor:** If you can't name the aesthetic in one phrase ("expedition journal," "brutalist manifesto," "Japanese minimalism"), the score is below 6.

### Originality (Weight: 2x)

**Question:** Would a human designer recognize deliberate creative choices?

What to evaluate:
- Is the layout structure conventional or inventive?
- Are font choices distinctive or generic?
- Are interactions standard or surprising?
- Does any element feel like it came from a template library?
- Is there at least one "I haven't seen that before" moment?

**Scoring anchor:** If you could swap in a different company's content without redesigning anything, the score is below 6.

**Mandatory Scoring Floors (Originality)**

The following patterns MUST score **4 or below** on originality, regardless of execution quality:

- Centered hero section with heading + subtitle + CTA button
- Feature cards in a uniform grid (2-3 columns)
- SaaS landing structure (hero → features → testimonials → CTA)
- Purple gradients or default Tailwind-like palette choices
- Common default fonts (Inter, Roboto, Helvetica, system-ui, Arial, Space Grotesk)
- Generic hover effects (scale-up, opacity fades, color-only transitions)
- Symmetrical centered layouts throughout
- Stock illustration/icon grid sections

Do not rationalize these upward for polish.

**Enhanced originality anchors:**

| Score | What You See |
|-------|-------------|
| 3-4 | Centered hero + subtitle + CTA. Feature cards in 2-3 column grid. SaaS template structure (hero → features → testimonials → CTA). Common default fonts (Inter, Roboto, system-ui). Purple gradients or default Tailwind palette. Symmetrical centered layouts throughout. You have seen this exact page 100 times. |
| 5-6 | One or two custom choices (an unusual color, an asymmetric section) but the overall skeleton is recognizable template. A designer would say "they tried, but it's still safe." The layout would survive a content swap without looking broken. |
| 7-8 | A specific creative vision is unmistakable. Layout has personality — maybe an editorial grid, diagonal rhythm, overlapping elements, or unexpected scroll behavior. Font choices are distinctive and deliberate. You could not swap in different content without the design feeling wrong. |
| 9-10 | Remarkable. A designer would screenshot this and share it. Every choice feels intentional and surprising yet coherent. The page has a point of view that is inseparable from its content. |

### Craft (Weight: 1x)

**Question:** Is the technical execution clean?

What to evaluate:
- Typography: consistent sizing scale, proper line-height, adequate letter-spacing
- Spacing: consistent padding/margin rhythm, proper element grouping
- Color: sufficient contrast for readability, harmonious palette application
- Alignment: elements snap to a grid or have intentional misalignment
- Responsive: layout adapts gracefully between 1440px and 390px

**Scoring anchor:** Check at 390px width. If the mobile experience is broken or clearly an afterthought, the score is below 6.

### Functionality (Weight: 1x)

**Question:** Can users accomplish their goals?

What to evaluate:
- Is the primary action immediately identifiable?
- Does navigation make sense without instruction?
- Do interactive elements provide feedback (hover, active, focus states)?
- Are there any broken links, missing images, or console errors?
- Can you complete the main user flow from start to finish?
- **UX pattern quality**: Are interactions contextually connected? Does clicking a detail element show information visually linked to the source? Are progressive disclosure patterns appropriate for the content type?
- **Visual grouping (Gestalt)**: Are related elements grouped through proximity, similarity, or enclosure? Are unrelated elements clearly separated?
- **Information hierarchy**: Does visual weight (size, color, contrast, position) match actual importance? Do eyes land on the primary action first?

**Scoring anchor:** Open the page cold (no context about what it does). If you can't figure out the primary action in 5 seconds, the score is below 6. If UX patterns are confused — detail panels disconnected from triggers, hover-to-reveal on critical content, related items scattered — the score cannot exceed 6 regardless of technical functionality.

## Weighted Average Calculation

The formula used to compute the weighted average score:

```text
weightedAvg = (designQuality * 2 + originality * 2 + craft * 1 + functionality * 1) / 6
```

Design quality and originality are weighted 2x because Claude already performs well on craft and functionality by default. The harness exists to push beyond "functional but generic." Agents reading this file alone have the full scoring picture -- the decision thresholds in `iteration.md` reference this weighted average.

### Craft Penalty Rule

When originality is 4 or below and craft is 6 or above, apply a craft penalty of **-1 to -2 points**. Rationale: excellent technical execution on a generic layout creates false confidence. High craft scores signal "the approach is working" when the structural direction needs to change entirely. This prevents "polished mediocrity" from stalling pivot decisions.

Example: A perfectly spaced, beautifully kerned centered-hero + card-grid layout scores originality 3, raw craft 7. After penalty, craft becomes 5 or 6. The weighted average drops enough to trigger a PIVOT instead of a REFINE, which is the correct decision when the design direction itself is the problem.

## Adversarial Testing Gate

The adversarial gate is a **mandatory pre-scoring protocol** that runs BEFORE aesthetic scoring. It catches technical defects that aesthetic scoring tends to rationalize away. No scoring may begin until all gate checks are complete.

### Gate Checks

#### 1. Viewport Boundary Audit
Scroll the full page at 1440px width. Flag:
- Any content extending beyond viewport width (triggers horizontal scrollbar)
- Elements cut off or unreachable
- Fixed/sticky elements that overlap content

Check with: `mcp__claude-in-chrome__javascript_tool(tabId: <EVAL_TAB_ID>, action: "javascript_exec", text: "document.documentElement.scrollWidth > document.documentElement.clientWidth")`

#### 2. Text Readability Sweep
Check all text zones for:
- **Overlapping text** — text from one element colliding with another
- **Clipped text** — text cut off by container overflow:hidden
- **Too-small text** — any text below 12px effective size
- **Insufficient contrast** — text/background pairs below WCAG AA (4.5:1 normal, 3:1 large)
- **Text-image collisions** — text running into or overlapping with images

Check with: `mcp__claude-in-chrome__javascript_tool(tabId: <EVAL_TAB_ID>, action: "javascript_exec", text: "[...document.querySelectorAll('*')].filter(el => { const s = getComputedStyle(el); return s.fontSize && parseFloat(s.fontSize) < 12 && el.textContent.trim().length > 0; }).map(el => el.tagName + ': ' + el.textContent.trim().slice(0,40))")`

#### 3. Interaction Completeness
- Every hover effect must have a corresponding click action or be purely decorative
- Every clickable element must have visible affordance (pointer cursor, underline, button styling)
- Forms must have submit paths
- Links must have valid destinations (no `href="#"` on functional navigation)

Use `mcp__claude-in-chrome__read_page(tabId: <EVAL_TAB_ID>, filter: "interactive")` to enumerate all interactive elements, then test each.

#### 4. Overflow Stress Test
Resize to 390px mobile width. Check for:
- **Horizontal overflow** — any horizontal scrollbar at mobile width
- **Overlapping elements** — elements stacking on top of each other
- **Meaningful text truncation** — text cut off in a way that loses meaning (not just ellipsis on a preview)
- **Touch targets too small** — interactive elements below 44x44px

Check touch targets with: `mcp__claude-in-chrome__javascript_tool(tabId: <EVAL_TAB_ID>, action: "javascript_exec", text: "[...document.querySelectorAll('a, button, input, select, [role=button]')].filter(el => { const r = el.getBoundingClientRect(); return r.width < 44 || r.height < 44; }).map(el => el.tagName + ': ' + el.textContent.slice(0,30) + ' (' + Math.round(el.getBoundingClientRect().width) + 'x' + Math.round(el.getBoundingClientRect().height) + ')')")`

### Gate Enforcement Rules

- Any gate failure **hard-caps Craft at 5/10 and Functionality at 5/10** for the affected zone (or whole page if the failure is page-wide)
- Gate failures are listed FIRST in the critique output, before any aesthetic feedback
- The evaluator MUST document each gate check as pass/fail with specifics
- Gate checks cannot be skipped, deferred, or rationalized away — "it's a stylistic choice" is not an acceptable reason to dismiss a readability failure

## Zone-Based Evaluation Protocol

Whole-page scoring misses subsystem problems. A beautiful hero can mask a broken chart section because the overall page score averages them out. Zone-based evaluation prevents this.

### Zone Identification

After full-page screenshots, the evaluator identifies all distinct visual zones:
- Header/navigation
- Hero section
- Each content section (features, testimonials, pricing, graphs, etc.)
- Sidebar (if present)
- Graph/chart areas (if present)
- Footer
- Modal/overlay (if present/triggered)

Use JavaScript to map zone bounding boxes:
```javascript
// Run via mcp__claude-in-chrome__javascript_tool(tabId: <EVAL_TAB_ID>, ...)
[...document.querySelectorAll('header, nav, main > section, main > div, footer, aside, [role=banner], [role=main], [role=contentinfo]')].map(el => {
  const r = el.getBoundingClientRect();
  return {
    tag: el.tagName, id: el.id,
    class: el.className.toString().slice(0, 50),
    top: Math.round(r.top + window.scrollY),
    left: Math.round(r.left),
    width: Math.round(r.width),
    height: Math.round(r.height)
  };
})
```

### Zone Screenshot Capture

For each zone:
1. Scroll to center the zone: `mcp__claude-in-chrome__javascript_tool(tabId: <EVAL_TAB_ID>, action: "javascript_exec", text: "window.scrollTo(0, ZONE_TOP - 100)")`
2. Take a screenshot: `mcp__claude-in-chrome__computer(tabId: <EVAL_TAB_ID>, action: "screenshot")`
3. For every zone, MUST resize the viewport to 2x zoom (halve the viewport width to isolate the zone area) for a closer view — this catches fine-grained defects invisible in full-page screenshots:
   - Resize to 2x zoom: `mcp__claude-in-chrome__resize_window(tabId: <EVAL_TAB_ID>, width: <ZONE_WIDTH>, height: <ZONE_HEIGHT>)`
   - Take zoomed screenshot: `mcp__claude-in-chrome__computer(tabId: <EVAL_TAB_ID>, action: "screenshot")`

### Zone Scoring

Each zone gets its own 4-criterion score card:

```text
Zone: [name]
  designQuality: X/10
  originality: X/10
  craft: X/10
  functionality: X/10
```

Apply gate caps: if any adversarial gate check failed for content within this zone, Craft and Functionality are hard-capped at 5.

### Zone-Level Critique Format

Each zone with a score below 6 on any criterion gets its own critique section:

```markdown
### Zone: [zone name] (e.g., "Graph/Chart Section")
**Scores:** DQ: X | O: X | Craft: X | Func: X
**Issues:** [specific visual problems — text overlap, clipping, alignment, readability]
**Screenshot evidence:** [which screenshot shows the issue]
```

Zones scoring 6+ on all criteria can be summarized briefly rather than given full critique sections.

### Zone Score Impact on Page Score

The overall page scores are computed as follows:
- **Design Quality**: whole-page score (zones inform the critique but DQ is inherently holistic)
- **Originality**: whole-page score (same reasoning)
- **Craft**: min(whole-page Craft score, lowest zone Craft score)
- **Functionality**: min(whole-page Functionality score, lowest zone Functionality score)

This means a single broken zone drags down the page-level Craft or Functionality. The implementation cannot hide subsystem failures behind strong sections.

## Live Evaluation Protocol

### Step 1: Serve and Verify

```bash
# For HTML files
npx serve ./harness-output/site -l 3333 &

# Or for React/Vite
cd harness-output/site && npm run dev &
```

**Health check (required):** After starting the server, verify it is responding before proceeding. Create a dedicated evaluation tab via `mcp__claude-in-chrome__tabs_create_mcp()` and store the returned `tabId` as `<EVAL_TAB_ID>` for all subsequent tool calls in this evaluation pass. Navigate to the URL via `mcp__claude-in-chrome__navigate(tabId: <EVAL_TAB_ID>, url: "http://localhost:3333")` — retry up to 3 times with 2-second delays. If the server fails to respond after all retries (port conflict, build error, missing dependencies), HALT with a clear error rather than attempting to screenshot a blank page.

**Cleanup (required):** After completing all screenshots and interactions for this iteration, kill the server process (`kill %1` or equivalent). Do not leave background processes running across iterations — this causes port conflicts and zombie processes.

### Step 2: Full-Page Screenshot

Use Chrome MCP to capture:
- Full-page screenshot at 1440px width: `mcp__claude-in-chrome__resize_window(tabId: <EVAL_TAB_ID>, width: 1440, height: 900)` then `mcp__claude-in-chrome__computer(tabId: <EVAL_TAB_ID>, action: "screenshot")`
- Full-page screenshot at 390px width: `mcp__claude-in-chrome__resize_window(tabId: <EVAL_TAB_ID>, width: 390, height: 844)` then `mcp__claude-in-chrome__computer(tabId: <EVAL_TAB_ID>, action: "screenshot")`
- Above-the-fold screenshot (viewport-only, no scroll) at both widths
- Key interaction states (expanded nav, hover effects, modal open)

### Step 3: Adversarial Gate (MANDATORY)

Run ALL gate checks before any scoring begins. See the "Adversarial Testing Gate" section above for the full protocol. Document every check as pass/fail.

### Step 4: Zone Identification and Evaluation

Identify all visual zones, capture per-zone screenshots, and score each zone independently. See the "Zone-Based Evaluation Protocol" section above for the full protocol.

### Step 5: Interact and Evaluate UX Patterns

Use Chrome MCP to test:
All tool calls below use the `<EVAL_TAB_ID>` obtained during Step 1:
```text
- Read interactive elements via read_page(tabId: <EVAL_TAB_ID>, filter: "interactive")
- Click every visible link/button via computer(tabId: <EVAL_TAB_ID>, action: "left_click", ...)
- Scroll to bottom via computer(tabId: <EVAL_TAB_ID>, action: "scroll", ...) — check scroll-triggered animations
- Hover over interactive elements via computer(tabId: <EVAL_TAB_ID>, action: "hover", ...)
- Test keyboard navigation via computer(tabId: <EVAL_TAB_ID>, action: "key", text: "Tab") through focusable elements
- Resize viewport from 1440 to 390 via resize_window(tabId: <EVAL_TAB_ID>) — check responsive transitions
- Check console for errors via read_console_messages(tabId: <EVAL_TAB_ID>, pattern: "error|warn")
```

Evaluate UX patterns during interaction testing:
- Test contextual connections between triggers and their revealed content
- Assess whether interaction patterns are appropriate for the content type
- Check visual grouping of related elements (Gestalt principles)
- Verify information hierarchy matches visual weight distribution

### Step 6: Score and Critique

Apply the rubric above. Apply gate caps and zone score floors. Write structured critique. Be specific about locations and elements — reference "the hero section," "the third card in the features grid," "the footer navigation," not vague areas.

## Evaluator Failure Modes

These are documented failure modes from real harness runs. The evaluator MUST actively resist each:

### 1. Rationalization

**Symptom:** The evaluator identifies a real problem, then explains why it's actually fine.

**Example:** "The hero text is hard to read against the background, but this creates an intentional sense of mystery."

**Fix:** If contrast is poor, it's poor. Score it. The Design Agent can decide if the trade-off is worth it in the next iteration.

### 2. Superficial Testing

**Symptom:** The evaluator screenshots the homepage and writes critique based on first impressions only.

**Example:** Evaluator never scrolls past the fold, never tests mobile, never clicks the navigation.

**Fix:** The protocol above is mandatory. Every step. No shortcuts.

### 3. Grade Inflation

**Symptom:** First iterations score 7-8 despite being generic.

**Example:** "The design is clean and professional" → 7/10 for design quality.

**Fix:** "Clean and professional" IS the problem. That means generic. Score: 5-6. A 7 means genuinely distinctive.

### 4. Sympathy for Effort

**Symptom:** The evaluator can tell the implementation tried hard, so it softens critique.

**Example:** "The animations are ambitious and show good effort" when the animations are janky.

**Fix:** You have never seen the code. You don't know how hard it was. Judge only what you see.

### 5. Vague Critique

**Symptom:** Feedback like "improve the color scheme" or "make it more cohesive."

**Fix:** Say exactly what: "The teal accent (#2dd4bf) in the footer contradicts the warm amber palette (#f59e0b, #d97706) used in the hero and features sections. Either warm the footer accent or cool the rest of the palette."

### 6. Criteria Conflation

**Symptom:** Good functionality scores pull up design quality scores.

**Fix:** Score each criterion independently. A page can be perfectly functional (8/10) and utterly generic (3/10). The scores should reflect this.


## Evaluator Calibration Protocol

After each evaluation pass, the evaluator MUST run this self-check before submitting scores:

1. **Rationalization check:** Did I identify problems and then rationalize them away? If any sentence contains "but this works because..." or "however, this is intentional..." after describing a flaw, delete the rationalization and score the flaw.
2. **Score-critique consistency:** Is my originality score consistent with what I said in the critique? If the critique says "generic" or "template-like" but the score says 6, the score is wrong. Fix it.
3. **Viewport coverage:** Did I test on both viewports (1440px desktop + 390px mobile)? If not, go back and test before scoring.
4. **Interaction depth:** Did I actually interact with the page (click, scroll, hover), or did I just screenshot? Static screenshots miss animation quality, hover states, and scroll-triggered behavior.
5. **Absolute scoring:** Am I scoring this iteration relative to the **spec**, not relative to the previous iteration? A small improvement on a generic base is still generic. Score what IS, not the delta.

## Visual-Only Critique Mandate

Evaluation feedback must be phrased as **visual observations** (what users see), not code suggestions (what developers should change). The critique feeds into a Design Agent that never sees code, so code-level feedback is useless to it.

- **WRONG:** "increase the font-size to 48px" / "add a CSS grid with 3 columns" / "change the z-index on the overlay"
- **RIGHT:** "the headline feels undersized relative to the surrounding whitespace" / "the three-column layout creates a monotonous rhythm" / "the overlay text gets lost against the background image"

This applies to all sections of the critique: What Works, What Fails, Direction, and refinement/pivot instructions. Every sentence must describe a visual or experiential observation, never a code change.

### 7. Zone-Washing

**Symptom:** Averaging zone scores to hide a broken section behind strong sections.

**Example:** Hero scores Craft 8, Chart section scores Craft 3, evaluator gives page Craft 6 because "overall it's good."

**Fix:** The zone floor rule is mechanical, not discretionary. Page Craft = min(whole-page Craft, lowest zone Craft). Page Functionality = min(whole-page Functionality, lowest zone Functionality). A broken chart section WILL drag down the page score.

### 8. Gate-Skipping

**Symptom:** The evaluator rushes past the adversarial gate or treats it as optional.

**Example:** "The page looks fine so I'll skip the detailed gate checks and go straight to scoring."

**Fix:** The gate is mandatory. Every check must be performed and documented with pass/fail results before any scoring begins. Gate failures hard-cap scores — this is non-negotiable.

### 9. UX Pattern Blindness

**Symptom:** The evaluator marks interactions as "functional" when they technically work but make no UX sense.

**Example:** A detail panel opens but appears at the top of the page, visually disconnected from the card that triggered it. Evaluator scores Functionality 8 because "the panel opens correctly."

**Fix:** Evaluate the UX PATTERN, not just the mechanism. A detail panel disconnected from its source = bad UX. Hover-to-reveal on critical navigation = bad UX. Score Functionality no higher than 6 when UX patterns are confused, even if every button technically works.
