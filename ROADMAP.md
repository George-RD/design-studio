# Design Studio roadmap

## Direction

Design Studio will become a **design orchestration layer**, not another independent catalogue of frontend rules.

Its job is to choose, combine and evaluate specialist design workflows while preserving the controls that make a run trustworthy:

- the agents choosing and judging a direction remain isolated from source code;
- product truth, capabilities, costs and assumptions are recorded before work starts;
- every material attempt survives;
- mechanical evidence and visual judgement stay separate;
- one component owns the final decision;
- interrupted runs resume from validated artifacts;
- the accepted result records which upstream tools and versions produced it.

**Impeccable becomes the required base design engine.** Design Studio should install and invoke it through a narrow, versioned adapter rather than reimplementing its design guidance, detector rules or provider support.

Specialist paradigms can then be added as workflow packs. Scroll World is the first serious candidate. Growth Arsenal copy is a smaller existing candidate. Design Studio owns the composition and evidence, while each upstream project continues to own its specialist method.

The first user is George. Build around repeated real use before generalising the architecture for a broader marketplace.

## Product boundary

| Layer | Owner |
|---|---|
| Product and design guidance, deterministic frontend checks, generic design commands | Impeccable |
| Run lifecycle, role isolation, workflow selection, immutable evidence, resume, final selection and acceptance | Design Studio |
| Offer and customer-copy workflows | Growth Arsenal |
| Scroll-cinematic story, scene chain, seam method and scrub runtime | Scroll World |
| Model-specific image and video execution | Replaceable generation backends such as image generation, Veo, Higgsfield or Monid |

Design Studio should not claim upstream methods as its own. Public documentation should name the dependency and explain the division of responsibility.

## Decisions already made

- [x] Preserve the source-blind Visual Director and Evaluator model.
- [x] Preserve immutable iterations, resumable evidence and one final decision owner.
- [x] Make Impeccable a required dependency rather than maintaining a parallel design rule set.
- [x] Keep Impeccable upstream. Do not fork or vendor it unless a stable integration cannot be achieved any other way.
- [x] Pin compatible dependency versions. Do not pull an untested latest release during every run.
- [x] Prefer upstream contributions for specialist workflows. Fork only behind an explicit decision gate.
- [x] Delete duplicate logic before introducing a general plugin framework.

## Success measures

The architectural change is useful only when all of these are true:

- a clean Design Studio install also installs or resolves a compatible Impeccable version;
- a run fails early with a precise repair command when the dependency is missing or incompatible;
- Design Studio contains no second implementation of Impeccable detector rules or generic design commands;
- roots, capabilities, serving, viewport verification, event recording, resume and acceptance each have one canonical implementation;
- every run records upstream package names, versions, licenses and invoked capabilities;
- representative dogfood runs show value over invoking Impeccable alone through better direction separation, repeatability, recovery, selection or composite execution;
- adding a second workflow does not require copying its complete skill into Design Studio.

---

## Milestone 0: prove the boundary

**Goal:** establish what Design Studio uniquely contributes before refactoring around dependencies.

- [ ] Write an architecture decision record for the Impeccable dependency, attribution policy and ownership boundary.
- [ ] Freeze representative fixtures:
  - [ ] new marketing surface;
  - [ ] existing product-screen overhaul;
  - [ ] review and polish pass;
  - [ ] visually ambitious experience suitable for a later Scroll World comparison.
- [ ] Run the same fixed briefs through:
  - [ ] Impeccable alone;
  - [ ] current Design Studio;
  - [ ] current Design Studio with Impeccable enabled.
- [ ] Record output preference, task clarity, originality, functional defects, elapsed time, token/tool cost, failed steps and recovery effort.
- [ ] Inventory every Design Studio step, reference, schema and check. Label each item `core`, `impeccable`, `external-workflow`, `compatibility` or `delete`.
- [ ] Identify workflows that only reproduce an Impeccable command and mark them for delegation or removal.
- [ ] Confirm the smallest differentiated product: orchestration, source isolation, evidence, resume, selection and composition.

**Exit:** there is an evidence-backed keep/delete/delegate map. The roadmap may change if Design Studio does not add enough value over Impeccable alone.

## Milestone 1: make Impeccable the required foundation

**Target:** v1.6

- [ ] Add a dependency manifest with:
  - [ ] compatible version range;
  - [ ] recommended tested version;
  - [ ] install source;
  - [ ] required capabilities;
  - [ ] license and attribution metadata.
- [ ] Test whether supported agent plugin systems can declare transitive dependencies.
- [ ] When native dependency installation is unavailable, add one bootstrap path that installs Design Studio and Impeccable together.
- [ ] Add a `doctor` or equivalent preflight that verifies:
  - [ ] Impeccable is installed;
  - [ ] its version is supported;
  - [ ] required CLI capabilities and JSON output are available;
  - [ ] the active harness can invoke it;
  - [ ] browser requirements are independently satisfied.
- [ ] Create one Impeccable adapter. No other Design Studio file should parse raw Impeccable output or construct Impeccable commands.
- [ ] Normalise upstream results into Design Studio's evidence schema with the upstream rule ID, version and original severity retained.
- [ ] Fail closed on unknown schemas or unsupported versions. Do not silently substitute a smaller local detector.
- [ ] Record the resolved version and exact invocation in `capabilities.json` and the final report.
- [ ] Test the minimum supported, recommended and latest candidate versions before changing the compatibility range.
- [ ] Reposition the README and website:
  - [ ] “Built on Impeccable” credit with a direct link and maintainer name;
  - [ ] explain that Impeccable owns design guidance and mechanical quality;
  - [ ] explain that Design Studio owns orchestration and composite workflows;
  - [ ] keep Apache-2.0 notices and dependency provenance current.

**Exit:** a user installs Design Studio once and receives a verified Impeccable-backed setup. There is no supported full run without Impeccable.

## Milestone 2: delete duplication and simplify the core

**Target:** v1.7

Delete before abstracting.

- [ ] Remove the local fallback catalogue of generic design checks. Retain only Design Studio-specific runtime integrity checks.
- [ ] Remove duplicated anti-pattern, typography, layout, accessibility and design-system guidance now owned by Impeccable.
- [ ] Route Review work to Impeccable wherever Design Studio adds no unique orchestration or evidence.
- [ ] Reduce local `PRODUCT.md`, `DESIGN.md` and `COPY.md` handling to the fields Design Studio needs for routing, isolation and run evidence. Reuse upstream parsing where a stable interface exists.
- [ ] Delegate customer-copy rewriting to Growth Arsenal when installed; keep only the cross-workflow input/output contract in Design Studio.
- [ ] Build a call graph for `SKILL.md`, `workflow.yaml`, agent prompts and references.
- [ ] Remove dead branches left by optional-Impeccable behaviour.
- [ ] Remove unreachable transitions, obsolete schemas, superseded evals and unused artifacts.
- [ ] Merge repeated procedures for:
  - [ ] root resolution;
  - [ ] capability probing;
  - [ ] target serving and readiness;
  - [ ] viewport verification;
  - [ ] detector invocation and snapshot replacement;
  - [ ] event append and artifact validation;
  - [ ] final acceptance.
- [ ] Give every policy one authority file. Other files should link to it rather than restate it.
- [ ] Reduce always-loaded prompt content and measure the token reduction.
- [ ] Add contract tests before each deletion and preserve failure semantics.
- [ ] Run a dead-code and duplicate-content check in CI.

**Exit:** the core is materially smaller, one path owns each runtime concern, and no generic upstream capability has a second local implementation.

## Milestone 3: separate the orchestration core from workflow packs

**Target:** v1.8

Do not design a universal plugin API from theory. Use Impeccable plus one real second integration to discover the contract.

- [ ] Define the stable core around:
  - [ ] run and event lifecycle;
  - [ ] role isolation;
  - [ ] dependency and capability resolution;
  - [ ] workflow routing;
  - [ ] budget and approval gates;
  - [ ] immutable artifact registration;
  - [ ] evaluation and final acceptance;
  - [ ] provenance and reporting.
- [ ] Define a minimal workflow-pack manifest containing:
  - [ ] ID, version, source and license;
  - [ ] compatible Design Studio range;
  - [ ] required and optional capabilities;
  - [ ] accepted inputs and produced artifacts;
  - [ ] cost-bearing steps and approval points;
  - [ ] resume boundaries;
  - [ ] quality and acceptance hooks;
  - [ ] fallback and failure behaviour.
- [ ] Add a dependency lock so completed and resumed runs use the same workflow and backend versions.
- [ ] Make packs addressable through adapters rather than copied prompts or files.
- [ ] Isolate pack failure so partial artifacts remain inspectable and resumable.
- [ ] Use Growth Arsenal's copy workflow as the smaller second integration if it exposes enough real differences to test the contract.
- [ ] Keep pack discovery explicit. Do not build a public registry until several packs exist and repeated use proves the need.

**Exit:** one optional external workflow can be added, updated or removed without changing the orchestration kernel.

## Milestone 4: Scroll World integration spike

**Target:** v1.9 experimental

Scroll World currently combines several concerns in one skill: story intake, art direction, still generation, video generation, seam construction, encoding and the browser scrub runtime. The integration should preserve its method while separating backend choice from the workflow.

### 4.1 Map the existing system

- [ ] Pin and credit the upstream `oso95/scroll-world` version used for the spike.
- [ ] Map the pipeline into explicit stages:
  - [ ] product and story brief;
  - [ ] ordered scene contract;
  - [ ] still generation;
  - [ ] motion generation;
  - [ ] boundary-frame extraction and frame-locked connectors;
  - [ ] encode and mobile variants;
  - [ ] scrub runtime and page integration;
  - [ ] visual, functional and performance evaluation.
- [ ] Separate Scroll World's core invariants from provider-specific commands.
- [ ] Record which current files and prompts assume Higgsfield, Monid or a particular model.

### 4.2 Define generation backend contracts

- [ ] Define an image backend contract: prompt, references, aspect ratio, output path, cost estimate, async status and provenance.
- [ ] Define a video backend contract: start-frame support, end-frame support, duration, aspect ratio, resolution, model options, async status, cost estimate and output path.
- [ ] Make frame-lock capability explicit. A backend that cannot condition both ends cannot silently produce connector clips.
- [ ] Keep seam extraction, encoding and scrub behaviour independent of the generation provider.
- [ ] Add Veo as the first alternative video backend used by George.
- [ ] Keep Higgsfield and Monid support upstream where practical rather than reproducing their command logic in Design Studio.
- [ ] Make native mobile generation, crop fallback and cost approval explicit capabilities rather than hidden branches.

### 4.3 Upstream-first change path

- [ ] Open an upstream issue or proposal describing the provider separation with a concrete interface.
- [ ] Prefer a focused upstream PR that keeps current defaults working.
- [ ] Use a Design Studio adapter if the existing Scroll World outputs are already sufficient.
- [ ] Fork only when provider coupling blocks the required composition and the upstream project cannot or will not accept a narrow abstraction.

If a fork is required:

- [ ] preserve the MIT license and original attribution;
- [ ] document every intentional divergence;
- [ ] keep the delta limited to provider separation and required integration hooks;
- [ ] track upstream and test rebases regularly;
- [ ] avoid renaming or rewriting unrelated Scroll World concepts.

### 4.4 Compose the first cinematic workflow

- [ ] Let Impeccable establish product, brand, interface and mechanical design context.
- [ ] Let Scroll World own the cinematic scene-chain method.
- [ ] Let Design Studio decide when the cinematic paradigm is appropriate, manage budgets and approvals, preserve attempts and coordinate final evaluation.
- [ ] Evaluate the cinematic canvas and the surrounding interface together rather than accepting a strong video inside a weak page.
- [ ] Preserve a non-cinematic responsive path when motion, bandwidth, reduced-motion preference or backend capability requires it.
- [ ] Record all upstream tools, models, prompts, costs and generated asset provenance in the run report.

**Exit:** the same Scroll World workflow can use Veo or its original supported backend without changing Design Studio's orchestration logic or the seam/scroll runtime.

## Milestone 5: prove composition adds value

**Target:** v2.0

- [ ] Add routing that selects the smallest suitable workflow rather than running every installed pack.
- [ ] Support at least:
  - [ ] standard Impeccable-backed surface work;
  - [ ] overhaul of an existing surface;
  - [ ] focused review delegated to Impeccable;
  - [ ] cinematic Scroll World composition;
  - [ ] optional Growth Arsenal copy pass.
- [ ] Compare each composite workflow against its upstream tool used alone with the same brief and assets.
- [ ] Measure independent preference, task clarity, functional defects, run cost, elapsed time, failed generations, recovery and manual intervention.
- [ ] Remove any Design Studio layer that adds cost without improving quality, repeatability, recovery or decision confidence.
- [ ] Add provenance to every accepted artifact so users can trace which workflow and provider produced it.
- [ ] Publish the narrower positioning and examples only after dogfood results support the claims.

**Exit:** Design Studio can choose and combine specialist design workflows, and the evidence shows that composition is better than manually invoking the same tools in sequence.

---

## Explicit non-goals

- Rebuilding Impeccable inside Design Studio.
- Automatically following the latest dependency release without compatibility tests.
- Forking Scroll World solely to replace one CLI command when an adapter is sufficient.
- Copying complete external skills into the Design Studio repository.
- Building a public workflow marketplace before two or three real integrations prove the common contract.
- Running expensive cinematic or copy workflows for every page.
- Optimising for broad adoption before the primary dogfood workflow is reliable.

## Release sequence

| Release | Outcome |
|---|---|
| v1.6 | Required, credited and versioned Impeccable dependency |
| v1.7 | Duplicate logic removed and orchestration core simplified |
| v1.8 | Minimal external workflow-pack contract proven by a second integration |
| v1.9 | Experimental Scroll World composition with provider-neutral generation and Veo support |
| v2.0 | Evidence-backed routing and composition across specialist design workflows |
