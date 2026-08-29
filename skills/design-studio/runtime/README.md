# Installed runtime helpers

This directory contains deterministic helpers that ship with the Design Studio Agent Skill. `../runtime-contract.md` remains the stable interface; these files are internal implementations behind that seam.

## Runtime policy

- Node.js 20+ and the Node standard library only. No install-time package dependency is required.
- Helpers use Node path, file and process APIs rather than shell-specific command syntax so the same contract works on Linux, macOS and Windows.
- The host supplies capabilities such as file access, shell execution and browser automation. A helper may validate or normalize facts from those capabilities; it does not own a second host or workflow policy.
- Repository-only research and capability tooling stays outside the installed runtime. It is not copied here merely because it contains similar historical behavior.

## Mechanical preflight

`mechanical/index.mjs` is the installed implementation used by the `mechanical_preflight` operation. It accepts current source/browser evidence, evaluates the supported local deterministic rules, applies exact authority-backed waivers and writes one normalized current snapshot.

Run it from the installed skill root:

```text
node runtime/mechanical/index.mjs input.json mechanical-findings.json
```

With no paths, it reads JSON from standard input and writes JSON to standard output. Exit `0` means a valid snapshot was produced, exit `2` means the supplied evidence/JSON did not satisfy the input contract, and exit `1` is reserved for an unexpected runtime error.

### Evidence boundary

The helper deliberately does not launch Chrome, install a detector, discover an application or infer visual quality. The host gathers facts from the actual current source and browser target. Missing source or browser access is recorded as an incomplete pass with an exact reason; it is never converted into a clean pass. Visual judgement remains with the source-blind Evaluator.

For a completed source pass provide:

- page title and declared language;
- whether heading order is valid and the primary-heading count;
- whether motion exists and has a reduced-motion path;
- explicit failure evidence for semantic controls, accessible names, alternative text, landmarks, focus visibility, placeholder links and debug controls.

For each completed browser pass provide:

- requested and actual viewport dimensions;
- document scroll/client widths;
- primary-action usability and reduced-motion verification;
- explicit failure evidence for contrast, clipping, keyboard reachability, focus, touch target size, resource loading and fatal console errors.

Each explicit failure item carries `location`, `value` and human-readable `evidence`. Stable finding identity is derived from rule ID, target, normalized location and relevant value. Evidence wording and timestamps do not alter the signature.

A waiver must exactly match that identity and must name both `authority` and `reason`. A previous snapshot is comparison evidence only: findings absent from the current target are reported under `notReproduced` and are not carried into the current open set.

## Migration boundary

Issue #50 does not turn historical browser/capability harnesses into product runtime. Those entrypoints remain repository research support and keep their existing behavior. Issue #42 therefore remains a separate reliability question for that research gate rather than a dependency of the installed skill.

The supported runtime had no prior executable helper entrypoint to preserve, so no compatibility wrapper is required for this first extraction. Future helpers should be added only when a supported runtime operation needs deterministic behavior that is cheaper and clearer to own here than in every host adapter.
