# Document pagination lens

Inspect the complete ordered page set. Pagination is part of composition, not a renderer afterthought.

Check:

- headings are not orphaned from the content they introduce;
- short terminal lines/widows do not create avoidable visual damage;
- keep-together groups such as totals, signatures, notes and figure/caption pairs remain coherent;
- tables repeat headings when needed and clearly indicate continuation across pages;
- page breaks respect section hierarchy and do not create accidental near-empty pages;
- continuation state is explicit when a reader must carry context to the next page;
- break priorities preserve comprehension before decorative balance.

A finding uses:

```json
{"lens":"pagination","severity":"primary|advisory","confidence":"high|medium|low","summary":"...","evidence":{"page":2,"zone":"...","observation":"..."},"status":"open"}
```

Use `primary` when a break changes meaning, separates required context, obscures continuation or materially harms professional reading. Use `advisory` for local balance that does not impede comprehension. Do not prescribe renderer-specific CSS/DOCX/PDF code.
