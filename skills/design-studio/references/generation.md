# Builder contract

Builder translates the selected visual contract into a working surface. It decides technical means, never a different design.

## Inputs

- `roots.json`, especially `appRoot` and `contextRoot`;
- `design-description.md` from Visual Director;
- product truth, spec, sprint contract and surface brief;
- copy baseline and constraints when text changes;
- source substrate for greenfield or overhaul;
- previous iteration site only on REFINE;
- existing `DESIGN.md` only when the task extends or refines that system.

On PIVOT, start from a clean copy of product behaviour and content. Do not carry visual structure, tokens or decorative code from the abandoned direction merely because reuse is convenient.

## Root discipline

Run project commands from the working directory recorded in `roots.json` or a validated `serve.json`. Do not infer the app root again inside Builder.

`serve.json` must state:

- command and arguments;
- working directory;
- expected URL or port;
- readiness condition;
- shutdown method when needed;
- source tree it serves.

Reject a serve contract that points outside the recorded local repository unless the target is explicitly external.

## Immutable output

Write only inside the current `iterations/<N>/` directory. Earlier iteration files are read-only evidence.

Required outputs:

- `site/`: runnable source;
- `serve.json`: validated run contract;
- `design-flags.json`: one entry for every material visual instruction;
- build notes needed by Orchestrator, never blind Evaluator.

Never self-commit, change branches or push. Git history is not the iteration store.

## Fidelity

Translate every material instruction into a testable requirement before coding. Literal proportions, scale relationships, named colours, content order and interaction intent remain literal unless technically impossible.

For each instruction, record:

- `implemented`: rendered as specified;
- `equivalent`: different technique, same visible or interactive outcome, with reason;
- `blocked`: cannot be delivered within current constraints, with evidence and closest safe behaviour.

Never silently soften scale, mute colour, conventionalise composition, omit a signature interaction or add decorative concepts absent from the direction.

## Product, copy and usability floor

Creative fidelity does not excuse broken product behaviour. Preserve or add as required:

- confirmed product facts and claim boundaries;
- incumbent copy unless an evaluated rewrite replaces it;
- semantic structure and landmarks;
- working keyboard path and visible focus;
- labels, names, descriptions and meaningful alternatives;
- responsive recomposition at verified viewports;
- loading, empty, error, disabled, success and degraded states where reachable;
- reduced-motion behaviour;
- honest synthetic or demo labels when real content is unavailable;
- clear action hierarchy and recoverable errors;
- performance safeguards for expensive effects.

Accessibility and state completeness are implementation obligations, not unsolicited art direction.

## Tokens and assets

Keep design tokens in one canonical source so codify can extract them without guessing. Use project conventions when they are compatible with direction.

Author or source the assets the composition needs. Do not substitute gradients, blur, generic icon tiles or empty chrome where the contract requires real imagery, diagrams or demonstrations. Verify remote assets resolve and provide fallbacks.

## Pre-handoff checks

Before mechanical preflight:

1. run build and basic tests from the recorded app root;
2. verify `serve.json` from a clean shell;
3. compare every design flag against rendered output;
4. test primary interactions and states;
5. verify no earlier iteration changed;
6. inspect desktop and mobile once for obvious overflow or breakage;
7. remove debug controls and invented claims;
8. append completion only after output validation.

Do not perform blind aesthetic scoring. Evaluator owns that pass.
