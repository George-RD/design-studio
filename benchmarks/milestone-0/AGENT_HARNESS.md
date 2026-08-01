# Comparison agent capability gate

- **Status:** Verified
- **Verified:** 2026-07-31
- **Execution surface:** GitHub Copilot CLI in GitHub Actions
- **Scope:** Controlled file tools, browser interaction, screenshot capture and source-blind role isolation
- **Decision boundary:** This gate makes the twelve Milestone 0 comparison runs executable. It does not count as a benchmark lane or comparative result.

## Why this gate exists

A fair Design Studio comparison needs more than model access. The execution surface must preserve source isolation, constrain file mutation, exercise the rendered page, retain failures and provide evidence that can be validated after the run.

GitHub Models was the original candidate, but GitHub [fully retired the service on July 30, 2026](https://github.blog/changelog/2026-07-01-github-models-is-being-fully-retired-on-july-30-2026/). The accepted gate therefore uses a pinned GitHub Copilot CLI instead.

The workflow runs three separate Copilot sessions around one isolated browser handoff:

1. a source-blind Visual Director receives only the public brief and creates `direction.json`;
2. a Builder receives the brief, direction and a canary-bearing baseline, then creates one self-contained `index.html`;
3. Chromium submits the generated form at `390x844`, verifies behavior and captures a screenshot;
4. a fresh source-blind Evaluator receives only the public brief and screenshot and creates `evaluation.json`.

## Acceptance contract

One exact workflow run must prove all of the following:

1. The pinned Copilot CLI installs and authenticates with a job-scoped token carrying `copilot-requests: write`.
2. Director, Builder and Evaluator use fresh `COPILOT_HOME` directories that trust only their own role workspace.
3. Director and Evaluator expose only the `create` tool. Builder exposes `view`, `create`, `edit` and `apply_patch`. Shell, URL, memory, custom instructions, built-in MCPs, remote execution and user questions remain disabled.
4. Director and Evaluator never receive the source canary or source files. Builder must read the canary-bearing baseline, but the accepted output must not contain the canary.
5. Every role preserves its exact command, JSONL output, stderr, resolved model and produced files.
6. With `--model=auto`, each role must preserve one concrete resolved model; different roles may resolve to different models. With an explicit model, every role must match it. A missing, ambiguous or inconsistent role receipt fails closed.
7. The Builder produces exactly one runnable HTML entrypoint with the required form, input and success-state IDs.
8. Chromium confirms that the success state starts empty and hidden and becomes visible after submission, the entered value survives, the form remains visible, the document URL does not change, there is no horizontal overflow, keyboard focus has a distinct visual state, reduced motion suppresses active motion and no external request occurs.
9. The Evaluator confirms that the title, form, success state and usable mobile layout are visible and that the source canary is absent.
10. Authentication, policy, unavailable-model, rate-limit and missing-browser conditions are distinguished from reachable-but-invalid contract failures. Both preserve partial evidence and fail CI.

A model response, file write or screenshot alone does not satisfy the gate. Every check must pass in one run.

## Verified result

GitHub Actions run [`30643540826`](https://github.com/George-RD/design-studio/actions/runs/30643540826) passed on head `6f21c4ec32ab34a2974db607a3197d5e586a86a7`.

- Copilot CLI version: `1.0.74`
- Requested model: `auto`
- Model policy: auto-selection is recorded independently for each role
- Director resolved model: `claude-haiku-4.5`
- Builder resolved model: `gpt-5-mini`
- Evaluator resolved model: `gpt-5-mini`
- Director tools: `create`
- Builder tools: `view`, `create`, `edit`, `apply_patch`
- Evaluator tools: `create`
- Verified viewport: `390x844`
- Submitted value: `Ada`
- Success transition: empty and hidden before submission, visible afterward with exact text `Capability complete`
- Form controls: visible before and after submission
- Keyboard focus: distinct focused styles for the input and submit control
- URL: unchanged at `about:blank`
- Width: `390` CSS pixels for the viewport, document and client
- Motion: `1000 ms` maximum normally and `0 ms` with reduced motion
- External requests: none
- Source-isolation checks: all passed
- Artifact: `copilot-cli-agent-capability-30643540826`
- Artifact digest: `sha256:685e259ce6478dadd6078297a16ccace7379d4aa9d43167b169ad2be0003af04`

The permanent sanitized receipt is [`evidence/copilot-cli-agent-capability.json`](evidence/copilot-cli-agent-capability.json). It preserves the exact run, head, artifact digest, execution surface and normalized checks after the raw artifact expires.

## Failure and cost boundary

Each role has a maximum of 30 AI credits. The workflow grants repository content read access and Copilot request access only; it has no repository write permission. The Copilot subprocess receives an explicit environment allowlist. The browser loads the self-contained output directly and observes Chrome DevTools Protocol network events rather than trusting a source scan.

- **blocked:** authentication, account policy, unavailable model, service availability, rate limit, credit exhaustion or missing Chromium prevents a valid test;
- **failed:** the CLI or browser is reachable, but output, tool use, isolation, interaction or evidence violates the contract.

Neither state permits a comparison-lane checkbox to be completed.

## Evidence location

- Executable capability gate: [`scripts/run_copilot_cli_agent_capability_gate.py`](../../scripts/run_copilot_cli_agent_capability_gate.py)
- Shared capability implementation: [`scripts/run_copilot_cli_agent_capability.py`](../../scripts/run_copilot_cli_agent_capability.py)
- Chromium probe: [`scripts/run_browser_capability.mjs`](../../scripts/run_browser_capability.mjs)
- Completion-state probe: [`scripts/run_browser_capability_completion.mjs`](../../scripts/run_browser_capability_completion.mjs)
- Role and permission contracts: [`test/test_copilot_cli_agent_capability.py`](../../test/test_copilot_cli_agent_capability.py)
- Auto-model receipt contract: [`test/test_copilot_cli_auto_model.py`](../../test/test_copilot_cli_auto_model.py)
- Model-policy contract: [`test/test_copilot_cli_model_compatibility.py`](../../test/test_copilot_cli_model_compatibility.py)
- Trusted-workspace contract: [`test/test_copilot_cli_trusted_workspace.py`](../../test/test_copilot_cli_trusted_workspace.py)
- Director retry contract: [`test/test_copilot_cli_director_retry.py`](../../test/test_copilot_cli_director_retry.py)
- Permanent-receipt contract: [`test/test_copilot_cli_agent_receipt.py`](../../test/test_copilot_cli_agent_receipt.py)
- Browser regressions: [`test/test_browser_capability_regressions.py`](../../test/test_browser_capability_regressions.py)
- Completion regressions: [`test/test_browser_completion_contract.py`](../../test/test_browser_completion_contract.py)
- CI: [`.github/workflows/boundary-agent-capability.yml`](../../.github/workflows/boundary-agent-capability.yml)
- Permanent receipt: [`evidence/copilot-cli-agent-capability.json`](evidence/copilot-cli-agent-capability.json)

The next roadmap work is to execute the same four frozen fixtures through all three lanes and complete the existing run-harness evidence. The twelve comparison runs remain unfinished.
