# Design Studio

**A multi-agent design harness for frontends with a point of view.**

Design Studio separates the agents deciding what a surface should become from the agent writing the code. The Visual Director and Evaluator never see source. The Builder does. This prevents the incumbent implementation from quietly becoming the design brief.

[See the workflow →](https://george-rd.github.io/design-studio/)

## The mechanism

| Role | Sees source? | Owns |
|---|---:|---|
| Planner | Yes | Product truth, scope, constraints, success criteria |
| Visual Director | No | Competing directions and the selected visual contract |
| Builder | Yes | Faithful implementation, semantics, states, responsiveness |
| Evaluator | No | Rendered behaviour, visual quality, craft and originality |
| Orchestrator | As needed | Direction selection, iteration decisions, budget and final handoff |

The Evaluator reports observations and scores. It does **not** decide whether to refine, pivot or ship. That decision belongs to the Orchestrator and is derived from the run history.

## What changed in 1.4

- **Durable context.** `PRODUCT.md` stores product truth; `DESIGN.md` stores the proven visual system; each run gets a small surface brief.
- **Direction choice before code.** Unless an exact direction is already pinned, three viable directions are produced without ranking. The user chooses when available; unattended runs use a reproducible recorded seed.
- **Immutable iterations.** Every build, screenshot, critique and detector result is kept under `harness-output/runs/<run-id>/iterations/<n>/`.
- **Mechanical and visual checks are separate.** Deterministic checks catch contrast, overflow and known generated-UI tells. A blind browser evaluator judges the experience. Neither substitutes for the other.
- **One decision owner.** Evaluators observe. The Orchestrator applies the ordered decision table.
- **Bounded finishing.** The best iteration receives one fresh-context finish review and at most one correction batch before handoff.
- **Reality becomes the design system.** `DESIGN.md`, design DNA and tokens are documented from the shipped build, not from an early intention.

## Install

```bash
claude plugin install https://github.com/George-RD/design-studio
```

Then reload plugins and run:

```text
/design-studio:create a landing page for a small coffee shop
```

To redesign an existing surface:

```text
/design-studio:create --overhaul ./site --goals "keep the information architecture" \
  replace the visual direction and raise originality
```

To audit without redesigning:

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

A single component or narrow CSS correction should not invoke the full Studio lane. Use Review or ordinary implementation instead.

## Output

```text
harness-output/
├── runs/<run-id>/
│   ├── run.json
│   ├── spec.md
│   ├── sprint-contract.md
│   ├── surface-brief.md
│   ├── scores.json
│   ├── iterations/<n>/
│   │   ├── direction/                 # directions.md omitted only for an exact pinned direction
│   │   ├── site/
│   │   ├── serve.json
│   │   ├── design-flags.json
│   │   ├── mechanical-findings.json
│   │   ├── screenshots/
│   │   ├── observation.json
│   │   └── critique.md
│   └── finish/
├── site/                       # final selected build
├── report.md
└── design-system/
    ├── design-dna.md
    ├── tokens.css
    └── skill/<project>-design/
```

## Optional Impeccable integration

When the `impeccable` CLI is installed, Design Studio uses its deterministic detector as the preferred mechanical preflight. Design Studio does not vendor Impeccable or copy its command suite; it consumes detector output and keeps its own orchestration model.

Without Impeccable, the harness runs a smaller browser-computed fallback gate. A detector result never counts as a visual review.

## Requirements

- A harness capable of isolated subagents.
- Local file and shell access.
- Browser automation that can set and verify desktop and mobile viewports.
- A runnable target or a `serve.json` contract.

## License

MIT. Optional Impeccable integration is attributed in `NOTICE.md` and remains governed by Impeccable's own Apache-2.0 license.
