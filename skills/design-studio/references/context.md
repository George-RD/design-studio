# Context model

Design Studio uses three authorities with different lifetimes. Do not collapse them into one brief.

## PRODUCT.md — durable product truth

`PRODUCT.md` records facts that future runs should not rediscover or invent. Inspect the repository before asking the user. Update an existing file rather than creating a competing authority.

Recommended shape:

```markdown
# Product

<!-- design-studio:product-schema 1 -->

## Platform
web

Design Studio 1.4 evaluates browser-rendered web surfaces. Do not record `ios`, `android` or another native platform here unless the harness gains a native evaluator and workflow first.

## Users and situation
[Who uses it, where, and what job they are doing.]

## Purpose and success
[What becomes possible and how success is recognised.]

## Positioning
[The truthful mechanism or position a neighbouring product could not copy unchanged.]

## Operating context
[Workflows, environments, tools, documents and constraints that are factual parts of use.]

## Capabilities and constraints
[Confirmed behaviour, terminology, technical or legal constraints, and labelled open decisions.]

## Brand commitments
[Name, voice, assets and explicitly pinned visual or identity constraints.]

## Evidence on hand
[Real demos, data, screenshots, testimonials, case studies and asset paths. State important absences.]

## Product principles
[Three to five durable principles, without visual recipes.]

## Accessibility and inclusion
[Known user needs or required standard.]
```

Ask only about material gaps the request and repository do not answer. Keep interview rounds small. Record undecided facts instead of inventing them. A redesign changes visual authority, not confirmed product truth.

Do not put palettes, component recipes, page layouts or an invented visual world in `PRODUCT.md`. Never invent prices, customers, benchmarks, capabilities, endpoints or testimonials.

## DESIGN.md — proven visual system

`DESIGN.md` records the visual system demonstrated by a shipped build.

- **Extension or refinement:** existing `DESIGN.md` is authority unless the user changes it.
- **Requested redesign:** preserve explicit brand commitments, but treat the incumbent visual world as evidence and an anti-reference rather than something to average into the replacement.
- **Missing file:** inspect code, tokens, components and assets before deciding there is no visual authority.

For a new or replaced world, write `DESIGN.md` after the build and finish review. Ground it in the final screenshots and canonical tokens, not an early intention.

Recommended content:

- name and essence;
- principles;
- visual thesis and creative tension;
- colour roles and contrast rules;
- typography roles and scale relationships;
- spatial rhythm and layout logic;
- component and control grammar;
- motion and interaction;
- responsive behaviour;
- signature motifs;
- content/voice rules;
- anti-goals and intentional exceptions;
- provenance: run ID, selected iteration and token paths.

## surface-brief.md — current surface strategy

Write `harness-output/runs/<run-id>/surface-brief.md` for the requested route, screen or artifact.

Keep it small:

- scope and mode: persuade / operate / read / experience;
- audience and situation;
- job, primary action or task;
- real content, proof and assets available;
- constraints and untouched areas;
- selected direction and memorable moment;
- unresolved surface decisions.

Do not duplicate global product truth or full token documentation here.

## Authority order

1. Explicit current user instruction.
2. Confirmed product truth and pinned brand commitments.
3. Current surface brief.
4. Existing proven `DESIGN.md` when the task preserves the world.
5. Repository evidence, treated as a hypothesis until confirmed.
6. Model preference, which has no authority.
