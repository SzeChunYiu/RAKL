# Where the reasoning lives

Status: research-only articulation, 2026-08-14. Grants no scientific or
promotion authority. Same-context analysis; not independent review.

Provenance: operator addendum to the programme question audit
(`research/programme_question_audit_v1/`). This document states WHERE reasoning
is located in the framework, what that claim predicts, and which experiments
falsify it. It introduces no new mechanism.

## The claim

The framework does not perform less reasoning than an unstructured agent; it
**relocates** reasoning to three sites, each with different authority rules.

### Site 1 — compiled into the space (reasoning-at-rest)

A hyperedge is a frozen inference step. The structure space is reasoning that
has already been performed, verified, and stored; traversal is cheap because
the reasoning is pre-paid. Shipped code states this exactly:

> "once the space holds verified inference steps, deriving a target is forward
> closure over hyperedges — no reasoning engine in the loop, only traversal."
> (`src/rakl/derivation.py`, module docstring)

The compiled step carries a certificate that is re-verified **at use time**
(`src/rakl/certificates.py`) — custody is continuous, not trust-at-compile-time.

**Falsifiable projection (the amortization thesis).** "Saturation = enough
compiled reasoning that solving becomes traversal" is an empirical claim, and
it is exactly what the benefit experiments test: if the mechanism arms of the
ladder (`research/benefit_L0_fcr_v1`, `benefit_L1_composition_v1`,
`benefit_L2_gluing_v1`, and successors) fail to beat naive arms on known-answer
corpora, the compiled-reasoning claim loses its payoff column. Cost accounting
for the compile/retrieve/verify split is the non-hidden `CostBreakdown` of
`src/rakl/amortization.py`. The ladder receipts to date (L0–L2 typed PROMOTE,
mechanical arms, synthetic corpora) are evidence at that scope and no further.

### Site 2 — governed interfaces (reasoning-at-the-boundary)

Where new structure enters the space, reasoning is **governed but not
mechanized**: the framework mechanizes the *justification obligations*, not the
discovery.

- reduction: `admit_reducer` (`src/rakl/reduction_validation.py`) demands
  scramble-sensitivity, obstruction harvest and label-author independence
  before any reducer's output may enter;
- decomposition/composition: gluing and bridge licensing demand explicit
  interface agreement before local results compose;
- invention: `LIFT` emits a `MissingTransformationSpecification` — a typed
  statement of what a not-yet-existing inference must preserve, break, expose
  and reduce — rather than performing the invention.

The generator (human or LLM) reasons; the interface decides whether that
reasoning's PRODUCT is admissible. No interface mints authority.

### Site 3 — failure analysis (reasoning-about-absence)

When traversal fails, the framework mechanically locates **where** new
reasoning is required without performing it: `DerivationReport.missing` names
the absent lemma; `UNDERIVABLE_IN_PRINCIPLE` vs `AUTHORITY_BLOCKED` are typed,
different findings; an obstructed cover names the exact conflicting subset.
The epistemic cut is a located address, not a vibe. Residual-driven reopening
(workflow step Q) then routes new reasoning to that address.

## What this articulation is not

- **Not elimination.** The reasoning compiled into the space was performed
  somewhere — by the Lean kernel, by authors, by governed generators. The
  framework claims custody and location, never creation ex nihilo.
- **Not a performance claim.** Whether relocation PAYS is the benefit ledger's
  open column (`research/mechanism_benefit_ledger/ledger.json`), settled by
  matched-ablation experiments only.
- **Not novelty by default.** See nearest work below.

## Nearest work (assimilated, not merely cited)

Upgraded 2026-08-14 per operator addendum #2: the four formal parents are
compiled as mechanic candidates with primary-source anchors in
`research/external_research_agents/mechanics/formal_parents_amortization_v1.json`,
and synthesized in
`research/programme_question_audit_v1/GOVERNED_AMORTIZATION_SYNTHESIS.md`
(common invariant: governed amortization — pay a verification/compilation cost
once so a DECLARED query class becomes cheap and safe).

- **Equality saturation / e-graphs** (Willsey et al. POPL 2021,
  primary-verified; Tate 2009 via Paper I's own citation): congruence-compact
  saturation + extraction — the operational parent of Site 1.
- **Knowledge compilation** (Darwiche & Marquis, JAIR 2002,
  primary-verified): the tractability contract — cheapness is only ever
  relative to a declared query class; this is the precision Site 1's
  amortization thesis was missing.
- **Case-based reasoning** (Aamodt & Plaza 1994, primary-verified incl. the
  RETRIEVE–REUSE–REVISE–RETAIN cycle verbatim): the failure taxonomy for a
  loop shaped like ours.
- **Proof-assistant lemma libraries / hammers** (Blanchette et al., JFR 2016,
  primary-verified): verified amortization at scale for the truth coordinate;
  premise selection is our retrieval problem with a literature.

The novelty-delta table (each delta clause chewed against each parent, two of
three clauses NARROWED) is in the synthesis file; the conjunction claim's
field occupancy remains CANNOT_CHECK pending the nearest-work lane.

**The delta this framework claims** (and must defend at nearest-work grade):
compiled steps carry *use-time-re-verified certificates* and typed authority
(not compile-time trust); interfaces are *fail-closed with typed refusal*
(`CANNOT_CHECK` distinct from rejection); obstructions are *preserved as
first-class objects* rather than discarded on failure; and authority transport
across the space is governed (representation never mints mechanism or
identification authority). Whether any prior system occupies this conjunction
is CANNOT_CHECK pending the nearest-work lane.

## Consequences for the papers

- **Paper I**: the discipline's hypotheses are the type system of compiled
  reasoning; the hypothesis-necessity audit
  (`research/programme_question_audit_v1/QUESTION_AUDIT_PAPER_I.json`) asks
  which compiled obligations are load-bearing.
- **Paper VI**: the ladder's per-layer benefit table is the amortization
  thesis tested layer by layer; the capstone's "working engine" claim, when it
  becomes available, is a claim that relocation pays at engine scale.
- **Representation tournaments**
  (`research/programme_question_audit_v1/REPRESENTATION_TOURNAMENT_PROTOCOL_V1.json`)
  ask whether the CURRENT compiled form is the right container, under bounded
  contests only.
