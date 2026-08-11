# Same-context expert review — NS-B1 implication matrix

**Authority:** same-context role-separated review only; **not independent review**.  
**Reviewed object:** `01_frontier/NS-B1_TYPE_I_IMPLICATION_MATRIX_20260811.md`.  
**Question:** after source normalization, what is the smallest defensible next atom in the Type-I blow-up lane, and which tempting bridges are already blocked?

## Expert cell

### 1. PDE regularity lead

**Background:** suitable weak solutions, partial regularity, critical-space criteria, blow-up rescaling and Liouville methods.

**Delegated checks**
- Verify the exact direction of Albritton–Barker Theorems 1.1 and 1.2.
- Separate a Type-I ancient witness from a generic bounded ancient solution.
- Check whether the matrix accidentally upgrades one Type-I formulation to another.

**Finding**
The source chain is clean only in the following composition: Type-I singularity gives a non-trivial mild bounded ancient solution with finite `I`; a backward sequence uniformly bounded in global `L^3` would force that ancient solution to vanish. The missing implication `I<∞ -> backward L^3 sequence` is not supplied by the source and must remain an open bridge.

**Strongest objection**
Proving that bridge for arbitrary smooth divergence-free fields would be irrelevant; the useful target must retain the mild Navier–Stokes equation.

**Vote:** `ACCEPT_MATRIX / OPEN_DYNAMICS_CHILD`.

### 2. Scaling and compactness lead

**Background:** critical scaling, concentration compactness, profile extraction, local energy compactness and non-compact symmetries.

**Delegated checks**
- Audit dimensions of `A,C,D,E` and the global `L^3` slice.
- Stress-test whether local scale-invariant control alone forces global tail tightness.
- Identify the exact non-compact coordinate lost by a norm-only argument.

**Finding**
The moving sparse-bump train in the matrix is a valid functional calibration: its local parabolic masses can remain uniformly scale controlled while infinitely many spatially separated copies make every global `L^3` slice infinite. The construction exploits spatial tail replication/escape, precisely the coordinate absent from local cylinder norms.

**Strongest objection**
This does not satisfy Navier–Stokes and therefore cannot refute a dynamics-specific trace theorem. It only kills proof families that use the definitions of `I` plus interpolation/counting without an equation-specific input.

**Vote:** `ACCEPT_SCOPED_NEGATIVE_CALIBRATION`.

### 3. Pressure / vorticity geometry lead

**Background:** pressure nonlocality, vorticity stretching, geometric depletion and local-to-global energy transport.

**Delegated checks**
- Decide whether pressure or vorticity geometry already supplies the missing tail bridge.
- Identify what a future candidate would have to control beyond local scale invariance.

**Finding**
No source-backed universal pressure-tail or vorticity-depletion statement currently closes the bridge. A future candidate should name a concrete equation-specific mechanism: pressure-coupled tail tightness, a transport restriction on sparse replication, an ancient mild representation estimate, or another property with a matching Liouville theorem.

**Strongest objection**
A qualitative phrase such as “vorticity alignment prevents blow-up” is not an atom. It needs an exact scale-invariant estimate, inheritance proof under rescaling and an adversarial class.

**Vote:** `REVISE_ANY_GEOMETRIC_CANDIDATE_UNTIL_QUANTIFIED`.

### 4. Adversarial falsification lead

**Background:** hostile examples, degenerate limits, counterexample-first theorem design and assumption-smuggling audits.

**Delegated checks**
- Attack self-similarity shortcuts.
- Attack norm-only `I -> L^3` reasoning.
- Freeze classes that every future bridge must survive.

**Finding**
Four adversarial classes must remain explicit: exact backward self-similar fixed profiles; discretely self-similar/periodic renormalized orbits; genuinely non-periodic ancient trajectories; and spatially sparse/intermittent far-field configurations. Forward self-similar solutions are a useful contrast showing that “self-similar” without time orientation and source hypotheses is not itself contradictory.

**Strongest objection**
A candidate that only excludes fixed points merely renames the already-known self-similar lane and does not advance generic Type-I rigidity.

**Vote:** `ACCEPT_ONLY_IF_NEXT_ATOM_TARGETS_THE_MISSING_COORDINATE`.

### 5. Formal-methods / statement-binding lead

**Background:** exact theorem contracts, dependency DAGs, typed authority and machine-auditable research traces.

**Delegated checks**
- Ensure no false theorem edge is added to the DAG.
- Distinguish functional calibration from a Navier–Stokes counterexample.
- Determine the next strict discovery state.

**Finding**
The DAG may record `NS-B1-FUNC-001` only as a scoped calibration negative result. `NS-B1a` must be a new child atom with status `CHILD_CONTEXT_REQUIRED_BEFORE_CANDIDATE`; a fresh child context, memory review and trace are required before theorem generation.

**Strongest objection**
Appending a theorem candidate directly to the parent trace after sharpening the atom would blur candidate identity and chronology.

**Vote:** `ACCEPT_ATOMIZATION / BLOCK_CHILD_CANDIDATE_UNTIL_NEW_GATES_PASS`.

### 6. Novelty / frontier lead

**Background:** primary-source mapping, neighboring-result search, rediscovery control and research-value assessment.

**Delegated checks**
- Determine whether the matrix itself is a novelty claim.
- Check the relation of the selected bridge to the source literature.

**Finding**
The matrix is source normalization and route pruning. The bridge is naturally exposed by composing Albritton–Barker Theorems 1.1 and 1.2; no novelty claim is appropriate. Any future dynamics-specific theorem must be searched against Type-I, ancient-solution, Lorentz/Morrey/Besov, local-energy and backward-uniqueness literature before promotion.

**Strongest objection**
Calling the bridge “new” merely because it is written as a child atom would be an authority error.

**Vote:** `ACCEPT_NO_NOVELTY_CLAIM`.

## Discussion and delegated synthesis

The cell considered four next moves:

1. generalize backward self-similar Liouville theorems immediately;
2. try direct interpolation from finite `I` to global `L^3`;
3. switch to Type-II before completing Type-I route discrimination;
4. isolate the local-parabolic-to-global-tail bridge and re-freeze context around the dynamics-specific missing coordinate.

Moves 1 and 2 were rejected by the fixed-point/general-orbit distinction and the functional sparse-tail calibration. Move 3 was retained as a sibling lane but has lower dependency readiness for this cell. Move 4 has the highest information value because either a valid dynamics-specific tail mechanism activates an existing Liouville theorem, or a counterexample/failure diagnosis sharply characterizes why Type-I control still permits non-trivial ancient behavior.

## Consensus

Open `NS-B1a` as **Dynamics-specific Type-I trace/tail bridge** and stop before theorem generation. The next run must freeze a child `MathContextFiber` whose structural coordinates include local-vs-global control, spatial tail tightness, pressure relation, mild ancient representation, translation/dilation escape, and orbit class. It must then query both success and failure memory and run a fresh expert cell before any candidate.

**Consensus authority:** `SAME_CONTEXT_ROUTE_SELECTION / SOURCE_BOUND / NO_NEW_THEOREM / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`.
