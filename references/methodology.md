# Harness Methodology

Source: "Harness design for long-running application development" by Prithvi Rajasekaran, Anthropic Labs (March 24, 2026).

## Origin

The methodology draws from Generative Adversarial Networks (GANs): a generator and discriminator (evaluator) that improve through adversarial feedback. Applied to frontend design, this means:

- A **generator agent** creates frontends from prompts
- An **evaluator agent** interacts with live pages via Chrome browser automation (claude-in-chrome MCP) and scores against explicit criteria
- **Feedback loops** back to the generator for iteration
- The evaluator is **separated** from the generator — it never sees code, only rendered output

## Key Findings

### Design Criteria Must Be Weighted

Four criteria were established: design quality, originality, craft, and functionality. Design quality and originality are weighted higher because Claude already performs well on technical competence (craft) and usability (functionality) by default. The harness concentrates pressure where the model is weakest.

### Criteria Wording Steers Generation

The specific language in rubrics shapes what gets generated. Phrases like "museum quality" push toward particular visual convergence. Criteria should describe qualities (cohesion, distinctiveness) not aesthetics (museum-like, editorial).

### Self-Evaluation Fails for Subjective Tasks

When agents evaluate their own output, they confidently praise mediocre work. This is particularly acute for design tasks where no binary correctness check exists. Separating the evaluating agent from the generating agent is more tractable than making generators self-critical.

### Live Page Interaction is Essential

The evaluator uses Chrome browser automation (claude-in-chrome MCP) to interact with running pages — not just review code or static screenshots. This catches rendering bugs, broken interactions, and layout issues that code review misses. The evaluator navigates, clicks, scrolls, and hovers as a real user would.

### Iteration Produces Breakthrough Results

Runs typically involve 5-15 iterations, with each cycle pushing toward more distinctive directions. A notable example: when prompted to create a Dutch art museum website, by iteration 10 the generator abandoned its initial dark-themed approach. It reimagined the site as a 3D spatial experience with CSS-perspective flooring, artwork hung on walls, and doorway-based navigation between gallery rooms.

### Architecture: From Blog Baseline to Plugin Extension

The blog originally described a 3-agent loop (Planner → Generator → Evaluator). This harness extends it to a **4-agent architecture** by splitting the Generator into two isolated roles:

> **Blog baseline → Plugin extension:** The blog's single "Generator Agent" is split into a **Design Agent** (visual-only, never sees code) and an **Implementation Agent** (faithfully executes design descriptions). This defeats code-anchoring bias, where seeing existing code constrains creative vision. See SKILL.md for the full current architecture.

1. **Planner Agent** — Expands simple prompts into full product specifications. Focuses on scope and high-level technical design, avoiding granular implementation details that cascade errors. Identifies opportunities to weave AI features throughout specs.

2. **Design Agent** — Receives screenshots and evaluator critique, produces prose design descriptions specifying layout, typography, color, and spatial rhythm. Never sees source code — this isolation defeats code-anchoring bias, where seeing existing implementations constrains creative vision (stronger models are MORE affected).

3. **Implementation Agent** — Receives the Design Agent's prose design description and faithfully translates it into working code. Does not second-guess the Design Agent's creative decisions. Uses git for version control.

4. **Evaluator Agent** — Uses Chrome browser automation (claude-in-chrome MCP) to interact with running applications as users would, testing UI features, visual quality, and interaction patterns. Before each build cycle, planner and evaluator negotiate a "sprint contract" defining testable success criteria.

### Evaluator Tuning Is Hard

Initially, Claude would identify legitimate issues then rationalize them as non-critical. It tested superficially rather than probing edge cases. Iterative prompt refinement — reading logs to find judgment divergences — gradually improved QA performance. Limits remain: small layout issues, unintuitive interactions, and undiscovered bugs in deeply nested features.

### Scaffolding Should Be Periodically Re-evaluated

With Claude Opus 4.6's release (better planning, sustained agentic tasks, larger codebase operation), sprint decomposition that helped Opus 4.5 could be abandoned. The evaluator isn't a fixed yes-or-no decision but worth the cost when tasks sit beyond what current models reliably handle solo.

### Cost and Duration

| Harness | Duration | Cost |
|---------|----------|------|
| Solo agent (no harness) | 20 min | $9 |
| Full harness (retro game maker) | 6 hr | $200 |
| Full harness (DAW, Opus 4.6) | 3 hr 50 min | $125 |

The harness is significantly more expensive but produces categorically better results for ambitious projects.

## The Conviction

> "The space of interesting harness combinations doesn't shrink as models improve. Instead, it moves, and the interesting work for AI engineers is to keep finding the next novel combination."

Experiment with production models, read traces on realistic problems, tune performance toward desired outcomes. Upon new model releases, re-examine harnesses — remove non-load-bearing pieces and add new components to achieve previously impossible capabilities.

## Extensions to the Original Methodology

### Zone-Based Evaluation

The original methodology scored pages holistically — one set of 4 scores for the entire rendered output. In practice, holistic scoring masks subsystem problems: a beautiful hero section can average away a broken sidebar, clipped graph text, or overflowing footer.

Zone-based evaluation extends the evaluation step: after the full-page screenshot, the evaluator identifies visual zones (header, hero, content sections, graphs/charts, sidebar, footer), captures each at 2x zoom, and scores independently. The final craft and functionality scores use the minimum of whole-page and worst-zone scores, ensuring no zone gets a free pass.

### Adversarial Testing Gate

Without explicit "try to break it" requirements, evaluators optimize for visual impression and miss rendering bugs. The adversarial gate is a mandatory pre-scoring step: check for text overflow, element overlap, responsive breakage, console errors, and broken interactions. Gate failures impose hard score caps (e.g., text clipping caps craft at 5), preventing high scores on technically broken implementations.
