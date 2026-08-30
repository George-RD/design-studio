# Work selection

GitHub Issues are the only executable backlog. `ROADMAP.md` supplies product context; it does not make an item actionable.

## Selection order

1. Continue an existing open or draft implementation before starting competing work.
2. Otherwise select an open implementation issue that is explicitly `ready-for-agent` and has no open blocker.
3. If there is no ready issue, stop cleanly and report that the executable queue is empty.

Do not invent product work, reopen historical milestones, or promote research and benchmark maintenance without a bounded issue. Closed issues and historical roadmap markers are evidence, not queue entries.

Before implementation, read the selected issue's full body, comments, labels, parent specification, and blocker state as defined in `docs/agents/issue-tracker.md`.
