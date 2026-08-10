# Round 045 Nature-skills technical review

Date: 2026-08-10

Status: internal same-context pre-submission review. This is **not independent peer review**. The environment did not provide isolated reviewer contexts, so the `nature-reviewer` mutual-blindness condition cannot be claimed. The report instead uses sequential fixed lenses and preserves that limitation explicitly.

Nature-skills source revision: `Yuan1z0825/nature-skills@a816314de0bb985e7034886e01596059522255b9`.

## Review setup

**Input scope.** RAKL V2.1 hardening branch through the matched same-model microtrial preregistration, with V2 manuscript, Round 043 pendulum demo, Round 044 lattice/archive receipts, atomic lifecycle and memory specifications.

**Assessment boundary.** This pass evaluates whether the new metrology, memory, discovery and microtrial additions are technically defensible enough to enter the manuscript and figures. It does not assess the unexecuted headline matched-workflow, self-evolution or real quant-finance results.

**Internal expert lenses.** These are work roles, not external reviewers.

1. Formal-method and knowledge-representation lens. Checks whether quantities have invariant meanings and whether a representation change can manufacture a result.
2. Information/memory and systems lens. Checks compression, provenance, storage, active-context scaling and resource accounting.
3. Experimental-design and adversarial-evaluation lens. Checks matching, leakage, evaluator chronology, metric gaming and claim boundaries.
4. Publication/figure lens. Checks whether each displayed number has one auditable source and whether a figure makes a defensible one-sentence claim.
5. Hostile novelty/search lens. Checks whether the framework can discover adjacent prior art outside its own vocabulary.

## External literature assimilation

This round deliberately searched outside the existing autonomous-science vocabulary.

### Minimum description length

Rissanen's shortest-description view is relevant to redundancy and model-complexity thinking, but it does **not** provide a ready-made definition of RAKL knowledge volume. The RAKL atlas stores scientific objects, contexts and provenance rather than selecting one statistical model by code length. The retained lesson is narrower: an engineering metric should resist growth that can be manufactured by representational bookkeeping, and compactness should be evaluated against retained task/evidence function rather than raw object count alone.

Primary route: J. Rissanen, *Modeling by shortest data description*, Automatica 14(5), 465-471 (1978), DOI `10.1016/0005-1098(78)90005-5`.

### Information bottleneck

The information-bottleneck principle formalizes compression that preserves information relevant to a target variable. It is a useful conceptual analogue for target-conditioned working context. RAKL must not claim that its current context compiler solves an information-bottleneck objective because it does not register the joint distributions or mutual-information quantities needed by that formalism. The retained lesson is to keep **compression rate** separate from **target-relevant retained function**.

Primary route: N. Tishby, F. C. Pereira and W. Bialek, *The information bottleneck method*, arXiv:physics/0004057.

### Provenance interchange

W3C PROV-O already supplies a mature ontology for representing and interchanging provenance across heterogeneous systems. RAKL therefore should not position source ancestry or provenance graphs themselves as novel. Its narrower claim is the scientific-authority and context discipline layered on provenance and gated canonical updates.

Primary route: W3C Recommendation, *PROV-O: The PROV Ontology*, 30 April 2013.

### Personal knowledge graphs

The personal-knowledge-graph literature reinforces the Obsidian lesson. Representation, management and utilization of structured individual knowledge is an established adjacent field, so a future external-method search that remains entirely inside LLM-agent vocabulary is incomplete by construction.

Primary route: Skjæveland et al., *An Ecosystem for Personal Knowledge Graphs: A Survey and Research Roadmap*, arXiv:2304.09572.

## Major concerns before repair

### R45-M1. Lattice volume was basis-dependent and gameable

**Blocking:** Yes for any longitudinal volume claim.

**Claim pointer.** `src/rakl/lattice_metrology.py`, occupied `(fiber_id, atom_kind)` volume.

**Concern.** Renaming, splitting, merging or changing the semantics of research fibers could change the occupied-cell count even if the scientific state did not change. A later method version could therefore create apparent expansion merely by refining its ontology.

**Resolution test.** Every longitudinal volume/density comparison must be tied to an immutable measurement-basis fingerprint. A changed basis must fail the comparison rather than report growth.

**Repair.** Implemented `LatticeMeasurementBasis` with a content-derived fingerprint over basis id, fiber-partition semantics, kind-schema version, identity policy and context schema. `compare_lattices()` now returns `COMPARISON_INVALID_BASIS` when the basis differs or is present on only one snapshot. The pendulum receipt is now `METROLOGY_V2` and carries the frozen basis id/fingerprint.

### R45-M2. Geometry could be mistaken for scientific value

**Blocking:** Yes for the paper's conceptual claim about knowledge growth.

**Claim pointer.** Round 044 metrology receipt and candidate paper delta.

**Concern.** An additional atom, edge or evidence binding can increase geometric density without improving the registered scientific target. Conversely, negative evidence can be scientifically useful while closing no support path. One scalar or one geometric dashboard cannot represent these outcomes without compensatory leakage.

**Resolution test.** Define a separate target-conditioned, non-compensatory progress vector and demonstrate a transition where geometry/evidence grows without target access improving.

**Repair.** Added `EpistemicStateSummary` and `EpistemicGainVector`, reporting blocking cuts closed, support paths opened, independent evidence roots added and negative-history objects added. In the pendulum trace, `R0 -> R1` improves target access, `R1 -> R2` is fully flat, while `R2 -> R3` improves evidential robustness without opening another target path. The receipt explicitly defines value separately from volume/density.

### R45-M3. The matched microtrial did not yet account for preprocessing resources

**Blocking:** Yes for any matched-workflow inference.

**Claim pointer.** `src/rakl/matched_microtrial.py` and `research/ROUND044_MATCHED_LLM_MICROTRIAL_PREREGISTRATION.json`.

**Concern.** Identical model, corpus, evaluator and tool policies are insufficient if RAKL receives unbounded preprocessing model/tool work while the direct arm does not. Equal usage is not required because preprocessing is the intervention, but both arms must face the same external resource envelope and actual usage must remain auditable.

**Resolution test.** Freeze identical token/tool/retrieval/wall-time ceilings for both arms. Reject any execution that exceeds its ceiling. Report actual usage separately so efficiency is not hidden.

**Repair.** Added `TrialResourceCeiling`, `TrialResourceUsage` and `validate_resource_usage()`. `MatchedTrialArm` now includes the resource ceiling and `validate_matched_arms()` rejects mismatched ceilings. The preregistration still needs its JSON resource section updated before execution.

### R45-M4. External-discovery repair remains retrospective

**Blocking:** No for the methods paper. Yes for a claim that the repair has learned a generally transferable discovery skill.

**Claim pointer.** `src/rakl/discovery_coverage.py` and `research/EXOGENOUS_DISCOVERY_ROUTE_DEMO_044.json`.

**Concern.** Re-discovering Obsidian after the failure name is known can validate the routing mechanism but cannot establish prospective transfer. The repair could still overfit the named miss.

**Resolution test.** Freeze a future set of function descriptions with hidden candidate identities, run the route ensemble without those names, and score candidate recall plus false-positive cost on fresh concepts.

**Disposition.** Keep the repair as an engineering safeguard and explicit failure memory. Do not promote it to strong self-evolution evidence until prospective hidden-concept evaluation exists.

## Minor comments

1. The paper should describe MDL and information bottleneck as analogies/lineage, not as algorithms currently implemented by RAKL.
2. Provenance should be positioned against W3C PROV and related standards so the novelty boundary is not inflated.
3. `occupied_volume_cells` should never appear in a figure without the basis identifier or a caption stating that the basis is frozen.
4. A figure should visually separate geometric state, target value and physical storage. Combining them into one scalar would undo the formal separation.
5. The deterministic demo remains zero-LLM and must continue to be labelled software/mechanics evidence only.

## Publication/figure gate after repair

**Recommendation posture:** major revision remains.

The main technical blockers R45-M1 through R45-M3 have executable repairs, but the manuscript and figures do not yet expose those repairs. The existing generated growth figure still contains arrow-associated text and reports only cumulative semantic objects/novelty rather than the new basis-bound geometry/value distinction. The next round should rebuild the quantitative figures from the frozen V2 receipts, enforce the no-arrow-text design rule, integrate the new conceptual boundaries into the manuscript, and then repeat review.
