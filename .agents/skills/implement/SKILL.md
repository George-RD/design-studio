---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

Use `/tdd` where possible at the seams established by the source spec, ticket, ADR or existing public interface.

During implementation, run focused typechecking/static validation and the smallest relevant test files regularly. Complete each behavioral slice before starting the next.

When the implementation is complete:

1. run the full relevant validation suite once;
2. use `/code-review` against the originating ticket/spec and repository standards;
3. address every still-valid review finding;
4. rerun typechecking/static validation and the full relevant test suite after the final review fixes;
5. commit only after that final validation passes.

Do not treat a pre-review green run as evidence for code changed during review cleanup.
