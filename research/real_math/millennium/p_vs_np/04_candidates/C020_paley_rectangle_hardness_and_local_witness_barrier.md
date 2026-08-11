# C020 — Paley rectangle hardness and the local-witness fusion barrier

**Status:** `PROOF_DRAFT_RESTRICTED_MODEL_CHECKPOINT / FULL_COVER_OPEN / NO_NOVELTY_CLAIM`

C020 advances the C019 residual without claiming a full-cover lower bound. It establishes that the quadratic-residue difference family is already linearly hard for the most obvious one-level rectangle construction, while also proving that a broad low-width class of semi-filter witnesses is universally coverable with only `O(log N)` pairs. The remaining gap is therefore genuinely about deep/cyclic pair reuse and high-width semi-filters.

## Object and notation

Let `p` be a prime with `p == 3 (mod 8)`. Let `chi` be the quadratic character of `F_p`, extended by `chi(0)=0`. Let

`QR_p = {(x,y) in F_p x F_p : chi(y-x)=1}`.

This is the C019 square bipartite graph. Write `N=p`, and let `U = QR_p^c` be its complement in `F_p x F_p`.

For subsets `A,B` of `F_p`, call `A x B` an **edge rectangle** when `A x B` is contained in `QR_p`.

For the Cavalar–Oliveira cover problem, a relevant semi-filter `F` is a semi-filter over `U` above some graph edge `a=(u,v) in QR_p`. Thus both `R_u intersect U` and `C_v intersect U` belong to `F`.

Because `U` is finite and `F` is upward closed, each member of `F` contains a minimal member of `F`. Define the local witness width at `a=(u,v)` by

`w_a(F) = min(r_a(F), c_a(F))`,

where

- `r_a(F)` is the minimum cardinality of a minimal member of `F` contained in `R_u intersect U`;
- `c_a(F)` is the minimum cardinality of a minimal member of `F` contained in `C_v intersect U`.

Both quantities are finite because the required row and column traces belong to `F`.

## C020-L1 — exact quadratic-character correlation identity

Define the `p x p` sign matrix

`M[x,y] = chi(y-x)`.

Then over the reals,

`M M^T = p I - J`,

where `J` is the all-ones matrix.

### Proof

For `x=z`,

`sum_y chi(y-x)^2 = p-1`,

because exactly one term has argument zero and every other term has square `1`.

For `x != z`, the standard quadratic-character correlation is

`sum_y chi(y-x) chi(y-z) = -1`.

A self-contained verification is obtained by translating and scaling to

`sum_t chi(t(t-1))`.

Count pairs `(t,s)` satisfying `s^2=t(t-1)`. Completing the square gives

`(2t-1)^2 - (2s)^2 = 1`,

or `(2t-1-2s)(2t-1+2s)=1`. For each nonzero first factor there is exactly one inverse second factor, giving `p-1` solutions. On the other hand, for each `t` the number of `s` is `1+chi(t(t-1))`. Hence

`p + sum_t chi(t(t-1)) = p-1`,

so the sum is `-1`.

Therefore the diagonal of `M M^T` is `p-1` and every off-diagonal entry is `-1`, which is exactly `pI-J`.

Since `M 1 = 0`, the nonzero singular values of `M` are all `sqrt(p)`. In particular `||M||_2 = sqrt(p)`.

## C020-L2 — every edge rectangle has area at most p

If `A x B` is an edge rectangle of `QR_p`, then

`|A| |B| <= p`.

### Proof

Every entry of `M` on `A x B` equals `1`, so

`|A||B| = 1_A^T M 1_B`.

By Cauchy–Schwarz and C020-L1,

`|A||B| <= ||M||_2 ||1_A||_2 ||1_B||_2 = sqrt(p |A||B|)`.

If the rectangle is nonempty, division by `sqrt(|A||B|)` gives `|A||B| <= p`.

## C020-L3 — linear one-level rectangle-cover lower bound

Any cover of the edge set of `QR_p` by edge rectangles needs at least

`(p-1)/2`

rectangles.

### Proof

`QR_p` is regular of degree `(p-1)/2`, hence has

`p(p-1)/2`

edges. By C020-L2 each rectangle covers at most `p` edges. Even allowing overlaps, at least

`[p(p-1)/2] / p = (p-1)/2`

rectangles are required.

### Authority boundary

This is a lower bound only for the **one-level** construction in which the graph is a union of rectangles, equivalently intersections of a union of rows with a union of columns followed by a free union. General intersection constructions can reuse intermediate sets, and cover complexity `rho` is even exactly cyclic intersection complexity in the active source. Therefore C020-L3 does **not** imply `rho(QR_p)=Omega(p)`.

The purpose of the lemma is adversarial: an `O(log p)` full-cover certificate, if one exists, cannot be a disguised rectangle cover. It must exploit intermediate-set reuse or cyclic propagation essentially.

## C020-L4 — constant local-witness width is universally logarithmically coverable

Fix any nontrivial square bipartite graph `G subset [N] x [N]`, not just `QR_p`, and let `U=G^c`. Fix an integer `k>=1`.

Let `F_{<=k}` be the collection of all relevant semi-filters `F` for which there exists an edge `a in G` above which `F` satisfies

`w_a(F) <= k`.

There is a family of at most

`2 ceil( 2^(k+1) ((k+1) ln N + 1) )`

pairs of subsets of `U` that covers every semi-filter in `F_{<=k}`.

Consequently, for every fixed `k`, this entire witness class has cover number `O(log N)`.

### Proof

We first build a separating family of row-index subsets. Consider every ordered pair `(u,S)` with

- `u in [N]`;
- `S subset [N] \ {u}`;
- `1 <= |S| <= k`.

Choose a random subset `A subset [N]` by including each index independently with probability `1/2`. The probability that

`u in A` and `A intersect S = empty`

is `2^(-|S|-1) >= 2^(-(k+1))`.

There are at most `N^(k+1)` such `(u,S)`. Thus, if

`t = ceil( 2^(k+1) ((k+1) ln N + 1) )`,

a union bound shows that some family `A_1,...,A_t` simultaneously isolates every `(u,S)`: for each one, some `A_i` contains `u` and avoids all of `S`.

For each `A_i`, define a pair of subsets of `U`

`E_i = U intersect (A_i x [N])`,
`H_i = U intersect (([N] \ A_i) x [N])`.

These sets are disjoint.

Now let `F` be above an edge `a=(u,v) in G`, and suppose `c_a(F) <= k`. Choose a minimal member `K of F` with

`K subset C_v intersect U`, `|K|<=k`.

Let `S` be the set of row indices of edges in `K`. Since all elements of `K` lie in one column, `|S|=|K|<=k`. Also `u notin S`, because `(u,v)` is a graph edge and therefore is not in `U`.

Choose `A_i` isolating `(u,S)`. Because `u in A_i`, the set `E_i` contains the required row trace `R_u intersect U`, which belongs to `F`; upward closure gives `E_i in F`. Because `A_i` avoids `S`, the set `H_i` contains `K`, and therefore `H_i in F`. But

`E_i intersect H_i = empty`,

and the empty set is forbidden in a semi-filter. Thus `F` fails to preserve `(E_i,H_i)` and is covered.

This handles all `F` with `c_a(F)<=k`. A symmetric separating family built from column-index subsets handles the case `r_a(F)<=k`, doubling the pair count and proving the theorem.

## C020-C1 — structural consequence for C019

C020-L3 and C020-L4 point in opposite directions, and that disagreement is informative.

- At depth one, the Paley relation is strongly resistant: rectangle cover size is `Omega(p)`.
- In the full fusion formulation, every semi-filter whose local minimal witness width is bounded by a constant belongs to a universally `O(log p)`-coverable class.

Therefore a super-logarithmic full-cover proof for `QR_p` cannot be obtained merely by enumerating principal/singleton or other bounded-width local witnesses. It must exploit semi-filters with local minimal witnesses whose size grows with `p`, and it must prove that arbitrary pair reuse cannot cover those high-width witnesses cheaply.

This is the new atomic obstruction.

## Counterexample-first executable checks

`05_falsification/quadratic_residue_rectangle_screen.py` checks the exact correlation identity and exhaustively computes the maximum edge-rectangle area for small admissible primes. The current finite examples are

- `p=3`: maximum rectangle area `1`;
- `p=11`: maximum rectangle area `5`;
- `p=19`: maximum rectangle area `9`.

These values are stronger than the analytic `<=p` bound but are finite calibration only. No asymptotic strengthening is inferred from the pattern.

The test suite also checks the `k=1` local-witness pair construction against every relevant semi-filter of the merged C008 five-complement-edge gadget. This validates the implementation of the witness notion on an exhaustible instance; it is not a proof of C020-L4.

## Primary-source and novelty context

The active source remains Cavalar–Oliveira, ECCC TR25-033 / ACM TOCT 17(2), 2025. Definitions 18–21 give the semi-filter and pair-cover object; Theorem 30 identifies cover complexity exactly with cyclic intersection complexity. Theorem 37 obtains linear cover complexity for a random graph by an incompressibility/counting argument, which does not transfer to this explicit Paley family.

A second primary source checked in this pass is Stasys Jukna, *On Graph Complexity*, ECCC TR04-005 revision 1 / Combinatorics, Probability and Computing 15 (2006). That work already uses Hadamard-type spectral/discrepancy structure to obtain strong lower bounds for restricted graph-representation models. This makes spectral rectangle hardness a known style of restricted-model evidence rather than a novelty anchor for unrestricted/full cover.

No claim that C020-L1, L2, or L3 is new is made. The local-witness formulation C020-L4 also carries `NO_NOVELTY_CLAIM` until a dedicated post-proof literature search is warranted by stronger authority.

## Five-role same-context research-cell review

### Complexity theory

**Vote: ACCEPT AS RESTRICTED-MODEL CHECKPOINT.** The character-correlation proof and rectangle consequence are clean. They establish that C019 is not easy for the one-level rectangle model, but they do not lower-bound full cover complexity.

### Meta-complexity

**Vote: ACCEPT WITH ROOT SCOPE WARNING.** Even a future super-log graph-cover lower bound would first pass the R004 transference gate and would constitute an unrestricted-circuit lower-bound advance, not automatically `P != NP`. C020 itself is much weaker.

### Adversarial proof review

**Vote: ACCEPT THE LEMMAS, REJECT ANY FULL-COVER INFERENCE.** C020-L4 exposes the exact failure mode of a naive semi-filter attack: constant-width local witnesses can be globally multiplexed by row/column separating cuts. The next lower-bound attempt must quantify high-width witnesses and pair coverage rather than relying on rectangle pseudorandomness alone.

### Formal methods

**Vote: REVISE BEFORE VERIFIED_LEMMA.** The proofs are natural-language drafts with finite regression checks. There is no theorem-prover artifact, `FormalizationWitness`, `ProofReceipt`, dependency/axiom audit, or isolated kernel recheck.

### Novelty and research value

**Vote: ACCEPT ONLY AS NO-NOVELTY-CLAIM.** Paley/Hadamard discrepancy and rectangle arguments are classical terrain, and graph-complexity literature already studies Hadamard-type restricted models. The useful contribution to the program is the combined discriminator: one-level hardness is not the missing issue; high-width semi-filter behavior under cyclic pair reuse is.

This is same-context review and is **not independent review**.

## Typed residual C020-R1

For `QR_p`, define the high-width class

`F_{>k} = {F relevant above a : w_a(F) > k for every witnessing graph edge a}`.

The next discriminator is to choose a growing `k=k(p)` and establish one of the following.

1. **Upper-bound branch.** Construct `O(log p)` pairs covering `F_{>k}` as well, which together with C020-L4 refutes C019 as a super-log target.
2. **Lower-bound branch.** Prove that every pair covers only a controlled fraction/structured subfamily of `F_{>k}`, yielding a super-log set-cover lower bound.
3. **Cannot-check branch.** Define a smaller, source-valid high-width semi-filter subfamily with exact small-`p` enumeration and an analytic pair-coverage statistic.

Character pseudorandomness may constrain rectangles, but it is not yet known to constrain arbitrary pairs `(E,H) subset U x U`. The next proof must bridge exactly that semantic gap.

## Root authority

C020 does not alter the root theorem state. `P != NP` remains `OPEN_NO_SOLUTION_CERTIFICATE`.
