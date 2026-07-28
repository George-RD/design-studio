# Visual lens: interaction and state completeness

Run for interactive surfaces or when the user asks about controls, states, keyboard or feedback. Ground every finding in observed behaviour.

## Inventory

Use the browser accessibility tree and real interaction to list:

- buttons and action links;
- inputs, selects, toggles, sliders and custom controls;
- tabs, menus, sidebars and disclosure controls;
- dialogs, popovers, sheets, carousels and scroll regions;
- rows/cards that are actionable;
- async/network actions and data-driven views.

## Per-control checks

- clear affordance at rest;
- pointer/hover feedback where relevant;
- pressed/active acknowledgement;
- logical keyboard reach and visible focus;
- disabled state that communicates why when gated;
- in-place loading and duplicate-submit prevention for async actions;
- explicit success or failure feedback;
- Escape, focus trapping and focus return for overlays;
- touch behaviour and target size at mobile.

## Per-screen/data checks

Where reachable, test loading, empty, error, partial, offline/degraded and long-content states. Empty/error states should provide a useful next action or recovery path.

## Transitions

Motion should clarify state change and never delay input. Verify reduced-motion behaviour for meaningful animation. Do not prescribe a specific CSS technique.

## Severity

- `blocker`: broken primary control, inaccessible keyboard path, focus trap, silent destructive/async failure, or state that prevents task completion.
- `quality`: missing feedback, unclear affordance, disabled-without-reason, or important empty/error/degraded state absent.
- `polish`: timing, transition or minor feedback refinement.

Evidence names the control, action taken, observed response and viewport. “Looks clickable” is not interaction evidence.
