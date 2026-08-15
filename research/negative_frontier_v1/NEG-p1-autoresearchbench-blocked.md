# `BLOCKED (AutoResearchBench external anchor unexecutable)`

**Paper:** I (overlay branch, via the same receipt as the bounded-saturation null)  
**Class:** `REVIVABLE_EXTERNAL`  
**In current manuscript:** no (successor lineage / receipt-level)  
**Artifact immutable:** no

## Where the manuscript states it

- `publication-overlay-papers-123:publication/papers/paper-01-epistemic-mechanics/sections/06c_current_evidence_update.tex:7 (implicit -- the manuscript reports only the substituted Mathlib anchor; the block is recorded in the receipt)`

## Receipt

- **`receipt_path`:** `research/orion_saturation_solve_enablement_v1/RESULT_V1.md` — **verified present**
- supporting: `research/orion_saturation_solve_enablement_v1/receipts/gate_audit.json`

## What happened

AutoResearchBench (arXiv:2604.25256) was verified to primary depth and upgraded from SEARCH_SNIPPET; title, authors, submission date and the 9.39%/9.31% ceiling were confirmed and the dataset was downloaded and characterised. Execution is nevertheless BLOCKED for two independent reasons: (1) the DeepXiv retrieval endpoint is unpublished (PAPER_SEARCH_API_URL empty in example.env, defaults to ""), so the paper's standard retrieval environment cannot be reproduced; (2) no LLM is available on the sanctioned compute host (no ollama, no vllm, no llama.cpp, 6 GiB GPU, no OpenAI-compatible endpoint). One discrepancy is preserved rather than smoothed: the released bundle contains 3695 wide-research gold papers against 3692 reported in the paper -- recorded FLAGGED.

## One-stage attribution

hardware/environment. Two independent environment blockers; nothing about the mechanic was tested.

## Lever

The substituted Lean/Mathlib anchor is the executed alternative. Reviving the original anchor needs a published retrieval endpoint and an LLM-capable host.

## Class justification

Needs a hosted or locally served LLM and an external retrieval API that is not published.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
