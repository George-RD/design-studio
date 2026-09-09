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

An entire value such as `{color.ink}` refers to another token of the same type. Dangling or cyclic aliases are invalid. Exports preserve aliases as CSS variables so theme overrides propagate through semantic relationships. Inline interpolation, untracked `var()`, environment/attribute/URL dependencies, declaration delimiters, escapes, comments, unbalanced strings/functions, CSS-wide inheritance keywords and control characters are outside this local literal subset. Functions are limited to the runtime's explicit local color, math, gradient, easing, layout, transform and filter allowlist; quoted font names are literals, not function calls. Unknown functions, URL-bearing `image()`/`image-set()` (including vendor forms), and custom external color profiles fail validation before export.

`themes` maps a lowercase hyphenated name to overrides of existing token values. Every effective theme must remain acyclic and type-compatible. Its export selector is `[data-theme="name"]`. Each theme emits its full effective token set so aliases resolve at the theme boundary and nested themes do not leak inherited overrides. Component variants use distinct named tokens and application guidance; arbitrary selectors, theme inheritance and executable component recipes are not supported by this profile.

`provenance` records the run ID, positive accepted iteration, project-relative source token paths, and the path plus SHA-256 of the existing acceptance receipt. `links.designDna` is required; `links.documentVisualContract` is optional. Each link records the original project-relative path and SHA-256. Linked text digests use UTF-8 with CRLF/CR normalized to LF. An acceptance receipt's digest is evidence supplied by the acceptance owner, not proof manufactured by validation.

The Markdown body must contain non-empty `## Overview`, `## Application guidance`, `## Anti-goals`, and `## Ownership boundaries` sections. Duplicate headings are invalid; headings inside code fences and content inside HTML comments do not count. A closing fence must use the opening character, be at least as long, and have only spaces or tabs after it. Guidance explains how to use the tokens without restating the full DNA or page contract.

## Required context

Use the accepted final-tree receipt, Builder-supplied tokens, source-blind DNA, optional Document contract, and their current provenance. For legacy inspection, use the unchanged existing document.

## Outputs and handoff

1. Require the existing final-tree `accept` receipt before codification. Preserve the source-blind roles: the Builder supplies token values from accepted source; the Director supplies DNA from permitted rendered evidence. The Orchestrator assembles provenance and links.
2. Create a fresh run-local staging directory. Record incumbent output digests or absence, but leave the accepted site, `DESIGN.md`, DNA, CSS and generated skill untouched. Assemble the proposed complete output set only in staging.
3. Run `validate_design_authority` on the staged `DESIGN.md`, then `derive_design_authority` into a new run-local receipt. Do not infer missing roles, values, evidence or acceptance. Compare the derived tokens against accepted source values and resolve disagreements before materializing staged consumers.
4. Copy the profiled `DESIGN.md`, DNA, derived CSS and any linked Document contract into the staged generated skill. Its index must contain a usable inline Markdown link to `DESIGN.md` or `./DESIGN.md`, optionally with a fragment. Fenced or indented examples, inline code, HTML comments, images and escaped links cannot supply that pointer.
5. Run `check_design_authority_parity` against the actual staged CSS and generated skill directory. Missing consumers, role/value drift, changed provenance, missing index pointers or linked-content hash mismatches block publication. Retain current parity and complete staged output digests with the run evidence.
6. Only verified staged parity plus the separately accepted transition in [lifecycle.md](lifecycle.md) may enter `publish_codification`. Require unchanged staged and incumbent digests, exclusive output access, complete rollback copies and a publication journal before any replacement. A host that cannot provide recoverable publication must halt before writing. Publish the staged set, then check actual published parity and every output digest before recording publication success. On failure, restore incumbents and remove outputs previously absent; interrupted publication must recover from the retained journal before retrying.

These operations never approve a design, mutate project-wide authority, or implement lifecycle transitions. `acceptanceVerified: false` remains explicit even when parity is verified. The existing acceptance owner authorizes surface completion; [lifecycle.md](lifecycle.md) gates separately accepted system transitions. Parity never promotes an extension, extraction or replacement by itself.

## Failure behavior

Incomplete profile data or failed staged consumer parity blocks publication without changing accepted outputs. Return the concrete findings for correction. Publication failure triggers rollback and halt; incomplete recovery is reported explicitly and can never be recorded as completion. Staging, publication and rollback do not rewrite the existing acceptance receipt.

## Legacy reading and migration

`inspect_design_authority` reports `legacy-unprofiled` for a document without a declared profile. That is readability, not profile validation or new acceptance. Do not invalidate historical runs, rewrite old evidence, or regenerate their tokens automatically. A damaged or unknown declared profile must fail validation, not fall back to legacy success.

For an explicit migration, retain the old document as evidence, assemble a candidate profile from confirmed values and provenance, obtain any missing role decisions, and validate it beside unchanged consumers. Export and check a staged generated skill. Promotion requires explicit extraction under [lifecycle.md](lifecycle.md), including source inspection, rendered proof and separate system acceptance. There is no automatic migration or authority deletion; preserve/none retains historical outputs and evidence.

## Evaluation hooks

`test_design_authority_profile.py` checks public runtime operations, installed-copy behavior, legacy inspection and drift. `test_design_authority_contract.py` checks schema, codification disclosure, generated-skill pointers and source pins.

## Source provenance

Format inspiration: `google-labs-code/design.md`, release `0.4.0`, commit `9bf8eae67128b6cc55ad9bf86665767deb4c11cd`, `docs/spec.md` and `README.md`, Apache-2.0. The local implementation adopts the layered token/prose format, typed roles and brace-reference idea. No upstream code or specification prose is copied.

This is a locally owned compatibility profile, not a claim that Google's linter, schema or exports accept these additional fields. General YAML, upstream token-group conventions, Tailwind/DTCG export and upstream lint rules are not implemented. Upstream updates require a new evidence-gated review; there is no automatic sync or runtime dependency.
