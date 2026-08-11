# YM-E1a same-context pre-candidate expert review — 2026-08-11

**Authority:** `SAME_CONTEXT_REVIEW_ONLY / NOT_INDEPENDENT / NO_CANDIDATE`.

The cell reviewed the exact root contract, source packet, context fiber and current RAKL memory before selecting the next action. Each role owns a distinct failure surface; disagreements are preserved rather than averaged.

## 1. Constructive-QFT lead

**Background/role:** constructive Euclidean QFT, Schwinger functions, OS reconstruction, cutoff and thermodynamic limits.

**Finding:** `YM-E1a` is correctly upstream of the mass-gap branch. A normalization/effective-action bound cannot substitute for a continuum observable algebra. The first object must specify which correlations converge and what topology lets the Euclidean axioms survive.

**Strongest objection:** “gauge-invariant observables converge” is still underspecified. Wilson loops are natural lattice observables but do not by themselves give the local field-operator correspondence requested in the Clay description.

**Delegated check:** build a three-column observable contract for Wilson loops, smeared local curvature composites, and source-inserted generating functionals; require a separate non-triviality witness for each.

**Vote:** `REVISE` until the observable interface is frozen.

## 2. Gauge / renormalization-group lead

**Background/role:** non-Abelian gauge symmetry, Wilson lattice actions, asymptotic freedom, multiscale RG and composite-operator renormalization.

**Finding:** Balaban is the closest same-problem multiscale source, but the transfer obligation is marked/inserted observables. Composite insertions can introduce new counterterms or operator mixing; uniformity of the unmarked RG step is therefore not enough.

**Strongest objection:** a naive “differentiate the generating functional” move can silently assume the source-deformed effective action remains inside the same Banach space and that source derivatives commute with the cutoff limit.

**Delegated check:** for the first candidate family, identify the exact source/observable insertion at finite lattice spacing and enumerate every operator generated under one blocking step before any continuum claim.

**Vote:** `REVISE`.

## 3. Adversarial mathematical-physics lead

**Background/role:** hostile limit tests, positivity/locality/non-triviality failures, counterexamples to interchange of limits.

**Finding:** fixed-cutoff reflection positivity is the least mysterious part of the chain if one already has compatible convergence of the relevant reflection-positive quadratic forms. The dangerous gap is obtaining and identifying that convergence on a common algebra.

**Strongest objections:**

- weak compactness can land on a trivial or wrong theory;
- convergence of individual expectations does not automatically give convergence of all reflected products needed for OS positivity;
- an observable basis can vary with cutoff so that “the same observable” has no exact refinement map;
- small-loop limits may need divergent renormalizations and mixing.

**Delegated falsifier:** reject any observable contract that cannot state a common/refinement-compatible positive-time algebra and a finite set of reflected Gram-matrix quantities whose convergence would be checked.

**Vote:** `BLOCK` on continuum-candidate generation before the calibration; `ACCEPT` the calibration itself.

## 4. Formal-methods lead

**Background/role:** exact statement binding, proof DAGs, dependency/axiom auditing and executable finite identities.

**Finding:** the first machine-checkable surface should be finite-cutoff algebra, not the full continuum theorem. Reflection-positive Gram matrices and source-derivative identities can be represented exactly at finite cutoff; the hard analytic estimates can then be isolated as explicit assumptions/obligations rather than hidden in prose.

**Strongest objection:** a proof draft that says “take a convergent subsequence” without binding the observable embeddings, normalization and topology is not formalizable enough to audit.

**Delegated check:** define the observable-interface schema before the first candidate and make the test fail closed if any representation lacks embedding, renormalization, reflection, convergence or non-triviality fields.

**Vote:** `REVISE`.

## 5. Novelty / frontier lead

**Background/role:** primary-source verification, theorem fingerprinting, claimed-solution triage and hidden dependence on unsolved statements.

**Finding:** the historical/modern source matrix supports the obstruction, not a new theorem. Recent arXiv manuscripts claim complete solutions; their existence is a novelty/review signal only. Clay continues to list the problem as unsolved, so no root authority changes without full theorem-level verification.

**Strongest objection:** the proposed observable-level decomposition is likely standard expert knowledge and must not be advertised as mathematical novelty. Its value here is research control and proof-obligation isolation.

**Delegated check:** before any theorem candidate is promoted beyond proof-draft, search exact and structurally equivalent observable-insertion / OS-limit lemmas in primary literature.

**Vote:** `ACCEPT` the decomposition at `NO_NOVELTY_CLAIM` authority.

## 6. Cross-domain transfer lead

**Background/role:** structural analogy, method-transfer assumptions and DifferenceWitness discipline.

**Finding:** the only retained non-domain analogy is instrumented-program verification: global stability of an unmarked system does not certify the semantics/stability of marked outputs. This maps cleanly to unmarked RG stability versus observable insertions.

**Strongest objection:** the analogy becomes invalid if used to infer the form of the needed RG norm or counterterms. It only motivates making the observable mark explicit.

**Delegated falsifier:** require the first finite-cutoff calibration to show an exact transport identity or closure statement for the mark; otherwise discard the analogy rather than elaborating it.

**Vote:** `ACCEPT_AS_PROPOSAL_ONLY`.

## Cell synthesis

The cell does **not** authorize a Yang–Mills mathematical candidate yet. It selects one high-partition pre-candidate action:

> Freeze and test an **observable-interface calibration** for three representation families — Wilson loops, smeared/renormalized local curvature composites, and source-inserted generating functionals. For each family specify (i) finite-cutoff definition, (ii) refinement/common-algebra map, (iii) gauge invariance/covariance, (iv) renormalization or mixing closure, (v) reflection action and positive-time algebra, (vi) convergence topology and required uniform bounds, (vii) non-triviality/short-distance witness, and (viii) cheapest counterexample/failure test.

### Why this action wins

It separates three logically distinct questions that were easy to conflate: **observable existence**, **positivity transfer**, and **non-triviality/physical identification**. It can falsify an entire representation before expensive RG proof search, while not assuming a mass gap or an infinite-volume limit.

### Residuals opened

- `YM-E1a-R1`: choose a refinement-compatible separating observable algebra.
- `YM-E1a-R2`: prove marked RG/source-insertion closure and cutoff-uniform bounds.
- `YM-E1a-R3`: identify a non-triviality / asymptotically-free short-distance witness that survives the same limit.
- `YM-E1a-R4`: only after R1–R3, discharge OS/locality/covariance reconstruction obligations on the limit.

No residual is a theorem candidate yet.