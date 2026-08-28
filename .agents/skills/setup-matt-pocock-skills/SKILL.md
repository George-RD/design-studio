---
name: setup-matt-pocock-skills
description: "Configure this repo for the engineering skills: set up its issue tracker, triage label vocabulary, and domain doc layout. Run once before first use of the other engineering skills."
disable-model-invocation: true
---

# Setup Matt Pocock's Skills

Scaffold the per-repo configuration that the engineering skills assume:

- **Issue tracker**: where issues live
- **Triage labels**: strings used for the five canonical triage roles
- **Domain docs**: where context and ADRs live, and the consumer rules for reading them

Explore the existing repo first. Prefer GitHub when the repository is hosted on GitHub. Default to the canonical labels `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix` when triage is installed. Default to a single-context domain layout unless genuine monorepo signals exist.

Write the resulting configuration under `docs/agents/` and add/update an `## Agent skills` section in the repository's existing agent-guidance file. If no guidance file exists, choose one deliberately for the host environment rather than creating duplicate Claude- and cross-agent files.

The seed templates in this folder are the source for GitHub, GitLab, local issue tracking, triage labels and domain docs.
