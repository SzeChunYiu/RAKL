# Empirical execution handoff — Papers II, III, and V

This is the machine-execution handoff for a future AI session running on the workstation/LUNARC environment. It complements GitHub issue #138.

**Do not invent missing measurements.** Preserve `CANNOT_CHECK` / `CANNOT_MEASURE`, failed runs, invalid packets, negative transfer, baseline-only wins, and unusable annotations as evidence. A successful software run is not automatically a scientific result.

## 0. Global startup contract

Before doing any experimental work:

1. Read `AGENTS.md`, `ARCHITECTURE.md`, `docs/RAKL_V3_EVALUATION.md`, and the current paper manuscripts.
2. `git fetch --all --prune` and record the exact `origin/main` SHA and working-tree status.
3. Never execute an evaluated packet from a dirty checkout.
4. Record the exact model ID/revision/interface, tool versions, resource contract, task/evidence cutoff, evaluator hash, state hashes, timestamps, scheduler/job IDs, and raw output hashes.
5. Freeze protocol/task/evaluator/sham/randomization choices **before** opening evaluated outcomes.
6. Do not mutate a protected evaluator after seeing results and then reuse the same packet as confirmatory.
7. Do not delete failed or superseded runs. Supersede by lineage.
8. Keep Paper I and Paper IV out of the compute queue unless their claims are deliberately expanded; their current core claims are formal/assurance claims rather than efficacy claims.

Paper V is currently developed on draft PR #127 (`paper5-experience-governed-evolution-20260811`). The helper scripts below live on that branch until separately reviewed/integrated. Synchronize the challenger with then-current `main` before any final evaluated packet, but do **not** merge Paper V merely to run an experiment.

---

## 1. Paper III first — structural witness versus strong semantic control

Scientific bottleneck: show whether the directional structural witness adds transfer-validity information beyond a strong modern content model, using genuinely independent annotation.

### 1.1 Native BGE descriptor lane

The existing native LUNARC lane is already implemented on `main`:

```bash
cd /projects/hep/fs9/users/scyiu/RAKL-paper3/repo
git fetch origin
# checkout the exact clean merged subject intended by the frozen contract
SHA=$(git rev-parse HEAD)
test -z "$(git status --porcelain --untracked-files=all)"

JOB_STAGE=$(bash experiments/paper3/lunarc/submit_semantic_model_stage.sh "$SHA")
echo "$JOB_STAGE"
```

After the allocation finishes:

```bash
bash experiments/paper3/lunarc/harvest_semantic_descriptor.sh model-stage "$JOB_STAGE"
```

Obtain a fresh, payload-free zero-label chronology observation while no external response labels are visible. Then submit the descriptor job:

```bash
JOB_DESC=$(bash experiments/paper3/lunarc/submit_semantic_descriptor.sh \
  "$SHA" \
  "$JOB_STAGE" \
  /absolute/path/to/current-zero-label-observation.json)
echo "$JOB_DESC"
```

After descriptor completion, create the required post-descriptor zero-label observation or first-label cutoff and harvest:

```bash
bash experiments/paper3/lunarc/harvest_semantic_descriptor.sh \
  descriptor "$JOB_DESC" \
  /absolute/path/to/post-descriptor-label-chronology.json
```

Do not substitute Jaccard or another model if the exact frozen BGE asset cannot be staged. Preserve a typed failure instead.

### 1.2 Independent annotation

Use the immutable v2.1 solicitation instructions in:

```text
research/paper3/annotation/README_V2_1.md
```

The confirmatory packet needs all of the following:

- two distinct human/domain-expert annotators completing all 16 items independently;
- a distinct adjudicator who begins only after both submissions are frozen;
- a distinct external provenance auditor for identity/expertise/conflict/chronology checks;
- exact packet/schema/hash bindings;
- no label/result exposure before the BGE descriptor chronology cutoff.

Do not count same-session AI roles as independent annotation.

### 1.3 Confirmatory gate and Paper III plots

Once annotation import/adjudication/provenance passes, run the frozen confirmatory evaluator in `src/rakl/paper3_confirmatory_gate.py`. The gate must compare witnessed structure to the strongest admissible non-structural control and must remain fail-closed if annotation or support requirements are incomplete.

Generate plots from the resulting receipt with:

```bash
python experiments/paper3/plot_confirmatory_metrics.py \
  --receipt /path/to/confirmatory-gate-result.json \
  --out-dir /path/to/paper3-figures
```

Expected outputs:

```text
paper3_confirmatory_signal.pdf
paper3_confirmatory_calibration.pdf   # when Brier/log-loss are present
```

Report at minimum:

```text
ROC-AUC
average precision
Brier loss
log loss when available
Q2 true-accept rate
Q3 false-accept rate
strongest-control identity
all gate failures / CANNOT_CHECK states
```

Only if this gate passes should expensive downstream training/inference be considered. If it fails, the negative result is the Paper III result and must not be tuned away post hoc.

---

## 2. Paper II — matched v3 persistent-experience benchmark

Scientific question: with the same underlying model and matched resource ceiling, does persistent external RAKL experience improve later fresh tasks relative to resetting RAKL state?

Use `docs/RAKL_V3_EVALUATION.md` and `src/rakl/experience_benchmark.py` as the authority contract.

### 2.1 Freeze a packet

Freeze before execution:

```text
benchmark ID
exact model ID/revision/temperature/seed/system prompt hash
max output tokens and full resource ceiling
tool-policy identity
output-schema identity
evaluator protocol hash
initial state hash
development task order
fresh-transfer task IDs
all task/evaluator artifact hashes
packet freeze timestamp/attestation where required
```

Use at least these three task strata where feasible:

```text
repeated-family
cross-domain transfer
hostile near-miss
```

Development and transfer task IDs must be disjoint.

### 2.2 Execution invariant

`RESET_BASELINE`:

```text
every task starts at S0
every task ends with registered state S0 unchanged
```

`LEARNING_ENABLED` development:

```text
S0 -> D1 -> S1 -> D2 -> ... -> Sn
```

Fresh transfer:

```text
Sn -> T1
Sn -> T2
Sn -> T3
...
```

Every transfer task independently starts from the same frozen `Sn`. `T1` must never teach `T2`.

Write one JSONL record per arm/task containing the fields expected by:

```text
experiments/paper2/analyze_v3_experience_benchmark.py
```

Then run:

```bash
python experiments/paper2/analyze_v3_experience_benchmark.py \
  --packet /path/to/paper2-v3-packet.json \
  --runs /path/to/paper2-v3-runs.jsonl \
  --out-dir /path/to/paper2-v3-analysis

python experiments/paper2/plot_v3_experience_benchmark.py \
  --metrics /path/to/paper2-v3-analysis/paper2_v3_metrics.csv \
  --out-dir /path/to/paper2-v3-figures
```

Expected figures:

```text
paper2_v3_experience_benchmark.pdf
paper2_v3_fresh_transfer_resources.pdf
```

Report:

```text
development/fresh-transfer success rate
mean registered score
repeated-failure rate
model input/output tokens
preprocessing-model tokens
tool calls
retrieval calls
wall time
development success/score delta
fresh-transfer success/score delta
fresh-transfer repeat-failure delta
```

A positive delta is scoped benchmark evidence only. Do not infer a universal continual-learning or global capability claim.

If the final Paper V task packet is exactly compatible, Paper II may reuse the `RAKL_RESET` and `RAKL_LEARNING` fresh-transfer executions rather than spend twice. Reuse requires exact matching of task, model, resource, evaluator, state and run identities; otherwise run Paper II separately.

---

## 3. Paper V — longitudinal metrology + four-arm causal attribution

Paper V's prospective core is the four-arm attribution study plus independent retained-novelty audit. Do not replace either with retrospective anecdotes.

Read first:

```text
experiments/paper5/ATTRIBUTION_PREREGISTRATION_V1.md
experiments/paper5/ATTRIBUTION_TASK_ELIGIBILITY_V1.md
experiments/paper5/NOVELTY_AUDIT_PROTOCOL_V1.md
docs/RAKL_METROLOGY.md
publication/papers/paper-05-experience-governed-evolution/FIGURE_PLAN.md
```

### 3.1 Final task packet

Target first complete confirmatory packet:

```text
120 task units total
40 REPEATED_FAMILY
40 CROSS_DOMAIN_TRANSFER
40 HOSTILE_NEAR_MISS
3 repetitions per task-arm if the frozen budget permits
4 arms
```

Full target at three repetitions is 120 x 4 x 3 = **1,440 model invocations**, before development-state construction and independent annotation work.

Do not use unsolved Millennium root problems as ordinary binary success labels. RAKL_math local atoms are eligible only when their evaluator/ground truth is independently frozen and checkable.

Freeze exact task IDs/payload hashes, evaluator/parser/threshold, model/tool/resource contract, source cutoff, initial/reset state, learned post-development state, sham state, and sham-policy construction **before outcomes**.

### 3.2 Generate execution order before outcomes

Prepare a task JSON such as:

```json
{
  "packet_id": "paper5-attribution-v1-final",
  "tasks": [
    {"task_id": "T001", "stratum": "REPEATED_FAMILY"},
    {"task_id": "T041", "stratum": "CROSS_DOMAIN_TRANSFER"},
    {"task_id": "T081", "stratum": "HOSTILE_NEAR_MISS"}
  ]
}
```

The final file must contain all 120 tasks; the abbreviated example above is illustrative structure only.

Generate and freeze the block-randomized schedule:

```bash
python experiments/paper5/build_attribution_schedule.py \
  --tasks /path/to/final-tasks.json \
  --out /path/to/frozen-schedule.json \
  --seed <FROZEN_RANDOMIZATION_SEED> \
  --repetitions 3
```

Commit/hash the schedule before evaluated output access.

### 3.3 Four execution arms

For every scheduled run use the same underlying model/evaluator/resource ceiling:

```text
MODEL_ONLY
  model + allowed external tool classes, no RAKL workflow/state

RAKL_RESET
  RAKL architecture, identical frozen S0 on every evaluation task, no mutation

RAKL_SHAM_MEMORY
  same RAKL workflow and matched memory/context/object budget;
  relevant learned objects replaced by frozen structurally incompatible controls

RAKL_LEARNING
  same RAKL workflow using one state frozen after development;
  every evaluation task independently starts from that same learned-state hash
```

The sham construction algorithm/seed must be frozen and audited for answer leakage and accidental true structural matches.

### 3.4 Missing executor adapter — implement before outcomes

The repository already has metrology, scheduling, analysis and plotting code, but the final 120-task benchmark still needs the environment-specific solver adapter that actually invokes the chosen model/tool interface for each arm.

Before any evaluated run, implement and freeze that adapter so it:

1. consumes exactly one frozen schedule row and task payload;
2. constructs only the allowed arm context/state;
3. applies the same registered resource ceiling;
4. stores the raw request/response artifact before parsing/scoring;
5. invokes the frozen arm-blind evaluator path;
6. records before/after state hashes and proves evaluation-state non-mutation;
7. records request timestamp/model/provider metadata;
8. emits exactly one normalized record conforming to `schemas/paper5-attribution-run-v1.schema.json`;
9. never reads another arm's output or future task result;
10. exits fail-closed on task/hash/state/evaluator/resource mismatch.

Do **not** alter the executor, evaluator, aggregation rule, task set, sham policy or analysis after inspecting outcomes and continue calling the same packet confirmatory. A needed repair creates a new versioned packet.

### 3.5 Analyze four-arm results

Concatenate normalized run records in frozen schedule order into JSONL and run:

```bash
python experiments/paper5/analyze_attribution_results.py \
  --tasks /path/to/final-tasks.json \
  --schedule /path/to/frozen-schedule.json \
  --results /path/to/normalized-results.jsonl \
  --out-dir /path/to/paper5-analysis
```

This produces:

```text
task_level.csv
arm_metrics.csv
contrasts.csv
paired_outcomes.csv
stratum_metrics.csv
summary.json
```

Then:

```bash
python experiments/paper5/plot_attribution_results.py \
  --analysis-dir /path/to/paper5-analysis \
  --out-dir /path/to/paper5-figures
```

Produces:

```text
paper5_fig5_four_arm_attribution.pdf
paper5_fig5_causal_contrasts.pdf
paper5_fig5_paired_outcomes.pdf
paper5_fig5_resources.pdf
paper5_fig6_transfer_safety.pdf
```

Primary causal contrasts:

```text
TOTAL        = RAKL_LEARNING - MODEL_ONLY
EXPERIENCE   = RAKL_LEARNING - RAKL_RESET
CONTENT      = RAKL_LEARNING - RAKL_SHAM_MEMORY
ARCHITECTURE = RAKL_RESET - MODEL_ONLY
```

Keep `RAKL_ONLY_SUCCESS` and `BASELINE_ONLY_SUCCESS` equally visible. The analysis uses task-level aggregation, paired uncertainty/inference, and Holm adjustment for the three preregistered primary score contrasts.

### 3.6 Longitudinal RAKL_math cycle metrics

Collect standardized `RAKL_CYCLE_METRICS` from active RAKL_math cycles. Each chronological record must include at least:

```text
cycle_id
exact RAKL + RAKL_math Git identities
measurement scope/state fingerprints
seven-axis retained-novelty delta
```

Where truly measurable, also collect:

```text
episode count
diagnosis/lesson candidate count
validated lesson count
reusable tool/motif count
successful fresh-reuse count
contradicted/failed-transfer count
repeated structural-failure rate
saturated-route retry rate
route-switch latency
memory-changed-action rate
process telemetry
resource usage
coverage-bound retrieval misses
residual before/after transformation
```

Use `CANNOT_MEASURE` rather than zero when historical instrumentation does not support a value. Do not infer absence of a failure/memory event from an unsearched lane.

For a complete numeric JSONL subset, generate longitudinal plots with:

```bash
python experiments/paper5/plot_longitudinal_metrics.py \
  --cycle-metrics /path/to/cycle-metrics.jsonl \
  --out-dir /path/to/paper5-figures
```

Outputs:

```text
paper5_fig2_retained_growth.pdf
paper5_fig3_experience_conversion.pdf        # only if funnel fields complete
paper5_fig4_routing_failure_dynamics.pdf     # only if dynamics fields complete
```

The seven-axis growth curve stays labelled `INTERNAL_METROLOGY` until the independent novelty audit passes.

### 3.7 Process dashboard

Validate process records against `schemas/process-telemetry.schema.json`, then run:

```bash
python experiments/paper5/analyze_process_telemetry.py \
  --telemetry /path/to/process-telemetry.jsonl \
  --out-dir /path/to/process-analysis

python experiments/paper5/plot_process_dashboard.py \
  --dashboard /path/to/process-analysis/process_dashboard.csv \
  --out-dir /path/to/paper5-figures
```

Outputs:

```text
paper5_fig7_process_dashboard.pdf
paper5_ext_process_costs.pdf
```

Do not rank heterogeneous processes by one scalar. If cost-policy IDs differ, report them as non-comparable rather than silently normalizing them.

### 3.8 Independent retained-novelty audit

Freeze the audit sample before annotation under `NOVELTY_AUDIT_PROTOCOL_V1.md`. Use two independent annotators and a separate adjudicator. Same-session AI roles are development only.

Normalize one audit item per JSONL line with:

```text
event_id
axis
internal_retained
annotator_a_label
annotator_b_label
adjudicated_label
```

Run:

```bash
python experiments/paper5/analyze_novelty_audit.py \
  --annotations /path/to/novelty-audit.jsonl \
  --out-dir /path/to/novelty-analysis

python experiments/paper5/plot_novelty_audit.py \
  --analysis-dir /path/to/novelty-analysis \
  --out-dir /path/to/paper5-figures
```

Outputs:

```text
novelty_audit_metrics.csv
annotator_confusion.csv
novelty_audit_summary.json
paper5_ext_novelty_audit_rates.pdf
paper5_ext_novelty_audit_agreement.pdf
```

Required audit reporting:

```text
retained-novelty precision per axis + pooled
false-collapse rate
wrong-axis rate
insufficient-evidence rate
raw inter-annotator agreement
Cohen kappa on complete two-annotator pairs
raw agreement/confusion matrix
```

### 3.9 Remaining Paper V figures

Do not fabricate quantitative data for these. Build them only from bound real artifacts:

**Figure 1 — episode to governed method evolution.** Architecture diagram. Visually separate proposal/routing from authority/promotion.

**Figure 8 — version evolution DAG.** Nodes: incumbent, challengers, assured/rejected/retired/rollback states. Keep failed challengers. Bind edges to motivating episode IDs, preregistered meta-QoIs, development/fresh-assurance evidence and governance/attestation status.

**Figure 9 — case-study taxonomy.** Rows: P-vs-NP, RH, Navier–Stokes, Yang–Mills, Hodge, BSD, framework engineering. Columns: retrieval coverage, surrogate/root faithfulness, representation defect, local/global gluing, transfer-interface mismatch, source completeness, chronology/provenance, tooling/CI/governance. Populate only cells with exact evidence IDs; blank means unmeasured/unsearched, not absent.

**Figure 10 — trusted boundaries.** Architecture/security diagram separating untrusted proposals, measurement/development, protected assurance, and governance/promotion/rollback. Mark deployed versus partially hardened versus Paper-V-challenger/protocol-only surfaces.

---

## 4. Paper I and Paper IV

### Paper I

No new performance benchmark is required for the paper's present formal claims. Verify definitions/propositions, citation/reference integrity, and the authority invariant that experience/routing cannot increase scientific authority without the appropriate evidence/verification transition.

### Paper IV

No efficacy benchmark is required for the present assurance-architecture claim. Keep proof truth checker-gated. A proof-search/fresh-transfer benchmark may be added only if the manuscript is intentionally expanded to claim search-efficiency or discovery benefit; then use the same reset/learning isolation and hostile-near-miss principles.

---

## 5. Required artifact bundle before manuscript updates

For every empirical packet preserve:

```text
protocol/preregistration bytes + SHA-256
task/evidence packet bytes + SHA-256
model/tool/evaluator/resource/sham identities
exact Git subjects and dirty-tree checks
randomization schedule + hash
raw model/tool outputs
normalized run records
state-before/state-after hashes
scheduler submission/execution/harvest receipts where applicable
analysis inputs and outputs
figure source data
generated figures
all failures/CANNOT_CHECK/CANNOT_MEASURE records
```

Only after those artifacts are frozen should a result-ingest PR edit the manuscripts. Regenerate exact PDFs, run the citation/log/layout gates, and visually inspect every changed empirical figure page.

## 6. Non-negotiable interpretation rules

```text
ACCESS != COHERENCE != AUTHORITY
Episode != diagnosis != obstruction
Reflection != verification
Co-retrieval != compatibility
Local success != global solution
Experience-conditioned routing != epistemic authority
Derived memory != replacement for raw evidence
Bounded/vector saturation != absolute completeness
Being stuck != missing operator
Self-evolution evidence != self-promotion
```

Additional empirical rules:

```text
raw repository growth != learning
retrieval != successful reuse
same-session review != independent annotation
positive transfer without hostile-near-miss safety != robust transfer
one successful run != a global capability claim
benchmark gain != automatic framework promotion
```

## 7. Completion condition for issue #138

The execution issue is complete only when either:

1. the required packets have valid, hash-bound results and all corresponding plots/manuscript updates are reproduced from those artifacts; **or**
2. a packet fails/blocks and the negative/CANNOT_CHECK result is preserved and the manuscript is narrowed accordingly.

Do not keep rerunning until a preferred outcome appears.
