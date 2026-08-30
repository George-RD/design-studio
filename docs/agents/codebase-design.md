# Codebase design composition

Apply this repository-owned rule in addition to upstream `codebase-design`.

Before deleting shallow-module tests, map each test to equivalent observable coverage at the deeper interface, including edge cases and failure behavior. Delete a test only when its protected behavior is demonstrably covered through the deeper seam. Retain tests for behavior the deeper interface intentionally cannot expose or verify.
