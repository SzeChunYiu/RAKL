# Yang–Mills existence and mass gap — RAKL Millennium lane

**Root control surface:** issue #87.

**Root authority:** `OPEN_PROBLEM / NO_SOLUTION_CERTIFICATE`.

**Official target:** for every compact simple gauge group `G`, construct a non-trivial quantum Yang–Mills theory on `R^4` satisfying axiomatic properties at least as strong as the Wightman/Osterwalder–Schrader schemes in the Clay problem description, and prove a positive mass gap `Δ > 0`.

## Current decomposition

- `YM0` — exact root existence + mass-gap statement.
- `YM-E` — continuum existence / axiomatic QFT branch.
- `YM-E1` — compact Euclidean construction from a controlled regulator.
- `YM-E1a` — **active atom:** observable-level cutoff removal for pure 4D Yang–Mills: obtain cutoff-uniform control of renormalized gauge-invariant observable expectations strong enough for an OS-compatible, non-trivial continuum limit.
- `YM-M` — positive spectral mass gap, with uniformity across the limits used by the construction.
- `YM-I` — infinite-volume passage to `R^4`.

The branches are deliberately separated. A compact continuum construction is not a mass-gap proof; a finite-cutoff gap is not a continuum gap; reflection positivity is not existence; weak compactness is not a non-trivial QFT.

## Same-context research cell

These are analytical roles, not independent reviewers.

1. **Constructive-QFT lead** — Euclidean measures, Schwinger functions, OS reconstruction, cutoff/volume limits.
2. **Gauge/RG lead** — gauge symmetry, Wilson lattice, asymptotic freedom, multiscale estimates, observable counterterms.
3. **Adversarial mathematical-physics lead** — limit interchange, positivity, locality, non-triviality, uniformity and hidden-assumption falsifiers.
4. **Formal-methods lead** — exact statement binding, dependency DAG, checker/trust boundary and formalizable sublemmas.
5. **Novelty/frontier lead** — primary-source coverage, claimed-solution triage and rediscovery/hidden-open-conjecture checks.
6. **Cross-domain transfer lead** — structurally witnessed method transfer only; analogies remain proposal-only.

## First-cycle state

The first strict packet freezes context, method-transfer disanalogies, dual-memory review, expert objections and a hash-chained pre-candidate trace for `YM-E1a`. No mathematical candidate is generated in that packet.

The next action is a finite-cutoff **observable-interface calibration** comparing Wilson loops, renormalized/smeared local curvature composites and source-inserted generating functionals. Candidate generation is permitted only after the calibration fixes the observable embedding, renormalization/mixing closure, reflection action, convergence topology, non-triviality witness and cheapest failure test.

All materially new work must use CURRENT `main` as framework authority and satisfy the latest RAKL context, dual-memory, trace, falsification, proof, novelty and review gates.