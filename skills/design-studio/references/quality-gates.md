# Mechanical quality gate

This gate owns deterministic source and browser-computed facts. It runs before blind visual evaluation and again after finish corrections.

It does not choose a direction, award Design Quality or Originality, or replace a human-style browser critique.

## Preferred path: Impeccable detector

When the `impeccable` CLI is available, run three JSON passes from the project root:

```bash
npx impeccable detect --json <source-path> > <iteration>/mechanical-source.json
npx impeccable detect --json --viewport 1440x900 <served-url> > <iteration>/mechanical-desktop.json
npx impeccable detect --json --viewport 390x844 <served-url> > <iteration>/mechanical-mobile.json
```

Use the installed CLI's help when syntax differs by version; record the version and exact commands. Do not silently fall back after a detector crash—record the failure, then run the fallback gate explicitly.

Normalise all results into `mechanical-findings.json`:

```json
{
  "detector": "impeccable",
  "version": "x.y.z",
  "passes": [
    { "target": "site source", "kind": "source", "completed": true },
    { "target": "1440x900", "kind": "browser", "completed": true },
    { "target": "390x844", "kind": "browser", "completed": true }
  ],
  "primary": [],
  "advisory": [],
  "waivers": []
}
```

Impeccable's project configuration, inline ignores and `DESIGN.md` context are authoritative for intentional exceptions. Keep advisory findings in the output, but never treat them as failures. A primary finding is resolved by a fix or an explicit waiver naming the pinned brief or design-system rule it serves.

## Fallback path

When Impeccable is unavailable, record `detector: fallback` and run a smaller deterministic gate.

### Source checks

- one page title and language declaration;
- sensible heading order and one primary heading per document/screen context;
- semantic controls rather than click handlers on inert elements;
- programmatic labels, alternative text and landmarks;
- no removed focus outline without a replacement;
- reduced-motion handling when motion exists;
- tokenised colours/type/spacing where the project supports tokens;
- no unresolved placeholder links, debug controls or false claims;
- no known decorative defaults used contrary to the selected direction: gradient text, purposeless backdrop blur/glow, nested card shells, emoji standing in for icons, or identical icon-card grids as page structure.

### Browser-computed checks

At verified desktop and mobile viewports:

- `window.innerWidth` equals the requested width;
- document scroll width does not exceed client width unless horizontal scrolling is an explicit task;
- text and component contrast meet the project's required standard;
- text containers do not clip meaningful content;
- interactive targets are keyboard reachable and visibly focused;
- important touch targets are at least 44×44 CSS pixels where relevant;
- critical resources and scripts load without fatal console errors;
- primary action/task is present and usable;
- reduced-motion emulation removes or simplifies non-essential motion.

Fallback coverage is not equivalent to Impeccable. State that limitation in the run report.

## Severity and score effects

- **Primary:** objective accessibility, overflow, interaction, resource or prohibited-pattern failure. Must be fixed or waived. An open primary finding caps affected Craft and Functionality at 5.
- **Advisory:** possible issue requiring context. It never blocks or changes a score by itself.
- **Waived:** intentional exception supported by the current brief or `DESIGN.md`. Record authority and reason; do not delete the evidence.

Never convert a detector count into an aesthetic score. A zero-finding page can still be generic, incoherent or wrong for the user.
