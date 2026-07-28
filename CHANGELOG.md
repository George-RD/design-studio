# Changelog

## 2.0.0

### Architecture

- Preserved the source-code isolation of DesignAgent and Evaluator.
- Added durable `.design-studio/` product, design, and surface context.
- Added per-surface modes: persuade, operate, read, and experience.
- Added explicit preserve, extend, and replace change semantics.
- Replaced the legacy open-ended default loop with component, standard, and ambitious profiles.
- Added `HOLD` for blocked, unevaluated, or below-floor outcomes.

### Quality control

- Added a zero-dependency deterministic frontend preflight with JSON output and documented suppression.
- Added tests for accessibility blockers, motion/focus signals, clean surfaces, suppressions, and invalid modes.
- Required preflight before live evaluation while retaining the browser as the only source of visual scores.
- Limited normal browser verification to one batched initial pass and one confirmation pass.

### Commands and context

- Added `/design-studio:init`.
- Updated `/design-studio:create` for modes, semantics, profiles, context, preflight, and four-way decisions.
- Updated `/design-studio:review` to preserve the incumbent world and return `HOLD` without live evidence.
- Added templates for PRODUCT.md, DESIGN.md, and surface briefs.

### Evaluation

- Added mode-specific weights and score floors.
- Reduced blanket originality pressure on operational and reading interfaces.
- Changed template-pattern rules from universal bans to contextual diagnostics.
- Prevented budget exhaustion from being treated as a pass.

### Package

- Rewrote the public site to express the v2 architecture and expose all three commands.
- Added package contract validation and GitHub Actions CI.
- Expanded eval coverage for context, mode routing, preflight, review preservation, browser failure, and budget exhaustion.

### Influence

- Adapted durable-context, surface-mode, bounded-QA, and deterministic-checking principles identified through comparison with pbakaus/impeccable.
- No Impeccable source files were vendored; Design Studio remains MIT.
