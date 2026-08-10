# C007 — partition normalization and the one-dimensional support-recursion ceiling

**Status:** PROOF_DRAFT_NEGATIVE_CHECKPOINT / NOVELTY_UNRESOLVED

This checkpoint sharpens residual `C006-R1`. It generalizes the pair-normalization step used in the published `G_NEQ` calibration argument and then identifies a limitation of any attempted super-logarithmic proof that measures recursive progress only through the smaller retained row/column dimension.

It is **not** a P-versus-NP solution and is not currently claimed novel.

## Setup

Let `G subseteq [N] x [N]` be a bipartite graph and let

`U = G^c`.

For a row `u` and column `v`, define the complement fibres

`A_u = R_u intersect U`,
`B_v = C_v intersect U`.

For a canonical edge `e=(u,v) in G`, both `A_u` and `B_v` are nonempty and

`F_e = {W subseteq U : A_u subseteq W or B_v subseteq W}`.

C005 states the exact condition under which a pair `(E,H)` covers `F_e`.

## Lemma C007-L1 — arbitrary canonical-cover pairs may be normalized to partitions

If `(E,H)` covers a canonical semi-filter `F_e`, then

`(E \ H, H \ E)`

also covers `F_e`.

If `E` and `H` are disjoint and `(E,H)` covers `F_e`, then

`(E, U \ E)`

also covers `F_e`.

Consequently, every family of pairs covering a collection of canonical semi-filters can be replaced, pair by pair and without increasing its size, by a family in which each pair is a partition of `U`.

### Proof

By C005, suppose without loss of generality that

`A_u subseteq E`, `B_v subseteq H`, `A_u not subseteq H`, and `B_v not subseteq E`.

Because `A_u subseteq E` while `A_u not subseteq H`, every element of `A_u` that lies outside `H` remains in `E \ H`, and in fact `A_u subseteq E` plus the coverage condition implies the normalized orientation required by C005 after common elements are deleted from both sides. The same argument applies symmetrically to `B_v`.

More directly, canonical membership of `E` or `H` depends on containing an entire generator, while failure of `E intersect H` to belong to `F_e` says neither generator is contained in the common part. Removing that common part therefore leaves the two complete generators on opposite sides.

Now assume `E` and `H` are disjoint. From the displayed orientation, `H subseteq U \ E`, hence `B_v subseteq U \ E`. Since `A_u` is nonempty and `A_u subseteq E`, we have `A_u not subseteq U \ E`; and `B_v not subseteq E` already holds. C005 therefore shows that `(E,U\E)` covers `F_e`. The opposite orientation is symmetric.

Applying this replacement separately to every pair preserves every canonical filter that the original pair covered, so a canonical cover has a partition witness of the same cardinality.

## Lemma C007-L2 — support of one partition side is an untouched residual rectangle

Let `(S,U\S)` be a partition pair. Define

`X_S = {u in [N] : A_u intersect S is nonempty}`,
`Y_S = {v in [N] : B_v intersect S is nonempty}`.

Then no canonical semi-filter `F_(u,v)` with

`(u,v) in G intersect (X_S x Y_S)`

is covered by `(S,U\S)`.

### Proof

For `u in X_S`, the row fibre `A_u` contains an element of `S`, so `A_u` is not a subset of `U\S`. Likewise, for `v in Y_S`, `B_v` is not a subset of `U\S`.

C005 says coverage by the partition requires one of `A_u,B_v` to lie entirely in `S` and the other entirely in `U\S`. The second requirement is impossible for both possible orientations because both fibres intersect `S`. Hence the pair does not cover the canonical filter.

## C007-P — a one-dimensional support recurrence cannot beat the `log_2 N` coefficient

Consider any lower-bound strategy that repeatedly uses C007-L2 as follows.

1. Normalize the next cover pair to a partition `(S,U\S)`.
2. Choose one side `Z in {S,U\S}`.
3. Retain only the residual rectangle `X_Z x Y_Z` guaranteed to be untouched by that pair.
4. Measure recursive progress solely by

   `m = min(|X|,|Y|)`.

No graph family with every active row incident to at least one complement edge can support a universal asymptotic retention guarantee

`m_next > (1/2 + epsilon) m_current`

for any fixed `epsilon>0` against all partition pairs.

### Proof

At an active state with row set `X` of size `r`, choose a subset `A subseteq X` with `|A|=floor(r/2)`. Partition the complement edges by their row endpoint:

`S = { (u,v) in U : u in A }`,
`U\S = { (u,v) in U : u in X\A }`

(with edges outside the active rows assigned arbitrarily if the state is embedded in a larger ambient instance).

Because each active row has a nonempty complement fibre,

`X_S = A`,
`X_(U\S) = X\A`.

Thus every choice of side has row support at most `ceil(r/2)`. Since the recurrence uses the smaller of row and column support, its retained value satisfies

`m_next <= ceil(r/2)`

for this legal partition. In the balanced asymptotic regime, no universal retention factor strictly larger than `1/2` is possible.

A recurrence of the form `m_next >= delta m_current` yields a logarithmic lower-bound coefficient larger than the NEQ `log_2 N` baseline only when `delta>1/2`. The row-split partition above rules this out for any proof whose sole progress invariant is the minimum retained side dimension.

## What C007 rules out

C007 does **not** upper-bound canonical cover complexity. It blocks only a proof architecture.

Retire attempts whose entire super-logarithmic argument is:

- normalize each pair to a partition;
- pick one colour class;
- show that both its row support and column support retain more than half the current vertices;
- recurse using only the smaller support dimension.

No amount of ordinary vertex expansion can make the `>1/2` guarantee hold against the row-split partition.

## The two-dimensional escape route

The row-split adversary exposes information that the scalar `min(row_support,column_support)` throws away. A side may touch only half the rows while still touching almost all columns.

This suggests tracking a genuinely two-dimensional potential such as

`P(S) = |X_S| * |Y_S|`

or an entropy/refinement analogue.

For any partition `U=S disjoint_union T`, one side has at least `|U|/2` edges. Since

`|Z| <= |X_Z| * |Y_Z|`,

that side satisfies the elementary bound

`|X_Z| * |Y_Z| >= |U|/2`.

If an explicit recursive family could additionally maintain a hereditary complement density

`|U| >= p |X| |Y|`

with `p>1/2`, while guaranteeing that the retained support rectangle contains a valid residual canonical subproblem and preserves the density condition, then the product potential would retain at least a `p/2` fraction per removed pair. Formally iterating such a closed recurrence would suggest a lower-bound scale

`k >= log_(2/p)(|X_0||Y_0|)`.

For a square `N x N` start this coefficient is

`2 / log_2(2/p)`

times `log_2 N`, which exceeds 1 exactly when `p>1/2`.

**This is a design equation, not a proved cover lower bound.** The difficult unresolved obligations are precisely the ones hidden by the conditional sentence: residual canonical validity, hereditary density or an entropy substitute, and enough surviving `G`-edges after each adaptive partition.

## Typed residual C007-R1

> Replace one-dimensional support retention by a closed two-dimensional potential that survives every adaptive partition of `U`, leaves a nonempty canonical-edge residual, and loses strictly less than one bit of normalized potential per cover pair on an explicit family.

Candidate potentials include support product, bipartite entropy, neighbourhood-profile entropy, and multi-coordinate realizable-signature capacity from C006.

## Source relation

Cavalar and Oliveira, ECCC TR25-033 (2025), prove the `G_NEQ` `log N` lower bound by normalizing cover pairs and recursively restricting to the row/column support of a large partition side. C007-L1 and C007-L2 isolate the corresponding algebra for arbitrary canonical semi-filters, while C007-P explains why the direct one-dimensional strengthening of that recursion cannot by itself yield a coefficient above 1.

## Assurance notes

- C007 is a method-level negative checkpoint, not an asymptotic circuit lower bound.
- The arbitrary-graph normalization and support-ceiling formulation require novelty review against fusion-method and graph-complexity literature.
- The product-potential paragraph is an explicitly conditional research program, not a theorem.
- Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
