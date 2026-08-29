<picture>
  <img src="docs/readme-banner.svg" width="100%" alt="Design Studio. Keep code out of the design decision." />
</picture>

<p align="center">
  <a href="https://george-rd.github.io/design-studio/"><strong>See the workflow</strong></a>
  ·
  <a href="#install"><strong>Install</strong></a>
  ·
  <a href="ROADMAP.md"><strong>Roadmap</strong></a>
  ·
  <a href="https://github.com/George-RD/design-studio/issues"><strong>Issues</strong></a>
</p>

# Design Studio

Design Studio is a portable design-engineering Agent Skill for creating, reviewing and judging visual work while keeping source code out of visual direction and evaluation.

The Builder sees the implementation. The agents choosing and judging the design do not. Code can implement the idea; it does not get to choose it.

<picture>
  <img src="docs/readme-flow.svg" width="100%" alt="Product truth moves to a source-blind Visual Director, then to a source-aware Builder, through browser checks, and into blind evaluation before the Orchestrator selects a build." />
</picture>

## Lanes

| Lane | Use it for | Primary authority |
|---|---|---|
| **Studio** | New interactive surfaces and material redesigns | `skills/design-studio/workflow.yaml` |
| **Review** | Audit and polish while preserving the existing visual world | `skills/design-studio/references/review/polish.md` |
| **Document** | Quotes, invoices, SOWs, proposals, reports and other paginated print/PDF artifacts | `skills/design-studio/references/document/document.md` |

Studio and Review also have optional Claude Code slash-command adapters. Document is invoked through the Agent Skill directly; there is no separate Document slash command.

## The split

| Room | Roles | What it can see |
|---|---|---|
| **Source room** | Planner, Builder | Product files, source, routes, assets and implementation constraints |
| **Blind room** | Visual Director, Evaluator | Product truth, screenshots, rendered pages, the live page and scoped critique |
| **Decision owner** | Orchestrator | Run evidence, budgets, findings and preserved iterations |

The Evaluator reports visible evidence. It cannot decide to refine, pivot or ship. The Orchestrator applies the recorded rules.

## Use it

With the Agent Skill installed, ask a capable host to use Design Studio directly:

```text
Use Design Studio to create a landing page for a small coffee shop.
Use Design Studio to review ./site without redesigning it.
Use Design Studio to design a paginated proposal and judge the rendered pages.
```

Claude Code can expose Studio and Review through its optional adapter:

```text
/design-studio:create a landing page for a small coffee shop
/design-studio:create --overhaul ./site --goals "keep the information architecture" replace the visual direction
/design-studio:review ./site
```

## Install

The canonical, host-portable product is the Agent Skill:

```bash
npx skills add George-RD/design-studio
```

`npx skills` is the installer used to obtain the Agent Skill; it is not a Design Studio runtime dependency. The public GitHub repository is the install source, so no separate skills.sh registration is required. A capable host can also copy `skills/design-studio/` into its local skills directory.

The Claude Code plugin is an optional, thin adapter over the same Agent Skill and does not reduce supported capability when absent on a capable host. See [ADR 0003](docs/decisions/0003-claude-adapter-and-deferred-cli.md) and [optional adapters](docs/runtime-boundary.md#optional-adapters).

```text
/plugin marketplace add George-RD/design-studio
/plugin install design-studio@design-studio
/reload-plugins
```

Claude CLI equivalents: `claude plugin marketplace add George-RD/design-studio` and `claude plugin install design-studio@design-studio`.

## Runtime requirements

- File and shell access plus isolated subagents.
- Studio needs a runnable target or valid `serve.json` and browser automation for a complete visual decision.
- Review needs rendered interactive evidence for a verified visual verdict.
- Document needs complete ordered rendered-page evidence from an existing artifact or a host-supplied renderer for a visual decision.

When required visual evidence is missing, Design Studio preserves bounded evidence and reports the result as unselected or unverified rather than inventing a verdict.

## Runtime boundary

A standard Agent Skills install contains `skills/design-studio/`. Root `commands/`, `agents/` and `.claude-plugin/` are optional compatibility adapters.

Repository `scripts/`, `benchmarks/`, `test/` and `.github/` are research and development support, not runtime dependencies. Deterministic helpers needed by a supported run ship inside the skill behind its internal runtime contract. After installation, the copied skill runs from that contract and host capabilities without requiring the `skills` CLI. See [the runtime boundary](docs/runtime-boundary.md).

## What a run records

- `roots.json` anchors the repository, app and product context before work starts.
- `capabilities.json` records the tools and evidence that were actually available.
- `events.jsonl` makes each step resumable without overwriting completed work.
- Directions, builds, rendered evidence, findings and decisions stay under one immutable run folder.
- Mechanical checks and source-blind visual judgement remain separate.
- Only an accepted final tree becomes durable visual authority.

`COPY.md` is optional. Growth Arsenal may provide separate approved offer or copy inputs through the composition contract; it is not required to install or run Design Studio.

## Run output

```text
harness-output/
├── runs/<run-id>/
│   ├── roots.json, capabilities.json, events.jsonl
│   ├── spec.md, sprint-contract.md, surface-brief.md
│   ├── iterations/<n>/
│   └── finish/
├── site/
├── design-system/
└── report.md
```

## v1.7 product boundary

Design Studio v1.7 has one self-contained Design Studio runtime: the installed Agent Skill. It ships a local deterministic mechanical runtime under `skills/design-studio/runtime/`; supported behavior does not branch on whether another design package is installed.

External systems are research inputs, not runtime dependencies. Impeccable and Emil Kowalski's skills are credited sources, not install requirements. Adopted methods live in the local kernel with provenance and progressive disclosure. Growth Arsenal remains a separate optional skill and composes only through the neutral artifact contract. See [ADR 0002](docs/decisions/0002-owned-method-kernel.md).

Codex and Claude Code are exercised through the standard Agent Skills install in CI. The first-class Document lane is renderer-neutral and uses complete rendered pages as visual evidence. See [the prepared v1.7 evidence record](docs/releases/v1.7.0.md).

Mechanical findings remain evidence. They never substitute for source-blind judgement of the rendered result.

## Licence

MIT. Attribution and licence notes for Impeccable and Emil Kowalski's skills are recorded in `NOTICE.md`; neither is required to install Design Studio.
