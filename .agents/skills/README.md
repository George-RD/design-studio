# Installed Matt Pocock engineering skills

This repository contains editable, repo-owned **adaptations** of a deliberately selected engineering subset from `mattpocock/skills`:

- `setup-matt-pocock-skills`
- `to-spec`
- `to-tickets`
- `triage`
- `implement`
- `tdd`
- `code-review`
- `codebase-design`

Source repository: `https://github.com/mattpocock/skills`
Reviewed source revision: `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`
Licence: MIT; see `LICENSE.mattpocock-skills`.

The revision above is the upstream source Design Studio reviewed; these files are **not promised to be byte-for-byte copies**. They are intentionally local and editable.

## Reproducible bootstrap

For this repository, the canonical engineering-skill bootstrap is simply the **checked-in `.agents/skills/` tree at the repository revision being worked on**. A fresh clone/checkout therefore receives the exact reviewed local adaptations; no network install or moving `latest` tag is required.

`npx skills@latest add mattpocock/skills` is useful only as an **optional upstream discovery/import aid** in a scratch/worktree when reviewing newer Matt Pocock skills. Do not use it to overwrite the checked-in set or claim reproducibility. Before adopting an upstream change:

1. record the exact upstream commit SHA being reviewed;
2. compare that revision against the current checked-in adaptation;
3. preserve the MIT notice and deliberate local differences;
4. update this reviewed-source revision only after the change is accepted and the repository checks pass.

## Local adaptation policy

The subset covers planning, issue decomposition, implementation, test-driven development, architecture vocabulary and review without importing unrelated productivity skills. Keeping the subset local prevents the engineering workflow from changing when upstream does and avoids loading unrelated skills.

Current deliberate differences from the reviewed source include:

- `setup-matt-pocock-skills` merges defaults into existing repository guidance and verifies sentinel rules survive instead of treating seed templates as overwrite sources.
- `to-spec` preserves its no-interview promise by inferring testing seams from existing conversation, code and ADR evidence; unresolved material uncertainty becomes a documented assumption.
- `to-tickets` validates and publishes a sufficiently specified ticket graph without a mandatory approval round, asks only when a material ambiguity cannot be resolved, uses immediate blocker edges, and emits the full `ready-for-agent` contract.
- `code-review` includes committed, staged, unstaged and untracked work, treats revision input as untrusted, and resolves implementation tickets back to their parent specification.
- `tdd` uses a red → green → refactor vertical-slice loop while reserving broader restructuring for separately justified work.
- `codebase-design` is a compact local adaptation of the upstream deep-module/seam vocabulary and its deepening/design-it-twice references.

Other selected files may be trimmed to the portions needed by this repository. Preserve the MIT notice, compare against upstream deliberately, and never automatically overwrite local adaptations during an update.
