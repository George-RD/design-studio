# Mechanical quality gate

This gate owns deterministic source and browser-computed facts. It runs before blind visual evaluation and again after finish corrections.

It does not choose a direction, award Design Quality or Originality, or replace browser critique.

## Preferred path: Impeccable detector

When the `impeccable` CLI is available, run three JSON passes from `roots.appRoot`:

```bash
npx impeccable detect --json <source-path> > <iteration>/mechanical-source.json
npx impeccable detect --json --viewport 1440x900 <served-url> > <iteration>/mechanical-desktop.json
npx impeccable detect --json --viewport 390x844 <served-url> > <iteration>/mechanical-mobile.json
```

Use the installed CLI help when syntax differs by version. Record version, exact commands, roots and exit status. Do not silently fall back after a detector crash. Record the failure, then run fallback explicitly.

## Current-snapshot rule

Every invocation writes a complete snapshot of the target as it exists now.

- Generate a stable signature from rule ID, target, normalised location and relevant value.
- Current findings begin as `open` or `waived`.
- Compare with the previous snapshot only to record `resolved` or `not-reproduced` history.
- Do not union previous open findings into the current open set.
- If a fixed signature appears again, it is open again.
- A waiver applies only when its rule, scope, value and authority still match.

Normalise all results into `mechanical-findings.json`:

```json
{
  "detector": "impeccable",
  "version": "x.y.z",
  "snapshotId": "sha256:...",
  "generatedAt": "...",
  "comparisonSnapshotId": "sha256:...",
  "passes": [
    { "target": "site source", "kind": "source", "completed": true },
    { "target": "1440x900", "kind": "browser", "completed": true },
    { "target": "390x844", "kind": "browser", "completed": true }
  ],
  "findings": [
    {
      "signature": "...",
      "ruleId": "low-contrast",
      "severity": "primary",
      "status": "open",
      "evidence": "...",
      "authority": null,
      "reason": null
    }
  ]
}
```

Impeccable project configuration, inline ignores and `DESIGN.md` context are authoritative for intentional exceptions. Keep advisory evidence, but never treat it as a failure. A primary finding is resolved by a fix or a waiver naming the pinned brief or design-system rule it serves.

Detector rules are fallible. A finding that depends on broad syntax matching must be confirmed against the actual utility, value and element context before it blocks the run.

## Fallback path

When Impeccable is unavailable, record `detector: fallback` and run a smaller deterministic gate.

### Source checks

- one page title and language declaration;
- sensible heading order and one primary heading per document or screen context;
- semantic controls rather than click handlers on inert elements;
- programmatic labels, alternative text and landmarks;
- no removed focus outline without a replacement;
- reduced-motion handling when motion exists;
- tokenised colours, type and spacing where the project supports tokens;
- no unresolved placeholder links, debug controls or false claims;
- no decorative defaults used against the selected direction: gradient text, purposeless blur or glow, nested card shells, emoji used as icons, or identical icon-card grids as page structure.

### Browser-computed checks

At verified desktop and mobile viewports:

- `window.innerWidth` equals the requested width;
- document scroll width does not exceed client width unless horizontal scrolling is explicit;
- text and component contrast meet the required standard;
- text containers do not clip meaningful content;
- interactive targets are keyboard reachable and visibly focused;
- important touch targets are at least 44×44 CSS pixels where relevant;
- critical resources and scripts load without fatal console errors;
- primary action or task is present and usable;
- reduced-motion emulation removes or simplifies non-essential motion.

Fallback coverage is not equivalent to Impeccable. State that limitation in the run report.

## Severity and score effects

- **Primary**: objective accessibility, overflow, interaction, resource or prohibited-pattern failure. Must be fixed or waived. An open primary caps affected Craft and Functionality at 5.
- **Advisory**: possible issue requiring context. It never blocks or changes a score by itself.
- **Waived**: intentional exception supported by the current brief, `COPY.md` or `DESIGN.md`. Record authority and reason; do not delete evidence.
- **Resolved / not-reproduced**: historical comparison only. These statuses do not count as current open findings.

Never convert a detector count into an aesthetic score. A zero-finding page can still be generic, incoherent or wrong for the user.
