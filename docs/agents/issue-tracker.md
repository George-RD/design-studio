# Issue tracker: GitHub

GitHub Issues in `George-RD/design-studio` are the authoritative executable backlog. Publish durable specs and implementation tickets there; `ROADMAP.md` only maps product state and frontier.

## Publishing

- Publish each specification as one issue.
- Publish implementation work as one issue per tracer-bullet ticket.
- Apply `ready-for-agent` only when the contract in `docs/agents/planning.md` is complete.
- Do not treat pull requests as a feature-request or triage surface by default.
- Do not close or rewrite a parent specification when deriving implementation tickets.

## Relationships

- Put the governing specification in each implementation ticket's `Parent` section.
- Prefer native GitHub sub-issue and blocking relationships when the available tooling supports them.
- Otherwise put `Blocked by: #<n>` references in the ticket body.
- Record only immediate blockers; transitive blockers are derived from the graph.

## Reading work

- Read an issue's full body, comments, labels, and open blockers before acting.
- When an implementation ticket names a parent, follow that relationship to the governing specification.
- For specification review, use both the parent specification and the implementation ticket: the parent owns product requirements; the child owns slice-specific acceptance criteria.

Work selection is defined once in `docs/agents/work-selection.md`.
