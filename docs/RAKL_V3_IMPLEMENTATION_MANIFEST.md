# RAKL v3 Implementation Manifest

**Branch:** `rakl-v3-experience-substrate`  
**Purpose:** exact implementation inventory for the recursive experience-substrate refactor.

This manifest distinguishes what is implemented from what still requires empirical evidence.

## Implemented architecture

### Persistent experience substrate

- `src/rakl/experience_substrate.py`
  - immutable `TaskEpisode` evidence roots;
  - versioned `Lesson` abstractions;
  - typed substrate nodes/relations;
  - explicit candidate/local/reusable/proof-backed lesson authority.

- `src/rakl/experience_memory.py`
  - TaskEpisodes map to existing canonical `MemoryView` roots;
  - Lessons map to explicitly lossy derived views pinned to exact episode hashes;
  - derived memory cannot replace raw experience.

### Failure learning

- `src/rakl/failure_learning.py`
  - immutable diagnosis revisions;
  - `OBSERVED_ONLY` records remain preserved;
  - supported/verified diagnoses may seed candidate boundary lessons;
  - boundary lessons still require ordinary lesson verification/transfer promotion.

- Existing `src/rakl/failure_lattice.py` remains the specialized failure/obstruction view.

### Problem fibres and local-to-global solving

- `src/rakl/problem_fibre.py`
  - explicit problem atoms/dependencies/interfaces;
  - target-conditioned fibres combining knowledge, tools, episodes, failures, motifs, and expertise;
  - direct read-only adaptation of existing `core.KnowledgeFiber` projections;
  - namespaced legacy projection identities;
  - interface-aware local-section gluing;
  - global authority requires compatibility + verification + complete atom coverage.

- `src/rakl/gluing_learning.py`
  - failed/incomplete gluing becomes typed experience residuals.

### Continual learning driver

- `src/rakl/driver_learning.py`
  - compiles a fibre before each replaceable LLM/agent turn;
  - freezes the observed result as TaskEpisode before interpretation;
  - projects non-success into failure memory only after the result exists.

- `src/rakl/v3_runtime.py`
  - persistent `RAKLV3State`;
  - fast task-episode recording;
  - slow evidence-gated lesson consolidation;
  - state-conditioned fibre compilation;
  - unified substrate materialization;
  - deterministic state fingerprints;
  - vector-saturation updates.

### Experience-conditioned problem solving

- `src/rakl/experience_policy.py`
  - scoped operator success/failure statistics;
  - experience-conditioned operator/path ranking;
  - exploration term to avoid early permanent blacklisting;
  - candidate strategy-motif induction from repeated successful trajectories;
  - contradiction/failure history retained;
  - invention readiness gate.

- Existing `problem_solving_algebra.py`, `strategy_motifs.py`, `research_tool_inventory.py`, and `breakthrough_learning.py` remain the specialized symbolic/operator/expertise mechanisms.

### Saturation and invention

- `src/rakl/saturation_vector.py`
  - independent axes: KNOWLEDGE, OPERATOR, EXPERIENCE_PATTERN, OBSTRUCTION, RELATION, PATH, META_METHOD;
  - recent retained novelty prevents flatness;
  - multiple independent flat routes required;
  - native residuals reopen only implicated axes;
  - no absolute completeness claim.

- Invention readiness requires bounded flatness plus stable residuals, ordinary-cause exclusion, cross-domain search exhaustion, and explicit method/representation gap evidence before routing to existing invention machinery.

### Problem novelty / RAKL-triviality metrology

- `src/rakl/problem_novelty.py`
  - STORED;
  - RAKL_TRIVIAL;
  - TRANSFER_NOVEL;
  - REPRESENTATION_NOVEL;
  - OPERATOR_NOVEL;
  - ONTOLOGY_NOVEL;
  - UNRESOLVED;
  - zero-invention and strict RAKL-trivial rates.

This makes the hypothesis "many apparently novel problems need no new problem-solving primitive once the atlas is rich enough" empirically measurable rather than assumed.

### Unified cross-view substrate

- `src/rakl/unified_substrate.py`
  - read-only overlay across specialized stores;
  - epistemic nodes from legacy knowledge fibres;
  - operator nodes from ResearchTool inventory;
  - episode/lesson nodes from ExperienceLedger;
  - obstruction nodes from failure lattice;
  - Self-RAKL architecture variants as META_METHOD nodes;
  - explicit episode->failure, lesson->tool, failure->tool-boundary, successful-reuse->tool, and variant-ancestry relations;
  - specialized stores remain semantic/authority owners.

### Branching Self-RAKL

- `src/rakl/evolution_archive.py`
  - incumbent/challenger/assured/rejected/retired variants;
  - reuses protected `SelfEvolutionAssessor`;
  - successful assurance never auto-promotes;
  - explicit governance required for incumbent replacement;
  - previous incumbent retained as rollback/alternative branch;
  - variants are represented in the unified substrate.

### Empirical learning evaluation

- `src/rakl/experience_benchmark.py`
  - reuses existing matched model/resource accounting;
  - RESET_BASELINE vs LEARNING_ENABLED arms;
  - sequential development-state chronology;
  - every fresh-transfer task starts from the same frozen learned state;
  - transfer cannot learn from earlier transfer cases;
  - success/score/repeated-failure/resource deltas;
  - descriptive evidence only; no automatic global capability claim.

### Stable API

- `src/rakl/v3.py`
  - stable `rakl.v3` facade;
  - legacy top-level imports remain untouched.

## Machine-readable schemas

- `schemas/task-episode.schema.json`
- `schemas/lesson.schema.json`

## Documentation

- `ARCHITECTURE.md` — canonical architecture extended with v3 recursive experience substrate.
- `docs/RAKL_V3_EXPERIENCE_SUBSTRATE.md` — full conceptual/software contract.
- `docs/RAKL_V3_API.md` — public API and learning-turn lifecycle.
- `docs/RAKL_V3_EVALUATION.md` — novelty/triviality and matched continual-learning evaluation.
- `docs/RAKL_V3_IMPLEMENTATION_MANIFEST.md` — this exact inventory.

## Regression suites added

- `tests/test_rakl_v3_experience_substrate.py`
- `tests/test_rakl_v3_driver_learning.py`
- `tests/test_rakl_v3_public_api.py`
- `tests/test_rakl_v3_hardening.py`
- `tests/test_rakl_v3_legacy_memory_novelty.py`
- `tests/test_rakl_v3_experience_benchmark.py`
- `tests/test_rakl_v3_public_integration_api.py`
- `tests/test_rakl_v3_unified_substrate.py`
- `tests/test_rakl_v3_failure_learning.py`
- `tests/test_rakl_v3_gluing_learning.py`
- `tests/test_rakl_v3_self_representation.py`
- `tests/test_rakl_v3_interface_guards.py`

The tests cover evidence immutability, causal non-self-certification, lesson identity/versioning, transfer promotion, failure revision, legacy knowledge integration, memory lineage, problem fibres, explicit interfaces, gluing, experience routing, motif induction, saturation, invention readiness, novelty/triviality metrology, matched learning evaluation, unified substrate, Self-RAKL self-representation, state fingerprints, and public API imports.

## Preserved authority boundary

The implementation deliberately does **not** weaken the existing RAKL authority architecture:

```text
ACCESS != COHERENCE != AUTHORITY
Episode != diagnosis != obstruction
Reflection != verification
Co-retrieval != compatibility
Local success != global solution
Experience-conditioned routing != epistemic authority
Derived memory != replacement for raw evidence
Bounded saturation != absolute completeness
Being stuck != missing operator
Self-evolution evidence != self-promotion
```

## Not established by this implementation

The branch does not by itself establish:

- empirical superiority of RAKL v3;
- universal continual-learning gains;
- the truth of the high RAKL-triviality hypothesis;
- automatic invention of genuinely new mathematics/science;
- safe autonomous promotion of architecture variants;
- absolute open-world or knowledge completeness.

Those remain empirical/evidence questions. The matched experience benchmark and existing protected Self-RAKL evolution machinery are the intended gates for those claims.
