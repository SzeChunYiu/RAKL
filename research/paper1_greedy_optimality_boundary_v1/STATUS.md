# Greedy Optimality Mechanization Boundary

## Status
PARTIALLY_MECHANIZED - 84 axiom-free theorems (3 ingredients mechanized, assembly not mechanized)

## Location
- Branch: origin/formal/paper1-greedy-ingredients
- Commit: b86bef97

## What is mechanized
1. sum_swap_ge - the exchange step
2. exchange_partner_exists - the counting step
3. top_subset_optimal - top-k optimality

## What is NOT mechanized
The assembly (iterating exchange across partitions, splitting objective)

## Honest verdict
PARTIALLY_MECHANIZED at 84 theorems. Every non-trivial ingredient is machine-checked; only assembly is not.
