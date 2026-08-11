# Paper II — ExperienceBenchmark protocol freeze (issue #138 §B1)

Status: `PROTOCOL_FROZEN_AWAITING_EXECUTION` / `NO_EMPIRICAL_RESULT`

## What this is

A pre-execution freeze of the canonical RAKL v3 matched experience benchmark:

```text
RESET_BASELINE vs LEARNING_ENABLED
DEVELOPMENT_SEQUENCE then FRESH_TRANSFER
```

Authority contracts: `docs/RAKL_V3_EVALUATION.md`, `src/rakl/experience_benchmark.py`.

This directory freezes protocol bytes **before** any evaluated model outputs for this packet.

## What this is not

- Not §B empirical completion.
- Not a Paper-II manuscript result ingest authorization.
- Not a reinterpretation of pendulum V4.1 microtrials (`3476520` / `3476521` / `3476524`).
  Those arms are `RAKL_CONTEXT` / `DIRECT` and lack the required S0→Sn chronology.
  Model **identity** reuse of the staged `Qwen/Qwen2.5-0.5B-Instruct@7ae55760…` snapshot is allowed; score/arm reuse is not.

## Frozen contents

| Artifact | Role |
|---|---|
| `protocol/MODEL_CONFIG.json` | Matched model identity / decoding |
| `protocol/RESOURCE_CEILING.json` | Shared TrialResourceCeiling |
| `protocol/SYSTEM_PROMPT.txt` | Frozen system prompt |
| `protocol/TOOL_POLICY.json` | No external tools/retrieval in v1 |
| `protocol/OUTPUT_SCHEMA.json` | Structured answer schema |
| `protocol/EVALUATOR_PROTOCOL.json` | Exact structured-match scorer contract |
| `protocol/INITIAL_STATE_S0.json` | Registered empty external RAKL state |
| `tasks/D1.json`–`D3.json` | Development tasks (repeated-family + cross-domain seed) |
| `tasks/T1.json`–`T3.json` | Fresh transfer (repeated / cross-domain / hostile near-miss) |
| `PROTOCOL_FREEZE_PACKET.json` | Protocol packet + `protocol_subject_hash` |
| `PROTOCOL_FREEZE_RECEIPT.json` | Freeze chronology receipt |

`learned_state_after_development_hash` remains `PENDING_AFTER_DEVELOPMENT_NOT_YET_EXECUTED` until LEARNING development finishes and Sn is bound.

## State chronology (required at execution)

### RESET_BASELINE

Every development or transfer task starts at S0 and must remain S0 after the task.

### LEARNING_ENABLED development

```text
S0 --D1--> S1 --D2--> S2 --D3--> Sn
```

### Fresh transfer

```text
RESET:     S0 --T*--> result
LEARNING:  Sn --T*--> result   (each Ti independently from the same frozen Sn)
```

T1 must not teach T2.

## Helper commands

```bash
python experiments/paper2/freeze_experience_benchmark_protocol.py
python experiments/paper2/freeze_experience_benchmark_protocol.py --check-only
```

After real runs exist (not yet):

```bash
python experiments/paper2/analyze_v3_experience_benchmark.py \
  --packet research/paper2_experience_benchmark_v1/PROTOCOL_FREEZE_PACKET.json \
  --runs /path/to/runs.jsonl \
  --out-dir /path/to/analysis

python experiments/paper2/plot_v3_experience_benchmark.py \
  --metrics /path/to/analysis/paper2_v3_metrics.csv \
  --out-dir /path/to/figures
```

Canonical validation remains `validate_experience_benchmark(...)` once Sn and runs are bound under protected freeze/match attestations.

## Next compute step

On LUNARC FS9 Paper-II checkout at exact `origin/main` (path `/projects/hep/fs9/users/scyiu/RAKL-paper2`, **not** Paper-III / #217):

```bash
SHA=$(git -C /projects/hep/fs9/users/scyiu/RAKL-paper2/repo rev-parse refs/remotes/origin/main)
bash experiments/paper2/lunarc/submit_experience_benchmark_v1.sh "$SHA"
# after completion:
bash experiments/paper2/lunarc/harvest_experience_benchmark_v1.sh <job-id>
```

Bindings are frozen in `BATCH_CONTRACT_V1.json` to `protocol_subject_hash`. V4.1 jobs `3476520/3476521/3476524` remain non-evidence.
