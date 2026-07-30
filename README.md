<picture>
  <img src="docs/readme-banner.svg" width="100%" alt="Design Studio. Keep code out of the design decision." />
</picture>

<p align="center">
  <a href="https://george-rd.github.io/design-studio/"><strong>See the workflow</strong></a>
  ·
  <a href="#install"><strong>Install</strong></a>
  ·
  <a href="https://github.com/George-RD/design-studio/issues"><strong>Issues</strong></a>
</p>

# Design Studio

Design Studio keeps visual direction and evaluation away from source code. The Builder sees the implementation. The agents choosing and judging the design do not.

Code can implement the idea. It does not get to choose it.

<picture>
  <img src="docs/readme-flow.svg" width="100%" alt="Product truth moves to a source-blind Visual Director, then to a source-aware Builder, through browser checks, and into blind evaluation before the Orchestrator selects a build." />
</picture>

## The split

| Room | Roles | What it can see |
|---|---|---|
| **Source room** | Planner, Builder | Product files, source, routes, assets and implementation constraints |
| **Blind room** | Visual Director, Evaluator | Product truth, screenshots, the live page and scoped critique |
| **Decision owner** | Orchestrator | Run evidence, budgets, findings and preserved iterations |

The Evaluator reports what happened in the browser. It cannot decide to refine, pivot or ship. The Orchestrator applies the recorded rules.

## Use it

Create a new surface:

```text
/design-studio:create a landing page for a small coffee shop
```

Replace the visual direction of an existing surface:

```text
/design-studio:create --overhaul ./site --goals "keep the information architecture" replace the visual direction
```

Audit and polish without redesigning:

```text
/design-studio:review ./site
```

A standard run gets four builds. The best eligible build wins, even when it is not the latest one.

## What a run records

- `roots.json` anchors the repository, app and product context before work starts.
- `capabilities.json` records the browser, server, detector and interaction tools that were actually available.
- `events.jsonl` makes each step resumable without overwriting completed work.
- Every direction, build, screenshot, finding and decision stays under one immutable run folder.
- Mechanical checks and blind browser judgement remain separate.
- The accepted build becomes `DESIGN.md`, design DNA and reusable tokens.

`COPY.md` is optional. When present, it carries durable voice, claim and terminology rules into the surface brief. Design Studio can also call Growth Arsenal's `business-copy-style` workflow when it is installed.

## Install

Add this repository as a Claude Code marketplace, install the plugin, then reload plugins:

```text
/plugin marketplace add George-RD/design-studio
/plugin install design-studio@design-studio
/reload-plugins
```

The CLI equivalents are:

```bash
claude plugin marketplace add George-RD/design-studio
claude plugin install design-studio@design-studio
```

## Run output

```text
harness-output/
├── runs/<run-id>/
│   ├── roots.json, capabilities.json, events.jsonl
│   ├── spec.md, sprint-contract.md, surface-brief.md
│   ├── iterations/<n>/
│   │   ├── direction/
│   │   ├── site/
│   │   ├── mechanical-findings.json
│   │   └── screenshots/, observation.json, critique.md
│   └── finish/
├── site/
├── design-system/
└── report.md
```

Completed iterations are immutable. A failed or interrupted run resumes from the first incomplete step after its recorded artifacts pass validation.

## Optional Impeccable gate

When the `impeccable` CLI is available, Design Studio uses its source, desktop and mobile detector passes for mechanical preflight. Each rerun is a complete current snapshot. Fixed findings leave the open set, and a reintroduced problem becomes open again.

Without Impeccable, the workflow records `detector: fallback` and runs a smaller browser-computed gate. Detector output never counts as visual judgement.

## Requirements

- File and shell access.
- Isolated subagents.
- A runnable target or valid `serve.json` contract.
- Browser automation for a complete Studio decision. Without it, Design Studio can preserve one unselected build and the mechanical evidence, but it will not invent a visual verdict.

## Licence

MIT. Optional Impeccable integration is attributed in `NOTICE.md` and remains governed by Impeccable's Apache-2.0 licence.
