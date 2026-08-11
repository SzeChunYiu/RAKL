# Paper II closest-parent function matrix

Status: `PRIMARY_SOURCE_AUDIT / PROPOSAL_ONLY / NO_ABLATION_RUN / NO_NOVELTY_CLAIM`
Issue: #156 · Date: 2026-08-11

Machine-checked record: [`PAPER2_CLOSEST_PARENT_ABLATION_MATRIX.json`](PAPER2_CLOSEST_PARENT_ABLATION_MATRIX.json),
validated by `rakl.closest_parent_matrix.validate_matrix`.

Detail:
[parent audit](paper2_closest_parent/PARENT_AUDIT.md) ·
[ablation ladder and intervention contracts](paper2_closest_parent/ABLATION_LADDER.md)

No ablation has been executed. Nothing here reports a result.

## The rule this document is built on

A row may claim a surviving residual **only** when the parent it is measured
against was read in primary full text, and only with a falsifier attached.
Conceding a function to prior art is cheap and needs no deep read. Claiming
something survives comparison is expensive and does. Where the closest parent
was read at abstract level, the row says `CANNOT_CHECK` and names the reading
that would resolve it.

This is enforced in code, not by good intentions:
`tests/test_closest_parent_matrix.py` trips every rule against a mutated copy
of the real matrix.

## Verdict

| Claim | Rows |
|---|---|
| `INHERITED_NO_CLAIM` — prior art owns it | 10 |
| `NARROW_RESIDUAL` — survives against a full-text parent | 6 |
| `CANNOT_CHECK` — closest parent not read deeply enough | 6 |
| `PARENT_STRONGER_ADOPT` — the parent is strictly stronger | 1 |

**Paper II may not claim novelty for 17 of 23 functions today.** Ten are
conceded outright, six are unadjudicated, and one — cascade repair — is a
function where RAKL is weaker than MemTX and should adopt rather than compare.

## Matrix

`SF` = same function (y / p = partial / n). Full columns, including
stronger-parent features and discriminators, are in the JSON.

| Function | Closest parent | SF | Claim | Residual, or what blocks it |
|---|---|---|---|---|
| persistent task/project memory | AutoSci | y | inherited | — |
| cross-project long-term knowledge | AutoSci | y | inherited | — |
| TaskEpisode / raw trajectory preservation | MemTX | y | inherited | — |
| versioned lesson/procedure abstraction | AutoSci | y | inherited | — |
| skill / DAG / workflow reuse | AutoSci | y | inherited | — |
| experience-conditioned routing | AutoSci | p | **cannot check** | read SciEvolve + SciMem retrieval |
| transactional commit | MemTX | y | inherited | — |
| provenance retention | PPMF | y | inherited | — |
| source / use permission | PPMF | y | inherited | — |
| staleness / supersession | MemTX | y | inherited | — |
| cascade repair | MemTX | n | **parent stronger** | RAKL has no transitive repair; adopt |
| contradiction preservation | MemTX | p | residual | alignment precedes adjudication; quarantine ≠ live contradiction |
| negative-history preservation | MemTX | p | residual | rollback log is audit, not evidence for later bounds |
| context-scoped scientific claims | MemTX | p | residual | scope is regime/population, not validity interval + share scope |
| prediction vs mechanism authority | PPMF | n | residual | PPMF authority is a source-channel total order, not typed by claim kind |
| mechanism vs identification authority | PPMF | n | residual | no representation of observational equivalence on a trust ladder |
| partial-identification terminal state | MemTX | n | residual | quarantine = pending; partial identification = admitted and bounded |
| proposal-only workspace | MemTX | y | inherited | — |
| experience → authority noninterference | AutoSci | p | **cannot check** | does SciEvolve reach knowledge records or only skills? |
| scientific transition audit | 2604.18805 | p | **cannot check** | read its trace coding scheme; RAKL side unrun |
| open-world discovery routes | AutoSci | p | **cannot check** | read SciFlow's literature stage |
| bounded / freshness-expiring saturation | MemClaw | p | **cannot check** | does any parent expire a *coverage* claim? |
| fresh-assurance self-evolution | AutoSci | p | **cannot check** | does SciEvolve gate on a post-hoc check? |

## The three findings worth carrying into Paper II

### 1. The generic non-amplification principle is prior art

PPMF (arXiv:2607.29167 §4) formalises source-authority non-amplification
exactly:

> auth(q, m) ⪯ min<sub>⪯</sub> { auth(oᵢ) : oᵢ ∈ supp(q) }

for a memory `m = C(O)` derived from observations `O`, over the trust lattice
`Unknown < External < TrustedTool < UserHistory < User_Confirmed < System`,
unless a platform-recorded declassification event applies.

Appendix A restates it as a runtime-monitor proposition with a proof sketch, and
Table 5 enumerates all seven policy stages: memory write, trust transition,
retrieval, risk labeling, authorization, tool taint, conflict handling.

**RAKL may not claim that derivation must not inflate authority.** That is
PPMF's, and Paper I already concedes it in
`sections/01d_transactional_state_nearest_work.tex`. This audit confirms and
sharpens that concession with the exact invariant.

What survives is narrower and is the prediction/mechanism and
mechanism/identification rows above: PPMF's authority is a **total order over
source channels**, and its claim `q` links a memory span to an **action
argument**. Two records identical in source, trust, risk label and validity but
differing in whether the evidence is predictive or mechanistic are
indistinguishable to PPMF by construction. It cannot express that the first
must not license the second, because it has no coordinate for what kind of
support a claim carries.

Every one of PPMF's seven policy stages is keyed on source channel and action
risk class; none references a kind of scientific support. So this is not an
argument from what the method summary happened to omit — it is what the complete
policy table contains.

That is a real residual, and it is much smaller than "RAKL governs provenance".

### 2. RAKL is behind on cascade repair

MemTX verifies cascade-repair completeness (I2) and that no committed or
action-safe record retains a revoked transitive ancestor (G3), over 5,530,160
canonical states, with type-dispatched repair and a rollback audit log. Abort
and revocation share one routine, so the guarantee is path-independent.

A search of `src/rakl` found `revoke` on individual records
(`authority_ledger.py`, `epistemic_noninterference.py`) and no transitive
repair over a derivation DAG, no invalidation propagation, and no `retract`.
This is a gap, not a residual. Paper II should inherit the mechanism and say
so.

### 3. Six rows are unadjudicated, and five of them turn on AutoSci

AutoSci is the closest parent for experience-conditioned routing,
experience→authority noninterference, open-world discovery routes and
fresh-assurance self-evolution, and it was read at abstract level plus repo
inspection only. Its SciEvolve module — feedback to versioned updates — is the
direct counterexample candidate for RAKL's noninterference residual. **If
SciEvolve's versioned updates can reach Long-Term Knowledge Memory records
rather than only skills, templates and memory organisation, that residual
weakens sharply.**

The next session's highest-value read is AutoSci's SciMem and SciEvolve
sections, on the `paper` branch at tag `arxiv-v1`.

## Reconciliation with the current bibliography

Paper I's `01d_transactional_state_nearest_work.tex` already cites MemTX and
PPMF and already disclaims staged belief commit, provenance preservation,
origin-bound and use-specific authority, and structured agent state. Nothing in
this audit contradicts it. Two things should be added:

1. the exact PPMF invariant, so the concession is specific rather than general;
2. the cascade-repair gap, which the current text does not mention.

Paper II's own bibliography has no nearest-work section yet
(`paper/papers/paper-02-rakl-evidence-governed-research/sections/` is empty).
It should inherit Paper I's section and add the six `CANNOT_CHECK` rows as open
work rather than writing novelty language over them.

## Claim boundary

Allowed: this matrix records which functions are conceded, which are
unadjudicated, and which residuals survive against parents read in full text.

Not allowed: any ablation result, any statement that RAKL outperforms any
parent, any novelty claim on a `CANNOT_CHECK` row, and any arm labelled with an
external system's name.
