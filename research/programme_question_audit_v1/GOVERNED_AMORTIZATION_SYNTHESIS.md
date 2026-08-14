# Governed amortization — synthesis across four formal parents

Status: research-only synthesis, 2026-08-14, base commit `08169241`. Same-context
analysis; not independent review; grants no scientific or promotion authority.

Provenance: operator addendum #2 to the programme question audit ("nearest works
are FOOD, not threats"). Parents compiled as mechanic candidates with primary-source
anchors in `research/external_research_agents/mechanics/formal_parents_amortization_v1.json`
(precedent shape: MEC-DERIVATION_QUANTIFIED_REFUSAL). This file is the synthesis move.

## The four parents, one line each

| Parent | Verified core mechanic | What we eat |
|---|---|---|
| Equality saturation / e-graphs (Tate 2009 via Paper I citation; Willsey et al. POPL 2021, primary-verified) | e-graph "efficiently represents a congruence relation over many expressions"; saturate, then extract under cost | congruence-compact storage; extraction-under-declared-cost |
| Knowledge compilation (Darwiche & Marquis, JAIR 2002, primary-verified) | languages analyzed "according to their succinctness and their polytime transformations and queries" | the tractability CONTRACT: cheapness is always relative to a DECLARED query class |
| Case-based reasoning (Aamodt & Plaza 1994, primary-verified incl. the four REs verbatim) | RETRIEVE–REUSE–REVISE–RETAIN over a case base | thirty years of failure taxonomy for a loop shaped like ours (retrieval bias / adaptation drift / retention pollution — our labels) |
| ITP hammers / lemma libraries (Blanchette et al., JFR 2016, primary-verified) | premise selection: "heuristic and learning methods that select relevant facts from large libraries" | proof that verified amortization works at scale for ONE authority coordinate, and that its bottleneck is retrieval |

## The common invariant

All four parents instantiate one move:

> **Pay a verification or compilation cost once so that a DECLARED class of
> future queries becomes cheap — and safe exactly to the extent the paid cost
> was a verification.**

e-graphs pay congruence closure at insertion so equivalence queries are cheap;
knowledge compilation pays compile time so the declared query set is polytime;
CBR pays solving+retention so similar problems retrieve instead of re-solve;
lemma libraries pay kernel checking so future proofs cite instead of re-derive.
This is the amortization thesis of `docs/REASONING_LOCATION.md` with its
missing precision supplied by parent 2: **the thesis is only well-formed
relative to a declared query class.**

## The proposed synthesis formalism

The structure space as a **congruence-aware, certificate-carrying compiled
knowledge base with declared tractable query classes and obstruction-preserving
semantics**:

- **congruence from e-graphs** — but merging is licensed only by an explicit
  equivalence WITNESS (relabeling bijection / proved equivalence), never by
  surface shape; the congruence contest below makes the difference measurable;
- **the tractability contract from knowledge compilation** — a declared table
  of query classes (signature/JUMP retrieval, role-exact match, derivation
  reachability, cut naming, obstruction lookup) with per-class
  preserved/degraded status under each storage discipline;
- **the failure taxonomy from CBR** — as planted-world designs against our own
  episode/lesson gates;
- **the premise-selection framing from proof assistants** — retrieval under
  authority as the scaling bottleneck, with selection carrying zero authority.

## The novelty delta — checked against each parent, honestly

Claimed delta: authority transport, fail-closed typed refusal, obstruction
preservation. Chewed:

| Delta clause | e-graphs | Knowledge compilation | CBR | ITP libraries | Surviving claim |
|---|---|---|---|---|---|
| Authority transport (multi-coordinate, certified transitions) | absent — all merges equally trusted once added | absent — compiler soundness assumed | absent — no typed authority order | **PARTIALLY PRESENT**: the kernel is a true authority chokepoint for the TRUTH coordinate | delta narrows to MULTI-coordinate authority (truth + specification alignment + novelty + verifier trust) and USE-TIME re-verification (`src/rakl/certificates.py` runs checkers at use; ITP practice trusts the build within a session — a real but modest difference whose COST must be measured, not asserted) |
| Fail-closed typed refusal (CANNOT_CHECK distinct from rejection) | absent | absent — queries return answers | REVISE detects failure but repair is ad hoc, no typed third verdict | hammers time out — a timeout is not a typed refusal | survives, but note the already-absorbed causal-transport parent (sID) occupies refusal-with-certificate; our returned third verdict remains the residual there |
| Obstruction preservation (failures as first-class navigable objects) | failed rewrites leave no record | absent | **PARTIALLY PRESENT**: failure cases can be retained (Aamodt & Plaza p.2, the blow-out mistake reminding) | failed proof attempts not standardly retained | delta narrows to TYPED obstruction objects with navigation semantics (min-cut naming, certified voids), beyond failure-case storage |

Two of three clauses NARROWED under chewing. That is the point of eating:
the honest novelty claim is the CONJUNCTION — no parent combines witnessed
congruence, a declared query-class contract, multi-coordinate use-time
authority, typed refusal, and typed obstruction navigation — and conjunction
claims are weaker than component claims. Whether any system outside these four
parents occupies the conjunction is CANNOT_CHECK pending the nearest-work lane.

## Executable discriminator (frozen separately)

`assimilation/CONGRUENCE_CONTEST_PROTOCOL_V1.json`: atomic storage (shipped
`StructureSpace.accumulate`, which appends every restatement while saturation
reads role-flat) vs surface-congruence merging (the tempting faithful-to-shape
import, predicted to false-merge distinct contents on the real Lean substrate)
vs witnessed-congruence merging with query translation (the governed
adaptation). The term-level FAITHFUL e-graph import is PRECONDITION_BLOCKED on
this substrate: the space carries no rewrite system, so the faithful mechanic
has no input — recorded as a blocked import, not a refuted one.

## Relation to the papers

- Feeds Paper I's reasoning-location frame (`docs/REASONING_LOCATION.md`) with
  its formal ancestry and the query-class precision.
- Feeds Paper VI's per-layer table: the declared query-class contract is what
  a layer's "contribution" is measured AGAINST.
- The containment hypothesis (`docs/CONTAINMENT_HYPOTHESIS.md`) states the
  axiom this machinery serves; equality saturation's saturate-then-extract is
  a shared parent of both.
