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

## Preserve before scaffolding

Treat existing agent configuration as repository-owned authority, not disposable generated output.

1. Read every existing file under `docs/agents/` and the repository's existing agent-guidance file before writing.
2. Record repository-specific guidance that is not present in the seed templates, including roadmap ownership, ADR precedence, parent-spec relationships, label mappings, host constraints and local vocabulary.
3. Merge the seed/template concepts into the existing documents. **Never replace an existing document wholesale with a seed template.**
4. Prefer one canonical statement plus links over duplicating the same repository rule in generated files.
5. When an existing rule conflicts with a seed default, preserve the repository-specific rule unless it is demonstrably obsolete; surface the conflict rather than silently overwriting it.

Write/merge the resulting configuration under `docs/agents/` and add/update an `## Agent skills` section in the repository's existing agent-guidance file. If no guidance file exists, choose one deliberately for the host environment rather than creating duplicate Claude- and cross-agent files.

## Preservation validation

Before setup edits, choose at least one distinctive repository-specific sentence or rule from each existing configuration file as a **sentinel**. After editing, verify every sentinel or its deliberately equivalent replacement remains present and that all newly required setup concepts were added. A setup pass is incomplete if repository-specific guidance disappears merely because a seed file lacked it.

The seed templates in this folder provide defaults for GitHub, GitLab, local issue tracking, triage labels and domain docs. They are merge inputs, not overwrite sources.
