# Contextual Atlas Gluing and Global Coherence

Status: research/support method layer  
Date: 2026-08-09

## 1. Purpose

The Apple/Knowledge-Atlas principle is local-to-global reconstruction. Different papers provide contextual charts of an underlying object. RAKL should combine them only when the relevant overlap structure is compatible and when a global object is actually justified.

The central safety rule is:

> **Pairwise agreement is local evidence. It is not, by itself, global scientific authority.**

A scientific atlas is therefore treated as presheaf-like by default, not silently assumed to satisfy a sheaf/local-to-global theorem.

## 2. Local chart

For declared atlas object `O`, question/QoI `q` and abstraction level `L`, a chart is represented as

\[
C_i=(U_i,\phi_i,\mathcal C_i,A_i,\Gamma_i,E_i),
\]

where `U_i` is the local facet, `phi_i` the representation, `C_i` the observational/context coordinates, `A_i` assumptions, `Gamma_i` validity regime and `E_i` evidence/provenance.

A source remains a local chart even if it is internally complete. Global scope must be earned.

## 3. Overlap transition witness

For overlapping charts `i,j`, RAKL records a transition witness

\[
T_{ij}:\phi_i(U_i\cap U_j)\to\phi_j(U_i\cap U_j)
\]

with explicit:

```text
mapping pairs
PRESERVED coordinates
NOT_PRESERVED coordinates
certified relation layers
context alignment
assumption compatibility
regime overlap
transition-map check
evidence/provenance
freeze chronology
```

The transition is certified only at declared layers such as semantic, mathematical, observational, QoI or mechanistic. Agreement at one layer cannot silently authorize another.

## 4. Local compatibility versus global coherence

RAKL distinguishes four questions that must not be collapsed:

1. **Overlap compatibility:** do the local charts agree on each declared overlap at the requested relation layer?
2. **Path/cycle coherence:** do alternative chains of transition maps give compatible transport when the cover has cycles?
3. **Global existence:** is there any global object/formalism whose restrictions recover all accepted local charts?
4. **Global uniqueness/identifiability:** is that global object unique for the declared QoI and evidence scope?

This yields the authority ladder:

```text
local overlaps pass
    -> PAIRWISE_COMPATIBLE_GLOBAL_UNPROVEN

global candidate exists, uniqueness unchecked
    -> GLOBAL_EXISTS_UNIQUENESS_UNPROVEN

multiple global candidates survive
    -> IDENTIFIED_SET_ONLY

unique coherent global candidate
    -> GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY
```

Even the final state is proposal-only until ordinary evidence promotion.

## 5. Cover topology and local-to-global certificates

A sheaf theorem can make local checks sufficient, but only after the relevant chart family and restriction structure have been shown to satisfy the required sheaf/local-to-global property.

RAKL therefore does **not** reason:

```text
scientific charts look sheaf-like
+ pairwise overlaps agree
=> unique global scientific theory
```

Instead it requires one of:

```text
A. a registered theorem/formal certificate establishing the applicable local-to-global property;
B. an explicit global-existence/uniqueness check for the frozen chart packet;
C. otherwise retain the atlas as GLOBAL_UNPROVEN.
```

Database local/global consistency results reinforce this restriction: the implication from local consistency to global consistency depends on the schema/cover and algebraic setting, so pairwise consistency is not a universal rule.

## 6. Cycle/path obstruction

When charts form multiple transport paths, RAKL asks whether composition is path independent in the declared scope.

For a loop

\[
C_A\xrightarrow{T_{AB}}C_B\xrightarrow{T_{BC}}C_C\xrightarrow{T_{CA}}C_A,
\]

a mismatch after composition is stored as

```text
CYCLE_OR_PATH_INCONSISTENCY
```

rather than averaged away. This is analogous to holonomy/path-dependence diagnostics in recent sheaf/gauge formulations of local semantic charts, but RAKL keeps the obstruction typed rather than reducing it to one universal scalar.

## 7. Obstruction ledger

Current obstruction classes include:

```text
CHART_SCOPE_MISMATCH
CONTEXT_MISMATCH
ASSUMPTION_CONFLICT
REGIME_DISJOINT
RELATION_LAYER_NOT_CERTIFIED
TRANSITION_MAP_FAILURE
MAPPING_WITNESS_CONTRADICTION
CYCLE_OR_PATH_INCONSISTENCY
GLOBAL_EXISTENCE_FAILURE
```

An obstruction is immutable negative history. It opens the specific child fiber capable of explaining it; it is not erased because a later chart or synthesis is attractive.

## 8. Selective rather than universal consensus

Different overlaps may need agreement on only a small shared interface. Recent cellular-sheaf coordination systems make this explicit by specifying which components neighboring local views must agree on.

RAKL adopts the same methodological lesson without importing their task-specific optimization machinery:

> **Global coherence requires agreement on the coordinates that define the registered overlap, not forced equality of every local coordinate.**

Thus a valid mechanistic glue may preserve a causal generator while recording substrate, notation or observation coordinates as `NOT_PRESERVED`.

## 9. Relation to GLUE, LIFT, JUMP, PROJECT

Contextual gluing is the conservative local-to-global operation inside the four-operator cycle:

```text
local target charts
   -> GLUE if coherent
   -> unresolved obstruction/residual
   -> LIFT to candidate parent/generator
   -> JUMP to sibling/distant charts
   -> GLUE at the lifted level when justified
   -> PROJECT only witnessed generator structure back
   -> target test
```

A JUMP can therefore supply a missing chart, but it cannot repair an obstruction merely by adding more sources. The new chart must satisfy the same typed transition/coherence requirements.

## 10. Capability shaping

This layer uses AI primarily for strengths in contextual translation and representation alignment while externalizing predictable weaknesses:

```text
AI strength: cross-representation/context translation
compensator: typed transition witnesses
AI weakness: narrative over-unification
compensator: global existence + uniqueness separation
AI weakness: surface agreement / layer escalation
compensator: exact certified relation layers
AI weakness: forgetting contradictions
compensator: immutable obstruction certificates
AI weakness: path-dependent mappings hidden by pairwise checks
compensator: registered cycle/path witnesses
```

The support API classifies evidence only. It cannot activate canonical knowledge or claim that a real scientific global theory exists.

## 11. Implementation

`src/rakl/atlas_gluing.py` provides immutable research contracts:

```text
AtlasChart
OverlapTransition
CycleConsistencyWitness
GluingObstructionCertificate
AtlasGluingTrial
AtlasGluingReport
```

and operations:

```text
validate_overlap_transition
evaluate_atlas_gluing
```

The implementation deliberately requires explicit global existence and uniqueness evidence rather than assuming a general sheaf theorem for arbitrary scientific charts.

## 12. Next empirical benchmark

The next real benchmark should contain multi-paper theory packets with known compatible and incompatible local views, false pairwise agreements, regime conflicts, observational/mechanistic mismatches, cycle/path inconsistencies and multiple globally compatible theories.

Compare:

```text
naive source union
pairwise-only gluing
pairwise + cycle/path checks
full overlap + global existence/uniqueness contract
```

under the same model, evidence and evaluator budget. If the richer contract does not reduce false global synthesis or improve obstruction localization, keep the simpler representation and preserve the null.
