# Paper Draft Addendum — Similarity as Surviving Distinguishing Probes

Status: manuscript module, provisional  
Date: 2026-08-09

## Why an explicit mapping is still not enough

A central design choice in RAKL is that similarity claims require explicit typed mapping witnesses rather than a single embedding score. Round-012 analysis reveals an additional problem: a mapping can be explicit yet scientifically uninformative if the permitted mapping family is sufficiently expressive to align almost any pair after the fact.

This issue is not specific to language models. Recent causal-abstraction theory makes cross-level transformations precise, while recent counterexamples show that unconstrained nonlinear alignment maps can make abstraction criteria vacuous. RAKL therefore treats **mapping capacity as part of the evidence contract**.

For relation type `tau`, a certifying witness is accompanied by an admissibility contract

\[
\Lambda^\tau=(\Phi^\tau,K,\mathcal C,N),
\]

where `Phi^tau` is the mapping family declared before candidate fitting, `K` is a capacity/complexity restriction, `C` contains relation-appropriate structural constraints, and `N` is a null-calibration plan. Depending on the scientific object, constraints may include dimensional consistency, typed roles, causal orientation, topology, invertibility, monotonicity, sparsity, intervention compatibility or transition-law preservation.

The goal is not to require simple maps in every domain. The goal is to prevent RAKL from increasing mapping freedom after seeing a desired pair until a correspondence appears.

This creates a deliberate asymmetry:

```text
candidate discovery
  expressive, diverse, high-recall mappings allowed
        ↓
structural proposal
        ↓
scientific certification
  relation-specific admissible map family
  + explicit preserved/broken structure
  + falsifiers/null controls
        ↓
target validation / scoped equivalence
```

Thus creative search can remain permissive without allowing representational flexibility to become scientific authority.

## Equivalence should be indexed by what we are allowed to ask

Similarity also depends on the available family of probes. Two systems can be indistinguishable under passive observations yet separable by intervention; two models can agree for one downstream QoI yet disagree on another; two states can share one-step behavior yet diverge over longer trajectories.

For an admissible mapping `phi`, context `Gamma`, probe family `Q`, and registered tolerances `epsilon`, RAKL uses the scoped notion

\[
A \sim^{\tau,\phi}_{Q,\epsilon,\Gamma} B
\iff
\forall q\in Q,\;
 d_q(q(A),q^{\phi}(B))\le\epsilon_q.
\]

The probe family is part of the claim. It may contain measurements, interventions, perturbations, trajectory tests, failure probes or other relation-appropriate queries.

A useful consequence follows when the map family, scope and tolerances are held fixed. If

\[
Q_1\subseteq Q_2,
\]

then equivalence under `Q2` implies equivalence under `Q1`, while the converse need not hold. Adding legitimate probes can therefore **refine** an equivalence class by splitting objects that were previously indistinguishable. It cannot, by itself, justify merging objects that were previously distinct.

This gives RAKL an operational interpretation of similarity:

> **Two objects are similar at a declared layer to the extent that they survive a declared family of attempts to distinguish them under an admissible mapping.**

This is intentionally different from claiming an intrinsic universal similarity score.

## Distinguishing certificates are scientific objects

When a candidate equivalence fails, RAKL records the successful discriminator rather than only a generic negative label. A distinguishing certificate has the form

\[
D_{A,B}=(q^*,\phi,\delta,\epsilon,\Gamma,\mathcal E),
\]

where `q*` is a registered probe for which the mapped discrepancy `delta` exceeds tolerance `epsilon` under context `Gamma`.

Examples include:

- observational agreement but divergent intervention response;
- shared equation form but incompatible dimensions or boundary conditions;
- matching present state but different transition law;
- matching role labels but reversed causal direction;
- short-horizon agreement but long-horizon divergence.

These negative certificates remain part of the atlas. If a successor later proposes that the same objects are equivalent, the old discriminator becomes a mandatory regression test unless the successor explicitly changes scope or assumptions.

This connects similarity research to RAKL's negative-history principle: knowing **how two things differ** can be more reusable than knowing that an earlier similarity score was low.

## A local dynamical view

For objects with genuine state-transition semantics, RAKL can use a behavioral or bisimulation-like local chart. The exact distance remains domain-specific, but the relation should compare both registered immediate observables and mapped future transitions, schematically

\[
d(s,t)
\approx
 d_O(O(s),O(t))
 + \gamma D\!\left(T(\cdot\mid s),T^\phi(\cdot\mid t)\right).
\]

This relation is not universal. A static theorem, a material ontology and a biological pathway need not admit an MDP-like action/transition interpretation. The Knowledge Atlas therefore treats behavioral similarity as one local representation whose assumptions must be declared, not as the global definition of similarity.

## Falsifiable consequences

The added machinery is useful only if it produces selective empirical gains on frozen hostile worlds. Registered predictions are:

1. unconstrained pair-specific maps should produce more false or vacuous correspondences than predeclared relation-specific map families;
2. explicit probe-family scopes should reduce promotion from observational equivalence to stronger causal/mechanistic equivalence;
3. distinguishing-probe memory should prevent successor mappings from repeating known false merges;
4. transition-aware similarity should reduce false merges where snapshots or equations agree but future behavior differs;
5. the discovery/certification split should preserve distant-analogy recall better than applying strict map constraints during candidate retrieval itself.

If these predicted differences do not appear under matched model, corpus, evidence and compute budgets, the additional structures should remain explanatory notation rather than active runtime complexity.

## Novelty boundary

RAKL does not claim causal abstraction, projected abstraction, bisimulation, behavioral metrics, abstraction-assisted analogy, or mapping-complexity warnings as new ideas. The narrower candidate contribution is the way these projections are assembled inside an evidence-governed scientific atlas: permissive discovery maps are separated from capacity-controlled certifying maps; equivalence is indexed by explicit probe families; decisive non-equivalence probes become immutable reusable evidence; and none of these relations may silently escalate scientific authority beyond their tested scope.
