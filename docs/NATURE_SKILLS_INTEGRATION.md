# Absorbing `nature-skills` into RAKL

RAKL is not a fork of `Yuan1z0825/nature-skills`. It absorbs several general research-agent design principles and re-expresses them inside the RAKL lattice.

Reference repository:

`https://github.com/Yuan1z0825/nature-skills`

## 1. Router + manifest + static modules

`nature-academic-search` and `nature-reader` use a small router, a manifest axis, always-loaded core fragments, and workflow/source-specific fragments loaded only when needed.

RAKL adopts this pattern because it solves two problems:

1. a giant monolithic prompt is difficult to audit and tends to drift;
2. loading every possible research procedure wastes context and encourages irrelevant reasoning.

RAKL generalizes the pattern:

```text
request/problem
→ detect workflow + active knowledge fibers
→ load core invariants
→ load only relevant workflow modules
→ recurse if a module opens a child fiber
```

The router itself is a RAKL object and may be challenged by alternative routing strategies.

## 2. Multi-source search and graceful fallback

`nature-academic-search` treats source routing and fallback as explicit operational logic rather than improvisation.

RAKL adds a second layer:

```text
source routing
× vocabulary routing
× facet routing
```

Searching more databases is not enough. A new query should often search a different **projection vocabulary**.

Example for “memory”:

```text
Hawkes excitation
renewal/age dependence
Volterra kernel
fractional process
relaxation spectrum
metastability
latent regime
order splitting
```

## 3. Literature pipeline

`nature-literature-pipeline` demonstrates a production pattern:

```text
search → coarse filter → fine read → deliver → archive
```

with deduplication and graceful source degradation.

RAKL changes the optimization target.

Instead of ranking papers primarily by topical relevance, RAKL ranks candidate sources by expected **semantic lattice gain**, for example:

```text
new facet
new mechanism
new representation
new assumption
new counterexample
new identifiability condition
new falsifier
new data source
new economic/decision implication
```

The daily/recurring pipeline should preserve rejected and duplicate candidates in the raw trial log so the research history remains auditable.

## 4. Experiment log and anomaly log

`nature-experiment-log` standardizes experiment IDs, raw archives, structured metadata, and anomaly records.

RAKL generalizes the “experiment” concept to include:

```text
literature search round
model comparison
derivation check
counterexample
native data experiment
review round
self-RAKL benchmark
```

Every failed or anomalous run is potentially a new residual that reopens a knowledge fiber.

RAKL therefore wants a standard record:

```text
run_id
object/fiber
hypothesis
frozen inputs
method version
evidence cutoff
result
residual signature
new semantic objects
promoted/rejected items
next recursion target
```

## 5. Terminology ledger

`nature-shared` uses a terminology ledger so one object does not drift across names.

RAKL extends this into an **ontology/equivalence ledger**.

It must detect both:

```text
FALSE_SPLIT: same object under several names
FALSE_MERGE: several objects under one name
```

This is central to the Apple Principle because different papers often use different vocabularies for the same facet or reuse one word for different mechanisms.

## 6. Consistency sweep

The retrospective consistency sweep in `nature-shared` catches terminology drift, numerical inconsistency, claim/data mismatches, and repeated-edit fragmentation.

RAKL applies the same idea to a knowledge lattice:

```text
same claim with different authority
same quantity with incompatible units
same mechanism assigned different status
same source counted as independent twice
summary stronger than receipt
derived formalism inconsistent with one of its claimed special cases
```

A lattice consistency sweep is therefore mandatory before synthesis/promotion.

## 7. Mutually blind reviewers

`nature-reviewer` requires separate reviewer contexts with a common frozen evidence packet. Reviewers remain blind to one another and reports are frozen before synthesis.

RAKL uses the same epistemic principle for:

```text
scientific review
mechanism review
mathematical review
identifiability review
statistics/reproducibility review
strategy/economic review
self-RAKL method review
```

Important distinction:

```text
same-context reflection != independent review
```

The synthesis pass is a separate object and must not retroactively rewrite the reviewers to manufacture diversity or agreement.

## 8. Raw archive versus promoted knowledge

`nature-literature-pipeline` deliberately separates raw archive writes from canonical knowledge-base modification.

RAKL adopts:

```text
raw/
  discoveries, source projections, duplicate candidates, rejected mappings, failed experiments

knowledge/
  promoted normalized claims, equivalence classes, mechanism sets, validated workflows
```

This prevents a search agent from rewriting the framework simply because it found a new paper.

## 9. What RAKL adds

RAKL's distinctive layer is the recursive object/facet/projection/mechanism model.

It adds:

- the Apple Principle;
- recursive knowledge fibers inside every atomic step;
- representation-equivalence taxonomy;
- compatibility-constrained global product rather than flat model lists;
- microscopic/mechanistic derivation requirements;
- failure-driven reopening of only implicated fibers;
- information-gain-based discriminator selection;
- meta-RAKL where the method recursively studies itself;
- LLM-as-proposer, evidence-as-authority governance.

## 10. Future external-framework absorption

When studying another research-agent repository, RAKL should not ask:

> Should we adopt this repository?

Ask:

> Which facets of the research-process object does this repository describe unusually well?

Then extract projections such as:

```text
routing
memory
planning
review
retrieval
provenance
benchmarking
formal verification
experiment design
human approval
```

Map those projections into the `RAKL_METHOD` meta-lattice, compare them with incumbents, and promote only the pieces that win explicit meta-evaluations.
