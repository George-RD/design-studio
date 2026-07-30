# Comparison agent capability gate

- **Status:** Candidate; the exact pull-request head must pass the live workflow before this gate is accepted.
- **Scope:** Controlled file tools, browser interaction, screenshot capture and source-blind role isolation.
- **Decision boundary:** This gate makes the twelve Milestone 0 comparison runs executable. It does not count as a benchmark lane or comparative result.

## Why this gate exists

The model capability probe proves strict structured text and image understanding, but it deliberately does not prove the parts that can invalidate a design comparison: constrained file editing, live interaction, source isolation or durable execution evidence.

The comparison runner therefore needs one additional capability gate before any lane can be counted. The gate uses the same repository-scoped GitHub Models surface, but runs three separate roles around an isolated workspace:

1. a source-blind Visual Director receives only a public brief and returns a strict design contract;
2. a Builder receives the brief, direction and constrained file tools, reads a source canary and writes only to an output root;
3. Chromium submits the generated form at `390x844`, verifies the success state, overflow and reduced-motion behavior, then captures a screenshot;
4. a fresh source-blind Evaluator receives only the public brief and screenshot and returns a strict visual receipt.

The live API calls follow GitHub's documented [models catalog](https://docs.github.com/en/rest/models/catalog) and [models inference](https://docs.github.com/en/rest/models/inference) interfaces rather than an undocumented compatibility endpoint.

## Acceptance contract

The gate is accepted only when one exact pull-request head proves all of the following:

1. The selected catalog model advertises text and image input, text output and `tool-calling`.
2. The Director request contains no source canary and returns the exact structured direction schema.
3. Builder tools can list and read only UTF-8 files under the work root and write only approved text files under the output root.
4. Absolute paths, traversal, backslashes, unsupported types, symlinks, excessive file sizes, excessive file counts and excessive total output are rejected before mutation.
5. The Builder reads `baseline.css`, writes a self-contained `index.html`, makes no external request and does not copy the source canary into the output.
6. Tool calls and matching tool responses follow the chat-completions continuation protocol, with every request, response and tool result preserved as evidence.
7. A dependency-free Chromium probe runs the output at `390x844`, enters and preserves a form value, prevents navigation, reveals exact success text, detects horizontal overflow, emulates reduced motion and captures a PNG.
8. The Evaluator request contains no source canary or source code, includes the captured PNG and returns the exact structured visual schema.
9. The report distinguishes `blocked` infrastructure from `failed` contract behavior, preserves partial evidence and never writes the token or authorization header.
10. Unit tests cover model selection, workspace boundaries, path and symlink attacks, required tool use, missing writes, output leakage, source isolation, evidence preservation, token redaction and both passing and failing browser behavior.

A model call, tool write or screenshot by itself does not satisfy the gate. Every check must pass in one run.

## Failure semantics

- **blocked:** authentication, Models access, rate limiting, request timeout or missing Chromium prevents a valid test;
- **failed:** the execution surface is reachable but a response, tool action, output, browser interaction or isolation receipt violates the contract.

Both states fail CI and upload the partial evidence tree. Neither state permits a comparison-lane checkbox to be completed.

## Cost and security boundary

The live run makes one catalog request, one Director inference, a bounded Builder loop of at most six turns and one Evaluator inference. The workflow grants only `contents: read` and `models: read`. File tools expose no shell command, network request or repository write permission.

The browser loads the generated self-contained HTML directly into an isolated headless document. This avoids depending on a package install or a network-accessible server while still exercising real DOM behavior and screenshot capture.

## Evidence location

- Contract tests: [`test/test_boundary_agent_capability.py`](../../test/test_boundary_agent_capability.py)
- Controlled agent runner: [`scripts/run_boundary_agent_capability.py`](../../scripts/run_boundary_agent_capability.py)
- Constrained file tools: [`scripts/boundary_agent_tools.py`](../../scripts/boundary_agent_tools.py)
- Builder and output contracts: [`scripts/boundary_agent_builder.py`](../../scripts/boundary_agent_builder.py)
- Chromium probe: [`scripts/run_browser_capability.mjs`](../../scripts/run_browser_capability.mjs)
- CI: [`.github/workflows/boundary-agent-capability.yml`](../../.github/workflows/boundary-agent-capability.yml)
- Raw result: `boundary-agent-capability-<run-id>` workflow artifact

After the live gate passes, preserve a sanitized receipt under `evidence/`, update this status with the exact head, run and artifact digest, and then use the runner to execute the fixed comparison lanes. The twelve lanes remain unfinished until their existing run-harness receipts validate.
