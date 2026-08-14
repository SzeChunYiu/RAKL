# Framework document map

Generated from `research/framework_ladder/ladder.json` plus a title-level assignment of every file in `docs/`.
Read `CORE.md` first; this file is the complete index.

`[research-only]` marks a document that declares itself non-activating. See issue #627 — the quarantine
held the framework's generative half, including the navigation loop and the measurement architecture.


## L0-OBJECT — Objects, facets, projections, contexts

*Expresses:* That two sources describe the same object through different projection operators under different contexts. Without this layer, disagreement cannot be distinguished from difference-of-view.

*Papers:* I

- [`APPLE_PRINCIPLE.md`](APPLE_PRINCIPLE.md) — The Apple Principle
- [`KNOWLEDGE_ATLAS_PRINCIPLE.md`](KNOWLEDGE_ATLAS_PRINCIPLE.md) — Knowledge Atlas Principle
- [`PERSPECTIVAL_PLURALISM.md`](PERSPECTIVAL_PLURALISM.md) — Perspectival Pluralism and Robustness
- [`MEASUREMENT_AWARE_SIMILARITY.md`](MEASUREMENT_AWARE_SIMILARITY.md) — Measurement-aware similarity
- [`TERMINOLOGY_GLOSSARY.md`](TERMINOLOGY_GLOSSARY.md) — RAKL terminology glossary (lattice vs typed-relational)
- [`THEORETICAL_FRAMEWORK.md`](THEORETICAL_FRAMEWORK.md) — RAKL Theoretical Framework

## L1-TRANSITION — Typed transitions and relation algebra

*Expresses:* That a step from one object to another has a type, and that composing steps is licensed or not. Without it, any two claims can be chained.

*Papers:* I, II

- [`CLAIM_EVIDENCE_PROVENANCE.md`](CLAIM_EVIDENCE_PROVENANCE.md) — Claim–Evidence Provenance
- [`EVIDENCE_LINEAGE_DEPENDENCE.md`](EVIDENCE_LINEAGE_DEPENDENCE.md) — Evidence lineage dependence
- [`PROBLEM_SOLVING_ALGEBRA.md`](PROBLEM_SOLVING_ALGEBRA.md) — RAKL Problem-Solving Algebra
- [`COMPARATIVE_GENERATOR_TRANSPORT.md`](COMPARATIVE_GENERATOR_TRANSPORT.md) — Comparative Generator Transport
- [`FORMAL_OPTIMIZATION_SEMANTICS.md`](FORMAL_OPTIMIZATION_SEMANTICS.md) — Formal Optimization Semantics

## L2-GLUING — Context alignment, contradiction and gluing

*Expresses:* That locally consistent pieces may have no global section. This is the layer where obstructions become first-class, and Paper I's three-context parity construction lives here.

*Papers:* I, II

- [`CONTEXTUAL_ATLAS_GLUING.md`](CONTEXTUAL_ATLAS_GLUING.md) — Contextual Atlas Gluing and Global Coherence
- [`MULTI_HOP_BRIDGE_COMPOSITION.md`](MULTI_HOP_BRIDGE_COMPOSITION.md) — Multi-Hop Scientific Bridge Composition `[research-only]`
- [`SIMILARITY_ANALOGY_ALGEBRA.md`](SIMILARITY_ANALOGY_ALGEBRA.md) — RAKL Similarity & Analogy Algebra `[research-only]`
- [`MODEL_CRITICISM_AND_ASSUMPTION_SENSITIVITY.md`](MODEL_CRITICISM_AND_ASSUMPTION_SENSITIVITY.md) — Model Criticism and Assumption Sensitivity
- [`SEMANTIC_SHORTCUT_ROUTER.md`](SEMANTIC_SHORTCUT_ROUTER.md) — RAKL Semantic Shortcut Router
- [`SEMANTIC_SHORTCUT_RESEARCH_SYNTHESIS.md`](SEMANTIC_SHORTCUT_RESEARCH_SYNTHESIS.md) — Semantic Shortcut Research Synthesis

## L3-AUTHORITY — Scientific authority as a partial order

*Expresses:* That a claim's evidential standing is multi-coordinate and that only certified transitions may change it. Without it, fluency substitutes for evidence.

*Papers:* I

- [`AUTHORITY_POSET.md`](AUTHORITY_POSET.md) — RAKL Scientific Authority Poset
- [`EPISTEMIC_NONINTERFERENCE.md`](EPISTEMIC_NONINTERFERENCE.md) — EPISTEMIC_NONINTERFERENCE
- [`CONTENT_ADDRESSED_ARCHIVE.md`](CONTENT_ADDRESSED_ARCHIVE.md) — Content-addressed canonical archive
- [`EVALUATOR_DEPENDENCY_PINNING.md`](EVALUATOR_DEPENDENCY_PINNING.md) — Evaluator Dependency Pinning
- [`CONTEXTUAL_METHOD_CAPABILITY_FRONTIER.md`](CONTEXTUAL_METHOD_CAPABILITY_FRONTIER.md) — Contextual, Authority-Scoped Method Capability Frontier

## L4-NAVIGATION — Goal-conditioned reachability and support structure

*Expresses:* That solving is search for an authority-valid support structure reaching the target, and that FAILING is informative: the min-cost cut names what would have to be established. This is the framework's verb.

*Papers:* I (only as of PR #623)

- [`EPISTEMIC_PATHFINDING_AND_GAP_COMPLETION.md`](EPISTEMIC_PATHFINDING_AND_GAP_COMPLETION.md) — Epistemic Pathfinding, Gap Completion, and Post-Saturation Expansion `[research-only]`
- [`OPEN_WORLD_DISCOVERY_AND_WORKSPACE.md`](OPEN_WORLD_DISCOVERY_AND_WORKSPACE.md) — Open-World Mechanism Discovery and Workspace-Gated Research Cognition
- [`BOUNDED_CONTEXT_ARCHITECTURE.md`](BOUNDED_CONTEXT_ARCHITECTURE.md) — Bounded Epistemic Context Architecture
- [`MULTI_RESOLUTION_RECONSTRUCTABLE_MEMORY.md`](MULTI_RESOLUTION_RECONSTRUCTABLE_MEMORY.md) — Multi-resolution reconstructable memory
- [`RESEARCH_MEMORY_ARCHITECTURE.md`](RESEARCH_MEMORY_ARCHITECTURE.md) — RAKL Research Memory Architecture
- [`SOLVING_NEW_MATHEMATICS.md`](SOLVING_NEW_MATHEMATICS.md) — Solving New Mathematics with Orion — an explicit protocol
- [`MATHEMATICAL_RESEARCH_ASSURANCE.md`](MATHEMATICAL_RESEARCH_ASSURANCE.md) — Mathematical Research Assurance in RAKL
- [`MATH_RESEARCH_QUICKSTART.md`](MATH_RESEARCH_QUICKSTART.md) — Mathematical Research Quickstart

## L5-SATURATION — Bounded epistemic saturation

*Expresses:* When search may stop. Requires L4 because saturation is relative to a declared route family, and requires a finite basis to be certifiable rather than merely bounded.

*Papers:* I

- [`EPISTEMIC_SATURATION.md`](EPISTEMIC_SATURATION.md) — Bounded Epistemic Saturation
- [`KNOWLEDGE_SATURATION.md`](KNOWLEDGE_SATURATION.md) — Knowledge Saturation
- [`MANUSCRIPT_SATURATION.md`](MANUSCRIPT_SATURATION.md) — Manuscript saturation
- [`LATTICE_METROLOGY_AND_CAPACITY.md`](LATTICE_METROLOGY_AND_CAPACITY.md) — RAKL lattice metrology, learning storage and capacity control

## L6-METHOD-EVOLUTION — Experience, challenge learning and method acquisition

*Expresses:* That the method itself is an object the system can revise. Requires L5: you cannot tell whether a method change helped until you can say when search was done.

*Papers:* III, IV

- [`SELF_RAKL.md`](SELF_RAKL.md) — Self-RAKL — Recursively Improving the Research Method
- [`CHALLENGE_LEARNING_LOOP.md`](CHALLENGE_LEARNING_LOOP.md) — Challenge Learning Loop for Self-RAKL `[research-only]`
- [`GENERATIVE_MECHANICS_PROGRAMME.md`](GENERATIVE_MECHANICS_PROGRAMME.md) — Generative Mechanics — a Method-Saturation Programme
- [`FAILURE_EXPERIENCE_LATTICE.md`](FAILURE_EXPERIENCE_LATTICE.md) — Failure Experience Lattice
- [`ATOMIC_LLM_RESEARCH_LIFECYCLE.md`](ATOMIC_LLM_RESEARCH_LIFECYCLE.md) — Atomic LLM Research Lifecycle and Scientific Memory
- [`METACOGNITIVE_METHOD_COMPLETENESS.md`](METACOGNITIVE_METHOD_COMPLETENESS.md) — Metacognitive Method Completeness
- [`SELF_EVOLUTION_EVIDENCE.md`](SELF_EVOLUTION_EVIDENCE.md) — Evidence for Governed RAKL Self-Evolution
- [`RAKL_V3_EXPERIENCE_SUBSTRATE.md`](RAKL_V3_EXPERIENCE_SUBSTRATE.md) — RAKL v3 — Recursive Experience Substrate
- [`HOURLY_SELF_RND.md`](HOURLY_SELF_RND.md) — Hourly Self-RAKL R&D Protocol
- [`PSYCHOLOGY_FUNCTIONAL_COMPLETENESS.md`](PSYCHOLOGY_FUNCTIONAL_COMPLETENESS.md) — Psychology-Informed Functional Completeness of RAKL
- [`AI_CAPABILITY_SHAPING.md`](AI_CAPABILITY_SHAPING.md) — AI Capability Shaping and Research Cognitive Architecture `[research-only]`
- [`SENIOR_RESEARCHER_COGNITIVE_ARCHITECTURE.md`](SENIOR_RESEARCHER_COGNITIVE_ARCHITECTURE.md) — Senior Researcher Cognitive Architecture for RAKL `[research-only]`

## L7-ASSIMILATION — External method assimilation and constructive invention

*Expresses:* That a competitor's mechanism can be absorbed under RAKL conditions. Requires L6: assimilation is a method change, so it inherits the method-evolution gate.

*Papers:* III, VI

- [`METHOD_ASSIMILATION.md`](METHOD_ASSIMILATION.md) — Evidence-Governed Method Assimilation
- [`CONSTRUCTIVE_INVENTION.md`](CONSTRUCTIVE_INVENTION.md) — Constructive Invention in RAKL
- [`NATURE_SKILLS_INTEGRATION.md`](NATURE_SKILLS_INTEGRATION.md) — Absorbing `nature-skills` into RAKL
- [`RAKL_EXTENSION_PROGRAMME.md`](RAKL_EXTENSION_PROGRAMME.md) — RAKL Extension Programme — Preserve the Original Core `[research-only]`
- [`MECHANICS_V_VI_SPEC.md`](MECHANICS_V_VI_SPEC.md) — Orion Mechanics V & VI — Testable Specification

## Specification (read after CORE)

- [`FORMAL_SYSTEM_SPECIFICATION.md`](FORMAL_SYSTEM_SPECIFICATION.md) — RAKL Formal System Specification

## Governance

- [`CONSTITUTION.md`](CONSTITUTION.md) — RAKL Constitution
- [`RAKL_UPGRADE_PROTOCOL.md`](RAKL_UPGRADE_PROTOCOL.md) — RAKL Governed Upgrade Protocol
- [`TOKEN_BUDGET_AUTHORITY.md`](TOKEN_BUDGET_AUTHORITY.md) — Token Budget Authority
- [`RSHEA_P5_P6_PROMOTION_POLICY.md`](RSHEA_P5_P6_PROMOTION_POLICY.md) — RSHEA Paper V–VI promotion policy
- [`ENGINEERING_CLOSURE.md`](ENGINEERING_CLOSURE.md) — RAKL Engineering Closure and Release Conformance
- [`RELEASE_ARTIFACT_IDENTITY.md`](RELEASE_ARTIFACT_IDENTITY.md) — Release Artifact Identity

## Runtime and engineering

- [`RAKL_V3_API.md`](RAKL_V3_API.md) — RAKL v3 Public API
- [`RAKL_V3_IMPLEMENTATION_MANIFEST.md`](RAKL_V3_IMPLEMENTATION_MANIFEST.md) — RAKL v3 Implementation Manifest
- [`REFERENCE_RUNTIME.md`](REFERENCE_RUNTIME.md) — RAKL Reference Runtime
- [`EXECUTION_RUNTIME.md`](EXECUTION_RUNTIME.md) — Governed Execution Runtime
- [`CODING_AGENT_INTEGRATION.md`](CODING_AGENT_INTEGRATION.md) — Coding-Agent Integration
- [`RESEARCH_MACHINE_WORKFLOW_V2.md`](RESEARCH_MACHINE_WORKFLOW_V2.md) — RAKL Research Machine Workflow v2
- [`ARTIFACT_EVALUATION.md`](ARTIFACT_EVALUATION.md) — RAKL Artifact Evaluation — Reference Runtime v1
- [`RAKL_V3_AUTHORITY_HARDENING_CHANGELOG.md`](RAKL_V3_AUTHORITY_HARDENING_CHANGELOG.md) — RAKL v3 authority hardening — 2026-08-11

## Metrology and evaluation

- [`RAKL_METROLOGY.md`](RAKL_METROLOGY.md) — RAKL Metrology
- [`ORION_KPI_AND_METRICS.md`](ORION_KPI_AND_METRICS.md) — Orion KPIs & Metrics — turning framework concepts into measurable, visualizable, algorithm-driving quantities
- [`RAKL_QUANTITATIVE_EVALUATION_MODEL.md`](RAKL_QUANTITATIVE_EVALUATION_MODEL.md) — RAKL Quantitative Evaluation Model `[research-only]`
- [`RAKLBENCH.md`](RAKLBENCH.md) — RAKLBench — Benchmarking the Research Method Itself
- [`RAKL_V3_EVALUATION.md`](RAKL_V3_EVALUATION.md) — RAKL v3 Evaluation Contracts
- [`PAPER_DUAL_HEADLINE_EVALUATION.md`](PAPER_DUAL_HEADLINE_EVALUATION.md) — Paper Evaluation Strategy — Two Headline Claims

## Paper material (drafts, inserts, addenda)

- [`PAPER_ANALOGY_DISCOVERY_ADDENDUM.md`](PAPER_ANALOGY_DISCOVERY_ADDENDUM.md) — Paper Draft Addendum — Analogy Discovery as a Four-Gate Process
- [`PAPER_CONTEXT_EFFICIENCY_SECTION.md`](PAPER_CONTEXT_EFFICIENCY_SECTION.md) — Paper Draft Module — Bounded Epistemic Context for an Expanding Knowledge Atlas
- [`PAPER_EPISTEMIC_PATH_GAP_COMPLETION_SECTION.md`](PAPER_EPISTEMIC_PATH_GAP_COMPLETION_SECTION.md) — Paper Addendum — Goal-Conditioned Epistemic Pathfinding and Gap Completion
- [`PAPER_METACOGNITIVE_SELF_DIAGNOSIS_SECTION.md`](PAPER_METACOGNITIVE_SELF_DIAGNOSIS_SECTION.md) — Paper Insert — Metacognitive Self-Diagnosis and Method Completeness
- [`PAPER_METHOD_ASSIMILATION_SECTION.md`](PAPER_METHOD_ASSIMILATION_SECTION.md) — Paper module: From component comparison to governed method assimilation
- [`PAPER_METHOD_FRONTIER_SECTION.md`](PAPER_METHOD_FRONTIER_SECTION.md) — Paper Insert — Cumulative Validated Method Acquisition
- [`PAPER_REAL_CROSS_DOMAIN_RETRIEVAL_ADDENDUM.md`](PAPER_REAL_CROSS_DOMAIN_RETRIEVAL_ADDENDUM.md) — Paper Draft Addendum — Real Benchmark Semantics: Relevance Is Not Analogy
- [`PAPER_SELF_EVOLUTION_SECTION.md`](PAPER_SELF_EVOLUTION_SECTION.md) — Paper Insert — Governed Open-Ended Method Evolution
- [`PAPER_SIMILARITY_ANALOGY_SECTION.md`](PAPER_SIMILARITY_ANALOGY_SECTION.md) — Paper Draft Module — Similarity, Analogy, and Scientific Jumps
- [`PAPER_SIMILARITY_DISTINGUISHABILITY_ADDENDUM.md`](PAPER_SIMILARITY_DISTINGUISHABILITY_ADDENDUM.md) — Paper Draft Addendum — Similarity as Surviving Distinguishing Probes
- [`PAPER_STRATEGY.md`](PAPER_STRATEGY.md) — RAKL Paper Strategy
- [`PAPER_QUANT_FINANCE_APPLICATION.md`](PAPER_QUANT_FINANCE_APPLICATION.md) — RAKL Paper — Quant-Finance Application `[research-only]`

## Status artifacts (point-in-time, not framework)

- [`PAPER5_IMPLEMENTATION_STATUS.md`](PAPER5_IMPLEMENTATION_STATUS.md) — Paper 5 implementation status
- [`VTG_MATHEMATICAL_CLOSURE_AUDIT.md`](VTG_MATHEMATICAL_CLOSURE_AUDIT.md) — VTG Mathematical Closure Audit — 2026-08-13
- [`ORION_UNIFIED_FRAMEWORK_VERIFICATION_LEDGER.md`](ORION_UNIFIED_FRAMEWORK_VERIFICATION_LEDGER.md) — Orion Unified Problem-Solving Framework — Verification Ledger
- [`META_FIBER_HISTORY_COMPILATION.md`](META_FIBER_HISTORY_COMPILATION.md) — Historical meta-fiber ledger compilation
- [`META_FIBER_REGISTRY_RECONCILIATION.md`](META_FIBER_REGISTRY_RECONCILIATION.md) — Meta-Fiber Registry Reconciliation
- [`TERMINOLOGY_RENAME_INVENTORY_V1.md`](TERMINOLOGY_RENAME_INVENTORY_V1.md) — Terminology and rename dependency inventory (issue #137, v1)
