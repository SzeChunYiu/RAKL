# C002 — dummy-variable padding threshold-transport barrier

**Status:** PROOF_DRAFT_NEGATIVE_CHECKPOINT / NOVELTY_UNRESOLVED

This is a negative research result about one obvious MCSP threshold-transport strategy. It is **not** a P-versus-NP solution and is not currently claimed novel.

## Setup

For a Boolean function `f:{0,1}^n->{0,1}` and an integer `q>=1`, define

`Pad_q(f)(x,y) = f(x)`

where `x` has `n` bits and `y` has `(q-1)n` dummy bits. The padded function therefore has

`n' = q n`

variables. Let

`N = 2^n`, `N' = 2^(n') = N^q`.

Use a fixed finite Boolean gate basis with unrestricted access to input variables. Circuit size counts internal gates.

## Lemma C002-L1 — exact circuit-complexity preservation

`CC(Pad_q(f)) = CC(f)`.

### Proof

Upper bound. Any circuit for `f` computes `Pad_q(f)` by ignoring the dummy variables, so

`CC(Pad_q(f)) <= CC(f)`.

Lower bound. Restrict every dummy variable of a circuit for `Pad_q(f)` to 0. The restricted circuit computes `f` and does not increase in size, so

`CC(f) <= CC(Pad_q(f))`.

Hence equality holds.

## Lemma C002-L2 — exact threshold matching

Fix constants `mu_low>0` and an integer `q>=1`. Put

`mu_high = q mu_low`.

Then

`2^(mu_low n') = 2^(mu_low q n) = 2^(mu_high n)`.

By C002-L1,

`f in MCSP[2^(mu_high n)]`

if and only if

`Pad_q(f) in MCSP[2^(mu_low n')]`.

Thus dummy-variable padding gives an exact many-one threshold match between these parameterized MCSP instances, ignoring only the mechanical representation of the repeated truth-table bits.

## Lemma C002-L3 — one-way-input simulation exponent

Suppose `MCSP[2^(mu_low n')]` on `N'=2^(n')`-bit truth tables is computable by a one-tape machine with one-way read-only input in time

`O((N')^a)`

for some constant `a>=1`.

Then the padded reduction yields an algorithm for `MCSP[2^(mu_high n)]` running in

`O(N^(a q))`

time, up to lower-order bookkeeping.

### Proof sketch

Order the padded truth table so that the dummy coordinates vary fastest. Each bit of the original `N`-bit truth table then appears as one consecutive block of `2^((q-1)n)` identical virtual input symbols. A simulator reads one original bit, stores it in finite control, and supplies that symbol whenever the padded machine advances within the corresponding virtual block. The padded machine's work-tape behavior is simulated directly. Hence its `O((N')^a)` steps cost `O((N')^a+N) = O(N^(aq))` for `a>=1`.

The same exponent accounting applies to deterministic algorithms as a special case of the randomized/oracle-robust lower-bound model.

## Proposition C002-P — exponent cancellation against the known high-threshold lower-bound envelope

The STACS 2021 theorem gives, for each constant

`1/2 < mu_high < 1`,

one-tape randomized/oracle lower bounds with exponents arbitrarily close below

`2 mu_high`.

After dummy padding, an `N'^a` low-threshold algorithm would induce exponent

`a q`

on the original high-threshold instance. Since

`mu_high = q mu_low`,

the induced algorithm can beat the high-threshold lower-bound exponent envelope only if

`a q < 2 mu_high = 2 q mu_low`,

which is equivalent to

`a < 2 mu_low`.

The padding factor `q` cancels completely.

### Consequence for barely-superlinear magnification targets

For the representative hardness-magnification exponent `a=1.01`, padding can create a contradiction from the known high-threshold lower bounds only when

`mu_low > 0.505`.

Therefore, for every magnification-relevant threshold with

`mu_low <= 1/2`,

plain dummy-variable padding cannot transport a hypothetical `N^1.01` algorithm/lower-bound question into the proven `mu_high>1/2` regime in a way that yields the desired contradiction. The truth-table expansion consumes at least as much exponent as the threshold alignment gains.

## Why this matters

The obvious idea "pad the function until the small threshold looks like the high threshold" preserves circuit complexity too faithfully. It enlarges the truth table from `N` to `N^q`, and the same factor `q` appears in the machine-time exponent. The known high-threshold lower-bound envelope scales as `2 mu_high = 2 q mu_low`, so no advantage is created.

This turns a vague near-miss into a quantitative design requirement.

A useful threshold transport must have a strictly better **circuit-threshold amplification / truth-table expansion ratio** than dummy-variable padding, or it must establish hardness magnification directly at high thresholds by a proof technique outside the existing short-oracle/locality paradigm.

## Residual opened by C002

Find a transformation `A` for which, on the relevant MCSP YES/NO boundary,

- circuit complexity is amplified by a factor/exponent larger than the induced truth-table expansion cost; or
- a gap version is preserved with enough slack to obtain the same effect; or
- the transformation supports a new high-threshold magnification theorem that does not use the blocked locality-style argument.

Candidate families include direct-sum, direct-product/XOR, block composition, self-reducibility amplification, and gap-preserving encodings. Circuit sharing is an expected obstruction and must be tested first.

## Assurance notes

- The padding lemmas are elementary and should be formalized before promotion.
- The proposition is source-dependent on the exact STACS 2021 high-threshold exponent statement.
- No novelty claim is made. This exponent-accounting barrier may be standard or implicit in existing work.
- The root P-versus-NP status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
