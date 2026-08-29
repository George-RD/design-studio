# Notices

Design Studio studies external design-engineering projects as credited research inputs. They are not required to install or start the Design Studio Agent Skill.

## Impeccable

Design Studio v1.5 can optionally invoke the deterministic detector distributed by the [Impeccable](https://github.com/pbakaus/impeccable) project.

- Impeccable is maintained separately and licensed under Apache License 2.0.
- Reviewed research source: `pbakaus/impeccable` at revision `63b04e2530f5c7b41ea83c133daab24f34912456`.
- This repository does not vendor Impeccable source or redistribute its command suite.
- When the optional v1.5 compatibility path invokes it, Design Studio calls the public `impeccable detect` interface and consumes its JSON output.
- Impeccable's own license and notices continue to govern that software.

## Emil Kowalski's skills

Design Studio also reviews methods from [emilkowalski/skills](https://github.com/emilkowalski/skills) as an optional research source.

- Reviewed revision: `d23d7f88a2e21c9e4b1418c7abe420f5c1052ba7`.
- The source is licensed under the MIT License.
- Design Studio does not require those skills at runtime and does not currently vendor their repository.
- Copied or substantially adapted material must retain the applicable MIT copyright and permission notice.

Design Studio's orchestration, prompts, workflow definition and documentation remain licensed under this repository's MIT license.
