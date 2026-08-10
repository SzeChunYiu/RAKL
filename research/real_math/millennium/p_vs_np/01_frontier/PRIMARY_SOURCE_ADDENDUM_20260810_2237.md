# Primary-source addendum — 2026-08-10 22:37 Europe/Stockholm

**Authority:** SOURCE-BOUND FRONTIER UPDATE. No new-mathematics authority is created by this document.

## 1. Exact MCSP threshold lane

### Cheraghchi–Hirahara–Myrisiotis–Yoshida, STACS 2021

**Title:** *One-Tape Turing Machine and Branching Program Lower Bounds for MCSP*  
**DOI:** `10.4230/LIPIcs.STACS.2021.23`

The source defines `MCSP[s(n)]` on `N=2^n`-bit truth tables. Its abstract states that, for some small threshold exponent, an `N^1.01` one-tape lower bound would imply `P != NP`, while the paper proves much stronger one-tape lower bounds at a larger circuit-size threshold. The detailed theorem regime used by C002–C004 gives high-threshold lower-bound exponents approaching `2 mu` for `1/2 < mu < 1`.

**Research use:** exact source for the threshold mismatch and for the exponent-cancellation discriminator in C002–C004.

## 2. Direct products are an average-case hardness tool, not an exact MCSP threshold amplifier

### Impagliazzo–Jaiswal–Kabanets–Wigderson

**Title:** *Uniform Direct-Product Theorems: Simplified, Optimized, and Derandomized*  
**DOI:** `10.1137/080734030`

The classical direct-product theorem concerns amplification of the probability that small circuits fail to compute multiple independent copies. It produces decoding/reconstruction consequences from a circuit that computes the direct product on a nontrivial fraction of inputs.

**Research use:** prevents a category error in R002. Average-case direct-product hardness does not by itself say that the exact minimum circuit size of a scalar truth-table transformation grows faster than the truth-table dimension. C004 shows that even ideal additive exact growth would not repair the MCSP threshold/length exponent mismatch for ordinary disjoint copies.

## 3. Lower-bound amplification via self-reducibility is a distinct mechanism

### Allender–Koucky, JACM 2010

**Title:** *Amplifying Lower Bounds by Means of Self-Reducibility*  
**DOI:** `10.1145/1706591.1706594`

This work shows lower-bound amplification phenomena for self-reducible problems in restricted circuit settings such as `TC^0`.

**Research use:** self-reducibility should remain a separate successor fiber after C004 retires ordinary black-box copying. Any application to MCSP must bind the exact circuit model, self-reduction, threshold direction, and truth-table cost rather than importing the word "amplification" across models.

## 4. Two-dimensional cover complexity

### Cavalar–Oliveira, ECCC TR25-033, 2025

**Title:** *Boolean Circuit Complexity and Two-Dimensional Cover Problems*

Primary source: Electronic Colloquium on Computational Complexity, Report TR25-033.

The source establishes:

- cover complexity lower-bounds intersection complexity;
- graph intersection-complexity lower bounds transfer tightly to the corresponding Boolean function;
- for an explicit graph `H subseteq [N] x [N]`, a `C log N` graph-intersection lower bound yields a related explicit Boolean function with `C m - O(1)` AND/OR-gate lower bound;
- random bipartite graphs have `Theta(N)` cover complexity;
- the explicit calibration graph `G_NEQ` has canonical/full cover and intersection complexity exactly `log_2 N` when `N=2^n`.

**Research use:** source authority for R004, C005, and the exact tiny canonical-cover oracle. The immediate atomic goal is to beat the `log N` explicit baseline, not to infer P versus NP from finite graphs.

## 5. Current unrestricted-circuit context

### Carmosino–Dang–Jackman, arXiv:2602.17942, 2026

**Title:** *Convergent Gate Elimination and Constructive Circuit Lower Bounds*

The paper studies gate elimination, describes it as the method behind known explicit unrestricted Boolean gate lower bounds, and formalizes convergent circuit simplification for selected bases.

**Research use:** confirms that R004 is aimed at a genuinely difficult frontier. Any small improvement produced by cover complexity must be compared against the exact basis and constant of current gate-elimination lower bounds before being described as state-of-the-art.

## Promotion boundary

None of the sources above establishes a P-versus-NP solution. C004 and C005 remain proof drafts, and R004 remains a discovery route. Any claimed asymptotic explicit cover lower bound requires independent proof, source-bounded novelty review, and the full Paper IV assurance gates.
