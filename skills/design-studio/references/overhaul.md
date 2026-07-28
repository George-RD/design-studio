# Overhaul mode

Overhaul is the Studio path for an existing surface that needs a material redesign. It is not a Review-only polish pass.

## Trigger

Use overhaul when `existing_site` or `existing_url` is present and the user asked to redesign, rebuild, rebrand, change direction or materially raise quality/originality.

Use Review when the user asked to audit or polish without replacing the visual world.

## Preservation contract

Before creating directions, separate four things:

1. **Product truth** — purpose, audience, real capabilities, factual copy and evidence.
2. **Behaviour** — routes, data contracts, tasks, interaction states and accessibility obligations.
3. **Explicit commitments** — identity assets, terminology, information architecture or visual elements the user said to retain.
4. **Incumbent styling** — layout, palette, type, component chrome and motion that may be replaced.

The first three are preserved unless the user changes them. Incumbent styling is evidence and an anti-reference, not default authority.

Write the result into the run's `spec.md`, `sprint-contract.md` and `surface-brief.md`.

## Baseline capture

Store the baseline under `harness-output/runs/<run-id>/baseline/`.

When a local tree is provided:

- inspect source only in Planner/Orchestrator/Builder contexts;
- discover the real start command, route and readiness condition;
- serve the incumbent without copying it into the final compatibility site;
- capture verified 1440×900 and 390×844 screenshots when possible;
- record console/resource failures and primary interaction notes;
- retain the original source path as Builder substrate.

When only a URL is provided:

- capture the same browser evidence;
- record that the Builder must start fresh unless source arrives later.

When capture fails, write the exact limitation. Direction can proceed from product truth and goals, but later Studio evaluation still requires browser capability.

## Isolation

| Role | Baseline render | Existing source | Full design contract |
|---|---:|---:|---:|
| Planner | yes | yes | no |
| Visual Director | yes | no | writes it |
| Builder | optional | yes | yes |
| Evaluator | live current build only | no | no |
| Orchestrator | yes | as needed | yes |

Never paste HTML, CSS, JSX, component names, selectors or implementation diffs into the Visual Director context.

## Direction rules

- Produce exactly three viable, unranked candidates from product truth, constraints and baseline screenshots.
- Treat the baseline as the thing to beat, not a composition to cosmetically reskin.
- Preserve confirmed information architecture only when the sprint contract requires it.
- User or deterministic seed selects the direction; the Visual Director does not choose its own winner.
- A candidate that differs only by typeface, colour or decoration is not a materially different overhaul direction.

## Builder seed rules

- Iteration 1 may use `existing_site` as behaviour/content substrate but writes only to `iterations/1/site/`.
- The original tree and earlier iteration directories remain untouched.
- REFINE copies the selected/current iteration into the next immutable iteration and changes only what the critique justifies.
- PIVOT starts from clean product behaviour/content and abandons the prior visual implementation.
- The Builder records preserved, replaced, equivalent and blocked instructions in `design-flags.json`.

Never seed or mutate `harness-output/site/` during iteration. That compatibility path is populated only after final selection.

## Failure cases

| Situation | Action |
|---|---|
| No browser for baseline | Record limitation; direction may proceed, but no final visual decision without later browser evaluation |
| URL only | Capture baseline; Builder starts fresh |
| Path not serveable | Record source path and failed command; Builder may still use the tree as substrate |
| Only one viewport captured | Record actual viewport; do not relabel it as the missing viewport |
| Existing copy contains unverified claims | Preserve as incumbent content but flag for user confirmation before publishing |

Workflow paths, budgets and decisions remain authoritative in `../workflow.yaml`.
