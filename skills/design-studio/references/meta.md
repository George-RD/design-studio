# Meta: improve Design Studio

## Purpose

Tune Design Studio's workflow and method kernel from representative evidence rather than anecdotes, while preventing prompt growth and duplicate authorities.

## Triggers

Load for Meta lane work, method-intake decisions, repeated owner corrections, dogfood gaps, model changes, or a meaningful upstream method change.

## Required context

Inspect complete run traces: prompt, roots/capabilities, direction assignment/candidates/selection, design flags, mechanical snapshots, screenshots/observations, events/resume, finish acceptance, and final codification. For external intake also load the exact pinned source metadata and the relevant concept in `docs/method-authority-map.json`.

## Outputs and handoff

Produce one bounded change hypothesis with the failure class, current authority, proposed smallest method/control change, evidence needed, and acceptance/ablation test. Update routing or a leaf only after the evidence justifies the maintenance cost.

## Authority boundary

`SKILL.md` owns the small public kernel, `workflow.yaml` owns lifecycle mechanics, agents own isolated role behaviour, and focused references own specialist procedures. Meta may evaluate those authorities but must not create competing copies. `method-router.json` maps signals to leaves; it does not own the leaf methods.

## Failure behavior

Do not change the workflow because one run felt weak. Do not import a whole upstream command system for one useful heuristic. Reject a candidate when it adds prompt volume or maintenance without improving quality, reliability or reducing human correction.

## Evaluation hooks

For material changes use representative prompts and fixed contexts, vary one layer where possible, and compare task success, independent preference, reliability, cost and intervention rate. Useful metrics include root/capability failures, resume success, candidate convergence, REFINE/PIVOT success, stale findings, finish-review yield, acceptance failures and user preference. A higher internal score alone is not proof.

## Method leaf contract

Every routed specialist leaf declares: Purpose, Triggers, Required context, Outputs and handoff, Authority boundary, Failure behavior, Evaluation hooks, plus Source provenance when an external method is formally adopted. Keep provenance exact and method-sized.

## Source provenance

No external method is adopted into this Meta leaf. External sources remain governed by `docs/method-sources.json` and concept-level dispositions in `docs/method-authority-map.json`.
