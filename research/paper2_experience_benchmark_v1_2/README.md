# Paper II — ExperienceBenchmark v1.2 (JSON-skeleton prompt repair)

Status: `EXECUTED_NEGATIVE_NO_SUCCESS_LIFT` / job **3476548**

## Why v1.2 exists

- **v1 / job 3476542**: missing verdict enum → illegal `REJECT`/`FAIL` → all schema_violation zeros.
- **v1.1 / job 3476546**: enum repaired; model often emits legal tokens but **CSV-like** non-JSON (`CONTEXT_MISALIGNED, [], [E1],`), especially on RESET. LEARNING sometimes returns valid JSON (state JSON primes format) and partial scores. Apparent RESET≪LEARNING gap is confounded by parse failures — not promotional experience lift.

v1.2 adds an explicit JSON-object-only skeleton without changing evaluator/tasks/model.

## Identity

- `benchmark_id`: `paper2-experience-benchmark-v1_2`
- `protocol_subject_hash`: `c4ae092b70859d145b7a4b8a7d6485b3d2a552867756fec6783c1e35f7d5f352`

## Forbidden

- V4.1/V4.2 pendulum score reuse; Paper3/#217; promotional lift claims before validated non-confounded runs.
