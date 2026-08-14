# Anchor verification — issue #588 "Initial external evidence anchors"

Issue #588 says: *"verify/update before freezing"* and *"Re-search these before execution because the
field is moving quickly."* This file is that check, run 2026-08-14.

**Evidence grades.** `PRIMARY_ABSTRACT` = the arXiv abstract page was fetched and read.
`SEARCH_SNIPPET` = the claim comes from search-result summaries only and may **not** be cited as a
measured capability. Only three of the anchors below reach primary depth in v1.

## Confirmed

| Anchor | Primary identifier | Verified content | Grade |
|---|---|---|---|
| AutoResearchBench | arXiv:2604.25256 | Deep Research + Wide Research split; **1000 problems, 8 CS areas**; strongest LLMs reach **9.39% accuracy / 9.31% IoU**, many baselines below 5%; pipeline released | SEARCH_SNIPPET |
| DeepResearch Bench | arXiv:2506.11763; ICLR 2026 poster 10008065 | 100 PhD-level tasks (50 zh / 50 en), 22 fields; RACE + FACT evaluation | SEARCH_SNIPPET |
| AstaBench | arXiv:2510.21652 | **2400+ problems across 11 benchmarks, 4 categories**; 57 agents / 22 architectural classes; best open-weight **11.1%**, Asta v0 **53.0%**; cost-aware leaderboard | SEARCH_SNIPPET |
| PhySciBench / DelveAgent | arXiv:2606.18648 | 200 questions, physics+chemistry, 6 categories; Gemini Deep Research ceiling **33.5%**; DelveAgent **+7.5pp at ~1/3 cost** | SEARCH_SNIPPET |
| Verification survey | arXiv:2608.05179 | Screened 125 works, included 35, analysed 26 (24 runnable + 2 position). **83% release code; 38% release seeds/traces; 38% report novelty verification; no L4 system has an externally validated in-loop oracle** | PRIMARY_ABSTRACT |
| Real-world failure evidence | arXiv:2607.27191 | Six days + thousands of dollars of compute on two unpublished NeurIPS 2026 papers; engineering completed, research questions not advanced; both rejected by original authors | PRIMARY_ABSTRACT |

The issue's paraphrases were accurate wherever they were checkable. The figures added above were
absent from the issue text and are new.

## Corrections

**1. ScienceAgentBench is dated wrongly.** The issue lists it as *"verified update Apr 2026"*. Its
primary anchor is **arXiv:2410.05080, ICLR'25** — 102 tasks from 44 peer-reviewed publications across
four disciplines, validated by nine subject-matter experts; best agent solves **32.4%** independently
and **34.3%** with expert-provided knowledge; self-debug raises solve rate at **>10× cost**. Recorded
with `date_consistency: FLAGGED`. This matters because #588 Phase 0 requires recording the exact
evaluated version and date, and a 2026 date would misrepresent the suite's vintage.

**2. The issue's anchor list is incomplete.** It is described as not frozen, and the pass confirmed
that: **ResearchClawBench** (arXiv:2606.07591), **AARRI-Bench** (arXiv:2606.07462), **HAL**
(arXiv:2510.11977) and **AgentAtlas** (arXiv:2605.20530) were all missed, along with class-D systems
Mimosa, EvoScientist, AutoScientists and Agon. ResearchClawBench and HAL are load-bearing for Phases 3
and 4 respectively — see `README.md`.

## Chronology flags

Two anchors show a gap between the arXiv identifier's encoded period and the reported submission date:

- **arXiv:2606.07591** (ResearchClawBench) — reported v1 **2026-05-28**, revised v5 2026-07-03.
- **arXiv:2608.05179** (verification survey) — reported submission **2026-06-29**.

Both are preserved as `FLAGGED` rather than silently resolved. Issue #588 makes *provenance chronology
violations = 0* a hard invariant, so these must be settled against the publisher record before the
version freeze supports any Tier 1 comparison (`RES-EXT-004`).

## Unverified

`SYS-INTERNAGENT` currently rests on a third-party mirror (alphaxiv) rather than the arXiv record, and
its reported gains across 12 tasks are recorded as `CANNOT_CHECK` for exact figures. Its own novelty
comparison uses AI Scientist-v2 as the baseline — a self-selected comparator, not independent
evaluation.

## Standing caution: self-paired releases

DelveAgent/PhySciBench and Asta v0/AstaBench are each a system and a benchmark released by the same
authors. Their reported gains are self-paired and require independent replication before being treated
as measured. The same caution applies to any future ORION-plus-ORION-benchmark result — which is
exactly why #588 mandates Tier 3 fresh blind tasks.
