# NS-R001 same-context expert review — 2026-08-11

Authority: `SAME_CONTEXT_REVIEW_ONLY / PRE_CANDIDATE / NO_THEOREM_AUTHORITY`

Selected atom: `NS-R001` — determine whether the 3D Leray energy class can be upgraded, using exact Navier–Stokes structure, to a scale-critical control strong enough to invoke an established regularity theorem.

## Expert cell

### 1. PDE regularity lead — critical spaces and weak/strong theory
Background: nonlinear parabolic PDE, Leray–Hopf/suitable weak solutions, Serrin criteria, endpoint regularity.

Finding: the energy class is supercritical under the 3D scaling. Existing sharp regularity criteria are downstream gates, not a source of the missing estimate. The cleanest first research object is the gap between energy control and a scale-invariant quantity such as `L_t^∞ L_x^3`, not another restatement of global smoothness.

Strongest objection: a new inequality that merely interpolates `L_t^∞L_x^2` and `L_t^2 dot H_x^1` cannot cross the scaling barrier; it will remain on the energy line `2/p+3/q=3/2`.

Recommendation: require an exact nonlinear/geometric input beyond energy interpolation.

### 2. Harmonic-analysis and pressure lead
Background: Littlewood–Paley methods, Calderón–Zygmund pressure, local energy inequalities, critical Besov/BMO spaces.

Finding: pressure must be carried explicitly in every local argument. A proposed local estimate can appear scale-invariant while hiding nonlocal tails or radius-dependent constants. Koch–Tataru shows that the heat/bilinear framework closes at critical scale for small data, but large data destroys the contraction parameter.

Strongest objection: generic bilinear estimates plus energy cancellation are not enough; Tao's averaged model preserves too much of that structure and still blows up.

Recommendation: any future candidate must identify a true-Navier–Stokes structural identity absent from the averaged model.

### 3. Vorticity-geometry lead
Background: vorticity stretching, strain alignment, geometric depletion, vortex-line criteria.

Finding: the 2D/3D difference localizes at `omega · grad u`. A viable positive route should expose a dimensionless measure of stretching efficiency versus viscous dissipation or prove that concentration forces geometric depletion. However, alignment heuristics are dangerous because exact smooth divergence-free fields can realize intense strain-vorticity alignment locally.

Strongest objection: pointwise alignment bounds are likely too strong and may be false even for smooth fields; any geometric statement must be scale-averaged or dynamically constrained.

Recommendation: build an adversarial test-field atlas before investing in a depletion theorem.

### 4. Adversarial scaling/falsification lead
Background: counterexample construction, scaling, toy/averaged models, obstruction analysis.

Finding: the cheapest falsifier for a proposed estimate is a three-part screen: (i) exact scaling audit, (ii) smooth divergence-free high-frequency concentration families, and (iii) whether the proof transfers to Tao's averaged nonlinearity. If it survives only by using an identity not available in the averaged model, that identity becomes a load-bearing coordinate.

Strongest objection: many attractive local inequalities are either dimensionally subcritical after constants are restored or reduce to an already-known conditional criterion.

Recommendation: next action should be falsifier infrastructure, not a theorem candidate.

### 5. Formal-methods/proof-architecture lead
Background: statement binding, dependency DAGs, symbolic/numerical checker boundaries.

Finding: the first strict packet should not propose a lemma until context/memory/trace chronology is frozen. The root statement must preserve Clay's four accepted alternatives and not silently replace the prize problem with uniqueness of arbitrary weak solutions.

Strongest objection: proving a criterion or excluding one blowup ansatz is not root closure.

Recommendation: keep `first_candidate_at = null`; add a regression that reconstructs context, memory, and trace gates.

### 6. Literature/novelty and research-value lead
Background: source verification, prior-art risk, route-value assessment.

Finding: the selected atom is not itself novel; it is a research-control re-representation of the established criticality barrier. Its value is to force every next candidate to say exactly how it crosses the energy-to-critical gap and which known obstruction it evades.

Strongest objection: the literature contains many regularity criteria; generating another conditional criterion with stronger hypotheses has low information value.

Recommendation: prioritize a discriminator that can kill an entire family of proposed depletion/critical-self-improvement estimates cheaply.

## Disagreement retained

The vorticity lead favors geometry-first search; the harmonic-analysis lead warns that geometry without a pressure/multiscale closure may not survive localization. The adversarial lead therefore recommends a representation-neutral falsifier atlas as the first action. No role claims that a critical self-improvement inequality exists.

## Selected next action

Construct a **pre-candidate adversarial atlas** of smooth divergence-free configurations and scaling families that stresses any future production-versus-dissipation or geometric-depletion quantity. The atlas should include concentrated rescalings, high strain/vorticity alignment, near-Beltrami/helical configurations, and fields engineered to separate local stretching from pressure/nonlocal effects. This is falsifier infrastructure, not a theorem candidate.

The first mathematical candidate may be proposed only after the strict packet test passes and the candidate explicitly states the exact true-Navier–Stokes structure it uses that is absent from the averaged blowup model.
