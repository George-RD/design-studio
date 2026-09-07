# Invocation contract

Design Studio is a standard Agent Skill. A host may expose slash commands, buttons, or another adapter, but those surfaces only translate user input into this contract. They do not own workflow logic or design authority.

## Host requirements

A host starting Design Studio must provide the generic capabilities declared in `runtime-contract.md`: `file_io`, `shell`, and `isolated_subagents`.

Use the host's isolated-agent mechanism for Planner, VisualDirector, Builder, Evaluator and Orchestrator. Preserve the source-visibility and decision boundaries in `SKILL.md`; do not collapse roles into one shared context because a host uses a different agent API.

## Design Intent input mapping

For Studio, Review and Document requests, translate the user request and current authority evidence into one result defined by `design-intent-contract.json` and `references/design-intent.md` before lane-specific input mapping:

- `lane` and `designMode`: one of the contract's Studio, Review or Document mode pairs.
- `surface`: interactive surface kind or `paginated-artifact`.
- `visualAuthority`: current accepted visual authority, or `none` when no compatible authority exists.
- `compositionState`: current state resolved through `composition-contract.json`, not prompt order or filename.
- `systemEffect`: the requested durable effect; execution records the actual accepted effect later.
- `requiredCapabilities`: the needs declared by `modeRules[designMode].requiredCapabilities` in the Design Intent contract.
- `selectedProcedures`: the canonical installed procedure selected by that mode.
- `assumptions`, `unresolved`, and `precedenceRule`: explicit classification evidence.

Capability declarations are needs, not successful probes. Interactive modes declare `runnable_target` and `browser_automation` as well as the generic capabilities; Document modes declare `page_artifact_rendering`. Record actual availability through `probe_capabilities` and `capabilities.json`. Missing visual capability retains the `build-once-unselected` or `mechanical-review` path owned by `runtime-contract.md`; it does not turn into a missing generic prerequisite or a false success.

Apply the ranked precedence in `references/design-intent.md` before loading a lane procedure. The validated result maps to the existing `task`, `surface`, `interaction` and `evidence` router signals. Host adapters preserve this result and do not add another intent taxonomy. Use the selected lane and current stage for task signals; interaction and evidence signals add relevant methods, not another lane. Review and Document resolve without loading `workflow.yaml`. All lanes retain the shared `coreAuthorities` and loading order declared by `SKILL.md` and `method-router.json`.

## Studio input mapping

Only after Studio is selected, map host input to the workflow's named inputs before `initialise`:

- `design_intent`: the already validated result, persisted by Studio; `create` maps to internal `greenfield`, while `extend` and `overhaul` keep their mode.
- `user_prompt`: remaining request after recognized control flags are removed, including the requested extension scope.
- `existing_target`: the current local path or URL for extension, or the target supplied after `--overhaul`, when present.
- `overhaul_goals`: text supplied after `--goals`, when present.
- `budget_override`: `quick`, `standard`, `ambitious`, or explicit integer supplied after `--budget`. `workflow.yaml` owns clamping and budget semantics.
- `optional_run_id`: explicit run identifier only when resuming a known run.

Supported adapter vocabulary is `--overhaul`, `--goals`, and `--budget`. Free-form hosts may populate the same named inputs directly. An additive request inside accepted authority selects `extend` through Design Intent; no new flag or second taxonomy is needed. Map its preflight/local-direction task to `studio-extend`, then use existing build/evidence stage signals. The selected procedure resolves accepted authority from the current target and surface brief, not from an adapter-invented visual system.

## Review input mapping

Review does not execute `workflow.yaml`. It also does not load that Studio procedure. Map host input to `references/review/polish.md` as:

- `target`: local path, URL, or existing `serve.json` contract.
- `constraints`: remaining review instructions.
- `report_only`: true when `--report-only` is present or the host supplies an equivalent choice.
- `mechanical_only`: true when `--mechanical-only` is present or the host supplies an equivalent choice.

Supported adapter vocabulary is `--report-only` and `--mechanical-only`.

## Document input mapping

A quote, invoice, statement of work/SOW, proposal, discovery or architecture report, executive brief, print/PDF deliverable, or other page-based artifact routes to the Document lane instead of pretending the pages are a browser viewport. Map it as:

- `task`: `document-create` for new/redesigned artifacts or `document-review` when preserving the current page world.
- `surface`: `paginated-artifact`.
- `target`: existing document, rendered artifact, local source substrate, or downstream production target when supplied.
- `structured_content`: confirmed content/fields supplied by the user or an adjacent domain skill. Treat this as input; do not infer agreement, accounting truth or commercial terms.
- `page_size`: explicit physical page contract when supplied; otherwise A4. Letter is the next standard preset and custom sizes require physical dimensions.
- `constraints`: brand/design-system truth, document purpose, audience, required furniture, print constraints and preservation rules.
- `document_visual_contract`: optional existing `document-visual-contract.json` to preserve or extend.
- `budget_override`: requested `quick`, `standard`, `ambitious` or explicit integer, passed unchanged to `initialise` when creation is needed. The lane's evaluation plan may clamp builds through `runtime-contract.md`.
- `optional_run_id`: explicit known run identifier to resume through `resume_validate`.

A browser-based dashboard or interactive report remains Studio/Review even if it can later export PDF. Page/print intent is the differentiator under the Design Intent precedence rules.

The host probes page rendering/export as optional `page_artifact_rendering` capability for this lane. Renderer identity is operational evidence for Orchestrator/Builder only and must not enter Visual Director or Evaluator context.

## Adapter boundary

Host-specific adapters may:

- translate argument syntax into the named inputs above;
- expose convenient commands for Studio, Review or Document;
- map `isolated_subagents` and rendering/browser capabilities to native host primitives.

They must not add a second quality mode, duplicate workflow rules, weaken source isolation, make a renderer or external design skill a prerequisite, or let a renderer become visual authority. When an adapter is absent, a capable host can start the same Design Studio skill from this directory alone.
