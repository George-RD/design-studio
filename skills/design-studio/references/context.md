# Context model

Design Studio keeps durable truth, proven design, current surface strategy and operational run facts separate. Do not collapse them into one brief.

## roots.json and capabilities.json: operational truth

`roots.json` answers where the repository, app and governing context live. `capabilities.json` answers which tools and target contracts were actually available for this run.

They are written before planning and are not creative inputs. Load `runtime-integrity.md` for resolution and resume rules.

## PRODUCT.md: durable product truth

`PRODUCT.md` records facts future runs should not rediscover or invent. Inspect the repository before asking the user. Update an existing file rather than creating a competing authority.

Recommended shape:

```markdown
# Product

<!-- design-studio:product-schema 1 -->

## Platform
web | ios | android | adaptive

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

The `Positioning` section is a durable snapshot only when that decision is explicitly settled. Design Studio does not create or revise positioning strategy; a user- or Growth-Arsenal-approved positioning change must update the snapshot before Design Studio treats it as confirmed product context.

Ask only about material gaps the request and repository do not answer. Record undecided facts instead of inventing them. A redesign changes visual authority, not confirmed product truth.

Do not put palettes, component recipes, page layouts or an invented visual world in `PRODUCT.md`. Never invent prices, customers, benchmarks, capabilities, endpoints or testimonials.

## COPY.md: durable language system

`COPY.md` is optional. When present, it records language decisions that should survive individual pages:

- audience vocabulary and terms to repeat consistently;
- voice and sentence character;
- claim boundaries and proof rules;
- action labels and microcopy conventions;
- journey-specific guidance;
- localisation, accessibility and AI-disclosure rules;
- phrases and structures to avoid.

Load it into planning and the surface brief. Do not let it override confirmed product facts. Do not create it for a one-line edit unless the user asks to preserve language rules across future work.

When a candidate external offer/copy artifact or composition metadata is present, do not infer authority from `COPY.md` or any other basename. Classify candidate artifacts by declared role, project scope and approval/acceptance provenance using `../composition-contract.json`. Add the `composition-artifacts` evidence signal so the method router loads the local copy boundary. Its human reference is `composition-contract.md`.

A Growth Arsenal repository-internal `DESIGN.md` or token file is not project visual authority merely because its name matches Design Studio's project artifact. Role and scope come before basename.

## DESIGN.md: proven visual system

`DESIGN.md` records the visual system demonstrated by an accepted build.

- **Extension or refinement**: existing project-scoped accepted `DESIGN.md` is authority unless the user changes it.
- **Requested redesign**: preserve explicit brand commitments, but treat the incumbent visual world as evidence and an anti-reference rather than something to average into the replacement.
- **Missing file**: inspect code, tokens, components and assets before deciding there is no visual authority.

For a new or replaced world, write `DESIGN.md` only after acceptance. Ground it in final screenshots and canonical tokens, not an early intention.

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
- content and voice rules that belong to visual application;
- anti-goals and intentional exceptions;
- provenance: run ID, accepted iteration and token paths.

## surface-brief.md: current surface strategy

Write `harness-output/runs/<run-id>/surface-brief.md` for the requested route, screen or artifact.

Keep it small:

- scope and mode: persuade, operate, read or experience;
- audience and situation;
- job, primary action or task;
- real content, proof and assets available;
- copy baseline and constraints when text changes;
- visual and behavioural constraints;
- untouched areas;
- unresolved surface decisions.

Do not duplicate global product truth, the selected visual contract or full token documentation. The surface brief remains stable across direction exploration.

## selected-direction.md: chosen visual contract summary

After selection, write `iterations/<n>/direction/selected-direction.md` as a source-free summary of the chosen candidate.

Include:

- candidate ID, selection method and whether selection was precommitted;
- visual thesis and creative tension;
- first-viewport composition;
- visitor or task path;
- visual grammar, typography and colour roles;
- responsive behaviour and interaction intent;
- signature moment;
- known risk and anti-goals.

This file is the immutable direction bridge for one iteration. REFINE copies it forward. PIVOT writes a new summary. Final selection copies the chosen iteration's summary into `finish/selected-direction.md` so fresh review uses the direction that build actually implemented. Regular iteration evaluation does not receive it.

## events.jsonl and acceptance.json: run evidence

`events.jsonl` records how the workflow progressed and where a resume should continue. `finish/acceptance.json` proves which final tree became authoritative. Neither file may contain invented visual scores.

## Authority order

Every run starts with:

1. Explicit current user instruction.
2. Confirmed product truth and pinned brand commitments.
3. The authoritative approved offer/copy artifact resolved through the composition contract when composition evidence exists; otherwise durable `COPY.md` language rules when present.
4. Current surface brief.

For an **extension, polish or preserve-world refinement**:

5. Existing project-scoped accepted `DESIGN.md`.
6. `selected-direction.md`, constrained to evolve the requested surface without replacing the proven system.

For a **greenfield surface or explicit redesign**:

5. `selected-direction.md` for active visual choices.
6. Existing project-scoped accepted `DESIGN.md` only for retained commitments, useful evidence and anti-reference lessons.

Then, in either mode:

7. Repository evidence, treated as a hypothesis until confirmed.
8. Model preference, which has no authority.

When a higher-authority artifact changes, apply the staleness rules in `../composition-contract.json` rather than treating every downstream file as current because it is newer on disk.
