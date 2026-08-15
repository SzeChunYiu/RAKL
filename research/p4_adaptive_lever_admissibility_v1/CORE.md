# P4 adaptive-vs-static — the lever's own precondition is unsatisfiable

**The negative is not revivable by its recorded lever.** Both halves of that lever have already been
measured and neither works, and the precondition it attaches — *"but only on an admissible
instrument"* — cannot be met on this instrument.

No new execution. Every number below is read from artifacts already on `main`.

## The lever

> coverage floor as constraint not budget target; fix within-round concentration — **but only on an
> admissible instrument**

## Both halves are already measured, in the lane's own attribution receipt

`research/paper4_allocator_attribution_v1/ATTRIBUTION_RECEIPT.json`:

| Field | Value | What it means for the lever |
|---|---|---|
| `predictions.P1_budget_capture_is_dominant` | **false** | the coverage-floor half is *not* the dominant cause |
| `fraction_of_gap_closed_by_budget_capture_lever` | 0.349 | capping it recovers about a third |
| `fraction_of_gap_closed_by_concentration_lever` | **−0.234** | the concentration half makes it **worse** |
| `predictions.P2_concentration_is_not_dominant` | true | consistent with the above |

Fixing within-round concentration is not a repair — it is measured as negative.

## The precondition cannot be met

Same receipt, unambiguously:

```text
instrument_terminal            = INSTRUMENT_CANNOT_DISCRIMINATE
frozen_parent_hard_gate_E_minus_D_min = 0.05
predictions.P3_instrument_ceiling_below_its_own_gate = true
can_promote_a_mechanic         = false
```

And the ceiling itself, recomputed as the sibling reproduction control inside
`research/paper3_lift_ceiling_qualification_v1/CEILING_RECEIPT.json`:

```text
published_tier3_upper_bound   = 0.024570935346802252
recomputed_tier3_upper_bound  = 0.024570935346802103
```

The rigorous harm-free upper bound is **0.0246** against a hard gate of **0.05**. Even a perfect
adaptive allocator falls roughly a factor of two short. The programme made this comparison itself —
`P3_instrument_ceiling_below_its_own_gate` is recorded as a prediction that held — and the sibling
control reproduces the bound to 1.5e-16.

So *"only on an admissible instrument"* is not a caveat that a better repair could satisfy. On this
instrument it is unsatisfiable, and no allocation-policy fix changes a ceiling.

## Consequence

`p4-adaptive-lost-to-static` should leave the revivable set. Its revival requires an instrument with
a ceiling above its own gate — a **new instrument**, hence a new epoch with its own freeze, not a
repair of the allocation policy.

## What this does not say

It does not retract the development negative, which stands. It does not claim adaptive allocation
cannot work — only that **this instrument cannot show it either way**, which is what
`INSTRUMENT_CANNOT_DISCRIMINATE` already says. Nothing here is new evidence; it is two committed
numbers put side by side against a lever that predates their comparison.
