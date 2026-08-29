# Repository scripts

**Status:** Repository-only research and development tooling. These scripts are not part of the installed Design Studio runtime.

The responsibility-level classification is maintained in [`docs/migration-map.md`](../docs/migration-map.md). Current families cover benchmark/comparison research, capability evidence and CI/development support; no current `scripts/` family is classified as product runtime.

Existing script paths remain stable for repository CI and retained research. A supported Design Studio run or host adapter must not import or shell into these entrypoints. If deterministic behavior is required by the product, extract the smallest supported implementation behind the skill-owned runtime contract under `skills/design-studio/` rather than making repository tooling a hidden dependency.
