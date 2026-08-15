# `FAIL_CLOSED_MISSING_INDEPENDENT_ANNOTATION`

**Paper:** II  
**Class:** `IMMUTABLE_HISTORY`  
**In current manuscript:** yes  
**Artifact immutable:** yes

## Where the manuscript states it

- `publication/papers/paper-02-structural-mechanics/sections/07_natural_domain.tex:12`

## Receipt

- **`receipt_path`:** `research/receipts/PAPER3_CHEAP_GATE_RESULT_20260810.json` — **verified present**
- supporting: `research/receipts/PAPER3_V2_GATE_PREPARATION_20260810.json`
- supporting: `research/PAPER3_CHEAP_GATE_SATURATION_20260810.md`
- supporting: `src/rakl/paper3_cheap_gate.py`

## What happened

44 constructed proposal pairs across 11 mechanism families, frozen at Git subject f2701f732f83. The deterministic pilot crossed its frozen incremental-signal thresholds (LOFO ROC-AUC 0.914 -> 1.000; AP 0.903 -> 1.000 over the strongest frozen lexical/tag control), but the independent-annotation gate has authority over the signal gate: zero of 44 items confirmatory-eligible, no training or inference run launched. A subsequent chronology audit found labels were visible during construction, so the v1 set is PERMANENTLY an internal constructed diagnostic.

## One-stage attribution

licence/abstention. The independent-annotation gate outranks the signal gate, and the chronology audit imposed the stricter cut.

## Lever

None for this artifact -- 'later annotations cannot retroactively convert it, and the receipt is retained unchanged as negative history' (07:12). The live successor is the v2.1 label-blind lane and open issue #359.

## Class justification

The manuscript states the artifact is permanently non-confirmatory and can never be reclassified. The research question continues live elsewhere (see NEG-p2-power-limited-packet and NEG-p2-independent-humans-absent).

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
