# RAKL Main-Figure and Extended-Data Plan

Status: figure contracts frozen before headline empirical results. Data-dependent panels remain receipt-bound placeholders until the registered experiments run.

## Global figure contract

**Target output:** arXiv-ready and adaptable to a top-tier methods/computational-science journal.  
**Visual rule:** one figure = one scientific conclusion.  
**Editable sources:** required for every schematic and plot.  
**Data panels:** generated only from immutable machine-readable result receipts.  
**Minimum rendered text:** 7 pt target, never below 5 pt.  
**No manual headline numbers:** labels, intervals and counts must come from figure-source tables.  
**No hidden clipping:** every final export must be inspected at manuscript physical size for text, marker, legend and equation overflow.

Concept schematics should be authored as editable vector/TikZ/SVG. Quantitative result panels should use the repository's Python/matplotlib stack once data exist, with one canonical plotting source per figure and one source-data file per plotted panel.

---

# Figure 1 — RAKL as a computational research scientist

**Core conclusion:** RAKL separates generative cognition from an external evidence-governed scientific state and couples scientific work to metacognitive learning without giving the proposer authority over truth.

**Archetype:** schematic-led composite.

**Target size:** two-column/full-width, approximately 178 mm wide.

**Panel map**

- **a. Functional researcher state.** Show
  \[
  \mathfrak R_t=(K_t,\mathcal Z_t,\Omega_t,\Pi_t,\mathcal G_t,\mathcal M_t,\mathcal X_t,\mathcal R_t)
  \]
  as eight functional compartments: evidence memory, explanatory world models, method skills, executive policy, research agenda, metacognition, experience/transfer memory and resources.
- **b. Evidence-governed cognition loop.** `observe/search -> propose -> verify -> canonical update -> residual -> next action` with a visual firewall between proposer and canonical state.
- **c. Learning loop.** A scientific residual splits into a domain residual and a method residual. Method residuals route to existing strategy, help/evidence acquisition, external assimilation or constructive invention; promotion requires fresh assurance.

**Hero evidence:** the architecture itself, not an empirical number.

**Validation evidence:** small callouts to executable support layers: immutable negative history, authority poset, context compiler, challenge-learning controller, promotion gate.

**Reviewer risks:** diagram could appear as generic agent orchestration. Counter this by making the authority firewall, dual science/method residual, typed epistemic state and fresh-assurance gate visually dominant.

---

# Figure 2 — From papers to a contextual Knowledge Atlas and target path

**Core conclusion:** RAKL does not compare papers as global wholes; it decomposes contextual projections, establishes typed transitions, preserves obstructions, and searches for an authority-valid support structure to a target.

**Archetype:** schematic-led composite.

**Panel map**

- **a. Atomic source decomposition.** Three example papers/datasets become contextual claim/evidence charts rather than single nodes.
- **b. Typed atlas.** Show local charts \(C_i=(U_i,\phi_i,\gamma_i,e_i,\alpha_i)\), typed transition maps and an explicit non-preserved-structure annotation.
- **c. Non-forced gluing.** One compatible region glues; one incompatibility produces an obstruction/identified set rather than a forced global model.
- **d. Goal-conditioned support hyperpath.** Highlight the smallest admissible subgraph supporting target \(\tau\). A missing prerequisite is shown as an epistemic cut \(B^*_{\tau}\).

**Reviewer risk:** “this is just a knowledge graph.” The figure must show contexts, typed relation/authority labels, gluing obstruction and target cut-set semantics that ordinary graph visualization does not encode.

---

# Figure 3 — Scientific authority and non-escalation

**Core conclusion:** evidence can strengthen one scientific coordinate without silently strengthening another.

**Archetype:** asymmetric schematic + quantitative/known-answer grid.

**Panel map**

- **a. Authority poset.** Display certificate coordinates
  \[
  \alpha(c)=(G,R,M,I,D)
  \]
  without implying a total order. Use example claims showing incomparable authority vectors.
- **b. Forbidden cross-axis jumps.** Observational equivalence \(\not\Rightarrow\) mechanism; mechanism plausibility \(\not\Rightarrow\) identification; decision robustness \(\not\Rightarrow\) mechanism; citation multiplicity \(\not\Rightarrow\) independent evidence.
- **c. Defining-controls ablation result grid — DATA DEPENDENT.** For each RAKL ablation, plot its preregistered selective failure mode: false contradiction, false merge, mechanism/identification leakage, negative-history loss, false saturation, hidden-gap miss. Use paired effect estimates with intervals, not a radar chart.

**Statistics needed:** paired or cluster-aware differences according to benchmark design; intervals and multiplicity policy visible in legend/source data.

**Reviewer risk:** if ablations are not selective, the formal coordinates may be vocabulary rather than mechanisms. That result is itself a falsifier and must remain visible.

---

# Figure 4 — Governed self-evolution under challenge

**Core conclusion:** RAKL distinguishes local optimization from transferable method improvement and preserves failed generations.

**Archetype:** quantitative lineage + process schematic.

**Panel map**

- **a. Challenge-learning state machine.** failure attribution -> persist/switch/help/acquire evidence/repair/invent-or-assimilate -> frozen discriminator -> fresh assurance.
- **b. Evolution lineage — DATA DEPENDENT.** Horizontal generation tree with every challenger, including `NO_IMPROVEMENT`, `META_OVERFIT`, `BLOCKED` and successful scoped evolution.
- **c. Development vs assurance effects — DATA DEPENDENT.** Paired scatter or forest plot of \(\Delta_D\) and \(\Delta_A\); visually separate generations that improve development but regress on assurance.
- **d. Cost per validated capability — DATA DEPENDENT.** Tokens/tool calls/wall time or normalized resource cost for fixed, generic-reflection, unconstrained-self-editing and governed-RAKL conditions.

**Reviewer risk:** self-improvement benchmark contamination. Figure legend must state hidden-label isolation, fresh-assurance policy, evidence-lineage policy and evaluator protection.

---

# Figure 5 — Bounded scientific cognition over an expanding archive

**Core conclusion:** RAKL can accumulate long-term scientific knowledge and method experience without making the LLM prompt grow with the archive.

**Archetype:** schematic + quantitative efficiency plot.

**Panel map**

- **a. Four memory tiers.** immutable archive -> rebuildable indexes/multi-resolution views -> task-specific epistemic working set -> LLM prompt.
- **b. Mandatory epistemic context.** Show falsifiers, negative history, contradiction sides, assumptions, mechanism ancestry and evaluator identity as non-droppable atoms.
- **c. Compression-reconstruction curve — DATA DEPENDENT.** Held-out scientific reconstruction/performance versus active context tokens for full history, recency truncation, similarity top-k, summary-only and RAKL bounded context.
- **d. Failure mode.** Mandatory set exceeds budget -> `CANNOT_COMPILE`, not silent truncation.

**Statistics needed:** matched task packets, same model/budget/evidence, bootstrap or task-cluster intervals, token counter identity.

**Reviewer risk:** prior art in memory tiers and prompt compression. The figure must focus on epistemically mandatory retention and fail-closed overflow, not claim generic hierarchical memory novelty.

---

# Figure 6 — Real quant-finance trial: spot science first, Polymarket downstream

**Core conclusion:** the real trial evaluates whether RAKL can build a coherent descriptive and predictive spot-movement science and whether the challenge makes RAKL itself better.

**Archetype:** schematic-led composite + quantitative result panels after execution.

**Panel map**

- **a. Causal application architecture.** local microstructure evidence + global crypto state -> descriptive spot atlas -> predictive 5m/15m spot-path distribution -> authenticated oracle/settlement transform -> downstream Polymarket. Polymarket is visually downstream and cannot repair the spot model.
- **b. Descriptive closure map — DATA DEPENDENT.** Heatmap/table of registered descriptive coordinates (return distribution, volatility, jumps/tails, activity, memory, liquidity/flow, global state, cross-asset/venue, observation/clock), with scoped authority and residual status.
- **c. Predictive tournament — DATA DEPENDENT.** Forest plot of proper-score improvement relative to the strongest lawful parent at 5m and 15m, including the primary \(\Delta_{joint}=\min(R_D,R_G)-R_{DG}\) estimand and interval/materiality threshold.
- **d. Transport/calibration — DATA DEPENDENT.** Compact leave-day/coin/venue transport and calibration summary; do not combine incompatible scales into one scalar.
- **e. Method-learning overlay — DATA DEPENDENT.** Mark the RAKL method version used at each major scientific milestone and any validated method upgrade triggered by the project.

**Reviewer risk:** selective model search in finance. The figure must trace every headline point to the frozen tournament and immutable receipt; exploratory overfit teachers appear only as hypothesis-generation instruments, never as confirmation results.

---

# Extended Data / Supplementary figures

1. **Closest-work component matrix.** Rows: Co-Scientist, Robin, AI Scientist-v2, Kosmos, SciAgents, PaperQA2, DGM, EvoSkill, SkillFoundry, EvoAgentBench, CausaLab, RAKL. Columns separate literature/world-state organization, contextual relation algebra, authority non-escalation, obstruction-aware gluing, negative-history monotonicity, semantic/evidence-lineage saturation, bounded epistemic context, external method assimilation, governed self-evolution and fresh assurance. Use checkmarks only for directly evidenced capabilities; uncertainty remains `?`.
2. **Formal state-transition map.** Full \(K_t\) coordinates and allowed read/write transitions for all 24 method surfaces.
3. **Measurement/UQ worked example.** Affine transform and covariance propagation, followed by a nonlinear delta-method example and a rejected RSS example lacking independence.
4. **Relation-composition hostile worlds.** Examples of valid and invalid multi-hop scientific bridges.
5. **Evidence-lineage dependence.** Several apparently independent sources/agents collapsing onto shared evidence ancestry.
6. **Missing-operator discovery benchmark.** Gap detected vs operator identified vs fresh transfer confusion matrix.
7. **Method assimilation lifecycle.** External framework -> atomic operator -> normalization/dedup -> shadow/parallel/reject -> transfer -> governed promotion.
8. **Constructive invention lifecycle.** Residual -> positive-goal contract -> candidate formalism -> structural/limiting-case tests -> discriminating predictions -> target validation.
9. **Complete self-evolution generation lineage.** Every failed, blocked, null and successful generation.
10. **Full Polymarket/spot baseline ladder and ablations.** All preregistered models, not only headline winners.
11. **Spot descriptive atlas by context.** Assets, venues, regimes and horizons.
12. **Release/provenance graph.** Source SHA, environment, data transforms, result receipts, figure source data and manuscript artifact identity.

---

# Figure QA gate

Before an arXiv or journal artifact is released:

1. regenerate every data figure from its source-data/receipt file;
2. export editable vector PDF/SVG for line art and high-resolution raster only where necessary;
3. inspect every panel at final physical size;
4. verify no cropped text, legend, equation, marker or error bar;
5. verify consistent terminology, capitalization, axis units and precision;
6. verify all panel labels and legend claims match the manuscript;
7. verify uncertainty definitions and sample/cluster units are visible;
8. verify source data contain every plotted value;
9. verify no placeholder/result token remains in a release candidate;
10. run an independent visual and statistical review before journal submission.
