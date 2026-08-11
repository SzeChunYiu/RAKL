# RAKL Metrology

**Status:** canonical measurement contract associated with Paper 5.  
**Authority:** measurement-only. These metrics never mint theorem, tool, review, gluing, or framework-promotion authority.

## Measurement questions

RAKL separates four questions that must not be collapsed:

1. **State growth:** what retained semantic structure entered the persistent system?
2. **Process quality:** did individual RAKL method surfaces perform their intended role?
3. **Learning effect:** did accumulated experience change later behaviour usefully?
4. **Causal assistance:** did RAKL improve outcomes relative to the same underlying model without the relevant RAKL intervention?

Raw files, commits, prose, issues, tokens, and node counts are inventory, not learning.

## Seven-axis retained-growth vector

Use the same coordinates as v3 saturation:

`KNOWLEDGE / OPERATOR / EXPERIENCE_PATTERN / OBSTRUCTION / RELATION / PATH / META_METHOD`.

For cycle `t`, report

`g_t = (ΔK, ΔO, ΔE, ΔB, ΔR, ΔP, ΔM)`

where every delta counts only retained semantic novelty after identity, deduplication, lineage, and supersession accounting. Also report raw inventory separately: episodes, lessons by authority, tools by kind/authority, failure diagnoses, variants, nodes/edges and unresolved links.

## Experience-to-method funnel

Track episodes -> diagnoses/lessons -> validated lessons -> tools/motifs -> successful fresh reuse. Report at minimum:

- episode outcome profile and cost;
- candidate/reusable/superseded lesson counts;
- lesson proposal and validation yield;
- new tools per 100 consequential episodes;
- successful and failed reuse per tool;
- applicability-block and target-validation rates;
- diagnosis maturity and latency;
- repeated structural failure rate;
- obstruction resolution rate.

Repeated-failure reduction is useful only when invalid-transfer and false-lesson rates do not increase.

## Process telemetry

Every consequential invocation of a canonical `method_specs.py` surface should emit a measurement record containing: invocation/process identity, task/episode identity, input state/fibre hashes, output identity, outcome, registered cost policy and usage, residual-before/after, seven-axis retained novelty, retrieved/selected/rejected IDs, verification/evidence pointers, and timestamp.

Applicable process families include decomposition, routing, retrieval/query generation, source selection, claim extraction, normalization, context translation, equivalence/transfer, gluing, contradiction diagnosis, gap discovery, discriminator selection, synthesis, memory, review, benchmarking, promotion, saturation, context compilation, capability shaping, execution, portfolio allocation, objective evolution and generator transport.

Process-specific metrics include retrieval precision/recall inside a bound universe, missed-relevant-memory rate, saturated-route retry rate, route-switch latency, source-scope mismatch, false semantic merge, transfer false-positive rate, hostile-near-miss rejection, local-success/global-gluing-failure rate, contradiction-diagnosis revision, decisive discriminator rate, overclaim/retraction rate, context overflow, exact-subject CI binding, false saturation and rollback.

## Residual contraction

For hard open problems, final success is sparse. Preserve typed blocker transformations rather than pretending one scalar captures progress. Report resolved, newly exposed, unchanged, reopened, blocked and unknown residual coordinates. If a scalar count is used, it is subordinate to semantic identity so blocker renaming cannot manufacture progress.

## Causal attribution

The prospective Paper 5 benchmark uses four arms under matched model, tool, task, evaluator and resource contracts:

- `MODEL_ONLY`: same base model and allowed tools, no RAKL workflow/state.
- `RAKL_RESET`: static RAKL architecture, reset to the same initial state for each task.
- `RAKL_SHAM_MEMORY`: same architecture and matched memory/context budget, but target-relevant learned memory is replaced by preregistered irrelevant or structurally mismatched controls.
- `RAKL_LEARNING`: persistent development experience, then one frozen learned state used independently for every fresh-transfer task.

For outcome metric `m`:

- architecture lift = `m(RAKL_RESET) - m(MODEL_ONLY)`;
- experience lift = `m(RAKL_LEARNING) - m(RAKL_RESET)`;
- learned-content lift = `m(RAKL_LEARNING) - m(RAKL_SHAM_MEMORY)`;
- total RAKL lift = `m(RAKL_LEARNING) - m(MODEL_ONLY)`.

Paired task categories must report `BOTH_SUCCESS`, `RAKL_ONLY_SUCCESS`, `BASELINE_ONLY_SUCCESS`, and `BOTH_FAIL` symmetrically. Baseline-only success is evidence of RAKL interference, not an inconvenient outlier.

## Resource and safety effects

Measure tokens, retrieval/tool calls, wall time, candidate/branch count and time to decisive falsifier. Separately measure false-progress, invalid-transfer, false-global-gluing, chronology/provenance violation, source-scope error and authority-escalation rates. Soft performance gains cannot compensate for a blocking integrity failure.

## Fresh-transfer isolation

After development, every fresh-transfer run must start from the same frozen learned-state identity. Transfer T1 may not teach T2. The sham policy, evaluator protocol, task set/order or sampling rule, primary meta-QoIs, effect thresholds, multiplicity policy, resource ceiling and stopping rule are frozen before confirmatory execution. Exposure of an assurance packet to the optimizer converts it to development evidence.

## Internal versus externally audited novelty

Seven-axis novelty counts are internal metrology until a separately frozen sample is independently audited for semantic novelty, duplication, false collapse, axis assignment and lineage. The system is not allowed to validate its own semantic-growth precision merely by re-reading its own classifications.

## Version meaning

A `3.0.x` change may be an implementation repair. A future `3.1`, `3.2`, and so on is reserved for a materially different Class-B method/workflow challenger with preregistered meta-QoIs and matched/fresh evidence. Version-number progression is therefore not a synonym for code growth.
