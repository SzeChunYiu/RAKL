# C009 — universal matching-number ceiling for canonical cover complexity

**Status:** PROOF_DRAFT_ROUTE_REFUTATION / NOVELTY_UNRESOLVED

C009 strictly generalizes the perfect-matching ceiling merged as C007. It resolves the Hall-deficient discriminator: the canonical semi-filter subproblem cannot yield a super-logarithmic graph-cover lower bound on any square bipartite graph.

This is a route-level negative theorem. It is **not** a P-versus-NP solution, and it does not upper-bound the full cover complexity studied by Cavalar–Oliveira.

## Setup

Let `G subseteq [N] x [N]` and let

`U = G^c`.

Call a left or right vertex **active** when it has positive degree in `U`. Exactly active endpoints can occur in a canonical edge whose row and column complement fibres are both nonempty.

Let `nu(U)` be the maximum matching size of `U`. Write `rho_can(G)` for the canonical cover complexity.

## Lemma C009-L1 — maximum matching gives a star-biclique partition of all active vertices

Let `M` be a maximum matching of `U` with edges

`e_j=(l_j,r_j)`, `j=1,...,m`,

where `m=nu(U)`.

Then all active vertices can be partitioned into `m` classes `(L_j,R_j)` such that

1. `l_j in L_j`, `r_j in R_j`;
2. both sides of every class are nonempty;
3. `L_j x R_j subseteq U`;
4. at least one side of every class has cardinality one.

### Proof

Every unmatched active left vertex `x` has a neighbour. Since a maximum matching is maximal, every such neighbour is a matched right endpoint; otherwise an edge joining two unmatched endpoints could be added to the matching. Choose one matched neighbour `r_j` and assign `x` to `L_j`.

Symmetrically, assign every unmatched active right vertex `y` to some class `R_j` whose matched left endpoint `l_j` is adjacent to `y`.

No matching edge can receive unmatched extras from both sides. If unmatched `x` is adjacent to `r_j` and unmatched `y` is adjacent to `l_j`, then

`x -- r_j -- l_j -- y`

is an augmenting path with the middle edge in `M`, contradicting maximality of `M` as a maximum matching.

Hence each class is either a left star around `r_j`, a right star around `l_j`, or the matching edge alone. The class is therefore a complete bipartite subgraph of `U`. The classes are vertex-disjoint and cover all active vertices.

## Lemma C009-L2 — biclique-cluster coding

Suppose the active vertices of `U` are partitioned into `q` nonempty biclique classes `(L_j,R_j)` satisfying

`L_j x R_j subseteq U`.

Then, for `q>=2`,

`rho_can(G) <= ceil(log_2 q)`.

For `q=1`, the canonical family is empty and `rho_can(G)=0`.

### Proof

For `q>=2`, choose distinct codes

`z_j in {0,1}^k`, `k=ceil(log_2 q)`.

For each coordinate `i`, use the C008 three-state normal form. Put every internal complement edge in `L_j x R_j` into E-only state `P_i` when `z_j[i]=0` and into H-only state `M_i` when `z_j[i]=1`. Put every other complement edge, necessarily a cross-class edge, into overlap `B_i`.

Every active row and column in class `j` has an internal complement edge because both class sides are nonempty. It therefore receives the class's nonzero sign in coordinate `i`; cross-class overlap edges cannot introduce the opposite exclusive colour.

If `(u,v) in G` is canonical, its endpoints cannot lie in the same class, because `L_j x R_j subseteq U`. Their class codes are distinct and differ in some coordinate, so C008 gives opposite nonzero endpoint signs in that coordinate. The corresponding pair covers the canonical semi-filter.

If `q=1`, all active row/column pairs lie in the single complement biclique, so no `G`-edge has two active endpoints and the canonical family is empty.

## Theorem C009 — universal canonical ceiling

If `nu(U)=0` or `nu(U)=1`, `rho_can(G)=0`. If `nu(U)>=2`, then

`rho_can(G) <= ceil(log_2 nu(U)) <= ceil(log_2 N)`.

### Proof

Apply C009-L1 with a maximum matching, obtaining `q=nu(U)` star-biclique classes. Then apply C009-L2.

## Tightness and relation to merged C007

When `G=G_NEQ`, the complement is a perfect matching of size `N`. Cavalar–Oliveira prove

`rho_can(G_NEQ)=log_2 N`

for `N=2^n`. Thus the universal `log N` ceiling is tight on the source calibration family.

Merged C007 is the special case `nu(U)=N`. Hall deficiency cannot evade that obstruction; it only lowers the matching-number bound.

## Route consequence

The former R004 atomic target

`rho_can(G_N) >= (1+epsilon) log_2 N`

is impossible for every square graph family.

This does **not** refute the source paper's full-cover programme. Full cover complexity `rho(G,G_{N,N})` quantifies over all relevant semi-filters, whereas `rho_can` covers only the canonical subfamily. Cavalar–Oliveira prove linear full cover complexity for random bipartite graphs. C009 shows only that canonical semi-filters cannot witness that hard regime.

Therefore the next R004 route must use genuinely noncanonical semi-filters or another source-complete full-cover invariant.

## Typed residual C009-R1

> Find a compact, source-complete noncanonical semi-filter family or invariant that can witness super-logarithmic full cover complexity while retaining enough structure for exact falsification and proof search.

Blind enumeration of all semi-filters is not an acceptable replacement because it destroys the executable advantage of the canonical reduction.

## Assurance notes

- C009 is an upper bound for a restricted canonical subproblem, not a Boolean circuit lower bound;
- the theorem should receive formal or isolated mathematical verification before promotion above proof draft;
- novelty is unresolved and must be searched against fusion-method, graph-complexity, matching, biclique-partition, and separating-system literature;
- root P-versus-NP status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
