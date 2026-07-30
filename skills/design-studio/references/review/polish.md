# Review lane: audit and polish

Review improves an existing surface without inventing a replacement visual world. It is independent of the Studio create loop.

## Inputs

- `target`: local path, URL or existing `serve.json`;
- `constraints`: optional scope or focus;
- `report_only`: write evidence without editing;
- `mechanical_only`: run deterministic checks and stop with visual status `unverified`.

Resolve roots and capabilities with `../runtime-integrity.md`. Load `PRODUCT.md`, optional `COPY.md`, `DESIGN.md` and any relevant surface brief. Incumbent design is authority in Review. Do not use the audit as an excuse to rebrand, restructure the product or replace factual copy.

## 1. Resolve and classify

Write review-local root and capability evidence under `harness-output/review/`. Resolve one runnable target and its primary user goal. Classify once:

- `static`: content or marketing surface whose meaningful interactions are navigation and links;
- `interactive`: forms, application controls, stateful navigation, data views, editors, dialogs or multi-step flows.

Record actual scope and excluded areas. When the browser or runnable target is missing, continue only as mechanical review.

## 2. Mechanical gate

Run `../quality-gates.md` before visual lenses.

- Prefer Impeccable source, desktop URL and mobile URL JSON scans.
- Otherwise run fallback source and browser-computed checks.
- Treat every rerun as a complete current snapshot with stable finding signatures.
- Preserve open, advisory, waived, resolved and not-reproduced states separately.
- Exact contrast, token, DOM, viewport, overflow and target-size claims come from this gate, not screenshot-only agents.

When `mechanical_only` is true, write the report with `visual_status: unverified` and verdict `unverified`.

## 3. Browser evidence

When a browser is available:

1. verify 1440×900 and 390×844 with measured `window.innerWidth`;
2. capture full-page and first-viewport screenshots at both widths;
3. read console and failed resources;
4. inventory meaningful controls and states;
5. test primary paths, keyboard focus and relevant edge cases;
6. capture extra state or zone screenshots only where they support a finding.

When no browser is available, or either viewport remains unreachable, retain mechanical and partial browser evidence but return `unverified`. Do not run visual lenses or infer readiness from source or one viewport.

## 4. Conditional lenses

Fan out lenses with screenshots, interaction evidence, surface goal, class, constraints and current mechanical summary. Lens agents report only; they do not edit.

- Always: `slop.md`, `hierarchy.md`, `a11y.md`.
- Interactive or state-focused request: also `interaction.md`.
- Static surfaces receive a reduced interaction inventory, not an accessibility exemption.

Every finding uses:

```json
{
  "id": "hier-001",
  "lens": "hierarchy",
  "severity": "blocker",
  "confidence": "high",
  "summary": "The primary action disappears below competing process labels",
  "evidence": "screenshots/desktop-1440.png, first viewport",
  "status": "open"
}
```

## 5. Aggregate

Deduplicate by user-visible defect, retain all supporting evidence and use the highest severity.

- **Blocker**: broken primary task or action, inaccessible interaction, serious comprehension failure or open primary mechanical finding.
- **Quality**: visible generated-template feel, weak hierarchy or rhythm, missing important states or material craft gap.
- **Polish**: local refinement that does not change direction, product or information architecture.

A detector pattern supported by the current brief or `DESIGN.md` can be waived when authority and reason are recorded. Common patterns receive no automatic quality credit because they are intentional.

## 6. Act once

When `report_only` is false:

1. fix Blockers that can be resolved without changing product or direction;
2. fix Quality findings in one grouped batch;
3. take cheap, local Polish fixes only when consistent with `DESIGN.md`;
4. flag judgement calls instead of inventing a new direction;
5. rerun a complete current mechanical snapshot and recapture the same viewports once;
6. mark each original finding fixed, partial, open or waived.

Do not start a per-tweak screenshot loop. Do not create design directions, originality scores or design-system artifacts.

## 7. Output and verdict

Write:

```text
harness-output/review/
  roots.json
  capabilities.json
  report.md
  findings.json
  mechanical-findings.json
  screenshots/
  confirmation/
```

Verdicts:

- `ready`: browser-grounded; no open Blocker or Quality finding; primary mechanical findings cleared or waived.
- `ready_with_nits`: browser-grounded; only Polish findings remain.
- `hold`: an open Blocker or material Quality issue remains.
- `unverified`: browser unavailable, either viewport unreachable or `mechanical_only`.

Report surface class, lenses, actual viewports, fixes, waivers, open items, limitations and `visual_status`.

## Stop condition

Review ends with the report. It does not emit REFINE, PIVOT or SHIP, execute `workflow.yaml` or call Visual Director.
