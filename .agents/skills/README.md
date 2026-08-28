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

## Local adaptation policy

The subset covers planning, issue decomposition, implementation, test-driven development, architecture vocabulary and review without importing unrelated productivity skills. The normal install route for a fresh repo is `npx skills@latest add mattpocock/skills`; this repository keeps a smaller pinned subset so its engineering workflow does not change when upstream does.

Current deliberate differences from the reviewed source include:

- `to-spec` preserves its no-interview promise by inferring testing seams from existing conversation, code and ADR evidence; unresolved material uncertainty becomes a documented assumption.
- `to-tickets` validates and publishes a sufficiently specified ticket graph without a mandatory approval round, asking only when a material ambiguity cannot be resolved from existing evidence.
- `code-review` includes staged, unstaged and untracked files in work-in-progress reviews instead of treating `HEAD` as the whole WIP.
- `codebase-design` is a compact local adaptation of the upstream deep-module/seam vocabulary and its deepening/design-it-twice references.

Other selected files may be trimmed to the portions needed by this repository. Preserve the MIT notice, compare against the reviewed/upgraded upstream revision deliberately, and do not automatically overwrite local adaptations during an update.
