# Planning Module

How to expand a terse user prompt into a full product specification and sprint contract.

## The Problem with Terse Prompts

A prompt like "build a portfolio website" gives the Design Agent no creative constraints to push against. Without a spec, the downstream agents default to the safest interpretation — a generic grid of cards with a hero section.

The planner's job is to turn that into a vivid, specific vision that constrains the Design Agent enough to be coherent but leaves room for creative interpretation.

## Spec Structure

Write `harness-output/spec.md` with these sections:

### 1. Purpose & Audience

Who is this for? What problem does it solve? What emotional response should users have?

Go beyond the functional: "A portfolio for a photographer" becomes "A portfolio for a wildlife photographer who shoots in extreme conditions — Arctic tundra, deep ocean, volcanic terrain. The site should feel like an expedition journal, not a gallery."

### 2. Aesthetic Direction & Creative Tension

Commit to a BOLD direction, but go beyond a single aesthetic label. A label alone ("brutalist", "editorial", "luxury") produces recognizable but generic designs — the Design Agent will pattern-match to typical examples of that aesthetic.

Instead, specify a **creative tension** — two seemingly contradictory qualities that create distinctiveness through their combination:

- "Brutalist WITH ornamental flourishes"
- "Minimalist BUT textural and warm"
- "Technical precision WITH organic imperfection"
- "Serious authority WITH playful micro-interactions"
- "Editorial sophistication WITH raw, unfinished edges"
- "Luxury restraint WITH maximalist typography"

A creative tension forces the Design Agent to find original solutions at the intersection. There is no existing template for "minimalist but textural" — the agent must invent one.

**Format:** Name the base aesthetic AND the tension explicitly. "This is an **expedition journal aesthetic** (base: documentary/field-research) WITH **museum-quality presentation** (tension: raw subject matter presented with institutional polish). Weathered textures and hand-annotated photography, but composed with the spatial precision of a gallery installation."

You may also choose from the spectrum of base aesthetics — or invent one:

- Brutally minimal, maximalist chaos, retro-futuristic, organic/natural
- Luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw
- Art deco/geometric, soft/pastel, industrial/utilitarian
- Spatial/3D, collage/mixed-media, typographic-led, data-visualization aesthetic

Name the direction explicitly. "This is an **expedition journal aesthetic**: weathered textures, hand-annotated photography, topographic overlays, field-notebook typography."

#### Creative Tension

The spec must define not just a base aesthetic but a **contrasting tension** — a secondary quality that pulls against the base direction. The tension forces original solutions at the intersection of the two qualities, preventing the Design Agent from defaulting to template execution of the base aesthetic alone.

Format: **"[Base Aesthetic] WITH/BUT [Contrasting Tension]"** (either connector works — WITH emphasizes additive fusion, BUT emphasizes contradiction)

Examples:
- "**Brutalist** WITH **ornamental flourishes**" — raw concrete structure adorned with unexpected decorative moments
- "**Minimalist** BUT **textural and warm**" — restrained composition with rich material surfaces (linen, wood grain, handmade paper)
- "**Swiss modernist grid** WITH **punk energy**" — Muller-Brockmann structure disrupted by unexpected scale breaks and raw typography
- "**Japanese editorial** WITH **industrial weight**" — delicate whitespace and considered placement anchored by heavy typographic elements
- "**Art deco geometric** BUT **organic and imperfect**" — geometric frameworks with hand-drawn quality and natural asymmetry

The tension is what the Design Agent expects to receive. Without it, the Design Agent will execute the base aesthetic faithfully but predictably. The tension is where originality lives — it creates a design problem that cannot be solved by templates.

### 3. Feature Set

List every feature, grouped by priority:

- **Core** — Must have for the page to function
- **Distinctive** — Features that make this memorable (animations, spatial layouts, interactive elements, AI features)
- **Polish** — Micro-interactions, loading states, easter eggs

Bias toward the Distinctive category. The evaluator weights originality heavily.

### 4. Technical Stack

Specify the implementation technology:
- HTML/CSS/JS (vanilla)
- React + Vite
- Next.js
- Vue
- Other

Default to vanilla HTML/CSS/JS for single pages. Use React/Vite for multi-component applications.

### 5. Expected Zones & Sections

Identify the expected visual zones and sections upfront so the evaluator knows what to look for during zone-based evaluation. This prevents the evaluator from guessing zone boundaries or missing important areas.

```markdown
## Expected Zones
- **Header**: Logo + navigation — persistent across scroll
- **Hero**: Full-viewport opening statement with [key visual element]
- **Feature showcase**: 3-4 capability demonstrations with interactive elements
- **Social proof / testimonials**: Customer stories with photography
- **Data visualization**: [if applicable] Charts, graphs, metrics display
- **Sidebar**: [if applicable] Contextual navigation or supplementary content
- **CTA section**: Conversion moment before footer
- **Footer**: Links, legal, contact
```

Each zone will be independently scored during evaluation. The planner should flag zones that are particularly important to the project's success or zones with high technical risk (e.g., data visualizations, complex interactive sections).

### 6. Reference Points

Name 2-3 real websites, designers, or art movements as reference points. NOT to copy — to establish a creative conversation.

"Reference the spatial navigation of Stripe's marketing site, the typographic confidence of Bloomberg's editorial layouts, and the atmospheric density of a Blade Runner set."

### 7. Anti-Goals

What this should NOT look like. Be specific and aggressive. Anti-goals are as important as goals — they define the negative space the design must avoid.

**Template patterns to explicitly reject:**
- "Not a SaaS landing page with alternating left-right feature sections"
- "Not a template with a hero → features → testimonials → CTA structure"
- "Not a dark theme with neon accents (unless the concept demands it)"
- "Not a centered-content-on-white-background layout with card grids"
- "Not a Bootstrap/Tailwind UI default component arrangement"

**Reference sites that represent what NOT to do:**
- Generic AI product landing pages (identical gradient heroes, floating UI mockups, "Powered by AI" badges)
- Template marketplaces (ThemeForest top sellers — technically polished but visually interchangeable)
- Default SaaS marketing sites (Stripe clones, Linear clones — beautiful but now a cliché)

**The aesthetic default to push AWAY from:**
Name the specific gravitational pull the design must resist. Every aesthetic has a default interpretation that AI models converge on. For example:
- "Minimalist" defaults to → white space, thin sans-serif, centered layout. Push AWAY from this toward textural minimalism, asymmetric minimalism, or dense minimalism.
- "Brutalist" defaults to → Times New Roman, harsh borders, monochrome. Push AWAY from this toward colorful brutalism, organic brutalism, or refined brutalism.
- "Editorial" defaults to → magazine grid, serif headlines, black-and-white photography. Push AWAY from this toward immersive editorial, interactive editorial, or spatial editorial.

**Zone-level anti-goals:**
- "No text overlaps, clipping, or overflow that hides behind an overall passing score"
- "No zones that look polished in isolation but break at actual viewport boundaries"

## Sprint Contract Structure

Write `harness-output/sprint-contract.md` with testable success criteria:

### Format

```markdown
# Sprint Contract

## Acceptance Criteria

### Design Quality
- [ ] The page has a single, nameable aesthetic direction
- [ ] Colors form a coherent palette (not scattered rainbow)
- [ ] Typography uses at most 2-3 font families with clear hierarchy
- [ ] Layout creates visual rhythm through spacing and composition
- [ ] [Project-specific criterion]

### Originality
- [ ] No generic hero section with centered heading + subtitle + CTA button
- [ ] At least one spatial or interactive element that surprises
- [ ] Typography choices are distinctive (not Inter, Roboto, Arial, system fonts)
- [ ] Color palette is not a stock theme (not the default Tailwind palette)
- [ ] [Project-specific criterion]

### Craft
- [ ] Responsive across 1440px and 390px viewports
- [ ] Typography hierarchy is consistent (heading sizes, body text, captions)
- [ ] Spacing follows a consistent scale
- [ ] Color contrast meets WCAG AA for text content
- [ ] [Project-specific criterion]

### Functionality
- [ ] Primary action is immediately identifiable
- [ ] Navigation is intuitive (user can reach any section in ≤2 clicks)
- [ ] Interactive elements respond to hover/focus states
- [ ] Page loads without console errors
- [ ] [Project-specific criterion]
```

### Negotiation

The sprint contract is not fixed by the planner alone. When the harness orchestrator creates the evaluator agent, it should include the sprint contract and invite the evaluator to propose additional criteria. This negotiation ensures the evaluator knows exactly what "done" means before evaluation begins.

## Planning Anti-Patterns

1. **Over-specification.** Don't write implementation details (CSS values, exact layouts). Specify the WHAT and WHY, not the HOW. The Design Agent needs creative freedom.
2. **Safe specs.** If the spec reads like a template, rewrite it. Every spec should have at least one element that feels ambitious or unexpected.
3. **Feature creep.** 6-10 features total. More than that diffuses the Design Agent's attention across too many concerns.
4. **Missing aesthetic direction.** A spec without a named aesthetic direction WILL produce generic output. This is the single most important field.
