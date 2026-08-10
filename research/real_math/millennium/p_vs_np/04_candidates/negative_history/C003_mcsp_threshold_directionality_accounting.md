# C003 — MCSP threshold-directionality accounting

**Status:** PROOF_DRAFT_NEGATIVE_CHECKPOINT / ROUTE_CORRECTION / NOVELTY_UNRESOLVED

This checkpoint corrects the direction of the R002 transport objective. It is not a P-versus-NP solution.

## Source-bound setting

Let an `n`-variable Boolean function be represented by a truth table of length `N=2^n`. The STACS 2021 MCSP lower-bound result records the following near-miss.

- For some sufficiently small constant `mu_L>0`, an `N^1.01` one-tape lower bound for `MCSP[2^(mu_L n)]` would imply `P != NP`.
- For a larger threshold constant `mu_H`, strong one-tape lower bounds are known, with the paper emphasizing that the threshold mismatch is the missing bridge.

To derive a low-threshold lower bound from a known high-threshold lower bound by contradiction, a hypothetical fast algorithm for the low-threshold problem must be converted into a fast algorithm for the high-threshold problem. Thus the reduction direction is

`high-threshold MCSP  ->  low-threshold MCSP`.

That direction matters.

## General threshold map

Suppose a reduction maps an `n`-variable source function `f` to an `m`-variable target function `A(f)`, where

`m = c n + o(n)`

for some asymptotic expansion factor `c>0`.

Suppose that, on the threshold boundary relevant to the reduction, circuit complexity scales on the logarithmic exponent by a factor `alpha>0` in the sense that

`log_2 CC(A(f)) = alpha * log_2 CC(f) + o(n)`.

For exact threshold alignment between

`S_H(n)=2^(mu_H n)`

and

`S_L(m)=2^(mu_L m)`,

we need

`alpha * mu_H n = mu_L * m + o(n)`.

Hence

`c = alpha * mu_H / mu_L + o(1)`.

## Runtime accounting

If the low-threshold MCSP problem on target truth-table length

`M=2^m = N^(c+o(1))`

has an `M^a` algorithm, then an explicit reduction whose overhead is no worse than the target truth-table scale gives a source algorithm with exponent at least

`a c = a * alpha * mu_H / mu_L + o(1)`

before additional simulation overhead.

Let `beta_H` be an exponent forbidden by the known high-threshold lower bound, meaning a source algorithm running in `N^(beta_H-o(1))` would contradict it. A necessary exponent-level condition for the transport to help is therefore

`a * alpha * mu_H / mu_L < beta_H`.

Equivalently,

`alpha < beta_H * mu_L / (a * mu_H)`.

When the available high-threshold lower-bound envelope is approximately

`beta_H ~= 2 mu_H`,

this simplifies to

`alpha < 2 mu_L / a`.

For the representative hardness-magnification target `a=1.01`, any `mu_L <= 1/2` requires

`alpha < 2 mu_L / 1.01 < 1`.

Thus an exponent-preserving transform with `alpha=1` cannot cross the threshold gap. More strongly, an ordinary complexity **amplifier** with `alpha>1` moves in the wrong direction for this reduction.

## Consequence C003-P1 — route correction

The useful transport object is not, in the first instance, a circuit-complexity amplifier. To combine a high-threshold lower bound with a low-threshold hardness-magnification target through an explicit high-to-low reduction, one needs at least one of the following.

1. **Circuit-threshold compression.** The transformed function's circuit-complexity exponent must shrink enough that `alpha<1`, while YES/NO threshold membership remains controlled.
2. **Sublinear truth-table expansion relative to threshold shift.** A more general non-power-law threshold map may evade the simple `alpha` model, but it must beat the same exponent accounting.
3. **A gap formulation.** Replace exact MCSP by Gap-MCSP and use sufficient slack to obtain a more efficient reduction without silently losing boundary correctness.
4. **Direct high-threshold magnification.** Avoid threshold transport entirely by proving hardness magnification at the high threshold using a technique outside the known locality/oracle barrier.

## Consequence C003-P2 — shared-core compositions do not solve the accounting problem

Consider a broad shared-core construction in which any size-`s` circuit for `f` can be substituted into at most `r(n)` black-box slots of a wrapper of size `w(n)` to obtain a circuit for `A(f)`:

`CC(A(f)) <= r(n) * CC(f) + w(n)`.

If

`r(n)=2^o(n)`, `w(n)=2^o(n)`, and `CC(f)=2^(mu n)`,

then

`CC(A(f)) <= 2^((mu+o(1))n)`.

So the logarithmic circuit-complexity exponent satisfies `alpha<=1` on the YES side, and for ordinary polynomial/constant replication it is exponent-preserving rather than a strong compressor. Dummy-variable padding has exactly `alpha=1`. Selector copies, polynomially many variable permutations, and polynomially many shared-core XOR/direct-sum wrappers likewise cannot obtain the strict exponent compression required by the inequality above merely from their upper-bound construction.

This does not prove that every such transformation fails as a reduction, because NO-instance preservation requires a separate lower bound on `CC(A(f))`. It does prove that the earlier phrase "complexity amplification" pointed in the wrong direction for the high-to-low transport objective.

## Research residual

The R002 invention target is now sharpened to:

> construct and falsify a threshold-compressing, gap-preserving, or direct-high-threshold transformation whose full truth-table simulation exponent satisfies the transport inequality, not merely a transformation that makes circuit size numerically larger.

Candidate fibers:

- root-like or compression-style circuit transformations with an efficiently checkable inverse/reconstruction property;
- self-reducibility transformations where the threshold parameter shrinks faster than input length grows;
- Gap-MCSP embeddings with asymmetric YES/NO circuit-size control;
- reductions based on implicit truth tables rather than explicit `2^m` output materialization;
- direct high-threshold magnification using a non-local argument.

## Assurance notes

- The exponent algebra above is elementary and source-dependent only through the chosen high-threshold lower-bound exponent `beta_H` and the low-threshold magnification target.
- The STACS 2021 abstract directly confirms the qualitative near-miss: `N^1.01` at a smaller threshold would imply `P != NP`, while `N^1.99` is proved at a larger threshold.
- No novelty claim is made for this accounting identity. It may be standard or implicit in prior hardness-magnification work.
- Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
