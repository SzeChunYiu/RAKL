# Paper IV instrument-admissibility gate v1

Executes the sealed revival packet
`../paper4_allocator_attribution_v1/PACKET_oracle_ceiling_calibration_gate_v1.json`
(sha256 `d318363d…`): a pre-execution admissibility gate for equal-budget
allocation-comparison instruments, `ceiling ≥ κ·MDE` with κ frozen before ceiling access.

Nothing here promotes, revives or reverses any terminal. `grants_scientific_authority=false`
everywhere. The parent negative and every existing freeze are byte-unchanged.

## Files

| File | Role |
|---|---|
| `KAPPA_FREEZE_V1.json` | κ=1.2 frozen + fresh-assurance case ids/seed/expected verdicts, declared before any fresh ceiling was computed |
| `GATE_ASSURANCE_RECEIPT.json` | 5/5 fresh-assurance verdicts match the frozen expectations; same-system ablation |
| `GATE_FALSIFIABILITY_AUDIT.json` | Per-condition black-box audit (`src/rakl/gate_falsifiability.py`), control first, expected SENSITIVE/INSENSITIVE declared pre-execution — all conditions pass |
| `REFERENCE_INSTRUMENT_ADMISSIBILITY.json` | Formal verdict on the preserved development-stress instrument: **INADMISSIBLE**, licensed by the tier-3 upper bound, κ-insensitive for κ > 0.4914 |

Gate: `src/rakl/instrument_admissibility.py` (+ `tests/test_instrument_admissibility.py`,
one test per packet counterexample). Runner:
`../../experiments/orion_closure/run_p4_instrument_admissibility_assurance.py`.

## Direction-of-license rules (the mechanic)

- only a rigorous **upper** bound may license `INADMISSIBLE`;
- only an achievability (lower/exact) bound may license `ADMISSIBLE`;
- uncomputable oracle, unequal budget, missing/inconsistent/too-loose bounds → `CANNOT_CHECK` (fail closed);
- κ and MDE are frozen before ceiling access; no verdict is upgradeable by arm-outcome access.

## Fresh assurance (seed 202608141101, disjoint from all development seeds)

| case | verdict | licensing evidence |
|---|---|---|
| `FRESH_DEGENERATE_ZERO_HEADROOM` | INADMISSIBLE | exact ceiling 0 (singleton allocation space) |
| `FRESH_STATE_DIVERGENT_INITIAL_MASTERY_HIGH_HEADROOM` | ADMISSIBLE | constructive lower bound +0.0823 ≥ 1.2·0.05 |
| `FRESH_NONSEPARABLE_CROSS_COORDINATE_SYNERGY` | ADMISSIBLE | lower bound only (+0.1078); no separable relaxation exists — gate works without any upper bound |
| `FRESH_UNCOMPUTABLE_ORACLE_STUB` | CANNOT_CHECK | claimed +0.40 headroom refused: no computable oracle |
| `FRESH_CEILING_MARGINALLY_ABOVE_MDE` | INADMISSIBLE | exact ceiling 0.0501 ∈ (MDE, κ·MDE); would flip only for κ ≤ 1.002 — the frozen-κ no-rescue case |

## Audit corrections (preserved)

The first audit run produced two false alarms from the **probe harness**, not the gate:
independent per-bound scale factors created lower > upper evidence, which the gate
correctly refused as `CANNOT_CHECK`. Attribution: one stage (probe construction).
The probe was repaired to a shared scale draw; the gate was not changed. Recorded in
the runner docstring for `_map_bounds`.

## Same-system ablation (packet obligation)

Dropping the tier-3 upper bound from the reference evidence — leaving only the
strongest implementable policy scores — flips INADMISSIBLE → CANNOT_CHECK in 32/32
trials. The upper-bound component carries the mechanic; the novelty residual is
**not** withdrawn.

## What this licenses next

The frozen development-stress instrument would not have been licensed for
confirmatory execution. Any successor allocation comparison must first obtain
`ADMISSIBLE` from this gate under `KAPPA_FREEZE_V1` before outcome access.
