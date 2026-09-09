# Accepted-system scenarios

`scenarios.json` is the frozen expected effect/publication matrix for issue #93.
`test_system_lifecycle.py` constructs actual profile and consumer text through the
installed exporter, supplies synthetic accepted-tree evidence to the public
lifecycle operations, and verifies the final receipt against this matrix.

These fixtures prove acceptance binding, deterministic parity and publication or
restoration readback. They are not screenshots, client design defaults, live host
acceptance, or fault-injected filesystem transactions. Host execution and rendered
dogfood remain the #97 release-proof boundary.
