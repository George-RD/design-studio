# Extend an accepted visual world

## Purpose

Add a page, route, component family, feature or interaction pattern within current accepted visual authority. Extend is a Studio mode, not a fourth lane or a reduced-quality create run.

## Triggers

After Design Intent selects `designMode: extend`, use `studio-extend` for preflight and local direction work. Load this leaf with `workflow.yaml`; do not add `studio-direction`, `studio-pivot` or `studio-overhaul` signals. Later build and mechanical stages use their existing routes.

A paginated variant remains Document under Design Intent's page-first precedence. It uses `document-create` with the existing document visual contract and a preserving/extending effect, not this interactive workflow.

## Required context

Use the validated Design Intent, current surface brief and accepted `DESIGN.md` with its linked authority and acceptance provenance. Confirm project scope and currency; a filename, source convention or inferred token is not evidence of acceptance. Missing, stale or conflicting authority blocks this path until resolved; it does not authorize a new visual world.

Before building, Orchestrator freezes a manifest of the existing `DESIGN.md`, design DNA, tokens, generated design-system skill and linked authority files. Record content digests, relative paths and absent outputs, including the complete generated-skill directory listing. Resolve paths from roots/accepted links, not assumed working directories. Keep copies in run evidence for diagnosis; never repair concurrent authority changes by overwriting them. The manifest records each path as file (SHA-256 content digest), directory (complete sorted membership, with child entries) or absent (null digest and empty membership). Its revision is tied to the accepted authority, not a fresh unverified timestamp. Recheck completed manifests before resuming and before publication.

Orchestrator projects the accepted system into source-free `extensionVisualConstraints`: visual thesis, semantic token roles and relationships, component/control grammar, responsive logic and anti-goals. Include current baseline renders and the local surface's purpose. Strip selectors, code, implementation metadata and proposed solution details. Only source-aware roles receive the raw authority files or manifest; Director and Evaluator receive the bounded visual constraints and permitted rendered evidence.

## Outputs and handoff

### Preflight and local direction

Record the requested scope, authority provenance and `systemEffect` in `extensionScope`. One candidate is normal. When a concrete local question needs comparison, record that question before allowing two or three equally specified alternatives inside the same visual world. Candidate IDs are neutral; no new thesis, typography voice or global control grammar may be introduced by implication.

`prepare_direction_assignment` records `extend-bounded`. For one candidate use index 1; for multiple candidates choose by user answer or an unattended index precommitted within the candidate count. Hide seed/index from Director. `explore_extension` replaces the divergent exploration step, then rejoins selection, direct, build, mechanical evidence, evaluation and final-tree acceptance. A local selected direction is subordinate to accepted authority, never its replacement.

### Surface acceptance and durable authority

A local addition requests `systemEffect: preserve`. A reusable rule requests `systemEffect: extend` only when explicitly in scope. Both use the normal immutable iteration, mechanical, rendered and final-tree acceptance gates. Each evaluated iteration writes `extensionConstraintEvidence` as pass, fail or unverified with evidence and violations. Only pass iterations enter final selection; with none available, halt without a winner. Fresh finish/correction evidence must cover the actual final tree. Acceptance also checks the frozen authority manifest, directory membership/absent outputs, and that implementation plus rendered evidence respect the inherited token roles and grammar. An unresolved material constraint breach rejects the extension even at an exhausted iteration budget.

After accepted proof, `complete_extension` rechecks authority at its entry guard and publishes the accepted surface only. Its `outputsFrom` binding resolves the accepted effect against `modePolicies.extend.completion`; preserve never requires or emits a delta artifact. Write `extensionResult` with before/after authority evidence and the actual surface result:

- **Preserve:** `status: accepted`, `systemEffect: preserve`, `publicationState: unchanged`, `proposedSystemDelta: null`.
- **Reusable addition:** `status: accepted`, `systemEffect: extend`, `publicationState: proposed-only`, and a `proposedSystemDelta` whose status is `proposed`. Record the incumbent revision, reusable rule, rationale, accepted-tree receipt and evidence. This is an accepted surface plus a proposal, not a new accepted design-system revision.
- **Rejected surface:** `status: rejected`, `systemEffect: none`, no proposed delta or published surface. Retain rejection and actual authority observations; never overwrite concurrent changes to restore a stale manifest.

For an early halt without complete authority observations, `authorityUnchanged` is null rather than a fabricated true; do not emit accepted or proposed output.

No branch writes `DESIGN.md`, design DNA, canonical tokens or the generated project skill. A rejected reusable proposal cannot be silently published as a global rule; a separately accepted local addition may finish as preserve only after a new intent/acceptance decision records that scope change. Issue #93 owns applying and verifying reusable deltas across durable consumers.

### Escalation

When the user explicitly reopens the world, or evidence identifies a required outcome that cannot be met under a named accepted constraint, Orchestrator runs `escalate_extension`. Record the exact request or incompatibility evidence, the original intent and a **new validated Design Intent** in `extensionEscalation`. Keep the original run, mode and incumbent system intact. A missing candidate, low originality score, exhausted budget or Builder preference is not incompatibility evidence.

Use overhaul for replacement within the governed project. Create is appropriate only when the new intent records a separately scoped world without governing visual authority. Do not relabel accepted project authority as absent to pass validation. The extension terminates halted with `extensionResult.status: escalated`, `systemEffect: none`, null acceptance/delta and the next-intent handoff. The next run, not an in-place mode flip, owns any replacement exploration. This gate is available before building and after rendered evaluation; Evaluator supplies evidence, never the escalation decision.

## Authority boundary

This leaf owns extension preservation, local alternatives and its bounded handoff. `workflow.yaml` owns paths, schemas, budgets and transitions. `references/context.md` owns authority precedence; `references/runtime-integrity.md` owns immutable evidence and final-tree proof. Builder follows `references/generation.md`. Portable token profiles and applying reusable system deltas remain separate lifecycle work; extension does not redefine token authority or import another skill's methods.

## Failure behavior

Preserve the accepted world when a local candidate is rejected. Missing browser evidence follows the existing one-build unselected halt; it cannot establish visual or system acceptance. Source leakage invalidates the affected blind-role evidence. A missing authority, changed authority digest or absent accepted provenance halts rather than silently creating or replacing a system.

## Evaluation hooks

Evaluate the rendered addition against product purpose and inherited visual constraints, including existing surrounding surfaces and desktop/mobile controls. Keep source, raw design-system files, full design description, assignment, effort and prior scores out of Evaluator context. Low originality is not permission to replace an accepted world. Local alternatives must solve the requested problem while retaining the thesis and grammar.
