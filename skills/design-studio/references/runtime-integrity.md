# Runtime integrity

This reference owns target roots, capability evidence, resumable step state, unattended direction assignment and final acceptance. These are operational facts, not visual judgement. Apply the relevant operations after Design Intent selects a lane; this shared guard does not load a lane procedure or select a lane.

## 1. Resolve three roots

Write `roots.json` before planning.

- **repoRoot**: the version-control or explicit repository boundary.
- **appRoot**: the local application that owns the requested route and runnable command.
- **contextRoot**: the nearest shared product context that governs the app.

Use evidence in this order: explicit path/URL/user override; a validated existing `serve.json`; framework/dev-server configuration tied to the target; route/entry/asset evidence; package/workspace metadata as supporting evidence. Do not select roots from familiar directory names alone. For local targets verify `appRoot` is inside `repoRoot`; external URLs record `targetKind: external-url`.

## 2. Probe capabilities once

Write `capabilities.json` before planning and repeat only when the runtime changes. Probe file I/O/shell and isolated subagents, then the selected lane's visual capabilities. Interactive work probes a runnable local target or reachable URL, browser automation and both required viewports. Document work probes complete ordered rendered pages and physical sizes instead of browser viewports. Probe structured user questions, image generation, and version control when relevant to the requested work. Each entry needs evidence from an actual call or inspection.

`runtime-contract.md` owns the shared `full`, `build-once-unselected` and `mechanical-review` evaluation plans and their failure semantics. Apply them to the selected lane's evidence, never to an unrelated medium's requirements. Missing file I/O, shell or isolated subagents blocks every lane before planning.

## 3. Append-only event journal

`events.jsonl` is the recovery source. `run.json` is a convenient current view, not the only record. Append `started` before work and `completed` only after artifact validation. Failures use `failed` or `blocked` with the exact missing contract and retry safety. Never edit an earlier event; later events may supersede it.

## 4. Resume rules

A resumed run validates, in order: prompt hash/explicit run ID; roots/capabilities; event sequence; schemas/files named by completed events; immutability of completed iteration trees; first step without a valid completion receipt. Continue from that step. Preserve later files as untrusted evidence until the missing dependency completes.

A completed build is never rerun inside the same iteration. Corrupt completed artifacts require a new iteration or invalid run; do not overwrite prior evidence.

## 5. Commit unattended selection before generation

When the selected procedure generates directions, before `directions.md` exists:

1. fix IDs `direction-1`, `direction-2`, `direction-3`;
2. derive a stable seed from run ID, prompt hash and iteration;
3. map it to `assignedIndex` 1–3;
4. write `direction-assignment.json`;
5. exclude seed/index from Visual Director context.

Visual Director then writes equally specified candidates. Orchestrator selects the committed index. Interactive user choice records `user-choice` without seed/index. A fully pinned direction records one candidate/index 1. This invariant does not add direction generation to a Review request.

## 6. Final acceptance receipt

`finish/acceptance.json` proves which tree became authoritative. Before codifying verify: `final-tree.json` names the same selected tree; the tree came from the recorded source iteration; the named current mechanical snapshot has no unacknowledged primary finding; open finish items match `finalStatus`; a deterministic tree manifest exists; source iterations remain unchanged.

For interactive acceptance also verify: the rewritten serve contract starts from it; claimed viewports match measured widths. For Document acceptance verify the complete ordered artifact, page images and physical sizes from that same immutable candidate under the selected Document procedure. These are medium-specific postconditions, not reasons to load another lane.

Directory existence is not acceptance. If a postcondition fails, halt and preserve evidence rather than publishing/codifying the tree.
