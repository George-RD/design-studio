# Design Studio ↔ Growth Arsenal composition contract

`../composition-contract.json` is the normative machine-readable contract. This reference explains how an agent applies it without coupling either skill to the other.

## Boundary

Growth Arsenal owns offer, positioning, persuasion strategy and authoritative commercial copy. Design Studio owns visual direction, design implementation, rendered evaluation and accepted visual-system output. Confirmed product truth is shared project context: neither skill owns permission to rewrite facts for convenience.

Each skill remains useful alone. Design Studio does not require Growth Arsenal to plan, build, review or accept design work. Growth Arsenal does not require Design Studio to produce offer/copy work. Composition adds durable decisions; it does not add a runtime dependency.

## Neutral artifact descriptor

Before resolving authority, normalize each candidate artifact to the descriptor defined by `artifactDescriptor` in `../composition-contract.json`:

- required: `path`, `role`, `scope`, `state`;
- optional: `producer`, `provenance`.

The physical serialization may be artifact frontmatter, a sidecar manifest or another durable machine-readable record. The semantic envelope does not vary: a candidate missing any required descriptor field is not authoritative. `provenance` should carry the approval, acceptance or explicit user designation required by that role.

## Identify artifacts by role, not filename

Resolve project artifacts in this order:

1. declared composition role and project scope;
2. explicit approval/acceptance provenance;
3. canonical location under the current project context root.

Prompt order, file modification time and basename alone never establish authority. A `DESIGN.md` inside Growth Arsenal can describe Growth Arsenal's own report presentation and is not therefore the project's accepted visual system. Likewise, an arbitrary `COPY.md` is not automatically an approved commercial-copy artifact.

Compatible project roles are:

- **product-truth** — normally `PRODUCT.md`, state `confirmed`;
- **audience-context** — shared researched or confirmed audience facts, in `PRODUCT.md` or an optional `AUDIENCE.md`; state `confirmed` or evidence-backed `approved`;
- **offer-copy** — normally `OFFER.md` or `COPY.md`, state `approved`;
- **visual-design** — normally `DESIGN.md`, state `accepted`.

Explicit user designation may establish or replace role/scope/state. When two artifacts still claim the same role with equal authority, mark that decision unresolved rather than choosing the later prompt or file.

## Precedence

For decisions that cross domains, apply:

1. explicit current user instruction;
2. confirmed product truth and pinned brand commitments;
3. confirmed or researched audience context, with hypotheses and simulations kept separate;
4. approved Growth Arsenal offer/copy authority, when present;
5. the current surface brief;
6. active Design Studio visual authority: accepted `DESIGN.md` for preserve-world work, or the selected direction for greenfield/redesign work.

This is not a license for a higher-ranked domain to absorb the methods of a lower-ranked one. Product truth can invalidate a claim, but Design Studio does not become the offer strategist. Approved copy can constrain composition, but Growth Arsenal does not become the visual evaluator.

## Conflict and staleness behavior

- **Copy contradicts product truth:** product truth wins. Mark the affected copy stale/unresolved and return it to Growth Arsenal or the user; never rewrite facts to fit copy.
- **Audience evidence changes:** mark dependent offer/copy and visual assumptions stale, preserving unrelated product facts and independent accepted system rules. Audience claims that contradict confirmed product truth remain stale or unresolved for the user.
- **Product truth changes:** invalidate dependent claims and visual assumptions, not unrelated artifacts. Revalidate downstream work before acceptance.
- **Approved copy changes:** invalidate surface briefs/layout assumptions that depended on superseded wording. The accepted visual system remains authoritative unless the user explicitly reopens it.
- **Copy does not fit the chosen composition:** Design Studio may change layout within its visual authority, but it must not silently truncate or weaken strategic copy. If both domains cannot be satisfied, return the trade-off to the copy authority or user.
- **Design and copy disagree about the solution:** Growth Arsenal owns wording/claims; Design Studio owns visual expression. If no compatible solution exists, the user resolves the cross-domain trade-off.
- **Accepted visual system changes:** invalidate dependent visual assumptions only after a verified system-publication receipt records the new revision and old manifest. Candidate, staged, preserve, none, rejected and rolled-back transitions invalidate nothing. Product truth and approved offer/copy remain intact.

A newly profiled system is accepted only with its verified lifecycle publication provenance, not merely a profile that points to accepted surface evidence. Historical accepted systems retain their original provenance; candidate stage directories never acquire project authority from their filenames.

A stale artifact may remain useful evidence, but it is not current authority until re-approved or re-accepted.

## Design Studio consumption rule

When planning discovers a compatible approved external offer/copy artifact, add the `composition-artifacts` evidence signal. The method router loads the local copy boundary; that boundary consumes this contract and the approved artifact.

Design Studio does not invoke, copy or reimplement Growth Arsenal methods. It reads the outputs needed for the design task: confirmed audience/business constraints, approved positioning/claims/copy, qualifications and unresolved decisions. Strategic copy changes hand back to Growth Arsenal or the user.

When no Growth Arsenal artifact exists, Design Studio continues with confirmed product truth, repository/user copy and its local surface-copy coordination rules. That fallback does not pretend to provide Growth Arsenal's offer or persuasion methodology.

## Growth Arsenal handoff expectation

A compatible Growth Arsenal export must normalize to the shared descriptor: project scope, `offer-copy` role, `approved` state and enough provenance to establish approval. The export may use frontmatter, a sidecar manifest or another durable machine-readable record, but consumers resolve the normalized descriptor rather than a Growth-Arsenal-specific prompt or implementation detail.

Growth Arsenal is not expected to reproduce Design Studio's source-blind direction generation, implementation orchestration, browser evaluation or accepted design-system codification. Its adoption work is tracked in `George-RD/growth-arsenal#34`.

## Website readiness through Design Intent

For website create, extend, polish or overhaul, normalize the relevant artifacts and attach `composition` to the Design Intent before visual direction. Use `compositionReadiness` in the normative contract for its fields, accepted evidence kinds and dependency requirements. `validate_design_intent` derives `composition.readiness`; its aggregate state must agree with `compositionState`. A supplied receipt is checked against recomputation, not trusted as an approval flag. Older intents without this field remain valid classification records but do not prove website readiness.

The input names the current `project`, whether this request is `strategySensitive`, Growth Arsenal availability (`available`, `absent` or host `unavailable`), and `artifacts`. The readiness profile uses the existing descriptor's `provenance`: a matching project, immutable role-scoped revision, evidence records `{kind, ref}`, and source dependencies `{facet, path, revision}`. A revision identifies the relevant accepted source contents, not file modification time. Normalize only evidence the host has inspected and verified. The helper validates the supplied snapshot; it cannot authenticate research, inspect a user conversation, or discover omitted contradictions. Record a discovered contradiction as stale/unresolved before validation.

Readiness classifies five facets: product truth, audience context, offer/positioning, commercial copy and accepted visual authority. Each is `ready`, `missing`, `stale`, `conflicting` or `not-applicable`, with its owner, source revision, reasons and next public action. Overall precedence is conflicting, then stale, then missing. No applicable facets yields not-applicable. Required unresolved facets block dependent direction; unrelated confirmed-input work can continue with an explicitly bounded scope.

Use `strategySensitive: false` only when the requested work does not depend on unresolved strategy or commercial copy, such as a local layout repair preserving existing wording. It is not a shortcut for a missing website brief. An existing accepted design system still requires current visual authority. Document requests retain their separate page workflow and do not carry this website preflight.

Approved offer/copy must declare which facets it covers in `provenance.facets`; approval of positioning does not imply approved commercial copy. Record the required product/audience dependencies for the offer and product/audience/offer dependencies for commercial copy. One approved export may cover both facets; its copy can reference the offer facet at the same path and revision. That internal handoff is not a dependency cycle. Other cycles, missing sources, changed revisions and unresolved sources make dependent authority stale. Candidate or staged visual systems cannot supersede accepted authority.

Two equally authoritative candidates stay conflicting. An optional `designations` entry names an exact facet, path and revision with current `user-designation` evidence. A missing designated revision does not fall back to whichever file was read next. Designation does not repair stale dependencies or replace approval evidence.

Ready inputs produce no handoff. Missing/stale audience or offer/copy may record a request to the public `growth-arsenal` identity when available; conflicts return to the user. With an absent or unavailable skill, request explicitly confirmed/approved supplied inputs and retain unresolved state. This operation never invokes a skill, reads its internals, runs its methods, or claims strategy authority. Public handoff execution and continuation are separate orchestration work under #95.

## Audience normalization

Use the `audience-context` role for project-scoped audience evidence from any compatible producer. Normalize existing `PRODUCT.md` Users and situation content with its actual confirmation or research references; a section path and sidecar provenance are sufficient. Do not require another file or invent missing evidence. A compatible adjacent export uses the same role, scope, state and provenance, not its producer's internal persona schema.

Each `provenance.audience` entry carries category, text, kind, confidence and evidence. Categories cover facts, situations, jobs, motivations, objections, decision criteria and vocabulary. Research-backed and explicitly confirmed entries become factual input only with matching evidence. Hypotheses, simulated reactions and unverified claims remain separate. An approved persona document cannot upgrade a simulation to a fact; separate research or explicit user confirmation must support that claim.

The receipt exposes these groups and unresolved categories. Role readiness means usable factual evidence exists, not that every audience question has been answered. Keep material unanswered questions in the surface brief; never fill them from simulation. Feed factual entries into shared planning context and keep persona reactions as review evidence, outside confirmed product truth. Revalidate dependent offer/copy when the audience revision changes.

## Host neutrality

This contract refers only to durable artifacts, roles, state and provenance. It does not require Claude commands, plugin ordering, a shared process, a specific agent host or one repository invoking code from the other.
