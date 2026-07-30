# Runtime integrity

This reference owns target roots, capability evidence, resumable step state, unattended direction assignment and final acceptance. These are operational facts, not visual judgement.

## 1. Resolve three roots

Write `roots.json` before planning.

- **repoRoot**: the version-control or explicit repository boundary.
- **appRoot**: the local application that owns the requested route and runnable command.
- **contextRoot**: the nearest shared product context that governs the app.

Use evidence in this order:

1. explicit path, URL or user override;
2. existing `serve.json` whose command and working directory validate;
3. framework and dev-server configuration tied to the target;
4. route, entry point and asset evidence;
5. package or workspace metadata as supporting evidence.

Do not choose a root only because a directory has a familiar monorepo name or because a package manager lists it. A nested app may own its own runtime while inheriting product context from a parent.

For local targets, verify `appRoot` is inside `repoRoot`. For an external URL, set `targetKind: external-url` and record that no local source root was proven.

## 2. Probe capabilities once

Write `capabilities.json` before planning and repeat the probe only when the runtime changes.

Probe:

- file I/O and shell;
- isolated subagents;
- a runnable local target or reachable URL;
- browser automation and the ability to attempt both required viewports;
- Impeccable availability, version and exact invocation;
- structured user questions;
- image generation;
- Growth Arsenal `business-copy-style` availability;
- version control when the caller asked for repository changes.

Each entry needs evidence. Do not report `available` because a tool name appears in a prompt. Call or inspect it.

### Evaluation plans

- `full`: runnable target and browser are available. The workflow may evaluate and select.
- `build-once-unselected`: Studio can build but cannot produce browser-grounded visual judgement. Clamp the build budget to one, run mechanical checks and halt without a winner.
- `mechanical-review`: Review was explicitly requested without visual readiness.

Missing file I/O, shell or isolated subagents blocks Studio before planning.

## 3. Append-only event journal

`events.jsonl` is the recovery source. `run.json` is a convenient current view, not the only record.

Before a step:

```json
{"sequence":12,"at":"...","step":"build","status":"started","iteration":2,"artifactPaths":["iterations/2/site","iterations/2/serve.json"],"message":"Building iteration 2"}
```

After output validation, append `completed`. On failure, append `failed` or `blocked` with the exact missing contract and whether retry is safe.

Never edit an earlier event. A later event may supersede it.

## 4. Resume rules

A resumed run validates dependencies in order:

1. prompt hash and explicit run ID;
2. root and capability manifests;
3. step event sequence;
4. schemas and files named by completed events;
5. immutability of completed iteration trees;
6. the first step without a valid completion receipt.

Continue from that first incomplete step. Preserve later files as untrusted evidence until the missing dependency completes.

A completed build is never rerun inside the same iteration. When its artifact is corrupt, create a new iteration or mark the run invalid; do not overwrite the old tree.

## 5. Commit unattended selection before generation

The model producing candidates must not know which candidate will be selected.

Before `directions.md` exists:

1. fix candidate IDs as `direction-1`, `direction-2`, `direction-3`;
2. derive a stable seed from run ID, prompt hash and iteration;
3. map it to `assignedIndex` 1–3;
4. write `direction-assignment.json`;
5. exclude seed and index from Visual Director context.

Visual Director then writes three equally specified candidates. Orchestrator selects the candidate at the committed index.

Interactive runs record `user-choice` with no seed or index. An exact pinned direction records one candidate and index 1.

## 6. Final acceptance receipt

`finish/acceptance.json` proves which tree became authoritative.

Before codifying, verify:

- `final-tree.json` names the same selected tree;
- the tree came from the recorded source iteration;
- its rewritten serve contract starts from the accepted tree;
- required viewports match actual measured widths when the result claims visual verification;
- the named current mechanical snapshot has no unacknowledged primary finding;
- open finish items match `finalStatus`;
- a deterministic tree manifest was recorded;
- source iterations remain unchanged.

Directory existence is not acceptance. When a postcondition fails, halt and preserve the evidence instead of publishing or codifying the tree.
