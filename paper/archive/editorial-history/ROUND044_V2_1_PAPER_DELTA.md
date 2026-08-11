# Round 044 / V2.1 manuscript delta

Status: candidate manuscript changes tied to executable Round 044 code/receipts. Do not merge the claims below into release prose unless the exact branch validations and source bindings remain clean.

## A. Paper review findings

The V2 manuscript already states the strongest boundaries correctly:

- RAKL is a candidate evidence-governed methodology, not an established claim of empirical scientific superiority.
- proposal generation is separated from canonical authority;
- memory/context compression is derivative and rehydratable rather than canonical truth;
- the 17-stage atomic lifecycle is executable;
- resource exhaustion is not saturation;
- real-project residuals can reopen apparently closed method surfaces;
- a semantically equivalent prior methodology must narrow the novelty claim.

Round 044 found three manuscript-level gaps that should be closed before the next release.

1. The phrase/intuition "lattice growth" lacked an executable decomposition into occupied volume, semantic density, relation density, evidence density and flat updates.
2. The manuscript did not state sharply enough that ordinary RAKL learning changes **external scientific/method state**, not the base LLM's model weights.
3. External-framework/novelty saturation lacked a required function-first/adjacent-discipline coverage gate. The user-supplied Obsidian analogy exposed this as a real false negative.

## B. Candidate insertion: operational metrology of Knowledge Atlas growth

Suggested location: Formal Method, after the memory/context-efficiency discussion and before stopping/saturation.

### Operational atlas-growth metrology

The term *lattice growth* is descriptive unless a coordinate system is registered. RAKL therefore does not treat a visualization's physical area, a force-directed graph layout, or an embedding-space volume as scientific knowledge volume. In the reference implementation, one conservative discrete occupancy proxy is defined over the symbolic atlas. If each active/canonical knowledge atom `a` has a research fiber `f(a)` and typed atom kind `k(a)`, define

\[
\mathcal C_t=\{(f(a),k(a)):a\in K_t\},\qquad
V_t^{\mathrm{occ}}=|\mathcal C_t|.
\]

`V_occ` counts occupied `(research fiber, atom type)` cells. It is explicitly **not** a Euclidean or latent-vector volume. Several density coordinates are reported separately rather than collapsed into one score:

\[
\rho_t^{\mathrm{atom}}=\frac{|A_t|}{V_t^{\mathrm{occ}}},
\qquad
\rho_t^{\mathrm{rel}}=\frac{|W_t|}{\binom{|A_t|}{2}}
\]

when the denominators are defined, together with atom/witness evidence-binding counts and distinct evidence-root counts.

A transition is classified as **expansion** when a previously unoccupied symbolic cell becomes occupied; **semantic densification** when an additional semantic atom enters an already occupied cell without another primitive growth coordinate changing; **relational densification** when typed relation witnesses increase without new cells/atoms; **evidence densification** when evidence bindings or independent evidence roots increase without semantic expansion; **mixed densification** when several density coordinates increase together; and **flat** when none of the registered primitive coordinates changes. A decrease is treated as an active-view/contraction event requiring interpretation because canonical evidence history is append-only.

These geometric diagnostics do not themselves measure scientific usefulness. Target-conditioned quantities such as epistemic-cut closure, support-path opening, identified-set shrinkage, contradiction resolution and held-out scientific performance remain separate coordinates.

## C. Candidate insertion: deterministic known-answer growth trace

Suggested location: Experiment 1 software-contract result or a compact supplementary table.

The existing pendulum known-answer world can now emit an exact metrology receipt from executable code. The frozen Round 044 receipt reports:

| Snapshot | Atoms | Occupied cells | Atoms/cell | Typed witnesses | Relation density | Evidence bindings | Distinct evidence roots |
|---|---:|---:|---:|---:|---:|---:|---:|
| EMPTY | 0 | 0 | 0.000000 | 0 | 0.000000 | 0 | 0 |
| R0 | 8 | 7 | 1.142857 | 8 | 0.285714 | 21 | 6 |
| R1 | 9 | 7 | 1.285714 | 11 | 0.305556 | 26 | 7 |
| R2 | 9 | 7 | 1.285714 | 11 | 0.305556 | 26 | 7 |
| R3 | 9 | 7 | 1.285714 | 11 | 0.305556 | 27 | 8 |

The corresponding transitions are:

- `EMPTY -> R0`: `EXPANSION`, `Delta occupied cells = +7`;
- `R0 -> R1`: `MIXED_DENSIFICATION`, `Delta occupied cells = 0`, `Delta atoms = +1`, `Delta witnesses = +3`, `Delta evidence bindings = +5`;
- `R1 -> R2`: `FLAT` on all registered primitive metrology coordinates;
- `R2 -> R3`: `EVIDENCE_DENSIFICATION`, no new atom/cell/relation, `Delta evidence bindings = +1`, `Delta distinct evidence roots = +1`.

This is an implementation/known-answer demonstration. It does not establish that RAKL makes an LLM scientifically better, and the deterministic demo still makes zero LLM calls. The matched same-model experiment remains necessary for that claim.

Source of truth: `research/MINI_RESEARCH_METROLOGY_044_RECEIPT.json`, reconstructed by `src/rakl/mini_research_metrology.py` and checked by `tests/test_round044_frozen_receipt.py`.

## D. Candidate insertion: what "learning" means in RAKL

Suggested location: Discussion, immediately before or inside the senior-researcher analogy.

Ordinary RAKL operation is **external-state learning**, not implicit model-weight training. Raw sources and verified scientific objects remain outside the replaceable language model. The reference flow is

```text
raw evidence
 -> contextual projection
 -> normalization
 -> identity resolution
 -> provenance binding
 -> typed atlas / relation update
 -> rebuildable memory and retrieval views
 -> bounded target-conditioned working context
 -> LLM proposal
 -> external verification
 -> gated canonical update
 -> residual / saturation / method-experience update
```

A contextual scientific projection, a normalization transform, an optional retrieval embedding and a lossy summary are different operators. An embedding may help navigate candidate material but cannot define scientific identity or authority. A lossy view must retain source pins and an erasure ledger; it can reduce active tokens but cannot replace raw evidence required by a strong verification operation. Reusable method experience is also external state and remains proposal-only until transfer/assurance gates are satisfied.

## E. Candidate insertion: practical growth control

Suggested location: Memory/context efficiency or Limitations.

RAKL separates **canonical archive growth** from **active cognitive growth**. A scientifically relevant new source may need to remain addressable in the canonical archive even when it contributes no new active prompt material. The active view is therefore capacity-controlled separately from the archive. Round 044 introduces explicit active caps for atoms, relation witnesses, fibers and observed type-span cells. A fully flat update can be rejected from active growth; an over-capacity active view returns `COMPACT_OR_DEMOTE_ACTIVE_VIEW`, requiring a bounded rematerialization while preserving canonical roots. Prompt capacity remains governed independently by the existing context compiler, which fails closed with `CANNOT_COMPILE` if mandatory epistemic material cannot fit.

A remaining infrastructure limitation should be stated explicitly: the reference implementation now specifies and tests active-state capacity and content-addressable/reconstructable memory semantics, but it is not yet a production cold-tier/object-store implementation with measured physical storage growth. Production archive-byte deduplication and cold-tier benchmarking remain engineering work.

## F. Related-work delta: Obsidian and the broader personal-knowledge-graph neighborhood

Suggested location: Related Work, after `Memory and context efficiency`, under a short heading such as `Knowledge-navigation systems and personal knowledge graphs`.

Obsidian provides a useful interaction analogy rather than a scientific-state equivalent. Its official Graph view represents notes as nodes and internal links as edges, supports a vault-wide graph and an active-note local graph whose depth can be changed, and provides graph filtering/grouping and directional-link display. Its Backlinks view exposes incoming linked and unlinked mentions. These affordances motivate useful RAKL interaction patterns: global-atlas navigation, target-centered local subgraphs, reverse support/provenance navigation and progressive-depth exploration.

The analogy stops at navigation semantics. A note link does not by itself certify shared scientific context, evidence provenance, compatibility, contradiction/refutation, mechanism ancestry, identification authority, an epistemic cut or independent evidence lineage. RAKL should therefore borrow the interaction grammar without treating an untyped note graph as its epistemic semantics.

The missed analogy also broadens the prior-art neighborhood. Personal Knowledge Graph research explicitly studies representation, management and utilization of individually controlled structured knowledge. This adjacent literature should be part of future function-first external-method discovery even when a task is framed as an autonomous-science or LLM-memory problem.

Candidate sources to add to `references.bib` before manuscript integration:

- Obsidian Help. `Graph view`. https://obsidian.md/help/plugins/graph
- Obsidian Help. `Backlinks`. https://obsidian.md/help/backlinks
- Obsidian Help. `Internal links`. https://obsidian.md/help/links
- Skjæveland, M. G.; Balog, K.; Bernard, N.; Łajewska, W.; Linjordet, T. (2023). `An Ecosystem for Personal Knowledge Graphs: A Survey and Research Roadmap`. arXiv:2304.09572.

## G. Candidate insertion: exogenous-concept miss as a saturation falsifier

Suggested location: Challenge Learning / Learning from external frameworks and Limitations/Falsifiers.

A method can falsely appear saturated because its search vocabulary is inherited from its current ontology. RAKL therefore distinguishes in-domain route flatness from **exogenous discovery coverage**. External-framework/novelty search should register multiple route classes: in-domain search, function-first search, adjacent-discipline search, interaction-analogy search and adversarial prior-art search. A later user- or evaluator-supplied concept that overlaps registered target functions but was absent from a completed route ensemble is recorded as an `EXOGENOUS_CONCEPT_MISS`; external-discovery saturation is reopened.

Round 044 provides a concrete diagnostic example. The prior external-framework atlas already contained STORM/Co-STORM with a `knowledge map` facet, yet it did not independently surface Obsidian or the personal-knowledge-management neighborhood. A subsequent name-free, capability-first query family using terms such as local graph, backlinks, notes and knowledge management surfaced Obsidian, another local object graph implementation (Capacities), and the personal-knowledge-graph research literature. The incident is therefore classified as a search-policy/coverage false negative rather than evidence that the knowledge was inaccessible.

This repair remains proposal-level until it succeeds prospectively on fresh unknown concepts. One retrospective recovered example cannot establish general discovery completeness.

## H. Proposed new falsifier

Add to `Limitations and falsifiers`:

**Exogenous-discovery falsifier.** If a later external concept materially overlaps a registered RAKL function yet was not surfaced by a route ensemble that had declared external-framework or novelty saturation, the saturation claim is false for that scope. The missed candidate is preserved as failure memory, the affected discovery route is reopened, and a repair earns method credit only through prospective fresh-concept evaluation rather than by rediscovering the named failure case.

## I. Release-boundary recommendation

Do not replace the paper's bracketed empirical-superiority fields with the Round 044 metrology numbers. These numbers are appropriate for a software/architecture panel demonstrating that the implementation can distinguish expansion, densification and flatness. They are not a substitute for the preregistered matched same-model LLM workflow, self-evolution transfer trial or real spot-science experiment.
