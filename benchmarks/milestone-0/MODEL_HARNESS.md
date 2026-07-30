# Comparison model capability gate

- **Status:** Pending live GitHub Actions evidence
- **Scope:** Milestone 0 comparison execution only
- **Decision:** Do not start the twelve comparison runs until an isolated model harness proves the minimum text and visual-evaluation capabilities below.

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
- Live result: `github-models-capability-<run-id>` workflow artifact

This document remains **Pending** until the live workflow passes on the exact PR head. A later evidence commit may record the selected model and workflow result, but must not mark any of the twelve benchmark lanes complete.
