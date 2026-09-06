# Design Intent

## Purpose

Classify each Studio, Review or Document design request once before its lane procedure executes. The Design Intent result is the host-neutral front door for lane, mode, surface, current authority, composition state, requested design-system effect, required capabilities, selected procedures, assumptions and unresolved state.

## Triggers

Load for Studio, Review and Document invocation. Host commands, buttons and free-form prompts map to the same contract; adapters do not keep a second intent taxonomy. Meta maintenance follows the existing `meta`/`method-intake` router signals, and post-acceptance codification consumes the accepted lane result. Neither is an additional design mode.

## Required context

Use the current user request, target kind, confirmed product/copy inputs, current accepted visual authority and available host capabilities. Resolve artifact authority through `composition-contract.json`; do not recreate its domains, artifact roles, provenance rules or conflict precedence here. Use capability names already declared by `workflow.yaml` and `runtime-contract.md`. Evaluation-plan downgrade policy remains owned by `runtime-contract.md`.

## Outputs and handoff

Produce one validated `design-intent-contract.json` result with these modes:

| Lane | Mode | Meaning | Initial procedure |
| --- | --- | --- | --- |
| Studio | `create` | Establish a new interactive visual world where no accepted visual authority governs the request. | `workflow.yaml` |
| Studio | `extend` | Add a surface, feature or reusable pattern inside current accepted visual authority. | `workflow.yaml` |
| Review | `polish` | Audit or improve an interactive surface while preserving its current visual world; existing unaccepted conventions may be recorded as extraction candidates. | `references/review/polish.md` |
| Studio | `overhaul` | Explicitly reopen and replace an interactive visual world while preserving settled product truth unless separately reopened. | `workflow.yaml` |
| Document | `document-create` | Create or materially redesign a paginated artifact. | `references/document/document.md` |
| Document | `document-review` | Review or locally improve a paginated artifact while preserving its current page world. | `references/document/document.md` |

`selectedProcedures` contains the mode's canonical initial procedure from the contract's `laneProcedures` list. Specialist leaves are resolved separately by `method-router.json`; external paths, path aliases and undeclared procedures are invalid handoffs.

The full execution of `extend` is delivered by issue #91. Until then this contract records the mode and routes to the existing Studio authority without implying that the later lifecycle semantics already exist.

For `extend`, request `systemEffect: preserve` when a local addition uses existing system rules; request `systemEffect: extend` when the user explicitly asks for a reusable addition to those rules. For example, a new page using accepted controls preserves the system, while a proposed reusable control pattern extends it. Neither requested effect promotes authority before acceptance under #93.

A Review result may request `systemEffect: extract` when the current implementation is evidence rather than accepted authority. The extracted conventions remain candidate and unresolved until issue #93 supplies verification, acceptance and promotion semantics.

Map the validated result to the existing `task`, `surface`, `interaction` and `evidence` signals in `method-router.json`. Return the selected procedure and matched specialist leaves without executing another lane's procedure. Issue #90 owns lane-first procedure loading; until it lands, the existing installed kernel may still load shared Studio authority, but no lane procedure executes before classification.

Apply this ranked precedence when wording is ambiguous:

1. **Paginated output:** when the primary requested artifact is a page or print/PDF deliverable, select Document. Within Document, preserve/review language selects `document-review`; otherwise select `document-create`. An interactive report with incidental PDF export remains interactive.
2. **Explicit replacement:** explicit overhaul, reinvention or replacement of an interactive visual world selects `overhaul`.
3. **Accepted-world addition:** an additive page, route, feature, component family or pattern inside accepted visual authority selects `extend`.
4. **Audit or polish only:** audit, review, fix, polish or candidate extraction language selects `polish` when the user is preserving an interactive visual world.
5. **New interactive world:** a new interactive surface with no higher-ranked rule selects `create`.

Prompt order, filename and file modification time do not break ties. Record equal-authority conflict or insufficient evidence in `unresolved` rather than silently choosing a lower-ranked interpretation.

## Authority boundary

This reference owns request classification vocabulary and precedence. `composition-contract.json` owns product, offer/copy and visual artifact authority. `runtime-contract.md` owns deterministic operations, capability downgrade and failure semantics. Lane procedures own execution after classification. `method-router.json` consumes mapped signals; it is routing data rather than another classification authority.

Design Intent records requested `systemEffect`; it does not apply durable design-system state transitions. Those lifecycle effects remain later work under #91 through #93.

## Failure behavior

Do not execute a lane procedure when required fields are missing, unexpected fields introduce a parallel taxonomy, enum values conflict, a mode disagrees with its lane/surface, selected procedures are undeclared or include another lane, or the selected precedence rule cannot justify the mode. Preserve explicit assumptions and unresolved state. Ask for authority resolution only when the ambiguity materially changes the lane, mode or durable system effect; otherwise continue with the recorded bounded assumption.

## Evaluation hooks

Use table-driven cases covering all six modes, interactive and paginated surfaces, present and absent visual authority, candidate extraction, and prompt-order variants. Validate supplied results through `validate_design_intent`. Existing Studio, Review, Document, source-blind, immutable-evidence and acceptance-owner contracts must remain green.

## Source provenance

No external method is adopted into this authority. The contract is repository-owned under ADR 0005 and issue #89. Growth Arsenal may provide compatible role-scoped artifacts through `composition-contract.json`, but its internal methods and workspace are outside this classification authority.
