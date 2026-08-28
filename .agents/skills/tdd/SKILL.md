---
name: tdd
description: Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions "red-green-refactor", or wants integration tests.
---

# Test-Driven Development

TDD is the **red → green → refactor** loop. This skill is the reference that makes that loop produce tests worth keeping: what a good test is, where tests go, the anti-patterns, and the rules of the loop. Every section applies on every cycle: consult them before and during the loop, not after.

When exploring the codebase, read `CONTEXT.md` (if it exists) so test names and interface vocabulary match the project's domain language, and respect ADRs in the area you're touching.

## What a good test is

Tests verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't. A good test reads like a specification: "user can checkout with valid cart" tells you exactly what capability exists, and it survives refactors because it doesn't care about internal structure.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for mocking guidelines.

## Seams: where tests go

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

Test only at the seams defined by the source spec/ticket or already-established public interface. When the seam is not explicit, infer the highest stable seam from the spec, ADRs and current architecture and record that assumption in the implementation evidence. Ask only when different seam choices would materially change the public contract and existing evidence cannot resolve the choice.

When the shape of that interface is itself in question (how deep the module is, where the seam belongs, what the interface should expose), use `codebase-design` for the shared module/interface/depth/seam/adapter vocabulary before starting the red cycle.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or verifies through a side channel (querying the database instead of using the interface). The tell: the test breaks when you refactor but behavior hasn't changed.
- **Tautological**: the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`, a snapshot derived by hand the same way, a constant asserted equal to itself), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth: a known-good literal, a worked example, or the spec.
- **Horizontal slicing**: writing all tests first, then all implementation. Bulk tests verify imagined behavior and commit to test structure before understanding the implementation. Work in **vertical slices** instead: one test → one implementation → one local refactor, with each test acting as a tracer bullet informed by the previous cycle.

## Rules of the loop

- **Red before green.** Write one failing behavioral test first. Confirm that it fails for the intended missing behavior rather than for setup noise.
- **Green minimally.** Implement only enough behavior to make that slice pass. Do not anticipate future slices or add speculative features.
- **Refactor after green.** Improve names, duplication and local structure while keeping the completed test green before starting the next red cycle.
- **One slice at a time.** One seam, one behavioral increment and one red → green → refactor cycle at a time.
- **Keep structural scope proportional.** Local refactoring belongs in each TDD cycle. Broader architectural/deepening changes that exceed the completed slice belong in a separately justified refactor or review step, protected by the established seam tests.
