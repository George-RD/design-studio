# Historical GitHub Models capability probe

- **Status:** Historical evidence; the execution surface is retired
- **Originally verified:** 2026-07-30
- **Retired by GitHub:** 2026-07-30
- **Current replacement:** [Copilot CLI comparison agent gate](AGENT_HARNESS.md)

## What this probe established

Before GitHub retired GitHub Models, run [`30556498881`](https://github.com/George-RD/design-studio/actions/runs/30556498881) proved that a same-repository Actions job could use a job-scoped `models: read` token for:

- live catalog access;
- strict JSON-schema text output;
- image input and structured visual evidence;
- sanitized request, response, usage and artifact receipts.

The probe selected `openai/gpt-4.1`, model version `2025-04-14`, and correctly read a generated red-left/blue-right PNG. Its permanent receipt remains at [`evidence/github-models-capability.json`](evidence/github-models-capability.json).

## Why it is no longer an execution dependency

GitHub [fully retired GitHub Models on July 30, 2026](https://github.blog/changelog/2026-07-01-github-models-is-being-fully-retired-on-july-30-2026/). Catalog and inference requests are therefore no longer a viable comparison surface. The historical receipt is retained because it records an actual passed experiment and explains the architecture path, but new runs must not call the retired endpoints.

The replacement [Copilot CLI agent gate](AGENT_HARNESS.md) proves the broader contract that the comparison actually needs: isolated Director, Builder and Evaluator sessions, bounded file tools, browser interaction, screenshot capture, source-canary separation and durable evidence.

## Historical evidence location

- Probe contract: [`test/test_github_models_capability.py`](../../test/test_github_models_capability.py)
- Probe implementation: [`scripts/probe_github_models.py`](../../scripts/probe_github_models.py)
- Historical-evidence validator: [`.github/workflows/model-capability.yml`](../../.github/workflows/model-capability.yml)
- Permanent receipt: [`evidence/github-models-capability.json`](evidence/github-models-capability.json)

The old probe does not complete a benchmark lane and is not used by the current comparison runner.
