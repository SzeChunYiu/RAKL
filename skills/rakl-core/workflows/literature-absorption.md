# Workflow — Literature Absorption v2: Quantified Apple Reading

Use for papers, repositories, books, standards, datasets or other knowledge sources.

## Goal

Do not produce a flat bibliography. Convert sources into contextual projections on a shared object, measure retained semantic gain, and stop/reopen search using a bounded, auditable rule.

Literature acquisition is a **research-machine process**. Raw paper count, token count and citation count are inventory, not knowledge gain.

## Round lifecycle

For each unresolved fiber child:

```text
intent / residual
-> generate materially different search routes
-> retrieve authentic source identities
-> triage
-> read/extract projections
-> normalize/deduplicate meaning
-> GLUE / contradiction update
-> ABSTRACT / JUMP when useful
-> emit round metrics
-> assess bounded KNOWLEDGE saturation
```

Search route families should include, when applicable:

1. exact/foundational theory;
2. impossibility, counterexample and failure literature;
3. newest primary research;
4. adjacent scientific/mathematical domains;
5. deliberately alien domains with the same formal structure;
6. alternative vocabularies, notation and ontology;
7. citation ancestry and influential descendants;
8. standards/repositories/datasets/grey literature when they can materially change the target.

A route may be explicitly blocked when access or source availability prevents execution. Blocked is not flat.

## Atomic source projection

Extract:

```text
source_id / immutable source identity
object
facet(s)
projection / observation operator
claim
mathematical object
mechanism interpretation
context tuple
assumptions
scale
observation model
method / inference
evidence level
uncertainty
counterexample / falsifier
data requirement
what this projection cannot see
mapping to existing lattice
QoI / decision implication
```

A prose paper summary is insufficient for an Apple reconstruction.

## Source authenticity and model tiering

Retrieval must return real source identities rather than allowing a generative model to invent citations.

Cheap or quantized/local models may be used for high-volume triage, vocabulary generation, candidate extraction and duplicate detection when their model/revision/quantization/runtime identity is recorded. Consequential claims must remain bound to the primary source and pass the normal extraction/evidence checks; a lightweight model's confidence cannot substitute for source evidence.

The research machine may choose model/tool tier by measured cost-quality performance, but model changes define a new observational epoch unless comparability is recovered.

## Semantic gain

A source has semantic gain when it contributes a retained, non-equivalent object such as:

```text
new facet
new mechanism
new context coordinate/regime
new representation class
new assumption/boundary
new scale law
new identifiability condition
new contradiction/counterexample
new falsifier/discriminator
new error/remainder
new data/observation source
new blind spot / unknown coordinate
new downstream decision implication
```

A source that repeats an existing semantic object may strengthen provenance/evidence without increasing lattice dimensionality.

For each round record at least:

```text
queries
sources processed
relevant sources
retained semantic object ids
new facets
new mechanisms
new contexts
new contradictions
new falsifiers
new blind spots
cost policy + cost
evidence pointers
```

Useful descriptive indicators include:

```text
relevance precision within the processed set
semantic novelty / source
semantic novelty / query
cost / retained semantic object
corroboration-only rate
semantic-duplicate rate
new-contradiction yield
new-blind-spot yield
```

Do not call a metric “recall” without a bound reference universe or another defensible denominator.

## Apple GLUE

Map new claims to:

```text
new facet
new member of existing facet
equivalent representation
contextual refinement
genuine contradiction
corroboration only
analogy only
```

Align context before declaring contradiction. Track what each projection cannot see. Search mechanisms connecting facets, not merely more property descriptions.

False merge is a first-class failure: normalization must not collapse distinct concepts merely to make the object portrait simpler.

## ABSTRACT + JUMP

When the object portrait is structured enough, abstract away domain nouns while preserving roles, constraints, causal directions, invariants, boundaries, regimes and intervention semantics.

Maintain an erasure ledger. Then search distant domains for structural realizations.

Every JUMP candidate must record:

```text
source domain/object
target roles
mapping witness
preserved structure
material disanalogies
erased coordinates
hypothesized transferable mechanism
target-domain falsifier
```

A JUMP is proposal generation, never target-domain evidence.

## Bounded saturation / stopping contract

Saturation is semantic and route-based, never paper-count based.

For the active knowledge fiber, stop broad acquisition only when:

```text
recent retained semantic novelty == 0
AND >= registered minimum independent route families are flat
AND required route-family coverage is complete or explicitly blocked
AND no native residual reopens KNOWLEDGE
AND no unresolved high-impact contradiction requires a discriminator
AND the evidence cutoff is fresh enough for the registered problem horizon
```

Use `src/rakl/research_machine_workflow.py` as the executable adapter to existing `saturation_vector.py`.

If new semantic objects continue to arrive, the state is `NOT_SATURATED` even if the search budget expires.

No stopping criterion can prove that undiscovered sources do not exist. Record a bounded coverage/saturation statement only.

## Persistent incremental update

Do not re-read the whole corpus every object-level iteration.

```text
initial problem
-> broad bounded saturation

ordinary local iteration
-> retrieve normalized prior knowledge

new residual / contradiction / ontology change
-> targeted resaturation of affected fiber

freshness event / new literature
-> incremental search from prior cutoff
```

Previously normalized sources remain history; new rounds append/supersede rather than erase.

## Archive rule

Raw discoveries enter proposal/raw storage first. Canonical knowledge requires normalization, compatibility review and evidence authority.

Reading/search metrics are measurement/control inputs. They do not mint truth, novelty, theorem, method or promotion authority.
