# Paper II closest-parent function matrix

Status: `PRIMARY_SOURCE_AUDIT_V2 / FULL_TEXT_PARENTS_ADDED / NO_CONFIRMATORY_ABLATION / NO_NOVELTY_FROM_NONCONFIRMATORY_EMPIRICS`
Issue: #156 (design/empirics terminal) · Literature deepening 2026-08-12

Machine-checked record: [`PAPER2_CLOSEST_PARENT_ABLATION_MATRIX.json`](PAPER2_CLOSEST_PARENT_ABLATION_MATRIX.json),
validated by `rakl.closest_parent_matrix.validate_matrix`.

Detail:
[parent audit](paper2_closest_parent/PARENT_AUDIT.md) ·
[ablation ladder and intervention contracts](paper2_closest_parent/ABLATION_LADDER.md) ·
[V2 audit receipt](paper2_closest_parent/PRIMARY_SOURCE_AUDIT_V2_RECEIPT.json)

No confirmatory ablation has been executed under `CAPABLE_MODEL_AVAILABLE=NO_REFUTED`.
Non-confirmatory A3↔A4 scores (job 3476749) are cited below as instrument history only.

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

## Verdict (V2)

| Claim | Rows |
|---|---|
| `INHERITED_NO_CLAIM` — prior art owns it | 12 |
| `NARROW_RESIDUAL` — survives against a full-text parent | 10 |
| `PARENT_STRONGER_ADOPT` — the parent is strictly stronger | 1 |
| `CANNOT_CHECK` — closest parent not read deeply enough | 0 |

**Paper II may not claim novelty for 13 of 23 functions today** (12 inherited +
cascade-repair adopt). Ten narrowed residuals survive full-text parents; none of
them is persistent memory, transactional commit, provenance, permissions,
workflow orchestration, skill reuse, generic self-improvement, or shared-memory
governance.

V2 closed the six prior `CANNOT_CHECK` rows by reading AutoSci, MemClaw and the
AI-scientists coding sections in primary text.

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
| experience-conditioned routing | AutoSci | y | inherited | SciFlow tailored views + SciDAG past-execution templates (V2) |
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
| experience → authority noninterference | AutoSci | p | residual | typed authority axes; AutoSci may rewrite knowledge/org/skills without G/R/M/I/D non-escalation (V2) |
| scientific transition audit | 2604.18805 | p | residual | epistemic-operation graphs ≠ authority-axis transition labels (V2) |
| open-world discovery routes | AutoSci | y | inherited | Literature `/discover` `/novelty` harness skills (V2) |
| bounded / freshness-expiring saturation | MemClaw | p | residual | per-record supersession ≠ coverage certificate (V2) |
| fresh-assurance self-evolution | AutoSci | p | residual | SciEvolve "stable enough" ≠ post-challenger held-out assurance (V2) |

## Critical empirical novelty test: A3 vs A4

The decisive *empirical* novelty contrast remains:

```text
A3 TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED
  vs
A4 SCIENTIFIC_AUTHORITY_TYPING
```

under matched panel/resources, co-reporting ALR and valid-upgrade recall.

| Status | Detail |
|---|---|
| Confirmatory | `CANNOT_IDENTIFY` while `CAPABLE_MODEL_AVAILABLE=NO_REFUTED` (V2_EXEC job 3476813; 2/5) |
| Non-confirmatory harvest | job **3476749** · `SCORED_ARM_RESPONSES_NON_CONFIRMATORY` |
| A3 | ALR≈0.154 · valid-upgrade recall=**0** · false-conservative refusal≈0.063 |
| A4 | ALR=**0** · valid-upgrade recall=**0** · false-conservative refusal=**0.625** |

Honest reading: A4's ALR=0 coincides with upgrade-recall=0 and high
false-conservative refusal — **conservatism, not typed-authority superiority**.
A3 also has upgrade-recall=0. **No A4>A3 novelty claim is licensed.**

## The three findings worth carrying into Paper II

### 1. The generic non-amplification principle is prior art

PPMF (arXiv:2607.29167 §4) formalises source-authority non-amplification.
**RAKL may not claim that derivation must not inflate authority.** What survives
is claim-kind typing: prediction vs mechanism and mechanism vs identification.

### 2. RAKL is behind on cascade repair

MemTX verifies cascade-repair completeness. This remains a gap to adopt, not a
residual.

### 3. AutoSci/MemClaw full text narrows — and preserves — specific residuals

AutoSci owns experience-conditioned routing and registered literature discovery
routes. SciEvolve and Active→Long-Term consolidation can rewrite knowledge
organization and long-term entity content, so RAKL cannot claim "experience
never updates knowledge." The surviving noninterference residual is **typed
scientific-authority coordinates**. Fresh-assurance gating and coverage-level
saturation also survive; generic self-improvement and per-record supersession do
not.

## Claim boundary

Allowed: which functions are conceded, which residuals survive full-text
parents, and honest citation of non-confirmatory A3↔A4 scores.

Not allowed: any confirmatory ablation result, any statement that RAKL
outperforms any named parent, any novelty claim on inherited rows, and any arm
labelled with an external system's name.
