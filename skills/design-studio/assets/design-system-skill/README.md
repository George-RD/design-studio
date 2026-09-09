# design-system-skill template

This directory is a template for an installable, harness-portable design-system skill.

## What it is

The template produces a self-contained skill carrying a project's visual DNA (`design-dna.md`), token CSS (`assets/tokens.css`), and, when Design Studio has accepted a paginated-artifact system, its renderer-neutral `document-visual-contract.json`. For profiled systems, `DESIGN.md` owns token values, semantic roles, aliases, themes and provenance; the CSS is derived. Legacy unprofiled systems retain CSS token-value authority. `SKILL.md` is an INDEX that routes to these authorities rather than restating them.

## How codification instantiates it

For newly profiled Studio systems, assemble this skill inside the run-local `designAuthorityStage`, not in the accepted output directory. Follow `references/design-authority/profile.md` for validation/parity and `references/design-authority/lifecycle.md` for separate system acceptance and recoverable publication. Historical unprofiled systems remain readable.

During codification the orchestrator:

1. Fills the placeholders in `SKILL.md.template`:
   - `{{PROJECT_NAME}}` - human-readable project name
   - `{{PROJECT_SLUG}}` - kebab-case identifier used for the skill name
   - `{{DNA_NAME}}` - design DNA document name
   - `{{ESSENCE}}` - one-paragraph visual-system essence
   - `{{CREATIVE_TENSION}}` - aesthetic tension defining the direction
   - `{{DATE}}` - codification date
2. Renames the filled file to `SKILL.md`.
3. Copies the accepted candidate DNA into the staged skill directory; do not substitute incumbent `harness-output/design-system/design-dna.md` when codifying a replacement.
4. Copies the candidate profile's derived CSS into staged `assets/tokens.css`, after comparing it with accepted source token values.
5. If an accepted Document run produced `harness-output/design-system/document-visual-contract.json`, copies it into the skill root unchanged. Do not synthesize one for interactive-only systems.
6. For profiled systems, copies accepted `DESIGN.md` into the skill root without independently editing its profile or guidance. Use `check_design_authority_parity` against the actual CSS and generated skill, including linked DNA and optional Document contract hashes. New codification follows `references/design-authority/profile.md`; historical unprofiled systems remain readable without synthesized provenance.
7. Publishes the verified staged skill to `harness-output/design-system/skill/<project-slug>-design/` only through the accepted lane's recoverable publication, after staged parity and `verify_design_system_transition` pass; Studio uses `publish_codification`. Confirm actual readback through `verify_design_system_publication` before reporting success. Failed publication restores incumbent outputs and halts rather than completing with a partial skill.

For paginated work, `document-visual-contract.json` owns page geometry, furniture, pagination, document component recipes and print QA. DNA owns visual reasoning/motifs/motion. The portable `DESIGN.md` owns shared tokens and guidance; generated CSS and this index do not add canonical rules. Renderer adapters are subordinate examples, never canonical design authority.

## Install paths per harness

- **Claude Code:** copy the skill directory into `.claude/skills/<project-slug>-design/` at the consuming repo root.
- **OMP:** copy into repo-scoped `.omp/skills/<project-slug>-design/` or user-scoped `~/.omp/agent/skills/<project-slug>-design/`.
- **Other harnesses / no harness:** keep it as plain design-system documentation or load the relevant authority files directly.
