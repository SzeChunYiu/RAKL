# The Apple Principle

## Metaphor

Suppose many researchers study one apple.

One paper says:

> The apple is red.

Another says:

> The apple is approximately spherical.

Another says:

> The apple is sweet.

Another studies hardness, another volatile compounds, another the mechanics of bruising, another the change of skin color through ripening.

The correct research response is usually **not** to select the “best paper”.

They may be answering different projections of the same object.

RAKL's task is to reconstruct the global object from these partial views, determine where the views are compatible, identify where context explains apparent conflict, discover missing facets, and eventually create a more complete description in a language suited to the problem we actually need to solve.

The Apple Principle now has a second operation as well. Once the apple has been reconstructed enough to expose its structure, RAKL should temporarily abstract away the fact that it is an apple and search other domains for systems that preserve useful parts of that structure. Those systems may have almost no vocabulary overlap with the original literature.

RAKL therefore distinguishes:

```text
GLUE = find and align more projections of the same underlying object
JUMP = find different objects/domains preserving useful deep structure
```

GLUE is conservative because false merges corrupt the Knowledge Atlas. JUMP is exploratory because a candidate analogy can be rejected later. A JUMP never becomes target-domain evidence merely because the structural mapping is elegant.

## Projection-first reading

For every source ask:

1. **What object is being described?**
2. **Which facet(s) does this source observe?**
3. **What projection/measurement operator turns the object into the reported quantity?**
4. **Under what context is the statement valid?**
5. **What is invisible under this projection?**
6. **What alternative projections could reveal the invisible dimensions?**
7. **What downstream quantities does this projection preserve?**

A paper summary is insufficient because it does not expose the projection operator.

## Context tuple

Each projection should be conditioned by a context tuple such as:

```text
population
state/regime
scale/horizon
observation process
instrument/sensor
units
assumptions
intervention/control
method/estimator
uncertainty/evidence level
```

Two claims are contradictory only after aligning their contexts.

Example:

```text
apple is red  | ripe Fuji, reflected visible light
apple is green | unripe Granny Smith, human color label
```

This is not a scientific contradiction. It is an omitted-coordinate problem.

## Four types of source relationship

### Complementary

Sources describe different facets.

```text
red + round + sweet
```

The global picture gains dimension.

### Equivalent

Sources describe the same facet through different mathematical or conceptual languages.

Examples:

```text
same stochastic process under two representations
same state under an invertible coordinate map
same prediction under different sufficient statistics
```

The global picture gains translation rather than another independent dimension.

### Conditionally different

Claims differ because context differs.

Examples:

```text
different scale
different population
different observation model
different boundary condition
different intervention
```

The global picture gains a state/regime coordinate.

### Genuinely contradictory

Claims assert incompatible values after context alignment and uncertainty accounting.

This creates a discriminator problem.

## The Projection Matrix

For an object, maintain a matrix:

| Source | Facet | Projection | Context | Claim | Uncertainty | What it cannot see |
|---|---|---|---|---|---|---|
| P1 | color | visible reflectance → label | ripe cultivar A | red | bounded | taste |
| P2 | shape | 3D geometry | same cultivar | near sphere | bounded | chemistry |
| P3 | taste | sensory assay | same cultivar | sweet | bounded | geometry |

The final object portrait is not a textual average of the rows. It is a structured synthesis of the facets and their dependencies.

## Dependencies among facets

The most valuable research often lies between facets.

For the apple:

```text
chemistry → volatile compounds → perceived taste
pigments + ripening → color
cell structure + water → texture
geometry + material properties → bruising mechanics
```

For a market:

```text
micro order actions
→ queue/liquidity mechanics
→ mesoscopic state
→ volatility/path law
→ settlement probability
→ prediction-market response
→ execution value
```

RAKL therefore searches for **mechanisms connecting facets**, not just more descriptions of each facet.

## The second operation: abstract and jump

The first half of the Apple Principle reconstructs one hidden object from many local views. The second half asks what can be learned once that object has a structured representation.

A mature object portrait should be projected through an abstraction ladder:

```text
L0 exact wording / terminology
L1 domain concept
L2 functional description
L3 causal / mechanistic schema
L4 relational / typed graph
L5 mathematical / dynamical schema
L6 domain-independent structural pattern
```

The purpose is not to delete scientific detail. It is to selectively remove domain identity while preserving the roles, predicates, constraints, causal directions, invariants, boundary conditions, regimes, and intervention semantics needed for a meaningful correspondence.

A practical transformation is controlled noun removal:

```text
apple-specific statement
→ typed roles and relations
→ causal/mechanistic pattern
→ mathematical/invariant pattern
→ foreign-domain search formulations
→ candidate analogues
```

For example, a domain statement can be rewritten as a generic pattern such as “a driving difference produces transport through a boundary resistance” and then instantiated into multiple scientific vocabularies. The retrieved systems are candidates only; RAKL must explicitly test which roles, relations, regimes, and equations are actually preserved.

Every abstraction step carries an erasure ledger. Removed units, scales, substrates, boundary conditions, stochastic assumptions, causal directions, conservation laws, and intervention semantics must be recorded. If an erased coordinate can change the target conclusion, the abstraction may support retrieval but cannot authorize transfer.

This creates two different graphs:

```text
GLUE GRAPH
many descriptions ──> one deeper object

JUMP GRAPH
one deeper object ──> abstract structure ──> distant realizations
```

A good scientific jump preserves deep structure while allowing large surface or disciplinary distance. Random remoteness is not creativity. The jump must expose an explicit mapping witness and the places where the analogy breaks.

Some discoveries may require multi-hop bridges:

```text
target
→ mechanism
→ abstract mechanism family
→ foreign-domain realization
→ method or experiment used there
→ mapped-back target hypothesis
```

Every hop must state what invariant or relation is preserved. `BRIDGE_TO` is a navigation relation, not automatic equivalence or transitive truth.

The operational loop becomes:

```text
GLUE
→ reconstruct object
→ ABSTRACT
→ JUMP
→ build mapping witness
→ TRANSFER hypothesis
→ TEST in target domain
→ GLUE new evidence
→ recurse
```

See `docs/SIMILARITY_ANALOGY_ALGEBRA.md` for the typed relation and witness formalism and `research/SIMILARITY_ANALOGY_LOOP_PROTOCOL.md` for the recurring research protocol.

## From global portrait to our own language

A mature RAKL study should eventually produce an internal representation that may not exactly match any single paper.

This is legitimate when the synthesis is explicit about provenance and derivation.

The process is:

```text
source languages
→ normalized facets
→ equivalence maps
→ mechanism connections
→ contradictions/gaps
→ discriminating evidence
→ latent/global object
→ derived RAKL formalism
```

The derived formalism should make the old source claims recoverable as projections or special cases whenever possible.

That is stronger than inventing a new model merely because the existing ones fit imperfectly.

## Self-application

The Apple Principle also applies to research methods.

One repository may contribute excellent source routing.
Another contributes blind peer review.
Another contributes provenance logging.
Another contributes experiment design.
Another contributes theorem search.

RAKL should not ask which repository is the one correct research framework.

It should treat each as a projection on the object:

> **How should an LLM-assisted research process work?**

RAKL then combines compatible best practices, tests them against explicit meta-QoIs, and derives its own research operating system.
