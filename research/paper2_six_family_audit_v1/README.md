# Paper II six-family robustness — execution receipt and auxiliary audit

Status: `CONFIRMATORY_EXECUTED__GATE_PASSED__GATE_SHOWN_NON_FALSIFIABLE`

Authority: same-context analysis. Not independent review. Promotes nothing.

## 1. What was executed

The frozen six-family robustness confirmatory packet was executed for the first
time. Freeze integrity was verified by blob hash before execution, on the
execution host, against `ROBUSTNESS_CONFIRMATORY_FREEZE_V1.json`:

| artifact | blob sha | matches freeze |
| --- | --- | --- |
| `research/empirical_10_of_10_v1/PAPER3/OBJECTIVE/ROBUSTNESS_REGISTRATION_V1.md` | `04fadc112a541f37060bef9f7f5116d5c83eda9c` | yes |
| `src/rakl/objective_transfer_robustness.py` | `33676013443e7e18942bf7050733e904f757e103` | yes |
| `scripts/paper2_robustness_confirmatory.py` | `58de8416a8d9743b042127c2460161008c7637d5` | yes |

Nothing frozen was modified. Result: `ROBUSTNESS_CONFIRMATORY_RESULT_V1.json`.

Seed `2026081212`, n = 810 (360 ACCEPT / 360 REJECT / 90 CANNOT_CHECK), six
registered extension families.

## 2. Registered gate outcome — PASSED

All frozen gates passed with `gate_reasons: []`.

| quantity | value | registered requirement |
| --- | --- | --- |
| positive family residuals | 6 / 6 | all six |
| exact two-sided sign test | `p = 0.03125` | `= 0.03125` |
| paired binary-Brier gain (mechanism − full) | `0.360` | `>= 0.05` MDE |
| item bootstrap 95% interval | `[0.3267, 0.3933]` | excludes zero |
| valid-transfer retention harm | none | `>= -0.02` per family |
| invalid false-accept harm | none | no worse per family |

Per family, `full_invalid_false_accept = 0.000` in all six.

## 3. Why this result must NOT be read as broad generalization

The auxiliary audit (`run_audit.py`, `results/SIX_FAMILY_AUDIT.json`) is not part
of the frozen registration. It adds falsifiers the registration does not contain.
Three of them are disqualifying for a generalization reading.

### 3.1 The `full` arm is the gold function (probe A)

`scripts/paper2_robustness_confirmatory.py` binds `"full": verify`, and `verify`
IS the gold. With `binary_probability(ACCEPT) = 0.98`, `binary_probability(REJECT)
= 0.02`, the full arm's Brier loss is a **constant 0.0004** on every decidable
item — measured variance `1.24e-37`.

The registered "paired" Brier gain is therefore not a paired comparison of two
predictors. It is the mechanism arm's absolute Brier loss minus a fixed constant.
One arm has no variance.

### 3.2 The sign test cannot fail (probe B)

Re-running the frozen `summarize()` on 12 arbitrary non-registered seeds
(`101 … 1212`) yields `positive_families = 6/6` and `p = 0.03125` and
`broad_known_world_robustness_supported = true` on **every single seed**.

The registered `p = 0.03125` is a property of the generator's item strata. It is
not evidence about cross-family generalization. A gate that no seed can fail is
not a test.

### 3.3 Two-thirds of the gain is construction, not measurement (probe F)

`mechanism_only` IS the `effect` coordinate. The frozen strata include item types
whose discriminating coordinate is by design not `effect`:

| item type | mechanism exact3 | share of total gain |
| --- | --- | --- |
| `BOUNDARY_QOI_MISMATCH` | **0.000** | 0.333 |
| `DIRECTION_REVERSED_INVALID` | **0.000** | 0.333 |
| `SEMANTIC_NEAR_MISS_INVALID_TRANSFER` | 0.500 | 0.167 |
| `INVALID_DISTANT_CONTROL` | 0.500 | 0.167 |
| `VALID_DISTANT_TRANSFER` | 1.000 | 0.000 |
| `VALID_NEAR_CONTROL` | 1.000 | 0.000 |

`mechanism_exact3` of exactly `0.000` — not 0.3, not 0.5 — is the signature of
construction. 66.7% of the headline advantage comes from strata built so the
control arm cannot see the discriminating coordinate. Family-level gains are
quantized at exactly `0.48` and `0.24`, the same signature.

## 4. What the run does legitimately establish

Two findings survive the above and are defensible.

### 4.1 The benchmark is not degenerate (probe D — equal-n null)

Coordinate-shuffle equal-n null, 200 reps: each task scored with a
ComponentAssessment drawn from a different task in the same family, preserving
the merge rule and the marginal coordinate distribution, destroying only the
task↔coordinate binding.

| | null mean | null 95% | observed `full` |
| --- | --- | --- | --- |
| exact3 | 0.407 | [0.379, 0.437] | 1.000 |
| valid_accept | 0.443 | [0.406, 0.475] | 1.000 |
| invalid_false_accept | 0.445 | [0.414, 0.489] | 0.000 |

Observed lies far outside the null. The coordinates carry task-specific
information; the gate is not merely conservative. This rules out one failure
mode. It does not touch §3.

### 4.2 Selectivity is not edge (probe C — clean trivial baseline)

| arm | exact3 | valid_accept | invalid_FA |
| --- | --- | --- | --- |
| `always_reject` | 0.444 | 0.000 | **0.000** |
| `always_accept` | 0.444 | 1.000 | 1.000 |
| `always_cannot_check` | 0.111 | 0.000 | 0.000 |
| `mechanism` | 0.593 | 1.000 | 0.750 |
| `relational` | 0.565 | 1.000 | 0.750 |
| `full` | 1.000 | 1.000 | 0.000 |

A trivial always-REJECT gate also attains `invalid_false_accept = 0.000`. Zero
false-accept alone is worthless as a claim. The defensible quantity is the
**joint** property — full retention at zero false-accept with correct abstention
— which no trivial arm attains.

Any Paper II sentence reporting false-accept reduction without the paired
retention number should be treated as unsupported.

## 5. New finding: one contract coordinate is near-inert (probe E)

Leave-one-coordinate-out on the six-coordinate contract:

| dropped | exact3 | invalid_FA |
| --- | --- | --- |
| `relation` | **0.990** | **0.000** |
| `qoi` | 0.944 | 0.125 |
| `boundary` | 0.944 | 0.125 |
| `direction` | 0.889 | 0.250 |
| `effect` | 0.880 | 0.250 |
| `precondition` | **0.825** | 0.250 |

Dropping `relation` costs 0.010 exact3 and zero false-accept on this benchmark:
it is nearly redundant here. `precondition` is the most load-bearing coordinate.

This is a genuine, non-tautological result about the contract's internal
structure, because it varies the candidate while holding the gold fixed. It
narrows the defensible claim from "six coordinates are necessary" to "five
coordinates carry the fail-closed behaviour on these six families; `relation`
is not separately load-bearing here."

## 6. Residual

The six-family extension is **executed but non-probative for generality**. To
make it probative the registration would need, in a new versioned epoch:

1. a `full` arm that is a predictor distinct from the gold function, so the
   primary statistic is genuinely paired;
2. item strata whose discriminating coordinate is sampled rather than assigned
   per stratum, so control-arm failure is measured rather than constructed;
3. a registered gate that some seed can fail, demonstrated by exhibiting one.

Until then the honest verdict is `SCOPED`, not `BROAD_GENERALIZATION`.

## 7. Reproduction

Execution host: laptop billy, `~/rakl-verify`, `.venv/bin/python` (3.11.14),
repo at `60654878`.

```
PYTHONPATH=src:. .venv/bin/python -m scripts.paper2_robustness_confirmatory
PYTHONPATH=src:. .venv/bin/python research/paper2_six_family_audit_v1/run_audit.py
```
