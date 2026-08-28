# Deepening

How to deepen a cluster of shallow modules safely, given its dependencies. Assumes the vocabulary in [SKILL.md](SKILL.md): **module**, **interface**, **seam**, **adapter**.

## Dependency categories

### 1. In-process

Pure computation or in-memory state. Merge shallow modules and test through the new interface directly.

### 2. Local-substitutable

Dependencies with local test stand-ins. Test the deepened module with the stand-in behind an internal seam.

### 3. Remote but owned

Define a port at the seam. The deep module owns the logic; production and in-memory/test adapters satisfy it.

### 4. True external

Inject the external dependency behind a small port and use a mock adapter at the true system boundary.

## Seam discipline

- One adapter means a hypothetical seam; two adapters means a real one.
- Internal seams may exist inside a deep module without being exposed through its external interface.

## Testing strategy: replace, don't layer

Once tests exist at the deepened module's interface, delete obsolete shallow-module tests. Assert observable outcomes through the interface, not internal state.
