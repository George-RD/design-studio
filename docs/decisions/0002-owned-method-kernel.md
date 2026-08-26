# ADR 0002: Design Studio owns its method kernel

- **Status:** Accepted
- **Decision date:** 2026-08-26
- **Supersedes:** ADR 0001
- **Owners:** Design Studio maintainers

## Context

ADR 0001 proposed Impeccable as a required external foundation with Design Studio acting mainly as an orchestration layer. That removed duplicate rules, but it also made the product boundary depend on another project's command surface, release decisions and information architecture.

Dogfood on Horaxon showed a different opportunity. The strongest outcomes came from combining several kinds of expertise:

- Design Studio's source-blind direction and evaluation;
- deterministic checks and anti-pattern research from Impeccable;
- Emil Kowalski's motion restraint, precise interaction craft and divergent prototype methods;
- Growth Arsenal's offer and copy framing;
- repeated owner feedback about meaning, subtraction, responsive composition, action hierarchy and product-specific metaphor.

The useful product is therefore not a switch between “Design Studio alone” and “Design Studio with Impeccable.” It is one coherent agentic design method that selectively learns from strong external systems, preserves attribution, and turns repeated dogfood corrections into better workflow and evaluation.

## Decision

Design Studio will have **one supported Design Studio runtime** and one locally owned, curated method kernel.

**No upstream project is a required runtime foundation.** A supported run must not change quality, workflow or available checks because Impeccable, Emil's skills or another research source happens to be installed. There is no supported “with” and “without” mode.

External systems are pinned research inputs. Design Studio may:

1. study a method at an exact revision;
2. adapt the smallest useful principle or procedure into its own progressive-disclosure structure;
3. vendor a narrowly bounded executable slice when local execution is genuinely required;
4. reject or continue observing material that does not improve outcomes enough to justify its cost.

A wholesale clone is not the default. It imports another project's architecture, prompt volume, terminology and maintenance burden before Design Studio has proved which parts matter. Cloning a repository into a research workspace is acceptable; distributing a fork or large vendored copy requires a separate evidence-backed decision.

## Product boundary

Design Studio owns the full supported design workflow:

| Layer | Design Studio responsibility |
|---|---|
| Product truth | Capture audience, business outcome, constraints, proof, current state and settled decisions before visual work begins. |
| Direction | Generate genuinely different named directions without source anchoring and state the axis, governing metaphor and trade-off of each. |
| Method routing | Load only the specialist method leaves needed for the task through progressive disclosure. |
| Implementation | Build the selected direction against real product constraints while preserving required behaviour. |
| Mechanical evidence | Run a stable local set of deterministic checks whose value and maintenance cost are justified. |
| Visual judgement | Evaluate rendered output source-blind at whole-page and target-viewport level. |
| Selection | Keep one recorded decision owner, immutable attempts and explicit acceptance evidence. |
| Learning | Convert repeated owner corrections into candidate workflow interventions and evals through an owner-feedback learning loop. |

Upstream projects own their original repositories and methods. Design Studio must credit sources but does not delegate its runtime authority to them.

## Method-kernel shape

The kernel is not one giant always-loaded prompt. It is a small authority layer plus routed leaves.

### Always loaded

Only information required to protect the run:

- role and source-visibility boundaries;
- artifact and event lifecycle;
- product truth and settled-decision precedence;
- direction selection and iteration rules;
- required evidence and final acceptance authority;
- method routing rules.

### Loaded by task

Specialist leaves may cover:

- marketing and conversion surfaces;
- operational product screens;
- review and subtraction;
- responsive composition;
- motion opportunity, implementation and review;
- interaction and affordance honesty;
- accessibility;
- copy coordination;
- design-system extraction;
- cinematic or other specialist paradigms.

Each leaf must have one purpose, explicit triggers, bounded outputs and a clear handoff. Duplicate principles belong in one authority file and are linked elsewhere.

## External method intake

The machine-readable source registry is [`docs/method-sources.json`](../method-sources.json). Every source record includes an exact revision, licence, attribution, relevant methods and current disposition.

A method may enter the kernel only when all of these are true:

1. A reusable failure class or missing capability is named before the source is copied.
2. The smallest coherent method is identified; unrelated source material is excluded.
3. The method fits the local role boundaries and progressive-disclosure model.
4. Licence and attribution obligations are recorded.
5. Any modification from the source is explicit.
6. An eval, contract test or dogfood comparison protects the claimed benefit.
7. The method improves output, reduces human correction, improves recovery or makes a decision more trustworthy.

Otherwise the method remains an observed research input.

Permitted dispositions are:

- **reject** — not useful or too costly;
- **observe** — promising, but evidence is insufficient;
- **adapt-local** — translate the method into Design Studio's own structure and language;
- **vendor-slice** — retain a pinned executable subset with notices and a deliberate update policy.

## Upstream maintenance policy

Design Studio performs **periodic source review**, not automatic synchronization.

At least quarterly, and whenever dogfood exposes a gap or a major upstream release lands:

1. compare the pinned revision with upstream changes;
2. shortlist only changes relevant to known failure classes or roadmap capabilities;
3. assess benefit, overlap, prompt cost, implementation cost and licence impact;
4. test candidates in isolation or against a frozen dogfood case;
5. adopt, reject or continue observing them explicitly;
6. update the source registry and provenance only after evidence is accepted.

Design Studio must not silently pull latest guidance into a run. A source update is a product change and receives the same review as local workflow changes.

## Dogfood and owner-feedback learning loop

The first user remains George, and repeated real feedback is a primary design-research input.

After a material dogfood iteration:

1. preserve the raw owner comment, prior output and accepted correction;
2. classify the correction as a local preference, one-off defect or reusable failure class;
3. locate the missed workflow decision or evaluation question;
4. propose the smallest intervention: context field, routing rule, review question, deterministic check or eval;
5. require a second example, or one severe outcome failure, before making a new always-on gate;
6. measure whether the intervention reduces feedback rounds or rework;
7. remove interventions that add prompt volume without improving results.

The initial Horaxon analysis is recorded in [`docs/research/horaxon-feedback-patterns.json`](../research/horaxon-feedback-patterns.json).

This loop must not encode Horaxon's Traverse visual language as the default. It extracts failure classes such as semantic repetition, false affordance, weak product specificity and page-level mobile rhythm while leaving each product free to develop its own visual world.

## Mechanical checks

Deterministic checks remain valuable, but they are not the product's design authority.

Design Studio will retain or implement a check only when:

- it catches a repeatable defect with acceptable false positives;
- the finding can be explained and tested;
- ownership is clear;
- maintaining it locally is cheaper than the rework it prevents;
- it does not pretend to replace rendered visual judgement.

A useful check or algorithm from Impeccable may be adapted or narrowly vendored with Apache-2.0 obligations preserved. Design Studio does not need the entire Impeccable command system to keep one proven check.

## Attribution and licensing

Selective ownership does not erase origin.

For copied or substantially adapted material, Design Studio must retain the source name, repository, exact revision, licence and required notices. Modified files must identify material changes where the licence requires it.

Current reviewed sources include:

- Impeccable, Apache-2.0;
- Emil Kowalski's skills, MIT.

Public documentation should explain that Design Studio learns from and credits specialist work without implying that those projects endorse or maintain Design Studio.

## Treatment of existing Milestone 0 work

The frozen fixtures, lane harness, immutable evidence and blind preference transaction remain useful research infrastructure.

The old three-lane comparison is no longer a release gate for a required Impeccable dependency. It may be run selectively when it answers a specific method-intake question, such as whether one adapted check or review procedure adds value. Do not spend twelve paid runs merely to complete a superseded architecture milestone.

Future comparisons should prefer:

- kernel revision A versus kernel revision B;
- an ablation with and without one candidate method;
- first-pass acceptance and number of owner corrections;
- page-level defects, task clarity, originality, elapsed cost and recovery;
- whether a change reduces human steering without narrowing outputs into one house style.

## Migration

1. Stop Milestone 1 work that would make Impeccable a runtime dependency.
2. Preserve ADR 0001 and its inventory as historical evidence; this ADR is authoritative from now on.
3. Reclassify the ownership inventory into local keep, adapt, vendor-slice, observe and delete decisions.
4. Establish a concise local method index and route specialist leaves through progressive disclosure.
5. Extract the highest-leverage Horaxon feedback patterns into workflow interventions and evals.
6. Remove runtime branches whose only purpose is handling Impeccable availability.
7. Keep source provenance and licence notices for every adopted method.
8. Validate the first owned-kernel release through real dogfood and measured human-correction reduction.

## Consequences

### Positive

- Users receive one predictable product rather than environment-dependent design quality.
- Design Studio can combine the best parts of several systems without inheriting all of any one system.
- Progressive disclosure controls prompt size and keeps specialist knowledge task-specific.
- Dogfood feedback becomes durable product learning rather than disappearing into PR history.
- Upstream inspiration remains available without automatic drift.

### Costs and risks

- Design Studio owns more maintenance and must avoid recreating large upstream catalogues without evidence.
- Selective adaptation requires disciplined provenance and licence handling.
- Local curation can become subjective or stale if periodic review and dogfood measurement are skipped.
- Excessive feedback codification can overfit to George or Horaxon and reduce creative range.
- A coherent kernel takes more editorial judgement than wiring together every available skill.

These costs are accepted because Design Studio's intended value is the coherent method and learning loop, not dependency management.

## Alternatives rejected

### Keep Impeccable as a required runtime foundation

Rejected because it makes Design Studio's supported behaviour depend on another project's architecture and creates pressure to shape the product around an adapter rather than around observed outcomes.

### Keep optional with/without modes

Rejected because two supported quality paths make evidence, documentation and user expectations inconsistent.

### Fork or vendor all of Impeccable now

Rejected as the default because it imports substantial unrelated scope and maintenance before the useful slices are known. A narrow vendored slice remains available when evidence justifies it.

### Copy useful prompts ad hoc

Rejected because untracked copying loses provenance, duplicates authority and makes later updates impossible to reason about.

### Ignore upstream systems and invent everything locally

Rejected because specialist projects contain tested expertise. The goal is disciplined intake, not isolation.

## Revisit triggers

Revisit this decision if:

- a narrow external runtime dependency consistently outperforms local ownership with materially lower maintenance;
- the source registry and intake process become more expensive than a well-bounded fork;
- dogfood shows that the kernel is overfitted and cannot produce distinct product worlds;
- human correction does not decrease across several representative projects;
- licence obligations prevent a required method from being distributed safely.
