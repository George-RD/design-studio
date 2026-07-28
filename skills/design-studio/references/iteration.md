# Compatibility reference: iteration

This path remains for older commands and third-party runners. It is not a second iteration or decision authority.

The ordered decision table, budgets, pivot limits, immutable artifact paths and termination rules live only in `../workflow.yaml`.

The Orchestrator must:

1. validate the current iteration's observation and mechanical evidence;
2. append the observation to the run's `scores.json`;
3. apply the workflow decision table in order;
4. write exactly one of REFINE, PIVOT, SHIP or HALT with a termination reason;
5. preserve every evaluated iteration under `harness-output/runs/<run-id>/iterations/<n>/`;
6. select the strongest eligible iteration at finish rather than assuming the latest is best.

The Evaluator cannot recommend or write a decision. No agent self-commits, and version-control history is not used as artifact storage. Do not recreate the legacy mutable `harness-output/site/` loop or duplicate thresholds here.
