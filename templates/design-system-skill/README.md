# design-system-skill template

This directory is a template for an installable, harness-portable design-system skill.

## What it is

The template produces a self-contained skill that carries a project's visual design DNA (`design-dna.md`) and its canonical token file (`assets/tokens.css`). It is an INDEX skill: `SKILL.md` routes to the detail files rather than restating them.

## How the codify step instantiates it

During the `codify` step the orchestrator:

1. Fills the placeholders in `SKILL.md.template`:
   - `{{PROJECT_NAME}}` — human-readable project name
   - `{{PROJECT_SLUG}}` — kebab-case identifier used for the skill name
   - `{{DNA_NAME}}` — name of the design DNA document
   - `{{ESSENCE}}` — one-paragraph essence of the visual system
   - `{{CREATIVE_TENSION}}` — the aesthetic tension that defines the direction
   - `{{DATE}}` — codification date
2. Renames the filled file to `SKILL.md`.
3. Copies `harness-output/design-system/design-dna.md` into the skill directory.
4. Copies `harness-output/design-system/tokens.css` into `assets/tokens.css`.
5. Writes the resulting skill to `harness-output/design-system/skill/<project-slug>-design/`.

## Install paths per harness

- **Claude Code:** copy the skill directory into `.claude/skills/<project-slug>-design/` at the root of the consuming repo.
- **OMP:** copy it into either the repo-scoped `.omp/skills/<project-slug>-design/` or the user-scoped `~/.omp/agent/skills/<project-slug>-design/`.
- **Other harnesses / no harness:** include the directory as plain documentation under `docs/design-system/` or load `design-dna.md` and `assets/tokens.css` directly into context.
