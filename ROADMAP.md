# Design Studio roadmap

## Direction

Design Studio will become a **self-contained agentic design system with a curated method kernel**.

It will not expose separate quality paths depending on whether another design project is installed. Users get **one supported runtime**. Design Studio owns the workflow, the method selection, the evidence, the final judgement and the learning loop.

External systems remain valuable research sources. Impeccable, Emil Kowalski's skills, Growth Arsenal, Scroll World and later specialist work can contribute ideas, procedures or narrowly bounded implementation slices. Design Studio adopts only the parts that prove useful, reshapes them for progressive disclosure and role isolation, records their provenance, and periodically reviews upstream changes without silently synchronising them into live runs.

The first user remains George. Repeated real projects and owner corrections are the main proving ground. The goal is not to remove human judgement entirely; it is to convert recurring, transferable corrections into a workflow that produces distinctive, coherent results with fewer feedback rounds.

The governing decision is [ADR 0002: Design Studio owns its method kernel](docs/decisions/0002-owned-method-kernel.md).

## Operating model

| Layer | Design Studio owns |
|---|---|
| Product truth | Audience, outcome, constraints, proof, current state, settled decisions and required behaviour |
| Direction | Source-blind divergence, named axes, governing metaphor and explicit trade-offs |
| Method routing | A small always-loaded authority layer plus task-specific progressive-disclosure leaves |
| Implementation | Source-aware building against the selected direction and real product constraints |
| Mechanical evidence | A stable local set of justified deterministic checks |
| Visual judgement | Source-blind rendered evaluation at component, whole-page and target-viewport levels |
| Acceptance | Immutable attempts, one decision owner, provenance, resume and final evidence |
| Learning | A feedback-to-eval loop that converts repeated owner corrections into tested interventions |

External projects own their original work. Design Studio records exact source revisions, licences and adaptations, but no external project controls supported runtime behaviour.

## Design principles

- [x] Preserve source-blind direction and rendered evaluation.
- [x] Preserve immutable attempts, resumable evidence and one final decision owner.
- [x] Use one supported Design Studio runtime rather than optional quality modes.
- [x] Prefer selective, attributed method intake over wholesale cloning.
- [x] Load specialist knowledge through progressive disclosure.
- [x] Separate mechanical checks from perceptual judgement.
- [x] Treat raw owner feedback as research evidence before abstracting it into a rule.
- [x] Protect settled decisions from unnecessary redesign churn.
- [x] Remove interventions that add prompt volume without improving outcomes.

## Success measures

The architecture is useful only when representative projects show that it:

- reduces the number and severity of owner corrections after the first complete pass;
- produces genuinely different product worlds rather than variations of one house style;
- keeps accepted visual and product decisions stable while fixing local problems;
- catches page-level responsive, semantic and interaction failures before owner review;
- distinguishes technically present motion from perceptually effective motion;
- keeps task-specific knowledge out of the always-loaded prompt;
- records the origin, licence and local modification of adopted external methods;
- can update one method without changing unrelated workflow behaviour;
- removes a method when its maintenance or prompt cost exceeds its measured value.

---

## Historical Milestone 0 evidence

The previous roadmap tested Design Studio as an orchestration layer around Impeccable. The completed evidence remains useful, but the required-dependency architecture is superseded by ADR 0002.

Completed assets retained:

- [x] Architecture boundary research in [ADR 0001](docs/decisions/0001-impeccable-foundation.md), now historical.
- [x] Frozen representative fixtures in [benchmarks/milestone-0](benchmarks/milestone-0/README.md).
- [x] Tamper-evident lane, matrix and blind-preference infrastructure.
- [x] Controlled source-blind agent, browser and evidence capability gates.
- [x] Inventory every Design Studio step, reference, schema and check. Evidence: [ownership inventory](benchmarks/milestone-0/OWNERSHIP_INVENTORY.md).
- [x] Identify workflows that only reproduce an Impeccable command and record their previous delegate/delete disposition.

Historical items deliberately left open rather than falsely completed:

- [ ] Run the same fixed briefs through: retained as an optional research comparison, not a release gate.
- [ ] Confirm the smallest differentiated product: re-framed below as proving the owned kernel and lower human correction.

Do not spend paid runs merely to finish the superseded three-lane matrix. Use the harness only when a targeted comparison answers a live method-intake or ablation question.

---

## Milestone 0: reset the product boundary

**Goal:** replace the external-foundation plan with one owned product and preserve useful prior evidence.

- [x] Accept ADR 0002 and supersede the required-runtime-foundation decision.
- [x] Pin reviewed upstream research sources in [docs/method-sources.json](docs/method-sources.json).
- [x] Extract reusable Horaxon feedback classes in [docs/research/horaxon-feedback-patterns.json](docs/research/horaxon-feedback-patterns.json).
- [x] Add an exact-head contract that prevents the roadmap from returning to optional with/without runtime modes.
- [ ] Reclassify the historical ownership inventory from `core` / `impeccable` / `external-workflow` into:
  - [ ] keep-local;
  - [ ] adapt-local;
  - [ ] vendor-slice;
  - [ ] observe;
  - [ ] delete.
- [ ] Identify every current runtime branch whose only purpose is handling Impeccable availability.
- [ ] Freeze the first owned-kernel baseline before behaviour changes.
- [ ] Define the smallest v1.6 release slice and its evidence.

**Exit:** one authoritative architecture, one runtime path, one source registry and an executable migration map.

## Milestone 1: build the owned method kernel

**Target:** v1.6

### 1.1 Authority and progressive disclosure

- [ ] Reduce the always-loaded skill to role boundaries, lifecycle, routing, evidence and acceptance authority.
- [ ] Give every design principle one canonical local authority file.
- [ ] Route specialist leaves by task, surface type, interaction frequency and evidence need.
- [ ] Define a minimal leaf contract:
  - [ ] purpose and triggers;
  - [ ] required context;
  - [ ] outputs and handoff;
  - [ ] authority boundaries;
  - [ ] failure behaviour;
  - [ ] evaluation hooks;
  - [ ] source provenance where adapted.
- [ ] Measure always-loaded token reduction against v1.5.

### 1.2 One supported runtime

- [ ] Remove user-visible and internal “with Impeccable” / “without Impeccable” branches.
- [ ] Remove dependency preflight whose only purpose is selecting a quality path.
- [ ] Make every supported check and method available from the distributed Design Studio package.
- [ ] Fail only for Design Studio's own missing capabilities, not an optional upstream installation.
- [ ] Preserve exact source and licence metadata for adapted or vendored material.

### 1.3 Mechanical check selection

- [ ] Re-evaluate each current detector family against real defect evidence and false-positive cost.
- [ ] Keep only checks that are explainable, testable and cheaper to maintain than the rework they prevent.
- [ ] Adapt or vendor the smallest proven slices rather than copying a complete upstream command system.
- [ ] Keep mechanical findings separate from source-blind visual judgement.
- [ ] Add contract tests before deleting old fallback or duplicate logic.

**Exit:** v1.6 installs as one coherent product, loads only relevant methods, and does not change behaviour based on external tool availability.

## Milestone 2: reduce first-pass human correction

**Target:** v1.7

Use Horaxon feedback as evidence of missed decision classes, not as a universal visual template.

### 2.1 Product world and direction quality

- [ ] Expand product context to capture:
  - [ ] the user and business outcome;
  - [ ] the current experience and required behaviour;
  - [ ] proof and unsupported-claim boundaries;
  - [ ] settled decisions and explicitly open questions;
  - [ ] brand or product metaphors that are available, prohibited or already overused.
- [ ] Require every candidate direction to state a named divergence axis and governing metaphor.
- [ ] Reject candidates that could be transferred unchanged to an unrelated product.
- [ ] Keep variants fully functional and evaluate them in realistic context rather than as thumbnails.

### 2.2 Meaning and subtraction

- [ ] Add a semantic-redundancy pass for repeated labels, badges, claims and explanatory chrome.
- [ ] Require every visible label to name the distinct information it adds.
- [ ] Add a scope-discipline check that favours local repair over reopening a settled visual world.
- [ ] Add an intent review that asks what each strong treatment means, not only whether it is polished.

### 2.3 Action and affordance integrity

- [ ] Identify the primary user decision before visual polish.
- [ ] Trace the shortest valid action path at every target viewport.
- [ ] Enforce one canonical name per action unless two labels represent different actions.
- [ ] Compare hover, active, selected and elevated treatments against actual interaction/state semantics.
- [ ] Prevent positional styling such as `:last-child` from implying meaning it does not own.

### 2.4 Whole-page responsive composition

- [ ] Evaluate full-page and first-viewport captures at phone, laptop and wide desktop sizes.
- [ ] Measure major section gaps, primary-action position, overflow and reading continuity.
- [ ] Review page rhythm separately from component quality.
- [ ] Verify visual order, DOM order and keyboard order together.

### 2.5 Motion that can be felt and trusted

- [ ] Route motion through a purpose, frequency, speed and function gate.
- [ ] Record rejected motion opportunities as evidence of restraint.
- [ ] Prefer interruptible transitions for rapidly reversible UI state.
- [ ] Require no-JS, reduced-motion and unsupported-engine settled states.
- [ ] Distinguish computed motion evidence from real-device perceptual confidence.
- [ ] Use physical-device or high-fidelity replay review when motion value depends on being noticed.

### 2.6 Contract migrations

- [ ] Treat material copy, action and state changes as migrations across canonical docs, rendered surfaces, privacy/legal copy, compatibility fields and tests.
- [ ] Record intentional historical exceptions instead of leaving unexplained drift.

**Exit:** the workflow catches the principal Horaxon correction classes before owner review without forcing every project into the Traverse style.

## Milestone 3: create the feedback-to-eval loop

**Target:** v1.8

- [ ] Define a durable feedback record containing:
  - [ ] raw owner comment;
  - [ ] output and revision being criticised;
  - [ ] accepted correction;
  - [ ] local preference, one-off defect or reusable failure class;
  - [ ] missed workflow/evaluation point;
  - [ ] proposed intervention;
  - [ ] validation and later outcome.
- [ ] Add a command or maintenance workflow that mines completed dogfood PRs for unresolved learning.
- [ ] Promote a new always-on gate only after two independent examples or one severe outcome failure.
- [ ] Prefer evaluation questions and routed leaves over a growing universal prohibition list.
- [ ] Add regression fixtures for accepted reusable failure classes.
- [ ] Compare kernel revisions with the existing blind preference infrastructure.
- [ ] Track:
  - [ ] first-complete-pass acceptance;
  - [ ] owner feedback rounds;
  - [ ] material rework commits;
  - [ ] repeated correction classes;
  - [ ] elapsed/token/tool cost;
  - [ ] methods loaded per run;
  - [ ] methods later removed as low value.

**Exit:** feedback survives project history and can be shown to improve later runs rather than merely expanding prompts.

## Milestone 4: operate method intake and upstream scouting

**Target:** v1.9

- [ ] Run the method intake review at least quarterly.
- [ ] Trigger an extra review after a major upstream release, repeated dogfood gap or new specialist capability.
- [ ] Compare pinned source revisions and shortlist only changes relevant to known needs.
- [ ] Evaluate every candidate for:
  - [ ] outcome benefit;
  - [ ] overlap with local authority;
  - [ ] prompt and runtime cost;
  - [ ] maintenance and security cost;
  - [ ] licence/attribution impact;
  - [ ] fit with role isolation and progressive disclosure.
- [ ] Test candidates as targeted ablations before adoption.
- [ ] Record explicit adopt, observe or reject decisions.
- [ ] Never auto-pull latest guidance into a production run.
- [ ] Review at minimum:
  - [ ] Impeccable for useful deterministic checks and evidence patterns;
  - [ ] Emil Kowalski's skills for motion, prototype and audit workflows;
  - [ ] Growth Arsenal for copy/offer coordination;
  - [ ] Scroll World for cinematic scene-chain methods;
  - [ ] other specialist systems only when a real project exposes the need.

**Exit:** external expertise improves Design Studio without turning upstream projects into hidden runtime authorities.

## Milestone 5: prove autonomous, distinct dogfood outcomes

**Target:** v2.0

- [ ] Run the owned kernel on Horaxon or its next material surface revision.
- [ ] Run it on at least one product with a substantially different audience and visual world.
- [ ] Compare against the v1.5 baseline or an ablated kernel using identical briefs and evidence rules.
- [ ] Require source-blind preference evidence where outputs are comparable.
- [ ] Measure reduction in owner feedback rounds and material rework.
- [ ] Verify that outputs remain distinguishable and product-specific.
- [ ] Remove methods that add cost without improving quality, recovery, confidence or human intervention.
- [ ] Publish claims only after dogfood evidence supports them.

**Exit:** Design Studio repeatedly produces coherent, unique and usable results with materially less human steering, while preserving the ability to learn from expert external systems.

---

## Explicit non-goals

- Supporting different design quality depending on which upstream tools happen to be installed.
- Vendoring complete external projects before their useful slices are known.
- Copying prompts or rules without provenance and licence records.
- Automatically following upstream latest releases.
- Encoding Horaxon's Traverse visual language as a universal default.
- Replacing perceptual design judgement with a larger static detector catalogue.
- Eliminating all human taste; the target is fewer repeated corrections and better decision leverage.
- Building a public method marketplace before the owned kernel proves itself across distinct projects.

## Release sequence

| Release | Outcome |
|---|---|
| v1.6 | One owned runtime and progressively disclosed method kernel |
| v1.7 | Horaxon-derived meaning, subtraction, composition, affordance and motion interventions |
| v1.8 | Durable feedback-to-eval learning loop |
| v1.9 | Evidence-gated periodic upstream method intake |
| v2.0 | Distinct dogfood results with materially lower human correction |
