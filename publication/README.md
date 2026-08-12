# Orion publications

This is the reader-facing publication directory for the **Orion** research series — an
evidence-governed framework for LLM-mediated scientific research. It contains six
canonical paper packages.

> **Naming.** The framework is named **Orion**. The internal code namespace `RAKL`
> (and frozen identifiers such as `RAKL_LEARNING`, `RAKLV3State`, `RAKL_math`) is
> retained verbatim to preserve the provenance of frozen experiments, receipts and
> job identities. Publication numbering may change; frozen identities do not.

**Author:** Sze Chun Yiu
**Affiliation:** Stockholm University
**Corresponding email:** sze-chun.yiu@fysik.su.se

## Papers

1. `papers/paper-01-epistemic-mechanics/` — **Epistemic Mechanics for Evidence-Governed Scientific Research**
2. `papers/paper-02-structural-mechanics/` — **Structural Mechanics: Directional Structural Witnesses for Fail-Closed Cross-Domain Transfer**
3. `papers/paper-03-method-evolution-mechanics/` — **Method-Evolution Mechanics: From Experience to Method in LLM Research Systems**
4. `papers/paper-04-structural-learning-mechanics/` — **Structural Learning Mechanics: A Preregistered Protocol for Learner-Conditioned Structural Data Allocation**
5. `papers/paper-05-verified-discovery-in-mathematics/` — **Verified Discovery in Mathematics: An Assurance Architecture for LLM-Mediated Mathematical Research**
6. `papers/paper-06-rakl-scientific-research-engine/` — **Orion Scientific Research Engine: Evidence-Governed AI-Assisted Scientific Research** (capstone)

Each package exposes its canonical TeX entry point as `main.tex` (Paper VI as
`source/main.tex`). Release PDFs are stored beside it once the exact-source build passes.

## Paper roles

The six papers are intentionally complementary:

1. **Paper I — Epistemic Mechanics** formalizes the scientific-authority/state projection: proposal ≠ authority, the multi-axis authority poset, freeze-before-outcome discipline.
2. **Paper II — Structural Mechanics** is the structural-transfer core: directional, quantity-of-interest- and boundary-scoped witnesses for fail-closed cross-domain reuse, with a preregistered objective confirmatory result and a preliminary external-model applicability-gate comparator.
3. **Paper III — Method-Evolution Mechanics** studies governed experience→method evolution (failure → diagnosis → lesson/method → fresh assurance).
4. **Paper IV — Structural Learning Mechanics** is a **design-and-protocol preprint** (no empirical claim): the mechanics of learner-conditioned structural data allocation plus a frozen Phase 0–4 training protocol. A standalone *empirical* Paper IV is gated on authorized training and decision gate #462.
5. **Paper V — Verified Discovery in Mathematics** specializes the framework to mathematical research, where an LLM may guide search but theorem authority stays verifier-gated.
6. **Paper VI — Orion Scientific Research Engine** is the capstone integrating Papers I–V into the whole-framework architecture and its honest evidence status.

## Honest status

The framework establishes software/formal architecture, a measurable experimental
programme, and a real external-model comparator showing the applicability gate reduces
invalid-transfer false-accepts. It does **not** by itself establish universal
continual-learning gain, autonomous scientific invention, or absolute completeness;
several coordinates (independent human review, in-ladder capable-model training, broad
cross-domain generalization) remain explicitly open. Each paper states its own limits.

Editorial/review/reference/figure-production material is kept outside this directory;
research experiments, receipts and scientific provenance remain outside the canonical
reader-facing packages.
