# RAKL Architecture

## 1. Objects, facets, projections, contexts

RAKL separates four concepts that ordinary literature review often conflates.

### Object

The thing we are trying to understand or solve.

Examples:

- an apple;
- market volatility;
- queue priority;
- a theorem assumption;
- a research method;
- RAKL itself.

### Facet

A semantically coherent dimension of the object.

For an apple:

```text
color
shape
taste
texture
chemical composition
ripening dynamics
```

For a market model:

```text
state
memory
noise
tail behavior
observation process
scale
execution consequence
```

### Projection

A source-derived statement about one or more facets.

A projection is always contextual:

```text
source
claim
facet(s)
population
scale
observation model
assumptions
method
evidence authority
uncertainty
```

### Context

The conditions under which a projection is asserted. Contradictions are assessed **after** context alignment.

## 2. The Apple Principle as mathematics

Let latent object state be `Z`. A source observes or studies the object through projection operator `P_i` under context `c_i`:

\[
y_i = P_i(Z; c_i) + \epsilon_i.
\]

The research problem is not to select one `y_i` as the truth. It is to infer a useful latent representation `Z*` and the family of projection maps that make the evidence jointly coherent.

RAKL therefore solves a constrained inverse problem:

\[
\text{find } (Z,\{P_i\})
\quad\text{s.t.}\quad
P_i(Z;c_i) \approx y_i
\]

subject to scientific, mathematical, observational, and decision constraints.

When no single `Z` fits all projections, RAKL must determine whether the cause is:

1. context dependence;
2. terminology/ontology mismatch;
3. observation bias;
4. approximation error;
5. genuinely different subpopulations/regimes;
6. scientific contradiction;
7. missing latent coordinate;
8. wrong object decomposition.

## 3. Knowledge fiber

Every unresolved atomic step owns a knowledge fiber:

```text
observables
representations
microscopic mechanisms
assumptions
scales/regimes
observation/clock/censoring models
coarse-graining/projection operators
identification/inference methods
numerical methods
falsifiers/counterexamples
native data products
QoIs
decision/economic consumers
```

Each member can recursively open another knowledge fiber.

## 4. Representation relationship taxonomy

Before counting two papers as two theories, classify their relationship:

```text
EXACT_ISOMORPHISM
GENERATOR_EQUIVALENCE
OBSERVATIONAL_EQUIVALENCE
ASYMPTOTIC_EQUIVALENCE
QOI_EQUIVALENCE
APPROXIMATE_REPRESENTATION
ANALOGY_ONLY
INCOMPATIBLE
UNKNOWN
```

This taxonomy is not cosmetic. It controls implementation debt and experiment selection.

## 5. Global lattice

The raw Cartesian product of all choices is usually enormous.

RAKL therefore constructs a compatibility-constrained graph

\[
\Gamma \subseteq K_1 \times K_2 \times \cdots \times K_n.
\]

A combination is rejected before empirical testing if it violates any hard constraint such as:

```text
units/support
causal availability
population identity
scale assumptions
observation model
mathematical regularity
protocol/rule state
identified-set authority
error-budget composition
```

Only compatible paths through the lattice become candidate theories or methods.

## 6. The LLM's role

The LLM is used for high-recall cognition:

- decompose problems;
- generate alternative vocabularies;
- find hidden facets;
- map papers into facets;
- propose equivalence mappings;
- propose competing mechanisms;
- propose discriminating experiments;
- synthesize a new formalism/language;
- critique the current RAKL procedure.

The LLM is **not** allowed to self-certify its proposals.

Promotion requires explicit evidence gates, known-answer worlds, counterexamples, reproducible records, or user-approved governance.

## 7. Recursive self-improvement

RAKL treats its own workflow as object `RAKL_METHOD`.

Meta-facets include:

```text
decomposition
routing
search/source selection
claim extraction
ontology normalization
equivalence detection
contradiction handling
gap detection
experiment selection
synthesis
review
stopping/saturation
logging/provenance
LLM prompting/context policy
```

For each meta-facet, RAKL can ingest alternative practices from other agent/research systems and compare them.

Example:

```text
search router
├── one giant prompt
├── static workflow rules
├── manifest-driven dynamic router
├── planner/executor agents
└── learned policy
```

These alternatives receive the same treatment as scientific models. Their performance is judged on explicit meta-QoIs such as recall, precision, evidence groundedness, token/latency cost, reproducibility, contradiction detection, and downstream decision quality.

## 8. Self-improvement promotion protocol

A proposed RAKL-method change follows:

```text
CURRENT PRACTICE
→ residual/failure evidence
→ recursive knowledge fiber
→ alternative practices
→ equivalence/difference map
→ benchmark/known-answer tasks
→ isolated reviewer critique
→ shadow comparison
→ promotion or rejection
```

The incumbent remains active until the challenger earns promotion.

## 9. Blind reflection

A single LLM context is prone to narrative lock-in. RAKL distinguishes:

### Reflection

Same-context critique. Cheap and useful, but not independent.

### Independent review

Multiple contexts receive the same frozen evidence packet and predeclared review lenses. They do not see each other's reports. Reports are frozen before synthesis.

### Meta-review

A separate synthesis compares frozen reviews, identifies consensus and disagreement, and converts them into new knowledge-fiber children or discriminators.

RAKL must never label same-context personas as independent replication.

## 10. Raw versus promoted knowledge

RAKL stores at least two layers:

```text
raw/
  source projections, extracted claims, candidate mappings, failed ideas

knowledge/
  normalized facets, promoted equivalence classes, surviving mechanisms, validated procedures
```

Raw ingestion never silently rewrites promoted knowledge.

## 11. Failure-driven recursion

Every failure emits a residual signature. Examples:

```text
source/access failure
schema/parser failure
clock/availability failure
population/target mismatch
observation/censoring mismatch
identifiability failure
mean fit but variance/tails fail
scale instability
transport failure
numerical instability
execution/value failure
```

The residual determines which fiber dimensions reopen. RAKL should not respond to a local defect by globally searching random models.

## 12. Stopping

Research is not saturated because many papers were read.

A local fiber is `FLAT_SAME_CONTEXT` when a new search/review round adds no new retained:

```text
facet
representation class
mechanism
assumption
scale law
identifiability condition
counterexample
falsifier
error/remainder
data source
QoI/decision implication
```

Independent flat rounds are tracked separately.

A new native residual reopens the relevant fiber.
