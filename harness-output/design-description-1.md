# Design Description — Iteration 1

> Note: The requested baseline screenshot (`harness-output/current-screenshot.png`) was not present in the repository. This description is therefore grounded entirely in the project spec and sprint contract.

## 1. Overall mood and creative intent

The page should read like a gallery exhibition poster for a working design studio: confident, typographic, spatially generous, and quietly opinionated. The layout is built on an editorial 12-column grid, but key elements deliberately break or stretch across it to create tension. Negative space is treated as an active material, not leftover canvas. The overall impression is of a studio that has already made decisions and is showing you the work, not asking for permission.

**This page MUST feel like a printed portfolio of a small, independent design studio — editorial, typographic, and intentionally asymmetrical — NOT like a SaaS product launch page with a centered hero, a subtitle, and a primary button.**

The creative tension is **editorial polish WITH engineering honesty**: the page is beautiful, but it also exposes its method openly through the process diagram, the scorecard, and the manifesto-like copy. Nothing is hidden behind vague marketing language.

## 2. Color palette

A restrained, warm, paper-forward palette. Use one accent color only, and use it sparingly.

- **Gallery Paper** (page background): `#F4F1EA` — warm off-white, like heavy cotton paper.
- **Ink** (headlines, body text, rules): `#121212` — near-black, not pure black, to keep the warmth.
- **Muted Ink** (secondary text, captions, hover states): `#5E5A52` — warm grey-brown.
- **Accent** (CTA, weighted bars, quotation mark, play button): `#B9462E` — burnt sienna / terracotta.
- **Warm Rule** (dividers, subtle borders): `#D9D5CC` — barely-there warm grey.
- **Deep Canvas** (video block, install command block): `#1A1A1A` — charcoal for the few dark moments.
- **Off-White** (text on dark canvas): `#F4F1EA` — same as the page background, for reversing out type.

No gradients. No background tints beyond the paper and the occasional charcoal band.

## 3. Typography

Load three distinct Google Fonts faces. Do not rely on system defaults alone.

- **Display / Headlines:** `Fraunces` (weights 700 and 800). A high-contrast, characterful serif with modern proportions. Use it large and loud, with tight leading.
- **Body / UI:** `Manrope` (weights 400, 600, 700). A clean, geometric sans with a warm, slightly rounded personality. Use it for body copy, labels, and the bolder list statements.
- **Mono / System accents:** `Space Mono` (weight 400). Used for indexes, captions, version labels, the install command, and small metadata. Keep it small and crisp.

Type scale and roles:

- **Hero wordmark/headline:** Fraunces 800, approximately `11vw` on desktop, line-height `0.88`, letter-spacing `-0.02em`. The type should feel almost too large for the viewport in a deliberate, poster-like way.
- **Section display headlines:** Fraunces 700, `56px`, line-height `1.05`, letter-spacing `-0.01em`.
- **Pull-quote / manifesto text:** Fraunces 700, `42px`, line-height `1.12`.
- **List statements / mid-size headings:** Manrope 700, `24px`, line-height `1.25`.
- **Body copy:** Manrope 400, `17px`, line-height `1.65`. Maximum comfortable line length ~65 characters.
- **Small labels / captions:** Space Mono 400, `12px`, line-height `1.5`, uppercase, letter-spacing `0.08em`.
- **Install command:** Space Mono 400, `16px`, line-height `1.4`.

All body text must remain at least `16px` effective at every viewport.

## 4. Layout and section-by-section description

Base grid: a 12-column editorial grid with side margins of roughly `8vw`, a gutter of `24px`, and a maximum content width of about `1200px`. Vertical rhythm is generous: `120px` to `160px` between major sections.

### Header / Navigation

- A single, quiet strip at the very top, `80px` tall, aligned to the grid.
- Left side: the wordmark “Design Studio” in Manrope 600, `18px`, with a slight positive letter-spacing (`0.02em`).
- Immediately to the right of the wordmark, a small `v1` label in Space Mono `12px` uppercase, separated by a `24px` gap and a thin vertical rule in Warm Rule.
- Far right: a single anchored link, “Install”, in Space Mono `12px` uppercase. No hamburger menu, no nav list, no logo mark.
- The header scrolls with the page; it is not fixed, so the hero can breathe against the top margin.

### Hero

- The hero is full viewport height minus the header, but the content is asymmetric, not centered.
- Left two-thirds (roughly 7 columns): a stacked typographic lockup. The wordmark/headline “Design Studio” sits high, aligned to the top of the grid, in the massive Fraunces display. Below it, a short manifesto line in Manrope 400, `20px`, line-height `1.5`, occupying about 60% of the column width. The line should feel like a caption to a poster, not a subtitle.
- Bottom-left of the left column: a thin horizontal rule in Warm Rule, then the install command displayed in Space Mono on a single line, preceded by a small prompt character. It is set as a quiet typographic element, not a button.
- Right third (roughly 5 columns): a tall, portrait-like framed artifact. Use the existing `poster.jpg` as a large image inside a thin `1px` Warm Rule border. The image should nearly fill the right column height, anchored to the right margin. Add a small rotated caption “Overview” in Space Mono uppercase, reading vertically along the right edge of the frame.
- The hero must not be a centered block with a button pair. The action is the command line, not a CTA button.

### Problem Statement

- This section is a full-width band of slightly warmer paper (`#EBE7DE`) to separate it from the hero.
- Left side (8 columns): a large serif pull-quote in Fraunces 700, `42px`, line-height `1.12`, left-aligned. Behind it, a giant quotation mark in the Accent color at roughly `20%` opacity, cropped by the left edge.
- Right side (4 columns): a short body paragraph in Manrope 400, `17px`, line-height `1.65`, explaining why AI-template fatigue is the problem. It sits lower than the quote, creating an intentional vertical offset.
- The section should feel like a magazine spread, not a features list.

### Process

- The four-agent loop is shown as a connected system, not a vertical stack of cards.
- A single thin horizontal ink line (`1px`) runs across the grid at mid-height, like a baseline or timeline.
- Four circular nodes sit on this line, evenly spaced but not mechanically equal. Each node is a small circle (`56px` diameter) with a thin ink border. Inside, the number `01`–`04` is set in Space Mono `12px` uppercase.
- Each node has a label placed alternately above and below the line to break the grid: node 1 label above, node 2 below, node 3 above, node 4 below. The label is in Manrope 700, `18px`, with a one-line description in Manrope 400, `16px`, beneath it.
- The labels should read: Plan, Design, Build, Evaluate.
- Keep the diagram in a large white field with plenty of breathing room above and below.

### Video / Proof

- Present the existing video as a curated design artifact.
- A wide charcoal block (`#1A1A1A`) spans the full content width, framed by a thin Warm Rule border. The block is approximately 16:9 in ratio.
- The video sits inside the frame, with `poster.jpg` as the placeholder. A circular play button in Accent (`#B9462E`) sits dead center, `72px` diameter, with a small white triangle/play icon in the center. No generic browser controls visible until the user interacts; the custom button is the only visible control.
- Below the video frame, a caption in Space Mono `12px` uppercase: “Two-minute overview” in Muted Ink, left-aligned with the frame.
- On hover, the play button subtly scales; the rest of the frame stays still.

### Differentiators

- Avoid any card grid. Use a typographic index.
- Five strong statements, each separated by a thin Warm Rule. The list spans the full content width.
- Each item is composed of:
  - A small mono index (`01`–`05`) in Space Mono `12px` uppercase, aligned to the left margin.
  - A large statement in Manrope 700, `24px`, line-height `1.25`, positioned to the right of the index.
  - A short explanatory note in Manrope 400, `16px`, line-height `1.6`, beneath the statement, indented to align with the statement text.
- No boxes, icons, badges, or images. The rhythm is created by the rules and the type hierarchy alone.

### Scoring

- Make the evaluation rubric tangible by showing the formula and the weighted criteria visually.
- At the top, the weighted-average formula is set in Fraunces 700, `48px`, line-height `1.1`, with the variables and weights in different sizes to create a readable hierarchy.
- Below the formula: four horizontal bars arranged in a single column, each bar representing one criterion.
  - Design Quality and Originality (the 2×-weighted criteria) are rendered as thick Accent bars (`#B9462E`, height `24px`).
  - Craft and Functionality are rendered as thinner Ink bars (`#121212`, height `12px`).
- Each bar has a label in Space Mono `12px` uppercase to the left and a weight note (“2×”) to the right.
- The whole scorecard sits inside a thin Warm Rule border with a very soft, paper-like shadow, like a pinned specimen card.

### Install / CTA

- The section is dominated by a large command block, not a button.
- Left-aligned headline in Fraunces 700, `42px`: “Install it.”
- Below, a wide charcoal rectangle (`#1A1A1A`) containing the install command in Space Mono `16px`, in Off-White (`#F4F1EA`). The command is preceded by a small prompt marker. A small “copy” text label in Muted Ink sits to the right of the command.
- The CTA is a confident inline text link in Accent (`#B9462E`) with a thin underline: “Read the full guide →”. No primary button.
- Generous negative space above this section (`140px`) to let the action feel deliberate.

### Footer

- A single thin Warm Rule across the full width, `24px` above the text.
- Left-aligned text in Space Mono `16px`, line-height `1.6`, in Muted Ink. Two lines: a license line and a community attribution line.
- No logo, no columns, no large type. The footer should feel like the small print on a studio letterhead.

## 5. Motion and interaction intent

Motion is restrained, editorial, and unhurried. The page should feel like a sheet being placed on a table, not a product launch countdown.

- On entry, the hero headline and poster frame fade up from `20px` below and settle into place over `700ms` with an ease-out curve. The rest of the hero copy follows with a `200ms` stagger.
- As each major section enters the viewport (about `30%` visible), its headline and primary content fade up `20px` over `600ms`. The process diagram’s connecting line draws in from left to right over `800ms` once the section is visible.
- The video play button scales to `1.05` on hover with a `200ms` transition.
- The install command block shifts to a slightly lighter charcoal (`#2A2A2A`) on hover.
- No parallax, no bouncing, no character-by-character reveals, no infinite loops, no loading spinners.

## 6. Atmospheric details

- A very fine, static film-grain overlay across the entire page at roughly `4%` opacity, in a warm grey tone. It should read as the texture of good paper or a risograph print, not as a digital filter.
- Thin `1px` Warm Rule lines divide the sections and the header from the page. These rules are not drop shadows; they are physical strokes.
- A faint, low-opacity `12-column` grid overlay in the hero only, rendered in Warm Rule at about `4%` opacity, to subtly reinforce the editorial grid without cluttering the reading experience.
- The Accent color is used only for the CTA link, the two 2× bars, the play button, and the ghosted quotation mark. It never appears as a background gradient or a large fill.
- All images should sit flat against the paper, with no heavy drop shadows except for the soft shadow on the scorecard and the video block.

## 7. Anti-goals and what to avoid

- No centered hero with a headline, subtitle, and two buttons.
- No purple, blue, or any gradient backgrounds.
- No 3–4 column card grid of features.
- No system-only font stack (Inter, Roboto, system-ui, etc.) as the primary typeface.
- No floating UI mockups, “AI” badges, robot imagery, or sparkle icons.
- No dark-only theme; the page lives on warm paper with selective charcoal moments.
- No generic SaaS landing-page rhythm (hero → feature grid → social proof → pricing → CTA footer).
- No single, centered `800px` text column running the length of the page. Break the reading into varied, intentional layouts.
- No generic marketing vagueness; the copy should occasionally read like a studio manifesto.
