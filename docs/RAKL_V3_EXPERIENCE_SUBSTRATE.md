# RAKL v3 — Recursive Experience Substrate

**Status:** implementation contract on branch `rakl-v3-experience-substrate`  
**Scope:** unifies persistent knowledge, problem solving, experience learning, saturation, invention readiness, and Self-RAKL evolution without granting the LLM authority to self-certify claims or methods.

## 1. Central change

RAKL is no longer modeled primarily as a knowledge lattice plus adjacent memory modules.

RAKL is a **persistent, typed, recursively evolving external cognitive substrate**.  Knowledge, tools, trajectories, failures, obstructions, strategies, and meta-methods are overlapping views over that substrate.

For task `P_t`, a replaceable LLM driver with parameters `theta` operates against persistent RAKL state `R_t`:

```text
(S_t, tau_t) = Driver_theta(P_t, R_t)
R_{t+1}      = Learn(R_t, tau_t)
```

The LLM weights may remain unchanged:

```text
theta_{t+1} = theta_t
```

while future behavior changes because the external structured state changed:

```text
Driver_theta(P, R_{t+1}) != Driver_theta(P, R_t)
```

This is the primary mechanism by which the LLM driving RAKL learns from repeated task experience without requiring online weight updates.

## 2. Four coupled loops

RAKL v3 is organized around four recursive loops.

### 2.1 Information -> knowledge

Existing claim extraction, context projection, identity resolution, provenance binding, compatibility analysis, and promotion remain authoritative for epistemic state.

```text
source/evidence
-> atomic projection
-> context
-> identity/representation normalization
-> provenance
-> relation/compatibility analysis
-> verification
-> canonical epistemic update
```

The new experience layer does not bypass this path.

### 2.2 Problem -> solution

```text
problem
-> adaptive atom/dependency graph
-> problem-conditioned fibres
-> local candidate sections
-> compatibility/gluing
-> verification
-> global solution candidate
```

A local success does not imply global success.  A complete solution requires compatible local sections, complete atom coverage, and verification.

### 2.3 Experience -> method

```text
TaskEpisode
-> outcome/residual detection
-> competing diagnoses
-> discriminating replay/challenge
-> candidate lesson
-> scoped verification
-> fresh transfer/proof
-> promoted lesson/tool/strategy/boundary
```

A failure is an observation before it is a diagnosis.  A diagnosis is not yet a reusable obstruction.  Reflection may propose a cause but cannot promote it.

### 2.4 RAKL -> better RAKL

```text
meta-residual
-> meta-problem fibre
-> challenger method/architecture
-> frozen development comparison
-> fresh protected assurance
-> branch marked ASSURED or rejected
-> explicit governance promotion
```

Self-evolution is branching rather than destructive.  Alternative RAKL variants remain in an archive so specialized variants and rollback targets can coexist.

## 3. Common substrate

`src/rakl/experience_substrate.py` introduces generic typed substrate objects and relations.

### Object kinds

```text
EVIDENCE
EPISTEMIC
OPERATOR
EPISODE
OBSTRUCTION
STRATEGY
META_METHOD
```

### Example cross-view relations

```text
DERIVED_FROM
SUPPORTS
CONTRADICTS
RESOLVED_BY
APPLIES_TO
INSTANCE_OF
USES
PRODUCED
FAILED_WITH
SUCCEEDED_WITH
SUPERSEDES
TRANSFERRED_TO
```

The purpose is not to replace specialized stores immediately.  The substrate is the unifying identity/lineage layer through which specialized views can overlap without duplicating the underlying experience.

## 4. TaskEpisode is the immutable learning root

`TaskEpisode` records what actually happened:

```text
episode_id
task_id
atom_id
context_hash
problem_signature
fibre_snapshot_hash
operator_ids
action_trace
observation_ids
verification_ids
outcome
residual_signature
evidence_pointers
artifact_hash
timestamp
cost
```

The canonical invariant is:

> **Never replace evidence with abstraction.**

`artifact_hash` is the raw lowercase 64-hex SHA-256 digest of
`episode_content_bytes(episode)`. Prefixed, truncated, non-hex, or stale
digests fail closed; the JSON schema and runtime enforce the same contract.

Summaries, lessons, expertise chunks, operator statistics, motifs, and routing priors are derived views.  They never delete or rewrite the source episodes from which they were produced.

Machine-readable contract: `schemas/task-episode.schema.json`.

## 5. Lessons are versioned, scoped abstractions

A `Lesson` contains:

```text
trigger signature
context scope
action
expected effects
boundaries
supporting episodes
contradicting episodes
falsifier
authority
validation obligations
evidence pointers
parent lesson version
```

Authority levels are:

```text
CANDIDATE
VERIFIED_LOCAL
CONDITIONALLY_REUSABLE
PROOF_BACKED
SUPERSEDED
```

A candidate can be produced by same-context reflection or pattern extraction.  Reusable status requires outcome-linked verification and fresh transfer or proof.

Promotion creates a **new lesson version** with a `SUPERSEDES` lineage edge.  It does not mutate the old lesson or source episodes.

Machine-readable contract: `schemas/lesson.schema.json`.

## 6. Fast and slow learning timescales

RAKL v3 deliberately separates two learning loops.

### Fast loop

Immediately after a consequential task attempt:

1. freeze the `TaskEpisode`;
2. if non-success, project an `OBSERVED_ONLY` failure record unless stronger diagnosis evidence already exists;
3. update retrieval/routing statistics as derived working views;
4. preserve all raw evidence.

Implemented by `record_task_episode()` in `src/rakl/v3_runtime.py`.

### Slow loop

Periodically or after sufficient discriminating evidence:

1. collect supporting and contradicting episodes;
2. run replay/diagnostic challenges;
3. require registered verification;
4. test fresh transfer;
5. create a promoted lesson version;
6. optionally project a validated operational lesson into `ResearchToolInventory`.

Implemented by `src/rakl/experience_learning.py` and `consolidate_lesson()`.

## 7. Failure episode != diagnosis != obstruction

The existing `FailureExperienceLattice` is retained, but it is now interpreted as a specialized view of episode-derived failure evidence.

```text
TaskEpisode(non-success)
-> FailureExperience(OBSERVED_ONLY)
-> competing causal diagnoses
-> discriminating evidence
-> SUPPORTED diagnosis
-> generalized boundary/obstruction lesson
-> cross-context validation
```

Ordinary failures remain warning priors rather than global blacklists.  Existing `DifferenceWitness` behavior is preserved.

The new runtime defaults new failure projections to `OBSERVED_ONLY` so the LLM cannot turn one failed attempt into a causal law.

## 8. Problem atoms and fibres

`src/rakl/problem_fibre.py` defines a problem atom as a locally manipulable unit whose interfaces and dependencies remain explicit.

An atom contains:

```text
atom_id
goal
context_hash
structural_coordinates
desired_effects
dependencies
interface_keys
```

For atom `a` under task/context `(P,c)`, the fibre is a derived query:

```text
F(a | P,c) = Pi_{a,P,c}(R)
```

and may contain:

```text
relevant epistemic items
success-derived tools
analogous TaskEpisodes
failure history
strategy motif instantiations
expertise chunks
unresolved warnings
```

A fibre is a working view.  Co-retrieval does not imply compatibility or authority.

## 9. Local-to-global gluing

A local solution is represented by `LocalSection`.

A global solution candidate requires:

```text
compatible interface assignments
+ dependency coverage
+ complete atom coverage
+ verified local sections
```

`glue_local_sections()` returns explicit `GluingObstruction` records when local sections disagree.

A `GluingReport` grants solution authority only when:

```text
compatible
AND all_sections_verified
AND complete_coverage
```

This prevents successful isolated atoms from being mistaken for a solved global problem.

## 10. Experience-conditioned operator policy

The existing symbolic operator algebra remains the planner basis.  RAKL v3 adds an experience-conditioned routing prior in `src/rakl/experience_policy.py`.

For each operator, RAKL derives scoped outcome statistics from structurally relevant episodes.  A smoothed policy score combines:

```text
operator cost
verification debt
boundary risk
empirical success rate
empirical failure rate
small exploration bonus for under-sampled operators
```

Experience can change **which operator/path is tried first**.

It cannot change what counts as proof, verification, authority, or promotion.

## 11. Learned strategy motifs

The original `StrategyMotif` mechanism remains valid, but motifs no longer need to be exclusively hand-written.

`induce_strategy_motifs()` mines repeated contiguous operator sequences from successful TaskEpisodes and retains failure episodes containing the same sequence as contradiction/boundary evidence.

The output is a **candidate learned motif** containing:

```text
operator sequence
supporting episode ids
contradicting episode ids
observed contexts
support count
contradiction count
failure modes
```

Induction does not promote the motif.  It must pass the same scoped lesson/tool validation path before authoritative reuse.

## 12. Expertise chunks

Existing `ExpertiseChunk` objects become high-speed retrieval aids inside problem fibres.

They link:

```text
cue signature
deep structure
tool ids
failure warnings
applicability conditions
non-applicability conditions
contrastive near misses
retrieval probes
```

This is the compact expert-memory layer; immutable episodes remain the evidential layer beneath it.

## 13. Saturation is a vector

`src/rakl/saturation_vector.py` introduces independent saturation axes:

```text
KNOWLEDGE
OPERATOR
EXPERIENCE_PATTERN
OBSTRUCTION
RELATION
PATH
META_METHOD
```

An axis is bounded-flat only when multiple independent route families add zero retained novelty and no recent native residual reopens that axis.

Consequences:

```text
knowledge saturation != operator saturation
operator saturation  != obstruction saturation
all local saturation  != absolute completeness
```

A native residual may reopen only the implicated axis rather than resetting all research.

## 14. Invention is a gated escalation

`assess_invention_readiness()` requires all of the following before recommending missing-operator or missing-representation search:

```text
relevant KNOWLEDGE axis flat
relevant OPERATOR axis flat
relevant PATH axis flat
residual stable across repeated attempts
ordinary failure causes excluded
cross-domain transfer routes bounded-flat
explicit representation-gap or method-basis evidence
```

Being stuck is insufficient.

The readiness report never grants invention authority; it only permits escalation to the existing invention machinery.

## 15. Branching Self-RAKL evolution

`src/rakl/evolution_archive.py` wraps the existing protected `EvolutionTrial` / `SelfEvolutionAssessor` logic in a persistent branch archive.

Variant states are:

```text
INCUMBENT
CHALLENGER
ASSURED
REJECTED
RETIRED
```

A successful assurance trial changes a challenger to `ASSURED` but **does not automatically replace the incumbent**.

Promotion requires an explicit `governance_approved=True` operation.

When a new incumbent is promoted, the previous incumbent remains `ASSURED` as a rollback/alternative branch.

This supports eventual task-conditioned variant selection without destructive linear self-modification.

## 16. Integrated v3 runtime

`src/rakl/v3_runtime.py` binds the specialized views into one persistent state:

```text
RAKLV3State
├── ExperienceLedger
├── ResearchToolInventory
├── FailureExperienceLattice
├── SaturationVectorState
└── EvolutionArchive (optional)
```

Primary operations:

```text
record_task_episode()
consolidate_lesson()
compile_state_fibre()
record_saturation_round()
```

The runtime is intentionally functional/immutable: each operation returns a new state value.

## 17. Driver lifecycle

The recommended v3 driver lifecycle is:

```text
REGISTER PROBLEM
-> adaptive atomization
-> for active atom:
     compile problem fibre
     review success + failure + expertise memory
     rank operator paths using structural + experiential priors
     execute candidate action
     verify outcome
     freeze TaskEpisode
     diagnose residual if any
     reopen implicated fibre/axis
-> glue verified local sections
-> verify global candidate
-> consolidate validated lessons
-> update saturation vector
-> if bounded-flat + stable missing-basis residual:
     activate representation/operator invention
-> if repeated meta-residual:
     open Self-RAKL challenger branch
```

## 18. Mapping to existing modules

The v3 refactor preserves and reinterprets existing mechanisms rather than replacing them wholesale.

| Existing component | v3 role |
|---|---|
| `core.py`, claim/evidence stack | epistemic/information loop |
| `TypedCompatibilityComplex` / atlas gluing | compatibility substrate and scientific local-to-global logic |
| `research_tool_inventory.py` | promoted operational lesson view |
| `failure_lattice.py` | failure/obstruction view over episode evidence |
| `research_memory.py` | precursor to problem fibre memory audit |
| `problem_solving_algebra.py` | symbolic operator basis |
| `strategy_motifs.py` | reusable multi-operator chunks, now also learnable |
| `breakthrough_learning.py` | expertise chunks and reflective strategy modes |
| `challenge_learning.py` | root-cause-sensitive learning-control policy |
| `multires_memory.py` | canonical-vs-derived memory lineage substrate |
| `saturation.py` / `epistemic_saturation.py` | existing local saturation mechanisms; v3 adds cross-view vector |
| `invention.py` / `missing_operator.py` | escalation target after invention readiness gate |
| `evolution.py` / `self_bootstrap.py` | protected self-improvement evidence; v3 adds branch archive |

## 19. Non-negotiable invariants

RAKL v3 preserves these constraints:

1. **ACCESS != COHERENCE != AUTHORITY.**
2. **Episode != diagnosis != obstruction.**
3. **Reflection != verification.**
4. **Co-retrieval != compatibility.**
5. **Local success != global solution.**
6. **Experience-conditioned routing != epistemic authority.**
7. **Derived memory never replaces immutable evidence roots.**
8. **Saturation is scoped and vector-valued; it never proves absolute completeness.**
9. **Being stuck does not prove a missing operator.**
10. **Self-evolution evidence does not self-promote the framework.**

## 20. Executable contracts

The branch adds:

```text
src/rakl/experience_substrate.py
src/rakl/experience_learning.py
src/rakl/problem_fibre.py
src/rakl/experience_policy.py
src/rakl/saturation_vector.py
src/rakl/evolution_archive.py
src/rakl/v3_runtime.py
schemas/task-episode.schema.json
schemas/lesson.schema.json
tests/test_rakl_v3_experience_substrate.py
```

The new tests cover raw episode preservation, failure observation semantics, lesson transfer gates, fibre integration, gluing coverage/compatibility, experiential operator ranking, learned motifs, vector saturation, invention readiness, and branching self-evolution.

## 21. Remaining empirical question

This implementation establishes software/formal contracts.  It does **not** by itself establish that the new architecture improves real task performance.

The next empirical gate is a matched repeated-task study comparing the same underlying LLM under:

```text
A: current RAKL memory/control
B: v3 episode + consolidation + fibre + experience-policy control
```

with frozen task families, fresh transfer tasks, equal model/tool/resource budgets, and metrics including:

```text
success rate
repeat-failure rate
sample efficiency
operator reuse quality
false lesson rate
transfer gain
regression rate
evidence-groundedness
cost
```

Only that experiment can support an empirical capability-improvement claim.
