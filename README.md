# Design Studio

**A multi-agent design harness for frontends with a point of view.**

Design Studio separates the agents deciding what a surface should become from the agent writing the code. The Visual Director and Evaluator never see source. The Builder does. This prevents the incumbent implementation from quietly becoming the design brief.

[See the workflow →](https://george-rd.github.io/design-studio/)

## The mechanism

| Role | Sees source? | Owns |
|---|---:|---|
| Planner | Yes | Product truth, scope, constraints and success criteria |
| Visual Director | No | Competing directions and the selected visual contract |
| Builder | Yes | Faithful implementation, semantics, states and responsiveness |
| Evaluator | No | Rendered behaviour, visual quality, craft and originality |
| Orchestrator | As needed | Direction selection, iteration decisions, budget and final handoff |

The Evaluator reports observations and scores. It does **not** decide whether to refine, pivot or ship. That decision belongs to the Orchestrator and is derived from the run history.

## What changed in 1.4

- **Durable context.** `PRODUCT.md` stores product truth; `DESIGN.md` stores the proven visual system; each run gets a small surface brief.
- **Direction choice before code.** Unless an exact direction is already pinned, three viable directions are produced without ranking. The user chooses when available; unattended runs use a reproducible recorded seed.
- **Immutable iterations.** Every build, screenshot, critique and detector result is kept under `harness-output/runs/<run-id>/iterations/<n>/`.
- **Mechanical and visual checks are separate.** Deterministic checks catch contrast, overflow and known generated-UI tells. A blind browser evaluator judges the experience. Neither substitutes for the other.
- **One decision owner.** Evaluators observe. The Orchestrator applies the ordered decision table.
- **Floor-aware selection.** A build that passes every quality floor outranks a higher average with a failed criterion.
- **Bounded finishing.** The selected iteration receives one fresh-context finish review and at most one correction batch before handoff.
- **Reality becomes the design system.** `DESIGN.md`, design DNA and tokens are documented from the shipped build, not from an early intention.

## Install

Add this repository as a Claude Code marketplace, install the plugin, then reload plugins:

```text
/plugin marketplace add George-RD/design-studio
/plugin install design-studio@design-studio
/reload-plugins
```

The non-interactive CLI equivalents are:

```bash
claude plugin marketplace add George-RD/design-studio
claude plugin install design-studio@design-studio
```

Run a new design:

```text
/design-studio:create a landing page for a small coffee shop
```

Redesign an existing surface:

```text
/design-studio:create --overhaul ./site --goals "keep the information architecture" replace the visual direction and raise originality
```

Audit without redesigning:

```text
/design-studio:review ./site
```

## Run shape

```text
Context → Plan → Explore directions → Select → Build → Mechanical preflight
        → Blind browser evaluation → Orchestrator decision → Repeat if justified
        → Fresh finish review → Codify → Handoff
```

Default iteration budgets are deliberately finite:

| Run class | Default budget | Typical use |
|---|---:|---|
| Quick | 2 | Focused surface or straightforward page |
| Standard | 4 | Ambitious landing page or product screen |
| Ambitious | 6 | Complex page, experience or multi-state interface |

An explicit numeric budget is clamped to 1–8. A single component or narrow CSS correction should not invoke the full Studio lane. Use Review or ordinary implementation instead.

## Output contract

```text
harness-output/
├── runs/<run-id>/
│   ├── run.json
│   ├── spec.md
│   ├── sprint-contract.md
│   ├── surface-brief.md
│   ├── baseline/                         # overhaul only
│   ├── scores.json
│   ├── iterations/<n>/
│   │   ├── direction/
│   │   │   ├── directions.md             # omitted for an exact pinned direction
│   │   │   ├── direction-selection.json
│   │   │   ├── selected-direction.md
│   │   │   └── design-description.md
│   │   ├── site/
│   │   ├── serve.json
│   │   ├── design-flags.json
│   │   ├── mechanical-findings.json
│   │   ├── screenshots/
│   │   ├── observation.json
│   │   └── critique.md
│   └── finish/
│       ├── selection.json
│       ├── selected-site/
│       ├── selected-serve.json
│       ├── selected-direction.md
│       ├── corrected-site/               # only when the bounded correction runs
│       ├── corrected-serve.json           # only when the bounded correction runs
│       ├── correction-verdict.json        # only when the bounded correction runs
│       └── final-tree.json
├── site/                                  # accepted final build
├── report.md
└── design-system/
    ├── design-dna.md
    ├── tokens.css
    └── skill/<project>-design/
```

Completed iteration directories are immutable. A refinement creates a new iteration and copies the selected direction metadata forward. A pivot creates a new iteration with a new direction tournament. Final selection copies the winning iteration’s own direction summary into the finish artifacts before review, so an earlier pre-pivot winner is never judged against a later pivot. The final site is copied from the accepted finish tree; a correction cannot replace the selected build merely because its directory exists.

## Optional Impeccable integration

When the `impeccable` CLI is installed, Design Studio uses its deterministic detector as the preferred mechanical preflight. Design Studio does not vendor Impeccable or copy its command suite; it consumes detector output and keeps its own orchestration model.

Without Impeccable, the harness runs a smaller browser-computed fallback gate and records `detector: fallback`. A detector result never counts as a visual review.

## Requirements

- A harness capable of isolated subagents.
- Local file and shell access.
- Browser automation that can set and verify desktop and mobile viewports.
- A runnable target or a valid `serve.json` contract.

## License

MIT. Optional Impeccable integration is attributed in `NOTICE.md` and remains governed by Impeccable's own Apache-2.0 license.
