# Design Studio Website Redesign — Spec

## 1. Purpose & Audience

Redesign the landing page for **Design Studio**, a Claude Code plugin that generates distinctive, production-grade frontends by separating planning, design, implementation, and evaluation into four isolated agents. The page must prove the product's central claim: that it can defeat the generic "AI-template" look.

**Target audience:**
- Primary: Claude Code users (developers, indie hackers, product builders, small agency owners) who are tired of building websites that look identical to every other AI-generated site.
- Secondary: Designers and design-engineering adjacent builders evaluating whether an AI tool can actually produce original work.

**Emotional response:** The visitor should feel, within seconds, that this is the work of a design studio — not a dev tool. Confident, opinionated, precise. They should trust that the tool can produce the kind of taste they can't get elsewhere.

## 2. Aesthetic Direction & Creative Tension

**Base aesthetic:** A small, independent design studio's own portfolio site — editorial, typographic, spatially confident, with generous negative space and a restrained palette.

**Creative tension:** **Editorial polish WITH engineering honesty.** The page should feel like a studio's portfolio (beautiful, art-directed, confident) but also expose its method openly — diagrams, process, technical constraints, and a candid explanation of why AI defaults are boring. This tension prevents the site from becoming either a slick marketing shell or a dry documentation page.

**Visual keywords:** gallery-white, ink-black, warm paper, bold serif type, monospaced accents, asymmetric grid, fine rules, generous margins, intentional whitespace, subtle grain.

## 3. Feature Set

### Core (must have)
- Hero that immediately communicates "design studio" not "SaaS tool"
- Clear statement of the problem (AI template fatigue)
- Clear explanation of the four-agent process
- Embedded overview video (existing asset)
- Installation instructions and quick-start command
- Scoring explanation
- Footer with license and community attribution

### Distinctive (push for these)
- Asymmetric, non-centered hero layout
- Custom typography pairing (serif display + sans body + mono accents)
- Process visualisation (not a numbered list of cards)
- A "scorecard" or evaluation visual that makes the scoring rubric tangible
- Subtle texture or grain to combat flat vector-smoothness
- A bold opinionated statement about what the product refuses to do

## 4. Technical Stack

- Single static HTML file: `docs/index.html`
- Inline CSS in `<style>` (no external CSS files)
- Vanilla JavaScript if needed (inline, no build step)
- Google Fonts loaded via `<link>` with `&display=swap` (distinctive, non-default faces only)
- Existing assets: `poster.jpg`, `video-720p.mp4` (must remain usable)
- No frameworks, no bundlers, no new dependencies

## 5. Expected Zones & Sections

1. **Header / Navigation** — minimal, logo/wordmark only, no hamburger menu needed.
2. **Hero** — the most important zone. Must establish the studio aesthetic and the value proposition. Asymmetric layout required.
3. **Problem Statement** — the "why this exists" section. Should feel like an editorial pull-quote or manifesto, not a feature list.
4. **Process** — the four-agent loop. Should be visualised as a connected system, not a vertical card stack.
5. **Video / Proof** — existing overview video, presented as a design artifact.
6. **Differentiators** — what makes it different. Avoid a 4-column grid of cards.
7. **Scoring** — the evaluation rubric, presented visually.
8. **Install / CTA** — clear command and action.
9. **Footer** — quiet, legal, attribution.

## 6. Reference Points

- **A24 Films editorial pages** — atmospheric, typographic, confident negative space.
- **Stripe Press** — information density with precision and hierarchy.
- **Independent design studios (e.g. The Studio, Playground Paris)** — small-studio personality, not corporate polish.
- **Swiss International Style** — grid discipline, typographic hierarchy, asymmetric balance.

## 7. Anti-Goals

- **NO centered hero with headline + subtitle + two buttons.** This is the exact AI-template pattern the product exists to defeat. Originality must be ≥ 7; this pattern caps it at 4.
- **NO gradient backgrounds, especially purple or blue.** The current #6c5ce7 is a generic AI-product accent.
- **NO card grid of features.** The "4 cards in a row" layout is a template.
- **NO generic system font stack as the only typeface.** Inter/Roboto/system-ui defaults read as "AI-generated."
- **NO floating UI mockups, "AI" badges, or robot imagery.** The design must speak for itself.
- **NO generic SaaS landing page rhythm** (hero → 3 features → social proof → pricing → CTA footer).
- **NO dark-only theme.** The current dark mode is generic; consider light, paper-like background with ink type.
- **NO text-heavy 800px centered column.** Break the reading experience into varied, intentional layouts.

## 8. Copy Notes

- British spelling.
- No AI/LLM provider names.
- Headlines should be bold and declarative, not tentative.
- CTAs should be confident and minimal.
- The copy should occasionally sound like a studio's manifesto, not a product spec sheet.
