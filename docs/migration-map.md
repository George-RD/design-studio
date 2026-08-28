# Portable product migration map

**Status:** authoritative issue #44 baseline  
**Governing decision:** [ADR 0002](decisions/0002-owned-method-kernel.md)  
**Baseline revision:** `492a874d0a7c935e51395d66f420608a997d9ed3` (`main`, Design Studio 1.5.0, before this map)

The machine-readable authority is [`migration-map.json`](migration-map.json). This document explains the consequences.

## Scope

No production behavior changes in this ticket. Nothing is removed, redirected to an upstream runtime, or promoted into a new runtime seam here.

The older [`benchmarks/milestone-0/ownership-inventory.json`](../benchmarks/milestone-0/ownership-inventory.json) remains frozen historical evidence from the superseded ADR 0001 direction. It is useful provenance, but it is not the current migration authority.

## Baseline findings

1. The portable product already has a natural canonical surface: `skills/design-studio/` contains the Agent Skill router, workflow, source-blind role contracts and eval contract.
2. Claude Code registration, commands and root agent stubs are adapters or compatibility bridges. They must not become a second behavior authority.
3. No current script family is product runtime, and none is classified as host-adapter support. The current `scripts/` tree is capability/benchmark research plus repository support, with the retired GitHub Models probe a delete candidate.
4. That absence is useful evidence, not a reason to promote the old harness. #46 must establish the internal runtime seam first; #49 can then physically separate shipped helpers from research machinery.
5. The frozen v1.5 workflow still contains one **current external execution branch**: when the Impeccable CLI is available, the mechanical gate runs three Impeccable JSON passes; otherwise it runs a smaller, explicitly **non-equivalent fallback**. This is **migration debt**, not the ADR 0002 target. The target-v1.6 policy remains **no external runtime dependency** for supported capability. #46, #47 and #50 must preserve the useful mechanical contract while removing environment-dependent behavior.
6. Impeccable and Emil Kowalski's skills remain pinned method-intake sources. Their candidate methods are recorded as `observe` until #47 chooses one local authority with provenance and evidence.
7. Historical benchmark receipts remain discoverable in the repository but are explicitly `shipsWithSkill: false`.
8. `references/methodology.md` is an existing legacy delete candidate. It stays until #47/#51 prove that any useful methodology is already represented by current rationale, meta and workflow authorities.

The distinction in point 5 is important: `externalRuntimeDependencyAllowed: false` in the machine-readable map is the **target-v1.6 architecture policy**, not a false claim that v1.5 has already removed the optional Impeccable branch.

## User-facing and host surfaces

| Surface | Classification | Migration meaning |
|---|---|---|
| `skills/design-studio/SKILL.md` | canonical skill | Portable entrypoint and progressive-disclosure router. |
| `skills/design-studio/workflow.yaml` | canonical skill | Lifecycle, schemas, paths, budgets, selection and acceptance. |
| `skills/design-studio/agents/*` | canonical skill | Source-blind direction and evaluation role contracts. |
| `skills/design-studio/evals/evals.json` | canonical skill | Observable behavior contract. |
| `.claude-plugin/*` | optional host adapter | Claude registration/marketplace metadata only. |
| `commands/create.md`, `commands/review.md` | compatibility bridge | Thin legacy command wrappers to canonical skill routing. |
| `agents/design-agent.md`, `agents/evaluator.md` | compatibility bridge | Thin root registration stubs to canonical skill agents. |
| `docs/index.html`, `docs/app.js` | repository-only tooling | Public repository site, not installed runtime. |
| `references/methodology.md` | delete candidate | Legacy harness methodology; delete only after its still-useful concepts are demonstrably owned elsewhere. |

Adapter contraction belongs to #52 after the portable install, runtime seam and method leaves exist. The legacy methodology can contract earlier only when its content has an explicit surviving authority.

## Script families

| Family | Classification | Decision |
|---|---|---|
| browser capability/evidence helpers | benchmark/research | Preserve as capability evidence; #46 decides whether any behavior needs a new product-runtime implementation behind the runtime seam. |
| Copilot CLI capability gate | benchmark/research | Historical execution-environment proof, not a supported runtime interface. |
| boundary benchmark + blind preference | benchmark/research | Optional comparison evidence after ADR 0002. |
| Copilot comparison generation | benchmark/research | Runs the historical comparison matrix only. |
| deadline helper | CI/dev support | Repository process helper; no installed product caller today. |
| benchmark fixture validator | CI/dev support | Protects frozen research fixtures. |
| GitHub Models probe | delete candidate | Retired path; delete only after #49/#50 confirm no active CI dependency and its permanent receipt remains. |

The important constraint is negative: the portable runtime should not be defined by moving these files into a nicer directory. #46 first defines what an installed run actually calls; later work can implement or extract only what that interface needs.

The v1.5 Impeccable branch is not one of these script families: it is workflow behavior declared by `quality-gates.md`/`workflow.yaml` that shells into an external CLI when available. It is therefore tracked separately as `currentRuntimeBranches` in the JSON map.

## Method authority map

`migration-map.json` maps current local guidance, reusable Horaxon dogfood failures and the pinned Impeccable/Emil sources by concept. The baseline uses these rules:

- **keep Design Studio local:** source-blind direction/evaluation, run integrity, immutable evidence, orchestration decisions, accepted-tree provenance and settled-world scope control;
- **observe external overlap until #47:** generic context/design guidance, deterministic source/browser checks, accessibility, hierarchy, interaction, anti-pattern critique, motion craft, divergent prototype comparison, read-only expert audit sequencing and generic design-system guidance;
- **keep visual judgement distinct from mechanical checks:** upstream detector ideas may improve evidence, but they do not become the source-blind Evaluator;
- **keep Growth Arsenal separate:** `skills/design-studio/references/copy.md` is a composition boundary, not permission to duplicate offer/copy methodology. #48 defines the neutral artifact contract.

Emil's divergent-prototype method overlaps direction exploration, not Design Studio's source-blindness or hidden assignment. Emil's read-only expert-audit method overlaps review sequencing, not Review's evidence and decision boundaries. Keeping those distinctions explicit prevents a useful upstream tactic from accidentally replacing the architecture that makes Design Studio differentiated.

`observe` is deliberate. It does not mean the local files are automatically permanent. It means #44 will not pre-empt #47 by copying, deleting or delegating methods before the authority decision has evidence.

## Horaxon and the remaining “AI” quality

The existing Horaxon dogfood record already names two reusable failure classes that directly cover the concern that a polished site can still feel generated:

- `semantic-redundancy`: labels, headings, explanatory copy or chrome repeat the same meaning, creating an over-labelled, model-like composition;
- `product-specific-metaphor`: a treatment can be polished but still be transferable to an unrelated company because its visible decisions do not grow from the product's own world.

They are grouped in the `generated-specificity-and-subtraction` concept alongside the current `review/slop.md` authority and Impeccable anti-pattern research. That preserves the problem for #47/#51 without turning it into another long universal prohibition list.

This does not make Horaxon a house style. The useful signal is the failure class: remove semantic echoes, require product-derived visual decisions, and measure whether the intervention reduces owner correction. Horaxon's specific typography, colours, survey/station metaphor or page structure remain site-specific evidence rather than reusable defaults.

The same record keeps `whole-page-responsive-composition`, `real-device-perceptibility`, `false-affordance`, `action-hierarchy-and-consistency`, `settled-world-preservation` and `cross-surface-contract-drift` attached to the concepts they inform.

## Behavior protected before contraction

Before #49, #50 or #52 deletes or relocates a surface, equivalent observable protection must remain for:

| Contract | Existing protection |
|---|---|
| source-blind role isolation | workflow invariants, role prompts, eval 3 |
| immutable iterations and append-only events | workflow invariants, evals 7 and 25 |
| precommitted unattended direction | workflow invariants, evals 8 and 26 |
| current mechanical snapshots | workflow invariants, evals 10 and 27 |
| required rendered evidence | workflow invariants, evals 5, 6 and 21 |
| Orchestrator decision authority + final acceptance | workflow invariants, runtime-integrity guidance, evals 3, 16 and 29 |
| version parity while Claude compatibility exists | eval 14 |

The Impeccable availability branch itself is **not** a behavior to preserve. Its useful capability contract is: one normalized, current mechanical snapshot with explicit detector/evidence metadata, severity/waiver semantics and no leakage into visual judgement. #46/#50 should protect that stable capability while removing “what happens depends on what external CLI is installed.”

## Downstream decisions

- **#45:** make the Agent Skill the actual canonical install/distribution surface and prove a clean install contains only required runtime assets.
- **#46:** establish the small internal runtime seam. Do not treat current capability/benchmark scripts as the seam by default; include the v1.5 Impeccable availability branch in the migration design.
- **#47:** resolve each observed external overlap into `keep-local`, `adapt-local`, `vendor-slice`, `observe` or `delete-reject`, with provenance and eval evidence.
- **#49:** after #46, separate the concrete shipped runtime helpers from benchmark/research tooling and make repository-only status true in CI triggers as well as imports/directories.
- **#50:** normalize the retained deterministic runtime behind the seam and remove the environment-dependent Impeccable/fallback capability split without a blanket language rewrite.
- **#51:** expose accepted methods as progressively disclosed leaves rather than loading the full design rulebook on every request.
- **#52:** requires `#45`, `#50` and `#51`; only then contract Claude compatibility surfaces.

This ordering avoids three second-order failures: accidentally shipping the historical research harness as the product, preserving v1.5's environment-dependent Impeccable behavior while claiming portability, or deleting useful local methods merely because an upstream project covers a similar topic.
