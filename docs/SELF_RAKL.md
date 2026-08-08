# Self-RAKL — Recursively Improving the Research Method

RAKL must be able to apply its own reasoning process to itself.

The method is therefore treated as a mutable research object, not a fixed prompt.

## 1. Meta-object

Define:

```text
OBJECT = RAKL_METHOD
```

Its facets include:

```text
problem decomposition
workflow routing
source discovery
source reliability/fallback
claim extraction
ontology and terminology normalization
representation equivalence
contradiction handling
knowledge-gap detection
experiment/discriminator selection
formalism synthesis
review/adversarial critique
evidence logging
reproducibility
saturation/stopping
context/token efficiency
LLM prompt policy
```

Each facet has an incumbent implementation and may have challengers.

## 2. The LLM is a proposer

The LLM may propose:

- new decomposition strategies;
- additional facets;
- better source-routing policies;
- better vocabularies or search terms;
- new equivalence mappings;
- new contradiction-resolution rules;
- new experiment-selection heuristics;
- new review configurations;
- new stopping criteria;
- new schemas or software architecture.

It may not promote its own proposal merely because it sounds persuasive.

## 3. Meta-QoIs

RAKL-method variants should be compared on explicit quantities such as:

```text
semantic recall
precision / false novelty rate
source diversity
primary-source share
contradiction detection
missing-facet discovery
mechanism-identification quality
experiment information gain
known-answer accuracy
unsupported-claim rate
reproducibility
context/token cost
latency/compute cost
user decision quality
```

Some QoIs are lexicographic gates rather than weighted objectives. For example, lower token cost does not compensate for fabricated evidence.

## 4. Challenger protocol

A method improvement follows the same process as a scientific model improvement.

### Step 1 — Observe a residual

Examples:

```text
search repeatedly returns the same vocabulary
reviewers all make identical mistakes
paper count rises but semantic novelty does not
contradictions are missed because terminology differs
lattice explodes combinatorially
wrong workflow modules load
LLM proposes unsupported equivalence mappings
```

### Step 2 — Open a meta-fiber

Research alternative approaches to the failing method step.

### Step 3 — Normalize alternatives

Determine whether alternatives are genuinely different or only different descriptions.

### Step 4 — Freeze evaluation

Specify benchmark tasks, expected behavior, negative controls, failure criteria, cost metric, and evidence cutoff before comparison.

### Step 5 — Shadow test

Run incumbent and challenger on the same immutable task packet.

### Step 6 — Blind review

If the evaluation involves qualitative judgment, use mutually isolated reviewers and freeze reports before synthesis.

### Step 7 — Promote narrowly

Promote only the step whose evidence supports improvement. Do not rewrite unrelated parts of RAKL.

### Step 8 — Preserve rollback

Keep the prior workflow version and a supersession receipt.

## 5. Router self-improvement

RAKL uses a manifest-driven router.

The router can itself be challenged.

Example alternatives:

```text
keyword router
LLM classifier
hierarchical router
rule + LLM hybrid
retrieval-based workflow selector
bandit/learned policy
```

Evaluate routing with a frozen corpus containing ambiguous and adversarial tasks. Required metrics include correct workflow load, unnecessary-module load, missed required module, and token cost.

## 6. Search self-improvement

Search itself is a fiber.

Dimensions include:

```text
query decomposition
source tiers
fallback sequence
keyword expansion
citation chaining
semantic search
negative-result search
counterexample search
adjacent-domain search
alien-domain search
freshness policy
deduplication
stopping
```

A search round that produces many papers but no new semantic objects is low-value.

## 7. Decomposition self-improvement

Problem atomization is not assumed correct.

RAKL should periodically ask:

- Are two atoms actually one object under different names?
- Is one atom hiding multiple independent assumptions?
- Is the boundary chosen for convenience rather than causal/mechanical meaning?
- Does a downstream failure point to a missing intermediate step?
- Is the current decomposition optimal for the decision/QoI?

Alternative decompositions can be compared by whether they reduce ambiguity, enable stronger derivations, improve experiment design, or reduce repeated work.

## 8. Equivalence-engine self-improvement

False novelty is expensive. False equivalence is dangerous.

The equivalence engine should therefore have explicit error modes:

```text
FALSE_SPLIT   same object counted as two
FALSE_MERGE   distinct mechanisms collapsed as one
SCOPE_LEAK    equivalence assumed beyond proven context
QOI_LEAK      equivalent for one consumer treated as globally equivalent
```

Create known-answer libraries with exact coordinate transformations, observationally equivalent mechanisms, asymptotically equivalent models, and analogy-only pairs.

## 9. Review self-improvement

A review process should itself be evaluated for:

```text
independence
coverage
blocking calibration
evidence grounding
novel concern yield
false concern rate
diversity of reasoning
ability to detect planted flaws
```

Same-context reviewer personas do not count as independent.

## 10. Saturation self-improvement

The stopping rule must distinguish:

```text
no new papers
no new vocabulary
no new semantic objects
no new decision-relevant objects
no new independent objections
```

RAKL's preferred unit is **semantic retained novelty after deduplication**.

A native residual reopens the affected local fiber even if prior literature rounds were flat.

## 11. Self-modification safety

RAKL must never optimize itself by making tests easier.

Prohibited self-improvement patterns:

```text
remove a falsifier after failure
change acceptance threshold after observing result
drop hard cases from benchmark
rewrite old evidence
promote a challenger tested on different tasks
call same-context review independent
replace missing evidence with LLM confidence
```

## 12. Desired long-run behavior

RAKL should increasingly learn:

- which decompositions work for which problem classes;
- which search sources and vocabularies reveal distinct facets;
- which representation mappings are often equivalent;
- which residuals imply which hidden mechanisms;
- which discriminators most efficiently destroy ambiguity;
- which research modules are unnecessary for a given task;
- when a new formalism is genuinely warranted.

The result should be a research system that becomes better at **choosing how to think**, not merely better at generating more text.
