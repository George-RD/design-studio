# Comparison model capability gate

- **Status:** Verified for the Milestone 0 runner spike
- **Verified:** 2026-07-30
- **Scope:** Model access, strict structured output and image understanding only
- **Decision:** The comparison runner may use this repository-scoped execution surface, but no benchmark lane is complete until the full workflow, browser, isolation and evidence contracts pass.

## Why this gate exists

The connected GitHub environment can read and change repository content, but it does not expose a general agent runner or workflow-dispatch tool. GitHub Actions can request GitHub Models access through a job-scoped `GITHUB_TOKEN` with `models: read`, so it is a possible execution surface for reproducible comparison agents.

A catalog entry alone is not enough. The Design Studio comparison needs a model call that can return machine-checkable evidence and a source-blind evaluator that can inspect rendered screenshots. This probe therefore tests the actual API path before any benchmark lane is counted.

Official interfaces used by the probe:

- [GitHub Models quickstart](https://docs.github.com/en/github-models/quickstart)
- [Models catalog REST API](https://docs.github.com/en/rest/models/catalog)
- [Models inference REST API](https://docs.github.com/en/rest/models/inference)

## Acceptance contract

The model harness is available only when one exact pull-request head proves all of the following:

1. A same-repository GitHub Actions job receives a `GITHUB_TOKEN` with job-scoped `models: read` and can list the live model catalog.
2. The selected model advertises text and image input with text output.
3. A text request returns a strict JSON-schema response with the exact expected receipt.
4. A vision request receives a generated red-left/blue-right PNG and returns the correct colors in a strict JSON-schema response.
5. The report records the selected model ID and version, supported modalities, API version, usage metadata when supplied, and the status of every check.
6. Raw catalog and inference responses, the generated image, sanitized request receipts and the final report are uploaded as one workflow artifact.
7. The workflow fails closed on missing permissions, disabled Models access, rate limiting, unsupported structured output, unsupported image content or an incorrect answer.
8. No token or authorization header is written to logs or artifacts.
9. Unit tests cover selection, payloads, response parsing, exact answers, blocker classification, evidence preservation and partial failure.

A passing catalog check with a failing text or vision check does not satisfy the gate.

## Verified result

GitHub Actions run [`30556498881`](https://github.com/George-RD/design-studio/actions/runs/30556498881) passed on head `ec23c5aaa824d867584566fb18554347170eca53`.

- The live catalog exposed 37 models.
- The probe selected `openai/gpt-4.1`, model version `2025-04-14`.
- The catalog reported text and image input with text output.
- Strict structured text returned `{"probe":"github-models","status":"ok"}`.
- Vision returned `{"leftColor":"red","rightColor":"blue"}` for the generated split-color PNG.
- The two inference calls used 98 and 173 total tokens respectively.
- The uploaded artifact digest was `sha256:12279c772ffdd738d328fd322b8a7f24705f0e2bad939bf0c5b337122c7b9c4a`.

The permanent sanitized receipt is [`evidence/github-models-capability.json`](evidence/github-models-capability.json). The raw artifact expires after its configured retention period; the receipt preserves the model, run, digest, result and scope without storing credentials.

This proves the minimum model API path only. It does not yet prove browser automation, screenshot capture, file-editing tools, source isolation, a complete Design Studio or Impeccable lane, or blind comparative preference.

## Failure semantics

The probe distinguishes:

- **blocked:** authentication, repository access, disabled capability, request timeout or rate limiting prevents a valid test;
- **failed:** the API is reachable but the selected path violates the required response, schema or visual-understanding contract.

Both states fail CI and preserve a sanitized `capability-report.json`. Neither state permits a comparison lane checkbox to be completed.

## Cost and security boundary

The live probe makes one catalog request and at most two small inference requests. It runs only for a branch inside this repository or by explicit manual dispatch. Pull requests from forks can run unit contracts but cannot execute the model job.

The workflow grants no write permission. It receives only `contents: read` and `models: read`, does not use a shell-expanded request containing the token, and uploads only files produced by the probe.

## Evidence location

- Contract: [`test/test_github_models_capability.py`](../../test/test_github_models_capability.py)
- Probe: [`scripts/probe_github_models.py`](../../scripts/probe_github_models.py)
- CI: [`.github/workflows/model-capability.yml`](../../.github/workflows/model-capability.yml)
- Permanent receipt: [`evidence/github-models-capability.json`](evidence/github-models-capability.json)
- Raw result: `github-models-capability-30556498881` workflow artifact

The next work is a real lane wrapper that provides browser capture, controlled file tools, role isolation and the existing run-harness receipts. The twelve comparison lanes remain unfinished.
