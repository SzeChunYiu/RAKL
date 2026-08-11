# RAKL Semantic Shortcut Router

## Status

This document specifies the proposal-only obstruction–transformation layer implemented in `src/rakl/semantic_shortcut.py`.

It changes **how candidate routes are selected**. It does not change theorem truth, novelty authority, independent-review credit, or method-promotion authority.

The governing question is:

> **Has this relational obstruction — and a transformation that breaks it — occurred anywhere in recorded knowledge?**

The search target is therefore not a sentence, topic label, theorem name, or embedding-nearest document. It is a reusable structural episode:

```text
obstruction O
  -- transformation T -->
changed state O'
```

## Why this layer exists

The existing RAKL mathematical workflow already freezes context, searches analogues, transfers methods, reviews success/failure experience, preserves residuals, and supports invention. The missing connective object was an auditable representation of the **obstruction itself**, the **transformation that previously changed an analogous obstruction**, and the evidence needed to decide whether that transformation may be reused, transported, composed, or must instead be invented.

This layer turns that connective object into a first-class pre-candidate artifact.

## Structural semantic coordinates

An `ObstructionFingerprint` records:

```text
roles
relations
constraints
failure mechanisms
invariants that must survive
desired transition
forbidden losses
```

Domain nouns are intentionally secondary. A newspaper story about packages circulating through depots and a proof problem about iterating a map over a finite set can be far apart lexically while sharing a finite-state-revisitation relation. RAKL should retrieve them because of the preserved relational skeleton, not because their words are close.

The reference ranker operates on already-normalized structural coordinates. It gives highest weight to shared failure morphology and the transformation's **recorded resulting relations**, then shared relations/constraints and preserved invariants, while penalizing target-forbidden losses. A similarity score is only a retrieval proposal. It is never a transport certificate.

## Content-bound obstruction–transformation memory

`ObstructionTransformationMemory` is a content-addressed snapshot containing a declared source universe and zero or more `ObstructionTransformationEpisode` records. The snapshot hash is recomputed from canonical episode content so a review cannot silently cite a different episode set under the same memory identity.

An episode includes:

```text
source obstruction fingerprint
transformation name and operation
source preconditions
recorded resulting relations
preserved invariants
constraints relaxed/broken
known breakpoints
source evidence and authority
lineage
```

Episodes may originate in mathematics, science, engineering, algorithms, organizations, ordinary situations, journalism, or other recorded knowledge. Their source authority is explicit:

```text
PROPOSAL_ONLY
SOURCE_EVENT_VERIFIED
VERIFIED_LOCAL
PROOF_BACKED
SUPERSEDED
```

Proposal-only and superseded episodes may inform exploration but cannot become strict viable SEARCH/JUMP routes. Source validity never implies target validity.

The episode memory is not a second truth-authority store. A successful target use may later be distilled into the existing `ResearchToolInventory` when that tool's normal scope, validation and promotion requirements pass. Failed target transports remain negative history in the failure lattice.

## Query semantics

`discover_shortcut_candidates(...)` derives a deterministic proposal set from one frozen memory snapshot.

The query does not simply ask whether source and target describe similar things. It asks whether a verified source episode shares the target's failure mechanism and whether the source transformation actually produced relations relevant to the target's desired transition without sacrificing a forbidden target property.

The reference implementation returns:

```text
direct_matches     -> same-domain structural candidates
jump_matches       -> cross-domain structural candidates
glue_episode_sets  -> partial pairs whose combined recorded effects cover the target transition
```

A returned candidate still requires explicit target applicability evidence.

## Invention-last route order

For each active obstruction, the router freezes one of five states.

### 1. SEARCH

Ask whether an existing same-domain transformation is reusable in the target scope.

A SEARCH route requires:

```text
candidate episode present in the bound memory
verified source episode authority
source -> target role mapping
shared relations and constraints
complete accounting of every source precondition
no unrepaired source precondition
explicit disanalogies
target validation obligations
```

If a viable direct transformation exists, choosing LIFT merely because invention is more novel is invalid.

### 2. JUMP

If direct reuse fails, search structurally distant knowledge for the same relational obstruction.

A JUMP uses the same applicability discipline as SEARCH but the source comes from another domain. A `StructuralMappingWitness` records:

```text
source -> target role mapping
shared relations
shared constraints
source-precondition -> target-condition mapping
unmatched source preconditions
material disanalogies
target-domain validation obligations
evidence pointers
```

Every enabling source precondition must be mapped or explicitly remain unmatched. An unmatched precondition blocks strict transport. Surface analogy, embedding proximity, or a shared topic label is insufficient.

### 3. GLUE

If no single episode supplies the needed transformation, compose compatible partial transformations.

The memory query first checks whether component transformations have recorded effects that jointly cover the desired target transition. That is only a proposal. Strict GLUE additionally requires each component to have a target mapping witness and a `TransformationCompositionWitness` with:

```text
selected episode ids
exact operation order
interface obligations
incompatibilities checked
target validation obligations
```

Narrative compatibility is not compositional validity.

### 4. LIFT

LIFT is entered only after SEARCH, JUMP, and GLUE are each explicitly `NO_VIABLE_MATCH` inside a recorded boundary.

LIFT additionally requires:

```text
at least two distinct failed attempts
repeated residual structure across those failures
multiple searched domains
multiple searched method families
a cross-problem coverage receipt hash
explicit accounting for every direct/JUMP/GLUE candidate returned by the bound memory query
rejection reasons and evidence
```

The coverage requirement is critical. A local empty search is not evidence that recorded knowledge has no relevant transformation.

The output is a `MissingTransformationSpecification`, not a new theorem or magically valid tool:

```text
must preserve
must break
must expose
must reduce
allowed representation changes
forbidden shortcuts
validation obligations
falsifiers
```

This is **inverse invention**: instead of randomly asking what tool to invent, RAKL asks what properties a transformation would need in order to cross the identified epistemic cut.

The downstream mechanism/formalism-invention workflow can then synthesize candidate representations/operators constrained by that specification.

### 5. CANNOT_CHECK

When memory identity, search coverage, applicability witnesses, repeated residuals, composition interfaces or validation obligations are insufficient, the correct route is `CANNOT_CHECK`/blocked rather than invented certainty.

## Failure as invention evidence

The LIFT mechanism treats failures as structured observations.

Given failed attempts with residual signatures

```text
F1 -> {a, b, c}
F2 -> {a, d}
F3 -> {a, b, e}
```

the repeated coordinates `{a, b}` become candidates for what a missing transformation must specifically break, expose, or re-represent.

This does **not** prove that a genuinely new mathematical object is necessary. It produces a constrained invention target. RAKL still distinguishes retrieval failure, representation failure, implementation defects, missing evidence, routing failure, and a true method-basis gap through its existing failure and metacognitive machinery.

## Strict mathematical chronology

For strict mathematical discovery the new order is:

```text
ATOMIZED
CONTEXT_FROZEN
ANALOGY_SCAN
METHOD_TRANSFER_REVIEW
EXPERT_CONTEXT_REVIEW
EXPERIENCE_MEMORY_REVIEW
OBSTRUCTION_TRANSFORMATION_REVIEW
NEXT_STEP_PROPOSED
CANDIDATE_PROPOSED
```

The strict math planner now receives both the `ObstructionTransformationMemory` and the `ObstructionTransformationReview`. The review is bound to:

- the target atom;
- the frozen context hash;
- the prior `ResearchMemoryReview` artifact hash;
- the exact content-bound transformation-memory snapshot hash; and
- its own artifact hash.

The trace binds that review hash before candidate generation. Backfilling the memory/review after a candidate exists does not satisfy strict discovery chronology.

## Cumulative learning loop

A validated target result may produce two different reusable descendants, each with separate authority semantics:

```text
successful scoped operation
    +--> ResearchTool candidate
         (preconditions, guarantees, non-guarantees, applicability witness)
    +--> ObstructionTransformationEpisode candidate
         (O -> T -> O' structural retrieval record)
```

The tool answers "what operation may I reuse under these conditions?" The episode answers "where has an obstruction of this morphology changed, and what changed it?" Neither grants theorem truth merely by being stored.

A failed transported episode also enriches future search because its failure becomes a `FailureExperience` and can later appear in a LIFT residual cluster.

This yields the cumulative loop:

```text
SEARCH / JUMP / GLUE
        |
        v
candidate + target validation
   |                 |
 failure           success
   |                 |
 failure lattice    scoped tool + episode candidate
   |                 |
   +-------> future obstruction search <------+
                     |
               persistent residuals
                     |
                    LIFT
                     |
            new typed candidate
```

## Authority boundary

A valid shortcut review can grant only:

```text
candidate_route_ready = true
```

It cannot grant:

```text
proof
novelty
scientific truth
mechanism truth
independent review
method promotion
framework improvement
```

Every transported or invented candidate remains subject to target-domain falsification, formalization, proof checking, novelty search, and the ordinary RAKL assurance/promotion contracts.

## Canonical method ownership

The extension does not create a new canonical method surface.

```text
memory                     -> content-bound episode snapshots
routing                    -> SEARCH/JUMP/GLUE/LIFT selection
gap_discovery              -> repeated-residual cut and missing-transform spec
equivalence_similarity     -> structural matching semantics
generator_transport        -> source-to-target transport validity
contextual_theory_gluing   -> transformation composition compatibility
mechanism invention        -> typed candidates synthesized from LIFT specs
review/assurance           -> target validation and authority
```

This preserves the RAKL v3 rule that implementation overlays do not silently create ungoverned method authority.

## Research hypothesis, not established improvement

The intended benefit is a shorter proof-discovery search path when useful reasoning morphology exists far from the target domain, and a more constrained invention process when it does not. That benefit must be established separately under the governed Class-B protocol with matched parent/challenger development evaluation and fresh assurance. The existence or merge of this implementation is not such evidence.
