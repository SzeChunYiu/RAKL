# YM-S1 primary-source packet — spectral / lattice-RG lane

**Date frozen:** 2026-08-11  
**Authority:** `PRIMARY_SOURCE_CONTEXT / NO_SOLUTION_CLAIM / NO_NOVELTY_CLAIM`

This packet binds only source claims needed to define and falsify the first spectral/lattice-RG atom. It is not a survey and does not promote any source theorem beyond its stated scope.

## Root statement

### Jaffe–Witten / Clay Mathematics Institute

Arthur Jaffe and Edward Witten, *Quantum Yang–Mills Theory*.

- Official problem description: https://www.claymath.org/wp-content/uploads/2022/06/yangmills.pdf
- Clay problem page: https://www.claymath.org/millennium/yang-mills-the-maths-gap/

**Bound use:** the root requires a non-trivial four-dimensional quantum Yang–Mills theory for every compact simple gauge group and a finite positive mass gap in the reconstructed physical theory. Fixed-cutoff lattice results, numerical evidence, or confinement-only statements are not root closure.

## Reflection positivity and transfer matrix

### Osterwalder–Seiler (1978)

K. Osterwalder and E. Seiler, *Gauge field theories on a lattice*, Annals of Physics 110 (1978), 440–471. DOI: https://doi.org/10.1016/0003-4916(78)90039-8

**Source result used here:** the Wilson-lattice framework satisfies physical/reflection positivity under the paper's hypotheses, yielding a positive self-adjoint transfer matrix; the paper also proves strong-coupling infinite-volume analyticity and Wilson confinement bounds.

**Non-transfer:** positivity/transfer-matrix existence does not itself prove a uniform spectral gap or continuum Yang–Mills.

## Strong-coupling correlation decay / lattice mass-gap proxy

### Shen–Zhu–Zhu

Hao Shen, Rongchan Zhu, Xiangchan Zhu, *A stochastic analysis approach to lattice Yang–Mills at strong coupling*, arXiv:2204.12737; Commun. Math. Phys. 400 (2023).

- Primary preprint: https://arxiv.org/abs/2204.12737

**Source result used here:** in explicit strong-coupling regimes for lattice `SO(N)` and `SU(N)`, the authors prove infinite-volume uniqueness, Poincaré/log-Sobolev inequalities, and exponential decay of correlations for a broad observable class, described in the paper as a positive mass gap for the infinite-volume lattice measure.

**Non-transfer:** the stochastic/Langevin functional-inequality gap is not automatically the physical Hamiltonian gap. The result is at fixed lattice cutoff/strong coupling and does not supply the weak-bare-coupling continuum trajectory.

## Weak-coupling multiscale control

### Balaban (1987)

Tadeusz Bałaban, *Renormalization group approach to lattice gauge field theories I. Generation of effective actions in a small field approximation and a coupling constant renormalization in four dimensions*, Commun. Math. Phys. 109 (1987), 249–301.

- DOI: https://doi.org/10.1007/BF01215223

**Source result used here:** four-dimensional pure gauge theory is treated by rigorous multiscale RG in a small-field approximation, with localized effective actions and coupling-constant renormalization.

### Balaban (1989)

Tadeusz Bałaban, *Large field renormalization II. Localization, exponentiation, and bounds for the R operation*, Commun. Math. Phys. 122 (1989), 355–392.

- DOI: https://doi.org/10.1007/BF01238433

**Source result used here:** the large-field programme closes ultraviolet-stability bounds at its stated scope.

**Non-transfer:** ultraviolet stability/effective-action control does not by itself produce an infrared physical mass gap, a complete gauge-invariant source algebra, or a theorem transporting a gap through the full continuum scaling trajectory.

## Wilson-loop area law as a calibration, not a gap theorem

### Cao–Nissim–Sheffield (2025)

Sky Cao, Ron Nissim, Scott Sheffield, *Expanded regimes of area law for lattice Yang–Mills theories*, arXiv:2505.16585.

- Primary preprint: https://arxiv.org/abs/2505.16585

**Source result used here:** rigorous area-law regimes for pure lattice Yang–Mills are extended, including large-`N` regimes for `U(N)`.

### Cao–Nissim–Sheffield (2025)

Sky Cao, Ron Nissim, Scott Sheffield, *Dynamical approach to area law for lattice Yang–Mills*, arXiv:2509.04688.

- Primary preprint: https://arxiv.org/abs/2509.04688

**Source result used here:** the argument verifies a mass-gap condition from the authors' cited dynamical framework and uses it to derive Wilson area law in specified gauge-group/parameter regimes.

**Directionality warning:** this source is evidence against silently reversing the implication. In that route, a mass-gap-type condition is an input to area law; area law is not automatically a proof of the full transfer-matrix gap.

### Nissim (2026)

Ron Nissim, *Deconfinement For SO(3) Lattice Yang–Mills at Strong Coupling*, arXiv:2605.16162.

- Primary preprint: https://arxiv.org/abs/2605.16162

**Source result used here:** `SO(3)` lattice Yang–Mills fails Wilson's confinement criterion in a strong-coupling regime.

**Calibration consequence:** Wilson-area-law confinement is not a universal proxy for the Clay mass-gap obligation across compact simple groups. Any root-relevant bridge must state exactly which observable sector detects the physical low-energy spectrum.

## Euclidean reconstruction

### Osterwalder–Schrader

Konrad Osterwalder and Robert Schrader, *Axioms for Euclidean Green's functions*, Commun. Math. Phys. 31 (1973), 83–112, and *Axioms for Euclidean Green's Functions II*, Commun. Math. Phys. 42 (1975), 281–305.

- Primary scan / publisher archive: https://projecteuclid.org/journals/communications-in-mathematical-physics/volume-42/issue-3/Axioms-for-Euclidean-Greens-functions-II-with-an-Appendix-by/cmp/1103899050.pdf

**Bound use:** a continuum spectral statement belongs only after the Euclidean objects satisfy the hypotheses needed for reconstruction. The spectral lane may formulate finite-cutoff operator lemmas, but root promotion must bind them to the same continuum Schwinger/Wightman theory as the existence lane.

## Proposal-only analogy source

Ning Bao, *Confinement as Decoding: Higher Form Codes and Lattice Yang-Mills Theory*, arXiv:2608.02452 (2026).

- Primary preprint: https://arxiv.org/abs/2608.02452

**Authority:** `PROPOSAL_ONLY_ANALOGY`. It motivates an explicit distinction between global/extended-sector suppression and local spectral information. It supplies no Clay-scale theorem and no Yang–Mills method authority.

## Frontier conclusion bound to YM-S1

The source packet supports seven separate obligations:

1. a reflection-positive physical transfer-matrix/Hamiltonian construction;
2. a quantitative finite-cutoff spectral/correlation estimate;
3. thermodynamic-volume uniformity;
4. spectral visibility/completeness of the controlled gauge-invariant sources;
5. an RG/coarse-graining comparison law for the gap-sensitive quantity;
6. correct physical-unit scaling as lattice spacing tends to zero;
7. convergence/reconstruction strong enough to identify the limiting physical spectrum.

No source above closes all seven simultaneously. The first spectral lane therefore treats any argument omitting one obligation as incomplete rather than compensating with evidence from another.
