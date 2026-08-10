# C008 — exact three-state overlap normal form for canonical cover pairs

**Status:** PROOF_DRAFT / COMPUTATIONALLY_REGRESSION_TESTED / NOVELTY_UNRESOLVED

C007 shows that the overlap `E intersect H` of a canonical-cover pair can be load-bearing and cannot in general be deleted. C008 identifies the complementary fact: the fourth edge state, belonging to neither `E` nor `H`, is never needed to preserve canonical filters already covered by the pair.

This yields an exact three-state normal form and a smaller exhaustive search space.

It is not a P-versus-NP solution and is not currently claimed novel.

## Setup

Let `G subseteq [N] x [N]`, `U=G^c`, and for a canonical edge `e=(u,v) in G` let

`A_u = R_u intersect U`,
`B_v = C_v intersect U`,

with both fibres nonempty. The canonical semi-filter is

`F_e = {W subseteq U : A_u subseteq W or B_v subseteq W}`.

C005 gives the exact pair-coverage criterion.

## Lemma C008-L1 — union normalization

Let `(E,H)` be any pair of subsets of `U`, and define

`N_0 = U \ (E union H)`.

Set

`E' = E union N_0`,
`H' = H union N_0`.

Then every canonical semi-filter covered by `(E,H)` is also covered by `(E',H')`.

In particular,

`E' union H' = U`.

Therefore every canonical cover can be replaced, pair by pair and without increasing its cardinality, by a cover in which every pair has union exactly `U`.

### Proof

Fix a canonical filter `F_e` covered by `(E,H)`. By C005, assume without loss of generality that

`A_u subseteq E`,
`B_v subseteq H`,
`A_u not subseteq H`,
`B_v not subseteq E`.

Because `A_u subseteq E`, the fibre `A_u` is disjoint from `N_0`; because `B_v subseteq H`, the fibre `B_v` is also disjoint from `N_0`.

Certainly `A_u subseteq E'` and `B_v subseteq H'`.

Adding `N_0` to `H` cannot make `A_u subseteq H'`, because `A_u` contains no element of `N_0`; hence `A_u not subseteq H'` remains true. Symmetrically, `B_v not subseteq E'` remains true.

C005 therefore shows that `(E',H')` still covers `F_e`. The opposite orientation is symmetric.

The same normalization is applied to each pair in a cover independently.

## Definition — three-state edge colouring

For a union-normalized pair, every edge of `U` lies in at least one of `E,H`. Partition `U` into

- `P = E \ H` (E-only),
- `M = H \ E` (H-only),
- `B = E intersect H` (both).

These three sets are disjoint and cover `U`.

Conversely, any three-colouring

`U = P disjoint_union M disjoint_union B`

defines a union-normalized pair

`E = P union B`,
`H = M union B`.

## Lemma C008-L2 — exact vertex-sign rule

For a three-state colouring, define the sign of a row `u` by its incident complement fibre `A_u`:

- `sign(u)=+` iff `A_u` contains no `M` edge and contains at least one `P` edge;
- `sign(u)=-` iff `A_u` contains no `P` edge and contains at least one `M` edge;
- `sign(u)=0` otherwise.

Define column signs analogously using `B_v`.

Then a canonical edge `e=(u,v) in G` is covered by the corresponding pair if and only if its row and column signs are opposite nonzero signs:

`(+,-)` or `(-,+)`.

### Proof

For a row fibre,

`A_u subseteq E = P union B`

holds exactly when no incident edge is in `M`. The condition

`A_u not subseteq H = M union B`

holds exactly when at least one incident edge is in `P`. Thus C005's first row orientation is exactly the `+` rule. The `-` rule is symmetric, and the same equivalence holds for columns.

Substituting these equivalences into C005 gives the edge criterion.

## Corollary C008-C1 — exact three-colouring formulation of canonical cover complexity

Canonical cover complexity is the minimum number `k` of three-colourings of the complement edge set

`U = P_i disjoint_union M_i disjoint_union B_i`, `i=1,...,k`,

such that every canonical edge `(u,v) in G` receives opposite nonzero endpoint signs in at least one colouring.

The `B` colour is the load-bearing overlap exposed by C007. There is no fourth `neither` colour in the normal form.

## Corollary C008-C2 — exact exhaustive-search reduction from `4^|U|` to `3^|U|`

An exhaustive canonical-cover oracle need only enumerate `3^|U|` normalized edge-colourings per candidate pair rather than all `4^|U|` membership states `(neither, E-only, H-only, both)`.

This is exact for the canonical subproblem, not a heuristic symmetry reduction.

The repository oracle is updated to use this normal form. Existing `G_NEQ` calibrations and the C007 overlap counterexample serve as regression tests.

## Structural interpretation

The full arbitrary-fibre difficulty can now be isolated in one state: `B`.

A `+` row may contain many `B` edges, but it must have at least one private `P` witness and no `M` edge. A `-` column may contain many `B` edges, but it must have at least one private `M` witness and no `P` edge. Hence a covered `(+,-)` graph edge requires exclusive witnesses while allowing their remaining complement fibres to overlap through `B`.

This suggests measuring the tradeoff between

1. how much complement incidence can be hidden in `B`, and
2. how many rows and columns can simultaneously obtain the exclusive `P`/`M` witnesses needed to create opposite signs.

## Typed residual C008-R1

> For an explicit complement graph family `U_N`, upper-bound the edge-separation capacity of one three-state colouring as a function of overlap incidence `B` and exclusive-witness structure `P,M`, in a form that composes across multiple colourings.

A one-colouring density bound is unlikely to be sufficient. The target should control the entropy or refinement rate of the **sequence** of realizable three-state sign patterns so that more than `log_2 N` coordinates are forced.

## Barrier relation

- C007 refutes deletion of the overlap `B` for arbitrary fibres.
- C008 proves deletion of the unused `neither` state is safe.
- The resulting three-state representation is exact and therefore is the preferred state space for subsequent R004 search.

## Assurance notes

- C008 is a local combinatorial normalization, not an asymptotic cover lower bound.
- The computational reduction is exact conditional on C008-L1/L2 and is regression-tested, but computational agreement does not prove novelty.
- Novelty review against graph complexity, fusion-method, and set-system formulations is still required.
- Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
