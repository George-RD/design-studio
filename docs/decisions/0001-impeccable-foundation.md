# ADR 0001: Make Impeccable the required design foundation

- **Status:** Accepted
- **Decision date:** 2026-07-30
- **Applies from:** Design Studio v1.6
- **Owners:** Design Studio maintainers
- **Upstream:** [Impeccable](https://github.com/pbakaus/impeccable), maintained by Paul Bakaus (`pbakaus`)

## Decision contract

This record is accepted only if it answers all of the following before implementation begins:

1. Which project owns design guidance, generic commands, deterministic frontend checks and visual orchestration?
2. How is a compatible Impeccable version installed, resolved and pinned?
3. What happens when Impeccable is absent, incompatible or returns an unknown schema?
4. Where may raw Impeccable commands and output be handled?
5. How are Impeccable, its version, licence and invoked capabilities credited in public documentation and run evidence?
6. Which changes must be proposed upstream, and what evidence is required before a fork or vendored copy is allowed?
7. How does the repository move from the optional v1.5 integration without claiming that v1.6 behaviour already exists?
8. Which observations would justify revisiting this decision?

Evidence required for this ADR:

- the ownership table below has one owner for every material responsibility;
- the failure policy has no silent local substitute for a missing upstream capability;
- the attribution policy names the upstream project, maintainer, repository and Apache-2.0 licence;
- the migration section keeps current v1.5 documentation truthful until Milestone 1 exits;
- `ROADMAP.md` links to this accepted record.

## Context

Design Studio's differentiated mechanism is not a second catalogue of frontend advice. It separates source-aware implementation from source-blind direction and evaluation, preserves attempts, records evidence, resumes interrupted work and gives one orchestrator responsibility for the final decision.

Impeccable already owns a broad design method, shared commands and deterministic frontend detection. Design Studio v1.5 can invoke Impeccable, but it still permits a smaller fallback path. Maintaining both paths would create duplicated rules, inconsistent findings and an incentive to copy upstream features into this repository.

The v1.6 boundary therefore needs to be explicit before dependency work starts.

## Decision

Impeccable becomes a required, credited and versioned foundation for supported full Design Studio runs from v1.6.

Design Studio will install or resolve a compatible Impeccable release through one dependency manifest and one adapter. The adapter is the only Design Studio component permitted to construct Impeccable commands, invoke the CLI, parse raw output or translate upstream failures.

A supported full run will not continue when Impeccable is missing, incompatible, cannot expose the required capabilities or returns an unknown result schema. Preflight must stop before generation, explain the exact problem and provide a repair command. Design Studio must not silently replace missing Impeccable behaviour with a smaller local catalogue.

Mechanical findings remain evidence, not visual judgement. The source-blind Evaluator still judges the rendered result. The Orchestrator still applies budgets, eligibility rules and final selection.

## Ownership boundary

| Responsibility | Owner | Design Studio treatment |
|---|---|---|
| Product and design context format exposed by Impeccable | Impeccable | Consume through the adapter; retain only routing and evidence fields unique to Design Studio |
| Generic design guidance and anti-pattern guidance | Impeccable | Link or invoke; do not restate a parallel catalogue |
| Generic design commands such as audit, polish, critique, layout and typeset | Impeccable | Delegate unless a composite Design Studio run adds isolation, evidence or selection |
| Deterministic source and browser detector rules | Impeccable | Invoke once through the adapter and retain upstream rule identity, version and severity |
| Source-blind direction generation | Design Studio | Preserve as a distinct role and artifact boundary |
| Source-aware implementation | Design Studio | Coordinate the Builder and immutable iteration outputs |
| Source-blind live evaluation | Design Studio | Preserve as independent visual judgement |
| Run lifecycle, budgets, events, resume and artifact validation | Design Studio | Keep in the orchestration core |
| Direction assignment, candidate eligibility and final selection | Design Studio | Keep one decision owner and recorded rules |
| Workflow composition and external pack routing | Design Studio | Add through adapters after Milestone 2 removes duplicate logic |
| Customer offer and copy workflows | Growth Arsenal when installed | Keep only the cross-workflow input and output contract locally |
| Cinematic scene-chain method | Scroll World when integrated | Keep upstream; Design Studio coordinates capability, cost, evidence and acceptance |

## Dependency and compatibility policy

Milestone 1 must add a machine-readable dependency manifest containing:

- the supported version range;
- one recommended version tested by Design Studio CI;
- the installation source;
- required CLI commands, flags and JSON schemas;
- the upstream repository, licence and attribution metadata.

Completed and resumed runs must use the same resolved version. A compatibility range may change only after the minimum supported version, recommended version and latest candidate have passed the adapter contract suite.

Design Studio must not pull an untested latest release during every run.

## Adapter and evidence policy

One adapter owns all Impeccable interaction. Other skills, commands, prompts and workflow steps consume normalised Design Studio evidence only.

Normalised findings must retain at least:

- upstream package and version;
- exact invocation and target root;
- upstream rule identifier;
- original severity;
- original message and location data needed for audit;
- collection time and artifact path;
- suppression state without deleting the original finding.

`capabilities.json`, the event stream and the final acceptance report must record the resolved dependency, exact invocation and result artifact.

Unknown output shapes, unsupported versions and missing required fields fail closed. They are not treated as an empty or clean result.

## Attribution and licence policy

Public installation and architecture documentation must say that Design Studio is built on [Impeccable](https://github.com/pbakaus/impeccable), maintained by Paul Bakaus, and explain the ownership boundary in plain language.

Impeccable is licensed under Apache License 2.0. Design Studio is licensed under MIT. Design Studio does not relicense Impeccable, imply ownership of its methods or remove upstream notices.

Every distributed dependency manifest and accepted run report must retain:

- upstream name and repository;
- resolved version;
- licence identifier;
- invoked capabilities;
- a direct attribution link.

`NOTICE.md` remains the repository-level notice. It must be updated when v1.6 changes the integration from optional to required, not before the required installation path is working.

## Upstream, vendoring and fork policy

Design Studio will prefer public upstream interfaces and focused upstream contributions.

Vendoring or forking Impeccable is allowed only when all of these are documented:

1. a required stable integration cannot be achieved through the published package, CLI or an accepted upstream change;
2. the exact blocker and attempted upstream path are recorded;
3. the fork preserves Apache-2.0 obligations and attribution;
4. the delta is limited to the integration blocker;
5. an update and rebase test plan exists;
6. maintainers accept the ongoing security and compatibility cost.

A fork is not justified by convenience, naming preference or a desire to copy the command surface into Design Studio.

## Migration from v1.5

The current v1.5 release remains accurately documented as optional until Milestone 1 meets its exit criteria.

Migration order:

1. freeze comparative fixtures and establish the keep, delete and delegate map;
2. add the dependency manifest and compatibility tests;
3. add one installation or bootstrap path;
4. add doctor and adapter contracts;
5. remove the fallback only after supported environments receive a precise repair path;
6. update README, website and `NOTICE.md` to required-foundation wording;
7. release v1.6 only after installation, invocation, evidence and failure-path tests pass.

There is no supported half-state in which documentation says Impeccable is required while a normal run silently uses local fallback behaviour.

## Consequences

### Positive

- Design Studio can focus on orchestration, isolation, evidence, recovery, selection and composition.
- Generic design rules and commands have one upstream authority.
- Findings retain provenance and can be reproduced against a pinned version.
- Improvements in Impeccable can arrive through a narrow compatibility boundary instead of copied guidance.

### Costs and risks

- A full run gains an external dependency and can be blocked by an incompatible release.
- CI must test multiple supported versions and unknown-schema failure paths.
- Installation UX must work across supported agent harnesses that may not support transitive plugin dependencies.
- Upstream availability and maintenance become explicit operational risks.

These costs are accepted because a smaller local substitute would weaken quality while recreating the maintenance burden this boundary is intended to remove.

## Revisit and rollback triggers

Revisit this ADR if evidence from Milestone 0 shows that Design Studio adds no material value over Impeccable alone, or if a stable adapter cannot support the required capabilities without a large fork.

A rollback may restore an earlier Design Studio release, but must not introduce an undocumented generic fallback under the v1.6 contract. Any replacement foundation requires a new ADR, comparative evidence and a migration plan.

## Alternatives rejected

### Keep Impeccable optional indefinitely

Rejected because supported runs would continue to have two quality paths with different coverage and evidence.

### Copy Impeccable guidance and detector rules into Design Studio

Rejected because it duplicates ownership, increases drift and obscures credit.

### Vendor or fork immediately

Rejected because the published package and CLI must first be tested through a narrow adapter and upstream change path.

### Remove mechanical checks and rely only on visual evaluation

Rejected because deterministic findings and source-blind judgement answer different questions and should remain separate evidence layers.
