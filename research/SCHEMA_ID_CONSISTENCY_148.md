# Schema `$id` consistency — issue #148

Status: `IMPLEMENTATION_CONSISTENCY_DEFECT / NO_SCHEMA_CHANGE_MADE / OWNER_DECISION_REQUIRED`

## Measured state (origin/main = `787c7e0`)

Reproduced by `python scripts/audit_schema_id_consistency.py`:

```
schema_count: 96
namespace_count: 4
namespaces:
   59  https://github.com/SzeChunYiu/RAKL/schemas
   32  https://example.invalid/rakl
    4  https://rakl.dev/schemas
    1  https://rakl.example/schemas
```

All 96 schemas carry a `$id` and every `$id` filename component matches its file
basename, so the only live defect is the 4-way namespace split. Counts have drifted
from the issue's snapshot at `bd1a2768f0` (52/32/2/1): the GitHub base grew to 59 and
the `rakl.dev` base grew from 2 to 4. The split itself is unchanged.

## What this change does

- Adds `scripts/audit_schema_id_consistency.py` — a stdlib-only regression checker
  that asserts `$id` exists, extracts the base, checks the filename component, and
  reports the namespace split. Exits nonzero on missing `$id`, foreign base vs a
  frozen expected base (`--expected-base`), filename mismatch, or a split
  (`namespace_count != 1` without `--expected-base`).
- Adds `tests/test_schema_id_consistency.py` — frozen-world tests under `tmp_path`
  (missing `$id`, foreign base / split, foreign base vs `--expected-base`, filename
  mismatch, clean control that must NOT fire) plus one `xfail(strict=True)` test that
  runs the checker against the real `schemas/`.

## What this change deliberately does NOT do

No `$id` value is changed. Choosing the canonical base is an owner decision: existing
artifacts/receipts may quote current `$id` values, and rewriting identities in
frozen/immutable artifacts is forbidden. The checker selects no winner and grants no
authority. See the issue's "Deliberately not done" section.

## xfail rationale

The real-`schemas/` test asserts the checker passes (`returncode == 0`). Today the
family is split, the checker exits 1, the assertion fails → **XFAIL** (green for CI).
When an owner unifies the bases to one, the checker exits 0, the assertion passes →
**XPASS**, and `strict=True` turns that red, forcing removal of the marker at the same
time the defect is closed. This documents the defect in the suite without going red.

## Owner-decision options (from the issue)

1. Adopt the GitHub base (`https://github.com/SzeChunYiu/RAKL/schemas`) — points at a
   real location but not a served schema document, and is unstable under a repo/org
   rename (the hard prerequisite for the Class-3 analysis in #137).
2. Adopt a controlled domain (e.g. `https://rakl.dev/schemas`) — stable under rename
   but requires the project to actually control the domain.
3. Adopt a non-resolvable stable URN — stable and rename-proof, at the cost of never
   resolving to a served document.

The checker supports all three via `--expected-base URL` once one is chosen.
