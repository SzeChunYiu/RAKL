# C016 — finite-state aggregation ceiling for full graph cover complexity

**Status:** PROOF_DRAFT_ROUTE_REFUTATION / EXECUTABLE_WITNESS / NO_NOVELTY_CLAIM

C016 advances O9d8 after C015. C015 shows that constant arboricity is too simple for a super-logarithmic full-cover target, but it leaves open dense or otherwise growing-arboricity relations. C016 attacks a different structural weakness. Even when a graph has linearly growing arboricity and genuinely global correlation across all coordinates, a fixed finite-state aggregation rule keeps its graph cover complexity only logarithmic.

This is an R004 upper-bound obstruction. It is not a Boolean circuit lower bound and is not a P-versus-NP solution. No novelty claim is made.

## Primary-source model

Primary source checked on 2026-08-11:

Bruno P. Cavalar and Igor C. Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 (18 March 2025), ACM Transactions on Computation Theory 17(2), Article 13 (2025), DOI `10.1145/3718746`.

The only source facts used here are the intersection-complexity model and the graph transference inequality already bound in C012. In particular, for a non-trivial graph on side size `N=2^m`, Proposition 38 gives

`rho(G,G_{N,N}) <= D_intersection(f_G^{-1}(1) | B_{2m})`.

C016 supplies an explicit intersection construction for a broad family of graph-membership predicates.

## Definition C016-D1 — fixed local symbol map plus deterministic finite-state aggregator

Fix a constant local block size `d >= 1` and write

`A = {0,1}^d`.

Fix a finite alphabet `Sigma` and a local symbol map

`h : A x A -> Sigma`.

For every symbol `a in Sigma`, let

`L_a = {(u,v) in A x A : h(u,v)=a}`

and suppose its local intersection complexity is

`c_a = D_intersection(L_a | B_{2d})`.

Because `d`, `Sigma`, and `h` are fixed, all `c_a` are constants.

Fix a deterministic finite automaton

`M = (Q, q0, delta, F)`

with finite state set `Q`, start state `q0`, transition function

`delta : Q x Sigma -> Q`,

and accepting-state set `F subseteq Q`.

For `t >= 1`, define a graph `G_t` on left and right vertex sets `A^t` by

`(x,y) in G_t`

iff `M` accepts the symbol word

`h(x_1,y_1) h(x_2,y_2) ... h(x_t,y_t)`.

The side size is

`N = |A|^t = 2^(dt)`.

The graph may be globally correlated across all coordinates even though the local symbol map is fixed.

## Lemma C016-L1 — lifted local symbol sets cost linearly in `t`

For every coordinate `i` and symbol `a`, the lifted set

`L_{i,a} = {(x,y) : h(x_i,y_i)=a}`

can be constructed with `c_a` intersections by copying the fixed local construction into coordinate `i`.

Thus all local symbol sets over all coordinates cost at most

`t C_h`,

where

`C_h = sum_{a in Sigma} c_a`.

## Lemma C016-L2 — deterministic finite-state propagation costs at most `t |Q| |Sigma|`

Let `P_{i,q}` be the set of input pairs whose length-`i` symbol prefix leaves the automaton in state `q`.

At step `i`, after the sets `P_{i-1,q}` and `L_{i,a}` are available, construct

`T_{i,q,a} = P_{i-1,q} intersection L_{i,a}`

for every `(q,a) in Q x Sigma` that is needed. Each transition set costs one intersection. Then set

`P_{i,q'} = union_{q,a : delta(q,a)=q'} T_{i,q,a}`.

Unions are free in the source definition of intersection complexity. Therefore at most `|Q||Sigma|` counted intersections are needed per coordinate, for total at most

`t |Q||Sigma|`.

The initial set `P_{0,q0}` is the ambient universe and no other initial state need be constructed. The displayed count is deliberately loose and remains a valid upper bound even when many transition sets are empty or unreachable.

## Theorem C016 — fixed finite-state aggregation has logarithmic full-cover complexity

For every `t` for which `G_t` is non-trivial,

`rho(G_t,G_{N,N}) <= t (C_h + |Q||Sigma|)`.

Hence, for fixed `d`, `h`, and `M`,

`rho(G_t,G_{N,N}) = O(t) = O(log N)`.

### Proof

Use C016-L1 to construct every lifted local symbol set. Use C016-L2 to propagate the automaton state sets through all `t` coordinates. The accepted graph-membership set is the free union

`f_{G_t}^{-1}(1) = union_{q in F} P_{t,q}`.

Therefore

`D_intersection(f_{G_t}^{-1}(1) | B_{2dt}) <= t(C_h + |Q||Sigma|)`.

When `G_t` is non-trivial, the source graph-transference inequality applies and gives the same upper bound on `rho`.

No lower bound and no novelty claim are asserted.

## Corollary C016-M3 — Hamming-distance mod 3 survives C015 but still has `O(log N)` cover

Take `d=1`, `Sigma={0,1}`, and

`h(u,v) = u XOR v`.

Let the automaton have states `{0,1,2}` and update the state by adding the symbol modulo 3. Accept state `0`. Then

`G_t = {(x,y) : HammingDistance(x,y) == 0 (mod 3)}`.

This relation is genuinely global. Whether `(x,y)` is an edge depends on the residue of the total Hamming distance, not on a single coordinate.

The two local symbol sets are XOR and XNOR. Each has an intersection construction of cost one:

`XOR(u,v) = (u union v) intersection ((NOT u) union (NOT v))`,

`XNOR(u,v) = (u union (NOT v)) intersection ((NOT u) union v)`.

Thus `C_h=2`, `|Q|=3`, and `|Sigma|=2`, so C016 gives

`rho(G_t,G_{N,N}) <= 8t = 8 log_2 N`.

This constant is not optimized. The point is the asymptotic ceiling.

### The same family has linearly growing arboricity

For fixed `x`, the map `y -> x XOR y` is a bijection. Hence every row has degree

`D_t = sum_{j == 0 (mod 3)} binom(t,j)`.

By the roots-of-unity filter,

`D_t = (2^t + 2 cos(pi t/3))/3`.

Therefore, with `N=2^t`,

`|E(G_t)| = N D_t`.

Any forest on the `2N` bipartite vertices has at most `2N-1` edges. Consequently any partition of `E(G_t)` into `a` forests must satisfy

`a >= ceil(N D_t / (2N-1))`.

Since `D_t >= (N-2)/3`, this gives

`a >= N(N-2) / (3(2N-1)) = Omega(N)`.

So C016-M3 explicitly survives the constant-arboricity screen C015 by a wide margin, yet its full cover complexity is still `O(log N)` because the global correlation has only three states of memory.

This is the key discriminator supplied by C016. Growing arboricity is necessary to evade C015, but it is nowhere near sufficient.

## Counterexample-first executable calibration

`05_falsification/finite_state_cover_ceiling.py` constructs the Hamming-mod-3 graph in the exact finite ambient set, propagates the DFA by literal set intersections and free unions, and compares the constructed accepted set to direct Hamming-distance evaluation.

The executable checks are intentionally finite and do not certify the asymptotic theorem. They test the proof-critical set identities and operation accounting on small instances.

Regression tests verify:

- exact DFA reconstruction for `t=1..5`;
- the `<= 8t` counted-intersection bound;
- exact row degree against the binomial residue formula;
- the elementary forest-count arboricity lower bound;
- a second two-state parity automaton to ensure the generic propagation code is not specialized to modulus 3;
- fail-closed validation of malformed automata and symbol partitions.

## Five-role same-context research-cell review

### Complexity theory

**Vote: ACCEPT AS ROUTE REFUTATION.** The dynamic-programming construction is a direct upper bound in the source model. The Hamming-mod-3 example is particularly useful because its density and arboricity are large, so it defeats the hypothesis that C015 already captures the only easy growing-degree families.

### Meta-complexity

**Vote: ACCEPT WITH SCOPE WARNING.** This has no MCSP threshold consequence. Its role is search-space control for R004. It shows that dense/global-looking relations can remain easy when their correlation has bounded state complexity.

### Adversarial proof review

**Vote: ACCEPT PROOF DRAFT WITH ONE SCOPE GUARD.** The load-bearing steps are that every local symbol set has a fixed-cost construction, transition sets use only one legal intersection each, state aggregation is by free union, and the accepted graph is exactly the final accepting-state union. The theorem must not be generalized to automata whose number of states, alphabet, or local-symbol intersection complexity grows with `t` without carrying those growth terms explicitly.

### Formal methods

**Vote: REVISE BEFORE VERIFIED_LEMMA.** The recurrence is finite and formalization-friendly, and the executable witness checks exact finite set equality. There is no theorem-prover artifact, dependency receipt, formalization witness, or isolated checker recheck. Authority remains proof draft.

### Novelty and research value

**Vote: ACCEPT AS NO-NOVELTY-CLAIM.** This is an elementary dynamic-programming consequence of the source intersection model and may be folklore. Its project value is diagnostic. It adds finite-state width as a new mandatory upper-bound adversary after quotient, degree, and arboricity screens.

This review is same-context only and is **not independent review**.

## Typed residual C016-R1

A viable successor to O9d8 must now survive not only growing degree and growing arboricity but also **state-complexity compression**.

Before asymptotic lower-bound search, any coordinate-structured candidate should expose the smallest known state space needed to aggregate local pair information. If a fixed-state or otherwise `O(1)`-state dynamic program recognizes membership with fixed local symbol cost, C016 kills any `omega(log N)` cover target immediately.

The next family should therefore have at least one of the following properties:

- the minimum useful aggregation state count grows with `t` and no alternative fixed-state representation is known;
- local symbol complexity itself grows with `t`;
- membership requires nonlocal information that cannot be summarized by a bounded-width dynamic program;
- an exact small-instance search shows pair reuse remains expensive after quotient, degree, arboricity, and finite-state compressions are applied.

Promising next generators include variable-modulus Hamming/sum constraints where the modulus grows with `t`, nonlinear code constraints with growing trellis/state complexity, and globally coupled algebraic relations whose natural dynamic-program width grows provably. Each must first face source-level intersection/cyclic constructions and quotient compression.

## Promotion blockers

- no theorem-prover artifact;
- no isolated independent review;
- no bounded novelty search because no novelty claim is requested;
- the `8t` Hamming-mod-3 constant is an upper bound, not an optimized value;
- theorem is an R004 upper-bound obstruction only;
- root P-versus-NP status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
