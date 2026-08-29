# Internal runtime contract

This file defines the **host-neutral deterministic seam** used by the Design Studio Agent Skill and by optional host adapters. It is an internal protocol, not a public CLI and not an executable package by itself.

## Authority boundaries

- `workflow.yaml` owns the step graph and artifact schemas.
- `references/runtime-integrity.md` owns the integrity invariants for roots, capability evidence, resume, append-only events, unattended assignment and final acceptance.
- This contract owns the names, inputs/outputs and failure semantics of deterministic operations that a supported run may invoke.
- This contract does not restate those schemas. Callers write and validate the shapes defined by `workflow.yaml` and obey the invariants in `references/runtime-integrity.md`.
- Source-blind Visual Director/Evaluator boundaries and immutable completed iterations are preconditions. No runtime adapter may weaken them.

The seam deliberately describes **what must happen**, not which language or current repository script performs it. The v1.5 repository has no product-runtime script family to promote wholesale: current benchmark/capability scripts remain research or repository-support tooling unless a later migration ticket explicitly extracts a supported helper.

## Stable operations

| Operation | Inputs | Result / durable evidence |
|---|---|---|
| `initialise` | prompt identity, mode, requested budget, optional run ID | create or reopen the run contract; write `run.json`, initialise `scores.json`, and record completion through `append_event` |
| `resume_validate` | run identity plus recorded manifests, events and immutable iteration evidence | either the first incomplete valid workflow step or an explicit invalid/blocked result; never overwrite completed evidence |
| `resolve_roots` | explicit target plus repository/application evidence | `roots.json` containing proven repo/app/context roots or external-URL status |
| `probe_capabilities` | actual host/tool probes and target evidence | `capabilities.json`, an evaluation plan and any required budget clamp; missing required capability blocks before planning |
| `prepare_direction_assignment` | run identity, iteration, candidate IDs, pinned/user-selection mode | committed `direction-assignment.json` before candidate generation, with hidden unattended seed/index |
| `mechanical_preflight` | current immutable site, serve contract, detector availability and applicable design/brief constraints | one complete current `mechanical-findings.json` snapshot with detector/evidence metadata; old findings do not stay open by history alone |
| `decide` | current observation, current mechanical snapshot, score history, run budget/pivot state and selection mode | one ordered workflow decision and transition, recorded through `append_event`; visual judgement remains Evaluator evidence rather than runtime invention |
| `finish_select` | eligible immutable evaluated iterations and current mechanical evidence | `finish/selection.json`, copied selected tree/serve contract/direction and fresh viewport evidence |
| `finish_correction_decide` | selected-tree evidence plus correction verdict, mechanical snapshot and viewport evidence | deterministic choice of accepted corrected tree or retained selected tree in `finish/final-tree.json` |
| `accept` | final-tree declaration, source iteration, serve evidence, viewport evidence, mechanical snapshot and immutability/tree-manifest evidence | `finish/acceptance.json`; failure halts without publishing or codifying the tree |
| `report` | final run evidence, assumptions, decisions, finish and acceptance state | `report.md`, terminal `run.json` state and final `append_event` record |
| `halt` | exact failed or blocked contract plus current durable run evidence | preserve completed artifacts, append the exact failure through `append_event`, set terminal halted state and publish no winner or accepted tree |
| `append_event` | step, status, sequence, iteration, artifact paths and exact message/failure contract | append one new line to `events.jsonl`; earlier events are never edited |

These identifiers are the stable internal vocabulary. A host may implement them directly or through shipped helpers introduced later, but adapters must preserve their observable artifacts and failure semantics.

## Capability and failure semantics

Required Studio capabilities are `file_io`, `shell` and `isolated_subagents`. If any required capability is absent or cannot be proven, **block before planning**. Record the failed probe when the host can still write evidence. Do not substitute a smaller workflow.

Visual-decision capability is represented by a runnable/reachable target plus browser automation able to attempt the required viewports:

- `full`: Studio may build, evaluate and select only when visual-decision capability is proven.
- `build-once-unselected`: when Studio can build but cannot make browser-grounded visual judgement, clamp the build budget to one, run the current mechanical preflight, preserve the build and halt without a winner.
- `mechanical-review`: Review may return deterministic mechanical evidence with `visual_status: unverified` when visual inspection is unavailable or a required viewport cannot be verified.

An unknown, errored or incomplete probe is not success. Capability handling must be explicit and must **never silently** return `full`, invent a visual score, or claim a lower-quality path is equivalent.

Failures are durable workflow facts. A deterministic operation must either produce its declared valid evidence or route through `halt` with the exact blocked/failed contract. Partial evidence that is already durable is preserved for diagnosis and resume.

## Mechanical detector boundary

The seam owns the normalized **current mechanical snapshot contract**, not a particular detector implementation. The existing optional Impeccable/fallback branch is migration debt: detector availability may be recorded, but an external CLI is not a required runtime dependency and its presence must not create a different supported quality mode. #47/#50 own later method/detector consolidation.

Mechanical checks report source/browser-computed facts and severity/waiver evidence. They do not assign visual quality and do not replace the source-blind Evaluator.

## Review lane

Review uses the same capability/evidence semantics without running the Studio iteration graph. Host adapters map Review input into the canonical skill, run the deterministic root/capability/mechanical operations needed by `references/review/polish.md`, and use `mechanical-review` when visual verification is unavailable. Review adapters may not create a separate detector policy or degradation mode.

## Adapter contract

A host adapter may:

1. translate host-specific input into the fields in `invocation.md`;
2. provide concrete implementations for host capabilities such as isolated subagents, file I/O, shell and browser automation;
3. invoke the operations above in the order required by the canonical skill/workflow; and
4. translate the final artifacts/result back to the host.

A host adapter may not own workflow decisions, artifact schemas, design methods, capability downgrade policy or acceptance rules. Claude compatibility commands are adapters over this contract, not alternative runtimes.

## Research boundary

The following are **excluded from the runtime seam**: blind comparison, lane matrix generation, benchmark fixture validation, model probing, preference transactions and other Milestone 0 research harness behavior.

Repository research tooling may call a genuinely shared shipped helper later, but a supported installed Design Studio run must not import or shell into benchmark/research tooling merely because similar machinery already exists there. #49 owns the physical shipped-runtime/research separation after this seam is established.
