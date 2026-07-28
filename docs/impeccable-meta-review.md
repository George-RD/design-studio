# Meta-review: Impeccable × Design Studio

## Question

Which parts of Impeccable make Design Studio materially better without erasing the reason Design Studio exists?

The answer is not “combine every prompt.” The two systems have different centres of gravity:

- **Design Studio v1:** independent visual authorship and judgment through agent isolation.
- **Impeccable:** strong context/routing discipline, practical craft guidance, deterministic enforcement, and bounded verification.

Version 2 keeps Design Studio's architectural centre and imports the operating controls that were missing.

## Comparison

| Dimension | Design Studio v1 | Impeccable | v2 decision |
|---|---|---|---|
| Visual authorship | Strong: DesignAgent never sees code | Strong design guidance, usually within a unified skill workflow | Keep Design Studio's isolated DesignAgent |
| Judgment independence | Strong: code-blind live Evaluator | Strong QA guidance and mechanical detector | Keep isolated Evaluator; add deterministic preflight before it |
| Product memory | Weak: each run can rediscover context | Strong product/design/surface context | Add durable `.design-studio/` context |
| Preserve vs redesign | Present but spread across references | Clear refinement/redesign semantics | Make preserve/extend/replace explicit in every surface brief |
| Surface purpose | One mostly universal scoring model | Visitor modes distinguish persuasion, operation, reading, experience | Add four modes with different weights and floors |
| Iteration cost | Expensive eight-plus-pass default | Bounded verification and practical craft floor | Add component/standard/ambitious profiles and batched passes |
| Failure state | Best remaining result could be treated as shippable | Stronger stop/check discipline | Add `HOLD`; budget exhaustion is never a pass |
| Mechanical defects | Mostly delegated to model/browser review | Deterministic detector and hooks | Add zero-dependency preflight with tests and CI |
| Anti-generic rules | Strong but could become blanket taste policy | Contextual craft floor and detector signals | Convert bans into mode/context-sensitive diagnostics |
| Public command surface | Create and Review; site lagged runtime | Broad command catalog | Add only Init; keep a three-command product |
| Design-system continuity | Codification exists after runs | Durable design context is first-class | Promote candidate design context only after live `SHIP` |

## Decisions

### 1. Preserve the code-blind split

This remains Design Studio's defensible mechanism. A unified all-seeing agent is cheaper, but it is more likely to optimize around the current component tree and approve its own compromises.

Imported guidance must fit around this boundary rather than dissolving it.

### 2. Add durable context, but separate ownership

A single design brief becomes stale and overloaded. V2 separates:

- product truth (`PRODUCT.md`);
- durable visual world (`DESIGN.md`);
- one surface's job and constraints (`surfaces/<slug>.md`).

This reduces repeated discovery while allowing one product to contain different modes and surface strategies.

### 3. Make quality mode-specific

The old universal originality pressure had a predictable failure: it could reward unusual task interfaces and punish appropriate operational patterns.

V2 keeps high originality pressure for `persuade` and `experience`. `operate` and `read` lower the originality floor and increase functionality/craft weight. Familiar patterns remain accountable to task-specific information design, state, and quality.

### 4. Replace the default long loop with bounded profiles

Eight-to-twelve passes can improve a flagship page, but as a default they create cost, latency, and diminishing returns. They also encourage the Evaluator to keep generating critique because capacity exists.

V2 uses:

- component: two evaluations, no automatic pivot;
- standard: three evaluations, one pivot;
- ambitious: five evaluations, two pivots.

Verification is batched across viewports/states. A user can expand the budget after seeing evidence.

### 5. Add `HOLD`

`SHIP` should mean the result qualifies. It should not mean “this is the best version produced before the loop stopped.”

`HOLD` covers missing browser evidence, unresolved blockers, incomplete state/viewport coverage, product decisions, and below-floor results after the budget. The current output can still be delivered as a preview.

### 6. Put deterministic checks before live judgment

The live Evaluator is expensive and should focus on hierarchy, comprehension, responsiveness, interaction, and visual quality. Missing alt attributes, placeholder links, removed focus outlines, and similar mechanical defects can be detected first.

The detector does not replace the browser and does not assign scores. Signals that depend on context remain subject to live judgment.

### 7. Keep anti-patterns defeasible

A list of common AI patterns is useful as a reflex check. As an absolute rule, it becomes another style monoculture.

V2 applies a template ceiling only when the axis was free, the mode did not justify the pattern, product-specific logic is absent, and the composition is interchangeable. Explicit user/brand commitments remain authority unless they create an objective blocker.

### 8. Keep the product small

Impeccable's broad command catalog is useful in its architecture. Copying it would make Design Studio harder to explain and maintain.

V2 exposes only:

- `/design-studio:init`;
- `/design-studio:create`;
- `/design-studio:review`.

Everything else is a lane or internal contract.

## Second-order effects

### More context can become stale

Mitigation: provenance, explicit unknowns, contradiction logging, and an authority order. The live product can disprove old context; filenames are not automatically truth.

### `HOLD` will reduce apparent autonomous success

This is intentional. It should increase decision integrity and make missing browser evidence visible. The cost is that users may need to approve a budget expansion or product decision more often.

### Modes add routing complexity

Mitigation: mode is stored per surface and chosen from primary visitor success. Evals cover ambiguous cases. A secondary conversion goal does not turn an operational screen into a persuasion surface.

### Deterministic rules can create false positives

Mitigation: signals are severity-labelled, suppressions are documented, and ignored findings remain in evidence. A rule should move into code only when it is reliably mechanical; aesthetic judgment stays with the Evaluator.

### Bounded loops may stop before a rare breakthrough

Mitigation: the ambitious profile and explicit user budget expansion remain available. The default optimizes expected value, not theoretical maximum polish.

### Delayed design-context promotion slows documentation

Mitigation: candidate context is still written during the run. Requiring `SHIP` prevents failed or unevaluated directions from becoming future authority.

## Dogfood target

The public `docs/index.html` was rebuilt using the v2 principles:

- `persuade` mode;
- explicit product mechanism in the first view;
- the isolated-agent architecture made structural rather than described only in prose;
- an interactive mode-weight exhibit tied to a real v2 feature;
- no repeated rounded-card grid;
- one authored ticker motion with reduced-motion fallback;
- all three commands and the `HOLD` contract exposed publicly;
- deterministic preflight included in package validation.

A live browser visual pass is still required before treating the page as visually qualified. Static preflight and code review are not substitutes.

## Measures for future iterations

Track across real dogfood runs:

- median live evaluation passes by profile;
- percentage of runs that incorrectly attempt `SHIP` without browser evidence;
- percentage of later runs that reuse product/surface context without rediscovery;
- mode-selection errors found by users;
- deterministic finding precision and suppression rate;
- change requests caused by preserve/replace misunderstanding;
- output quality versus v1 on the same brief, including counterexamples where v1 was stronger;
- number of `HOLD` results later resolved by one clear decision versus abandoned as process friction.

## Rollback or narrowing triggers

Narrow or revert a v2 mechanism when evidence shows:

- mode routing creates more wrong decisions than the universal rubric it replaced;
- the detector's false-positive cost exceeds the blockers it catches;
- context files routinely become stale and mislead later runs despite provenance rules;
- bounded profiles repeatedly stop one pass before qualification without reducing waste elsewhere;
- `HOLD` becomes a vague escape rather than an evidence-backed state;
- public complexity makes the plugin harder to use without improving output.

The merge is successful only if the process becomes more truthful and efficient while preserving or improving the rendered results.
