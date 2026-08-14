# Active-CANNOT_CHECK Repair Cross-Reference

## Status
FROZEN -> Referenced to #685 (Registry/gate reconciliation sweep)

## Issue
- #685: Registry/gate reconciliation sweep (successor NETBEN placeholders, missing claim rows, issue relinks, ledger scoping)

## What this means
The active-CANNOT_CHECK repair experiment is frozen. Any registry/gate reconciliation work related to CANNOT_CHECK verdicts is tracked under issue #685, which serves as the single-writer for registry bookkeeping completion.

## Related work
- PR #691 (registry single-writer) is in flight - this handles the PROMOTION_GATE.json and ATOMIC_CLAIM_REGISTRY.json reconciliation.
- No duplicate work should be started; all registry rows are managed through #685.
