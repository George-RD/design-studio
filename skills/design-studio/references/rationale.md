# Rationale (Meta / cold path)

Cold-path material for the Meta lane and user education. Not required to run the Studio loop.

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

The fix: the Design Agent never sees code. It receives only screenshots, the evaluator's visual critique, and the spec. Its output is a design description — a prose document describing what the page should look like, not how to implement it. The Implementation Agent then receives this description alongside the existing code and faithfully executes it.
