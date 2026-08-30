# Code review composition

Apply these repository-owned rules in addition to upstream `code-review`.

Review the current resulting work, not only committed `HEAD` state:

1. Treat a supplied revision as untrusted input. Pass Git arguments as an argument array, resolve the revision to a commit before use, and never evaluate or interpolate it through a shell command string.
2. Include the merge-base committed diff, staged and unstaged tracked changes, every non-ignored untracked file, full commit messages, and relevant pull-request context.
3. Consider a review empty only when committed, tracked-worktree, and untracked inputs are all empty. Deduplicate findings that appear in more than one input.
4. Resolve the governing specification through `docs/agents/issue-tracker.md`. Give the Spec review both the parent specification and implementation ticket.

Use the upstream Standards and Spec axes after assembling that bundle.
