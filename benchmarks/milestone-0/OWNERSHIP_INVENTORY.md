# Milestone 0 ownership inventory

**Baseline:** `George-RD/design-studio@7e8a1df3a9ce6ade1116d804abfc7b1189d61381`  
**Compared upstream:** `pbakaus/impeccable@aee6ce9352b842217b3f57c78296a7a4fa35a7f3`  
**Machine-readable source:** [`ownership-inventory.json`](ownership-inventory.json)

## Decision

The smallest Design Studio product worth testing is not another design rule set. It is a resumable orchestration harness that:

- separates source-blind direction, source-aware implementation and source-blind browser evaluation;
- preserves every material attempt as immutable evidence;
- records roots, capabilities, budgets, provenance and failures before accepting a result;
- resumes from validated artifacts rather than repeating completed work;
- applies one ordered decision and final-acceptance authority;
- composes specialist workflows without copying their complete methods.

This remains a **provisional boundary** until the fixed three-lane comparison supplies output, defect, cost and recovery evidence. The inventory is sufficient to guide delegation and deletion, but not to claim that Design Studio outperforms Impeccable alone.

## Coverage

| Kind | Items |
|---|---:|
| Workflow steps | 28 |
| Schemas | 8 |
| Runtime references and compatibility surfaces | 30 |
| Check families | 25 |
| Enumerated checks inside those families | 156 |
| **Total labelled items** | **91** |

| Label | Items | Disposition |
|---|---:|---|
| `core` | 52 | Keep and simplify around one authority |
| `impeccable` | 25 | Delegate through the versioned Impeccable adapter |
| `external-workflow` | 2 | Delegate; retain only routing, inputs, outputs and evidence |
| `compatibility` | 9 | Retain temporarily while callers migrate |
| `delete` | 3 | Remove after the replacement path is verified |

CI validates that every current workflow step, schema and canonical reference is present exactly once, that all labels have the permitted action, and that every non-core item names its target.

## Keep: Design Studio core

All 28 Studio workflow steps remain core at the orchestration level. The important boundary is what each step owns:

| Core responsibility | Why it remains |
|---|---|
| Roots and capability evidence | Prevents work against the wrong app and prevents fabricated browser or tool readiness |
| Hidden direction assignment | Stops the direction-generating agent from steering unattended selection |
| Source-blind Visual Director | Avoids implementation anchoring during direction creation |
| Source-aware Builder in immutable trees | Converts the selected contract without destroying previous attempts |
| Source-blind browser Evaluator | Produces rendered evidence and scores without source or workflow authority |
| Ordered decision table and budgets | Keeps one owner for REFINE, PIVOT, SHIP and HALT |
| Append-only events and resume | Makes long runs recoverable without repeating completed builds |
| Tiered final selection and bounded correction | Prevents latest-wins and unbounded taste loops |
| Final acceptance receipt | Proves the exact tree, viewports, mechanical snapshot and immutability before codification |
| Provenance and reporting | Records upstream tools, versions, failures, limitations and accepted artifacts |

`mechanical_preflight` remains a core **orchestration step**. Its detector commands and rule catalogue do not: those move behind the Impeccable adapter.

## Delegate to Impeccable

The inventory identifies four local surfaces that reproduce Impeccable ownership:

1. **Review lane.** `commands/review.md` and `references/review/*` recreate audit, polish, hierarchy, accessibility, interaction and generated-template critique. Route this work to Impeccable. Keep a Design Studio wrapper only where composite-run evidence or routing adds value.
2. **Mechanical detector implementation.** `quality-gates.md` constructs Impeccable commands and also maintains a smaller fallback catalogue. Milestone 1 should move invocation and parsing into one adapter. Milestone 2 should delete both fallback check lists.
3. **Generic context and design-system guidance.** Most PRODUCT/DESIGN context formatting and the generated design-system template restate upstream design guidance. Retain only fields and packaging needed for isolation, routing, provenance and resume.
4. **Generic Builder quality advice.** Keep the immutable-tree, serve-receipt and fidelity contract. Reduce repeated accessibility, state, token and visual-cleanup instructions to upstream references or adapter evidence.

Pinned upstream evidence supports the delegation: Impeccable already defines technical audit and whole-path polish across accessibility, responsive behavior, hierarchy, state completeness, design-system drift and implementation cleanup.

## Delegate to external workflows

`references/copy.md` and its five local copy gates belong to Growth Arsenal `business-copy-style`. Design Studio should keep:

- the confirmed product and claim boundary passed in;
- the current surface and journey context;
- the external workflow/version invoked;
- the returned artifact and evidence;
- failure and fallback policy.

It should not maintain a second customer-copy methodology.

## Compatibility and deletion map

### Retain temporarily

- `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`: Claude Code installation and marketplace registration surfaces; they mirror canonical skill metadata and do not own workflow behavior.
- `references/planning.md`, `references/evaluation.md` and `references/iteration.md`: explicit aliases to canonical workflow or agent authorities.
- top-level `agents/*.md`: thin plugin registration stubs.
- `commands/create.md`: thin platform command over the canonical Studio lane.
- `commands/review.md`: temporary route until the Impeccable adapter owns Review.

### Delete after replacement evidence

- the fallback source-check catalogue in `quality-gates.md`;
- the fallback browser-computed-check catalogue in `quality-gates.md`;
- unreferenced legacy `references/methodology.md`, superseded by the current rationale, meta and workflow contracts.

## Migration constraints

The map does **not** authorize immediate deletion. Apply this order:

1. land the dependency manifest, doctor and one Impeccable adapter;
2. prove supported install, invocation, schema and failure paths;
3. switch Review and mechanical preflight to the adapter;
4. update evals to test adapter contracts rather than local duplicate behavior;
5. delete the fallback catalogues and compatibility aliases;
6. verify representative greenfield and overhaul runs still preserve isolation, resume, selection and acceptance;
7. use fixed-lane comparison evidence to confirm or revise the provisional smallest product.

## Remaining Milestone 0 evidence

Still required:

- execute the frozen four-fixture, three-lane matrix with one explicit model and shared elapsed budget;
- collect blinded output preference, defects, elapsed time, token/tool cost, failed steps and recovery effort;
- decide whether the retained orchestration controls earn their cost over Impeccable alone.

Until that evidence exists, the inventory proves **ownership and duplication**, not comparative product value.