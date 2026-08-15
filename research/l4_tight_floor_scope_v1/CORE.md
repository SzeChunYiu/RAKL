# L4 tight resource floor — scope check

**This record is not a negative result about the mechanism.** It is a stratum the protocol declared
outside the claim *before execution*, and both arms scoring zero there is what that declaration
predicts.

Two findings, both verified against committed artifacts.

## 1. The tight stratum is protocol-excluded, in the protocol's own words

`research/benefit_L4_navigation_v1/PROTOCOL.json`, `corpus.budget_classes`:

```text
TIGHT   budget_units = 2 * S*  (zero-waste distillation is just fundable; outside PROMOTE scope)
MEDIUM  budget_units = 4 * S*  (primary PROMOTE regime)
LOOSE   budget_units = 8 * S*  (secondary; non-inferiority gate)
```

At `2·S*` the budget exactly funds a perfect, zero-waste solution. **Any** method carrying overhead
fails by arithmetic, and the protocol says so — *outside PROMOTE scope* — in the same sentence that
defines the class.

So `sr_a_tight = sr_b_tight = 0.0` is not evidence about distil-and-navigate. It is a stratum whose
support for distinguishing any two realistic arms is zero by construction. The record's own
attribution already says *"by construction... a designed floor, not an instrument defect"*; what was
missing is that the protocol pre-declared the exclusion, which turns "designed floor" into "outside
the registered claim".

The positive half of the same run is untouched and remains strong: arm B solves every registered
medium/loose primary world (`sr_b = 1.0` vs `sr_a = 0.3226`, McNemar `p = 1.2e-63`, discordant
210/0, both null models far below).

## 2. The record's one unconfirmed number is now confirmed

The frontier record states:

> the receipt records the tight-stratum solve rates but not the stratum size in its summary block,
> so the count is quoted from the manuscript and not independently confirmed here

It is confirmable — from two artifacts the summary block does not include:

| Source | Value |
|---|---|
| `PROTOCOL.json` → `corpus.composition.N2_deep_chain_tight` | **60** |
| `results_v1/per_class_breakdown.json` → `budget_TIGHT.n`, both arms | **60** |

The manuscript's "60-world resource floor" is therefore independently confirmed. That verification
gap is closed.

## Consequence

`p1-l4-tight-resource-floor` should not be counted in the revivable set. Its lever — *extending the
mechanism into the tight-budget regime is a new epoch* — is correct precisely because there is
nothing to revive: a new epoch would be a **new claim** about a regime the original protocol
excluded, not the repair of a failed one.

## What this does not say

It does not retract the record, which honestly reports what the run produced. It does not claim the
mechanism would succeed at `2·S*` — nothing here tests that, and the arithmetic suggests only a
zero-waste method could. It does not touch the positive half of the run.
