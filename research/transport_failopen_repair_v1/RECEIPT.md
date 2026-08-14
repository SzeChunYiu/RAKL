# Receipt: assess_transfer_v2 fail-open repair (transport_failopen_repair_v1)

Date: 2026-08-14
Branch: `solver/transport-fail-closed` (based on origin/main `6c94030f`)
Finding repaired: L3 `FAIL_OPEN_FOUND`, frozen in `research/framework_ladder/ladder.json`
(2026-08-14 reproduction). The frozen ladder entry is history and is intentionally
NOT edited by this repair.

## Defect

`assess_transfer_v2` in `src/rakl/structural_transport_v2.py` classified the decision as

```python
if violations:
    decision = TransferDecision.REJECTED
elif unknowns:
    decision = TransferDecision.CANNOT_CHECK
else:
    decision = TransferDecision.LICENSED
```

where `violations` and `unknowns` are filtered from the load-bearing obligation set
(REQUIRED or FORBIDDEN requirement). When that set is **empty** — zero obligations, or
OPTIONAL-only obligations — both lists are vacuously empty and the gate returned
`LICENSED` with **zero reasons**. Wholly disjoint structures (no shared roles,
relations, invariants, or QoI) were licensed for transport. Fail-open: absence of
evidence licensed instead of blocking.

## Exact before/after behavior

| Input | Before | After |
|---|---|---|
| Empty obligation tuple, disjoint structures | `LICENSED`, `reasons=()` | `CANNOT_CHECK`, `reasons=("empty_load_bearing_obligation_set",)` |
| OPTIONAL-only obligations (empty load-bearing set) | `LICENSED` (optional rationale codes only in reasons) | `CANNOT_CHECK`, `reasons=("empty_load_bearing_obligation_set", *optional_non_satisfied_codes)` |
| Any witness with >= 1 load-bearing obligation | unchanged | **bit-identical** (decision branch and reasons computation untouched for non-empty sets) |
| Identity/context mismatch | `CANNOT_CHECK` (identity reasons) | unchanged |

Vocabulary choice: `CANNOT_CHECK`, not `REJECTED`, and no new enum member. The gate's
own contract states REJECTED requires a *demonstrated violation*; an empty obligation
set demonstrates nothing — it is unresolved absence of evidence, which is exactly the
module's CANNOT_CHECK case. Explicit reason string: `empty_load_bearing_obligation_set`.

## Change

- `src/rakl/structural_transport_v2.py`:
  - `assess_transfer_v2` returns `CANNOT_CHECK` with reason
    `empty_load_bearing_obligation_set` (prepended to any optional-obligation
    non-satisfied rationale codes) when the load-bearing obligation set is empty,
    before the violations/unknowns/licensed branch. Traces are preserved.
  - Docstring documents the empty-set fail-closed rule and cites the frozen finding.
- `tests/test_structural_transport_v2.py`, hostile tests added:
  - `test_empty_obligation_set_fails_closed_on_disjoint_structures` — the original
    defect reproduction: disjoint structures + empty obligations -> NOT LICENSED,
    `CANNOT_CHECK`, explicit reason present.
  - `test_optional_only_obligations_fail_closed` — OPTIONAL-only set fails closed.
  - `test_licensed_always_carries_a_satisfied_load_bearing_obligation` — the
    LICENSED-with-zero-reasons path is dead: any LICENSED assessment traces >= 1
    satisfied load-bearing obligation.
  - `test_no_alarm_legitimate_licensing_unchanged` — no-alarm control: a legitimate
    satisfied-obligation case still returns LICENSED with empty reasons and all
    traces SATISFIED, exactly as before the repair.
- No other files changed. `research/framework_ladder/ladder.json` untouched (frozen).

## Test evidence

Single targeted invocation (no xdist, no full suite):

```text
$ uv run pytest tests/test_structural_transport_v2.py tests/test_structure_space.py -p no:xdist -q
...............................                                          [100%]
```

31/31 passed (12 transport incl. 4 new hostile tests; 19 structure_space), exit 0.
All 8 pre-existing transport tests pass unchanged — non-empty-obligation behavior
verified bit-identical.

## Pin check

Searched `src/rakl/`, `schemas/`, `.github/workflows/`,
`docs/EVALUATOR_DEPENDENCY_PINNING.md` for `structural_transport_v2`:

- `docs/EVALUATOR_DEPENDENCY_PINNING.md`: no entry for this module.
- `schemas/`, `.github/workflows/`, other `src/rakl/` modules: no references.
- `research/empirical_10_of_10_v1/PAPER3/OBJECTIVE/{VERIFIER_BINDING.json,MACHINE_WITNESS_PROTOCOL.json,PROTOCOL.md}`
  and campaign scoreboards reference the module **by path only** — no content hash,
  no pin fields. Not a pinning mechanism; nothing to update, nothing silently broken.

Result: NOT hash-pinned. No pin update required.

## Call-site workaround status

`src/rakl/structure_space.py` (`match`, module docstring lines ~21-25) rejects
zero-satisfied-obligation candidates at its own layer. That workaround **remains in
place, unedited**. With the gate now failing closed it is redundant-but-harmless and
is deliberately kept as defense in depth; its docstring's account of the 2026-08-14
finding is historical record and stays. All 19 `tests/test_structure_space.py` tests
pass unchanged.

## Residuals

- `research/orion_architecture_audit_v1/AUDIT.md` row 7 states "FAIL_OPEN live" for
  this module; after this branch merges that row is stale. Audit doc update is a
  separate documentation fiber, not performed here (out of scope for the gate repair).
- Ladder promotion (recording the repair against the frozen FAIL_OPEN_FOUND finding)
  is governance-gated by the parent session; nothing here self-promotes.
