# Round 004 CI repair

Classification: **Class A test-isolation defect**.

After round 004 appended `verified_failure_constraint_compilation_v1` to the shared `packets/` directory, the historical round-001 test failed because it globbed every packet in the append-only directory and asserted the entire directory still equalled the six round-001 variants.

The repair changes only the test scope:

- round-001 semantic assertions now select the six frozen round-001 variant IDs explicitly;
- a separate global assertion checks packet variant IDs remain unique and that the round-001 set remains present;
- no round-001 or round-004 packet content, hash, hypothesis, parent, metric, threshold, outcome or authority field is changed.

This note exists to trigger and bind exact-head CI after the repair. It creates no scientific or promotion evidence by itself.
