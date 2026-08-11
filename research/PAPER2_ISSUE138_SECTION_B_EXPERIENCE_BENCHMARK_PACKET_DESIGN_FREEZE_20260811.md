# Issue #138 §B — ExperienceBenchmarkPacket design freeze (RESET vs LEARNING)

Date: 2026-08-11  
Parent subject (design freeze base): `d1f6337c49905729b27314528a02136f7cbc7aa4` (`origin/main` at freeze authoring)  
Authority contracts: `docs/RAKL_V3_EVALUATION.md` §3–§4; `src/rakl/experience_benchmark.py`

## Object and claim boundary

This receipt **freezes the design requirements** for a future `ExperienceBenchmarkPacket` that would measure `RESET_BASELINE` vs `LEARNING_ENABLED` under issue #138 section B.

It is a **research status / design freeze** only.

```text
§B ExperienceBenchmarkPacket design requirements: FROZEN
§B experience compute / runs / scores: NOT STARTED
§B complete: false
ExperienceBenchmarkPacket scores: NOT INVENTED / NOT PRESENT
```

This document does **not**:

- freeze a concrete task set, model revision, resource ceiling values, or state hashes;
- authorize LUNARC/FS9 experience-benchmark compute;
- produce or cite any RESET/LEARNING success rates, mean scores, or deltas;
- reinterpret pendulum V4.1 microtrial results as experience-benchmark evidence;
- close issue #138.

Machine-readable twin: `research/receipts/PAPER2_ISSUE138_SECTION_B_EXPERIENCE_BENCHMARK_PACKET_DESIGN_FREEZE_20260811.json`.

---

## Arms and phases (required)

| Arm | Meaning |
|-----|---------|
| `RESET_BASELINE` | Every development or transfer task starts at registered `S0`; baseline state remains `S0` after the task. |
| `LEARNING_ENABLED` | Development: `S0 --D1--> S1 --…--> Sn`. Fresh transfer: every `Ti` starts independently from the **same frozen `Sn`**. |

| Phase | Meaning |
|-------|---------|
| `DEVELOPMENT_SEQUENCE` | Ordered development tasks; learning arm must form an uninterrupted state chronology. |
| `FRESH_TRANSFER` | Transfer tasks disjoint from development; learning arm must not chain `T1`→`T2` state. |

Canonical validation path: `validate_experience_benchmark(...)` / `assess_experience_benchmark(...)` in `src/rakl/experience_benchmark.py`. Ad-hoc analysis alone is not authority.

---

## Required packet fields (pre-result freeze)

Before any evaluated model outputs are opened, the operator must freeze and bind at least:

### Protocol identity

- `benchmark_id`
- `model`: `MatchedModelConfig` — `model_id`, `model_revision`, `temperature`, `seed`, `system_prompt` (recorded via `system_prompt_hash`), `max_output_tokens`
- `resource_ceiling`: full `TrialResourceCeiling` (`max_model_input_tokens`, `max_model_output_tokens`, `max_preprocessing_model_tokens`, `max_preprocessing_tool_calls`, `max_external_retrieval_calls`, `max_wall_time_ms`) with `max_model_output_tokens` matching the model config
- `tool_policy_id` + `tool_policy_artifact_id`
- `output_schema_id` + `output_schema_artifact_id`
- `evaluator_protocol_hash` + `evaluator_artifact_id` (artifact payload SHA-256 must equal the declared hash)
- `initial_state_hash` (`S0`)
- `development_task_ids` (ordered, non-empty)
- `transfer_task_ids` (non-empty; **disjoint** from development)
- `task_artifact_ids` bindings covering exactly the registered tasks
- strata where the final packet permits: repeated-family, cross-domain-transfer, hostile-near-miss

### Chronology / attestation (before result access)

- `packet_frozen_at` (timezone-aware ISO-8601)
- `freeze_attestation_id` for `AttestationPurpose.BENCHMARK_FREEZE` over `benchmark_protocol_subject_hash(...)`
- protocol artifacts frozen **at or before** `packet_frozen_at`
- `frozen_before_runs = true` must be backed by protected freeze chronology, not a caller Boolean alone
- no evaluated run outputs opened until freeze attestation is issued

### Post-development / run fields (recorded after execution; not inventable here)

- `learned_state_after_development_hash` (`Sn`) — only after LEARNING development completes under the frozen packet
- `runs`: paired `RESET_BASELINE` + `LEARNING_ENABLED` per task, with `state_before_hash` / `state_after_hash`, `success`, `score`, `failure_signature`, `resource_usage`, `output_hash`, `output_artifact_id`, `executed_at`
- `match_attestation_id` for `AttestationPurpose.BENCHMARK_MATCH` over `benchmark_result_subject_hash(...)` issued **after** all runs

Fail-closed conditions include: missing/duplicate tasks, wrong arm count, phase mismatch, resource-ceiling violation, baseline state mutation, learning chronology break, wrong frozen `Sn`, transfer starting from a prior transfer result, incomplete protocol bindings, run-not-after-frozen-packet, duplicate run identity.

---

## Explicit NON-EVIDENCE (must not be reused as §B)

The following artifacts are **not** `ExperienceBenchmarkPacket` evidence for issue #138 §B. Do not feed them to `analyze_v3_experience_benchmark.py` / `plot_v3_experience_benchmark.py` as RESET/LEARNING results. Use `experiments/paper2/refuse_v4_1_as_experience_benchmark.py` as the fail-closed compatibility gate.

| Artifact family | Why excluded |
|-----------------|--------------|
| V4.1 pendulum native jobs **3476520**, **3476521**, **3476524** | Wrong arms (`RAKL_CONTEXT` / `DIRECT`); no frozen `ExperienceBenchmarkPacket`; no RESET/LEARNING development→transfer state chronology |
| Ingest / status for those jobs | Receipt-chain authority for pendulum V4.1 native execution only |
| Sibling STAGING_REFUSED jobs `3476523` / `3476526` | Not experience-benchmark; not to be resubmitted as §B substitutes |
| Any pendulum V4.1 harvest under `research/paper2_microtrial_v4_1/` interpreted as experience scores | Schema/protocol mismatch |

Pointers (ingest status already on main):

- `research/PAPER2_V4_1_NATIVE_JOBS_3476520_3476521_3476524_INGEST_STATUS_20260811.md`
- `research/paper2_microtrial_v4_1/native_job_3476520/`
- `research/paper2_microtrial_v4_1/native_job_3476521/`
- `research/paper2_microtrial_v4_1/native_job_3476524/`
- `research/paper2_microtrial_v4_1/PAPER2_V4_1_NATIVE_JOB_3476520_INGEST_RECEIPT_20260811.json`
- `research/paper2_microtrial_v4_1/PAPER2_V4_1_NATIVE_JOB_3476521_INGEST_RECEIPT_20260811.json`
- `research/paper2_microtrial_v4_1/PAPER2_V4_1_NATIVE_JOB_3476524_INGEST_RECEIPT_20260811.json`

V4.1 scores/verdicts (including `NATIVE_EXECUTION_CHAIN_PASS__ONE_ARM_SCORABLE_NO_EXACT_PASS__COMPARISON_NOT_ESTIMABLE`) remain pendulum-protocol evidence only.

---

## Merged #191 helpers (ready; not §B completion)

Squash-merged on `main` as `eca9697` — PR https://github.com/SzeChunYiu/RAKL/pull/191:

```text
experiments/paper2/analyze_v3_experience_benchmark.py
experiments/paper2/plot_v3_experience_benchmark.py
experiments/paper2/refuse_v4_1_as_experience_benchmark.py
tests/test_paper2_experience_benchmark_helpers.py
```

Helpers enable metrics/figures **after** a real frozen packet + runs exist. They do not mint packet contents, scores, or §B closure.

---

## Gate state

| Gate | State |
|------|-------|
| Design requirements for RESET vs LEARNING packet | **FROZEN** (this receipt) |
| Concrete operator-approved packet (tasks/model/ceiling/S0/artifacts) | **NOT FROZEN** |
| Experience-benchmark compute submitted | **false** |
| Canonical `validate_experience_benchmark` result | **absent** |
| ExperienceBenchmarkPacket scores / deltas | **absent (not invented)** |
| §B complete | **false** |
| Issue #138 closable on §B alone | **false** |

---

## Next operator decision (required before experience compute)

**Decision needed:** approve and freeze a concrete `ExperienceBenchmarkPacket` protocol subject — exact `benchmark_id`, model identity/revision/temperature/seed/system-prompt bytes, full `TrialResourceCeiling`, tool/output/evaluator artifact bindings, `S0`, disjoint ordered development + transfer task sets (with intended strata), and issue a `BENCHMARK_FREEZE` attestation — **before** any evaluated RESET/LEARNING outputs are opened or any experience job is submitted.

Until that decision is recorded with hash-bound artifacts, experience compute remains **BLOCKED**. Do not substitute V4.1 pendulum jobs, synthetic scores, or helper round-trips for that freeze.

After a clean freeze: run canonical validation path; preserve failures/`CANNOT_CHECK`; only then use #191 analyze/plot helpers on those artifacts.

---

## Interpretation invariants

```text
design freeze != packet freeze != executed packet != VALID_MEASUREMENT
V4.1 pendulum != ExperienceBenchmarkPacket
helper merge (#191) != §B complete
positive transfer delta != global capability claim
grants_global_capability_claim remains false
```
