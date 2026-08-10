# R002 — MCSP threshold transport and compression

**State:** ACTIVE PRIMARY ROUTE

## Source-bound obstruction

For an `n`-variable Boolean function represented by a truth table of length `N=2^n`, write

`MCSP_mu(n) := MCSP[2^(mu n)]`.

The STACS 2021 MCSP lower-bound paper records two facts that nearly meet but use different threshold regimes.

1. A barely superlinear one-tape lower bound for `MCSP[2^(mu n)]` at a sufficiently small `mu>0` would imply `P != NP` via the McKay–Murray–Williams hardness-magnification route.
2. At larger threshold constants the paper proves much stronger one-tape lower bounds and explicitly identifies the circuit-size threshold as the missing bridge.

The current route therefore treats **threshold transport** as the atomic object rather than attempting another unrelated MCSP lower bound.

## Reduction direction

The useful contradiction has the form

`fast low-threshold MCSP algorithm  +  high->low reduction  =>  forbidden fast high-threshold MCSP algorithm`.

Therefore the transport direction is

`high-threshold MCSP -> low-threshold MCSP`.

`C003` records the exponent accounting implied by this direction. In particular, an ordinary circuit-complexity amplifier is not automatically useful and can be directionally adverse.

## Desired transport object

We seek a transformation

`A_n : {Boolean functions on n variables} -> {Boolean functions on m(n) variables}`

with enough of the following properties to transfer a lower bound from a high threshold to a magnification-relevant low threshold.

### T1. MCSP decision preservation

There should be controlled functions `s_low`, `s_high` such that

`CC(f) <= s_high(n)` iff (or with a registered gap) `CC(A_n(f)) <= s_low(m(n))`.

The high-to-low direction must be frozen before any circuit-size intuition is used.

### T2. Input-length efficiency

Writing `N=2^n` and `M=2^m`, an algorithm on the transformed truth table must be simulable from the original truth table at a cost that does not erase the lower-bound exponent.

Explicitly materializing a target truth table of length `M=N^c` already spends exponent `c` before the target algorithm runs.

### T3. Threshold-compression accounting

Suppose on the relevant threshold boundary

`log2 CC(A_n(f)) = alpha * log2 CC(f) + o(n)`

and

`m = c n + o(n)`.

Exact alignment of high and low exponential thresholds gives

`c = alpha * mu_high / mu_low + o(1)`.

If the target algorithm runs in time `M^a`, the induced source exponent is at least

`a * alpha * mu_high / mu_low`

before additional overhead. Against a high-threshold lower-bound envelope near `2 mu_high`, a necessary condition is approximately

`alpha < 2 mu_low / a`.

For a barely-superlinear target exponent and `mu_low <= 1/2`, this requires `alpha<1`. Thus exponent-preserving transports such as padding are insufficient, and pure amplification `alpha>1` points in the wrong direction unless another component of the reduction changes the accounting.

### T4. Boundary robustness

Exact MCSP threshold preservation is fragile. If a transport only gives inequalities with slack, move explicitly to `Gap-MCSP` rather than treating the threshold boundary as negligible.

### T5. Proof-technique independence

A high-threshold hardness-magnification theorem cannot simply reuse the short-oracle/locality technique blocked by the existing barrier analysis. Any magnification-at-high-threshold candidate must name its non-local step.

## Candidate transformation families

These are only generators and must be tested in the high-to-low direction.

- dummy-variable padding as the exponent-neutral calibration;
- threshold-compressing transforms with an inverse or reconstruction theorem;
- self-reducibility transforms that shrink the threshold scale faster than truth-table length grows;
- Gap-MCSP embeddings with asymmetric YES/NO circuit-size control;
- implicit-output reductions that avoid explicit `2^m` materialization;
- direct sum / XOR / block composition only if they provide a proved compression advantage rather than merely larger circuits;
- direct high-threshold hardness magnification using a non-local proof ingredient.

## Falsification order

For each transport, check in this order.

1. freeze the reduction direction and exact YES/NO threshold implication;
2. exact effect on circuit size, with both upper and lower directions where required;
3. exact effect on number of variables and truth-table length;
4. induced machine-time exponent, including reduction/simulation overhead;
5. threshold-boundary or gap semantics;
6. whether the transformed problem remains the registered MCSP variant;
7. whether the resulting source algorithm actually enters the forbidden lower-bound regime.

A transport that fails the exponent inequality is retained as negative history even if its circuit identity is mathematically elegant.

## Current checkpoints

`C002` analyzes dummy-variable padding exactly. It shows that the threshold multiplier and induced input-length exponent multiplier cancel.

`C003` generalizes the accounting and corrects the route language. For high-to-low transport, the next invention target is a **threshold compressor, gap-preserving reduction, implicit-output reduction, or direct high-threshold magnification theorem**, not a generic complexity amplifier.
