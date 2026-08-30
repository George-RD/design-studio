# Matt Pocock skill updates

`skills-lock.json` defines the upstream-managed Matt Pocock skill names, source paths, and current content hashes. Each matching `.agents/skills/<name>/` directory must remain byte-for-byte upstream; `npx skills update` overwrites local edits there.

Repository guidance belongs in `AGENTS.md` and `docs/agents/`. A repository-owned skill may coexist under a name absent from `skills-lock.json`.

The lock format records GitHub source paths and content hashes, not an immutable commit reference. A clean restore reproduces the locked name/source set from current upstream and refreshes hashes if upstream changed. Review that result as a dependency update; do not describe it as a historical byte-for-byte pin.

## Restore and update

Run only in a clean dedicated worktree:

```text
npx skills@latest experimental_install
npx skills@latest update --project --yes
```

## Verified project workflow

On 2026-08-30, a clean scratch project containing only this lockfile plus sentinel repository guidance was exercised with the two commands above. `experimental_install` restored all 37 locked skills. `update --project --yes` refreshed the same 37 managed directories. Both preserved the scratch `AGENTS.md`, `docs/agents/issue-tracker.md`, `.agents/skills/README.md`, and a repository-owned skill absent from the lock. A deliberate edit inside locked `code-review` was overwritten by update, confirming the ownership boundary.

This manual networked probe is update evidence, not a CI test or immutable reproduction guarantee. `test/test_engineering_skill_management.py` separately checks the committed lock hashes, managed directories, and same-name host links without network access.

Before accepting an update:

1. preserve the pre-update status and diff;
2. compare the installed tree and lockfile against the previous revision;
3. classify differences as repository policy, generic improvement, or obsolete adaptation;
4. compose repository behavior through `AGENTS.md` or `docs/agents/`, never a locked skill directory;
5. verify repository guidance and repository-owned skills remain unchanged;
6. verify `skills/design-studio/` is unchanged;
7. run `python3 -m unittest discover -s test -p 'test_engineering_skill_management.py' -v`, applicable repository contracts, and code review.

## Setup protection

This repository is already configured. If `setup-matt-pocock-skills` is used to change tracker or domain configuration, existing `AGENTS.md` and `docs/agents/*` files are authoritative inputs. Merge the requested configuration into them; preserve repository-specific rules and one-source-of-truth links instead of replacing files from upstream seed templates.
