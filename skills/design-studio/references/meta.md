# Meta: improve the harness

Design Studio is a living experiment. Model capability changes which scaffolding remains useful, but it does not justify changing the workflow from anecdotes alone.

## Sources of truth

- `skills/design-studio/SKILL.md` owns routing and public behaviour.
- `skills/design-studio/workflow.yaml` owns paths, schemas, transitions, budgets and decisions.
- agent files own role behaviour and isolation.
- reference leaves own procedures.
- run traces are evidence of actual behaviour.

Keep duplicated policy to a minimum. Version plugin metadata, skill, workflow and eval suite together.

## What to inspect

Sample complete run directories, not only final screenshots. Compare:

- prompt and product context;
- the three direction candidates and selection method;
- design descriptions;
- design flags and mechanical findings;
- screenshots, observations and critiques;
- decisions and final selection;
- finish findings and open items;
- codified design DNA/tokens.

Look for recurring failure modes:

- candidates converge despite different names;
- the Visual Director uses implementation language or appears source-anchored;
- the Builder softens ambitious instructions without flags;
- the Evaluator gives high scores to competent templates;
- mechanical facts appear in screenshot-only critique;
- two components claim decision authority;
- later iterations become more complex while functionality falls;
- the latest iteration is selected despite an earlier stronger build;
- finish review restarts an unbounded taste loop.

## Tune criteria without creating a house style

Scoring language steers generation. Define qualities—clarity, cohesion, specificity, craft, task fit—not preferred aesthetics. Named movements, fonts, palettes and composition examples belong in a user's brief or a single candidate derivation, not in always-loaded scoring prompts.

When runs look alike, audit prompt examples and rubric nouns before adding more anti-pattern bans.

## Calibrate the Evaluator

Across representative first iterations:

- median scores materially above 6.5 suggest inflation;
- critiques without interaction evidence suggest superficial testing;
- Craft mirroring Design Quality suggests criterion conflation;
- high Originality on swappable pages suggests poor product-specificity calibration;
- post-ship user bugs suggest weak adversarial gates.

Use blind benchmark screenshots with known defects to test catch rate. Do not train the evaluator on its own previous prose only.

## Ablation protocol

For a material model or harness upgrade:

1. select several representative prompts and fixed product contexts;
2. run the current workflow and record cost, time, scores and independent human preference;
3. remove or simplify exactly one layer;
4. repeat with the same seeds and budgets;
5. retain the layer only when quality, reliability or debuggability improves enough to justify its cost.

Test planner depth, candidate count, zone screenshots, iteration budget and finish review separately. Test the code-blind Visual Director/Builder split last: it addresses anchoring rather than context-window size.

## Metrics worth tracking

- first-iteration score distribution;
- user-selected direction distribution;
- REFINE and PIVOT success rate;
- best iteration versus latest iteration frequency;
- open primary finding rate;
- finish-review defect yield;
- final user preference against one-pass and Impeccable-only baselines;
- time, tokens and browser operations per accepted run;
- number of waivers and whether they trace to real commitments.

A higher internal score is not proof of a better harness. Prefer blinded external preference and real task success.

## Change discipline

A workflow change is complete only when:

- schemas and transitions still terminate deterministically;
- isolation tests pass;
- immutable paths still preserve earlier builds;
- eval cases cover the new behaviour and likely near-misses;
- docs describe current capability rather than roadmap;
- version metadata agrees;
- one greenfield and one overhaul smoke run complete in a browser-capable harness.
