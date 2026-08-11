# Schema `$id` consistency — issue #148

Status: `OWNER_DECISION_LANDED (#184) / CLI_REGRESSION_CHECKER_ADDED`

## Measured state (origin/main after #184 = `5816452`)

Reproduced by `python scripts/audit_schema_id_consistency.py`:

```
schema_count: 96
namespace_count: 1
namespaces:
   96  https://github.com/SzeChunYiu/RAKL/schemas
findings: none
```

#184 unified the previous 4-way split onto the frozen GitHub schemas base. This PR
adds a standalone CLI regression checker plus planted-world tests so the same
defect class cannot reopen without a failing operator-facing tool.

## What this change does

- Adds `scripts/audit_schema_id_consistency.py` — a stdlib-only regression checker
  that asserts `$id` exists, extracts the base, checks the filename component, and
  reports any namespace split. Exits nonzero on missing `$id`, foreign base vs a
  frozen expected base (`--expected-base`), filename mismatch, or a split
  (`namespace_count != 1` without `--expected-base`).
- Adds `tests/test_schema_id_consistency.py` — frozen-world tests under `tmp_path`
  (missing `$id`, foreign base / split, foreign base vs `--expected-base`, filename
  mismatch, clean control that must NOT fire) plus a real-`schemas/` regression
  that pins `--expected-base https://github.com/SzeChunYiu/RAKL/schemas`.

## What this change deliberately does NOT do

No `$id` value is rewritten here (that landed in #184). The checker still grants no
theorem/mechanism authority; it is measurement/regression only.

## Relation to `tests/test_schema_id_uniformity.py`

The in-suite uniformity guard from #184/#0772e74 remains the pytest-facing
sentinel. This checker is the operator-facing CLI twin: same defect class, same
canonical base, usable outside pytest and emit-able as JSON for receipts.

## Frozen canonical base

`https://github.com/SzeChunYiu/RAKL/schemas` (no trailing slash in the checker’s
base extraction; `$id` values keep the trailing `/` before the filename).

Enforce with:

```bash
python scripts/audit_schema_id_consistency.py \
  --expected-base https://github.com/SzeChunYiu/RAKL/schemas
```
