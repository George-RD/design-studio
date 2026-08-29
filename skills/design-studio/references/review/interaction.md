# Visual lens: interaction, state and motion

## Purpose

Review controls, state completeness, feedback and motion as user-visible behaviour. Motion is admitted only when it serves a named purpose at an appropriate interaction frequency.

## Triggers

Load when Review includes controls, forms, stateful navigation, dialogs/popovers, async/data states, keyboard paths, carousels, animation/transition work, or evidence shows unclear affordance/feedback.

## Required context

Use real browser interaction, accessibility tree, current mechanical findings, surface goal, established design authority and the frequency/context of affected actions. Evidence must name the control/action/state and viewport.

## Outputs and handoff

Report findings only. Inventory meaningful controls and reachable loading/empty/error/partial/degraded states; test affordance, hover/pointer feedback where relevant, active acknowledgement, keyboard/focus, disabled reasons, async duplicate-submit prevention, success/failure feedback, overlay Escape/focus return and mobile touch behaviour. For routed motion work, record the purpose/frequency decision and any deliberately rejected motion opportunity in run evidence so a later pass does not re-propose it without new evidence.

## Authority boundary

This leaf owns experiential interaction/state/motion judgement. Exact source semantics, contrast, viewport and target measurements remain mechanical evidence. Existing project motion tokens and the brief outrank generic timing heuristics. Do not turn upstream framework-specific prescriptions into universal bans.

## Failure behavior

If an interaction/state cannot be reached, report it as unverified rather than passing it. Motion without a defensible purpose is removed or left instant. High-frequency or keyboard-driven actions default to instant or near-imperceptible feedback unless product evidence justifies more. Reduced-motion support is mandatory for meaningful movement.

## Evaluation hooks

Motion purpose must be one of feedback, spatial continuity, state indication, preventing a jarring change, explanation, or rare delight. Treat frequency as a pressure toward less motion: repeated/high-frequency actions should be fastest/subtlest; occasional overlays may use standard motion; rare explanatory moments may carry more.

Use project tokens first. As review heuristics, button feedback commonly lands around 100–160ms, small popovers 125–200ms, dropdown/select transitions 150–250ms, and larger modal/drawer motion may extend roughly 200–500ms when distance/context warrants it. UI motion materially above ~300ms needs a reason. Rapidly retriggered motion should retarget from the current state rather than visibly restart; gestures should remain interruptible; anchored transitions should feel spatially connected to their trigger; exits should preserve understandable continuity.

Blocker: broken primary control, inaccessible keyboard path, focus trap, silent destructive failure or motion that prevents task completion. Quality: unclear affordance, missing feedback/state/recovery, non-interruptible dynamic UI, or unjustified distracting motion. Polish: local timing/transition refinement.

## Source provenance

Adopted local method slices: `emilkowalski/skills` at revision `d23d7f88a2e21c9e4b1418c7abe420f5c1052ba7`, MIT. This is provenance only; the upstream project is not required at runtime.

Design Studio adapts (1) the purpose/frequency gate from `skills/improve-animations/SKILL.md`, (2) bounded timing/interruptibility heuristics from `skills/animate/SKILL.md`, and (3) concise evidence for rejected animation opportunities. Values are contextual review ranges, not framework-specific prescriptions. No upstream animation toolchain is vendored.
