# Document tables and dense-data lens

Judge tables, totals, financial/operational rows and dense metadata as reading structures.

Check:

- row/column hierarchy is immediately scannable and headers remain attributable;
- numeric values align consistently, with tabular treatment where comparison matters;
- currency/unit/decimal treatment is unambiguous and totals/subtotals are visually distinct without decoration overload;
- long labels wrap without breaking row association;
- repeated headings and continued tables preserve context across pages;
- dense metadata uses spacing, rules and typographic contrast rather than generic cards;
- no value is clipped, hidden in print, or separated from a qualifier/source note that changes meaning.

Finding shape:

```json
{"lens":"tables","severity":"primary|advisory","confidence":"high|medium|low","summary":"...","evidence":{"page":1,"zone":"financial-table","observation":"..."},"status":"open"}
```

Use `primary` for ambiguity, clipping, broken attribution, unreadable density or misleading totals. Visual evaluation never verifies accounting correctness unless a separate deterministic/content authority supplied that fact.
