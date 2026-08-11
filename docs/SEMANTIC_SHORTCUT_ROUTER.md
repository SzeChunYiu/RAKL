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
more tractable state O'
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

The reference ranker therefore operates on already-normalized structural coordinates. A similarity score is only a retrieval proposal. It is never a transport certificate.

## Obstruction–transformation episodes

An `ObstructionTransformationEpisode` records a source situation in which a transformation changed a scoped obstruction. It includes:

```text
source obstruction fingerprint
transformation name and operation
preconditions
resulting relations
preserved invariants
constraints relaxed/broken
known breakpoints
source evidence and authority
lineage
```

Episodes may originate in mathematics, science, engineering, algorithms, organizations, ordinary situations, or other recorded knowledge. Source validity does not imply target validity.

A successful target use can later be distilled into the existing success-derived research-tool inventory when its normal scope/authority requirements are met. A failed transport is preserved in the failure lattice. The episode memory is therefore a structural retrieval projection over accumulated experience, not a replacement for RAKL's existing truth/evidence planes.

## Invention-last route order

For each active obstruction, the router freezes one of five states:

### 1. SEARCH

Ask whether an existing transformation is directly reusable in the target scope.

```text
same/compatible context
+ applicable transformation
-> SEARCH
```

If a viable direct transformation exists, choosing LIFT merely because invention is more novel is invalid.

### 2. JUMP

If direct reuse fails, search structurally distant knowledge for the same relational obstruction.

A JUMP requires a `StructuralMappingWitness` containing:

```text
source -> target role mapping
shared relations
shared constraints
material disanalogies
target-domain validation obligations
evidence pointers
```

Surface analogy without these fields fails closed.

### 3. GLUE

If no single episode supplies the needed transformation, compose compatible partial transformations.

A GLUE requires a `TransformationCompositionWitness` with:

```text
selected episode ids
exact operation order
interface obligations
incompatibilities checked
target validation obligations
```

Composition is not licensed by narrative compatibility.

### 4. LIFT

LIFT is entered only after SEARCH, JUMP, and GLUE are each explicitly `NO_VIABLE_MATCH` inside a recorded boundary.

LIFT also requires **multiple distinct failed attempts sharing residual structure**. One failure is not evidence of a missing transformation.

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

This is inverse invention: instead of randomly asking what tool to invent, RAKL asks what properties a transformation would need in order to cross the identified epistemic cut.

The downstream mechanism/formalism-invention workflow can then synthesize candidate representations/operators constrained by that specification.

### 5. CANNOT_CHECK

When the search boundary, witnesses, repeated residuals, or validation obligations are insufficient, the correct route is `CANNOT_CHECK`.

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

The obstruction–transformation review is bound to:

- the target atom;
- the frozen context hash;
- the prior `ResearchMemoryReview` artifact hash;
- the obstruction–transformation episode-memory snapshot hash; and
- its own artifact hash.

The trace must bind that review hash before candidate generation. Backfilling the review after a candidate exists does not satisfy strict discovery chronology.

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
routing                    -> SEARCH/JUMP/GLUE/LIFT selection
gap_discovery              -> repeated-residual cut and missing-transform spec
equivalence_similarity     -> structural matching semantics
generator_transport        -> source-to-target transport validity
contextual_theory_gluing   -> transformation composition compatibility
memory                     -> persistent episode representation/retrieval
review/assurance           -> target validation and authority
```

This preserves the RAKL v3 rule that implementation overlays do not silently create ungoverned method authority.

## Research hypothesis, not established improvement

The intended benefit is a shorter proof-discovery search path when useful reasoning morphology exists far from the target domain, and a more constrained invention process when it does not. That benefit must be established separately under the governed Class-B protocol with matched parent/challenger development evaluation and fresh assurance. The existence or merge of this implementation is not such evidence.
