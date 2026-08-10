# C010 — fixed-gadget block-sum ceiling for full graph cover complexity

**Status:** PROOF_DRAFT_ROUTE_REFUTATION / EXECUTABLE_WITNESS / NOVELTY_UNRESOLVED

C010 attacks the typed residual opened by the merged C008 finite full-cover separator. It shows that the most direct composition idea, repeating a fixed hard gadget in disjoint complement blocks, cannot amplify full cover complexity beyond logarithmic scale.

This is a route-level negative theorem. It is not a Boolean circuit lower bound and is not a P-versus-NP solution.

## Primary-source model

Use Cavalar–Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 / ACM TOCT 17(2), 2025.

For graph complexity the ambient generator family is the set of all rows and columns. Their Definition 18 defines semi-filters, Definition 19 says a semi-filter above a graph edge must contain the complement trace of every generator containing that edge, Definition 20 defines preservation of a pair `(E,H)`, and Definition 21 defines cover complexity as the minimum pair family that destroys preservation for every relevant semi-filter.

Thus, for a graph edge `(u,v) in G`, any semi-filter above it must contain the complement row fibre `A_u` and complement column fibre `B_v`. If either fibre is empty then no semi-filter can be above the edge, because Definition 19 would require the empty set in the semi-filter.

## Definition C010-D1 — disjoint generator-separating cover

Let `U=G^c`. A pair `(E,H)` of subsets of `U` is **disjoint** when

`E intersect H = emptyset`.

A family `Lambda={(E_j,H_j)}` is generator-separating for `G` when every graph edge `(u,v)` with nonempty complement row and column fibres has some `j` such that either

`A_u subseteq E_j` and `B_v subseteq H_j`,

or the reverse orientation.

Let `sigma(G)` be the minimum size of such a family.

This is an auxiliary screening parameter. It is introduced here only to state the upper-bound obstruction cleanly. No novelty claim is made for the definition.

## Lemma C010-L1 — generator separation upper-bounds full cover complexity

For every bipartite graph `G`,

`rho(G,G_{N,N}) <= sigma(G)`.

### Proof

Let `F` be any semi-filter above a graph edge `(u,v)` and choose a generator-separating disjoint pair `(E,H)` for that edge, in the orientation

`A_u subseteq E`, `B_v subseteq H`.

Definition 19 gives `A_u,B_v in F`. Upward closure gives `E,H in F`. But

`E intersect H = emptyset notin F`

by non-triviality of a semi-filter. Therefore `F` does not preserve `(E,H)` under Definition 20. Hence the generator-separating pair family covers every relevant semi-filter, proving the inequality.

A trivial finite witness is always available: for each relevant graph edge `(u,v)`, the pair `(A_u,B_v)` is disjoint because

`A_u intersect B_v subseteq {(u,v)}`

and `(u,v)` belongs to `G`, not to the complement ground set `U`.

## Definition C010-D2 — block-diagonal complement sum

Fix a base graph `G_0 subseteq [n] x [n]` with complement `U_0` and an integer `t>=1`.

The `t`-fold block sum `G_0^{boxplus t}` is the graph on `tn` left and `tn` right vertices whose complement consists of `t` vertex-disjoint copies of `U_0` on the diagonal blocks and contains no cross-block complement edges.

Equivalently, every off-diagonal block is entirely contained in the graph.

## Theorem C010 — block-sum multiplexing ceiling

For every base graph `G_0` and every `t>=1`,

`sigma(G_0^{boxplus t}) <= sigma(G_0) + ceil(log_2 t)`.

Consequently,

`rho(G_0^{boxplus t}, G_{tn,tn}) <= sigma(G_0) + ceil(log_2 t)`.

### Proof

Let `k=sigma(G_0)` and fix a disjoint generator-separating family

`Lambda_0={(E_1,H_1),...,(E_k,H_k)}`.

For each `j`, form a global pair by taking the union of the copy of `E_j` over every diagonal block and, independently, the union of the copy of `H_j` over every diagonal block. The global pair remains disjoint because the local pair is disjoint and the block ground sets are disjoint.

Every relevant graph edge whose endpoints lie in the same block is generator-separated by one of these `k` multiplexed pairs exactly as in the base graph.

It remains to handle graph edges whose endpoints lie in distinct blocks. Give the `t` blocks distinct binary labels of length

`ell=ceil(log_2 t)`.

For each bit coordinate, form a disjoint pair by putting the entire complement ground set of every block with bit 0 on one side and the entire complement ground set of every block with bit 1 on the other side.

Consider a cross-block graph edge with a nonempty complement row fibre in block `r` and a nonempty complement column fibre in block `s`, where `r != s`. Their binary labels differ in some coordinate. In that coordinate, the whole row fibre lies on one side and the whole column fibre lies on the other, so the edge is generator-separated.

Edges with an empty endpoint fibre have no semi-filter above them and require no pair.

Thus the `k+ell` pairs generator-separate every relevant graph edge. Apply C010-L1.

## Corollary C010-C008 — the merged finite separator does not amplify by block sum

For the merged C008 gadget, label its complement edges

`a=(0,0)`, `b=(0,1)`, `c=(1,0)`, `d=(1,2)`, `e=(2,1)`.

The following two pairs are disjoint and generator-separate all four graph edges:

1. `({a,b},{d})`;
2. `({a,c,d},{b,e})`.

Indeed:

- `(0,2)` is separated by pair 1 using row fibre `{a,b}` and column fibre `{d}`;
- `(1,1)` is separated by pair 2 using row fibre `{c,d}` and column fibre `{b,e}`;
- `(2,0)` is separated by pair 2 using column fibre `{a,c}` and row fibre `{e}`;
- `(2,2)` is separated by pair 2 using column fibre `{d}` and row fibre `{e}`.

Hence `sigma(C008)<=2`. Since merged C008 proves its full cover number is exactly 2, the two-pair family is also an optimal full-cover witness.

For `t` block-diagonal copies, on `N=3t` vertices per side,

`rho(G_t,G_{N,N}) <= 2 + ceil(log_2 t) = O(log N)`.

Therefore repeating the fixed C008 gadget in disjoint complement blocks **cannot** produce the explicit super-logarithmic full-cover family sought by R004.

## Executable witness

`05_falsification/block_sum_cover.py` implements the sufficient generator-separation criterion and the block-sum construction. The regression suite:

- independently checks the two disjoint C008 pairs against every relevant semi-filter using the merged exact full-cover oracle;
- constructs block sums for `t=1,...,16`;
- checks the exact pair count `2+ceil(log_2 t)`;
- verifies every returned pair is disjoint;
- verifies every relevant graph edge is generator-separated.

These finite checks are proof regression only. The theorem authority remains the hand argument above until formalized and independently rechecked.

## Five-role same-context research-cell review

### Complexity theory

**Vote: ACCEPT AS ROUTE REFUTATION.** The result directly answers the first composition attempt opened by C008. A fixed gadget cannot gain asymptotic hardness merely by repetition in isolated complement blocks because the same local pairs multiplex across every copy and binary block codes handle off-diagonal edges.

### Meta-complexity

**Vote: ACCEPT WITH NO ROOT CLAIM.** C010 is independent of the MCSP lane and does not establish a bridge to `P != NP`. Its value is search-space pruning.

### Adversarial proof review

**Vote: ACCEPT PROOF DRAFT.** The load-bearing checks are that the multiplexed local pairs remain disjoint, cross-block edges are genuine graph edges because the complement is block diagonal, and edges with an empty complement fibre admit no semi-filter above them. All three conditions are explicit. A composition that adds cross-block complement structure is outside the theorem and must not be declared refuted.

### Formal methods

**Vote: REVISE BEFORE VERIFIED_LEMMA.** The executable constructor checks the finite combinatorial invariant for many copies, but no theorem-prover artifact or isolated kernel recheck exists.

### Novelty and research value

**Vote: ACCEPT ONLY AS NOVELTY_UNRESOLVED.** The argument is elementary and may be folklore or follow from known direct-sum facts for graph/discrete complexity. It should not be promoted as new mathematics without a bounded literature search. Its immediate research value is nevertheless high because it eliminates a natural but false amplification strategy.

This five-role review was produced in one research context and is **not independent review**.

## Typed residual C010-R1

The C008 residual becomes sharper:

> Any useful composition must defeat pair multiplexing. In particular it must introduce load-bearing cross-coordinate complement structure, use a base family whose relevant generator-separating complexity itself grows, or force non-disjoint intersection information that cannot be reused across coordinates. The first discriminator for any proposed composition is an explicit upper-bound attack by globally multiplexed pairs.

The next search should therefore not repeat fixed gadgets in isolated blocks. It should test coupled products/tensors in which cross-coordinate complement edges alter the semi-filter constraints, with an upper-bound adversary constructed before a lower-bound proof is attempted.

## Promotion blockers

- formal theorem-prover artifact absent;
- isolated independent review absent;
- bounded novelty search absent;
- theorem is only a cover-complexity upper-bound obstruction;
- root P-versus-NP status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
