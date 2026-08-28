---
name: to-tickets
description: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker (edges as text in one file per ticket locally, or native blocking links on a real tracker).
disable-model-invocation: true
---

# To Tickets

Break a plan, spec, or conversation into a set of **tickets**: tracer-bullet vertical slices, each declaring the tickets that **block** it.

The issue tracker and triage label vocabulary should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes a reference as an argument, fetch it and read its full body and comments. If the source is an issue, follow its declared parent/spec relation and use the designated parent specification as the durable product contract.

### 2. Explore the codebase

Understand the current state, use project vocabulary, respect ADRs, and look for opportunities to **refactor** the code to make implementation easier without turning refactoring into a horizontal ticket.

### 3. Draft vertical slices

Each slice should cut a narrow but complete path through the relevant layers, be independently verifiable, and fit in one fresh context window. Give each ticket only its **immediate** blocking edges; do not repeat transitive blockers. Use expand-contract for wide refactors that cannot stay green as one vertical slice.

For each slice, resolve enough current implementation context to state the current behavior, desired behavior, durable interface/seam affected, acceptance criteria and explicit out-of-scope boundary. Do not use `ready-for-agent` as a substitute for this contract.

### 4. Validate the graph

Review the proposed titles, delivered behavior and blocker edges against the source spec and current codebase. Prefer the smallest graph that covers the required behavior without horizontal layer tickets, duplicate scope or redundant transitive dependencies.

When the user has already asked for tickets and the source material is sufficient, publish without an additional approval round. Ask only when a material ambiguity cannot be resolved from the spec, ADRs, codebase or current conversation; otherwise record assumptions in the affected ticket.

### 5. Publish tickets

For a real issue tracker, publish one issue per ticket in dependency order so blockers can reference real identifiers. Apply `ready-for-agent` only when the complete template below is populated with concrete project-specific content. If native blocking links are unavailable, record `Blocked by: #<n>` references in the body.

Do NOT close or modify any parent issue.

<issue-template>

## Parent

A reference to the parent issue on the tracker (if the source was an existing issue, otherwise omit this section).

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective, not layer-by-layer implementation.

## Current behavior

What happens now that makes this slice necessary. Cite durable concepts or interfaces rather than brittle file/line locations.

## Desired behavior

What should happen when this ticket is complete, including important edge/failure behavior.

## Key interfaces

- The durable public/runtime/artifact/configuration seam whose behavior changes or becomes protected.
- Include authority/precedence contracts when the slice crosses skill or host boundaries.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Out of scope

- Adjacent work intentionally excluded from this slice.

## Blocked by

- A reference to each **immediate** blocking ticket, or "None (can start immediately)".

</issue-template>

Avoid specific file paths or code snippets because they go stale quickly.
