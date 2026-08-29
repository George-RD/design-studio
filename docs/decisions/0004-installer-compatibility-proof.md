# ADR 0004: Prove public installation without making the installer part of the runtime

- **Status:** Accepted
- **Decision date:** 2026-08-29
- **Owners:** Design Studio maintainers

## Context

Design Studio's canonical product is the portable Agent Skill under `skills/design-studio/`. Existing CI proves that an exact checked-out revision installs through a pinned `skills` CLI, but that proof uses a local repository path. It does not prove that the public GitHub source resolves correctly, and a permanently pinned installer cannot reveal compatibility drift in newer installer releases.

The public distribution contract also needs to stay separate from the runtime contract. Users obtain Design Studio with `npx skills add George-RD/design-studio`, but supported behavior runs from the installed Agent Skill and host capabilities after installation.

## Decision

Keep three complementary CI signals in `.github/workflows/validate-agent-skill-install.yml`:

1. **Pinned exact-revision proof, blocking.** Install the checked-out revision from `$GITHUB_WORKSPACE` with `skills@1.5.23`, verify the installed package, and execute the shipped deterministic mechanical runtime. This remains the reproducible product proof.
2. **Pinned public-source proof, blocking.** Install `George-RD/design-studio#main` with `skills@1.5.23` for both `codex` and `claude-code`, verify required installed files, execute the installed mechanical runtime, and reject repository-only leakage. On a pull request this explicitly tests merged `main`, not the unmerged PR head. On a push to `main`, the public install must also match the checked-out merged revision at selected package files.
3. **Latest-installer public-source proof, advisory.** Repeat the public install with `skills@latest` for both representative hosts. `continue-on-error: true` makes this a drift signal rather than a release gate because an upstream installer release must not erase the known-good product proof.

`npx skills` is an installation mechanism only. It is not a Design Studio runtime dependency, and no skills.sh registration or publishing step is required for installation from the public GitHub repository. The `skills` CLI resolves the repository source directly.

`codex` and `claude-code` remain the representative host install targets. This decision does not make either host canonical; both consume the same Agent Skill package.

## Consequences

### Positive

- CI now proves both the repository package itself and public GitHub-source resolution.
- Reproducibility remains anchored to a known installer version.
- Installer drift is visible without allowing an unrelated upstream release to invalidate the known-good product proof.
- Pull-request evidence cannot be mistaken for proof that an unmerged head is already available from the public source.
- Installation tooling remains outside the supported runtime boundary.

### Costs and risks

- The public-source jobs add network-dependent CI work.
- The blocking public-source proof can fail when GitHub-source resolution is unavailable even if the local package is correct; that is deliberate because public installation is part of the supported distribution path.
- The advisory latest-installer signal can fail without blocking a merge, so maintainers must investigate persistent drift rather than treating green merge status as proof of latest-installer compatibility.

## Alternatives rejected

### Replace the pinned proof with `skills@latest`

Rejected because a moving installer would make failures non-reproducible and could erase evidence that the Design Studio package still works through the last known-good installer.

### Test only the checked-out repository path

Rejected because it does not prove the public `George-RD/design-studio` source can be discovered and installed.

### Make latest-installer compatibility blocking

Rejected because Design Studio does not control upstream installer releases. Latest compatibility is useful evidence, but the pinned public and exact-revision proofs remain the release gates.

### Add a skills.sh registration or separate publishing step

Rejected because installation resolves directly from the GitHub repository. A registry step would add a second distribution authority without being required by the supported install path.

## Revisit triggers

Revisit this decision if the `skills` CLI removes direct GitHub-source installation, if branch/ref semantics change, if another installer becomes the canonical Agent Skills distribution path, or if repeated advisory failures show that latest-installer compatibility should be promoted to a controlled blocking upgrade process.
