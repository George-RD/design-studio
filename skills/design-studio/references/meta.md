# Meta: improve Design Studio

Design Studio is a living experiment. Model capability changes which controls remain useful, but anecdotes alone do not justify changing the workflow.

## Sources of truth

- `SKILL.md` owns routing and public behaviour.
- `workflow.yaml` owns paths, schemas, transitions, budgets and decisions.
- agent files own role behaviour and isolation.
- focused references own procedures.
- run traces and external preference are evidence of actual behaviour.

Keep duplicated policy small. Version plugin metadata, skill, workflow and eval suite together.

## Inspect complete runs

Sample run directories, not only final screenshots. Compare:

- prompt, roots, capabilities and product context;
- direction assignment timing, three candidates and final selection;
- design descriptions and Builder fidelity flags;
- detector snapshots and finding lifecycle;
- screenshots, observations and critiques;
- event journal, resume points and failures;
- decisions, final selection and acceptance receipt;
- codified design DNA and tokens.

Look for recurring failure modes:

- the wrong app or context root is selected;
- capabilities are assumed rather than probed;
- a resumed run repeats a completed build or trusts a partial directory;
- candidates converge despite different names;
- unattended selection correlates with candidate order;
- Visual Director uses implementation language or appears source-anchored;
- Builder softens ambitious instructions without flags;
- Evaluator gives high scores to competent templates;
- fixed detector findings remain open, or reintroduced findings remain closed;
- mechanical facts appear in screenshot-only critique;
- later iterations become more complex while functionality falls;
- latest wins despite an earlier stronger build;
- finish review restarts an unbounded taste loop;
- acceptance and codified output point to different trees.

## Why the runtime controls exist

The controls should answer real failure classes:

| Failure class | Workflow response |
|---|---|
| Nested app or monorepo runs from the wrong directory | evidence-backed `roots.json` |
| Tool or browser access is assumed | `capabilities.json` before planning |
| Agent candidate ordering becomes hidden preference | precommitted slot hidden from Visual Director |
| A crash loses state or repeats expensive work | append-only events plus artifact-validated resume |
| Detector cache keeps stale issues or misses regressions | complete current snapshots with stable signatures |
| A corrected directory is accepted because it exists | final acceptance receipt with postconditions |
| Customer copy improves mechanically but loses meaning | frozen baseline plus qualitative copy gates |

Delete a control when representative evidence shows it no longer earns its cost.

## Tune criteria without creating a house style

Scoring language steers generation. Define qualities such as clarity, cohesion, specificity, craft and task fit. Named movements, fonts, palettes and composition examples belong in the user brief or one candidate, not always-loaded scoring prompts.

When runs look alike, audit prompt examples, candidate diversity axes and rubric nouns before adding more bans.

## Calibrate the Evaluator

Across representative first iterations:

- median scores materially above 6.5 suggest inflation;
- critiques without interaction evidence suggest superficial testing;
- Craft mirroring Design Quality suggests criterion conflation;
- high Originality on swappable pages suggests poor product-specificity calibration;
- post-ship user bugs suggest weak adversarial gates.

Use blind benchmark screenshots with known defects to test catch rate. Do not train the Evaluator only on its own previous prose.

## Ablation protocol

For a material model or workflow upgrade:

1. select representative prompts and fixed product contexts;
2. run the current workflow and record cost, time, scores and independent human preference;
3. remove or simplify exactly one layer;
4. repeat with the same seeds, assignment slots and budgets;
5. retain the layer only when quality, reliability or debuggability improves enough to justify its cost.

Test planner depth, candidate count, precommit assignment, zone screenshots, iteration budget, finish review and resume separately. Test the code-blind Visual Director and Builder split last because it addresses anchoring rather than context size.

## Metrics worth tracking

- root-resolution override and failure rate;
- capability downgrade rate;
- resume success and repeated-step rate;
- candidate-slot selection distribution;
- first-iteration score distribution;
- user-selected direction distribution;
- REFINE and PIVOT success rate;
- best iteration versus latest frequency;
- open primary finding rate and stale-finding rate;
- finish-review defect yield;
- acceptance postcondition failure rate;
- final user preference against one-pass and Impeccable-only baselines;
- time, tokens and browser operations per accepted run;
- waiver count and whether each traces to a real commitment.

A higher internal score is not proof of a better workflow. Prefer blinded external preference and real task success.

## Change discipline

A workflow change is complete only when:

- schemas and transitions terminate deterministically;
- roots and capability evidence are explicit;
- isolation tests pass;
- resume cannot overwrite completed iterations;
- detector snapshots cannot retain stale open state;
- eval cases cover the new behaviour and likely near-misses;
- docs describe current capability rather than roadmap;
- version metadata agrees;
- one greenfield and one overhaul smoke run complete in a browser-capable tool.
