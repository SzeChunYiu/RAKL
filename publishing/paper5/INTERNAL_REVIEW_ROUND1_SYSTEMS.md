# Paper 5 internal adversarial review — Round 1: AI systems and experimental design

**Review status:** same-session internal adversarial review. This is **not** independent or mutually blind peer review.  
**Review basis:** Paper 5 draft branch, RAKL metrology/attribution code, upgrade protocol, live RAKL/RAKL_math case artifacts, and primary literature/source metadata inspected during this session.  
**Emphasis:** causal attribution, experimental design, statistics, systems reproducibility, scalability, and whether the reported metrics actually distinguish RAKL from the base LLM.

## Overall assessment

The manuscript has a credible systems-method question and now addresses a key weakness common to self-improving-agent work: it separates deployment from validated evolution and separates total framework lift from static workflow, persistent experience and memory-content effects. The seven-axis growth vector plus process telemetry is more informative than raw archive size. However, a strong empirical claim remains blocked until the preregistered prospective study is executed. The current live Millennium record is observational and adaptive; it can motivate mechanisms but cannot supply confirmatory causal effect sizes.

## Major concerns

### R1-M1 — Prospective causal evidence is not yet collected
- **Severity:** Major
- **Blocking:** Yes for any claim that RAKL improves research capability; No for the architecture/protocol/case-study draft as explicitly scoped.
- **Axis:** experimental-design / claim-moderation
- **Claim pointer:** any future claim that RAKL 3.x helps the same underlying LLM or that experience improves fresh research.
- **Evidence pointer:** Paper 5 abstract and Sections 7 and 10; `experiments/paper5/ATTRIBUTION_PREREGISTRATION_V1.md`.
- **Concern:** the manuscript currently contains an implemented architecture and retrospective case observations, not a completed matched experiment. The live agents are not randomized arms and most historical episodes predate standardized v3 telemetry.
- **Resolution test:** freeze the final attribution packet, run the registered task set across the four arms, publish all paired outcomes/resources/integrity failures, and retain null/negative results.
- **Status after revision:** OPEN / correctly scoped as prospective.

### R1-M2 — Initial four-arm implementation did not prove fresh-transfer state isolation
- **Severity:** Major
- **Blocking:** Yes until fixed.
- **Axis:** experimental-design / reproducibility
- **Claim pointer:** `RAKL_LEARNING` evaluation tasks are independent draws from one frozen learned state and cannot learn from earlier transfer tasks.
- **Evidence pointer:** initial `src/rakl/v3_metrology.py` implementation on the Paper 5 branch.
- **Concern:** packet-level learned/reset/sham hashes existed, but individual runs initially lacked before/after state hashes. A transfer run could therefore mutate state without the validator noticing.
- **Resolution test:** bind every run to exact before/after state hashes; require MODEL_ONLY, RESET, SHAM and LEARNING runs to equal their registered arm state before and after; add a planted contamination test.
- **Status after revision:** RESOLVED in commits adding per-run state identity and `test_attribution_fails_closed_when_fresh_learning_run_mutates_state`.

### R1-M3 — Sham memory could be an unfair or leaky placebo
- **Severity:** Major
- **Blocking:** Yes for a memory-content causal claim until frozen.
- **Axis:** experimental-design
- **Claim pointer:** `RAKL_LEARNING - RAKL_SHAM_MEMORY` isolates the effect of learned semantic content.
- **Evidence pointer:** Paper 5 Section 7 and attribution preregistration.
- **Concern:** an arbitrary irrelevant context may be more distracting than learned memory, while a too-close sham may leak the answer. Without a construction rule, the contrast is uninterpretable.
- **Resolution test:** freeze `sham_policy_hash`, match object type/count/token budget/metadata where feasible, exclude eligible structural matches and target answers, audit accidental equivalence/leakage, and report residual budget mismatch.
- **Status after revision:** PROTOCOL RESOLVED in `ATTRIBUTION_PREREGISTRATION_V1.md`; empirical validation remains future work.

### R1-M4 — Task sample size, multiplicity and stopping rules were initially underdetermined
- **Severity:** Major
- **Blocking:** Yes for confirmatory inference until frozen.
- **Axis:** statistical-rigor
- **Claim pointer:** primary lift estimates and significance/uncertainty.
- **Evidence pointer:** initial Paper 5 Section 7.
- **Concern:** without a fixed task count, strata, repeated-run policy, multiplicity rule and stopping conditions, the evaluation can drift after outcomes.
- **Resolution test:** freeze task count/strata, primary contrasts, Holm or other family-wise control, paired analysis, resource policy and no efficacy early stopping.
- **Status after revision:** PROTOCOL RESOLVED. Current design targets 120 task units across three strata, with three repeated generations per task-arm when budget permits, paired task-level inference, Holm control and integrity-only early stopping.

### R1-M5 — Open Millennium roots cannot serve as routine ground truth
- **Severity:** Major
- **Blocking:** Yes if used as confirmatory success labels.
- **Axis:** mechanism-evidence / experimental-design
- **Claim pointer:** claims that RAKL improves research based on the live six-problem programme.
- **Evidence pointer:** observational case-study sections.
- **Concern:** for an unsolved root problem there is no frequent external positive label. Internally defined residual contraction could become a self-serving proxy.
- **Resolution test:** separate the observatory from the confirmatory attribution benchmark; require held-out tasks with independently frozen evaluation contracts; allow RAKL_math local atoms only when their evaluator is independently checkable.
- **Status after revision:** PROTOCOL RESOLVED in `ATTRIBUTION_TASK_ELIGIBILITY_V1.md`; live Millennium data remain observational.

### R1-M6 — Retained semantic novelty is itself a modelled judgment
- **Severity:** Major
- **Blocking:** Yes for a strong claim that the seven-axis curve measures true learning; No for internal descriptive metrology.
- **Axis:** data-resource-quality / mechanism-evidence
- **Claim pointer:** lattice growth is quantified by retained novelty rather than raw object count.
- **Evidence pointer:** `docs/RAKL_METROLOGY.md`, `src/rakl/v3_metrology.py`.
- **Concern:** RAKL could label its own additions novel and thereby inflate the growth curve. Identity/supersession errors are especially dangerous for EXPERIENCE_PATTERN, PATH and META_METHOD.
- **Resolution test:** freeze a sample before inspection, obtain genuinely independent semantic novelty/identity judgments and adjudication, report retained-novelty precision, false-collapse and wrong-axis rates, and keep the curve labelled `INTERNAL_METROLOGY` until audited.
- **Status after revision:** PROTOCOL RESOLVED in `NOVELTY_AUDIT_PROTOCOL_V1.md`; confirmatory independent audit not yet executed.

### R1-M7 — Initial state metrology did not cover the full declared knowledge world
- **Severity:** Major
- **Blocking:** Yes for the phrase “whole RAKL lattice size.”
- **Axis:** data-resource-quality / reproducibility
- **Claim pointer:** state snapshots quantify how the RAKL lattice grows.
- **Evidence pointer:** initial `measure_state` implementation.
- **Concern:** the first implementation counted v3 runtime state but did not automatically include legacy `KnowledgeFiber` epistemic projections, even though they can be materialized in the unified substrate.
- **Resolution test:** require callers to explicitly supply the legacy knowledge-fibre universe, include it in the substrate hash/counts, report coverage fields, and reject comparisons across different measurement scopes.
- **Status after revision:** RESOLVED in `v3_metrology.py` and `test_rakl_v3_metrology_coverage.py`.

### R1-M8 — Generic cost scalar was not comparable across processes
- **Severity:** Major
- **Blocking:** No for state-growth measurement; Yes for resource-normalized process comparison.
- **Axis:** statistical-rigor / reproducibility
- **Claim pointer:** retained novelty or residual contraction per unit cost can be compared across invocations.
- **Evidence pointer:** initial `ProcessTelemetry.cost`.
- **Concern:** “cost” can mean tokens, wall time, money or a composite. Averaging heterogeneous units is meaningless.
- **Resolution test:** bind every cost to a `cost_policy_id`; mark aggregates with multiple cost policies non-comparable; prefer raw registered resource vectors in confirmatory attribution.
- **Status after revision:** RESOLVED in metrology code/schema/tests.

## Minor comments

### R1-m1 — Distinguish resource ceiling from matched resource use
The current design correctly records actual use in addition to a common ceiling. The manuscript should avoid saying arms are “resource matched” solely because they share a ceiling; report actual paired usage and sensitivity analyses.

### R1-m2 — Randomize arm order
The preregistration now block-randomizes four-arm run order within task/repetition. Keep this visible in Methods to reduce service-time drift concerns.

### R1-m3 — Report baseline-only wins prominently
A system paper can unconsciously hide cases where scaffolding harms a capable model. The paired outcome table should put `BASELINE_ONLY_SUCCESS` next to `RAKL_ONLY_SUCCESS` in the main result figure.

## Round-1 recommendation posture

**Architecture/protocol draft:** ACCEPT for continued review.  
**Empirical “RAKL improves LLM research” claim:** NOT YET ACCEPTABLE.  
**Blocking unresolved evidence:** R1-M1 and the execution portions of R1-M6. These require prospective data/independent audit and must not be fabricated by manuscript revision.
