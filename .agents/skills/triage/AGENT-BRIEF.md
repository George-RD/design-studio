# Writing Agent Briefs

An agent brief is the durable contract for an issue moved to `ready-for-agent`.

## Principles

- Describe behavioral contracts and durable interfaces, not file paths or line numbers.
- State current and desired behavior.
- Include complete, independently verifiable acceptance criteria.
- State explicit out-of-scope boundaries.

## Template

```markdown
## Agent Brief

**Category:** bug / enhancement
**Summary:** one-line description

**Current behavior:**
What happens now.

**Desired behavior:**
What should happen when complete, including edge cases.

**Key interfaces:**
- Durable interface/type/config contract that changes

**Acceptance criteria:**
- [ ] Specific criterion
- [ ] Specific criterion

**Out of scope:**
- Adjacent work intentionally excluded
```
