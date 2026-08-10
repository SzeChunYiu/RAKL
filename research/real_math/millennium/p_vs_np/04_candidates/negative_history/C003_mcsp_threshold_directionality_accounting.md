# C003 — MCSP threshold-directionality accounting

**Status:** PROOF_DRAFT_NEGATIVE_CHECKPOINT / ROUTE_CORRECTION / NOVELTY_UNRESOLVED

This checkpoint corrects the direction of the R002 transport objective. It is not a P-versus-NP solution.

## Source-bound setting

Let an `n`-variable Boolean function be represented by a truth table of length `N=2^n`. Cheraghchi, Hirahara, Myrisiotis, and Yoshida (STACS 2021) record the following near-miss.

- Their Theorem 1 states that for some small constant `mu_L>0`, an `N^1.01` one-tape lower bound for `MCSP[2^(mu_L n)]` would imply `P != NP`.
- Their Theorem 2 proves an `N^1.99` randomized one-tape lower bound for a larger threshold constant chosen close to 1.
- Their Theorem 16 gives the parameterized form: for every `1/2 < mu_H < 1`, and every `1/2 < mu_prime < mu_H`, `MCSP[2^(mu_H n)]` is outside the corresponding short-query oracle one-tape class with time exponent `2*(mu_prime-o(1))`. Hence the lower-bound exponent can approach `2 mu_H` from below.
- The paper explicitly says the missing step is the size-parameter mismatch and notes that extending the existing magnification technique beyond `mu>1/2` requires a different, non-short-query technique.

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

has an `M^a` algorithm, then an explicit reduction whose own overhead is at most the same asymptotic scale yields a source algorithm running in

`O(N^(a c + o(1))) = O(N^(a * alpha * mu_H / mu_L + o(1)))`.

Additional reduction or simulation overhead can only worsen this exponent accounting.

Let `beta_H` denote an exponent below which the relevant high-threshold theorem rules out source algorithms. A necessary exponent-level condition for the transport to create a contradiction is therefore

`a * alpha * mu_H / mu_L < beta_H`.

Equivalently,

`alpha < beta_H * mu_L / (a * mu_H)`.

For the oracle-robust STACS 2021 parameterized theorem, `beta_H` can be chosen arbitrarily close below `2 mu_H` when `mu_H>1/2`. At the envelope level this gives the necessary asymptotic condition

`alpha < 2 mu_L / a`.

For the representative hardness-magnification target `a=1.01`, any `mu_L <= 1/2` therefore requires

`alpha < 2 mu_L / 1.01 < 1`.

Thus an exponent-preserving transform with `alpha=1` cannot cross this threshold gap under the stated explicit-output accounting. More strongly, an ordinary complexity **amplifier** with `alpha>1` moves in the wrong direction for this reduction unless another component changes the variable/output/runtime relation.

## Consequence C003-P1 — route correction

The useful transport object is not, in the first instance, a circuit-complexity amplifier. To combine a high-threshold lower bound with a low-threshold hardness-magnification target through an explicit high-to-low reduction, one needs at least one of the following.

1. **Circuit-threshold compression.** The transformed function's circuit-complexity exponent must shrink enough that `alpha<1`, while YES/NO threshold membership remains controlled.
2. **Sublinear truth-table expansion relative to threshold shift.** A more general non-power-law threshold map may evade the simple `alpha` model, but it must beat the same exponent accounting.
3. **A gap formulation.** Replace exact MCSP by Gap-MCSP and use sufficient slack to obtain a more efficient reduction without silently losing boundary correctness.
4. **Direct high-threshold magnification.** Avoid threshold transport entirely by proving hardness magnification at the high threshold using a technique outside the known locality/short-query barrier.

## Consequence C003-P2 — shared-core compositions do not solve the accounting problem

Consider a broad shared-core construction in which any size-`s` circuit for `f` can be substituted into at most `r(n)` black-box slots of a wrapper of size `w(n)` to obtain a circuit for `A(f)`:

`CC(A(f)) <= r(n) * CC(f) + w(n)`.

If

`r(n)=2^o(n)`, `w(n)=2^o(n)`, and `CC(f)=2^(mu n)`,

then

`CC(A(f)) <= 2^((mu+o(1))n)`.

So such a construction provides no YES-side evidence for a logarithmic exponent factor larger than 1, and ordinary polynomial/constant replication is exponent-preserving rather than a strong threshold compressor. Dummy-variable padding has exactly `alpha=1`. Selector copies, polynomially many variable permutations, and polynomially many shared-core XOR/direct-sum wrappers likewise do not obtain the strict exponent compression required above merely from their standard upper-bound construction.

This does not prove that every such transformation fails as a reduction, because NO-instance preservation requires a separate lower bound on `CC(A(f))`. It does prove that the earlier phrase "complexity amplification" pointed in the wrong direction for the high-to-low transport objective.

## Research residual

The R002 invention target is now sharpened to:

> construct and falsify a threshold-compressing, gap-preserving, implicit-output, or direct-high-threshold transformation whose full simulation exponent satisfies the transport inequality, not merely a transformation that makes circuit size numerically larger.

Candidate fibers:

- root-like or compression-style circuit transformations with an efficiently checkable inverse/reconstruction property;
- self-reducibility transformations where the threshold parameter shrinks faster than input length grows;
- Gap-MCSP embeddings with asymmetric YES/NO circuit-size control;
- reductions based on implicit truth tables rather than explicit `2^m` output materialization;
- direct high-threshold magnification using a non-local argument.

## Assurance notes

- The exponent algebra above is elementary and source-dependent through the chosen high-threshold lower-bound exponent and low-threshold magnification target.
- The cited theorem forms are bound to STACS 2021, DOI `10.4230/LIPIcs.STACS.2021.23`.
- No novelty claim is made for this accounting identity. It may be standard or implicit in prior hardness-magnification work.
- Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
