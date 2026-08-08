# Knowledge Saturation

RAKL treats knowledge saturation as a first-class scientific object.

The purpose is not to prove that “all knowledge has been read”. The purpose is to determine, for a **scoped knowledge fiber**, whether additional search/review rounds are still producing new retained semantic content.

## 1. Saturation is not paper count

A round does not count as new knowledge merely because it finds new papers.

A retained semantic increment is a new item after deduplication in at least one category:

```text
facet
representation class
microscopic mechanism
assumption/boundary
scale/regime law
observation model
identifiability condition
counterexample/impossibility
falsifier/discriminator
error/remainder term
data/source requirement
QoI/decision implication
method/workflow practice
```

Additional citations that only corroborate an existing item strengthen provenance or confidence but do not increase lattice dimensionality.

## 2. Required research routes

A scoped fiber should normally search materially different routes:

```text
FOUNDATIONAL_EXACT
FAILURE_COUNTEREXAMPLE
NEWEST_PRIMARY
ADJACENT_DOMAIN
ALIEN_DOMAIN
ALTERNATIVE_VOCABULARY
CITATION_ANCESTRY_DESCENDANTS
CODE_FRAMEWORK_IMPLEMENTATIONS
```

Not every fiber needs every route. Any omitted route must be explicitly marked not applicable or prohibitively costly.

This prevents “saturation” from meaning “the favorite keyword stopped finding papers.”

## 3. Research-round record

Each round records:

```text
round_id
fiber_id
route
context_id
source universe/query family
candidate count
source IDs
atomic claims extracted
semantic items before dedup
retained new items after dedup
corroborations
rejected false novelty
contradictions opened
new discriminators/data requirements
flat_after_dedup
independent
cost
```

## 4. Saturation states

```text
UNSEARCHED
ACTIVE_NON_FLAT
ROUTE_LOCAL_FLAT
SAME_CONTEXT_PLATEAU
INDEPENDENT_FLAT_1
INDEPENDENT_FLAT_2
INDEPENDENT_FLAT_3
SATURATED_SCOPED
REOPENED_BY_RESIDUAL
```

### Route-local flat

A route is locally flat when repeated materially different searches in that route add no retained semantic items.

### Same-context plateau

The current agent/context has at least the registered number of trailing flat rounds across the required routes.

This is an operational plateau, **not independent saturation**.

### Independent flat

A genuinely different context/implementation/source-routing pass independently adds no high-impact semantic object after deduplication against the frozen ledger.

Same-session personas do not count as independent.

### Saturated scoped

Default strong criterion:

- required route coverage is complete;
- at least 3 trailing same-context eligible flat rounds;
- at least 3 genuinely independent flat rounds;
- no newly discovered contradiction remains unregistered;
- the semantic ledger and evidence cutoff are frozen for the saturation receipt.

A project may choose stricter criteria.

## 5. Unseen-semantic-mass diagnostics

RAKL may use **unseen-species style estimators** as diagnostics, never as proof of exhaustive knowledge.

Treat each normalized semantic object as a “species” and each independent discovery route/round as a sampling process.

Frequency counts such as:

```text
f1 = semantic objects seen exactly once
f2 = semantic objects seen exactly twice
```

can produce exploratory lower-bound or unseen-mass diagnostics inspired by Good–Turing/Chao/species-accumulation methods.

Important limitation:

RAKL searches are adaptive, non-iid and heterogeneous across routes. Therefore species estimators' classical assumptions generally do not hold. Their output is a **novelty-risk diagnostic**, not a saturation certificate.

Use it to answer questions such as:

- Are many retained concepts still singletons?
- Does each new route find mostly already-known objects?
- Is semantic discovery rate flattening?
- Which route appears to contain the most unseen mass?

## 6. Multi-route capture overlap

Independent source/search traditions can be treated descriptively as different capture systems.

High overlap in retained semantic objects across independently designed routes increases confidence that the local conceptual landscape is well covered.

Low overlap is evidence **against** saturation and should trigger:

```text
vocabulary expansion
new adjacent domains
new source tiers
additional independent review
ontology reconciliation
```

Formal capture–recapture estimates require explicit dependence/heterogeneity assumptions and must not be treated as automatic truth.

## 7. Saturation versus problem closure

These are separate booleans.

### Knowledge saturated, problem not closed

Example:

- literature and frameworks are semantically flat;
- all known mechanisms remain observationally equivalent;
- native data needed to separate them do not exist.

Result:

```text
knowledge_saturated = true
problem_closed = false
```

The next action is data acquisition, an identifying intervention, or R10 formalism invention if the residual survives R0–R9.

### Problem closed, knowledge not saturated

A robust decision may already be possible while adjacent research continues to add interpretations or mechanisms.

Result:

```text
problem_closed = true for registered QoI
knowledge_saturated = false
```

This is acceptable if the decision scope does not require the unresolved knowledge.

## 8. Residual-driven reopening

Saturation is reversible.

Any material new native residual, source change, contradiction, protocol change, or independent new semantic object sets the implicated fiber to:

```text
REOPENED_BY_RESIDUAL
```

and identifies which dimensions/routes should be searched again.

## 9. R10 invention after saturation

A saturated literature fiber does not authorize arbitrary invention.

New formalism/mechanics is licensed when:

1. R0–R9 lower-level failure modes are cleared or precisely blocked;
2. known representations/mechanisms have been mapped and tested as far as evidence permits;
3. the residual is explicit and persistent;
4. the new object explains something the current atlas cannot;
5. the invention includes a distinct competitor and null/observation explanation;
6. predictions/falsifiers are frozen before native confirmation;
7. old models appear as special cases/projections where the synthesis claims they should.

## 10. Self-RAKL saturation

Every RAKL meta-fiber also uses this protocol.

Examples:

```text
routing
search
claim extraction
equivalence detection
review architecture
experiment selection
synthesis
memory
stopping
```

RAKL is never globally “finished”. Individual method fibers can become `SATURATED_SCOPED` until a benchmark failure or new external framework reopens them.
