# YM-S1a source-visibility calibration — 2026-08-11

**Authority:** `EXACT_FINITE_DIMENSIONAL_CALIBRATION / NO_YANG_MILLS_THEOREM / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`

This artifact executes the discriminator frozen in `YM-S1-E007`. It tests one logical bridge only:

> Can exponential Euclidean decay of a **restricted** observable family certify the full transfer-matrix spectral gap when that family has not been proved spectrally complete?

The answer is **no**, by an exact three-state positive-transfer-matrix example. This is an abstract calibration of an inference pattern, not a Yang–Mills transfer matrix and not evidence for or against the Clay root.

## Exact model

Let the Hilbert space be `C^3` with orthonormal basis

`Omega, e1, e2`.

Define the positive self-adjoint transfer matrix

`T = diag(1, 1/2, 1/4)`.

The vacuum is `Omega`. With one Euclidean time step normalized to one, the associated Hamiltonian is

`H = -log T = diag(0, log 2, log 4)`.

Therefore the **true full spectral gap** above the vacuum is

`Delta_full = log 2`.

Now define the self-adjoint source

`A = |e2><Omega| + |Omega><e2|`.

Then

`<Omega, A Omega> = 0`,

`A Omega = e2`,

and, for every integer `n >= 0`,

`C_A(n) = <Omega, A T^n A Omega> = <e2, T^n e2> = (1/4)^n`.

So this source has an exact visible decay rate

`m_A = log 4`.

But `e1` is a genuine lower excitation with energy `log 2`, and it is orthogonal to the source-generated subspace `span{Omega,e2}`. Hence

`m_A = log 4 > log 2 = Delta_full`.

The tested correlator is perfectly exponential and nevertheless overestimates the full spectral gap by a factor of two in this normalization.

## Repair calibration

Add

`B = |e1><Omega| + |Omega><e1|`.

Then `B Omega=e1`, so the enlarged source family detects the true first excited state. This isolates the missing coordinate: **spectral visibility of the source-generated subspace**.

The calibration does not show that every complete source family automatically gives a useful gap bound. It separates two distinct obligations:

- `G4a — kinematic source completeness`: the chosen gauge-invariant source family has vacuum-generated span dense in the relevant physical excited-state Hilbert space;
- `G4b — common-rate decay coverage`: one proves a common positive exponential rate for a source family rich enough to satisfy `G4a`, with the exact constants/quantifiers needed to pass to the full spectrum.

A basis without a common rate does not prove a gap. A common rate on a non-dense source family does not prove a full gap.

## Fixed-lattice Yang–Mills refinement from primary literature

The calibration changes the research question rather than merely adding a warning. At fixed lattice/graph, gauge-invariant Hilbert-space completeness is not an unknown principle in general: spin-network/Peter–Weyl constructions provide spanning or orthonormal bases for compact gauge groups. Therefore the first useful Yang–Mills spectral bridge should not ask vaguely whether *some* complete gauge-invariant basis exists. It should ask whether the **particular observable/source class carrying the rigorous decay estimate can be tied to a complete/dense physical source family with one controlled rate**.

This avoids two opposite errors:

1. treating a restricted Wilson-loop/correlation family as automatically spectrally complete;
2. treating fixed-lattice basis completeness as if it already supplied a uniform decay theorem, an RG bridge, or a continuum mass gap.

## Same-context expert disposition

The six-role cell agrees on the logical counterexample. It also agrees that the repair must be target-specific:

- transfer-matrix/operator theory: `G4` must be stated as a spectral-measure support problem, not merely “correlations decay”;
- lattice gauge theory: bind the controlled observables to an explicit gauge-invariant basis/dense algebra at fixed cutoff;
- RG/asymptotic freedom: `G4` closure does not address transport across coupling regimes;
- confinement/center sectors: Wilson area-law information remains a different projection from the full neutral spectrum;
- constructive QFT/OS reconstruction: continuum cyclicity/completeness cannot be imported as a substitute for constructing the continuum theory;
- formal/novelty assurance: the three-state example is elementary calibration, not a new theorem claim.

## Typed failure

Register:

`F-YM-S1A-RESTRICTED-SOURCE-HIDDEN-STATE`

with bounded diagnosis:

`restricted_source_decay_not_full_gap`.

It applies only when the source family has not been proved dense/cyclic for the physical excited-state space. It is a warning, not a blacklist against correlation methods.

## Next child atom

Open `YM-S1a1`:

> Bind a concrete fixed-lattice gauge-invariant source basis/dense algebra to a **common-rate spectral exclusion statement** and determine the weakest exact hypotheses under which that rate lower-bounds the full finite-lattice transfer gap.

Only after the fresh memory review includes the new failure record should a mathematical candidate for this bridge be generated. Even success on `YM-S1a1` leaves `G3`, `G5`, `G6`, and `G7` independently open.
