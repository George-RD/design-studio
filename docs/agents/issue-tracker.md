# Issue tracker: GitHub

Issues and specs for this repository live in GitHub Issues for `George-RD/design-studio`.

## Conventions

- Publish specs as GitHub issues.
- Publish implementation work as one GitHub issue per tracer-bullet ticket.
- Put `Blocked by: #<n>` references in ticket bodies when native issue-dependency tooling is unavailable to the current agent.
- Apply the `ready-for-agent` state label to fully specified tickets when the label exists in the tracker.
- When selecting work, continue an existing open/draft implementation before choosing a new ready issue.
- If there is no ready issue, `/implement` must stop cleanly rather than invent work or reviving historical roadmap items.
- Do not treat pull requests as a feature-request/triage surface by default.
- Do not modify or close a parent spec issue when creating implementation tickets from it.

## Pull requests as a triage surface

**PRs as a request surface: no.**

## When a skill says "publish to the issue tracker"

Create a GitHub issue in this repository.

## When a skill says "fetch the relevant ticket"

Read the full issue body and comments before acting.
