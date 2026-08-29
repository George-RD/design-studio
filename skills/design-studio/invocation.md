# Invocation contract

Design Studio is a standard Agent Skill. A host may expose slash commands, buttons, or another adapter, but those surfaces only translate user input into this contract. They do not own workflow logic or design authority.

## Host requirements

A host starting Design Studio must provide the generic capabilities declared in `workflow.yaml`: `file_io`, `shell`, and `isolated_subagents`.

Use the host's isolated-agent mechanism for Planner, VisualDirector, Builder, Evaluator and Orchestrator. Preserve the source-visibility and decision boundaries in `SKILL.md`; do not collapse roles into one shared context because a host uses a different agent API.

## Studio input mapping

For an interactive create, build, or redesign request, map host input to the workflow's named inputs before `initialise`:

- `user_prompt`: remaining request after recognized control flags are removed.
- `existing_target`: local path or URL supplied after `--overhaul`, when present.
- `overhaul_goals`: text supplied after `--goals`, when present.
- `budget_override`: `quick`, `standard`, `ambitious`, or explicit integer supplied after `--budget`. `workflow.yaml` owns clamping and budget semantics.
- `optional_run_id`: explicit run identifier only when resuming a known run.

Supported adapter vocabulary is `--overhaul`, `--goals`, and `--budget`. Free-form hosts may populate the same named inputs directly.

Audit or polish-only language routes to Review instead of Studio unless the user explicitly asks for a redesign.

## Review input mapping

Review does not execute `workflow.yaml`. Map host input to `references/review/polish.md` as:

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
- `budget_override` and `optional_run_id`: same semantics as Studio when a create loop is required.

A browser-based dashboard or interactive report remains Studio/Review even if it can later export PDF. Page/print intent is the differentiator.

The host probes page rendering/export as optional `page_artifact_rendering` capability for this lane. Renderer identity is operational evidence for Orchestrator/Builder only and must not enter Visual Director or Evaluator context.

## Adapter boundary

Host-specific adapters may:

- translate argument syntax into the named inputs above;
- expose convenient commands for Studio, Review or Document;
- map `isolated_subagents` and rendering/browser capabilities to native host primitives.

They must not add a second quality mode, duplicate workflow rules, weaken source isolation, make a renderer or external design skill a prerequisite, or let a renderer become visual authority. When an adapter is absent, a capable host can start the same Design Studio skill from this directory alone.
