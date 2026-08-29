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
- **offer-copy** — normally `OFFER.md` or `COPY.md`, state `approved`;
- **visual-design** — normally `DESIGN.md`, state `accepted`.

Explicit user designation may establish or replace role/scope/state. When two artifacts still claim the same role with equal authority, mark that decision unresolved rather than choosing the later prompt or file.

## Precedence

For decisions that cross domains, apply:

1. explicit current user instruction;
2. confirmed product truth and pinned brand commitments;
3. approved Growth Arsenal offer/copy authority, when present;
4. the current surface brief;
5. active Design Studio visual authority: accepted `DESIGN.md` for preserve-world work, or the selected direction for greenfield/redesign work.

This is not a license for a higher-ranked domain to absorb the methods of a lower-ranked one. Product truth can invalidate a claim, but Design Studio does not become the offer strategist. Approved copy can constrain composition, but Growth Arsenal does not become the visual evaluator.

## Conflict and staleness behavior

- **Copy contradicts product truth:** product truth wins. Mark the affected copy stale/unresolved and return it to Growth Arsenal or the user; never rewrite facts to fit copy.
- **Product truth changes:** invalidate dependent claims and visual assumptions, not unrelated artifacts. Revalidate downstream work before acceptance.
- **Approved copy changes:** invalidate surface briefs/layout assumptions that depended on superseded wording. The accepted visual system remains authoritative unless the user explicitly reopens it.
- **Copy does not fit the chosen composition:** Design Studio may change layout within its visual authority, but it must not silently truncate or weaken strategic copy. If both domains cannot be satisfied, return the trade-off to the copy authority or user.
- **Design and copy disagree about the solution:** Growth Arsenal owns wording/claims; Design Studio owns visual expression. If no compatible solution exists, the user resolves the cross-domain trade-off.
- **Accepted visual system changes:** invalidate dependent visual assumptions only. Product truth and approved offer/copy remain intact.

A stale artifact may remain useful evidence, but it is not current authority until re-approved or re-accepted.

## Design Studio consumption rule

When planning discovers a compatible approved external offer/copy artifact, add the `composition-artifacts` evidence signal. The method router loads the local copy boundary; that boundary consumes this contract and the approved artifact.

Design Studio does not invoke, copy or reimplement Growth Arsenal methods. It reads the outputs needed for the design task: confirmed audience/business constraints, approved positioning/claims/copy, qualifications and unresolved decisions. Strategic copy changes hand back to Growth Arsenal or the user.

When no Growth Arsenal artifact exists, Design Studio continues with confirmed product truth, repository/user copy and its local surface-copy coordination rules. That fallback does not pretend to provide Growth Arsenal's offer or persuasion methodology.

## Growth Arsenal handoff expectation

A compatible Growth Arsenal export must normalize to the shared descriptor: project scope, `offer-copy` role, `approved` state and enough provenance to establish approval. The export may use frontmatter, a sidecar manifest or another durable machine-readable record, but consumers resolve the normalized descriptor rather than a Growth-Arsenal-specific prompt or implementation detail.

Growth Arsenal is not expected to reproduce Design Studio's source-blind direction generation, implementation orchestration, browser evaluation or accepted design-system codification. Its adoption work is tracked in `George-RD/growth-arsenal#34`.

## Host neutrality

This contract refers only to durable artifacts, roles, state and provenance. It does not require Claude commands, plugin ordering, a shared process, a specific agent host or one repository invoking code from the other.
