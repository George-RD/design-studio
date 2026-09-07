# Extend contract fixtures

These four synthetic scenarios cover the Design Intent to Studio workflow handoff, a complete declared path, inherited authority and completion outputs. `DESIGN.md` models an accepted system; it is explicitly not a claim of real acceptance or UI quality.

The automated test validates each supplied Design Intent with the installed runtime, follows declared workflow edges, excludes replacement exploration/global codification and checks preservation versus proposed-only outputs. It does not execute isolated creative roles, render a product, verify file hashes from an actual run or prove aesthetic quality. Those checks remain required during a real run; representative rendered dogfood belongs to #97.

| Scenario | Scope | Expected boundary |
| --- | --- | --- |
| new-page | Account settings route using existing controls | Accepted local surface; global authority unchanged |
| reusable-pattern | Reusable dismissible status pattern | Accepted surface; reusable delta proposed, never applied |
| one-off-component | Local import summary using accepted rows | No global token or generated-skill update |
| incompatible-extension | Required partner brand conflicts with immutable accepted grammar | Explicit new overhaul intent; original extension halted |

Run `python3 -m unittest discover -s test -p test_extend_workflow.py -v` from the repository root. The four prompts and expected boundaries also seed the agent-facing eval catalog.
