# Paper IV Phase-1 v1 — root-cause analysis (generator defect)

The v1 Phase-1 result (no state-dependent residual; 2/3 families at exactly 0.5 for every
model) is an **instrument/generator defect**, not a valid test of the mechanism.

## Evidence (local diagnostic, Qwen2.5-0.5B, `balance_conservation`)
- The training pool of 66 examples contains only **2 unique rendered inputs**: every VALID is
  identical (`inflow:10, outflow:4, store:6`), every INVALID is identical (`store:5`).
- Predictions are a **constant** regardless of training strength:
  - base model → all `INVALID`; weak trainer (r8,3ep,1e-4) → all `VALID`; strong trainer
    (r16,20ep,5e-4) → **still all `VALID`** → accuracy 0.5 on the balanced probe.
- So "training" attempts to memorize a **one-token difference** (6 vs 5) on two near-identical
  strings and collapses to a constant. There is no distribution from which to induce a rule.
- `state_reachability` "learned" only because its VALID inputs are **longer** (2 edges vs 1) —
  a length artifact, not structural learning.

## Ruled out
Scoring length-bias (both labels are single tokens); loss target (prompt correctly masked);
train/probe leakage (`assert_disjoint`); trainer strength (strong config still constant).

## Fix
A v2 generator with **varied instances per family** (genuine rules, length-matched valid/invalid,
train and probe from **disjoint instances** → rule generalization not memorization) + a
**learnability positive-control gate** (a model must clear the base task before any "no residual"
verdict). v1 is preserved as negative history; v2 is re-frozen and re-run.
