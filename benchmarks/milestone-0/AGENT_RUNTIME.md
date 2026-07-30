# Milestone 0 comparison agent runtime

- **Status:** Pending live generation smoke
- **Scope:** Generation and role isolation only
- **Does not complete:** any comparison lane, functional check, browser evaluation or output preference

## Purpose

The frozen briefs and run receipts do not by themselves ensure that each comparison lane sees the right information. The generation runtime enforces the minimum role boundary needed before browser evidence can be trusted:

- Impeccable alone receives the frozen brief, acceptance contract, baseline source and a pinned fixture-specific subset of upstream Impeccable guidance.
- The Design Studio Visual Director receives the frozen brief and acceptance contract, but never source files, builder reasoning, another lane's output or Impeccable guidance.
- A deterministic selector assigns one of exactly three materially distinct directions. The director does not rank or choose its own work.
- The Design Studio Builder receives only the assigned direction, frozen task inputs, baseline source and the current builder contract.
- The `design-studio-impeccable` builder is not given upstream Impeccable design guidance. Its difference from `design-studio-current` is the later mechanical provider, matching the current v1.5 boundary.

The source-blind evaluator is intentionally not executed in this slice. It requires rendered screenshots, interaction evidence and mechanical findings, which are the next implementation gate.

## Accepted upstream guidance

The Impeccable-only lane reads `skill/SKILL.src.md` plus the smallest fixture-specific references from an external checkout. It records the package version, exact revision, path, byte count and SHA-256 digest of every guidance file.

| Fixture kind | Additional pinned references |
|---|---|
| `new-marketing-surface` | `new-work.md`, `craft-floor.md` |
| `existing-product-overhaul` | `new-work.md`, `operate.md`, `craft-floor.md` |
| `review-and-polish` | `polish.md`, `audit.md`, `craft-floor.md` |
| `new-visually-ambitious-experience` | `new-work.md`, `overdrive.md`, `animate.md`, `craft-floor.md` |

Design Studio does not copy these files into its repository. The live smoke checks out the exact upstream revision separately.

## Output contract

Every builder returns one strict JSON file bundle. The runtime validates the whole bundle before writing a byte:

- `index.html` is required;
- paths must be relative POSIX paths without traversal, hidden segments or unsupported extensions;
- duplicate paths are rejected;
- only text files are accepted;
- the bundle is limited to 24 files and 750,000 UTF-8 bytes;
- external network URLs are rejected because all frozen fixtures require local execution;
- the prepared output directory must be empty;
- validated files are written to a temporary sibling and atomically moved into place;
- every output file receives a SHA-256 receipt.

The model request and raw response are preserved without the GitHub token. Model usage is copied into the generation report when the endpoint supplies it.

## Live smoke acceptance

The exact pull-request head must prove both of these non-counting runs:

1. **Impeccable alone**
   - uses the pinned upstream checkout;
   - performs one isolated builder call;
   - writes a valid local file bundle;
   - records upstream source provenance.
2. **Design Studio current**
   - performs separate director and builder calls;
   - director request contains no baseline source;
   - builder request contains the selected direction and baseline source only where a baseline exists;
   - writes a valid local file bundle;
   - records the deterministic selection receipt.

Both runs must pass through `run_boundary_benchmark.py prepare` and `execute`, finish in `awaiting-evidence`, and validate without being marked complete. Their artifacts are smoke evidence only and must not be reused as a final lane result.

## Evidence

- Contract tests: [`test/test_boundary_benchmark_agent.py`](../../test/test_boundary_benchmark_agent.py)
- Runtime: [`scripts/comparison_agent.py`](../../scripts/comparison_agent.py)
- Live smoke: [`.github/workflows/comparison-agent-smoke.yml`](../../.github/workflows/comparison-agent-smoke.yml)

The next gate adds browser serving and capture, deterministic interaction checks, the appropriate mechanical provider, and a fresh source-blind evaluator. Until that gate is complete, all three lane checkboxes in `ROADMAP.md` remain open.
