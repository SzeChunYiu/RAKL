# The Containment Hypothesis

Status: research-only, proposal-grade, 2026-08-14. Grants no scientific or
promotion authority. Same-context analysis; not independent review.

Provenance: operator axiom, stated 2026-08-14 in geometric form, formalized
here per the operator's four qualifications with receipts. Candidate role:
Paper I's opening axiom (weighed in
`research/programme_question_audit_v1/QUESTION_AUDIT_PAPER_I.json`).

## The axiom (operator's form)

> Information, by decomposition, becomes a structure in a definable space;
> every knowledge is so representable; RAKL's dynamics fill the volume of
> semantic structures until it stops growing; the solution is then likely
> contained within the volume.

## Formalization

Fix a declared source universe `D` and a reduction operator `red`. Decomposition
sends sources to structures in the structure space; accumulation under the
framework's dynamics yields an occupied volume `V_t` (monotone in `t`);
**saturation** is the event that growth is flat under the declared discipline.
The hypothesis: for a problem `P` whose solution admits structural support,

```text
Pr[ support(P) is realizable inside V_sat \ voids(V_sat) ]  is high,
```

where the probability is an EMPIRICAL quantity (see the measurability clause),
never a theorem.

## The four qualifications (each with its receipt)

**Q1 — RELATIVITY.** "Stops growing" is only ever flat RELATIVE to `(red, D)`.
The open-world theorem (`RaklFormal.open_world_not_finitely_certifiable`,
machine-checked in `formal/RaklFormal.lean`) forbids upgrading "likely" to
"certainly": two worlds agreeing on the whole finite transcript can disagree
about undiscovered mechanisms, so no finite saturation certifies completeness.
Reopening on new growth is both machine-checked (`stabilized_is_fixed` gives
the fixed point only for the declared sequence) and behaviourally enforced in
shipped code via `PFC-SATURATION-REOPENS-ON-GROWTH`
(receipt: `research/mechanism_benefit_ledger/ledger.json`,
row `MECH-BOUNDED-SATURATION`).

**Q2 — REPRESENTABILITY is not EXTRACTABILITY.** The axiom asserts the
EXISTENCE of a structural representation, not our ability to compute it from a
given surface form. Extractor capability is empirical, and was measured absent
in one real case: the external-corpus epoch
(`research/paper2_external_corpus_v1/`, terminal
`NEGATIVE__CAPABILITY_ABSENT`) found the registered deterministic reducer
recovers no usable system-level structure from natural narratives. That
boundary instance is cited here as the measured gap between the axiom's
existential claim and any operational pipeline — and is never re-read
positively.

**Q3 — NON-CONVEXITY.** The volume carries certified VOIDS: covers whose
members are pairwise fine and jointly unrealizable, invisible to any pairwise
record (`RaklFormal.no_pairwise_predicate_decides_global_realizability`,
machine-checked; bound to shipped code in `src/rakl/support_solver.py`;
exercised as the mechanized parity family in the L2 gluing arm,
`research/benefit_L2_gluing_v1/`). Containment therefore means "in the volume
MINUS the voids" — a solution path that realizes an obstructed cover is not
contained, however many of its atoms are.

**Q4 — DEMAND-DRIVEN REGROWTH.** When containment fails, failure is an
address, not a verdict: the epistemic cut names the missing region
(`DerivationReport.missing`; `UNDERIVABLE_IN_PRINCIPLE` vs
`AUTHORITY_BLOCKED` in `src/rakl/derivation.py`), and targeted research or
governed invention grows the volume exactly there
(`src/rakl/recursive_solver.py` fibers;
`docs/EPISTEMIC_PATHFINDING_AND_GAP_COMPLETION.md` post-saturation expansion).
The axiom's "likely" is thus self-repairing under a governed loop — which is a
design property, not a probability amplifier.

## Part 2a — Compositional containment (first-class, not a caveat)

For frontier problems the volume contains the **ingredients, not the
solution-object**. The solve is a novel composition: a derivation DAG that
never existed, over hyperedges that all did. Receipt: the end-to-end real
solve (`tests/test_end_to_end_real_problem.py`) re-derives a named theorem as
an extracted DAG — a NEW object — whose every edge is a pre-existing
kernel-checked dependency.

**Combinatorial amplification.** `N` stored structures span a composition
space exponential in `N`; the space's value is its **span, not its
inventory**. Counting stored structures therefore undercounts the volume in
exactly the way that matters for frontier work.

**Scatter mechanisms.** The ingredients of one solve are scattered across
regions: the backward corridor over the multi-premise support relations
(`docs/FORMAL_SYSTEM_SPECIFICATION.md` section 8's `H_t`, traversed backward
from the target per `docs/EPISTEMIC_PATHFINDING_AND_GAP_COMPLETION.md`)
collects them by demand, and shape-signature analogy retrieval
(`src/rakl/analogy_retrieval.py`) reaches pieces hidden in FOREIGN
vocabularies — zero shared roles, same relation shape.

**Why obstruction preservation is MOST load-bearing here.** Distant-region
recombination is precisely where pairwise-plausible, jointly-unrealizable
gluings occur — the machine-checked identifiability result
(`RaklFormal.no_pairwise_predicate_decides_global_realizability`) says no
pairwise record can catch them. A composition engine without certified voids
does not merely miss solutions; it manufactures false ones, and the risk
GROWS with the reach of retrieval.

## Part 2b — Governed extension (first-class, not a caveat)

When a bridge is absent from the span, **invention proposes what no source
contained** — strictly AFTER research saturation and decomposition exhaustion.
Receipts: `src/rakl/recursive_solver.py` ("When research saturates AND
decomposition is exhausted ... the LIFT rule already enforced in
`semantic_shortcut`: invention requires at least two distinct failed attempts
first"), and the invented candidate "enters the space only at **authority
floor 0** and only with obligations" (same module, machine-tested).

**The domain-strength claim, stated precisely.** Frontier mathematics is the
framework's strongest domain BECAUSE invention's obligations are
kernel-dischargeable: a proposed bridge lemma's verification obligation is a
typecheck, which is a fully mechanical authority — no LLM judge anywhere in
the discharge path. The frontier cycle:

```text
cut names the missing bridge (DerivationReport.missing)
-> invention proposes at floor 0 with obligations
-> kernel verifies (certificate; discharge is mechanical)
-> volume grows exactly at the hole
-> derivation completes
```

The creative slot (who proposes) stays pluggable — human, LLM, enumerator;
the framework's guarantee is only, and exactly, that **nothing invented
becomes load-bearing silently**.

## Part 3 — The loop is scale-invariant (short, prospective)

(a) **Solver dynamics** are a local mutation loop over candidate structures
(receipts: the Paper IV allocation row in
`research/mechanism_benefit_ledger/ledger.json` — including its honest
refutation — and `src/rakl/epistemic_trajectory.py`; the specific
STALE-trajectory receipt is CANNOT_CHECK in this pass and not asserted).

(b) **Self-interaction**: the solver applied to itself as object — the global
loop's structural pass over its own trajectories, the falsifiability battery
auditing its own gates
(`research/paper3_gate_falsifiability_audit_v1/`), the framework built by its
own loop. Named hazard: self-interaction is where evaluator-Goodhart lives —
the dead-gate receipts (`src/rakl/certificates.py` docstring;
`research/paper6_scoped_utility_v1/`) are its record, and governance is
load-bearing here, not decorative.

(c) **Higher levels**: a cluster of solvers = each solver's
(space, trajectories, receipts) as a `ReducedStructure` in a higher-level
space, with the SAME loop run over it; cluster-of-clusters is the functor
again. Pre-existing quarantined sketch:
`docs/design/orion_mechanics_multiscale_plan/03_RECURSIVE_MULTISCALE_ORION.md`
(promote-from-quarantine pattern as with pathfinding; note for issue #627).

Honest boundaries, all first-class: clusters pay only via
**reduction-operator diversity** (complementary volumes, cross-checked
obstructions); **cluster agreement is not independence** (same-context
correlation — the constitution's caveat one level up); and **every level owes
the ladder a benefit obligation**. Registered falsifier (designed, NOT
executed): a two-solver diverse-reducer cluster vs one solver at matched TOTAL
budget. Part 3 inflates no paper's claims — it is architecture plus one
falsifier, prospective.

## Measurability clause (the axiom's falsifier)

The containment probability is exactly what the benefit experiments estimate:
a traversal arm's solve rate on known-answer corpora is the realized frequency
with which saturated volumes contain the planted solutions
(`research/mechanism_benefit_ledger/ledger.json`; running arms
`research/benefit_L0_fcr_v1`, `benefit_L1_composition_v1`,
`benefit_L2_gluing_v1`, and successors). FALSIFIER: if saturated volumes
systematically fail to contain solutions that Q4-regrowth then finds cheaply,
the measured "likely" is low at the declared `(red, D)` and the axiom is
useless there — a first-class negative, not a paradox.

## What "volume" means today

Today: role-coverage cardinality over the declared basis
(`StructureSpace.accumulate` measures growth in newly seen roles;
`src/rakl/structure_space.py`). This is a counting measure on a discrete
basis. With a validated graded metric on the structure space it becomes a
genuine measure with distances — that is the open-problem study
(`research/programme_question_audit_v1/metric_open_problem/PROTOCOL_METRIC_V1.json`;
Stage A executed `NEGATIVE_AT_FROZEN_GATE`; Stage B external validation
reducer-blocked). Until then, every "volume" statement is a cardinality
statement.

## Nearest work (assimilation-first; honest marks)

Primary verification status: equality saturation verified in this pass
(`research/external_research_agents/mechanics/formal_parents_amortization_v1.json`);
the other three below are from-training sketches, CANNOT_CHECK verbatim until
the nearest-work lane verifies primaries.

- **Version spaces** (Mitchell): candidate elimination maintains a
  boundary-represented set guaranteed to contain the target concept —
  containment-by-construction over a HYPOTHESIS space. Delta: our volume grows
  from evidence decomposition, not hypothesis elimination; no authority
  typing; no voids.
- **PAC learning** (Valiant): "likely approximately contained" after
  polynomially many samples — the statistical ancestor of the axiom's "likely".
  Honest gap it exposes: a PAC-style bound requires a DECLARED problem
  distribution, which this programme has not declared; without one the
  containment probability is per-corpus empirical, never a bound.
- **Closure operators / FCA** (Ganter & Wille): saturation as a closure
  fixpoint — the shape already mechanized in `formal/RaklFormal.lean`
  (`iter_below_prefixed`, `stabilized_is_fixed`, `iInter_closed`).
- **Equality saturation** (verified): saturate-then-extract = fill the volume,
  then select under cost — the operational parent of the dynamics half.

Common invariant across parents: grow a representable set to a fixpoint, then
answer by membership/extraction, with guarantee quality tied to the growth
discipline. **Our delta, post-chewing:** authority-typed growth, certified
voids as first-class negative volume, demand-driven regrowth at named
addresses, and typed refusal when the query leaves the declared universe.
Whether the CONJUNCTION is unoccupied elsewhere is CANNOT_CHECK pending the
nearest-work lane.

**Part 2 parents** (compiled as mechanic candidates in
`research/external_research_agents/mechanics/formal_parents_invention_v1.json`;
verification marks there): hammers/premise selection (automated composition
over lemma spaces — primary-verified in the amortization packet), conjecturing
systems (Lenat's AM, Fajtlowicz's Graffiti, recent neural conjecturing —
CANNOT_CHECK verbatim this pass), Polya's heuristics (the classical
decomposition/analogy parent — CANNOT_CHECK verbatim), and MCTS-style proof
search (AlphaProof-class — published details only; unpublished internals are
CANNOT_CHECK and are not guessed). Part-2 delta candidates: governed invention
floor + obstruction-preserving composition + authority transport across the
composition.

## What must not be claimed

- No completeness: Q1 caps every containment statement at the declared basis.
- No extraction promise: Q2's measured boundary stands until a capable
  admitted reducer exists.
- No convex-volume intuition: Q3's voids are certified, not hypothetical.
- No probability without measurement: the "likely" is an estimand of the
  benefit arms, not an assumption; quoting the axiom without its falsifier is
  quoting a slogan.
- Part 2a licenses no combinatorial optimism: span is exponential, but so is
  the search; the corridor and retrieval disciplines are what make span
  usable, and their cost is measured, not waived.
- Part 2b licenses no autonomous-mathematician claim: kernel-dischargeability
  governs the ADMISSION of invented bridges, not the quality or rate of
  proposals; the creative slot's capability remains an empirical, currently
  unmeasured quantity.
