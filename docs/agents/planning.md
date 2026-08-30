# Planning composition

Apply these repository-owned rules in addition to upstream `to-spec`, `to-tickets`, and `tdd`.

Resolve the current conversation, governing issues and comments, accepted ADRs, and existing interfaces before asking a question. Infer the highest stable test seam supported by that evidence and record material uncertainty as an assumption. Ask only when unresolved choices would produce materially different public contracts.

When the user has already requested a specification or ticket set and the source evidence is sufficient, publish it without an additional approval interview.

A `ready-for-agent` ticket must state:

- current and desired observable behavior;
- the durable interface or seam affected;
- independently verifiable acceptance criteria;
- explicit out-of-scope boundaries;
- immediate blockers.

Use `docs/agents/issue-tracker.md` for parent and blocker relationships.

The upstream TDD workflow already requires red/green vertical tracer-bullet slices and defers broader refactoring to review. Do not maintain a repository fork merely to rename that loop.
