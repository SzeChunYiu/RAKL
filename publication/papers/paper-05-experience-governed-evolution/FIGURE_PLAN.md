# Paper 5 figure plan

**Status:** draft figure architecture. No panel may display unmeasured prospective values as data.

## Figure 1 — From research episode to governed method evolution

**Purpose:** communicate the paper's central object in one frame.

Flow:

```text
problem/task
  -> problem fibre
  -> operator/search action
  -> TaskEpisode
  -> diagnosis / lesson / obstruction
  -> retained RAKL state
  -> framework hypothesis
  -> challenger branch
  -> matched development evaluation
  -> fresh protected assurance
  -> governance / attestation
  -> next research episodes
```

Use a separate visual boundary around authority. Episode/lesson/method proposals may affect search priority; promotion requires protected external gates.

Do not depict same-session reviewer roles as independent human reviewers.

## Figure 2 — Seven-axis retained structured growth

**Purpose:** answer “what does RAKL learn over time?” without equating archive size with learning.

Planned data:
- x-axis: chronological research cycles or exact method-version epochs;
- cumulative retained novelty series/panels:
  - KNOWLEDGE
  - OPERATOR
  - EXPERIENCE_PATTERN
  - OBSTRUCTION
  - RELATION
  - PATH
  - META_METHOD
- annotate version promotion/rollback events;
- separate faint/raw inventory counts from adjudicated retained growth if shown;
- mark periods before standardized v3 telemetry as retrospective/incomplete.

Main rule: if semantic-novelty audit has not passed, label the curve `INTERNAL_METROLOGY`.

## Figure 3 — Experience conversion funnel with contradiction branches

**Purpose:** show that stored experience is not automatically reusable knowledge.

Funnel:

```text
TaskEpisodes
 -> diagnosis/lesson candidates
 -> supported/validated lessons
 -> reusable tools/motifs
 -> successful fresh reuses
```

Side branches:
- contradicted lessons;
- superseded diagnoses;
- failed transfers;
- unresolved episodes.

Do not make the graphic a monotonic success funnel; negative history is part of the result.

## Figure 4 — Repeated-failure and routing dynamics

**Purpose:** test whether persistent experience changes research behavior.

Candidate panels:
- repeated structural-failure rate by cycle/version;
- saturated-route retry rate;
- route-switch latency after a supported failure;
- fraction of actions observably changed by retrieved experience/gates.

Annotate major case-study failures such as XM003 retrieval miss and later coverage-bound-memory intervention if/when evaluated.

## Figure 5 — Four-arm causal attribution

**Purpose:** distinguish base-model capability from RAKL architecture and learned-memory content.

Main comparison:

```text
MODEL_ONLY
RAKL_RESET
RAKL_SHAM_MEMORY
RAKL_LEARNING
```

Show:
- task-level registered score with uncertainty;
- paired success outcomes including RAKL-only and baseline-only wins;
- validity failures;
- resource usage.

Add derived contrasts only after raw arm data:
- architecture lift;
- experience lift;
- content-specific lift;
- total lift.

No one aggregate “RAKL score.”

## Figure 6 — Hostile near-miss / false-transfer panel

**Purpose:** prevent a memory system that reuses everything from looking good.

Compare repeated-family, cross-domain-transfer and hostile-near-miss task strata.

Primary visual question:
- can RAKL gain on legitimate transfer while maintaining or improving near-miss rejection?

Report false-transfer alongside successful-transfer rates.

## Figure 7 — Process dashboard

**Purpose:** quantify the whole framework rather than only final answers.

For each canonical `method_specs.py` process surface show a compact matrix of:
- invocation count;
- valid completion / blocked / cannot-check;
- registered cost policy and cost;
- retained novelty yield;
- residual transformation;
- downstream reuse or decision effect where available.

Avoid ranking heterogeneous processes by one scalar.

## Figure 8 — RAKL version evolution DAG

**Purpose:** show recursive improvement as governed branching evidence rather than a marketing version sequence.

Nodes:
- 3.0 incumbent;
- candidate challengers;
- assured/rejected/meta-overfit/rollback states;
- later incumbents if/when promoted.

Edges show:
- motivating episode/failure IDs;
- preregistered meta-QoIs;
- development delta;
- fresh assurance delta;
- governance/attestation status.

A failed 3.1 candidate remains in the DAG rather than disappearing.

## Figure 9 — Case-study taxonomy across domains

**Purpose:** support the claim that research-process failures can share structure despite unrelated mathematics.

Rows: P-vs-NP, RH, Navier-Stokes, Yang-Mills, Hodge, BSD, framework engineering.
Columns:
- retrieval coverage;
- surrogate/root faithfulness;
- representation defect;
- local/global gluing;
- transfer-interface mismatch;
- source completeness;
- chronology/provenance;
- tooling/CI/governance.

Populate only evidence-backed cells with exact episode/artifact IDs. Do not infer absence from an unsearched lane.

## Figure 10 — Upgrade constitution / trusted boundaries

**Purpose:** answer the formal-methods/security reviewer quickly.

Layered diagram:

```text
untrusted proposal layer
  LLM / retrieved text / lesson candidates / challenger code

measurement and development layer
  telemetry / visible benchmarks / replay / debugging

protected assurance layer
  frozen fresh tasks / evaluator identity / thresholds / resource contract

governance layer
  approval / promotion gate / active-main attestation / rollback
```

Mark where current v3 is fully implemented, partially declaration-bound, Paper-5-challenger-only, or protocol-only.

## Main-text versus supplement

Likely main text:
1. episode-to-method loop;
2. seven-axis growth;
3. four-arm attribution;
4. version DAG;
5. case-study taxonomy.

Likely Extended Data/Supplement:
- detailed process dashboard;
- repeated-failure dynamics;
- hostile near-miss breakdown;
- trusted-boundary diagram;
- novelty-audit confusion matrices;
- resource sensitivity and component ablations.

## Pre-data rule

Until measured values exist, manuscript figures may show only:
- architecture diagrams;
- exact qualitative case-study mappings;
- empty/pre-registered axes or table structures explicitly labelled `PLANNED`.

Do not create illustrative fake bars/curves that could be mistaken for empirical results.