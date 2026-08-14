# Paper VI — which external comparison is runnable now (`P6-EXT-COMPARISON-READINESS-V1`)

**Verdict: none at causal grade.** Assessment only. Grants no scientific or promotion authority.
No scalar ranking. Uses external-agent registry v1 as its sole comparison framework; builds no
parallel one.

Registry: `research/external_research_agents/` on branch `research/issue-588-external-agent-registry`
(PR #591), `basis_fingerprint` `a0565504e70eacf6e0b44bb4a7ff2c0d5eacfb88bc533a75e121c7b702c4a946`,
`saturation_status: OPEN`. Facts below are read from it; nothing here imports it, because `main`
does not carry it.

## The four architecture-causal-eligible systems

Registry v1 marks 4 of 9 systems `ARCHITECTURE_CAUSAL_ELIGIBLE`. Every one of them is blocked:

| System | Evidence grade | Reproduction | Runnable as a causal arm now? |
|---|---|---|---|
| `SYS-AI_SCIENTIST_V2` | `SEARCH_SNIPPET` | `NOT_ATTEMPTED` | No |
| `SYS-KARPATHY_AUTORESEARCH` | `SEARCH_SNIPPET` | `NOT_ATTEMPTED` | No |
| `SYS-ASTA_V0` | `SEARCH_SNIPPET` | `NOT_ATTEMPTED` | No |
| `SYS-MINI_SWE_AGENT` | `SEARCH_SNIPPET` | `NOT_ATTEMPTED` | No — and see the second gate below |

## The binding blocker is evidence grade, not adapter work

This is the actionable finding, and it inverts the natural instinct to start writing adapters.

A matched-resource contract must pin model, tool/retrieval stack, budget and evaluator. In registry
v1 those architecture fields read `CANNOT_CHECK` for every eligible system, because the entries rest
on search snippets rather than primary text — issue #588 forbids equating marketing claims with
measured capability, so the fields are honestly empty rather than guessed.

**You cannot specify a matched contract from fields that read `CANNOT_CHECK`.** Adapter scoping is
therefore *downstream* of primary-text reads, not parallel to them. Any adapter written now would
encode guessed architecture, and the resulting arm would confound exactly what the comparator-class
rule exists to prevent. The blocking residual is `RES-EXT-001` (upgrade evidence grades by reading
primary full text), not an engineering backlog.

## A second gate the registry does not pin: task-population compatibility

`comparator_class` answers *can this system's confounders be matched*. It does **not** answer *can
this system attempt the task at all*. These are independent, and eligibility on the first does not
imply the second.

`SYS-MINI_SWE_AGENT` is the concrete case: it is `ARCHITECTURE_CAUSAL_ELIGIBLE`, and registry
`TAXONOMY.md` places it in class **B only** (scientific-execution / code). It cannot enter a
literature-route arm at all — the class-to-benchmark map routes class B to ScienceAgentBench /
PhySciBench / AARRI-Bench, never to AutoResearchBench or DeepResearch Bench. Treating causal
eligibility as arm-readiness would have put it in a literature comparison it cannot attempt.

**Recommendation:** record a `task_population_compatibility` field per system alongside
`comparator_class`, so the two gates are checked separately rather than conflated.

## Same-substrate exclusion still holds

`BM-RESEARCHCLAWBENCH` is the closest external instrument to RAKL's Tier 3 fresh-blind requirement
(target paper hidden at evaluation). Its strongest published agent is **Claude Code, which is ORION's
own harness**. Any ORION result there is a same-substrate comparison and is not an independent
architecture arm, regardless of comparator class. This is not a blocker to be engineered away; it is
a permanent scope label on that instrument.

## `MEC-CONTROLLED_RETRIEVAL_ENVIRONMENT` — assessed, and now quantified

Registry status: highest-value **infrastructure** adoption in v1; `independent_evidence: NONE - not
yet adopted`; transfer obligation says adopt *before* any Tier 1 literature comparison.

The registry argues this qualitatively — a controlled retrieval environment is what makes a
literature-route arm causal rather than confounded by corpus access. The Paper VI scoped-utility
result (`SRSU-P6-GOVERNED-ACCEPTANCE`, PR #596) supplies a second and quantitative reason:

> Under externally anchored evidence-availability rates (arXiv:2608.05179 — 83% of surveyed systems
> release code, 38% release seeds or traces), fail-closed governed acceptance carries a throughput
> tax of **0.897 → 1.000**. With a 12-gate contract, per-gate evidence availability must reach
> **0.9816** for a 20% tax and **0.9913** for a 10% tax.

So a controlled evidence/retrieval environment is not only what makes the *comparison* fair — it is
what gives ORION's own governance layer an **operable regime at all**. Availability is the binding
parameter, and an uncontrolled environment sits two orders of magnitude below the requirement.

That promotes the adoption from methodological preference to **precondition**, with a falsifiable
target: raise per-gate evidence availability above 0.98, or accept that fail-closed promotion is
near-vacuous outside a controlled environment.

**Caveat, stated plainly:** the registry entry for Asta is `SEARCH_SNIPPET` grade. Whether the Asta
Environment actually delivers a controlled corpus with the required properties is `CANNOT_CHECK`
until read at primary depth. The *requirement* is quantified; the *fit of this particular
instrument* to it is not yet evidence.

## Ordered unblock path

1. `RES-EXT-001` — read primary full text for the four eligible systems; fill architecture fields
   from primaries only. **Nothing else can start before this.**
2. Record `task_population_compatibility` per system, separately from `comparator_class`.
3. `RES-EXT-004` — settle the two flagged chronology anchors (`arXiv:2606.07591`, `arXiv:2608.05179`)
   against the publisher record; #588 makes provenance chronology violations a hard invariant.
4. Read the Asta Environment at primary depth and decide `MEC-CONTROLLED_RETRIEVAL_ENVIRONMENT`
   adoption against the 0.98 availability target.
5. Only then scope adapters, and only for systems that pass **both** gates.
6. `RES-EXT-002`/`RES-EXT-003` remain open independently; registry saturation is `OPEN` with **zero**
   flat rounds, so no completeness claim is available in the meantime.

## What must not be promoted from this assessment

- This is a readiness verdict, not a comparison. **No ORION-versus-anything result exists.**
- "No external comparison is runnable at causal grade" is a statement about *our current evidence*,
  not a claim that these systems are weak, unavailable, or worse than ORION.
- The availability requirement (0.9816 for a 20% tax) is derived from the Paper VI **synthetic**
  population under a 12-gate contract. It does not transfer to real research populations without
  a separate study.
