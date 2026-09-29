# Jakub Krehel method intake

Date: 29 September 2026. Governing specification: [#113](https://github.com/George-RD/design-studio/issues/113).

This is a research and work-planning record, not installed method authority. The ratified decision is to run bounded experiments under the existing intake policy. No candidate below has passed its adoption gate.

## Reviewed sources

Initial reviewed baseline: `a82b9270d6a3d2c40431abcc6ad46a9feacdd3b3`. The intake PR also incorporates current main `62c71eef8d8c7284e09cf989d7d67fbd4667bf76`, preserving its later meaningful-label rules and tests; the existing intake-related documents are unchanged between those revisions.

Upstream: https://github.com/jakubkrehel/skills at `267330e1adfc66a718fb65fa6918c1f06d0a689e`. Licence: MIT, Copyright (c) 2026 Jakub Krehel. Reviewed `skills/break/SKILL.md`, `skills/interface-review/SKILL.md`, `skills/better-interface/SKILL.md`, `skills/variant/SKILL.md`, `skills/explain-interface/SKILL.md`, `skills/better-ui/SKILL.md` and `LICENSE`.

The source registry records this revision as `observe`. No upstream code or method prose is copied or adopted. Later adoption must record the exact method-sized modification and retain applicable attribution.

## Candidate dispositions

Paths below are relative to `skills/design-studio/`. They identify existing owners, not additional authorities.

| Candidate | Existing owner | Disposition and next evidence |
| --- | --- | --- |
| Reproducible component stress evidence | `references/review/interaction.md` for state/affordance, `references/review/hierarchy.md` for responsive composition, and `references/quality-gates.md` for measured geometry | Observe. [#114](https://github.com/George-RD/design-studio/issues/114) tests an applicable scenario plan, actual component reuse, adverse cases and healthy controls. |
| Change-aware review and causal attribution | `references/review/polish.md` | Observe. [#115](https://github.com/George-RD/design-studio/issues/115) tests base/head scope, affected consumers, regressions, equivalent replacements and uncertain attribution. |
| One primary axis for a local comparison | `references/extend.md` | Observe. [#116](https://github.com/George-RD/design-studio/issues/116) tests a concrete local question within accepted authority; create/overhaul divergence stays unchanged. |
| Mechanism-first reference analysis and evidence tiers | Existing implementation/evidence boundaries | Observe only. No separate implementation ticket without a demonstrated gap. |

The experiment uses the existing router-selected lenses: the source-aware producer supplies component scenarios; interaction and hierarchy reviewers interpret their respective rendered states; mechanical measurements do not substitute for either visual judgement. This record adds no second lens-selection rule.

The useful hypothesis is more reproducible evidence and narrower decisions, not a new orchestration system. Existing state coverage, realistic-context comparisons, source-blind evaluation and bounded fixes already cover much of the source material.

## Rejected imports

Do not import the upstream command taxonomy, parallel severity/decision authorities, universal numeric motion/style prescriptions, or optional rendered verification. These conflict with or duplicate existing Design Studio boundaries.

Two adaptations need particular care: an untouched component can regress through a changed shared token, and a change with no new defects is not necessarily a surface ready for final acceptance. A narrow container is also not an actual narrow viewport.

## First experiment: capability result

A scenario plan was written before harness construction. It is retained in [component-stress-plan.json](./component-stress-plan.json): ordinary content, long title, unbreakable title, empty/loading/error states, a narrow container, and a separate narrow viewport. Inapplicable axes have reasons. These are planned inputs, not inspected outcomes.

The environment had Playwright and Chromium `144.0.7559.96`. Browser preflight was blocked before the component fixture was built or rendered:

- Navigation to a locally served preview returned `net::ERR_BLOCKED_BY_ADMINISTRATOR`.
- Navigation to a minimal local HTML file returned the same policy error.

Browser policy was not changed. No screenshot, component finding, healthy-control result or behavioral red/green result was obtained. The experiment remains **unverified**. The same failure is not evidence against the proposed method; it prevents ratification in this environment.

Full Git checkout also failed because `github.com` could not resolve in the container. The edited source registry and companion were reconstructed from GitHub reads and checked against their original Git blob SHAs before modification. Local document checks are not presented as full-repository CI.

## Handoff and boundaries

Execute #114 first in a capable environment. It must observe seeded failures and healthy controls, distinguish viewport and container cases, preserve source isolation and retain inspectable evidence. A synthetic geometry result can establish that bounded fixture's behavior; it cannot prove autonomous visual quality or reduced human intervention.

Only a passing, reviewed experiment can promote a method into the relevant installed owner and machine-readable adoption records. Prefer a conditional addition to an existing owner over another leaf. Preserve read-only Review, mechanical evidence, final-tree acceptance and the current installed loading graph.

#115 and #116 remain separate experiments, not automatic follow-on adoptions. #96 remains an editorial pruning task, not a vehicle for introducing these methods. The unrelated audience-composition PR #111 and the v1.8 release graph are unchanged.
