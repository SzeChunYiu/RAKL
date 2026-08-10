# RAKL lattice metrology, learning storage and capacity control

Status: Round 044 / V2.1 hardening companion specification.

## 1. Scope

This document turns the informal intuition that a Knowledge Lattice can "grow in volume", "become denser", or "stay flat" into executable observables. The implementation owner is `src/rakl/lattice_metrology.py`; the deterministic known-answer trace is `src/rakl/mini_research_metrology.py`.

The metrology is deliberately conservative. RAKL does **not** claim that its typed atlas has a physically meaningful Euclidean volume, nor that an embedding-space volume is scientific knowledge. The current volume is a discrete occupancy proxy over registered symbolic coordinates.

## 2. What is actually learned and where it lives

A normal RAKL research cycle does not update the base LLM weights. It updates external research state.

The information path is:

```text
source bytes
  -> contextual scientific projection
  -> normalization
  -> identity resolution
  -> provenance binding
  -> typed Knowledge Atlas insertion / relation mapping
  -> derived memory/index views
  -> bounded active context
  -> LLM proposal
  -> external verification
  -> gated canonical update
  -> residual/saturation/method-experience update
```

These objects are intentionally different.

### Tier 0: canonical authority roots

Raw evidence, identities, provenance, verified atlas objects, verification records, negative history and saturation records live at the canonical layer. Canonical evidence is append-only/addressable; a later interpretation may supersede an earlier one without deleting the historical event.

### Tier 1: rebuildable representations and indexes

Normalization products, lexical indexes, graph indexes, optional embeddings and materialized views are navigation/representation structures. They can be rebuilt from canonical roots. Similarity in an embedding is not scientific identity, compatibility or authority.

### Tier 2: bounded working set

The context compiler selects the target-conditioned evidence needed for the current operation. This is an active materialization, not the whole archive.

### Tier 3: LLM prompt

Only the bounded prompt packet is sent to the replaceable LLM. The model proposes; it does not directly mutate canonical scientific state.

### Method memory

Validated trajectories can become candidate reusable procedures or method changes. This is external procedural memory. A method candidate still requires transfer/assurance before strong promotion.

## 3. Projection, transformation and compression are different operations

RAKL uses several transformations that must not be conflated.

### Scientific projection

A contextual projection selects what a source asserts for a registered scientific question and context:

```text
c = pi_(q,gamma)(e)
```

This changes scientific representation: which claim/measurement/equation/assumption is being considered and under which scope.

### Normalization

Normalization aligns units, terminology, symbols or coordinates:

```text
c' = N(c)
```

It can expose representational equivalence but cannot increase scientific authority.

### Retrieval projection

An optional vector/index projection can be written:

```text
z = E(v)
```

It is used to retrieve or navigate candidates. Distance in `z` never defines canonical identity or compatibility.

### Compression/materialization

Compression is derivative storage work:

1. exact/identity collapse removes duplicate semantic objects while preserving all source lineage;
2. a lossless view must be reconstructable from pinned canonical roots;
3. a lossy view must record its source pins, transform and erasure ledger;
4. active-context compilation selects only relevant material under a token budget;
5. method trajectories may be consolidated into candidate procedural memory.

A lossy summary can save tokens; it cannot replace the raw evidence needed for strong verification.

## 4. Discrete knowledge-volume proxy

For one lattice snapshot let each atom have a research fiber `f` and typed kind `k`.

Define the occupied cell set

```text
C = {(f(a), k(a)) : a is an active/canonical atlas atom}
```

and the current discrete occupied-volume proxy

```text
V_occ = |C|.
```

This answers a narrow question: how many distinct fiber/type regions of the registered symbolic space are occupied?

It deliberately does **not** answer how large a continuous latent manifold is, how important the knowledge is, or how much disk space is consumed.

The observed type-span capacity is

```text
V_span = (# active fibers) * (# occupied atom kinds)
```

and occupancy is

```text
rho_occ = V_occ / V_span
```

when `V_span > 0`.

The span is only a dashboard coordinate. It is not a reason to manufacture atoms in empty cells.

## 5. Density is multi-coordinate

One scalar "density" would hide scientifically different changes, so V2.1 reports separate densities.

### Atom-per-cell density

```text
rho_atom = # atoms / V_occ
```

A new semantic object inside an already occupied `(fiber, kind)` cell increases this density without expanding `V_occ`.

### Relation density

For `n >= 2` atoms and `w` registered typed witnesses:

```text
rho_relation = w / choose(n, 2)
```

This is graph fill, not confidence. Unknown/unregistered pairs remain different from incompatible pairs.

### Evidence-binding density

RAKL counts source/evidence bindings on atoms and relation witnesses separately and tracks the number of distinct evidence roots. Independent corroboration can therefore densify evidence without creating fake semantic volume.

## 6. Transition classes

For two snapshots `K_t -> K_(t+1)`, `compare_lattices()` reports a vector of deltas rather than one compensatory score.

### `EXPANSION`

`Delta V_occ > 0`.

A previously unoccupied fiber/type region is now populated.

### `SEMANTIC_DENSIFICATION`

`Delta V_occ = 0` and new semantic atoms are added without another primitive growth coordinate changing.

### `RELATIONAL_DENSIFICATION`

No new occupied cell or atom is needed, but additional typed relation witnesses are established.

### `EVIDENCE_DENSIFICATION`

No semantic or relational object is added, but evidence/source bindings increase. Independent replication of an existing canonical claim belongs here when its semantics are unchanged.

### `MIXED_DENSIFICATION`

Several density coordinates increase together. Real scientific updates commonly fall here; for example a new finite-amplitude representation may add an atom, relation witnesses and evidence while occupying an already known period/representation cell.

### `FLAT`

None of the registered primitive lattice coordinates changes.

A flat transition may still consume resources; it must not be counted as new knowledge merely because the LLM produced new prose.

### `CONTRACTION_OR_VIEW_CHANGE`

A primitive count decreases. Because canonical history is append-only, this normally indicates an active-view change, supersession projection or an invalid comparison rather than deletion of canonical evidence.

## 7. Known-answer metrology trace

`src/rakl/mini_research_metrology.py` reuses the V2 pendulum world and produces four transitions:

```text
EMPTY -> R0  : expansion
R0    -> R1  : finite-amplitude mixed densification
R1    -> R2  : flat repeat
R2    -> R3  : independent evidence densification
```

The values are emitted by executable code and tested in `tests/test_mini_research_metrology.py`; they must not be manually changed in paper figures.

This demonstrates implementation semantics only. It does not establish that RAKL improves real scientific discovery.

## 8. Why a duplicate can be flat while replication can add value

"Same semantic content" and "zero value" are not equivalent.

- An exact repeat of an already stored source/lineage can be flat.
- A semantically duplicate statement from the same evidence lineage is normally flat semantically and does not earn independence.
- A genuinely independent replication can be semantically flat but evidence-dense: confidence/coverage may improve while `V_occ` stays fixed.
- A contradiction under aligned context can add a typed obstruction/negative-history object even when it does not expand the target's support path.

This is why RAKL cannot use atom count alone as a knowledge-growth metric.

## 9. Practical anti-explosion controls

RAKL needs two different growth policies: archive preservation and active-state capacity.

### Canonical archive

The authority root should preserve evidence and lineage. Practical deployments should use content-addressed blob storage, hash-level byte deduplication, immutable object storage and cold tiers. Compression may reduce physical bytes if exact hashes/reconstruction semantics remain valid.

The reference implementation currently specifies the invariants but does **not** yet provide a production object-store/cold-tier backend. This remains an engineering gap; it should not be hidden by prompt-level compression.

### Active lattice/materialized view

`ActiveLatticeCapacityPolicy` registers explicit limits for active atoms, witnesses, fibers and observed type-span cells.

When a transition is flat, the active update can be rejected as redundant. When active capacity is exceeded, the correct action is:

```text
COMPACT_OR_DEMOTE_ACTIVE_VIEW
```

not delete canonical evidence.

The active view can then be rebuilt around current target fibers, mandatory contradictions, negative history, authority prerequisites and high-value support paths.

### Prompt capacity

The existing context compiler separately enforces a token budget. If mandatory epistemic material does not fit, the operation returns `CANNOT_COMPILE` rather than silently dropping it.

### Search capacity

Search budgets remain non-terminal. Exhausting a token/round/tool budget is not semantic saturation.

## 10. What should be monitored in real projects

At every canonical update, a production trace should record at least:

```text
atom_count
fiber_count
kind_count
occupied_volume_cells
observed_type_span_cells
atom_cell_density
witness_count
relation_density
atom_evidence_bindings
witness_evidence_bindings
distinct_evidence_sources
semantic_novelty
negative_history_count
blocking_epistemic_cuts
target_support_paths
archive_bytes or archive tokens
active_context_tokens
active/archive ratio
capacity decision
```

For target-conditioned evaluation, add quality coordinates such as support-path opening, identified-set shrinkage, contradiction resolution and held-out predictive/experimental performance. Geometry is not a substitute for usefulness.

## 11. Remaining hardening items

V2.1 closes the missing executable volume/density distinction at the symbolic-lattice level, but several items remain empirical or infrastructural:

1. calibrate whether the discrete `(fiber, kind)` occupancy proxy predicts useful research progress across domains;
2. compare it with alternative graph/entropy/description-length measures without letting a convenient scalar become scientific authority;
3. implement a real content-addressed archive backend and measure physical storage growth;
4. benchmark active-view compaction under long runs and verify mandatory recall stays one;
5. run the same-model matched LLM experiment; the deterministic pendulum trace still uses zero LLM calls;
6. integrate exogenous-discovery coverage into formal saturation for framework/novelty searches.

Those are registered work, not claims already established.
