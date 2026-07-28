# Influences and merge rationale

Design Studio v2 was developed by comparing this repository with [Impeccable](https://github.com/pbakaus/impeccable).

The useful overlap was not another collection of design prompts. It was a set of operating disciplines:

- durable product, design, and surface context;
- explicit preserve-versus-replace semantics;
- surface modes that change what quality means;
- deterministic checks for mechanical defects;
- bounded visual verification instead of open-ended polishing;
- a clear distinction between product truth and visual invention.

Those ideas are adapted here to Design Studio's existing architecture. Design Studio keeps the parts that are structurally different and load-bearing:

- a DesignAgent that never sees source code;
- an Evaluator that judges only the live rendered experience;
- a Builder that executes rather than chooses the visual direction;
- explicit refinement and aesthetic pivot paths;
- codification of a shipped direction into reusable design context.

No Impeccable source files are vendored into this package. The implementation and wording are original to Design Studio. Impeccable remains Apache-2.0; Design Studio remains MIT.

## Rejected merge paths

### Copy the entire command catalog

Rejected. It would turn Design Studio into a second Impeccable and obscure the core multi-agent proposition. Design Studio keeps three public commands: initialize context, create/overhaul, and review/polish.

### Keep eight-to-twelve iterations as the default

Rejected. Long loops are useful only for genuinely ambitious work. Default verification is now bounded, with an explicit ambitious profile when the expected value justifies the cost.

### Apply the same originality pressure to every interface

Rejected. Marketing and experiential surfaces benefit from high originality pressure. Operational and reading surfaces should not be punished for using familiar patterns that improve task completion or comprehension.

### Treat a clean static scan as design evaluation

Rejected. Deterministic checks and live judgment solve different problems. Preflight can block broken work, but only the code-blind browser evaluator may score the rendered experience.

### Ship the best available result when the budget expires

Rejected. Budget exhaustion is not evidence of quality. A result below its mode floors, with open blockers, or without live evaluation ends in `HOLD`. It may be delivered as a preview, but it is not promoted as shipped design truth.
