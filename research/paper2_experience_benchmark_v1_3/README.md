# Paper II — ExperienceBenchmark v1.3 (root_cause_v1 / #247)

Status: `TERMINAL_WITH_CAPABILITY_FLOOR_KILL` / `MODEL_CAPABILITY_FLOOR_0_5B` (jobs 3476730 primary / 3476731 race-duplicate; parse-valid; success_rate 0/3). Issue #247 terminal receipt: `ISSUE_247_TERMINAL_RECEIPT.json`.

## Why v1.3 exists

Parent `v1.2` / job **3476548** remains immutable honest-negative history (#138 closed).
It is not promotional lift and must not be reopened for a scale-only clone.

v1.3 is the #247 successor after #238 / PR #299 (`learning_loop_mode=root_cause_v1`):

1. RC1 — failed episodes do not auto-mint reusable Lessons
2. RC2 — selective materialization with retrieval receipts
3. Phase 0 causal arm ladder frozen before model output
4. Phase 1 first job = **0.5B ORACLE** on FRESH_TRANSFER only

## Identity

- `benchmark_id`: `paper2-experience-benchmark-v1_3`
- `protocol_subject_hash`: `ed116353230dc526fa45657d1a81afab26a460fe3b8411480a0f84bb1f711672`
- `learning_loop_mode`: `root_cause_v1`
- model: Qwen2.5-0.5B-Instruct (same staged snapshot as v1.2)

## Forbidden

- scale-only DifferenceWitness on broken v1.2
- ExperienceBenchmark@1.5B before ORACLE 0.5B gate
- reopen #138 / reinterpret 3476548 as lift
- V4.1/V4.2 pendulum score reuse; Paper3/#217 path

## Phase-1 ORACLE result

- Decision: see `ORACLE_DECISION_RECEIPT_V1_3.json`
- Paper-facing note: `PAPER_FACING_NOTE_ORACLE_FLOOR_ISSUE247.md`
- Native landings: `native_job_3476730/`, `native_job_3476731/` (duplicate preserved)
- Staircase/1.5B: **not** authorized from this gate
