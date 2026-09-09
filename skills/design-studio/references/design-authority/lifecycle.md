# Accepted design-system lifecycle

## Purpose

Apply the Design Intent system effect without confusing an accepted surface with permission to change shared visual rules. `DESIGN.md` remains the portable token/guidance authority. A lifecycle receipt records a transition; it is not another design-system profile.

## Triggers

Load at accepted-surface completion, when staging a reusable system delta, or when explicitly extracting legacy conventions. Review and Document use this reference without loading Studio. Profile inspection alone does not load or execute the lifecycle.

## Required context

Use the validated Design Intent, frozen incumbent output manifest, actual final-surface acceptance and its current tree/mechanical/rendered evidence. For a mutation, also load [profile.md](profile.md), the complete staged candidate and its actual consumers. Preserve the incumbent throughout staging.

The acceptance owner is still the Orchestrator/host. A Review verdict, generated persona reaction, inferred token or successful profile validation is not system approval. Resolve missing roles or reusable intent before approval; do not infer them from file names, timestamps or prompt order.

## Outputs and handoff

### 1. Freeze and stage

At intent resolution, freeze the accepted authority and its complete output inventory, including explicit absence and generated-skill directory membership. At completion, read those outputs again. Concurrent changes block continuation; do not restore an older snapshot over someone else's work.

The runtime's logical bundle has exactly nine keys: `design`, `designDna`, `tokensCss`, `skillDesign`, `skillTokensCss`, `skillIndex`, `skillDesignDna`, `documentVisualContract`, `skillDocumentVisualContract`. Each is actual UTF-8 file content or `null` for observed absence. Map them to the resolved project `DESIGN.md`, project DNA/CSS, generated skill files and optional project/skill Document contracts. An omitted key is not proof of absence. Retain the full directory manifest separately for assets outside these declared consumers.

For `extend`, copy the incumbent into staging and apply only the proposed reusable delta. Retain established token identifiers, types, semantic roles and CSS names; an identity removal/rename needs a new replacement intent. Changed values, themes, guidance or reusable DNA rules need explicit acceptance of that delta and visual-world continuity. Rebuild all derived consumers from the staged profile rather than editing CSS independently.

For Document, `publish_document_visual_contract` may materialize the proposed v1 contract **inside staging**. This does not authorize replacing the project contract. Document-specific rules stay in that contract. Shared roles use optional `sharedTokenBindings`, for example `{"colour.roles.ink":"color.ink"}` with the corresponding role value `"{color.ink}"`. Resolve that symbolic reference from the portable profile; do not maintain a duplicate literal value or a circular DESIGN/document hash. Unshared page rules remain independently Document-owned.

### 2. Approve the exact effect

Write a separate immutable `finish/system-acceptance.json` using the `systemAcceptance` definition in [lifecycle.schema.json](lifecycle.schema.json). It binds the validated intent digest, frozen before manifest, complete candidate manifest, immutable surface-acceptance reference and evidence references. Its status is `candidate`, `rejected` or `accepted`. An accepted reusable extension additionally needs a nonblank `reusableRule` and `retainsVisualWorld: true` backed by the accepted rendered result.

Keep `finish/acceptance.json` unchanged. The profile's provenance hashes that surface receipt; placing the profile's digest back inside that receipt would create a circular dependency. The system-acceptance sidecar and final publication receipt record the before/after revisions and actual durable effect instead. The earlier extension result remains immutable surface/proposal evidence, not proof that the global delta was applied.

| Requested effect | Preconditions and accepted output | Failure / staleness |
| --- | --- | --- |
| `establish` | No incumbent system output; accepted final tree and separately accepted candidate profile/consumers. | Pending or rejected work establishes nothing. |
| `preserve` | Accepted local result; current output manifest equals the frozen approved manifest. A supplied candidate must be identical. | No global writes, revision change or invalidation. Legacy systems remain readable. |
| `extend` | Current profiled authority, explicit reusable rule and accepted continuity; complete staged delta passes parity. | Unapproved deltas stay proposals. Do not silently downgrade rejected reuse to local preserve. |
| `replace` | Accepted replacement tree and system, with incumbent retained in the journal until readback passes. | Failed staging leaves the old system authoritative; failed publication requires restoration before retry. |
| `extract` | Candidate conventions, verified source inspection covering every source token path, rendered verification and explicit system acceptance agree on the exact candidate/tree. | Inference alone stays candidate. Extraction cannot overwrite an already profiled system; use a replacement intent. |
| `none` | Local result; no changed shared output. | No global writes or staleness. |

New shared deltas against an unprofiled legacy system require explicit extraction first; do not invent an accepted portable predecessor. Interactive extraction uses Review; paginated extraction uses `document-review` with `systemEffect: extract`, source inspection and page evidence. This is not automatic migration of historical evidence.

### 3. Verify the supplied proof

Call `verify_design_system_transition` with `schemaVersion: 1`, validated `intent`, fresh `before` bundle, staged `candidate` bundle or `null`, `acceptance`, `evidence` and `approval`. The last three carry actual captured records as `{path, content}`; `evidence` is an array. The helper does not follow these paths. The host reads and verifies the real files before supplying them.

The surface receipt uses the existing final-acceptance fields: accepted status, selected tree, source snapshot/iteration ordinal, tree-manifest path, mechanical snapshot ID, rendered-receipt paths in `viewportEvidence`, and immutable snapshot integrity. Interactive work supplies `serveValidated`; Document supplies `artifactValidated` instead. Review may use its one immutable confirmed snapshot, without entering a Studio iteration loop. Any acknowledged primary findings must be exact current signatures in `acknowledgedPrimaryFindings`, not a blanket waiver.

Normalize actual measured render evidence into JSON receipts with `status: verified`, the exact `{path, sha256}` tree-manifest reference, unique ordered image references in `evidence`, and `kind: browser` or `page-artifact`. Browser receipts include measured `viewports` (`width`, `height`) for both views. Page receipts include `pageCount` and ordered `pageSizes` (`widthMm`, `heightMm`) matching all page images. The host verifies the actual images and completeness; synthesizing successful receipts is not evidence. A source-inspection receipt additionally has `kind: source-inspection`, verified status, the same tree reference, `candidateRevision`, and inspected path-to-SHA-256 `files` covering the profile's source token paths.

The helper checks the supplied proof and exact consumer parity. It does not perform filesystem writes, inspect source, render pages, judge visual continuity or replace the acceptance owner. `verified-transition` authorizes only the host's next recoverable publication step. Its actual effect remains `none` and its accepted after-revision remains the incumbent until readback passes. `unchanged` completes preserve/none without publication. Candidate, rejected, missing or invalid proof cannot enter publication.

### 4. Publish and verify readback

Before any write, the host requires exclusive output access, rechecks incumbent and stage digests and directory membership, and retains complete rollback copies plus an on-disk publication journal. A host without recoverable writes halts before replacing anything. The journal binds the transition digest, before/after logical manifests and actual guard results; retain complete path inventories and per-write recovery state alongside them.

Publish the staged set together, including both copies of linked DNA/Document rules and every generated-skill asset. Recheck actual parity, all file digests and full directory membership. Call `verify_design_system_publication` with the original frozen `request`, freshly read `observed` bundle and `{path, content}` publication journal. The journal declares `schemaVersion: 1`, `transitionDigest`, `before`, `after`, `exclusiveAccess`, `incumbentRechecked`, `stageRechecked`, `rollbackReady`, `status` and `failure`.

Only `status: published`, null failure and matching readback produce a published lifecycle receipt. Keep exclusive access through verification. On any failed write/readback or lifecycle verification, restore all incumbents and remove newly created outputs. `rolled-back` requires a concrete failure and observed restoration of the entire prior set, including absence. Incomplete recovery blocks completion and retains the journal; resume recovers it before new work. The helper verifies the supplied restoration result, not the host's filesystem recovery implementation.

Use the schema-validated receipt for acceptance/event evidence. `authorityRevisionBefore/After` are LF-normalized SHA-256 digests of the portable or legacy `DESIGN.md` (null when absent); full before/after manifests also cover independently owned page rules and consumers. Append the final effect, revisions, provenance and output digests to events only after verification. A published change emits `visual-design` invalidation tied to the old manifest; the host marks only downstream assumptions depending on it stale. Preserve, candidates, rejection and rollback invalidate nothing. Product truth and approved offer/copy remain unchanged.

## Authority boundary

Design Intent owns effect vocabulary and mode compatibility. This reference and its receipt schema own shared system transitions. The selected lane owns surface execution; `runtime-integrity.md` still owns final-surface acceptance and immutable evidence. Profile operations own token/export parity. Document owns page rules. The host owns actual capture, exclusive writes, full inventory checks and recovery; the runtime verifies supplied proof and readback through the stable operations in `runtime-contract.md`.

## Failure behavior

Fail closed on stale approval, changed incumbent/candidate, missing accepted-tree evidence, invalid source extraction, unmatched linked files or consumer drift. Preserve existing authorities and failed staging evidence. Never convert an invalid mutation into success, rewrite a completed receipt, or publish from directory existence alone.

## Evaluation hooks

`test_system_lifecycle.py` exercises all effects, exact approvals, actual supplied consumer parity, rejection and publication/restoration readback. `test_system_lifecycle_contract.py` checks schema, lane disclosure and publication gates. These are synthetic contract proofs, not live rendered dogfood or fault-injected host filesystem recovery tests. Representative end-to-end host execution remains the #97 proof boundary.

## Source provenance

Locally owned lifecycle under ADR 0005 and issue #93. No external method or runtime is incorporated.
