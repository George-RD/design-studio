# Portable DESIGN.md authority profile

## Purpose

Validate portable token authority and deterministic consumers without promoting candidate design decisions.

## Triggers

Load this reference when codifying a newly accepted Studio system, checking a profiled system's consumers, or deliberately migrating legacy design documentation. It does not load during direction or source-blind evaluation.

## Authority boundary

`DESIGN.md` contains the machine-readable profile and human application guidance. There is no second canonical JSON profile. During this additive stage, check it beside the existing accepted tokens and generated skill; a disagreement blocks codification rather than selecting whichever file was read last.

The profile owns token identifiers, types, semantic roles, alias relationships, theme overrides and token provenance. `design-dna.md` owns the broader thesis, motifs, composition and motion. A linked `document-visual-contract.json` owns page geometry, furniture, pagination, document recipes and print rules. Link those authorities by path and digest instead of copying their rules. Shared-token changes require agreement, not independent edits to each output.

## Representation

Use JSON front matter between two lines containing only `---`, followed by Markdown guidance. JSON is the deliberately narrow YAML-compatible representation: no YAML parser, external CLI or network operation is needed. Validate the header against `design-authority.schema.json` and the additional semantic checks below.

Required header fields are `profile: "design-studio/design-authority"`, `schemaVersion: 1`, `name`, `tokens`, `provenance`, and `links`. `themes` is optional. Unknown fields and duplicate JSON keys are errors.

Each token has a stable identifier, a `type`, a semantic `role`, a unique CSS custom-property name in `css`, and a string `value`. Identifiers and roles use lowercase words separated by dots or hyphens. Types are `color`, `dimension`, `number`, `font-family`, `duration`, or `css` for other literal CSS values. Types constrain alias compatibility; this is not a browser CSS grammar or contrast validator.

An entire value such as `{color.ink}` refers to another token of the same type. Dangling or cyclic aliases are invalid. Exports preserve aliases as CSS variables so theme overrides propagate through semantic relationships. Inline interpolation, untracked `var()`, environment/attribute/URL dependencies, declaration delimiters, escapes, comments, unbalanced strings/functions, CSS-wide inheritance keywords and control characters are outside this local literal subset.

`themes` maps a lowercase hyphenated name to overrides of existing token values. Every effective theme must remain acyclic and type-compatible. Its export selector is `[data-theme="name"]`. Each theme emits its full effective token set so aliases resolve at the theme boundary and nested themes do not leak inherited overrides. Component variants use distinct named tokens and application guidance; arbitrary selectors, theme inheritance and executable component recipes are not supported by this profile.

`provenance` records the run ID, positive accepted iteration, project-relative source token paths, and the path plus SHA-256 of the existing acceptance receipt. `links.designDna` is required; `links.documentVisualContract` is optional. Each link records the original project-relative path and SHA-256. Linked text digests use UTF-8 with CRLF/CR normalized to LF. An acceptance receipt's digest is evidence supplied by the acceptance owner, not proof manufactured by validation.

The Markdown body must contain non-empty `## Overview`, `## Application guidance`, `## Anti-goals`, and `## Ownership boundaries` sections. Duplicate headings are invalid; headings inside code fences do not count. Guidance explains how to use the tokens without restating the full DNA or page contract.

## Required context

Use the accepted final-tree receipt, Builder-supplied tokens, source-blind DNA, optional Document contract, and their current provenance. For legacy inspection, use the unchanged existing document.

## Outputs and handoff

1. Require the existing final-tree `accept` receipt before codification. Preserve the source-blind roles: the Builder supplies token values from accepted source; the Director supplies DNA from permitted rendered evidence. The Orchestrator assembles provenance and links.
2. Run `validate_design_authority` on the proposed `DESIGN.md`. Do not infer missing roles, values, evidence or acceptance.
3. Run `derive_design_authority` into a new run-local receipt. It returns normalized DESIGN.md text, deterministic CSS, semantic-role metadata and lineage. Compare against the accepted source tokens; resolve any mismatch explicitly before materializing consumers.
4. Materialize the existing token and generated-skill outputs. Copy the profiled `DESIGN.md`, DNA, CSS and any linked Document contract into the generated skill. Its index links to `DESIGN.md` instead of duplicating the profile.
5. Run `check_design_authority_parity` against the actual CSS and generated skill directory. Missing consumers, role/value drift, changed provenance, missing index pointers or linked-content hash mismatches block completion. Retain the result with the run evidence.

These operations never approve a design, mutate project-wide authority, or implement lifecycle transitions. `acceptanceVerified: false` remains explicit even when parity is verified. The existing acceptance owner authorizes codification; proposed extension/extraction/replacement deltas remain proposed until the separate lifecycle contract supports their transition.

## Failure behavior

Incomplete profile data or failed consumer parity blocks codification; preserve existing accepted outputs and return the concrete findings for correction.

## Legacy reading and migration

`inspect_design_authority` reports `legacy-unprofiled` for a document without a declared profile. That is readability, not profile validation or new acceptance. Do not invalidate historical runs, rewrite old evidence, or regenerate their tokens automatically. A damaged or unknown declared profile must fail validation, not fall back to legacy success.

For an explicit migration, retain the old document as evidence, assemble a candidate profile from confirmed values and provenance, obtain any missing role decisions, and validate it beside unchanged consumers. Export and check a staged generated skill. Promotion still requires the existing acceptance owner; no lifecycle migration or authority deletion occurs in this additive stage.

## Evaluation hooks

`test_design_authority_profile.py` checks public runtime operations, installed-copy behavior, legacy inspection and drift. `test_design_authority_contract.py` checks schema, codification disclosure, generated-skill pointers and source pins.

## Source provenance

Format inspiration: `google-labs-code/design.md`, release `0.4.0`, commit `9bf8eae67128b6cc55ad9bf86665767deb4c11cd`, `docs/spec.md` and `README.md`, Apache-2.0. The local implementation adopts the layered token/prose format, typed roles and brace-reference idea. No upstream code or specification prose is copied.

This is a locally owned compatibility profile, not a claim that Google's linter, schema or exports accept these additional fields. General YAML, upstream token-group conventions, Tailwind/DTCG export and upstream lint rules are not implemented. Upstream updates require a new evidence-gated review; there is no automatic sync or runtime dependency.
