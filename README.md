# Orion — Evidence-Governed Research Operating System for LLMs

> **Naming.** The framework is named **Orion**. `RAKL` (the original "Recursive Atomic Knowledge Lattice" codename) is retained as the repository name and the internal code namespace — and in frozen identifiers such as `RAKL_math`, `RAKL_LEARNING`, `RAKLV3State`, receipt/job names, and the immutable commit URLs cited below. Those are deliberately **not** renamed: they are the frozen provenance that lets the papers' honesty claims stay verifiable. In short: **Orion is the framework; `RAKL` is the codename/namespace kept for provenance.**

Orion is a mechanism-first, recursively self-improving research operating system for solving hard problems with an LLM without reducing research to blind model search.

> **Paper 1 external-review solicitation:** External reviewers are invited through [GitHub issue #41](https://github.com/SzeChunYiu/RAKL/issues/41) using the [immutable solicitation packet at commit `9d3eb91c6bfc746d6c843f6c1c6b0f7cea887dc6`](https://github.com/SzeChunYiu/RAKL/tree/9d3eb91c6bfc746d6c843f6c1c6b0f7cea887dc6/review/paper1/external_solicitation). As observed on 2026-08-11, the issue has zero public responses. This is a solicitation, not independent review, peer review, or acceptance.

> **Paper 3 external-annotation solicitation:** Pre-label power design (#248) is frozen as `CONFIRMATORY_PACKET_POWER_LIMITED`; retain the sixteen-item v2.1 packet. External annotators, a distinct adjudicator, and a distinct external provenance auditor are invited through [GitHub issue #217](https://github.com/SzeChunYiu/RAKL/issues/217) using the bindings in `research/paper3/power_design/DECISION_RECEIPT.json`. As observed at the #248 cutoff, the issue has zero public annotation responses; private response status is `CANNOT_CHECK` from the public repository. This solicitation is not annotation evidence, review, adjudication, provenance-audit evidence, a gate pass, peer review, or publication.

## Core idea

A hard problem is not one question. It is a graph of atomic steps. Every step may itself contain many possible:

- observables;
- mathematical representations;
- microscopic mechanisms;
- assumptions;
- scales;
- observation and censoring models;
- coarse-graining or projection operators;
- identification and inference methods;
- numerical methods;
- falsifiers and counterexamples;
- data products;
- downstream quantities of interest;
- economic or decision consumers.

RAKL recursively expands those dimensions, learns the different ways the same object is described, deduplicates equivalent descriptions, finds genuine contradictions, designs experiments to separate surviving explanations, and synthesizes a higher-dimensional description of the object.

## The Apple Principle

Different papers may describe the same apple from different projections:

- one says the apple is **red**;
- one says it is approximately **spherical**;
- one says it is **sweet**;
- one studies its **texture**;
- another derives how its color changes during ripening.

These are not automatically competing theories. They may be orthogonal facets of one latent object.

RAKL therefore treats a source contribution primarily as a **projection** onto one or more facets of an object, not as a whole-object answer.

The Apple Principle now has two explicitly different discovery operators:

```text
GLUE = conservatively find and align more projections of the same underlying object
JUMP = adventurously find different objects/domains that preserve useful deep structure
```

After GLUE reconstructs a deeper object, RAKL can abstract away domain identity through relational, causal, mechanistic, dynamical, mathematical, functional, regime, and failure representations and search for distant analogues. A JUMP is a search/hypothesis operation, not target-domain evidence; transfer requires an explicit mapping witness and target validation.

See `docs/APPLE_PRINCIPLE.md`, `docs/SIMILARITY_ANALOGY_ALGEBRA.md`, and `research/SIMILARITY_ANALOGY_LOOP_PROTOCOL.md`.

The synthesis problem is:

```text
many partial projections
        ↓
facet normalization
        ↓
representation/equivalence mapping
        ↓
compatibility + contradiction analysis
        ↓
missing-facet discovery
        ↓
global object portrait
        ↓
our own derived language / formalism / mechanism
```

A contradiction is real only after conditioning on population, scale, observation process, assumptions, and semantics. “Red” and “green” may conflict, or they may describe different cultivars, ripeness states, wavelengths, or measurement protocols.

## From papers to a global picture

For an object `O`, RAKL stores source projections

\[
\pi_i(O; c_i) = y_i,
\]

where `c_i` is the context of the projection: population, scale, observation model, assumptions, method, and evidence authority.

The goal is not to vote on papers. The goal is to construct the smallest useful latent description `Z(O)` that explains the compatible projections and exposes the unresolved ones.

When possible, RAKL derives a generative/mechanistic map

\[
\text{fundamental building blocks}
\to \text{interactions}
\to \text{mechanisms}
\to \text{mesoscopic state}
\to \text{effective law}
\to \text{downstream decision}.
\]

## RAKL is recursive

Every unresolved object can be expanded with the same procedure.

A model can be decomposed into atomic operations. A proof can be decomposed into assumptions and transformations. A data pipeline can be decomposed into source, parser, units, clocks, joins, filters, targets, and estimators. Each child can open its own knowledge lattice.

Native residuals decide where to recurse next.

```text
problem
→ atomize
→ expand knowledge fibers
→ search multiple vocabularies/domains
→ normalize atomic claims
→ map equivalent representations
→ prune incompatible combinations
→ derive candidate mechanisms/formalisms
→ freeze discriminating experiment
→ test
→ inspect residual
→ reopen implicated fibers
→ repeat
```

## RAKL recursively improves RAKL

The method itself is not sacred. RAKL maintains a **meta-lattice** whose object is RAKL.

Its own atomic steps include:

1. problem decomposition;
2. workflow routing;
3. source search and fallback;
4. source reliability;
5. claim extraction;
6. terminology/ontology normalization;
7. representation-equivalence detection;
8. contradiction diagnosis;
9. knowledge-gap discovery;
10. experiment selection;
11. synthesis/formalism invention;
12. review and adversarial checking;
13. saturation/stopping;
14. evidence logging and reproducibility.

The LLM may propose better alternatives for any of these steps. Proposed changes must compete against the incumbent under explicit evaluation criteria before becoming the default.

**The LLM is a proposer and synthesizer, not the authority.** Evidence, invariants, known-answer tests, falsifiers, and explicit governance determine promotion.

## AI capability shaping

RAKL treats the research algorithm as a **capability transformer**, not just a prompt around the model.

For each atomic cognitive operation, a candidate method should declare:

```text
strengths to exploit
predictable weaknesses to suppress
amplification mechanisms
compensators / externalizers
verification oracles
typed handoff / memory contract
resource additions
falsifier
```

The goal is not to add maximum scaffolding. The goal is to use the **smallest targeted compensator** that measurably improves the same model on a frozen task packet without blocking validity regressions.

RAKL distinguishes model-utilization amplification from system gains caused by external solvers, tools, specialist models, interfaces, or extra resources. System success must not be misreported as intrinsic model improvement.

See `docs/AI_CAPABILITY_SHAPING.md` and `research/SELF_RAKL_RESEARCH_015_FROZEN_BENCHMARK.json`.

## Design lessons absorbed from `nature-skills`

RAKL adopts several architectural patterns inspired by the open-source `Yuan1z0825/nature-skills` project while remaining a distinct method:

- a **small dynamic router + versioned static modules + manifest**, so the LLM loads the right workflow rather than applying a giant prompt from memory;
- **multi-source routing and graceful fallback** rather than one search endpoint;
- **atomic literature records and deduplication** rather than flat paper lists;
- **standardized experiment/anomaly logs** so failures become reusable evidence;
- **terminology ledgers and consistency sweeps** so one object does not silently split into multiple names, or multiple objects collapse under one name;
- **mutually blind reviewer contexts**, frozen before synthesis, so self-critique does not become one narrative reinforcing itself;
- **raw archive versus promoted knowledge**, preventing automatic ingestion from rewriting the canonical knowledge base.

See `docs/NATURE_SKILLS_INTEGRATION.md` for the mapping.

## Authority levels

RAKL distinguishes:

```text
SOURCE_PROJECTION
NORMALIZED_CLAIM
EQUIVALENCE_CLASS
COMPATIBLE_MECHANISM
PREDICTIVE_SURVIVOR
MECHANISTICALLY_DERIVED
IDENTIFIED_OR_BOUNDED
DECISION_USABLE
```

A better-fitting model is not automatically a mechanism. A mechanism is not automatically identified. A prediction is not automatically a decision rule.

## Repository structure

```text
README.md
ARCHITECTURE.md
docs/
  APPLE_PRINCIPLE.md
  SIMILARITY_ANALOGY_ALGEBRA.md
  AI_CAPABILITY_SHAPING.md
  SELF_RAKL.md
  NATURE_SKILLS_INTEGRATION.md
  RAKL_EXTENSION_PROGRAMME.md
research/
  SIMILARITY_ANALOGY_LOOP_PROTOCOL.md
  SELF_RAKL_RESEARCH_011.md
  SELF_RAKL_RESEARCH_015_FROZEN_BENCHMARK.json
skills/
  rakl-core/
    SKILL.md
    manifest.yaml
    static/core/
    workflows/
schemas/
  knowledge-fiber.schema.json
  projection.schema.json
src/rakl/
  core.py
  similarity.py
  capability.py
tests/
  test_core.py
  test_similarity.py
  test_capability.py
```

## First-use workflow

For a new problem:

1. Define the object, decision/QoI, population, scale, observation boundary, and evidence cutoff.
2. Atomize the problem.
3. Create one knowledge fiber per unresolved atomic step.
4. Search exact, foundational, failure, newest, adjacent, alien-domain, and alternative-vocabulary literature.
5. Extract atomic projections rather than paper summaries.
6. Normalize terminology and mathematics.
7. Classify relationships among representations.
8. Build the compatibility-constrained global lattice.
9. Identify missing facets and contradictions.
10. Select the cheapest high-information discriminator.
11. Freeze predictions before testing.
12. Test on known-answer, hostile, and native worlds.
13. Feed the residual back into the relevant fiber.
14. Synthesize the global object portrait and derive new formalism only when existing representations cannot close the residual.
15. Run isolated adversarial review before promotion.

## Status

This repository starts as a research/control framework. It should evolve by recursively applying RAKL to its own design and by importing **principles**, not blindly copying workflows, from high-quality research-agent repositories.
