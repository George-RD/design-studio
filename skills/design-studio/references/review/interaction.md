# Review: Interaction states lens

Verify every interactive element has a complete state set and every data-driven screen has its full state coverage. Elements without state feedback feel broken. Loaded as a **conditional lens** under `polish.md` when the surface is interactive or the user asked about states/keyboard/a11y.

## When to use

Load this lens when:

- The reviewed surface is **interactive** (forms, buttons with state, modals, menus, tabs, multi-step flows, app UI).
- The user explicitly asked about interaction states, keyboard focus, or feedback.
- `polish.md` classified the surface as `interactive`.

## Not when

- The surface is **static** (marketing/landing/content with no meaningful widgets beyond links) and the user only asked for visual polish — skip this lens unless states were requested.
- The work is a redesign/overhaul — that is the Studio lane, not a Review lens.

> **Other platforms:** For non-web targets (native/SwiftUI), the same inventory applies but replace CSS-state terms with the platform's press/focus-disabled primitives. This leaf is written web-first; adapt the vocabulary, not the checks.

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| `surface` | yes | Path and/or URL and/or running `harness-output/serve.json` from `polish.md` |
| `screenshots` | yes | Desktop 1440 + mobile 390 captures from `polish.md` |
| `surface_class` | yes | `interactive` (this lens is skipped otherwise) |
| `constraints` | no | Explicit scope ("only the checkout form", "skip modals") |

Grounded in live screenshots + real interaction. Never a code-only review (BOC: probe to first available browser adapter; HALT and record if none).

## Phase 1: Inventory

Walk the surface and list every interactive element:

- Buttons and any element with a click/tap handler.
- Links that trigger navigation or actions (not inline text links).
- Text inputs, selects, checkboxes, radios, toggles, sliders, date/color pickers.
- Tappable cards, rows, list items, expandable headers.
- Nav items: tabs, menus, back/forward, toolbar actions, sidebars.
- Custom widgets: modals, sheets, popovers, dropdowns, swipe/context actions, carousels.
- Any element that fires a network or async action.

Record each as a row; you will check it against the state set in Phase 2.

## Phase 2: Per-element states

For each inventoried element, verify the full state set:

1. **Default.** Clearly interactive at rest — fill, border, or affordance distinct from static text. Flag tap-targets that look inert (touch users never hover).
2. **Hover.** Pointer affordance on hover where a pointer exists (color/underline/shadow shift). Flag elements that change nothing on hover yet clearly invite a click.
3. **Active / pressed.** Visible press feedback: darkening, `scale(0.97)`, opacity dip, or a press ripple. Flag fire-and-forget taps on network actions with no press acknowledgement.
4. **Focus-visible.** Keyboard reachable with a clearly visible `:focus-visible` ring. Flag bare `outline: none` with no replacement, or focus that is invisible against the background.
5. **Disabled.** Visually distinct (~0.5–0.6 opacity), non-interactive, AND communicates *why* when gated on a condition ("add an item first") — not just grayed out.
6. **Loading.** In-flight actions show progress **in place** (button spinner, skeleton, progress bar) and prevent double-fire. Flag network taps with no in-flight state.
7. **Completion feedback.** Success or failure is communicated — state change, toast, inline message — not silence.

## Phase 3: Per-screen states

Every data-driven screen needs the full coverage set. For each screen, confirm:

- **Loading.** Skeleton or progress, never a blank flash.
- **Empty.** Guides the next action ("Create your first project"), not "nothing here".
- **Error.** States what failed and what to do next (retry, contact, back).
- **Offline / degraded.** Cached content usable? Clearly marked as stale or offline?
- **Partial.** Some items failed, some succeeded — handled without a full-screen failure.

## Phase 4: Transitions

State changes animate purposefully (150–300ms, confident easing) or happen instantly — never jarring pops where motion was clearly intended, never slow drifts that block input. Respect `prefers-reduced-motion`: replace meaningful motion with an opacity/state fallback.

## Output

Emit one finding per issue. Each finding follows the shared Review schema so it merges into `harness-output/review/findings.json`:

```json
{
  "id": "int-001",
  "lens": "interaction",
  "severity": "blocker | quality | polish",
  "confidence": "high | medium | low",
  "summary": "short statement of the missing or broken state",
  "evidence": "screenshot path + element/screen + observed behavior",
  "status": "open"
}
```

Bucket by severity (mirrors `polish.md` aggregation):

1. **Blockers** — no keyboard focus, `outline: none` with no replacement, broken interaction, missing loading state on a network action (double-fire risk).
2. **Quality** — missing hover/press feedback, disabled-without-reason, empty/error/offline screens absent.
3. **Polish recommendations** — subtler timing/easing, reduced-motion fallbacks, clearer completion feedback.

Do not self-censor "minor" issues; report every gap with its confidence + severity. `polish.md` merges and dedupes across lenses; highest severity wins on overlap.
