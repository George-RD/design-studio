# ADR 0005: Route Design Intent before lane work and compose website strategy through public artifacts

- **Status:** Accepted
- **Decision date:** 2026-08-30
- **Owners:** Design Studio maintainers
- **Governing spec:** [#88](https://github.com/George-RD/design-studio/issues/88)
- **Implementation baseline:** verified v1.7 head `d6614f81e6d487ba2f20bca0aff7fe7e5c3d3e3c`, frozen at `release/v1.7.0`
- **Publication ordering:** [#98](https://github.com/George-RD/design-studio/issues/98) depends on [#78](https://github.com/George-RD/design-studio/issues/78); v1.8 cannot publish before parked v1.7 publication closes
- **Relationship:** Refines ADR 0002. It does not supersede ADR 0002, ADR 0003, or ADR 0004.

## Context

Design Studio v1.7 owns one portable method kernel and already supports Studio, Review, and Document work. It also has a neutral artifact contract with Growth Arsenal and can codify accepted visual work into durable design-system outputs.

Repository-owned v1.7 work was merged and exact-head verified at `d6614f81e6d487ba2f20bca0aff7fe7e5c3d3e3c`. The `release/v1.7.0` branch freezes that product baseline. Issues #77 and #78 now contain only external repository metadata, tag, GitHub Release, and final acceptance publication that require a publication-capable environment.

The remaining product failure class sits at the front door:

- users still choose design workflows through prompt wording rather than one explicit intent contract;
- adding a page inside an accepted visual world can enter the same divergent exploration used for a new visual world;
- Review and Document can encounter Studio lifecycle guidance before their lane is selected;
- website work often stacks Growth Arsenal and Design Studio manually, which can repeat audience discovery, reopen settled strategy, or make prompt order affect the result;
- accepted design-system outputs exist, but establish, preserve, extend, replace, extract, and no-effect transitions are not one explicit lifecycle.

The architecture review identified one high-leverage seam: decide intent and authority once, then route lane work, adjacent-skill composition, and design-system effects from that decision.

## Decision

### Separate implementation readiness from release publication

v1.8 implementation may proceed from the frozen, verified v1.7 baseline while #77 and #78 remain parked as `ready-for-human`. This avoids treating unavailable GitHub publication operations as technical prerequisites for unrelated product work.

Release order remains strict at the publication boundary. #98 depends on #78, so the `v1.8.0` tag and GitHub Release cannot overtake `v1.7.0`. Any release-only acceptance commit on `release/v1.7.0` requires exact-head verification before tagging. Later v1.8 product commits do not rewrite the frozen v1.7 release line.

### Design Studio is the front door

Design Studio remains the single public entry point for supported design work. This phase does not create a separate Website Studio skill.

A host-neutral **Design Intent** decision is the highest stable interface. It resolves, before lane execution:

- the selected lane;
- the design mode;
- the surface kind;
- current visual authority;
- composition readiness;
- intended design-system effect;
- required capabilities and procedures;
- material assumptions or unresolved state.

Supported modes are create, extend, polish, overhaul, document-create, and document-review.

### Route before loading lane procedures

Only universal source, evidence, recovery, degradation, and acceptance guardrails may precede Design Intent resolution. Studio, Review, Document, and specialist method authorities load only after their branch is selected.

This preserves progressive disclosure after the Design Studio skill activates, not only before activation.

### Extend is distinct from create and overhaul

Extend begins from an accepted visual world. It may explore bounded alternatives inside that world, but it does not generate replacement visual directions by default.

An extend request can escalate only through explicit user intent or recorded evidence that the accepted system cannot satisfy the request. Escalation produces a new Design Intent decision rather than silently changing mode.

### Website composition uses public role-scoped artifacts

Website work resolves composition readiness before visual direction. Product truth, audience context, approved offer and copy, and accepted visual authority are selected by role, scope, state, and provenance.

Growth Arsenal remains an independent optional skill. When strategy-sensitive inputs are missing or stale and a compatible Growth Arsenal skill is available, the host requests its public workflow and consumes compatible approved artifacts. Design Studio does not invoke Growth Arsenal internals or copy its methods.

When Growth Arsenal is absent, Design Studio remains usable with explicitly confirmed inputs and reports unresolved or unverified strategy-sensitive state rather than imitating Growth Arsenal.

### Audience context is neutral authority

Audience context carries research-backed or explicitly confirmed facts that both products can use. Simulated persona reactions remain review evidence unless supported by research or confirmed by the user.

### Design-system effects are acceptance-controlled

Design Intent declares the intended durable effect: establish, preserve, extend, replace, extract, or none. Final acceptance records the actual effect.

Durable authority changes only after accepted rendered evidence. Local fixes do not become global rules by implication, failed overhaul work cannot erase incumbent authority, and extracted conventions remain candidate authority until verified and accepted.

A locally pinned portable `DESIGN.md` profile may provide machine-readable token roles plus human application guidance. Derived CSS tokens, design DNA links, generated project design-system skills, and document-specific contracts remain deterministic or linked consumers. No external format tool becomes a runtime dependency.

### Instruction pruning follows structural implementation

After routing, composition, and lifecycle behaviour settles, apply writing-for-agents to the complete installed instruction system. The skill index stays a concise router and universal guardrail layer. Branch procedures and specialist references remain behind precise pointers. Each meaning has one canonical authority.

## Consequences

### Positive

- Publication-environment limitations no longer idle safe product implementation.
- Release ordering remains explicit and testable at #98.
- Users can invoke one skill without remembering internal lanes or prompt combinations.
- Create, extend, polish, overhaul, and paginated work have explicit and testable semantics.
- Review and Document avoid unrelated Studio lifecycle context.
- Growth Arsenal can improve website strategy without becoming a Design Studio dependency or parallel design authority.
- Shared audience evidence reduces duplicate discovery while keeping simulated persona output in its proper evidence role.
- Accepted visual authority has clear lifecycle transitions and deterministic consumers.
- One Design Intent seam gives adapters, lanes, composition, and tests a common interface.

### Costs and risks

- Maintaining a frozen release branch adds a small release-management obligation until v1.7 publication completes.
- Design Intent becomes a load-bearing contract and needs representative ambiguity fixtures.
- Cross-repository composition requires coordinated public contracts and release sequencing.
- A portable design-system profile adds migration and parity obligations.
- Over-routing can become rigid if intent modes are treated as keywords instead of evidence-based decisions.
- An eager composition preflight could add work to simple requests unless strategy-sensitive branches remain explicit.
- Instruction pruning performed too early could remove behaviour that later structural tickets still need.

These costs are accepted because the prior gate confused publication capability with implementation safety, while manual routing and skill stacking already create inconsistent output and repeated human steering.

## Alternatives rejected

### Block all v1.8 implementation on v1.7 publication

Rejected because repository metadata, tag, and GitHub Release operations do not change the verified product baseline needed by #89. Preserving order at #98 gives the release guarantee without idling unrelated implementation.

### Publish v1.7 from the moving main branch later

Rejected because v1.8 implementation can change product behaviour and release evidence. `release/v1.7.0` keeps the verified v1.7 line explicit.

### Create a separate Website Studio skill

Rejected for this phase. Visual direction, implementation, rendered evaluation, and final acceptance remain Design Studio responsibilities. A second public front door would add cognitive load and another authority boundary before a distinct product need is proven.

### Merge Growth Arsenal into Design Studio

Rejected because offer, positioning, persuasion, and commercial copy are a separate domain with their own evidence and approval lifecycle. Merging would increase context load, duplicate authority, and weaken independent installation.

### Continue manual prompt stacking

Rejected because prompt order and human memory are not reliable composition interfaces.

### Keep route-after-load behaviour

Rejected because it makes progressive disclosure cosmetic after skill activation and allows unrelated lane rules to compete.

### Treat generated personas as shared truth

Rejected because simulated reactions can be useful review evidence but are not research-backed facts by default.

### Make an external DESIGN.md tool canonical

Rejected because Design Studio owns its supported runtime and design-system authority. External formats may inform a pinned local profile, but no external tool controls runtime behaviour or automatic updates.

## Revisit triggers

Revisit this decision if:

- the frozen v1.7 line cannot be published independently without product ambiguity;
- repeated dogfood shows that the six modes cannot classify supported work without frequent manual override;
- a separate website product develops distinct users, lifecycle, or acceptance authority beyond Design Studio;
- public cross-skill invocation remains unavailable across representative hosts and artifact handoff cannot provide equivalent composition;
- the portable design-system profile creates more drift or maintenance than it prevents;
- measured human steering and correction do not improve across representative create, extend, polish, overhaul, and website-composition work;
- route-first disclosure removes necessary universal context and causes repeatable recovery or safety failures.
