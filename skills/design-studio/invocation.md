# Invocation contract

Design Studio is a standard Agent Skill. A host may expose slash commands, buttons, or another adapter, but those surfaces only translate user input into this contract. They do not own workflow logic or design authority.

## Host requirements

A host starting Design Studio must provide the generic capabilities declared in `workflow.yaml`: `file_io`, `shell`, and `isolated_subagents`.

Use the host's own isolated-agent mechanism to instantiate the roles named by the workflow: Planner, VisualDirector, Builder, Evaluator, and Orchestrator. Preserve the source-visibility and decision boundaries in `SKILL.md` and `workflow.yaml`; do not collapse the roles into one shared context merely because the host uses a different agent API.

## Studio input mapping

For a create, build, or redesign request, map host input to the workflow's named inputs before `initialise`:

- `user_prompt`: the remaining user request after recognized control flags are removed.
- `existing_target`: the local path or URL supplied after `--overhaul`, when present.
- `overhaul_goals`: the text supplied after `--goals`, when present.
- `budget_override`: `quick`, `standard`, `ambitious`, or an explicit integer supplied after `--budget`. `workflow.yaml` owns clamping and budget semantics.
- `optional_run_id`: an explicit run identifier only when the user or calling host is resuming a known run.

Supported adapter vocabulary is `--overhaul`, `--goals`, and `--budget`. Free-form hosts do not need to expose those exact flags; they may populate the same named inputs directly from structured UI or conversation state.

Audit or polish-only language routes to the Review lane instead of Studio unless the user explicitly asks for a redesign.

## Review input mapping

Review does not execute `workflow.yaml`. Map host input to `references/review/polish.md` as:

- `target`: local path, URL, or existing `serve.json` contract.
- `constraints`: remaining review instructions.
- `report_only`: true when `--report-only` is present or the host supplies the equivalent structured choice.
- `mechanical_only`: true when `--mechanical-only` is present or the host supplies the equivalent structured choice.

Supported adapter vocabulary is `--report-only` and `--mechanical-only`.

## Adapter boundary

Host-specific adapters may:

- translate their argument syntax into the named inputs above;
- expose convenient commands for Studio or Review;
- map `isolated_subagents` to the host's native agent-spawn primitive.

They must not add a second quality mode, duplicate the workflow rules, weaken source isolation, or make an external design skill a prerequisite. When an adapter is absent, a capable host can still start the same Design Studio skill from this directory alone.
