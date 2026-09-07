# Method authority map

Issue #47 defined the concept-level ownership record. Issue #51 realizes that record as a progressively disclosed local kernel. The machine-readable authorities remain in [`docs/method-authority-map.json`](./method-authority-map.json); shipped signal routing lives in `skills/design-studio/method-router.json`.

## Lane-first activation

ADR 0005 and issue #90 refine activation without changing method ownership. `design-intent-contract.json` selects the single lane procedure before it is loaded. The universal `coreAuthorities` retain input mapping, classification, source/evidence, context, recovery, degradation and acceptance guards. Studio's full `workflow.yaml` is conditional on a Studio intent; Review and Document do not load it.

Matched task/surface/interaction/evidence signals disclose specialist methods. Visual evaluation remains mandatory when making rendered decisions, but its role prompt is loaded at the relevant stage rather than at every activation. A matched route may name the same procedure as Design Intent; it may not choose a competing lane.

The [activated-context budget](./activated-context-budget.md) names the universal hot path and representative branch bounds. It is repository validation metadata, not another installed loading graph. No specialist leaf or existing Studio lifecycle step was removed to meet that budget.

## Boundary

- **Design Studio — design engineering:** generic visual-design methods and specialist review guidance.
- **Design Studio — orchestration/runtime:** lifecycle, role isolation, evidence, routing, resume, acceptance and supported runtime behaviour.
- **Growth Arsenal — offer/copy:** offer, positioning, persuasion strategy and authoritative copy. Design Studio consumes approved artifacts through its copy boundary; it does not become a second copy authority.

No upstream repository is required at runtime. Pinned external repositories are provenance/research inputs, not execution dependencies.

## Provenance pins

| Source | Exact reviewed revision | Licence | Runtime role |
| --- | --- | --- | --- |
| https://github.com/pbakaus/impeccable | `63b04e2530f5c7b41ea83c133daab24f34912456` | Apache-2.0 | Research/provenance only; selected methods are re-expressed in local leaves |
| https://github.com/emilkowalski/skills | `d23d7f88a2e21c9e4b1418c7abe420f5c1052ba7` | MIT | Research/provenance only; selected methods are re-expressed in local leaves |

| https://github.com/google-labs-code/design.md | `9bf8eae67128b6cc55ad9bf86665767deb4c11cd` | Apache-2.0 | Layered token/prose format inspiration only; no upstream code or prose copied |

`docs/method-sources.json` owns source metadata. Repository-level `currentDisposition: observe` means an upstream project is not promoted wholesale. Concept-level entries decide the smallest useful method slice.

For `adapt-local`/`vendor-slice`, `implementationStatus: candidate` means selected but not shipped; `adopted` means a focused implementation has recorded exact provenance/modifications and protects the benefit with tests or evidence. `observe` and `reject` authorize no copying.

## Canonical concept authorities

| Concept | Single authority | Routing |
| --- | --- | --- |
| source-blind direction/evaluation | `references/rationale.md` with role prompts | direction/evaluation signals |
| runtime integrity/evidence | `references/runtime-integrity.md` | always |
| product context/planning | `references/context.md` | always |
| implementation fidelity | `references/generation.md` | build/refine |
| mechanical evidence | `references/quality-gates.md` | evidence signals |
| review orchestration | `references/review/polish.md` | Review |
| accessibility | `references/review/a11y.md` | Review lens |
| hierarchy/rhythm/responsive | `references/review/hierarchy.md` | Review lens |
| interaction/state | `references/review/interaction.md` | interaction signals |
| motion craft | `references/review/interaction.md` | motion signals |
| generated specificity/subtraction | `references/review/slop.md` | Review core |
| design-system codification | `assets/design-system-skill/SKILL.md.template` | accepted system |
| offer/copy authority | **Growth Arsenal**; local boundary `references/copy.md` | composition |
| accepted-world extension | `references/extend.md` | extend preflight/local direction/completion |
| overhaul scope | `references/overhaul.md` | redesign/reopen |
| visual evaluation | `agents/evaluator.md` | rendered decisions |

`method-router.json` maps task/surface/interaction/evidence signals to these authorities. It is not another source of design rules.

## Adopted local method slices

Issue #51 adopts only the seven #47 `adapt-local` candidates:

- Emil: materially divergent alternatives compared in realistic context → `references/rationale.md`.
- Impeccable: repeatable technical audit/finding semantics → `references/quality-gates.md`; the supported implementation is Design Studio's local mechanical runtime.
- Emil: read-only expert audit → executable improvement plan handoff → `references/review/polish.md`.
- Emil: motion purpose/frequency gate → `references/review/interaction.md`.
- Emil: bounded motion timing/interruptibility heuristics → `references/review/interaction.md`.
- Emil: concise evidence for rejected motion opportunities → `references/review/interaction.md`.
- Impeccable: useful recurring anti-pattern categories → `references/review/slop.md`.

Each adopted leaf contains the exact source ID, revision, licence and local modification boundary. No upstream command framework, prompt library, picker/prototype harness, CLI, or animation toolchain is imported.

## Observe and reject

Impeccable accessibility, hierarchy/responsive, interaction, generic motion and design-system guidance remain comparison-only because Design Studio already has local authorities. Impeccable lifecycle/review command taxonomies remain rejected as parallel routing systems. External mechanical-versus-visual separation is also rejected as a second authority because Design Studio already owns that boundary.

## Duplicate retirement

The installed compatibility stubs `references/planning.md`, `references/evaluation.md` and `references/iteration.md` were removed by #51 after callers were routed to their real authorities.

Top-level `references/methodology.md` was removed by #53 after #48 completed composition migration and clean-install validation confirmed no supported runtime path required it. The machine-readable `delete-after` record is retained as the historical disposition that authorized the contraction.

## Future intake

Do not reopen broad upstream comparisons by default. A proposed method names one reusable gap, one current authority, the smallest coherent source slice, exact revision/licence, the local modification boundary, and evidence that would justify its cost. If the evidence is absent, observe rather than adopt.

## Additive portable authority

Issue #92 keeps codification under its existing concept owner and discloses `references/design-authority/profile.md` only for accepted codification, parity checks or explicit legacy migration. The local JSON-front-matter profile is embedded in `DESIGN.md`, not a new competing canonical file. Token/CSS/generated-skill parity is deterministic; DNA and document-specific rules remain linked concerns. Legacy unprofiled evidence stays readable. Lifecycle transitions and deletion of redundant authority claims remain #93.
