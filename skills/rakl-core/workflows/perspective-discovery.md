# Workflow — Perspective Discovery

Use before deep literature search when the object may be under-specified or when repeated queries are returning the same conceptual neighborhood.

## Goal

Generate **orthogonal ways of looking at the object** before generating search terms.

This is the operational form of the Apple/Knowledge-Atlas Principle.

## Perspective axes

Ask whether the object can be viewed through materially different axes:

```text
observable / sensor
structure / geometry
dynamics / time
mechanism / causal generation
function / downstream QoI
scale / coarse-graining
population / regime
observer / stakeholder
decision / control
failure / adversarial boundary
information / identifiability
mathematical representation
computational realization
historical / evolutionary origin
resource / economic constraint
```

These are prompts for discovery, not a mandatory ontology.

## Procedure

1. Freeze the current object statement and existing facets.
2. Generate candidate perspectives from multiple axes.
3. For each perspective, ask:
   - what would this view measure?
   - what would it be blind to?
   - which disciplines use this view?
   - what terminology do those disciplines use?
   - what observation/experiment would distinguish this view from current ones?
4. Deduplicate perspectives that are only synonyms or coordinate changes.
5. Rank remaining perspectives by expected semantic novelty and decision relevance.
6. Open child knowledge fibers for the highest-value missing perspectives.
7. Generate search queries **after** the perspectives are selected.

## Anti-collapse rule

Do not let the current dominant model generate every perspective.

At least one perspective round should be driven by:

```text
failure modes
adjacent domains
alien domains
opposite causal direction
alternative observer
alternative scale
alternative decision consumer
```

## Output

```text
existing_facets
candidate_perspectives
rejected_equivalent_perspectives
new_facets_opened
new_vocabularies
blind_spots
priority_search_fibers
```

A perspective only enters the promoted atlas after evidence is found; perspective generation itself is hypothesis generation, not knowledge authority.
