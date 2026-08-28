---
name: code-review
description: "Review changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards and Spec. Includes current staged, unstaged, and untracked work when reviewing work in progress."
---

Two-axis review of the change set since a fixed point:

- **Standards**: does the code conform to this repo's documented coding standards?
- **Spec**: does the code faithfully implement the originating issue / spec?

Both axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings.

The issue tracker should have been provided to you. If `docs/agents/issue-tracker.md` is missing, tell the user to run `/setup-matt-pocock-skills`.

## Process

### 1. Pin the fixed point and review bundle

Whatever the user said is the fixed point (a commit SHA, branch name, tag, `main`, `HEAD~5`, etc.). If they didn't specify one, use the repository's normal integration branch when it is unambiguous; otherwise ask for the fixed point.

Resolve it first with `git rev-parse <fixed-point>`.

Build one review bundle from:

1. **Committed branch changes:** `git diff <fixed-point>...HEAD` (three-dot, against the merge-base).
2. **Current tracked WIP:** `git diff HEAD`, which adds staged and unstaged tracked changes relative to `HEAD`.
3. **Current untracked WIP:** `git ls-files --others --exclude-standard`; read each listed file as part of the review input rather than silently omitting it.
4. **Commit list:** `git log <fixed-point>..HEAD --oneline`.

Use `git status --porcelain` to determine whether WIP exists. A review is empty only when the committed diff, tracked WIP, and untracked-file list are all empty. Do not reject a WIP review merely because no new commit exists.

Avoid double-counting findings when a line appears in both the committed and working-tree material. The review target is the **current resulting work**, while the committed diff remains useful evidence for how it diverged from the fixed point.

### 2. Identify the spec source

Look for the originating spec, in this order:

1. Issue references in the commit messages (`#123`, `Closes #45`, GitLab `!67`, etc.), fetched via the workflow in `docs/agents/issue-tracker.md`.
2. A path the user passed as an argument.
3. A spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.
4. If nothing is found, ask the user where the spec is. If they say there isn't one, the **Spec** sub-agent will skip and report "no spec available".

### 3. Identify the standards sources

Anything in the repo that documents how code should be written, such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`.

On top of whatever the repo documents, the Standards axis always carries this smell baseline: Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man and Refused Bequest. Repository standards override the baseline; baseline smells are judgement calls, not hard violations.

### 4. Spawn both sub-agents in parallel

The Standards sub-agent receives the full review bundle, standards sources and smell baseline. It reports documented-standard violations separately from heuristic smells.

The Spec sub-agent receives the full review bundle and originating spec. It reports missing/partial requirements, scope creep and apparently implemented requirements whose behavior is wrong. If no spec exists, skip this axis and say so.

Both sub-agents must inspect untracked files listed in the bundle. Neither may infer that `HEAD` alone represents a WIP review.

### 5. Aggregate

Present the two reports under `## Standards` and `## Spec`. Do not merge or rerank the axes. End with counts and the worst finding within each axis.

## Why two axes

A change can pass one axis and fail the other. Keeping them separate prevents clean code from masking a wrong implementation and prevents spec fidelity from masking poor code design.
