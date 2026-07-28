# Deterministic preflight

Run deterministic checks after every build and before independent visual evaluation. The preflight catches mechanical defects cheaply; it does not score design quality or replace a browser pass.

## Command

From the target project root:

```bash
node <design-studio-plugin>/scripts/design-studio-check.mjs <surface-path> \
  --mode <persuade|operate|read|experience> \
  --json harness-output/preflight.json
```

Use `--strict` in CI to fail on quality findings as well as blockers. Without `--strict`, the process exits non-zero only for blockers.

Projects may suppress a false positive with a nearby comment containing `design-studio-ignore <rule-id>`, or with `.design-studio/check.json`:

```json
{
  "ignoreRules": ["decorative-gradient-text"],
  "ignoreFiles": ["vendor/**"]
}
```

Suppression is evidence, not deletion: ignored findings remain in the JSON with `status: "ignored"`.

## Required output

`harness-output/preflight.json` contains:

```json
{
  "version": 1,
  "mode": "operate",
  "target": "./src",
  "summary": { "blocker": 0, "quality": 2, "polish": 1, "ignored": 0 },
  "findings": [
    {
      "id": "a11y-outline-removed",
      "severity": "blocker",
      "file": "src/app.css",
      "line": 42,
      "message": "Focus outline is removed without a visible replacement.",
      "evidence": "outline: none",
      "status": "open"
    }
  ]
}
```

## Division of responsibility

### Deterministic preflight can establish

- missing document metadata and image alternatives in static HTML;
- dead placeholder links;
- removed focus indicators;
- motion without a reduced-motion path;
- unsafe transition and interaction shortcuts;
- common mechanical AI-pattern signals;
- package drift between metadata, workflow, commands, and docs.

### Only live evaluation can establish

- actual hierarchy and visual quality;
- rendered contrast across real layered backgrounds;
- clipping, collisions, and responsive composition;
- interaction behavior and state comprehension;
- whether a visual pattern feels generic or earned;
- whether the surface succeeds for a cold user.

Never convert static detector findings into visual claims. Never use a clean preflight as permission to skip browser evaluation.

## Gate behavior

1. Builder runs preflight and fixes all blockers before handoff when possible.
2. Evaluator receives only the preflight summary and finding list, never source code.
3. Open blockers prevent `SHIP`.
4. If budget remains, deterministic blockers route to `REFINE` without spending a full aesthetic evaluation.
5. If blockers remain when the budget is exhausted, decision is `HOLD`, not `SHIP`.
6. A missing browser still permits preflight and a partial report, but visual status is `unevaluated` and decision is `HOLD`.

## Bounded verification

A run gets one batched initial browser pass covering desktop, mobile, relevant states, console, and interactions. After fixes, it gets at most one confirmation pass unless the user explicitly expands the budget. Do not take a new screenshot for each micro-fix.
