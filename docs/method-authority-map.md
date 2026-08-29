# Method authority map

Issue #47 turns the migration inventory into the concept-level authority record for Design Studio. The machine-readable source of truth is [`docs/method-authority-map.json`](./method-authority-map.json); this file is the maintainer view.

## Boundary

- **Design Studio — design engineering:** generic visual-design methods and specialist review guidance.
- **Design Studio — orchestration/runtime:** lifecycle, role isolation, evidence, routing, resume, acceptance, and runtime behaviour.
- **Growth Arsenal — offer/copy:** offer, positioning, persuasion strategy, and authoritative copy. Design Studio consumes approved artifacts through `skills/design-studio/references/copy.md`; it does not become a second copy authority.

No upstream repository is required at runtime. Impeccable and Emil Kowalski's skills are pinned research inputs only. Design Studio does not wholesale-fork either source.

## Provenance pins

`docs/method-sources.json` is canonical for source metadata. External overlap entries reference a `sourceId` rather than duplicating mutable provenance fields in multiple files.

| Source | Exact reviewed revision | Licence | Runtime role |
| --- | --- | --- | --- |
| https://github.com/pbakaus/impeccable | `63b04e2530f5c7b41ea83c133daab24f34912456` | Apache-2.0 | Research input only; no runtime dependency |
| https://github.com/emilkowalski/skills | `d23d7f88a2e21c9e4b1418c7abe420f5c1052ba7` | MIT | Research input only; no runtime dependency |

`adapt-local` and `vendor-slice` mean **candidate**, not already adopted. A later implementation PR must cite the source ID and exact revision, describe modifications, preserve required notices when source material is copied, and protect the retained benefit with evidence or tests. `observe` and `reject` authorize no copying and create no runtime dependency.

## Canonical concept authorities

| Concept | Domain | Single authority | Routing |
| --- | --- | --- | --- |
| `source-blind-direction-and-evaluation` | design engineering | `references/rationale.md` | When generating or evaluating competing directions without source identity |
| `runtime-integrity-and-immutable-evidence` | orchestration/runtime | `references/runtime-integrity.md` | Always |
| `product-context-and-planning` | design engineering | `references/context.md` | Always |
| `implementation-fidelity` | design engineering | `references/generation.md` | Accepted direction → implementation |
| `mechanical-source-and-browser-evidence` | orchestration/runtime | `references/quality-gates.md` | Source/browser evidence collection and re-checks |
| `review-orchestration` | orchestration/runtime | `references/review/polish.md` | Iteration and final design review |
| `accessibility-review` | design engineering | `references/review/a11y.md` | Accessibility-relevant UI or evidence |
| `hierarchy-rhythm-and-responsive-composition` | design engineering | `references/review/hierarchy.md` | Hierarchy/layout/breakpoint review |
| `interaction-state-and-affordance` | design engineering | `references/review/interaction.md` | Interaction/state review |
| `motion-craft-and-perceptibility` | design engineering | `references/review/interaction.md` | Motion is added, changed, or reviewed |
| `generated-specificity-and-subtraction` | design engineering | `references/review/slop.md` | Generated UI feels generic/repetitive/over-produced |
| `design-system-codification` | design engineering | `assets/design-system-skill/SKILL.md.template` | Accepted visual world needs reusable codification |
| `offer-copy-authority` | copy/offer | **Growth Arsenal**; local boundary is `references/copy.md` | Compose only from approved copy/offer artifacts |
| `overhaul-scope-and-settled-world` | orchestration/runtime | `references/overhaul.md` | Explicit overhaul/reinvention or evidence requires reopening the visual world |
| `visual-evaluation-contract` | orchestration/runtime | `references/evaluation.md` | Always for rendered decisions and final acceptance |

Paths in this table are relative to `skills/design-studio/` unless otherwise stated. Supporting references are deliberately not additional authorities; they implement role prompts, handoffs, or adjacent lifecycle behaviour around the one concept owner.

## External overlap decisions

The migration map exposed the overlaps; #47 resolves them without importing another system.

### Adapt locally — candidates

- **Divergent prototypes in realistic context** — Emil `skills/prototype/SKILL.md`. Retain the divergence criterion, but keep Design Studio's source-blind role split, evidence contract, and routing.
- **Deterministic source/browser checks with explicit finding severity** — Impeccable `.agent/skills/impeccable/reference/audit.md`. Implement only repeatable local checks that can be tested; issue #50 is the intended runtime follow-up.
- **Read-only audit → executable improvement plan** — Emil `skills/improve-animations/SKILL.md`. Retain the handoff shape while the evaluator stays source-blind/read-only and the orchestrator keeps decision ownership.
- **Motion purpose/frequency gate, bounded values/interruptibility, and rejected-opportunity evidence** — Emil `skills/improve-animations/SKILL.md` and `skills/animate/SKILL.md`. Route only for motion work; upstream preferences are heuristics, not universal laws.
- **Useful anti-pattern categories** — Impeccable `.agent/skills/impeccable/SKILL.md`. Admit only categories that correspond to recurring local evidence; do not import its command framework or full prompt text.

### Observe

Impeccable's accessibility, hierarchy/responsive, interaction-state, generic motion, and design-system/token guidance stay pinned comparison sources. Design Studio already has local authorities for these concepts, and current evidence does not justify another maintained rule set.

### Reject as authority

- Impeccable's lifecycle/design-command taxonomy does not replace Design Studio's local phase/routing model.
- Impeccable's broad review command taxonomy does not become a parallel routing framework.
- Its mechanical-versus-visual separation does not become a second authority because Design Studio already owns that boundary in `quality-gates.md` and `evaluation.md`.

## Duplicate retirement

`references/methodology.md` is now a legacy aggregate, not a method authority. Delete it after issues #48 and #51 migrate remaining supported references/routing and a clean-install validation shows that no runtime path depends on it. The retained authorities are enumerated in the JSON map so deletion cannot silently remove the only copy of a concept.

## Future intake and comparison

There is no broad comparison or dogfood gate attached to #47. `targetedComparisons` is intentionally empty because the current overlaps can be classified from existing evidence and the pinned source review.

If a future observed method is proposed for adoption, add one comparison request naming: one concept, one unresolved question, and the evidence required to decide it. Do not reopen general Impeccable-versus-Design-Studio benchmarking by default.
