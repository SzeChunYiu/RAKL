# C011 — coordinate-product ceiling for full graph cover complexity

**Status:** PROOF_DRAFT_ROUTE_REFUTATION / EXECUTABLE_WITNESS / NOVELTY_UNRESOLVED

C011 attacks O9d2, the first genuinely coupled composition opened after C010. It shows that a natural tensor-style coupling still collapses to logarithmic full graph cover complexity when the **complement relation factorizes coordinatewise**.

This is a route-level negative theorem. It is not a Boolean circuit lower bound and is not a P-versus-NP solution.

## Primary-source model

Use Cavalar and Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ACM Transactions on Computation Theory 17(2), Article 13 (2025), DOI `10.1145/3718746`; source version ECCC TR25-033.

Their Definitions 18–21 define semi-filters, semi-filters above a graph edge, pair preservation, and cover complexity. Their Theorem 37 shows that random bipartite graphs have linear cover complexity, while Proposition 38 transfers graph-cover lower bounds to Boolean circuit lower bounds. The source does not itself certify any explicit super-logarithmic graph family.

C010 introduced the auxiliary screening parameter `sigma(G)`, the minimum number of **disjoint generator-separating pairs** needed to separate every graph edge whose complement row and column fibres are both nonempty. C010-L1 proves directly from Definitions 18–21 that

`rho(G,G_{N,N}) <= sigma(G)`.

## Definition C011-D1 — coordinate-product complement

Fix a square bipartite graph

`G_0 subseteq [n] x [n]`

with complement `U_0 = G_0^c` and an integer `t >= 1`.

Define the `t`-fold **coordinate-product complement graph** `G_t` on left and right vertex sets `[n]^t` by declaring

`(x,y) in G_t^c`

if and only if

`(x_i,y_i) in U_0` for every coordinate `i in [t]`.

Equivalently,

`G_t^c = U_0^t`

as a relation. Thus a product edge belongs to `G_t` exactly when at least one coordinate is a base graph edge of `G_0`.

This construction is coupled across coordinates in the ambient graph. It is not the block-diagonal sum ruled out by C010.

## Theorem C011 — coordinate-product subadditivity

For every base graph `G_0` and every `t >= 1`,

`sigma(G_t) <= t * sigma(G_0)`.

Consequently,

`rho(G_t,G_{n^t,n^t}) <= t * sigma(G_0)`.

### Proof

Let

`Lambda_0 = {(E_j,H_j) : j in [k]}`

be an optimal disjoint generator-separating family for `G_0`, where `k=sigma(G_0)`.

For each coordinate `r in [t]` and each local pair `(E_j,H_j)`, define cylinder subsets of the product complement `U_0^t` by

`E_{r,j} = { (a,b) in U_0^t : (a_r,b_r) in E_j }`,

`H_{r,j} = { (a,b) in U_0^t : (a_r,b_r) in H_j }`.

Because `E_j intersect H_j = emptyset`, the lifted pair is also disjoint:

`E_{r,j} intersect H_{r,j} = emptyset`.

There are exactly `t k` lifted pairs.

Now consider a graph edge `(x,y) in G_t` that has both a nonempty product complement row fibre and a nonempty product complement column fibre. Since `(x,y)` is not in `U_0^t`, choose a coordinate `r` for which

`(x_r,y_r) in G_0`.

The product complement row fibre is

`A_x = { (x,z) : (x_i,z_i) in U_0 for every i }`,

and the product complement column fibre is

`B_y = { (z,y) : (z_i,y_i) in U_0 for every i }`.

Nonemptiness of `A_x` implies that every base row fibre `A^0_{x_i}` is nonempty. Nonemptiness of `B_y` implies that every base column fibre `B^0_{y_i}` is nonempty. Hence the chosen base graph edge `(x_r,y_r)` is relevant to the definition of `sigma(G_0)`.

Therefore some local pair `(E_j,H_j)` generator-separates that base edge. In one orientation,

`A^0_{x_r} subseteq E_j` and `B^0_{y_r} subseteq H_j`;

the reverse orientation is symmetric.

Every element of the product row fibre `A_x` has its coordinate-`r` base edge in `A^0_{x_r}`, so

`A_x subseteq E_{r,j}`.

Similarly,

`B_y subseteq H_{r,j}`.

Thus the lifted pair generator-separates `(x,y)`. Since every relevant product graph edge has at least one base graph coordinate witnessing graph membership, the `t k` lifted pairs generator-separate every relevant product edge.

Hence

`sigma(G_t) <= t k = t sigma(G_0)`.

C010-L1 then gives

`rho(G_t,G_{n^t,n^t}) <= sigma(G_t) <= t sigma(G_0)`.

This proves the theorem.

## Corollary C011-C008 — tensoring the finite separator still does not amplify

For the merged C008 gadget, C010 gives `sigma(C008) <= 2`. Therefore its `t`-fold coordinate-product complement satisfies

`rho(G_t,G_{3^t,3^t}) <= 2t`.

Writing `N=3^t`,

`2t = 2 log_3 N = O(log N)`.

So even though the complement now contains cross-coordinate coupled edges and has `5^t` elements, the natural factorized tensor power of C008 cannot produce the explicit super-logarithmic full-cover family sought by R004.

More generally, any fixed-base coordinate-product complement has

`rho = O(log N)`

whenever `sigma(G_0)` is constant and `N=n^t`.

## Executable proof witness

`05_falsification/coordinate_product_cover.py` constructs the complement relation `U_0^t`, lifts each local disjoint pair to one cylinder per coordinate, and verifies the global generator-separation condition.

`tests/test_real_math_coordinate_product_cover.py` checks the C008 construction for `t=1,...,4`:

- side size is exactly `3^t`;
- complement size is exactly `5^t`;
- pair count is exactly `2t`;
- all lifted pairs are disjoint;
- every relevant product graph edge is generator-separated;
- an explicit cross-coordinate complement edge is present, confirming this is not merely the block-diagonal construction from C010.

These finite checks are proof regression only. The theorem authority remains a proof draft until formalized and independently rechecked.

## Five-role same-context research-cell review

### Complexity theory

**Vote: ACCEPT AS ROUTE REFUTATION.** The proof uses the exact cover model and shows that a natural coupled tensor power remains easy because graph membership is witnessed by one violating coordinate, which lets a local separator lift to a coordinate cylinder.

### Meta-complexity

**Vote: ACCEPT WITH NO ROOT CLAIM.** C011 is a structural circuit-lower-bound route filter. It does not touch the MCSP threshold lane directly and supplies no separation of complexity classes.

### Adversarial proof review

**Vote: ACCEPT PROOF DRAFT.** The load-bearing step is the inference that nonempty product row/column fibres force the corresponding base fibres to be nonempty in every coordinate. That is valid because the product complement is an exact Cartesian product. The theorem must not be extended to correlated or code-constrained complements where this factorization fails.

### Formal methods

**Vote: REVISE BEFORE VERIFIED_LEMMA.** The executable constructor checks the finite sufficient invariant, but there is no theorem-prover artifact, exact formal statement hash, dependency receipt, or isolated kernel recheck.

### Novelty and research value

**Vote: ACCEPT ONLY AS NOVELTY_UNRESOLVED.** A bounded search of the source paper and primary-index results did not reveal an explicit tensor/product subadditivity theorem for this cover parameter, but that search is not a novelty certificate. The theorem may be folklore or an immediate consequence of known product facts. Its immediate value is route pruning.

This five-role review was produced in one research context and is **not independent review**.

## Typed residual C011-R1

C010 killed isolated block sums. C011 now kills the natural Cartesian complement tensor power.

The surviving composition target must therefore break **coordinate witness locality**. A useful explicit family cannot let every graph edge be certified by one coordinate whose local generator fibres can be placed in a lifted disjoint pair.

Promising next constructions are globally correlated complement relations, for example code-constrained or parity-constrained fibres, where membership in the graph cannot be witnessed by a single coordinate and where product row/column fibres do not decompose into independent local fibres.

The next upper-bound adversary should first test whether such a correlated construction still admits a low-dimensional feature code whose cylinder pairs give `O(log N)` generator separation.

## Promotion blockers

- formal theorem-prover artifact absent;
- isolated independent review absent;
- bounded novelty certificate absent;
- theorem is only a cover-complexity upper-bound obstruction;
- root P-versus-NP status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
