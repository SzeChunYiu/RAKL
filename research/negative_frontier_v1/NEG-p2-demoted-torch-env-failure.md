# `preserved negative history -- first demoted train/inference pair failed on a missing torch environment`

**Paper:** II  
**Class:** `IMMUTABLE_HISTORY`  
**In current manuscript:** yes  
**Artifact immutable:** yes

## Where the manuscript states it

- `publication/papers/paper-02-structural-mechanics/sections/07_natural_domain.tex:18`

## Receipt

- **`receipt_path`:** `research/paper3_independent_human_residual_v1/ISSUE_332_TERMINAL_RECEIPT.json` — **verified present**

## What happened

Jobs 3476750 (training) and 3476751 (inference) failed on a missing torch environment and remain negative history. After hardening, jobs 3476753/3476754 passed under DEMOTED_AI_OPERATOR authority.

## One-stage attribution

hardware/environment. Missing torch runtime on the execution host.

## Lever

Already discharged -- the hardened rerun succeeded. Retained only as preserved history.

## Class justification

Superseded by a successful hardened rerun; retained as preserved negative history and not to be relabelled.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
