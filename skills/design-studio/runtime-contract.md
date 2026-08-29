# Internal runtime contract

This file defines the **host-neutral deterministic seam** used by the Design Studio Agent Skill and optional host adapters. It is an internal protocol, not a public CLI or executable package by itself.

## Authority boundaries

- `workflow.yaml` owns the step graph and artifact schemas for interactive Studio.
- `references/document/document.md` owns the progressively disclosed paginated-artifact procedure without creating a second copy of the Studio graph.
- `references/runtime-integrity.md` owns the integrity invariants for roots, capability evidence, resume, append-only events, unattended assignment and final acceptance.
- This contract owns deterministic operation names, inputs/outputs and failure semantics used by supported lanes.
- This contract does not restate those schemas. Callers obey the lane authority plus `references/runtime-integrity.md`.
- Source-blind Visual Director/Evaluator boundaries and immutable completed iterations are preconditions. No adapter or renderer may weaken them.

The seam describes **what must happen**, not which language or renderer performs it. Repository benchmark/capability scripts remain research/support tooling. A shipped helper is introduced only for bounded deterministic behavior a supported operation actually needs.

## Stable operations

| Operation | Inputs | Result / durable evidence |
|---|---|---|
| `initialise` | prompt identity, mode, requested budget, optional run ID | create/reopen run contract; write `run.json`, initialise scores/evidence and record completion through `append_event` |
| `resume_validate` | run identity plus recorded manifests/events/immutable iteration evidence | first incomplete valid step/procedure action or explicit invalid/blocked result; never overwrite completed evidence |
| `resolve_roots` | explicit target plus repository/application/document evidence | `roots.json` containing proven roots/target status |
| `probe_capabilities` | actual host/tool probes and target evidence | `capabilities.json`, evaluation plan and any required budget clamp; missing generic required capability blocks before planning |
| `prepare_direction_assignment` | run identity, iteration, candidate IDs, pinned/user-selection mode | committed assignment before candidate generation, with hidden unattended seed/index |
| `mechanical_preflight` | current source, browser and/or page-artifact facts plus applicable constraints and optional comparison snapshot | one complete current `mechanical-findings.json` snapshot from the supported local rule set; history never keeps an absent finding open |
| `publish_document_visual_contract` | accepted proposed Document Visual Contract plus output path | validate the v1 renderer-neutral contract and write the actual accepted JSON artifact; never synthesize visual values or renderer code |
| `decide` | current observation, mechanical snapshot, score history, budget/pivot state and selection mode | ordered lane decision recorded through `append_event`; visual judgement remains Evaluator evidence |
| `finish_select` | eligible immutable evaluated iterations/artifacts and current mechanical evidence | final selection plus copied/identified accepted candidate and fresh required rendered evidence |
| `finish_correction_decide` | selected evidence plus correction verdict, mechanical snapshot and required rendered evidence | deterministic choice of accepted correction or retained selected candidate |
| `accept` | final candidate declaration, source iteration, rendered evidence, mechanical snapshot and immutability/manifest evidence | acceptance receipt; failure halts without publishing or codifying authority |
| `report` | final evidence, assumptions, decisions, finish and acceptance state | terminal report/run state and final `append_event` record |
| `halt` | exact failed/blocked contract plus durable evidence | preserve completed artifacts, append exact failure, set halted state and publish no winner |
| `append_event` | step/action, status, sequence, iteration, artifact paths and exact message/failure contract | append one new line to `events.jsonl`; earlier events are never edited |

A host may implement operations directly or use shipped helpers, but adapters preserve observable artifacts and failure semantics.

## Capability and failure semantics

Generic required capabilities are `file_io`, `shell` and `isolated_subagents`. If any is absent or cannot be proven, **block before planning**. Record the failed probe when the host can still write evidence. Do not substitute a smaller workflow.

Interactive visual-decision capability is a runnable/reachable target plus browser automation able to attempt the required viewports. Paginated visual-decision capability is a complete ordered rendered artifact/page-image set with verifiable page order, count and physical page sizes; `page_artifact_rendering` is the optional host capability that may produce that evidence.

Use the same evaluation-plan vocabulary for every lane:

- `full`: the lane has rendered evidence required for source-blind visual judgement and may select a winner.
- `build-once-unselected`: creation can produce one build/artifact but cannot make grounded visual judgement; clamp to one build, run available mechanical preflight, preserve evidence and halt without winner.
- `mechanical-review`: Review/Document review may return deterministic evidence with visual status `unverified` when required rendered evidence is unavailable.

A renderer may be HTML-to-PDF, DOCX/PDF, native PDF or another host/downstream implementation. Design Studio does not choose one as visual authority. Record renderer identity/operational settings only for Orchestrator/Builder diagnostics; exclude them from Visual Director/Evaluator input.

An unknown, errored or incomplete probe is not success. Capability handling must never silently return `full`, invent a visual score or claim a lower-evidence path is equivalent.

Failures are durable facts. A deterministic operation produces declared valid evidence or routes through `halt` with exact blocked/failed contract. Preserve partial durable evidence for diagnosis/resume.

## Mechanical detector boundary

The seam owns one normalized **current mechanical snapshot contract** and one supported local deterministic rule set. External detector or renderer presence must not change supported checks, severity semantics or outcome.

Hosts provide current source/browser/page-artifact facts through existing capabilities. Missing evidence is an incomplete pass rather than a clean result. The installed mechanical helper validates/normalizes those facts, creates stable finding identities, applies only exact authority-backed waivers and keeps previous findings as comparison history rather than current truth.

The optional `pageArtifacts` input is parallel to browser passes. A completed pass supplies target, positive page count, physical page size `{name,widthMm,heightMm}`, plus explicit failure arrays for printable-area overflow, content clipping, required furniture and print contrast. An incomplete pass supplies target, `completed:false` and exact reason. The helper never launches a renderer or judges pagination aesthetics.

For resume compatibility, legacy detector values remain schema-readable in durable pre-#50 snapshots. The current helper emits only `design-studio`; accepting `impeccable` or `fallback` in an existing artifact does not re-enable those runtime branches.

Mechanical checks report computed facts and severity/waiver evidence. They do not assign visual quality or replace source-blind evaluation.

## Document contract publication

`runtime/document-contract/index.mjs` implements `publish_document_visual_contract`. It accepts only an already accepted proposed visual contract, validates the required renderer-neutral v1 shape, creates output parent directories and writes JSON. It does not infer design values, read business source truth or select a renderer. Validation failure returns explicit error and must block downstream publication.

## Review lane

Interactive Review uses the same capability/evidence semantics without the Studio iteration graph. Host adapters run deterministic root/capability/mechanical operations needed by `references/review/polish.md` and use `mechanical-review` when visual verification is unavailable.

## Document lane

`references/document/document.md` composes the same stable operations for page artifacts. It does not fork a renderer-specific runtime or copy the browser workflow. Page-specific direction/evaluation remains source-blind; deterministic `page-artifact` facts join the same mechanical snapshot; accepted page-system output is published as renderer-neutral `document-visual-contract.json`.

## Adapter contract

A host adapter may translate input from `invocation.md`; provide isolated-agent/file/shell/browser/page-rendering capabilities; invoke stable operations in lane order; and translate final results back to the host.

An adapter may not own workflow decisions, artifact schemas, design methods, capability downgrade policy or acceptance rules. Claude compatibility commands remain adapters over this contract, not alternative runtimes.

## Research boundary

blind comparison, lane matrix generation, fixture validation, model probing, preference transactions and other historical Milestone 0 research behavior are excluded from the runtime seam.

Repository research tooling may call a genuinely shared helper later, but a supported installed run must not import or shell into benchmark/research tooling merely because similar machinery exists there. The shipped-runtime/research separation from #49 remains authoritative.
