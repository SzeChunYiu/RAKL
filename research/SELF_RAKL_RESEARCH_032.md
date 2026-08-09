# SELF-RAKL Research Round 032 — Epistemic Pathfinding, Missing-Corner Completion, and Post-Saturation Expansion

Date: 2026-08-09  
Starting main: `260d9dcdc47cfc7c3dce0bd9d4379fd17ef55f3a`  
Change class: research/docs only; no active runtime or Constitution change.

## Trigger

The user identified two connected questions:

1. if papers/research objects form a lattice, is scientific inquiry better modeled as finding a path through that lattice toward a target theory/answer?
2. if the lattice has a missing corner that blocks every path, can RAKL identify and fill it; and can RAKL continue expanding after saturation without further external input?

## Panel

- graph algorithms / formal methods researcher: distinguish simple paths from multi-premise support hypergraphs and characterize cut sets;
- philosophy-of-science / epistemology reviewer: distinguish connectivity, explanation, support, and authority;
- active-learning / experimental-design researcher: route gap-closing actions by expected target relevance and mechanism separation per cost;
- scientific-discovery / LLM systems researcher: compare graph-based hypothesis chains and autonomous conjecture generation;
- context-systems engineer: exploit target-conditioned path corridors to reduce LLM context growth;
- adversarial reviewer: attempt to turn generated bridge candidates into unsupported target authority and require fail-closed semantics.

## Repository projection

The current Knowledge Atlas already supplies the local-chart, transition-map, gluing, obstruction, and recursive-fiber primitives. An obstruction can already represent a missing transition map, missing context coordinate, non-identifiability, incompatible observation process, or unresolved identity.

The current theoretical framework already records `open gap`, `request data`, `design experiment`, and `challenge the method` as admissible actions; residuals open the smallest implicated child fibers.

The current saturation protocol already separates knowledge saturation from problem closure and explicitly licenses disciplined R10 invention after scoped saturation while forbidding arbitrary invention.

The existing multi-hop bridge composition layer already distinguishes navigable local chains from stronger composable transfer hypotheses and forbids endpoint authority minting from path existence alone.

The missing theoretical object was the **target-conditioned support structure** and its dual object, the **minimal blocking gap/cut set**.

## External projections

Materially adjacent external routes were checked.

### SciAgents — arXiv:2409.05556

Uses ontological knowledge graphs, LLMs, and multi-agent reasoning to uncover interdisciplinary relationships and generate/refine scientific hypotheses.

Projection for RAKL: scientific graph exploration and cross-domain paths are established prior art; path existence alone cannot be claimed as novel.

### HypoChainer — arXiv:2507.17209

Combines LLMs, knowledge graphs, expert interaction, hypothesis-chain construction, and weak-link strengthening for validation prioritization.

Projection for RAKL: explicit hypothesis-chain navigation and strengthening weak graph links are close prior art for the missing-corner intuition.

### DARK — arXiv:2510.11462

Unifies deductive and abductive reasoning on knowledge graphs and iteratively generates/validates candidate logical hypotheses.

Projection for RAKL: abductive missing-link generation is not novel by itself.

### LeanConjecturer — arXiv:2506.22005

Generates large numbers of formal conjectures from existing mathematical contexts and filters them for syntactic validity and non-triviality.

Projection for RAKL: after-input conjectural expansion is established; RAKL must distinguish proposal-space growth from empirical authority.

### ProjectionBench — arXiv:2605.30284

Evaluates scientific hypothesis generation under progressively disclosed information, directly probing hypothesis generation with limited context.

Projection for RAKL: no-input/minimal-input hypothesis generation is empirically testable, but generated hypotheses remain hypotheses rather than new observations.

## Retained semantic objects

### R32-O1 — TARGET_CONDITIONED_SUPPORT_HYPERPATH

The target object is not generally a simple graph path. A scientific answer often requires several premises to converge, so use an authority-typed support hypergraph/subgraph.

A registered target is

\[
\tau=(q,\alpha,\gamma),
\]

and RAKL searches for the smallest support structure capable of licensing that target without context or authority drift.

### R32-O2 — EPISTEMIC_CUTSET_GAP

If no admissible target-support structure exists, identify a minimal unresolved set intersecting every valid route.

The gap may be a missing context coordinate, transition map, mechanistic intermediate, calibration, measurement, experiment, ontology relation, identity resolution, lemma, parameter, or formalism.

### R32-O3 — GAP_COMPLETION_NON_AUTHORITY

A candidate completion generated by an LLM, graph model, analogy engine, or formal system does not fill the scientific gap merely by making the graph connected.

Generated completions remain proposals until the evidence gate validates the required transition/claim.

### R32-O4 — POST_SATURATION_EXPANSION_TAXONOMY

Scoped saturation permits multiple kinds of further expansion:

1. deductive consequences;
2. abductive gap proposals;
3. analogical/cross-domain proposals;
4. re-projection under a new QoI/context;
5. disciplined R10 formal/mechanistic invention;
6. active acquisition of genuinely new evidence.

Only new world/evidence interaction can create new empirical observations.

### R32-O5 — PATH_CORRIDOR_CONTEXT_COMPILATION

Goal-conditioned pathfinding offers a new efficiency route: compile only the target, surviving support structures, blockers, relevant negative history, and evidence pointers into the LLM context.

This suggests a joint validity-efficiency benchmark rather than maximizing total lattice materialization.

## Important negative result / novelty narrowing

Do not claim novelty for:

- knowledge-graph path reasoning;
- hypothesis chains;
- strengthening weak graph links;
- abductive knowledge-graph completion;
- automated conjecture generation;
- scientific graph exploration.

The candidate RAKL distinction is the integration of target-conditioned path/gap reasoning with contextual relation typing, scoped authority, negative history, saturation semantics, and fail-closed proposal/evidence separation.

## Scientific answers to the triggering questions

### Is research a path inside the lattice?

Partly. A path is a useful intuition, but the general object should be a **support hyperpath/subgraph** because scientific conclusions can require multiple premises simultaneously.

### Can RAKL find a missing corner that blocks the path?

Conceptually yes: treat it as an epistemic cut set and route the smallest gap-closing fiber. What is not yet empirically established is whether an executable RAKL planner localizes such gaps better or more efficiently than strong graph/search baselines.

### Can RAKL fill the piece?

It can search, derive, reconcile, propose, or design an experiment to fill it. It must not label the piece filled until the appropriate evidence/derivation validates it. A valid outcome can also be proof of non-identifiability or impossibility under the current evidence regime.

### Can RAKL expand without further input after saturation?

It can expand the proposal/derived lattice by deduction, abduction, analogy, re-projection, and formal invention. Without new external evidence it cannot mint new empirical observations. If it executes a new experiment or obtains a new source, that new evidence can reopen the saturated fiber.

## Research portfolio update

Exploit:
- connect target-conditioned path corridors to bounded-context compilation.

Diversify:
- compare support-hyperpath search with knowledge-graph chain and abductive-reasoning baselines.

Moonshot:
- automatic epistemic cut-set localization followed by experiment/formalism invention.

Meta-RAKL:
- use the same mechanism to find missing method prerequisites blocking publication-grade RAKL closure.

## Saturation

Round 032 is `ACTIVE_NON_FLAT`.

Reasons:

- five retained semantic objects;
- future executable support benchmark is frozen but not run;
- no independent flat round exists for this new target-conditioned path/gap fiber;
- no real scientific task has yet demonstrated that cut-set routing improves valid closure or context efficiency.
