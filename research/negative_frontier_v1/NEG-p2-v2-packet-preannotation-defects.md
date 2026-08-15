# `two preserved pre-annotation defects: near_miss identifier leakage; forced cannot_assess=false schema`

**Paper:** II  
**Class:** `IMMUTABLE_HISTORY`  
**In current manuscript:** yes  
**Artifact immutable:** yes

## Where the manuscript states it

- `publication/papers/paper-02-structural-mechanics/sections/07_natural_domain.tex:14`

## Receipt

- **`receipt_path`:** `research/receipts/PAPER3_V2_SOURCE_ID_REPAIR_20260810.json` — **verified present**
- supporting: `research/receipts/PAPER3_V2_1_ANNOTATION_PACKET_INTERNAL_REVIEW_20260810.json`
- supporting: `research/paper3/annotation/README_V2_1.md`

## What happened

A pre-annotation identifier-leakage audit found four curator-only source identifiers containing the phrase near_miss; that source set was preserved as negative history and replaced by an otherwise byte-equivalent v2.1 set with neutral identifiers. Separately, a hostile usability check found the response schemas forced cannot_assess=false against the frozen rubric; the repaired schemas permit abstention only as a fully null judgement, with the compiler preserving such submissions while failing confirmatory import.

## One-stage attribution

instrument-construct (both). Leakage of an answer-correlated token into curator-visible identifiers; and a response schema that made the registered abstention option unreachable.

## Lever

Both already repaired into the v2.1 packet, which is the frozen 16-item set now carrying CONFIRMATORY_PACKET_POWER_LIMITED.

## Class justification

Preserved defect history of a superseded packet version; the repair is already shipped.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
