# Capability qualification V3 (issue #447)

Shared capability qualification for Paper II (#443) and Paper V (#446). Deliberately
separate from RAKL treatment experiments so model and interface selection cannot depend on
whether RAKL wins.

## Status

| Stage | Artifact | State |
| --- | --- | --- |
| 0 gold + instrument audit | `GOLD_AUDIT.json` | complete — `INSTRUMENT_DEFECT_EVIDENCE_ROLE_UNDEFINED` |
| 1 diagnostic decomposition | `BOTTLENECK_RECEIPT.json`, `DIAGNOSTIC_RESULTS/` | complete — `BENCHMARK_CONSTRUCT_DEFECT` |
| 2 interface challenger | `INTERFACE_CHALLENGER_SPEC.json`, `protocol_stage2/`, `STAGE2_INTERFACE_CHALLENGER_RECEIPT.json` | complete — `STAGED_INTERFACE_DEVELOPMENT_PROMISING` |
| 3 model candidate freeze | — | not yet frozen |
| 4 fresh qualification panel | — | not yet frozen |
| 5 qualification decision | — | blocked on 3–4 |

`CAPABLE_MODEL_AUTHORIZE_RECEIPT_V3` does **not** exist. Every capability-dependent
Paper II/V treatment experiment remains blocked. Stage 2 is development-only: it
repairs the undefined evidence-role surface under a **new versioned challenger
identity** and does not rescore sealed job 3476813 or mutate
`paper2-oracle-capability-gate-v2-exec`.

## What Stage 1 found

Diagnosed from preserved development data only: the sealed 7B generation of job 3476813
(`Qwen/Qwen2.5-7B-Instruct`, revision `a09a3545`, `transformers-4.55.0/torch-2.8.0+cpu`).

1. **Structured readout is not the bottleneck.** Parse validity 5/5.
2. **The gold is sound.** All five sealed partitions are total and disjoint over the
   supplied evidence ids, and all five use one convention: *selected = the evidence that
   licenses the verdict*. T1 rules out the competing "selected = relevant evidence"
   reading, because it places an on-topic mass reading (51.20 kg, drifted out of
   tolerance) in `rejected`.
3. **The instruction surface never states that convention.** Both surfaces the job
   rendered — `protocol/SYSTEM_PROMPT.txt` and the static instruction block in
   `paper2_experience_benchmark_runner.build_user_prompt` — specify key names, the verdict
   enum and the JSON skeleton, and define no role semantics for
   `selected_evidence_ids`/`rejected_evidence_ids`. Seven distinct role-language patterns
   were swept across both surfaces; none matched.
4. **Two generations reproduced the gold partition exactly with the labels swapped.** On
   T2 and T3 the model's selected set equals the gold rejected set and vice versa,
   set-for-set.

Consequently the measurement cannot separate two hypotheses on T2/T3: that the model
cannot bind evidence, or that it answered under the other admissible reading of an
undefined field. That is an identifiability defect in the instrument.

## What Stage 1 does **not** claim

- **No rescore.** `MODEL_CAPABILITY_FLOOR_7B_V2_EXEC` stands byte-for-byte. No
  convention-corrected score for job 3476813 is computed anywhere in this directory, and
  `rakl.paper2_capability_v3_diagnostic` has no code path that produces one.
- **No gate change.** No threshold is lowered, and the frozen exact-success gate is
  untouched. The per-stage verdict accuracy reported in the receipt is a Stage 1
  diagnostic metric and is explicitly *not* comparable to that gate, which requires
  verdict AND support recall AND reject recall jointly.
- **No authorization.** Stage 1 runs on development items and cannot authorize capability.
- **No exoneration of the model.** T4 is a real composition failure: gold `REFUTE` on two
  same-QoI readings that numerically conflict (850 vs 420 W/m²), model `CANNOT_CHECK`.
  That error is convention-invariant and survives any repair to the interface.

## Why this is diagnosed from the instrument, not the outcome

Declaring `BENCHMARK_CONSTRUCT_DEFECT` after an unfavourable result can look like voiding
an inconvenient negative. It is not, and the code enforces the distinction:
`audit_instruction_semantics` accepts prompt text only. It is never passed scores,
generations or sealed answers, so its verdict is a property of the instrument that would
read identically had the model passed.

Issue #447 Stage 0 requires this audit *before* model evaluation. It was not run for
`paper2-oracle-capability-gate-v2-exec`. Discovering the defect afterwards is precisely
why the terminal is "capability unidentified at this instrument, repair under a new
version" rather than any claim about what a 7B model can do.

## Reproduce

```bash
python experiments/paper2/freeze_capability_v3_stage1_diagnostic.py
python -m pytest tests/test_paper2_capability_v3_diagnostic.py
```

The freeze script asserts its emitted constants against the bound schema's const locks
before writing anything.
