# Review lane: audit and polish

Review improves an existing surface without inventing a replacement visual world. It is independent of the Studio create loop.

## Inputs

- `target`: local path, URL or existing `serve.json`;
- `constraints`: optional scope/focus;
- `report_only`: write evidence without editing;
- `mechanical_only`: run deterministic checks and stop with visual status `unverified`.

Load `PRODUCT.md`, `DESIGN.md` and any relevant surface brief. The incumbent design is authority in Review. Do not use the audit as an excuse to rebrand, restructure the product or replace factual copy.

## 1. Resolve and classify

Resolve one runnable target and capture its primary user goal. Classify once:

- `static`: content/marketing surface whose meaningful interactions are navigation and links;
- `interactive`: forms, application controls, stateful navigation, data views, editors, dialogs or multi-step flows.

Record actual scope and excluded areas.

## 2. Mechanical gate

Run `../quality-gates.md` before visual lenses.

- Prefer Impeccable source, desktop URL and mobile URL JSON scans.
- Otherwise run the fallback source/browser-computed checks.
- Preserve primary, advisory and waived findings separately.
- Exact contrast, token, DOM, viewport, overflow and target-size claims come from this gate—not from screenshot-only agents.

If `mechanical_only` is true, write the report now with `visual_status: unverified` and verdict `unverified`.

## 3. Browser evidence

When a browser is available:

1. verify 1440×900 and 390×844 using measured `window.innerWidth`;
2. capture full-page and first-viewport screenshots at both widths;
3. read console and failed resources;
4. inventory meaningful controls and states;
5. test primary paths, keyboard focus and relevant edge cases;
6. capture additional state/zone screenshots only where they support a finding.

If no browser is available, retain mechanical evidence and return verdict `unverified`. Never infer visual readiness from source.

## 4. Conditional lenses

Fan out visual lenses with screenshots, interaction evidence, surface goal, class, constraints and the mechanical summary. Lens agents report only; they do not edit.

- Always: `slop.md`, `hierarchy.md`, `a11y.md`.
- Interactive or state-focused request: also `interaction.md`.
- Static surfaces receive a reduced a11y interaction inventory, not an exemption from accessibility.

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

Merge all findings. Deduplicate by user-visible defect; retain all supporting evidence and use the highest severity.

- **Blocker:** broken primary task/action, inaccessible interaction, serious comprehension failure or open primary mechanical finding.
- **Quality:** visible generated-template feel, weak hierarchy/rhythm, missing important states or material craft gap.
- **Polish:** local refinement that does not change direction, product or information architecture.

A detector pattern supported by the current brief or `DESIGN.md` can be waived, but the waiver names the authority and reason. Common patterns receive no automatic quality credit simply because they are intentional.

## 6. Act once

When `report_only` is false:

1. fix all Blockers that can be resolved without changing product or direction;
2. fix Quality findings in one grouped batch;
3. take cheap, local Polish fixes only when clearly consistent with `DESIGN.md`;
4. flag judgment calls instead of inventing a new direction;
5. rerun the mechanical gate and recapture the same viewports once;
6. mark each original finding fixed, partial, open or waived.

Do not start a per-tweak screenshot loop. Do not create design directions, originality scores or design-system artifacts.

## 7. Output and verdict

Write:

```text
harness-output/review/
  report.md
  findings.json
  mechanical-findings.json
  screenshots/
  confirmation/
```

Verdict rules:

- `ready`: browser-grounded; no open Blockers or Quality findings; primary mechanical findings cleared or explicitly waived.
- `ready_with_nits`: browser-grounded; only Polish findings remain.
- `hold`: any open Blocker, or a material Quality issue the requested pass could not resolve.
- `unverified`: browser unavailable or `mechanical_only`; mechanical evidence may exist but visual readiness was not established.

The report names the surface class, lenses run, actual viewports, fixes, waivers, open items, limitations and `visual_status`.

## Stop condition

Review ends with the report. It does not emit REFINE, PIVOT or SHIP, does not execute `workflow.yaml`, and does not call the Visual Director.
