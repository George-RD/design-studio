# Agent guidance

## Agent skills

### Issue tracker

GitHub Issues in `George-RD/design-studio` are the durable tracker for specs and implementation tickets. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default Matt Pocock triage vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository. Read relevant decisions under `docs/decisions/` before changing architecture; use `CONTEXT.md` if one is added later. See `docs/agents/domain.md`.

### Installed engineering skills

Repo-owned editable adaptations of selected `mattpocock/skills` engineering workflows live under `.agents/skills/`. The reviewed upstream source is commit `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`, but the checked-in repository tree is the canonical reproducible copy and contains deliberate local changes. It does not update automatically.

Do not refresh these files from an unpinned `npx skills` install. Use upstream installs only in a scratch/worktree for comparison, record the exact upstream revision, and deliberately merge accepted changes while preserving local adaptations and the MIT notice. See `.agents/skills/README.md`.
