# Paper-facing note — Issue #138 §B ExperienceBenchmark (v1.2 / job 3476548)

## Bound measurement

- Packet: `paper2-experience-benchmark-v1_2`
- `protocol_subject_hash`: `c4ae092b70859d145b7a4b8a7d6485b3d2a552867756fec6783c1e35f7d5f352`
- Job: **3476548** (`p2-exp-v12`), subject `1317aa6…`, COMPLETED 0:0
- Model: `Qwen/Qwen2.5-0.5B-Instruct@7ae55760…` (matched ceiling; CPU transformers)
- Arms: `RESET_BASELINE` vs `LEARNING_ENABLED` with required S0→Sn development and independent fresh transfer from frozen Sn

## Interface lineage (preserved; not promotional)

| Job | Packet | Role |
|---|---|---|
| 3476542 | v1 | Prompt missing verdict enum → illegal `REJECT`/`FAIL` → all schema zeros |
| 3476546 | v1.1 | Enum repaired; CSV/non-JSON residual (especially RESET) confounded deltas |
| **3476548** | **v1.2** | JSON skeleton + enum; **12/12 schema-valid** |

## Honest result (no promotional lift)

Under the frozen v1.2 packet:

- Success rate = **0.0** for both arms on development and fresh transfer
- Development score delta (LEARNING − RESET) = **0.0**
- Fresh-transfer score delta is small and **does not authorize** a capability or method-promotion claim (`grants_global_capability_claim=false`)
- V4.1/V4.2 pendulum jobs remain **non-evidence** for §B
- Paper III confirmatory annotation (#217) was **not** used or simulated

Manuscript language must stay inside this bound: matched experience under 0.5B did **not** produce transfer successes; interface repairs were required before the packet became scientifically interpretable.

## Figures

Reproducible from landed artifacts:

- `native_job_3476548/figures/paper2_v3_experience_benchmark.pdf`
- `native_job_3476548/figures/paper2_v3_fresh_transfer_resources.pdf`
