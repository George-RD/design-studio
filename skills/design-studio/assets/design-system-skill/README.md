# design-system-skill template

This directory is a template for an installable, harness-portable design-system skill.

## What it is

The template produces a self-contained skill carrying a project's visual DNA (`design-dna.md`), canonical tokens (`assets/tokens.css`), and, when Design Studio has accepted a paginated-artifact system, its renderer-neutral `document-visual-contract.json`. `SKILL.md` is an INDEX that routes to these authorities rather than restating them.

## How codification instantiates it

During codification the orchestrator:

1. Fills the placeholders in `SKILL.md.template`:
   - `{{PROJECT_NAME}}` - human-readable project name
   - `{{PROJECT_SLUG}}` - kebab-case identifier used for the skill name
   - `{{DNA_NAME}}` - design DNA document name
   - `{{ESSENCE}}` - one-paragraph visual-system essence
   - `{{CREATIVE_TENSION}}` - aesthetic tension defining the direction
   - `{{DATE}}` - codification date
2. Renames the filled file to `SKILL.md`.
3. Copies `harness-output/design-system/design-dna.md` into the skill directory.
4. Copies `harness-output/design-system/tokens.css` into `assets/tokens.css`.
5. If an accepted Document run produced `harness-output/design-system/document-visual-contract.json`, copies it into the skill root unchanged. Do not synthesize one for interactive-only systems.
6. Writes the resulting skill to `harness-output/design-system/skill/<project-slug>-design/`.

For paginated work, `document-visual-contract.json` owns page geometry, furniture, pagination, document component recipes and print QA. `design-dna.md` and tokens still own the wider visual system. Renderer adapters are subordinate examples, never canonical design authority.

## Install paths per harness

- **Claude Code:** copy the skill directory into `.claude/skills/<project-slug>-design/` at the consuming repo root.
- **OMP:** copy into repo-scoped `.omp/skills/<project-slug>-design/` or user-scoped `~/.omp/agent/skills/<project-slug>-design/`.
- **Other harnesses / no harness:** keep it as plain design-system documentation or load the relevant authority files directly.
