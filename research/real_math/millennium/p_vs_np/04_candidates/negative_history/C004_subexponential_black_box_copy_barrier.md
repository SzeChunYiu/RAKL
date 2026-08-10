# C004 — subexponential black-box copy barrier for MCSP threshold transport

**Status:** PROOF_DRAFT_NEGATIVE_CHECKPOINT / NOVELTY_UNRESOLVED

This checkpoint attacks residual `C003-R1`. It shows that ordinary direct-product, XOR, AND, OR, and similar multi-copy black-box compositions do not provide the missing MCSP threshold amplification when the number of invocations of the unknown function is subexponential. It is **not** a P-versus-NP solution and is not currently claimed novel.

## Setup

Fix a finite Boolean gate basis and write `CC(f)` for minimum internal-gate circuit size.

For each `n`, let `T_n` map an `n`-variable Boolean function `f` to an `m(n)`-variable Boolean function `T_n(f)`.

Call `T` a **subexponential-copy restriction-recoverable wrapper** when the following hold.

1. **Restriction recovery.** For each `f` in the registered family, there is a restriction of the transformed inputs under which `T_n(f)` becomes `f` or `not f`. Therefore

   `CC(f) <= CC(T_n(f)) + O(1)`.

2. **Black-box copy implementation.** Given a circuit of size `s` for `f`, one can construct a circuit for `T_n(f)` using at most

   `k(n) * s + h(n)`

   gates, where

   `k(n) = 2^(o(n))` and `h(n) = 2^(o(n))`.

The intended examples are scalar aggregations of a polynomial, quasipolynomial, or otherwise subexponential number of evaluations of `f`, together with fixed/subexponential pre- and post-processing. Ordinary constant-copy direct products followed by XOR, AND, OR, majority, selectors, or another low-complexity aggregator fall into this class whenever the restriction-recovery condition holds.

## Lemma C004-L1 — subexponential copying does not change the exponential circuit-size exponent

Let `{f_n}` satisfy

`CC(f_n) = 2^(mu n + o(n))`

for a constant `mu > 0`. Then every subexponential-copy restriction-recoverable wrapper satisfies

`CC(T_n(f_n)) = 2^(mu n + o(n))`.

### Proof

Restriction recovery gives

`CC(T_n(f_n)) >= CC(f_n) - O(1) = 2^(mu n + o(n))`.

The black-box implementation gives

`CC(T_n(f_n)) <= k(n) CC(f_n) + h(n)`.

Since `log_2 k(n) = o(n)`, `h(n)=2^(o(n))`, and `CC(f_n)=2^(mu n+o(n))`,

`k(n) CC(f_n) + h(n) = 2^(mu n + o(n))`.

The upper and lower exponential scales match.

## Corollary C004-C1 — direct-sum perfection would still not fix the threshold/length ratio

Assume

`m(n) = q n + o(n)`

for a constant `q >= 1`. Then C004-L1 becomes

`CC(T_n(f_n)) = 2^((mu/q) m(n) + o(m(n)))`.

Thus the circuit-size exponent in the transformed variable scale is `mu/q`.

In particular, take an ordinary constant-`r` disjoint-copy composition on `r` blocks of `n` variables. Then `m = r n`. Even if an ideal direct-sum theorem gave the strongest plausible additive statement

`CC(T_n(f)) = Theta(r * CC(f))`,

for `CC(f_n)=2^(mu n+o(n))` one would still have

`log_2 CC(T_n(f_n)) / m -> mu/r`.

So **perfect prevention of circuit sharing across copies does not produce the desired exponential threshold amplification**. The dimensional expansion alone dilutes the exponent.

This is stronger route pruning than merely observing that a direct-sum lower bound is difficult.

## Corollary C004-C2 — STACS 2021 exponent cancellation persists

Add the same representation condition used in C003: the truth table of `T_n(f)` can be supplied virtually to a one-way-input machine from the truth table of `f` with only subpolynomial bookkeeping beyond the transformed machine's own steps.

Write

`N = 2^n`, `M = 2^m = N^(q+o(1))`.

An `M^a` algorithm for the transformed MCSP instance then yields an

`N^(a q + o(1))`

algorithm on the original instance.

To align a transformed low threshold `2^(mu_low m)` with an original high threshold `2^(mu_high n)` at exponential scale, C004-L1 again requires

`mu_low m = mu_high n + o(n)`,

so

`q = mu_high / mu_low`.

Cheraghchi, Hirahara, Myrisiotis, and Yoshida, STACS 2021, prove high-threshold one-tape lower bounds with exponents arbitrarily close below `2 mu_high` for every constant `1/2 < mu_high < 1` in the theorem regime used by C002/C003.

Therefore a transported `M^a` algorithm can contradict that envelope only if

`a q < 2 mu_high`,

which is equivalent to

`a < 2 mu_low`.

The copy construction does not change this discriminator. For the representative magnification target `a=1.01`, contradiction still requires `mu_low > 0.505`.

## Why classical direct-product theorems do not repair this checkpoint

Classical direct-product and XOR lemmas amplify **average-case prediction hardness** of a function or a vector/XOR of copies. They do not assert that exact minimum circuit size of a scalar transformed truth table grows superlinearly in the number of copies. More importantly, even exact additive growth `Theta(r CC(f))` is insufficient here by C004-C1.

This distinction is source-bound to the classical circuit direct-product literature rather than inferred from terminology.

## Primary source anchors

- Mahdi Cheraghchi, Shuichi Hirahara, Dimitrios Myrisiotis, Yuichi Yoshida, *One-Tape Turing Machine and Branching Program Lower Bounds for MCSP*, STACS 2021, DOI `10.4230/LIPIcs.STACS.2021.23`.
- Russell Impagliazzo, Ragesh Jaiswal, Valentine Kabanets, Avi Wigderson, *Uniform Direct-Product Theorems: Simplified, Optimized, and Derandomized*, SIAM Journal on Computing 39(4), DOI `10.1137/080734030`. This is an average-case direct-product theorem, not an exact MCSP circuit-size amplifier.
- Eric Allender, Michal Koucky, *Amplifying Lower Bounds by Means of Self-Reducibility*, JACM 57(3), DOI `10.1145/1706591.1706594`. This demonstrates a different lower-bound amplification mechanism in restricted circuit settings and motivates keeping self-reducibility separate from black-box truth-table copying.

## What C004 rules out

Do not spend further primary-route budget on a transformation whose only nontrivial operation is a subexponential number of black-box evaluations of the same unknown `f`, surrounded by subexponential fixed logic, while retaining a restriction that recovers `f`.

This includes the obvious versions of:

- constant/poly/quasipolynomial direct products;
- XOR of disjoint copies;
- AND/OR of disjoint copies;
- majority or threshold aggregation of copies;
- block composition whose inner unknown function is simply instantiated a subexponential number of times;
- any such construction followed only by low-complexity masking, selectors, or padding.

## What remains open

C004 does **not** rule out:

1. genuinely non-black-box transformations of the truth table that exploit its global structure rather than invoking `f` as an oracle;
2. exact or Gap-MCSP self-reductions with a provable complexity-amplification property not expressible as subexponential black-box copying;
3. transformations with no simple restriction recovery but with a separately proved two-sided MCSP boundary theorem;
4. a direct high-threshold hardness-magnification theorem using a non-local technique;
5. abandoning R002 temporarily for an independent unrestricted-circuit framework.

## Typed residual

> **C004-R1.** Any successor MCSP threshold transport must demonstrate a non-black-box complexity-amplification mechanism or a new two-sided gap theorem. Merely adding more copies is retired.

## Assurance notes

- The asymptotic proof is elementary and should be formalized before promotion.
- Novelty is unresolved. The no-go observation may be folklore or implicit in the magnification literature.
- The STACS corollary remains conditional on the explicit streamability and threshold-alignment assumptions stated above.
- Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
