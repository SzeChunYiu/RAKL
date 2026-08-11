# Paper II — ExperienceBenchmark v1.1 (verdict-enum prompt repair)

Status: `PROTOCOL_FROZEN_AWAITING_EXECUTION` / `NO_EMPIRICAL_RESULT`

## Why v1.1 exists

Job **3476542** executed the full v1 RESET/LEARNING chronology (S0→Sn + independent fresh transfer) under `protocol_subject_hash=1248dd10…`. All 12 scores were 0.0 with `schema_violation`.

Root cause (not a scorer chronology bug; not incomplete S0→Sn):

- System/user prompts named the JSON keys but **did not enumerate** the allowed `verdict` tokens.
- Qwen2.5-0.5B-Instruct emitted illegal tokens `REJECT` / `FAIL` (and one run with spaced keys) instead of `SUPPORT|REFUTE|CONTEXT_MISALIGNED|CANNOT_CHECK`.
- Evaluator correctly fail-closed; deltas were therefore uninformative for experience lift.

v1 artifacts and job 3476542 remain preserved negative history. Evaluator/task sealed answers are unchanged. This packet only repairs the **prompt interface**, analogous to V4.2 field-polarity repair.

## Frozen identity

- `benchmark_id`: `paper2-experience-benchmark-v1_1`
- `protocol_subject_hash`: `c7b1a04007e237f54acd2d0efd1c90870ad20718dec9392216ce49b169f7bedb`
- Parent v1 job: `3476542` (NON-promotional; interface defect)

## Forbidden

- Reuse V4.1/V4.2 pendulum scores (`3476520/21/24`, `3476540`) as §B evidence
- Paper3 / #217 path
- Mutating the v1 evaluator after outcomes under the same packet id
- Claiming promotional experience lift before v1.1 harvest + analysis

## Submit (FS9 Paper-II only)

```bash
SHA=$(git -C /projects/hep/fs9/users/scyiu/RAKL-paper2/repo rev-parse refs/remotes/origin/main)
bash experiments/paper2/lunarc/submit_experience_benchmark_v1_1.sh "$SHA"
bash experiments/paper2/lunarc/harvest_experience_benchmark_v1_1.sh <job-id>
```
