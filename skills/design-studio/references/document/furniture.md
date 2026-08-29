# Document furniture lens

Furniture is repeated page-system structure: title zone, metadata strip, running header/footer, page number, status/version/confidentiality treatment and acceptance/signature/payment zones.

Check:

- required furniture is present where the brief says it must be;
- repeating furniture is stable enough to orient without competing with body content;
- page numbers, document IDs, dates, versions and statuses are legible and consistently placed;
- confidentiality/status emphasis matches consequence rather than becoming decoration;
- signature, acceptance or payment blocks have sufficient space and clear association with the relevant terms/content;
- first/last page exceptions are intentional and do not break wayfinding.

Finding shape:

```json
{"lens":"furniture","severity":"primary|advisory","confidence":"high|medium|low","summary":"...","evidence":{"page":3,"zone":"footer","observation":"..."},"status":"open"}
```

Do not invent missing IDs, dates, statuses, names, signatures or commercial fields. Report the visual/system gap and hand content truth back to its owning domain.
