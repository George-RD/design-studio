# Surface modes

The mode describes what success looks like for a visitor on one surface. It is selected per surface, not per product.

| Mode | Visitor success | Design priority |
|---|---|---|
| `persuade` | Understands the offer, believes it, and acts | Clarity, desire, proof, memorable form |
| `operate` | Completes a task correctly and efficiently | State clarity, scanability, familiar affordances, resilience |
| `read` | Understands and can navigate information | Comprehension, hierarchy, wayfinding, reading comfort |
| `experience` | Encounters or explores the work itself | Artifact primacy, atmosphere, discovery, authored transitions |

A product can use all four. A tool's marketing page is `persuade`; its editor is `operate`; its documentation is `read`; its showcase may be `experience`.

## Mode-specific evaluation

All modes use the same four score names, but their weights and floors differ.

| Mode | Design quality | Originality | Craft | Functionality | Minimums to ship |
|---|---:|---:|---:|---:|---|
| `persuade` | 2.0 | 2.0 | 1.0 | 1.0 | 7 / 7 / 7 / 7 |
| `experience` | 2.0 | 2.0 | 1.0 | 1.0 | 7 / 7 / 7 / 7 |
| `operate` | 1.5 | 0.75 | 1.5 | 2.25 | 7 / 5 / 7 / 8 |
| `read` | 1.5 | 0.75 | 1.75 | 2.0 | 7 / 5 / 7 / 7 |

Weighted average is:

```text
sum(score × mode weight) / sum(mode weights)
```

The weighted average never overrides a failed minimum or an open blocker.

## What originality means by mode

**Persuade:** the form should be inseparable from this offer and its proof. A content swap should break the page's logic.

**Experience:** the interface should create a specific encounter. The work leads; navigation supports it.

**Operate:** originality is useful only when it improves recognition, speed, confidence, or error prevention. A familiar table, form, modal, or sidebar is not a failure when it is the right task pattern. Decorative novelty that obscures state is a failure.

**Read:** originality may live in editorial rhythm, diagrams, navigation, or material character. It must not reduce comprehension or wayfinding.

## Template reflexes

Common AI patterns are warnings when the axis is free, not universal bans. A centered opening, card grid, system font, dark theme, or conventional app shell may be correct when the brief, content, platform, or mode earns it.

Apply an originality ceiling only when all are true:

1. the brief did not require the pattern;
2. the mode did not make it the clearest task structure;
3. the execution has no product-specific composition, interaction, or information logic;
4. the content could be replaced with another product's without redesign.

Do not redirect a clear user or brand commitment toward the evaluator's taste.

## Mode selection

Select mode from the requested surface and primary visitor action. When two modes appear plausible, choose the one governing the first successful session and record secondary needs in the surface brief.

Examples:

- A documentation home that mainly routes readers to answers: `read`, even if it includes a signup link.
- An onboarding flow inside an app: `operate`, even if it persuades users to enable a feature.
- A portfolio case-study index: `experience` when the work itself leads; `persuade` when the main goal is hiring conversion.

Mode changes require an explicit update to the surface brief. Do not silently change weights mid-run to manufacture a passing score.
