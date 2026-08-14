# Paper II novelty threat ranking — 2026 audit

Date: 2026-08-14. Same-context analysis, not independent review.

## RED — dissolves the claim as currently worded

**Causal transportability (Bareinboim & Pearl, 2011–2016).**

The abstract's residual is "a directional, evidence-bearing transport contract
that binds QoI, source preconditions, role/relation mapping, preserved
invariants, forbidden losses, target boundaries and uncertainty, evaluated for
fail-closed transfer decisions."

Conjunct-by-conjunct against the `sID` signature and completeness results:

| conjunct | transportability | status |
| --- | --- | --- |
| directional | Π → Π\*, asymmetric by construction | **occupied** |
| binds QoI | `Px*(y)` is an explicit formal argument | **occupied** |
| source preconditions | `I`, `P*` — which distributions must be available | **occupied** |
| preserved invariants | absence of an S-node *is* declared mechanism invariance | **occupied** |
| target boundaries | the selection diagram `D` demarcates what differs | **occupied** |
| evidence-bearing | returns a transport formula naming exactly which datasets to fuse | **occupied** |
| fail-closed | `FAIL(F, F')` + Corollary 3 → failure is a **proof of impossibility** | **occupied, and strictly stronger** |
| not analogy similarity | do-calculus derivation, zero similarity scoring | **occupied** |
| uncertainty at target | partial transportability yields bounds (NeurIPS 2024) | largely occupied |

Pearl & Bareinboim (2014) even use the word: transportability is *"a licence to
transfer causal effects learned in experimental studies to a new population."*

Any causal-inference reviewer will read the current sentence as the transport
formula with different nouns. Worse, transportability's guarantee is *stronger*
than fail-closed: completeness turns refusal into a certificate of impossibility,
whereas the Paper II gate merely declines.

## AMBER — occupies one conjunct each; must be cited and distinguished

**Structure-Mapping Theory / SME / MAC-FAC (Gentner; Falkenhainer, Forbus &
Gentner; Forbus, Gentner & Law).** Owns the role/relation-mapping conjunct
outright, with a 40-year computational ancestry, and systematicity is a
principled invariant-selection rule. Differs in output: SME produces ranked
candidate mappings, not a licence. The claim may not present role mapping as
novel.

**Selective prediction / learning-to-defer / conformal under shift (Cortes,
DeSalvo & Mohri; Geifman & El-Yaniv; Madras, Pitassi & Zemel; Wang & Qiao).**
Owns the abstain channel. Wang & Qiao mounts abstention directly on a transfer
setting with target-domain coverage guarantees. Differs in trigger: abstention
is threshold-triggered on a scalar confidence signal, not structure-triggered by
unverifiable declared preconditions.

**SKILL.nb (El Hattami, Chapados & Pal, `arXiv:2606.08049`).** Nearest live
contemporary in reusable-experience governance: evidence-calibrated lifecycle
policies, gate-conditioned execution, fallback on drift. Same problem statement
and same fail-closed instinct. Differs: binary runtime step validation, no
declared QoI, no role mapping, no forbidden-loss enumeration, no third verdict.
A reviewer who knows this paper will raise it; it needs its own paragraph.

**Leake, Kinley & Wilson (AAAI-97).** The CBR ancestor of precondition-bound
reuse — replaces semantic similarity with estimated *adaptability* as the
retrieval criterion. Differs: real-valued estimate feeding ranked retrieval, no
directional contract, no abstention.

## GREEN — not threats

All eight analogy/transfer works named in #487 verified and none occupies the
niche: they measure whether transfer *succeeds*, or rank candidate analogies by
similarity. None issues a per-transfer licence. GraphARC and Portable Agent
Memory are costumes. AbstentionBench abstains on answerability, not on transfer.

Note: the operator listed ARN as TACL 2026; the primary record is **TACL 12,
2024**. Corrected in `CLAIM_MATRIX.md`.

## What actually survives

Four residuals, and only these should be claimed:

1. **The returned third verdict.** Transportability is complete *conditional on
   a fully specified selection diagram*; it has no way to return "I cannot
   evaluate this". PNAS 2016 p. 7351 pushes the missing-knowledge case outside
   the formalism as a user obligation, verbatim: *"If knowledge about
   commonalities and disparities is not available, transport across domains
   cannot, of course, be justified."* A contract that **returns**
   `CANNOT_CHECK` when its own preconditions are unverifiable is outside the
   formalism.

2. **Cross-vocabulary role/relation mapping under a licence.** Transportability
   presumes shared variable identity — the selection diagram overlays two causal
   diagrams over the *same* variable set. SMT/SME does mapping but not
   licensing. **Nobody does both.** The contract must *establish* the
   correspondence transportability assumes for free, then license across it.
   This is the strongest residual.

3. **Applicability without a causal graph, over non-causal research artifacts.**
   `D` is a hard input to `sID`, and its QoI is a probabilistic causal quantity.
   Reusable research experience is neither.

4. **Explicit forbidden-loss enumeration.** No counterpart found in any of the
   five searched families.

## Required manuscript action

Cite Bareinboim & Pearl as the **acknowledged parent**, not as related work, and
narrow the residual to (1)–(4). Claiming directionality, QoI binding, source
preconditions, invariants, target boundaries, evidence-bearing and fail-closed
as residual will not survive review — every one is in the `sID` signature.
