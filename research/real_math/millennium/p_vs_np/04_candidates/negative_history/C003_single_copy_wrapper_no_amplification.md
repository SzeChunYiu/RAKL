# C003 — single-copy wrapper no-amplification checkpoint

**Status:** PROOF_DRAFT_NEGATIVE_CHECKPOINT / NOVELTY_UNRESOLVED

This checkpoint generalizes the dummy-variable padding failure in C002. It isolates a whole class of threshold transports that cannot create exponential circuit-complexity amplification. It is **not** a P-versus-NP solution and is not currently claimed novel.

## Setup

Fix a finite Boolean gate basis and let `CC(f)` denote minimum internal-gate circuit size.

For each `n`, let `T_n` map an `n`-variable Boolean function `f` to an `m(n)`-variable Boolean function `T_n(f)`. Call `T` a **single-copy restriction-recoverable wrapper** when the following hold.

1. **Restriction recovery.** There is a restriction of the added variables under which `T_n(f)` becomes `f` or `not f`. Hence

   `CC(f) <= CC(T_n(f)) + O(1)`.

   In the usual cases where negating the output is free or one gate, this additive constant is harmless.

2. **Single-copy implementation.** From any circuit of size `s` for `f`, one can build a circuit for `T_n(f)` of size at most

   `s + h(n)`

   where `h(n)=2^(o(n))`.

Examples include dummy-variable padding, adding control bits, output masking by a fixed low-complexity function, and other wrappers that invoke the unknown function only once and surround it with subexponential fixed logic.

## Lemma C003-L1 — exponential-size exponent is preserved in the original variable scale

Let `{f_n}` be any family satisfying

`CC(f_n) = 2^(mu n + o(n))`

for a constant `mu>0`. Then every single-copy restriction-recoverable wrapper satisfies

`CC(T_n(f_n)) = 2^(mu n + o(n))`.

### Proof

Restriction recovery gives

`CC(T_n(f_n)) >= CC(f_n) - O(1) = 2^(mu n + o(n))`.

Single-copy implementation gives

`CC(T_n(f_n)) <= CC(f_n) + h(n)`.

Because `h(n)=2^(o(n))` and `mu>0`, the second term is exponentially smaller than `2^(mu n+o(n))`. Therefore

`CC(T_n(f_n)) <= 2^(mu n + o(n))`.

The lower and upper bounds match at exponential scale.

## Corollary C003-C1 — variable expansion only dilutes the threshold exponent

Assume

`m(n) = q n + o(n)`

for a constant `q>=1`. Then C003-L1 is equivalently

`CC(T_n(f_n)) = 2^((mu/q) m(n) + o(m(n)))`.

Thus a wrapper of this type cannot turn exponent `mu` in the original variable scale into any exponent strictly larger than `mu/q` in the expanded scale. It can only preserve the absolute complexity while diluting its exponent by the variable-expansion factor.

## Streamable-wrapper corollary for the STACS 2021 MCSP threshold gap

Now add a representation assumption specific to MCSP transport.

Suppose the truth table of `T_n(f)` can be supplied virtually to a one-way-input machine from the truth table of `f` with only subpolynomial bookkeeping beyond the transformed machine's own steps. Write

`N=2^n`, `M=2^m=N^(q+o(1))`.

Then an `M^a` algorithm for the transformed MCSP instance yields an

`N^(a q + o(1))`

algorithm on the original instance.

To align a low threshold `2^(mu_low m)` with a high threshold `2^(mu_high n)` using a single-copy wrapper, the exponential scales require

`mu_low m = mu_high n + o(n)`,

so asymptotically

`q = mu_high / mu_low`.

Cheraghchi, Hirahara, Myrisiotis, and Yoshida, STACS 2021, Theorem 16, prove for every `1/2 < mu_high < 1` one-tape oracle-RTM lower bounds with exponents arbitrarily close below `2 mu_high`. Therefore a transported `M^a` algorithm can contradict that envelope only if

`a q < 2 mu_high`,

which after substituting `q=mu_high/mu_low` reduces to

`a < 2 mu_low`.

The threshold-shift factor cancels. For the representative hardness-magnification target `a=1.01`, this again requires `mu_low>0.505`.

Hence **no streamable single-copy wrapper in this class can use variable expansion alone to bridge the small-threshold MCSP magnification regime to the known high-threshold STACS 2021 lower-bound regime**.

## Primary source binding

- Mahdi Cheraghchi, Shuichi Hirahara, Dimitrios Myrisiotis, Yuichi Yoshida, *One-Tape Turing Machine and Branching Program Lower Bounds for MCSP*, STACS 2021, DOI `10.4230/LIPIcs.STACS.2021.23`.
- Theorem 1 records the small-threshold `N^1.01` hardness-magnification implication for P versus NP.
- Theorem 16 gives the oracle-robust high-threshold lower-bound envelope for every constant `1/2 < mu < 1`, with exponents `2(mu'-o(1))` for every `1/2 < mu' < mu`.
- The paper explicitly says the missing ingredient is moving the circuit-size parameter from the near-maximal regime toward the small/subexponential regime, or developing a fundamentally different high-threshold magnification technique.

## What C003 rules out

The next amplifier should not spend research budget on variants whose only effect is

- add variables;
- wrap one copy of `f` in fixed/subexponential logic;
- recover `f` by a simple restriction;
- preserve absolute circuit complexity up to subexponential additive overhead.

This includes a broad family of padding, masking, control-bit, and one-copy encoding ideas.

## What C003 does not rule out

C003 does **not** rule out transformations that genuinely duplicate or compose independent uses of the unknown function, non-black-box transformations of the truth table, gap-preserving encodings, or a direct high-threshold hardness-magnification proof using non-local techniques.

Those routes face a different obstruction: one needs a lower bound showing that circuit sharing across copies cannot erase the intended amplification. That is a direct-sum/direct-product style obligation, not supplied by C003.

## Typed residual

> **C003-R1.** Construct or refute a multi-copy composition `A_k(f)` whose circuit complexity provably grows faster than the truth-table length exponent paid by the composition, with exact MCSP YES/NO or Gap-MCSP boundary control.

Counterexample-first subquestions:

1. Can a circuit share intermediate computations across copies enough to defeat additive amplification?
2. Is the proposed lower bound merely a direct-sum conjecture in disguise?
3. Does fixing all but one block collapse the claimed lower bound back to `CC(f)`?
4. Does the output aggregator create a cheap shortcut on structured functions?
5. Does the truth-table expansion consume the entire threshold gain as in C002/C003?

## Assurance notes

- The elementary wrapper lemma should be formalized before promotion.
- Novelty is unresolved; the structural observation may be folklore.
- The STACS-dependent corollary is only as strong as its explicitly stated streamability and threshold-alignment assumptions.
- Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
