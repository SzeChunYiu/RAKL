# Paper II — ExperienceBenchmark v1.3 (root_cause_v1 / #247)

Status: `PROTOCOL_FROZEN_AWAITING_ORACLE_0_5B` / no empirical result yet

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
