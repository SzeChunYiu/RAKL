# R002 — MCSP threshold transport and complexity amplification

**State:** ACTIVE PRIMARY ROUTE

## Source-bound obstruction

For an `n`-variable Boolean function represented by a truth table of length `N=2^n`, write

`MCSP_mu(n) := MCSP[2^(mu n)]`.

The STACS 2021 MCSP lower-bound paper records two facts that nearly meet but use different threshold regimes.

1. A barely superlinear one-tape lower bound for `MCSP[2^(mu n)]` at a sufficiently small `mu>0` would imply `P != NP` via the McKay–Murray–Williams hardness-magnification route.
2. For every constant `1/2 < mu < 1`, the same paper proves strong oracle-robust one-tape lower bounds with exponents approaching `2 mu`, but explicitly identifies the circuit-size threshold as the missing bridge.

The current route therefore treats **threshold transport** as the atomic object rather than attempting another unrelated MCSP lower bound.

## Desired transport object

We seek a transformation

`A_n : {Boolean functions on n variables} -> {Boolean functions on m(n) variables}`

with enough of the following properties to transfer a lower bound from a high threshold to a magnification-relevant low threshold.

### T1. MCSP decision preservation

There should be controlled functions `s_low`, `s_high` such that

`CC(f) <= s_high(n)` iff (or with a registered gap) `CC(A_n(f)) <= s_low(m(n))`.

The direction needed for each reduction must be frozen before use.

### T2. Input-length efficiency

Writing `N=2^n` and `M=2^m`, an algorithm on the transformed truth table must be simulable from the original truth table at a cost that does not erase the lower-bound exponent.

### T3. Circuit-complexity amplification

Plain dummy-variable padding preserves circuit complexity exactly. A useful stronger transport may need

`CC(A_n(f))` to grow faster than the truth-table/input-length expansion, at least on the boundary separating YES and NO MCSP instances.

### T4. Boundary robustness

Exact MCSP threshold preservation is fragile. If a transport only gives inequalities with slack, move explicitly to `Gap-MCSP` rather than treating the threshold boundary as negligible.

### T5. Proof-technique independence

A high-threshold hardness-magnification theorem cannot simply reuse the short-oracle/locality technique blocked by the 2021 oracle lower bound. Any magnification-at-high-threshold candidate must name its non-local step.

## Candidate transformation families

These are only generators.

- dummy-variable padding, first calibration and likely negative checkpoint;
- direct sum / disjoint union of truth tables;
- XOR/direct-product composition;
- block composition `g(f_1,...,f_k)` with a reconstruction restriction;
- error-correcting encodings of truth tables with circuit-complexity preservation/amplification;
- tensor/product constructions with a provable inverse restriction;
- self-reducibility based amplifiers;
- gap-preserving randomized embeddings with frozen completeness/soundness.

## Falsification order

For each transport, check in this order.

1. exact effect on circuit size, including both upper and lower directions;
2. exact effect on truth-table length;
3. induced exponent when simulating the target machine model;
4. threshold-boundary direction;
5. whether the transformed problem remains the exact registered MCSP variant;
6. whether the hoped-for contradiction actually enters the proven lower-bound regime.

A transport that fails item 3 is retained as negative history even if items 1 and 2 are mathematically elegant.

## Current discriminator

`C002` analyzes dummy-variable padding exactly. It shows that threshold matching multiplies the input-length exponent by the same factor that it multiplies the threshold exponent. Against the STACS 2021 exponent envelope, the factors cancel. Thus padding cannot move a barely-superlinear lower-bound target from `mu <= 1/2` into the proven `mu > 1/2` regime.

The next invention target is therefore a **nontrivial complexity amplifier** with a better threshold-gain / truth-table-expansion ratio than padding.
