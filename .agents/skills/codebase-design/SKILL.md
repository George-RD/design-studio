---
name: codebase-design
description: Shared vocabulary for designing deep modules. Use when the user wants to design or improve a module's interface, find deepening opportunities, decide where a seam goes, make code more testable or AI-navigable, or when another skill needs the deep-module vocabulary.
---

# Codebase Design

Design **deep modules**: a lot of behaviour behind a small interface, placed at a clean seam, testable through that interface. Use this language and these principles wherever code is being designed or restructured. The aim is leverage for callers, locality for maintainers, and testability for everyone.

## Glossary

**Module**: anything with an interface and an implementation.

**Interface**: everything a caller must know to use the module correctly: type shape, invariants, ordering constraints, error modes, required configuration and performance characteristics.

**Implementation**: what's inside a module.

**Depth**: leverage at the interface. A module is deep when a large amount of behaviour sits behind a small interface.

**Seam**: a place where behaviour can vary without editing in that place; the location at which a module's interface lives.

**Adapter**: a concrete thing that satisfies an interface at a seam.

**Leverage**: capability callers get per unit of interface they learn.

**Locality**: concentration of change, bugs, knowledge and verification in one place.

## Principles

- Depth is a property of the interface, not the implementation.
- The deletion test: if deleting a module makes complexity vanish, it was probably pass-through; if complexity spreads to callers, the module was earning its keep.
- The interface is the test surface.
- One adapter means a hypothetical seam; two adapters means a real one. Do not introduce a seam unless something actually varies across it.
- Prefer small interfaces that hide complexity and accept dependencies rather than constructing them internally.

See [DEEPENING.md](DEEPENING.md) for dependency/seam strategy and [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md) when alternative interfaces should be explored deliberately.
