# ADR 0003: Keep Claude Code as an adapter and defer the public CLI

- **Status:** Accepted
- **Decision date:** 2026-08-29
- **Owners:** Design Studio maintainers

## Context

Design Studio now ships a canonical portable Agent Skill under `skills/design-studio/` and a stable internal runtime contract. Root Claude Code commands, agent discovery files and plugin metadata still provide useful host integration, but historical evolution left some workflow guidance duplicated between those adapter files and the canonical skill.

A standalone Design Studio CLI has also been discussed. There is not yet evidence that a separate human-facing command surface solves a problem the Agent Skill and its shipped scripts cannot solve cleanly. Building one now would create another public interface and another place for design or runtime logic to drift.

The tested adapter-versus-canonical classification remains recorded in `benchmarks/milestone-0/OWNERSHIP_INVENTORY.md` and `benchmarks/milestone-0/ownership-inventory.json`. This decision does not re-derive that inventory.

## Decision

Claude Code remains supported as an **optional, thin adapter** over the canonical Agent Skill. The adapter may own host discovery metadata, argument translation and the mapping from Claude Code's `Agent` tool to the skill's isolated-subagent capability. It does not own design methods, quality policy, workflow transitions, deterministic operations or failure semantics.

The supported capability lives in the installed Agent Skill. Removing or not installing the root `commands/`, `agents/` and `.claude-plugin/` surfaces does not reduce supported Design Studio capability on a capable host.

No standalone Design Studio CLI is built or published by this work.

## Internal runtime seam

The public host adapters and any future CLI must wrap the same canonical contract rather than introduce a second runtime:

- `skills/design-studio/SKILL.md` owns lifecycle, routing, role boundaries and acceptance authority;
- `skills/design-studio/workflow.yaml` owns Studio lifecycle and transitions;
- `skills/design-studio/references/runtime-integrity.md` owns operational evidence, recovery and acceptance facts;
- `skills/design-studio/runtime-contract.md` defines deterministic operations exposed to the skill.

Host-specific integration may translate invocation into this seam. It may not duplicate or reinterpret the seam's product logic.

## Claude adapter policy

Root Claude Code surfaces are compatibility adapters only:

- `.claude-plugin/` owns Claude plugin discovery and marketplace metadata;
- `commands/` maps Claude command arguments to canonical Studio or Review inputs and delegates to the canonical entrypoint;
- `agents/` contains discovery stubs that point at canonical prompts in `skills/design-studio/agents/`.

Substantive instructions belong in the canonical skill or a routed reference. Compatibility tests protect this boundary without making Claude-specific behavior a requirement for the portable skill.

## CLI adoption policy

A public CLI becomes justified only when evidence shows at least one of these conditions:

1. Design Studio has a stable human-facing command API that users repeatedly need independently of an agent host.
2. A repeated cross-host need exists that skill scripts cannot satisfy cleanly through the current Agent Skill contract.

Convenience alone is not enough. Before adding a CLI, the proposed interface must show that it reduces integration cost or enables a durable workflow that current hosts cannot provide.

Any future CLI must wrap the same internal runtime seam and **own no business or design logic**. It may expose stable operations, but the Agent Skill remains the authority for design method, routing, evidence and acceptance behavior.

## Consequences

### Positive

- Design Studio has one capability authority regardless of host.
- Claude Code remains convenient without becoming a second product surface.
- Removing the plugin cannot silently remove supported design behavior.
- A future CLI has explicit evidence triggers and cannot become a parallel runtime.

### Costs and risks

- Claude-specific conveniences must stay deliberately small even when richer command-local guidance would be easy to add.
- Adapter compatibility tests add maintenance whenever canonical entrypoint paths change.
- Deferring a CLI means some non-agent integrations may remain less convenient until repeated demand proves the need.

## Alternatives rejected

### Make the Claude plugin the canonical install

Rejected because it couples supported capability to one host and conflicts with the portable Agent Skill distribution contract.

### Remove Claude Code support entirely

Rejected because a thin adapter provides useful discovery and invocation convenience without requiring a second method or runtime authority.

### Build a standalone CLI now

Rejected because there is no demonstrated stable command API or repeated cross-host gap that the Agent Skill cannot satisfy cleanly.

## Revisit triggers

Revisit this decision when either CLI adoption trigger is demonstrated with repeated usage evidence, or when a host integration cannot express the canonical skill/runtime contract without adding duplicated product logic.
