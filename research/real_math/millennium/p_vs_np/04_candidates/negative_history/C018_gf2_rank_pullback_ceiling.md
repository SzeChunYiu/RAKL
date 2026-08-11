# C018 — GF(2)-rank pullback ceiling for full graph cover complexity

**Status:** PROOF_DRAFT_ROUTE_REFUTATION / EXECUTABLE_FACTORIZATION / NO_NOVELTY_CLAIM

C018 attacks O9d10 after C017. C017 showed that arbitrary symmetric functions of `x XOR y` stay logarithmic in full graph cover complexity. The next natural attempt was to preserve coordinate identity through dense, non-symmetric algebraic coupling, beginning with bilinear forms.

The result is again negative, and more general than the bilinear test. Any square bipartite graph whose adjacency matrix has low rank over `GF(2)` is a pullback of a low-dimensional mod-2 inner-product graph. Full cover complexity cannot increase under such a pullback.

This is an R004 upper-bound obstruction. It is not a Boolean circuit lower bound, not a P-versus-NP solution, and carries no novelty claim.

## Primary-source and registered dependencies

Primary R004 source:

Bruno P. Cavalar and Igor C. Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 / ACM Transactions on Computation Theory 17(2), Article 13 (2025), DOI `10.1145/3718746`.

Registered project dependencies:

- C012 proves for the `r`-bit mod-2 inner-product graph `IP_r` that

  `rho(IP_r,G_{2^r,2^r}) <= 3r-2`;

- C013 proves vertex-blow-up monotonicity by lifting cover pairs and pushing any hypothetical preserving semi-filter back to the quotient.

C018 observes that the same C013 proof does not actually require the vertex maps to be surjective. This yields pullback monotonicity and allows arbitrary `GF(2)` rank factorizations to be screened.

## Definition C018-D1 — graph pullback

Let `H subseteq [K] x [K]` be a square bipartite graph. Let

`lambda_L:[N]->[K]`, `lambda_R:[N]->[K]`

be arbitrary maps. They need not be surjective. Define the pullback graph

`G = Pullback(H;lambda_L,lambda_R)`

by

`(u,v) in G iff (lambda_L(u),lambda_R(v)) in H`.

Write `U_H=H^c` and `U_G=G^c`. For `S subseteq U_H`, define

`Lift(S) = {(u,v) in U_G : (lambda_L(u),lambda_R(v)) in S}`.

Then `Lift` preserves inclusion and intersections and sends `U_H` to `U_G` and the empty set to the empty set.

## Theorem C018-L1 — pullback monotonicity

For every nontrivial pullback as above,

`rho(G,G_{N,N}) <= rho(H,G_{K,K})`.

### Proof

Let `Lambda_0={(E_i,H_i):i in [m]}` be a pair family covering all relevant semi-filters of the base graph, where

`m=rho(H,G_{K,K})`.

Lift every pair:

`Lambda={(Lift(E_i),Lift(H_i)):i in [m]}`.

Assume this lifted family fails to cover `G`. Then there is a semi-filter `F` over `U_G`, above some graph edge `(u,v) in G`, that preserves every lifted pair.

Set

`a=lambda_L(u)`, `b=lambda_R(v)`.

Then `(a,b) in H`. Define

`F_0={S subseteq U_H : Lift(S) in F}`.

We check the semi-filter conditions.

- Since `F` is nonempty and upward closed, `U_G in F`. As `Lift(U_H)=U_G`, we have `U_H in F_0`.
- `Lift(emptyset)=emptyset`, and a semi-filter excludes the empty set, so `emptyset notin F_0`.
- If `S in F_0` and `S subseteq T`, then `Lift(S) subseteq Lift(T)`, so upward closure of `F` gives `T in F_0`.

Now check that `F_0` is above `(a,b)`. The actual complement row fibre of `u` in `G` is contained in the lift of the base complement row fibre at `a`. Because `F` contains the actual row fibre and is upward closed, it contains the lifted base row fibre. Hence the base row fibre lies in `F_0`. The same argument applies to the column fibre at `b`.

Finally, if `E_i,H_i in F_0`, then `Lift(E_i),Lift(H_i) in F`. Preservation in `F` gives

`Lift(E_i) intersect Lift(H_i)=Lift(E_i intersect H_i) in F`,

so `E_i intersect H_i in F_0`. Thus `F_0` preserves every pair in `Lambda_0`.

We have produced a base semi-filter above the base edge `(a,b)` that preserves a family which covers all such semi-filters, a contradiction. Therefore the lifted family covers `G` and `rho(G)<=m`.

**Important:** no surjectivity of `lambda_L` or `lambda_R` was used.

## Theorem C018 — GF(2)-rank ceiling

Let `G subseteq [N] x [N]` be a nonzero square bipartite graph and let `M_G` be its `N x N` adjacency matrix over `GF(2)`. Put

`r=rank_GF(2)(M_G)>=1`.

Then

`rho(G,G_{N,N}) <= 3r-2`.

### Proof

Take a rank factorization over `GF(2)`,

`M_G = U V`,

where `U` is `N x r` and `V` is `r x N`.

For each left vertex `u`, let `lambda_L(u)` be row `u` of `U`, viewed as a vector of `GF(2)^r`. For each right vertex `v`, let `lambda_R(v)` be column `v` of `V`.

For every pair `(u,v)`,

`M_G[u,v] = lambda_L(u) dot lambda_R(v) mod 2`.

Therefore `G` is exactly the pullback of the `r`-bit mod-2 inner-product graph `IP_r` under these two arbitrary feature maps.

By C018-L1,

`rho(G,G_{N,N}) <= rho(IP_r,G_{2^r,2^r})`.

By C012-IP,

`rho(IP_r,G_{2^r,2^r}) <= 3r-2`.

Combining the two inequalities proves the theorem.

The zero-rank case is the empty graph and is excluded from the nontrivial research target.

## Corollary C018-C1 — necessary rank growth for an R004 lower-bound family

If an explicit graph family satisfies

`rho(G_N,G_{N,N}) = omega(log N)`,

then necessarily

`rank_GF(2)(M_{G_N}) = omega(log N)`.

Thus `GF(2)` adjacency rank becomes a cheap mandatory upper-bound screen for every O9d successor.

The converse is not claimed. High matrix rank alone is not evidence for high cover complexity.

## Corollary C018-C2 — all pure bilinear-form graphs are logarithmically bounded

Let `A in GF(2)^{t x t}` and define the graph on `x,y in GF(2)^t` by

`(x,y) in G_A iff x^T A y = 1 mod 2`.

Its adjacency matrix factors as

`M_{G_A} = X A Y^T`,

where the rows of `X` and `Y` enumerate the `t`-bit vectors. Hence

`rank_GF(2)(M_{G_A}) <= rank_GF(2)(A) <= t`.

For every nonzero `A`, C018 gives

`rho(G_A) <= 3 rank(A)-2 <= 3t-2 = 3 log_2 N - 2`.

So dense and non-symmetric bilinear coupling does not escape the logarithmic ceiling. The matrix `A` may preserve coordinate identity and may have no Hamming symmetry; graph cover complexity still sees only the low-dimensional parity feature factorization.

## Why this matters

C017 showed that exchangeable coordinate information is too compressible. C018 shows that simply making the coupling non-exchangeable through a bilinear form is also insufficient. More generally, any candidate whose whole adjacency matrix has only `O(log N)` rank over `GF(2)` is already dead, regardless of how complicated its vertex encoding makes the rank-factor features look.

This distinction is load-bearing. C018 is **not** an assertion that arbitrary row-feature predicates are free in the Boolean `D_intersection(f_G|B)` model. The proof bypasses that issue at the graph-cover level by pulling a known cover of `IP_r` back through arbitrary vertex maps.

## Counterexample-first executable calibration

`05_falsification/gf2_rank_pullback_ceiling.py` computes an exact `GF(2)` row-rank factorization and returns left/right feature labels whose inner products reconstruct the original adjacency matrix bit-for-bit.

The regression suite:

- exhausts all nontrivial `2 x 2` Boolean adjacency matrices, verifies the rank pullback certificate, and checks the exact full-cover oracle never exceeds `3r-2`;
- checks selected rank-1, rank-2 and rank-3 `3 x 3` matrices within the exact oracle guard;
- checks a dense non-symmetric full-rank bilinear form on `GF(2)^3` and verifies its `8 x 8` adjacency matrix has the promised rank-factor pullback certificate;
- fails closed on malformed or non-binary matrices.

Finite checks support the construction only. They do not promote the asymptotic proof draft.

## Five-role same-context research-cell review

### Complexity theory

**Vote: ACCEPT AS ROUTE REFUTATION.** The theorem turns matrix rank into a strict necessary screen for super-logarithmic cover complexity. The pullback argument is stronger than the surjective blow-up statement used previously.

### Meta-complexity

**Vote: ACCEPT WITH NO ROOT CLAIM.** This refines the unrestricted-circuit graph-cover search only. It does not resolve the independent MCSP hardness-magnification residuals.

### Adversarial proof review

**Vote: ACCEPT PROOF DRAFT WITH MODEL GUARD.** The critical possible error was to treat arbitrary rank-factor row/column predicates as free in a bit-level intersection circuit. C018 does not do that. It lifts graph-cover pairs through arbitrary vertex maps, where only set-theoretic preimages are used. The non-surjective case is explicit in C018-L1.

### Formal methods

**Vote: REVISE BEFORE VERIFIED_LEMMA.** Exact finite factorization and exact tiny-cover regression are available, but there is no theorem-prover artifact, formalization witness, dependency/axiom receipt, or isolated kernel recheck.

### Novelty and research value

**Vote: ACCEPT AS NO-NOVELTY-CLAIM / NOVELTY_UNRESOLVED.** Matrix-rank factorization and inner-product representations are classical. This pass did not establish that the exact graph-cover inequality is absent from prior literature, so no new-mathematics claim is made. Its current value is strong route pruning.

This review is same-context and is **not independent review**.

## Typed residual C018-R1

A viable O9d successor must now have a provable `GF(2)` adjacency-rank lower bound that is itself super-logarithmic in side size. It must simultaneously survive:

- quotient/twin and arbitrary pullback compression;
- maximum-degree and arboricity ceilings;
- fixed-state and population-count compression;
- product/block multiplexing;
- low-dimensional linear/syndrome and low-`GF(2)`-rank feature representations;
- source-level intersection/cyclic constructions;
- exact tiny full-cover search for unexpected pair reuse.

The next candidate fiber should therefore be explicitly high-rank and non-bilinear. High rank is only an admission ticket to the search, never evidence of a lower bound.

## Promotion blockers

- no theorem-prover artifact;
- no isolated independent review;
- novelty unresolved and no novelty claim requested;
- result is an R004 upper-bound obstruction only;
- root P-versus-NP status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
