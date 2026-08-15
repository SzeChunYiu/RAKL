# `CANNOT_CHECK_MODEL_ASSET_MISSING`

**Paper:** II  
**Class:** `IMMUTABLE_HISTORY`  
**In current manuscript:** yes  
**Artifact immutable:** yes

## Where the manuscript states it

- `publication/papers/paper-02-structural-mechanics/sections/07_natural_domain.tex:16`

## Receipt

- **`receipt_path`:** `research/receipts/PAPER3_STRONG_CONTROL_DESCRIPTOR_ATTEMPT_20260811.json` — **verified present**
- supporting: `src/rakl/paper3_strong_control.py`
- supporting: `experiments/paper3/build_semantic_descriptor.py`

## What happened

An earlier clean-environment attempt to build the label-blind strong semantic control on the pinned revision 953dc6f6f85a1b2d of BAAI/bge-reranker-v2-m3 returned CANNOT_CHECK_MODEL_ASSET_MISSING and is preserved. Label-blind descriptor jobs 3476527-3476529 subsequently reached HARVEST_DESCRIPTOR_READY under the preserved pre-annotation chronology, with training unauthorized throughout.

## One-stage attribution

hardware/environment. The pinned model asset was absent from the clean environment; nothing about the instrument or the science failed.

## Lever

Already discharged by the successful descriptor jobs. Retained as preserved history.

## Class justification

Superseded and preserved; the manuscript reports it only to keep the attempt chronology honest.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
