# Governance tradeoff v1 — governed vs ungoverned recursive solver improvement

Executes `PROTOCOL.json` (frozen pre-outcome): the same 14-proposal allocator mutation
stream through (a) the registered ungoverned comparator `MEC-GREEDY_ACCEPT_ON_HELD_OUT_SCALAR`
(accept iff a held-out development scalar improves; no gates, no admissibility, no
CANNOT_CHECK) and (b) the governed pipeline (admissibility gate → licensed instrument →
frozen screening + assurance gates). Truth meter: licensed-instrument evaluation at a
disjoint seed, experimenter-level. No scalar verdict; the result is a frontier.

## Frontier (from `TRADEOFF_RECEIPT.json`)

| axis | UNGOVERNED_GREEDY | GOVERNED |
|---|---|---|
| environment | reference instrument (formally INADMISSIBLE — the arm has no mechanic to know) | reference REFUSED (CANNOT_CHECK); licensed v2 |
| development gain (own instrument) | +0.0025 (final incumbent `M05_SCALAR_DEFICIT_BLOCK`) | +0.0781 (promoted `M09_MG_NOFLOOR`) |
| fresh-assurance (truth) gain of final incumbent | +0.0756 | +0.0781 |
| dev-vs-truth agreement | **30× understatement** (0.0025 vs 0.0756) | agreement to 4 decimals |
| accepted / promoted | 1 of 14 | 1 of 14 (11 passed screen; best assured once) |
| false promotions (frozen def.) | 0 | 0 |
| honest-terminal rate | 0.0 (no refusal semantics exist) | 1.0 (14/14 reference comparisons refused with receipt) |
| evaluator integrity at end state | acceptance signal content-dependent on the one acceptance (0 content-inert, 0 noise) | gates FALSIFIABLE (2/2 probes SENSITIVE, 16/16 flips) |
| budget (eval-units) | 14 | 19 (incl. 4 declared qualification units) |

## Frozen predictions — three of five FALSIFIED, preserved

- **TP1 FALSIFIED**: the greedy arm recorded *zero* false promotions.
- **TP2 FALSIFIED**: the greedy arm did not win raw acceptance throughput (1 vs 1).
- **TP3 FALSIFIED**: its single acceptance was neither noise-driven nor content-inert.
- TP4 HELD: governed promoted exactly one candidate, zero false promotions.
- TP5 HELD (honest counter-prior): the greedy final incumbent transfers positively (+0.0756).

## The measured shape of the ungoverned cost (post-hoc description, labeled as such)

In this environment the ungoverned failure mode is **not** false promotion — it is
**silent starvation and verdict inversion**. On the inadmissible instrument every
marginal-gain proposal measured ≈ −0.001 and was rejected; 10 of the 13 rejected
proposals clear the 0.05 screening gate on the licensed instrument (`M01`, `M02`,
`M06`–`M11`, `M13`, `M14`). The greedy loop discarded the entire winning mechanism
family, kept a candidate whose measured value understates its true value 30-fold, and
emitted zero honest terminals — it structurally cannot report that its instrument is
broken. The false-promotion failure mode presumably needs a noisier or looser
environment to manifest; that regime was not exercised here and no claim is made
about it.

## What governance measurably bought and cost here

Bought: instrument qualification (the whole reason the licensed comparison exists),
dev/truth agreement, refusal semantics on 14/14 broken comparisons, falsifiable
end-state gates. Cost: +5 eval-units (~36%) and a slower acceptance cadence; plus, on
a separate external surface, the STALE receipt's −0.217 ON−OFF contrast (PR #673) is
carried on the frontier as a measured cost cell with its abstention-scoring caveat
(`../paper3_stale_revival_v1/`).

Scope: model-free development stress; one proposal family; one environment. Grants no
scientific authority.
