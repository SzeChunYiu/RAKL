# Risk and Failure Registry

## R1 — Field circularity

**Failure:** building the field requires solving the original problem.

**Detection:** compare total field construction cost against baseline search.

**Verdict:** `FIELD_CONSTRUCTION_CIRCULAR_OR_COSTLY`.

---

## R2 — False gradient

**Failure:** local potential points toward actions that look promising but hurt root progress.

**Detection:** gradient/action rank correlation and false-attractor rate.

---

## R3 — Attractive metaphor

**Failure:** lightning analogy drives architecture despite negative experiments.

**Control:** all natural analogies enter through the Spark-to-Mechanic protocol.

---

## R4 — Representation leakage

**Failure:** transformed representation contains target answer or evaluator-only information.

**Control:** freeze transform semantics and provenance before answer exposure.

---

## R5 — Lossy lift treated as equivalence

**Failure:** important constraints disappear.

**Control:** `RepresentationTransitionWitness` with non-preserved coordinates.

---

## R6 — Representation bloat

**Failure:** higher-dimensional lift makes the problem easier conceptually but computationally impossible.

**Metric:** lift construction + solve + decode cost.

---

## R7 — Conductance lock-in

**Failure:** early lucky successes reinforce the wrong path family.

**Controls:**

```text
exploration floor
decay/staleness
scope matching
failure memory
fresh reset benchmark
```

---

## R8 — Negative-memory overblocking

**Failure:** prior failures prevent re-evaluation in a changed regime.

**Control:** failure is scope-qualified, not global.

---

## R9 — Branch explosion

**Failure:** lightning-style branching becomes beam search with huge cost.

**Control:** budgeted branching, entropy/concentration rule, route diversity accounting.

---

## R10 — Hidden-facet miss

**Failure:** no observed residual -> premature stop.

**Control:** coverage scouts and explicit unseen-coordinate risk.

---

## R11 — Over-refinement

**Failure:** recursive scale controller keeps decomposing.

**Control:** value-of-refinement / coarsening alternatives / budget / root-progress checks.

---

## R12 — Composition compounding

**Failure:** local reliability degrades rapidly across many interfaces.

**Control:** hierarchical verification and parent invariants.

---

## R13 — Verification false negatives

**Failure:** checking every local interface rejects valid global solutions.

**Control:** measure sensitivity/specificity and compare verification schedules.

---

## R14 — Meta-controller merely spends more compute

**Failure:** gains vanish under matched resources.

**Control:** strict cost receipt and fixed-budget arms.

---

## R15 — Diagnosis theatre

**Failure:** labels look sensible but do not improve decisions.

**Control:** separate diagnostic accuracy from end-task effect.

---

## R16 — Specialist non-differentiation

**Failure:** correct mechanic choice does not matter because all specialists perform similarly.

**Control:** measure conditional specialist advantage.

---

## R17 — Learned field overfits surface vocabulary

**Failure:** strong development geometry, poor surface-shifted transfer.

**Control:** structural shift benchmark and hidden renaming.

---

## R18 — Semantic embedding mistaken for solvability geometry

**Failure:** semantically similar states require different actions.

**Control:** action-consequence probes.

---

## R19 — Authority leakage

**Failure:** high field score is described as evidence/confidence in scientific truth.

**Control:** types, naming, test assertions, and no authority mutation.

---

## R20 — Root/local confusion

**Failure:** local residual shrinks while root result worsens.

**Control:** every episode records both local and root effect.

---

## R21 — New ontology duplicates existing one

**Failure:** `MechanicKind` becomes a competing taxonomy with current failure lattice.

**Control:** map to existing objects; only create new categories after gap benchmark.

---

## R22 — Grand-system trap

**Failure:** implementation becomes too large to attribute.

**Control:** promote atomic mechanics independently.

---

## R23 — Benchmark adapts after seeing results

**Failure:** thresholds/tasks drift to favor challenger.

**Control:** freeze development protocol and separate fresh assurance.

---

## R24 — Oracle contamination

**Failure:** exact cost-to-go or hidden solution leaks into learned field input.

**Control:** explicit solver/evaluator information boundary.

---

## R25 — “Higher dimension” becomes automatic complexity

**Failure:** every problem is lifted even when original space is simpler.

**Control:** representation search must include identity transform and charge lift overhead.
