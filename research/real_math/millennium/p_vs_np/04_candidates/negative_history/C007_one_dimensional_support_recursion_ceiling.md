# C007 — the partition-normalization generalization fails for non-singleton canonical fibres

**Status:** REFUTED_DRAFT_NEGATIVE_CHECKPOINT / PARTITION_SUBMODEL_ANALYZED / NOVELTY_UNRESOLVED

This checkpoint records a failed attempt to generalize the recursive `G_NEQ` proof pattern from Cavalar–Oliveira to arbitrary canonical semi-filters. The failure is mathematically useful: it identifies **pair overlap** `E intersect H` as a load-bearing degree of freedom that disappears in the singleton-fibre `G_NEQ` calibration.

It is **not** a P-versus-NP solution and is not currently claimed novel.

## Setup

Let `G subseteq [N] x [N]` and let

`U = G^c`.

For a row `u` and column `v`, define complement fibres

`A_u = R_u intersect U`,
`B_v = C_v intersect U`.

For a canonical edge `e=(u,v) in G`, both fibres are nonempty and

`F_e = {W subseteq U : A_u subseteq W or B_v subseteq W}`.

C005 gives the exact criterion for a pair `(E,H)` to cover `F_e`.

## Refuted claim C007-X1

The first attempted generalization asserted:

> if `(E,H)` covers an arbitrary canonical semi-filter, then `(E\H,H\E)` also covers it.

This is false when a canonical generator has more than one element.

### Exact counterexample

Take a canonical edge `e=(0,0)` and a complement containing

`x=(0,1)`, `y=(0,2)`, `z=(1,0)`,

with no other complement edge in row 0 or column 0. Then

`A_0 = {x,y}`,
`B_0 = {z}`.

Let

`E = {x,y}`,
`H = {y,z}`.

Then

- `A_0 subseteq E`;
- `B_0 subseteq H`;
- `A_0 not subseteq H` because `x notin H`;
- `B_0 not subseteq E` because `z notin E`.

By C005, `(E,H)` covers `F_e`. Equivalently, `E in F_e`, `H in F_e`, while

`E intersect H = {y}`

contains neither full generator and therefore is not in `F_e`.

But after deleting the overlap,

`E\H = {x}`,
`H\E = {z}`.

The set `{x}` contains neither `A_0` nor `B_0`, so `{x} notin F_e`. Hence the disjoint pair does **not** cover `F_e`.

Therefore the proposed arbitrary-fibre analogue of the singleton normalization step is refuted.

## Why the published NEQ normalization survives

For `G_NEQ`, each relevant complement row fibre and complement column fibre is a singleton. If a singleton generator is contained in `E` but not contained in `H`, its unique element lies in `E\H`. It cannot straddle the common part `E intersect H` and an exclusive part.

A larger fibre can straddle exactly this way. In the counterexample, the row generator `{x,y}` uses `x` as an `E`-exclusive witness while `y` sits in the overlap. Removing the overlap destroys full containment of the row generator.

Thus the singleton structure is not cosmetic. It is load-bearing in the direct normalization argument.

## Valid lemma C007-L1 — completion works once a covering pair is already disjoint

Suppose `E intersect H` is empty and `(E,H)` covers a canonical semi-filter `F_e`. Then

`(E, U\E)`

also covers `F_e`.

### Proof

By C005, suppose without loss of generality

`A_u subseteq E`,
`B_v subseteq H`,
`A_u not subseteq H`,
`B_v not subseteq E`.

Disjointness gives `H subseteq U\E`, so `B_v subseteq U\E`. Since `A_u` is nonempty and `A_u subseteq E`, it is not a subset of `U\E`. Together with `B_v not subseteq E`, C005 shows that `(E,U\E)` covers `F_e`.

The opposite orientation is symmetric.

**Boundary:** this does not show that an arbitrary overlapping cover pair can first be made disjoint.

## Valid lemma C007-L2 — partition-side support gives an untouched residual rectangle

For the **partition-only submodel**, let `(S,U\S)` be one cover pair and define

`X_S = {u : A_u intersect S is nonempty}`,
`Y_S = {v : B_v intersect S is nonempty}`.

Then no canonical filter `F_(u,v)` with

`(u,v) in G intersect (X_S x Y_S)`

is covered by `(S,U\S)`.

### Proof

For `u in X_S`, `A_u` contains an element of `S`, so `A_u` is not a subset of `U\S`. Likewise `B_v` is not a subset of `U\S` for `v in Y_S`.

Coverage by a partition requires one complete generator on `S` and the other complete generator on `U\S`. Both possible orientations fail because neither fibre can lie entirely in `U\S`.

## Valid method barrier C007-P — minimum-dimension recursion cannot beat the NEQ coefficient inside the partition-only submodel

Assume a proof method has already justified restriction to partition pairs and recursively measures progress only through

`m = min(number of active rows, number of active columns)`.

No such method can obtain a universal retention factor strictly larger than `1/2` against all partitions.

### Proof

At an active state with row set `X`, split `X` into two parts `A` and `X\A` as evenly as possible. Put every complement edge whose row endpoint lies in `A` into `S` and every complement edge whose active row endpoint lies in `X\A` into `U\S`.

If every active row has a nonempty complement fibre, then the row supports of the two partition sides are exactly `A` and `X\A`. Hence whichever side is selected has at most `ceil(|X|/2)` active rows. The scalar minimum of row and column support therefore cannot enjoy an asymptotic guarantee above `1/2`.

A recurrence based solely on this scalar support must retain more than half the dimension per removed pair to improve the coefficient beyond `log_2 N`; the balanced row partition prevents that.

### Scope

This is a barrier only for the **partition-only proof architecture**. Because C007-X1 is false, it is not yet a barrier for full canonical cover complexity.

## The actual obstruction exposed by the refutation

For a general pair, every complement edge has four states:

1. `E` only;
2. `H` only;
3. both `E` and `H`;
4. neither.

Under the C005 orientation

`A_u subseteq E`, `B_v subseteq H`, `A_u not subseteq H`, `B_v not subseteq E`,

a covered edge needs

- at least one `E`-only witness in the row fibre `A_u`;
- at least one `H`-only witness in the column fibre `B_v`;
- but all remaining elements of either fibre are allowed to sit in the shared `both` state.

The `both` state is exactly what defeats partition normalization. Any super-logarithmic lower-bound argument for arbitrary canonical fibres must control how much simultaneous row/column containment can be hidden in this overlap while still supplying exclusive witnesses.

This is naturally compatible with the ternary signature formulation in C006: a nonzero row/column sign records existence of the required exclusive witness plus full containment in one side, but the underlying edge-state realization can still use the overlap heavily.

## Successor target C007-R1 — overlap-sensitive two-dimensional potential

> Construct a potential for realizable C006 signature systems that charges the shared `E intersect H` state and proves that every cover pair loses less than one bit of normalized two-dimensional potential on an explicit graph family.

Possible coordinates include:

- overlap mass and its row/column incidence profile;
- entropy of the four-state edge colouring;
- support product of exclusive witnesses;
- private-neighbour counts for `E`-only and `H`-only witnesses;
- a compression bound for simultaneously realizable ternary row/column signatures.

A useful potential must work for arbitrary overlapping pairs. A theorem proved only after silently replacing pairs by partitions does not address full canonical cover complexity.

## Conditional partition-model design equation

The earlier support-product idea remains valid only as a **partition-submodel heuristic**. If one had a recursively closed partition-only family with complement density `p>1/2`, residual canonical validity, and support-product retention at least `p/2` per pair, then a formal recurrence would suggest a coefficient

`2 / log_2(2/p)`

multiplying `log_2 N`, which is greater than 1 for `p>1/2`.

Because full cover pairs may overlap, this does not currently transfer to `rho_can`. It is retained only as a clue for designing an overlap-sensitive replacement.

## Source relation

Cavalar and Oliveira, ECCC TR25-033 (2025), establish the `G_NEQ` `log N` bound using canonical filters with singleton complement fibres and normalize the pairs in that special setting before recursion. The source also defines canonical cover complexity for arbitrary bipartite graphs. The failed C007-X1 attempt shows that the singleton normalization mechanism cannot simply be copied to the arbitrary-fibre setting.

## Assurance notes

- The false generalization is preserved explicitly rather than deleted.
- C007-L1, C007-L2, and C007-P are bounded statements whose assumptions are visible.
- No asymptotic full-cover or circuit lower bound is claimed.
- Novelty of the overlap-obstruction formulation is unresolved.
- Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
