# Bounded-saturation NULL — power re-analysis

**Terminal: `UNDERPOWERED`.** The recorded NULL reports the study's resolution, not the mechanic's
absence.

Pure re-analysis of numbers already committed in `research/orion_saturation_solve_enablement_v1/`.
No new data, no new execution, no model. The decision rule was stated before computing.

## What the study did

112 held-out Mathlib theorem-proving tasks under Lean adjudication. Saturation arm 0.357, matched
uniform arm 0.3125, gold coverage essentially equal (0.342 vs 0.349) so the arms were genuinely
matched. Discordant pairs **8 vs 3**, exact McNemar two-sided **p = 0.2266**. Filed `NULL`.

## Reproduction control

Recomputed exact McNemar on (8, 3): **p = 0.2266**, matching the receipt. Nothing below is reported
unless this holds.

## The power

| | |
|---|---|
| discordant pairs collected | **11** |
| smallest majority reaching α=0.05 at n=11 | **10 of 11** |
| power at the observed effect | **0.154** |
| discordant pairs needed for 80% power | **37** |
| tasks needed at the same discordance rate | **~377**, against the 112 used |

With eleven discordant pairs the study could only have reached significance if **ten of them fell
one way**. That is a far larger effect than the one hypothesised. At the effect it actually
observed, the design had a **15% chance** of detecting it.

## What follows

The mechanic was not shown ineffective. The design could not distinguish the hypothesised benefit
from chance, and a NULL filed from a 15%-powered test carries almost no evidential weight against
the mechanic.

`UNDERPOWERED` is a registered terminal in this programme precisely for this case.

## What this does not say

- **It does not show the mechanic works.** The point estimate favours saturation; the study cannot
  support that either, and a 4.5-point difference on 112 tasks is exactly what noise looks like.
- **It does not retract the NULL**, which was correctly filed against its own protocol. The protocol
  simply did not include a power analysis.
- **It does not license re-running the same design at larger n** without a fresh freeze.

## Consequence for the frontier

The record's lever — *frozen revival as a separate epoch* — is correct but understated. The revival
needs a **powered** design, and the requirement is now computed rather than guessed: 37 discordant
pairs, on the order of 377 tasks. That is a 3.4x scale-up, which moves this record from
`REVIVABLE_LOCAL` toward the resource-bound boundary and should be re-classed accordingly by whoever
maintains the inventory.

## Reproduce

```bash
python research/orion_saturation_power_reanalysis_v1/run_power_reanalysis.py
```
