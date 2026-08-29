# Document print and legibility lens

Evaluate the artifact as pages that may be read on screen, printed in colour, or printed in grayscale.

Check:

- body, metadata, table and annotation text remain legible at intended physical size;
- hierarchy survives grayscale and does not rely on colour alone;
- light rules, fills and low-contrast text remain distinguishable on ordinary office printing;
- large ink-heavy areas are intentional and do not make working documents impractical;
- small type, fine line weight and reversed text are used only when robust at print scale;
- figures/callouts preserve labels and source-note association under reduced colour;
- paper/ink roles enhance reading rather than imitating a website background literally.

Finding shape:

```json
{"lens":"print","severity":"primary|advisory","confidence":"high|medium|low","summary":"...","evidence":{"page":2,"zone":"metadata","observation":"..."},"status":"open"}
```

Use host-supplied deterministic contrast/print facts when available, but visual judgement remains source-blind. A renderer-specific workaround is implementation advice, not part of this lens.
