# Primary-source frontier refresh — 2026-08-10

**Authority:** SOURCE-BOUND FRONTIER UPDATE. This document binds research routes to primary/publication sources; it does not promote any new theorem.

## A. Limited negation / monotone-to-nonmonotone transfer

### Amano–Maruoka, SIAM J. Comput. 35(1), 2005

**Title:** *A Superpolynomial Lower Bound for a Circuit Computing the Clique Function with at most (1/6) log log n Negation Gates*  
**DOI:** 10.1137/S0097539701396959

The published abstract proves a superpolynomial lower bound for CLIQUE circuits with at most `floor((1/6) log log m)` negation gates. It also states that, via a result of Fischer, improving the tolerated negation count to `floor(2 log m)` in that statement would imply `P != NP`.

**RAKL consequence:** route R001 is established literature territory. C001 must not be represented as a novelty claim merely because its restriction proof was generated independently. Its value is currently as a simple structural checkpoint and residual generator.

### Jukna–Lingas, STACS 2019

**Title:** *Lower Bounds for DeMorgan Circuits of Bounded Negation Width*  
**DOI:** 10.4230/LIPIcs.STACS.2019.41

They define negation width for De Morgan circuits computing monotone functions and show lower bounds in terms of monotone circuit complexity divided by a penalty depending on the width and prime-implicant length.

**RAKL consequence:** a structural replacement for raw `|T(C)|` already exists in the literature. Any successor to C001 must compare explicitly against negation width rather than rediscovering it under new notation.

## B. MCSP hardness magnification and the threshold gap

### McKay–Murray–Williams, STOC 2019

**Title:** *Weak Lower Bounds on Resource-Bounded Compression Imply Strong Separations of Complexity Classes*  
**DOI:** 10.1145/3313276.3316396

Their Theorem 1.2 gives a one-pass streaming algorithm for search-MCSP with small PH-oracle queries, and Theorem 1.3 shows that an appropriate weak streaming lower bound for oracle MCSP would imply `P != NP`.

### Cheraghchi–Hirahara–Myrisiotis–Yoshida, STACS 2021

**Title:** *One-Tape Turing Machine and Branching Program Lower Bounds for MCSP*  
**DOI:** 10.4230/LIPIcs.STACS.2021.23

The paper makes the near-miss explicit:

- for some small constant `mu > 0`, an `N^1.01` one-tape lower bound for `MCSP[2^(mu n)]` would imply `P != NP`;
- unconditionally, for every constant `1/2 < mu < 1`, their oracle-robust theorem gives lower bounds for `MCSP[2^(mu n)]` against one-tape randomized machines at exponents approaching `2 mu`;
- the authors state that the missing step is precisely moving the MCSP circuit-size parameter from the high-threshold regime toward the small/subexponential regime, or obtaining magnification at the high threshold by fundamentally different techniques.

Their Remark 19 also identifies an oracle/locality-style barrier for extending the existing magnification proof technique to `mu > 1/2`.

**RAKL consequence:** R002 is promoted from a generic meta-complexity lane to the current highest-priority atomic obstruction: **threshold transport / complexity amplification for MCSP**.

## C. Hardness magnification near known lower bounds

### Oliveira–Pich–Santhanam, Theory of Computing 17(11), 2021

**Title:** *Hardness Magnification Near State-of-the-Art Lower Bounds*  
**ECCC precursor:** TR18-158

This work develops Gap-MCSP / Gap-MKtP magnification and studies why small improvements over known weak-model lower bounds can imply major complexity separations.

**RAKL consequence:** if exact-threshold transport is blocked by boundary effects, a gap formulation is a legitimate sibling fiber and should be preferred over silently ignoring the threshold boundary.

## D. Current meta-complexity refresh

Recent ECCC work through the 2026-08-10 cutoff continues to study MCSP/implicit MCSP, hardness, reductions, and near-maximum lower bounds. No source found in this refresh claims a resolution of P versus NP.

Examples retained for later fibers include:

- ECCC TR26-091, Goldberg–Juvekar–Kabanets, *Non-Levin NP-Hardness of Implicit MCSP and PAC Learning under Few Assumptions*;
- revised ECCC TR24-053 (2026 revision), Mazor–Pass, *Gap MCSP is not (Levin) NP-complete in Obfustopia*.

These do not close R002, but they reinforce that reduction type and witness preservation are first-class constraints in meta-complexity.

## Route reprioritization

1. **R002 / MCSP threshold transport:** ACTIVE PRIMARY.
2. **R001 / negation-limited CLIQUE:** ACTIVE SECONDARY; C001 novelty unresolved and now explicitly compared with known limited-negation work.
3. **R003 / state potentials:** exploratory generator; do not spend major asymptotic proof budget until R002 transport obstructions are exhausted.

## Next discriminator

Attempt the strongest obvious threshold transport first: dummy-variable truth-table padding. Prove exactly what it preserves, then compute whether the induced input-length exponent can possibly combine the STACS 2021 lower bound with the small-threshold magnification hypothesis. If it cannot, preserve the failure as a theorem-level negative checkpoint and identify what stronger transformation would be required.
