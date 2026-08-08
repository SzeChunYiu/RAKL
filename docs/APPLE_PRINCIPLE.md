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
