# YM-S1a primary-source packet — source visibility and fixed-lattice completeness

**Scope:** primary literature used only to sharpen the `G4` source-visibility obligation. None of these sources proves the 4D continuum Yang–Mills mass gap.

## Osterwalder–Seiler — positive lattice transfer matrix

K. Osterwalder and E. Seiler, **“Gauge field theories on a lattice,”** *Annals of Physics* **110** (1978), 440–471. DOI: `10.1016/0003-4916(78)90039-8`.

The paper verifies physical positivity for the lattice Schwinger functions in its framework and states that this implies a positive self-adjoint transfer matrix. It also proves strong-coupling infinite-volume existence/analyticity and Wilson's confinement bound. For `YM-S1a`, this is support for the fixed-cutoff positive-transfer-matrix setting, not for source completeness or continuum-gap transport.

## Baez — spin-network spanning/completeness at fixed graph

John C. Baez, **“Spin Networks in Gauge Theory,”** *Advances in Mathematics* **117** (1996), 253–272. DOI: `10.1006/aima.1996.0012`.

For a compact connected Lie group, Baez constructs spin-network vectors spanning the gauge-invariant Hilbert space `L^2(A/G)` and describes an orthonormal spin-network basis associated with a fixed graph. This is a primary-source reason to split `G4`: fixed-graph kinematic completeness can be treated separately from the analytic problem of proving a common positive decay rate for a sufficiently complete source family.

## Burgio et al. — physical Hilbert-space basis for lattice gauge theory

G. Burgio et al., **“The basis of the physical Hilbert space of lattice gauge theories,”** *Nuclear Physics B* **566** (2000), 547–561. DOI: `10.1016/S0550-3213(99)00533-7`.

Using non-linear Fourier/Peter–Weyl analysis on compact groups, the paper constructs an orthonormal basis of the physical gauge-invariant Hilbert space of Hamiltonian lattice gauge theories and computes Hamiltonian matrix elements in that basis. The result is kinematic/fixed-lattice input. It does not provide the uniform correlation-decay, RG-transport, lattice-spacing scaling, or continuum spectral convergence needed by `YM-S1`.

## Consequence for the route

The exact three-state calibration shows that **restricted-source decay is not a full-gap certificate**. The primary fixed-lattice literature then prevents an overreaction: the repair is not to abandon correlation/spectral methods, but to bind them to an explicit complete/dense gauge-invariant source representation and a common rate.

The research obligations are therefore refined to:

- `G4a`: identify/prove the relevant fixed-cutoff physical source basis or dense algebra and its vacuum-generated spectral coverage;
- `G4b`: prove one quantitative decay/spectral estimate with the quantifiers needed to control that complete family;
- keep `G3`, `G5`, `G6`, `G7` separate.

## Deliberate exclusions

- Numerical glueball spectra are calibration only and are not used as theorem authority here.
- A Wilson-loop area law is not promoted to a theorem about the full neutral transfer spectrum.
- A stochastic/Langevin Poincaré or log-Sobolev gap is not identified with the physical Hamiltonian gap.
- Continuum local-algebra cyclicity results are not used to bypass construction of the 4D continuum Yang–Mills theory.
