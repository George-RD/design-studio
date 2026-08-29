# Mechanical quality gate

This gate owns deterministic source and browser-computed facts. It runs before blind visual evaluation and again after finish corrections.

It does not choose a direction, award Design Quality or Originality, or replace browser critique.

## One supported local gate

Supported runs use the installed Design Studio mechanical runtime. From the installed skill root:

```text
node runtime/mechanical/index.mjs <input-json> <mechanical-findings-json>
```

The helper is Node-standard-library only and ships with the Agent Skill. External detector availability must not change the supported rule set or result semantics.

The host still owns source access, serving and browser automation. Gather facts from the actual current target, then give those facts to the helper. Do not infer a clean result from missing evidence.

## Evidence input

The input uses `schemaVersion: 1` and contains one source pass plus zero or more browser passes.

A completed source pass provides:

- `pageTitle` and `language`;
- `headingOrderValid` and `primaryHeadingCount`;
- `motionPresent` and `reducedMotionHandled`;
- arrays named `semanticControlFailures`, `accessibleNameFailures`, `altTextFailures`, `landmarkFailures`, `focusVisibilityFailures`, `placeholderLinkFailures` and `debugControlFailures`.

A completed browser pass provides:

- `requestedViewport` and the measured `actualViewport`;
- `scrollWidth` and `clientWidth`;
- `motionPresent` and `reducedMotionVerified`;
- arrays named `contrastFailures`, `clippedContentFailures`, `keyboardFailures`, `focusFailures`, `touchTargetFailures`, `resourceFailures` and `fatalConsoleErrors`.

Each explicit failure item contains `location`, `value` and exact human-readable `evidence`. Record only observed failures; an empty array means that check was actually completed and no failure was observed.

When source or browser evidence cannot be collected, set that pass to `completed: false` with an exact `reason`. An incomplete pass is evidence of a limitation, not evidence that the target is clean. Studio still follows the workflow rule that no visual winner can be selected without both required browser viewports. Review returns `visual_status: unverified` when browser evidence is unavailable.

## Local deterministic rules

The runtime turns current facts into primary findings for:

### Source

- missing page title or declared document language;
- invalid heading order or a primary-heading count other than one for the document context;
- semantic-control, accessible-name, alternative-text and landmark failures;
- removed or ineffective focus visibility;
- motion without a reduced-motion source path;
- unresolved placeholder links and debug controls.

### Browser

- requested versus actual viewport mismatch;
- horizontal document overflow;
- measured contrast or meaningful-content clipping failures;
- keyboard reachability or visible-focus failures;
- undersized relevant touch targets;
- resource-load failures or fatal console errors;
- rendered motion that remains materially active under reduced-motion emulation.

Keep task-specific functionality and judgement-heavy categories such as visual hierarchy, generic-template feel, token-system quality and aesthetic anti-patterns in the routed review/evaluation methods. They are not universal deterministic checks merely because they can be expressed as a checklist.

## Current-snapshot rule

Every invocation writes a complete snapshot of the target as it exists now.

- Stable finding identity is derived from rule ID, target, normalised location and relevant value.
- Current findings begin as `open` or `waived`.
- Evidence wording and timestamps do not change finding identity.
- A previous snapshot is comparison evidence only.
- Previous findings absent now are reported as `not-reproduced`; they are not copied into the current open set.
- If the same signature appears again, it is open again unless the current exact waiver still matches.

The normalized output is `mechanical-findings.json`:

```json
{
  "schemaVersion": 1,
  "detector": "design-studio",
  "version": 1,
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
      "signature": "sha256:...",
      "ruleId": "horizontal-overflow",
      "severity": "primary",
      "status": "open",
      "target": "390x844",
      "location": "document",
      "value": { "scrollWidth": 412, "clientWidth": 390 },
      "evidence": "Document scroll width 412px exceeds client width 390px.",
      "authority": null,
      "reason": null
    }
  ],
  "notReproduced": []
}
```

## Waivers

A waiver applies only when `ruleId`, target, location and value exactly match the current finding and the waiver names both an `authority` and a `reason`.

Use a pinned brief, `COPY.md` or `DESIGN.md` rule as authority for an intentional exception. Do not suppress the underlying evidence. If scope or value changes, the old waiver no longer applies.

## Severity and score effects

The installed runtime emits **primary** findings only for the repeatable rules above.

- **Primary**: objective accessibility, overflow, interaction, resource or explicitly prohibited-state failure. Must be fixed or waived. An open primary caps affected Craft and Functionality at 5.
- **Waived**: intentional exception supported by current authority. Preserve the finding plus authority and reason.
- **Not reproduced**: comparison history only. It does not count as a current open finding.
- **Advisory evidence** from a host or research tool may be preserved separately, but it never blocks or changes a score by itself.

Never convert a mechanical finding count into an aesthetic score. A zero-finding page can still be generic, incoherent or wrong for the user.

## Provenance and research boundary

Impeccable remains a pinned research source recorded in `docs/method-sources.json`; it is not required at runtime. The repeatable-check and explicit-finding model informed the local review, but this helper implements Design Studio's own mechanical contract and does not copy or require an upstream CLI, prompt library or source file.

Historical browser/capability probes remain repository research tooling. Reliability work tracked in issue #42 stays on that research surface and must not become a reason to bundle its browser-launch or comparison machinery into the Agent Skill.
