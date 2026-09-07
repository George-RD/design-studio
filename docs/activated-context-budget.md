# Activated-context budget

Issue #90 implements ADR 0005's route-before-loading decision. This document is a repository test oracle and maintenance budget, not an installed runtime dependency or a second routing authority.

## Universal hot path

A Studio, Review or Document request loads the skill index and the six `coreAuthorities` declared by `skills/design-studio/method-router.json`. It validates Design Intent, reads the method router, then loads the selected procedure. The hot path is **eight unique files**, with no lane procedure, specialist method or role prompt. Merely naming a conditional path in an index is not a load instruction.

The following budget is checked by `test/test_design_intent_loading.py`:

```json
{
  "universalPath": [
    "SKILL.md",
    "invocation.md",
    "design-intent-contract.json",
    "references/design-intent.md",
    "runtime-contract.md",
    "references/context.md",
    "references/runtime-integrity.md",
    "method-router.json"
  ],
  "maxBranchAuthorities": {
    "create-direction": 2,
    "selected-build": 3,
    "accepted-world-extension": 2,
    "overhaul-preflight": 4,
    "static-review": 4,
    "interactive-review": 6,
    "composition-review": 5,
    "document-create": 8,
    "document-review": 8
  },
  "maxRoutedRoleAuthorities": 2
}
```

The classification contract owns modes, capabilities and the single initial procedure. The method router owns all-populated-dimensions matching. An adapter preserves the validated result and this shared load order; a command name does not override the lane.

## Representative branch budgets

A **branch authority** here means a unique selected procedure or method/lens file, in addition to the universal hot path. Deduplicate a procedure that also appears as a leaf. These are bounds for the named stage, not cumulative counts across a complete run and not a claim about model token usage.

| Request/stage | Included branch authorities | Maximum |
| --- | --- | ---: |
| Create direction | Studio workflow and rationale | 2 |
| Selected build with mechanical preflight | Studio workflow, generation and quality gates | 3 |
| Accepted-world extension at entry | Studio workflow and extend preservation procedure; no replacement-direction leaves | 2 |
| Overhaul with mechanical preflight | Studio workflow, overhaul, rationale and quality gates | 4 |
| Static Review | Review procedure, specificity, hierarchy and accessibility | 4 |
| Interactive/motion Review with confirmation | Static Review plus interaction and quality gates | 6 |
| Review with composition artifacts | Static Review plus the copy-authority boundary | 5 |
| Document create/review at page evaluation with mechanical evidence | Document procedure, specificity, hierarchy, quality gates and four page lenses | 8 |

Document page evaluation loads pagination, tables, furniture and print. It does not load Studio's workflow, generation/overhaul methods or interactive Review's orchestration/accessibility/interaction procedures. It reuses the explicitly medium-agnostic specificity and hierarchy leaves. Studio and Review do not load the Document page lenses.

Issue #91 raises only the extension branch from one to two authorities because accepted-world preflight and bounded completion now have a canonical extend method. Its selected/excluded loading test includes that leaf while excluding rationale/overhaul and all Document lenses. The universal hot path is unchanged.

## Stage-specific context

Role prompts named in matched routes are conditional dependencies, capped at two unique role files for these examples. The selected procedure supplies them to the relevant isolated role at its stage, not to every activation or every role. Universal source-blind boundaries still apply before any role is invoked.

Project truth, accepted visual artifacts, rendered evidence, runtime helper code and operation-specific schemas are not method files and are not included in these branch-method counts. They must be loaded only when the selected operation needs them. For example, Document publication loads its visual-contract schema after acceptance; it is not part of classification or initial review. Composition authority resolution may need the composition contract before intent can settle; that bounded authority lookup does not authorize loading an adjacent skill's methods.

A new source/evidence signal can add a method, but a new lane must produce a new validated Design Intent. Do not reuse accumulated task signals from an earlier lane. Conflicting route procedures block loading until the signals or intent are resolved.

## Verification and change policy

Run `python3 -m unittest discover -s test -p 'test_design_intent*.py' -v`. The tests validate supplied intents through the shipped runtime, apply the existing router matching contract, and compare selected and excluded file paths against independent expectations. They also check adapter prerequisites, the universal path, the Document procedure's explicit lens references, and the bounds above. They do not snapshot full prompts or use token counts as proof of routing correctness.

Raising a bound requires a named need and updated selected/excluded-authority evidence. Do not remove necessary source, recovery, capability or acceptance guards to meet the budget. The later #96 instruction-pruning pass should work from this settled loading boundary rather than introduce another router.
