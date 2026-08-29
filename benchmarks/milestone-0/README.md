# Milestone 0 comparison fixtures

**Status:** Historical research evidence retained for targeted comparisons. This tree is not a release gate or an installed-runtime dependency.

These fixtures freeze the inputs used to test whether Design Studio adds useful orchestration beyond a specialist design workflow used alone.

## Acceptance contract

A fixture set is frozen only when:

1. all four roadmap scenarios have a versioned manifest;
2. every lane receives the exact same brief, baseline tree, assets, viewport list and functional checks;
3. briefs contain no lane names or lane-specific instructions;
4. overhaul and review fixtures include self-contained runnable baselines;
5. the lock file covers every fixture input byte;
6. the required measurements match `ROADMAP.md`;
7. contract tests reject silent mutation, missing baselines and biased prompts.

The comparison lanes are defined once in `manifest.json`. They are not repeated inside briefs.

## Running a fixture

Each run copies one fixture into a fresh work directory and records output outside this tree.

- Read `fixture.json`.
- Give the runner exactly `brief.md` and any declared `input/` tree.
- Use the declared viewports and functional checks.
- Do not add lane-specific help, assets or corrections.
- Preserve all raw attempts and record the required metrics.
- Store the lane, tool versions and exact invocation in the run evidence, not in the fixture.

## Change policy

These files are evidence inputs, not examples to casually improve. A material change requires:

- a fixture version bump;
- an explanation in the pull request;
- an updated `fixture-lock.json`;
- rerunning every comparison lane for that fixture.

Formatting-only changes still update the lock because they can alter model input.
