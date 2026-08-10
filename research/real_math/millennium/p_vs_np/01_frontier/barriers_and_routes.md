# Barrier map and route tournament

This file is a research-control map, not a literature survey. Exact current bibliographic metadata must be refreshed from primary sources before novelty claims.

## Barrier B-REL — relativization

Canonical result family: Baker, Gill, Solovay.

There are oracle worlds in which the relativized P/NP question has opposite answers. Therefore a proof schema that relativizes uniformly cannot settle the unrelativized root question.

**RAKL gate:** for every candidate route, state the step that provably does not relativize. If no such step exists, the route is blocked as a root proof strategy even if its restricted lemmas remain useful.

## Barrier B-NAT — natural proofs

Canonical result family: Razborov, Rudich.

Under strong pseudorandomness assumptions, a circuit-lower-bound method satisfying an appropriate combination of usefulness, largeness, and efficient constructivity cannot prove strong general circuit lower bounds.

**RAKL gate:** any proposed scalable circuit invariant must be audited for these three axes. A candidate that is obviously large and efficiently decidable must explain which natural-proofs premise it escapes before high proof-search budget is spent.

## Barrier B-ALG — algebrization

Canonical result family: Aaronson, Wigderson.

Many arithmetization-based nonrelativizing techniques still survive an algebraic-oracle extension and therefore remain insufficient for P versus NP.

**RAKL gate:** identify the non-algebrizing step for routes that rely primarily on arithmetization, low-degree extensions, or algebraic oracle access.

## Strong restricted-model parents

Several major lower-bound programs already prove strong statements for restricted circuit/proof models. These are parents, not evidence that the general gap is small. The program must identify the exact structural capability absent from the restricted model and avoid silently assuming it away.

### R001 — CLIQUE negation-gap route

Use strong monotone lower bounds for CLIQUE as a parent theorem and isolate what internal negation/cancellation buys general circuits computing a monotone NP-complete predicate.

- advantage: structured target and strong lower-bound ancestry;
- blocker: monotone and nonmonotone complexity can differ drastically for monotone functions, so a generic monotone-lifting lemma is false;
- atomic target: characterize restricted negation patterns for which a provable lifting/lower-bound survives, then widen the pattern class.

### R002 — meta-complexity / MCSP route

Study the minimum-circuit-size problem and hardness-magnification style bridges where modest-looking lower bounds for meta-complexity tasks can imply much stronger consequences.

- advantage: finite truth-table instances admit exact SAT/enumeration checks and generate falsifiable structural conjectures;
- blocker: the key magnified lower bounds remain open and meta-complexity has its own barrier phenomena;
- atomic target: select one exact MCSP variant and formally bind the weakest currently useful lower-bound obligation to its claimed consequence before searching for a proof.

### R003 — circuit-state dual-potential synthesis

Represent exact small circuit construction as a shortest-path problem over states of available truth tables. Search for compressed state potentials whose value increases by at most one per gate and is large on a target.

- advantage: every finite candidate inequality is exactly falsifiable;
- blocker: a scalable output-only potential may collapse into known natural/constructive lower-bound paradigms;
- escape requirement: any serious candidate must be target-specific, state-sensitive, non-large, nonconstructive, or otherwise explicitly outside the natural-proofs premises.

**Current selection:** R003 as discovery engine, with R001 and R002 as structured target families.

## Stable baseline sources to verify/refresh

- Baker, Gill, Solovay, relativization barrier.
- Razborov, Rudich, natural proofs.
- Aaronson, Wigderson, algebrization.
- Razborov and related monotone CLIQUE lower bounds.
- Williams, algorithms-to-circuit-lower-bounds / ACC lower bounds.
- Current primary literature on MCSP, meta-complexity, and hardness magnification.

Until the source-refresh receipt is complete, this map has `FRONTIER_BASELINE` authority only and cannot support a novelty claim.
