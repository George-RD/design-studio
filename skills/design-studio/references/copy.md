# Customer-facing copy

Use this reference when a surface adds or materially rewrites customer-facing copy. It does not replace product strategy or technical documentation.

## Authority

1. Current user instruction.
2. Confirmed facts and claim boundaries in `PRODUCT.md`.
3. Voice, terminology and journey rules in `COPY.md` when present.
4. The current surface brief.
5. Incumbent copy as a baseline, not automatic authority.

Never weaken a legal, factual or commercial qualification to make a line shorter.

## Existing copy

Freeze the incumbent before rewriting. A candidate replaces it only when it improves the important jobs without introducing a trust, action or factual regression.

Compare:

- audience recognition;
- category clarity;
- mechanism clarity;
- specificity;
- action clarity;
- claim discipline;
- voice and memorability.

A lower reading grade or shorter sentence count does not choose the winner by itself.

## Drafting rules

- Put the point in the first one or two lines.
- Use one main idea per sentence.
- Prefer concrete nouns and active verbs.
- Name the buyer, problem, action, number or mechanism when evidence supports it.
- Keep short customer-facing copy free of em dashes.
- Cut inflated significance, filler, vague authority and generic AI vocabulary.
- Avoid repeated contrast formulas, padded groups of three and identical section rhythms.
- Preserve necessary product and technical terms.
- Use one spelling convention. Default to British English unless the project says otherwise.

## Gates

Every changed version must pass:

- **Position**: at least one line says something a reasonable person could challenge.
- **Read aloud**: it sounds like a person, not a press release or chatbot.
- **Specificity**: a nearby product cannot inherit it by swapping one noun.
- **Action**: the right reader knows what to do next.
- **Trust**: every claim stays inside the evidence.

For a public landing page, also test a three-second skimmer, a right-fit sceptic and a wrong-fit reader. Keep at least one judgement outside deterministic lint.

## Growth Arsenal integration

When `business-copy-style` is installed, use its current brief, de-AI, lint and paired-evaluation flow. Record `copyWorkflow: business-copy-style` in `capabilities.json`.

When it is absent, apply this reference and record `copyWorkflow: local-rules`. Do not claim the external workflow ran.
