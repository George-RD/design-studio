# Milestone 0 comparison run protocol

This protocol controls the comparative runs used to decide what Design Studio uniquely adds over Impeccable. It defines how evidence is produced; it does **not** claim that any comparison lane has completed.

## Acceptance contract

A lane result is admissible only when all of these are true:

1. `scripts/validate_benchmark_fixtures.py` accepts the frozen suite before preparation.
2. The run records the fixture version, suite lock digest, protocol digest, harness digest, lane, tool version, tool source and exact command.
3. The harness copies the frozen fixture into a fresh `input/` tree and rejects any later byte change.
4. Existing-surface baselines are copied into a separate mutable `work/` tree.
5. The lane writes its deliverable to the isolated `output/` tree and does not change `input/`.
6. Standard output, standard error, timestamps, measured duration, exit status and failed attempts are preserved.
7. A successful command remains `awaiting-evidence` until every required metric and every frozen acceptance check is supplied.
8. Raw observer evidence is preserved before a normalized result is written.
9. The completed output tree is SHA-256 receipted and later mutation makes validation fail.
10. The lane cannot declare itself preferred. Preference is recorded only after all three outputs for a fixture are anonymized and reviewed together.

The roadmap lane checkbox stays open until every fixture has one validated result for that lane. The parent comparison item stays open until all twelve lane runs and the blind preference evidence exist.

## Fair comparison rules

For one fixture, use the same:

- fixture version and `fixture-lock.json` digest;
- protocol digest and run-harness digest;
- model or agent harness, model version, context limits and approval policy where the lane permits them;
- machine class, browser version and viewport set;
- starting assets, brief, acceptance checks and maximum elapsed budget.

Only the workflow assignment may differ:

| Lane | Allowed workflow |
|---|---|
| `impeccable-alone` | Impeccable without Design Studio orchestration |
| `design-studio-current` | Design Studio v1.5 with Impeccable unavailable, exercising the current fallback path |
| `design-studio-impeccable` | Design Studio v1.5 with the pinned Impeccable capability available |

Do not add hints, corrections, examples or assets to one lane only. Do not expose other lane outputs during generation or lane-level evaluation.

A failed attempt is terminal. Keep it as evidence and prepare a new run ID for any recovery. Record the failed step, recovery actions and time in the successful run's evidence, with the failed run ID cited.

## Roles

- **Operator:** prepares and launches a lane. The operator may know the lane because it must configure the workflow.
- **Evidence observer:** verifies the declared viewports, interactions and acceptance checks against the rendered output. The observer records defects and metrics but does not select a winner.
- **Preference reviewer:** receives anonymized outputs only after all three lane results for a fixture validate. The reviewer must not see lane names, commands, tool versions, implementation history or costs until preference is locked.

For Design Studio lanes, preserve the project’s existing source-isolation rules. This benchmark protocol does not relax the Visual Director or Evaluator boundaries.

## Run lifecycle

### 1. Prepare

Run from the repository root:

```bash
python3 scripts/run_boundary_benchmark.py prepare \
  --fixture marketing-surface \
  --lane impeccable-alone \
  --run-id marketing-v1-impeccable-001 \
  --tool-name impeccable \
  --tool-version 3.5.0 \
  --tool-source pbakaus/impeccable@<exact-revision>
```

Preparation creates:

```text
harness-output/benchmarks/milestone-0/
  <fixture>/
    <lane>/
      <run-id>/
        run.json
        events.jsonl
        input/
        work/
        output/
        evidence/
```

`harness-output/` is ignored by Git. Publish selected evidence separately only after redacting secrets and checking licenses.

### 2. Execute

Use a lane wrapper that accepts the environment contract below and exits non-zero on an incomplete workflow:

```bash
python3 scripts/run_boundary_benchmark.py execute \
  --run-dir harness-output/benchmarks/milestone-0/marketing-surface/impeccable-alone/marketing-v1-impeccable-001 \
  -- <lane-wrapper> [arguments...]
```

The wrapper runs with `work/` as its current directory and receives:

| Variable | Meaning |
|---|---|
| `DESIGN_BENCHMARK_RUN_DIR` | absolute run root |
| `DESIGN_BENCHMARK_INPUT_DIR` | immutable copied fixture |
| `DESIGN_BENCHMARK_WORK_DIR` | mutable baseline or empty work tree |
| `DESIGN_BENCHMARK_OUTPUT_DIR` | required final deliverable tree |
| `DESIGN_BENCHMARK_EVIDENCE_DIR` | execution logs and lane evidence |
| `DESIGN_BENCHMARK_BRIEF` | exact frozen brief |
| `DESIGN_BENCHMARK_ACCEPTANCE` | exact frozen checks |
| `DESIGN_BENCHMARK_FIXTURE` | fixture ID |
| `DESIGN_BENCHMARK_LANE` | lane ID |
| `DESIGN_BENCHMARK_RUN_ID` | unique run ID |

The wrapper must:

- pass only the frozen brief, declared baseline and lane assignment into the workflow;
- copy the final runnable result to `DESIGN_BENCHMARK_OUTPUT_DIR`;
- leave `DESIGN_BENCHMARK_INPUT_DIR` unchanged;
- avoid network-fetched assets unless the same pinned asset is made available to every lane;
- record any model, plugin, browser or provider versions not already represented by the tool record.

A zero exit code records measured elapsed time but does not complete the run.

### 3. Observe and record evidence

Create a JSON object with this shape:

```json
{
  "schemaVersion": 1,
  "taskClarity": {
    "score": 4,
    "evidence": "No clarification was required; one assumption was recorded before generation."
  },
  "originality": {
    "score": 7,
    "evidence": "Specific visual and interaction evidence from the rendered output."
  },
  "functionalDefects": [
    {
      "id": "mobile-overflow",
      "severity": "primary",
      "evidence": "At 390x844 the document width measured 428 CSS pixels."
    }
  ],
  "tokenCost": {
    "status": "unavailable",
    "inputTokens": null,
    "outputTokens": null,
    "reason": "The selected harness did not expose token accounting."
  },
  "toolCost": {
    "status": "unavailable",
    "amount": null,
    "currency": null,
    "reason": "The selected harness did not expose monetary cost."
  },
  "failedSteps": [],
  "recoveryEffort": {
    "minutes": 0,
    "actions": []
  },
  "acceptanceChecks": [
    {
      "id": "<exact ID from acceptance.json>",
      "status": "pass",
      "evidence": "Observed result and evidence path."
    }
  ]
}
```

Rules:

- `taskClarity.score` is 1–5; `originality.score` is 1–10.
- Defect severity is `primary` or `advisory`.
- Cost status is `measured`, `estimated` or `unavailable`. Unavailable values require a reason; do not invent a zero.
- `acceptanceChecks` must cover every frozen check exactly once with `pass`, `fail` or `blocked`.
- Evidence should name screenshots, measurements, browser traces or interaction observations. A bare assertion is not sufficient.
- Do not add `elapsedSeconds`; the harness owns measured duration.
- Do not add `outputPreference`; the later blind comparison owns it.

### 4. Complete

```bash
python3 scripts/run_boundary_benchmark.py complete \
  --run-dir <run-directory> \
  --evidence <observer-evidence.json>
```

Completion preserves the supplied evidence as `evidence/lane-evidence.json`, writes `evidence/result.json`, receipts the output tree and changes the run to `complete`.

### 5. Validate

```bash
python3 scripts/run_boundary_benchmark.py validate --run-dir <run-directory>
```

Validation checks the input receipt, event sequence and state, execution receipt, preserved evidence, normalized result and completed output tree. A changed fixture or output must fail instead of being treated as the original result.

## Evidence still required after lane completion

Lane completion intentionally leaves:

```json
"outputPreference": {
  "status": "comparison-level",
  "reason": "pending blind comparison"
}
```

A separate comparison bundle must later:

1. require one complete, valid result from each lane for the same fixture version and digests;
2. copy outputs under random labels;
3. hide lane and tool provenance from the preference reviewer;
4. record the reviewer, rubric, ranking or tie and evidence;
5. reveal provenance only after the preference receipt is immutable;
6. aggregate the remaining metrics without replacing raw lane evidence.

Until that bundle exists and all twelve lane runs validate, the comparative roadmap work is unfinished.
