# C017 — universal symmetric-Hamming ceiling for full graph cover complexity

**Status:** SOURCE_ALIGNED_PROOF_DRAFT_ROUTE_REFUTATION / EXECUTABLE_WITNESS / KNOWN_CIRCUIT_ANCESTRY / NO_NOVELTY_CLAIM

C017 advances O9d9 immediately after C016. C016 showed that a fixed finite-state aggregator over fixed-cost local pair symbols gives only logarithmic full graph cover complexity. That leaves an obvious escape attempt: let the aggregation state space grow with the coordinate count, for example by taking a Hamming-distance residue modulo a growing modulus, an exact Hamming weight, or an arbitrary selected set of Hamming weights.

That escape fails much more generally. Every graph whose membership is an arbitrary symmetric Boolean function of the coordinatewise XOR bits has `O(log N)` full cover complexity. The proof does not enumerate automaton states. It computes the Hamming weight with a linear-size complement-carrying adder network, decodes every possible weight with a linear-size prefix tree, and takes a free union of the accepted weights.

This is an R004 upper-bound obstruction. It is not a Boolean circuit lower bound and is not a P-versus-NP solution. No novelty claim is made.

## Source and prior-work context

Primary R004 source checked on 2026-08-11:

Bruno P. Cavalar and Igor C. Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 (2025), ACM Transactions on Computation Theory 17(2), Article 13, DOI `10.1145/3718746`.

C017 uses the same source-side graph transference bound as C012 and C016:

`rho(G,G_{N,N}) <= D_intersection(f_G^{-1}(1) | B_{2m})`

for non-trivial square graphs of side size `N=2^m`.

There is also strong classical prior ancestry for the underlying Boolean-circuit fact. Demenkov, Kojevnikov, Kulikov and Yaroslavtsev, *New upper bounds on the Boolean circuit complexity of symmetric functions*, Information Processing Letters 110(7), 264–267 (2010), DOI `10.1016/j.ipl.2010.01.007`, give linear-size circuits for every symmetric Boolean function. C017 does **not** claim this circuit fact as new. The project-specific content is an explicit complement-carrying construction inside the intersection-complexity accounting used by R004.

## Definition C017-D1 — XOR-symmetric graph family

For each `t >= 1`, let

`S_t : {0,1}^t -> {0,1}`

be any symmetric Boolean function. The function may vary arbitrarily with `t`. Symmetry means that `S_t(z)` depends only on the Hamming weight

`|z| = z_1 + ... + z_t`.

Define a graph `G_t` on left and right vertex sets `{0,1}^t` by

`(x,y) in G_t`

iff

`S_t(x XOR y)=1`.

The side size is

`N=2^t`.

This class includes every Hamming-distance threshold, exact-distance relation, arbitrary union of distance shells, and every residue condition `HammingDistance(x,y) mod m_t in R_t`, even when the modulus `m_t` grows with `t`.

## Lemma C017-L1 — each XOR bit and its complement cost two intersections total

For coordinate `i`, write `x=x_i`, `y=y_i`. Construct

`z_i = x XOR y = (x union y) intersection ((NOT x) union (NOT y))`

and

`zbar_i = NOT(z_i) = (x union (NOT y)) intersection ((NOT x) union y)`.

Thus the pair `(z_i,zbar_i)` costs two intersections. Across all coordinates the cost is `2t`.

The explicit complement is important because intermediate complements are not assumed free.

## Lemma C017-L2 — a complement-carrying full adder costs at most 22 intersections

Suppose sets representing Boolean signals `a,b,c` and their complements are already available. A full adder must construct both output bits and both complements.

The sum bit `s=a XOR b XOR c` is the free union of its four odd-parity minterms. Each three-literal minterm costs two intersections, so `s` costs at most eight intersections. Its complement `sbar` is the free union of the four even-parity minterms and costs at most another eight.

The carry bit is

`k = (a intersection b) union (a intersection c) union (b intersection c)`,

which costs three intersections. Its complement is

`kbar = (abar intersection bbar) union (abar intersection cbar) union (bbar intersection cbar)`,

which costs another three.

Hence one full adder producing `(s,sbar,k,kbar)` costs at most

`8+8+3+3 = 22`

intersections.

No negation of a newly constructed set is used as a free operation.

## Lemma C017-L3 — the binary Hamming weight and all output-bit complements cost `O(t)` intersections

Start with the `t` signal pairs `(z_i,zbar_i)`, all in weight column zero. Perform carry-save compression: whenever three signal pairs occur in one binary weight column, apply C017-L2. The sum pair returns to the same column and the carry pair moves to the next column.

Every carry-save full adder reduces the total number of live signal pairs by one. Therefore fewer than `t` such full adders are used.

After compression, every weight column contains at most two signal pairs. Regard these as two binary numbers, filling missing positions with a single reusable zero/complement-one pair. Ripple-add the two rows. The number of relevant binary positions is `O(log t)` and in particular at most `t+1`; therefore this final addition uses at most `t+1` further full adders.

Thus at most `2t+1` complement-carrying full adders suffice. By C017-L2, the Hamming-weight bits and all their complements cost at most

`22(2t+1)`

intersections, plus one harmless constant-construction operation if the empty set is not treated as a free empty union.

The constant is deliberately loose. Only linearity is load-bearing.

## Lemma C017-L4 — all exact Hamming-weight classes can be decoded in `O(t)` intersections

Let the binary Hamming weight use `k=ceil(log2(t+1))` significant bits, with each bit and complement already available.

Build all binary prefix conjunctions as a tree. The one-bit prefixes are already the bit set and its complement. At each later bit, intersect every current prefix set with the next bit and with its complement. The number of counted intersections is at most

`4 + 8 + ... + 2^k < 2^(k+1) <= 4(t+1)`.

Every leaf is an exact binary-weight class. Leaves encoding values larger than `t` are empty and may be ignored.

Since `S_t` is symmetric, there is a set of accepted weights `R_t subseteq {0,...,t}`. The graph-membership set is the free union of the decoded weight classes indexed by `R_t`.

Therefore the choice of symmetric function costs no further intersections after the common decoder is built.

## Theorem C017 — every XOR-symmetric graph family has logarithmic full cover complexity

For every `t` for which `G_t` is non-trivial,

`rho(G_t,G_{N,N}) = O(t) = O(log N)`.

A conservative explicit accounting from C017-L1 through C017-L4 gives, for all `t>=1`,

`rho(G_t,G_{N,N}) <= 80 t`.

The constant `80` is not optimized and has no research significance.

### Proof

Construct all coordinatewise XOR bits and their complements using C017-L1. Construct the binary Hamming weight and output complements using C017-L2 and C017-L3. Decode every exact weight using C017-L4 and take the free union selected by `S_t`.

This gives an `O(t)` intersection construction for `f_{G_t}^{-1}(1)`. Because `N=2^t` and the graph is assumed non-trivial, the source transference inequality gives the same asymptotic upper bound on full graph cover complexity.

## Corollary C017-MOD — growing Hamming moduli do not escape C016

Let `m_t` be any positive integer and `R_t` any residue set. The graph

`G_t = {(x,y): HammingDistance(x,y) mod m_t in R_t}`

is XOR-symmetric. Therefore, regardless of how `m_t` grows,

`rho(G_t) <= 80 log2 N`.

A growing DFA state count is therefore not by itself a viable O9d9 escape. The population-count representation compresses the same relation without paying for all residue states.

The same conclusion holds for exact-distance graphs, Hamming balls, majority/threshold distance graphs, and arbitrary unions of Hamming shells.

## Counterexample-first executable calibration

`05_falsification/symmetric_hamming_cover_ceiling.py` realizes the proof-critical identities on the exact finite ambient graph.

It explicitly constructs both a signal and its complement at every stage, uses the 22-intersection full-adder formulas, carry-save compresses coordinate XOR bits, performs the final ripple addition, decodes exact Hamming weights by a prefix tree, and compares the constructed accepted set against direct evaluation.

Tests include:

- arbitrary selected Hamming-weight sets for `t=1..5`;
- growing-modulus residue predicates;
- exact-distance and threshold predicates;
- exact Hamming-weight reconstruction at every input pair;
- complement disjointness/completeness for every produced weight bit;
- the conservative `<=80t` operation ceiling on the tested range;
- fail-closed guards for invalid accepted weights.

Finite execution checks the construction, not the asymptotic theorem authority.

## Five-role same-context research-cell review

### Complexity theory

**Vote: ACCEPT AS ROUTE REFUTATION.** The proof is an explicit linear intersection construction. It closes the most obvious growing-state successor to C016: arbitrary Hamming-symmetric constraints remain logarithmic in `N` even when their minimal automaton description grows.

### Meta-complexity

**Vote: ACCEPT WITH NO ROOT CLAIM.** This is an unrestricted-circuit route filter only. It does not improve the MCSP threshold bridge or directly imply a complexity-class separation.

### Adversarial proof review

**Vote: ACCEPT PROOF DRAFT WITH MODEL GUARD.** The critical issue is internal negation. The proof does not assume it free; every generated signal is carried together with an explicitly constructed complement. The `80t` constant is intentionally slack. The theorem applies only to predicates symmetric in the coordinatewise XOR vector and must not be generalized to arbitrary globally correlated relations.

### Formal methods

**Vote: REVISE BEFORE VERIFIED_LEMMA.** The full-adder identities and finite set construction are executable, but no theorem-prover artifact, formalization witness, dependency receipt, or isolated checker recheck exists. This remains research-route history.

### Novelty and research value

**Vote: ACCEPT AS KNOWN-ANCESTRY / NO-NOVELTY-CLAIM.** Linear-size standard circuits for arbitrary symmetric Boolean functions are classical prior art, including Demenkov et al. (2010). C017 is valuable here because it translates the population-count idea into the exact no-free-intermediate-negation accounting needed by the R004 intersection model and prunes an active search fiber. No new-mathematics claim is requested.

This is same-context review and is **not independent review**.

## Typed residual C017-R1

O9d9 must now exclude not only fixed-state aggregators but every relation that collapses to an arbitrary symmetric function of coordinatewise XOR symbols.

A viable next family should therefore be genuinely non-symmetric and retain information about **which coordinates** carry which local relations, not only an aggregate count. Before lower-bound search it must face:

- quotient/twin compression;
- degree and arboricity ceilings;
- fixed-state and population-count compression;
- low-dimensional linear/syndrome representations;
- product/block multiplexing;
- source-level intersection/cyclic constructions;
- exact tiny full-cover search for unexpected pair reuse.

The next candidate fiber should use a growing-width structured relation with non-exchangeable coordinate interactions, for example a nonlinear code/constraint graph whose membership cannot be reduced to a weight enumerator or bounded-width trellis.

## Promotion blockers

- no theorem-prover artifact;
- no isolated independent review;
- no novelty claim; classical symmetric-circuit ancestry is explicit;
- the `80t` constant is deliberately unoptimized;
- theorem is an R004 upper-bound obstruction only;
- root P-versus-NP status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
