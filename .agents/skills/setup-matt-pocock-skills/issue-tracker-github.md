# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Use the `gh` CLI for all operations.

## Conventions

- Create/read/comment/label/close issues with `gh issue` commands.
- Infer the repo from the current git remote.
- PRs as a request surface: no, unless explicitly changed in the repo config.
- When a skill says "publish to the issue tracker", create a GitHub issue.
- When a skill says "fetch the relevant ticket", read its full body and comments.
- Prefer native issue dependencies for blocking edges; otherwise record `Blocked by: #<n>` in the issue body.
