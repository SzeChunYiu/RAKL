# SELF-RAKL Research Round 015 — AI Capability Shaping and Research Cognitive Architecture

Date: 2026-08-09

Starting `main`: `20c7cb78c1d3563812ef76417647b92a285ccf7b`

Entering status: `ACTIVE_NON_FLAT`.

## 1. Baseline audit

The run began from live `main` and inspected recent commits, open issues/PRs, `docs/CONSTITUTION.md`, the latest self-RAKL round/receipt, current similarity implementation/tests, the meta-fiber backlog, and the repository test workflow.

Observed baseline:

```text
main = 20c7cb78c1d3563812ef76417647b92a285ccf7b
open issues = 0
open pull requests = 0
Constitution SHA = 4d456ceab32122391c830fe8586766cf0e0037aa
latest completed research round = SELF_RAKL_RESEARCH_014
similarity lane = ACTIVE_NON_FLAT
```

The selected residual was broader than similarity:

> A research algorithm should magnify capabilities the AI already expresses well while suppressing, externalizing, routing around, or substituting operations it performs unreliably.

The atomic question was not "does scaffolding help?" but:

> Can RAKL represent capability shaping as an evidence-governed method object and distinguish same-model utilization gain, failure suppression, and system gains caused by added external resources?

## 2. Constitutional classification

This is a **Class A supporting implementation plus Class B research formalization**, not a constitutional amendment.

It preserves:

- `LLM proposes; evidence governs`;
- same-context reflection is not independent review;
- blocking validity dominates optimization gains;
- frozen evaluation before method promotion;
- negative-result preservation;
- no automatic promotion from support code.

`docs/CONSTITUTION.md` was not modified.

## 3. Expert panel

Six role-separated review passes were used. They shared one orchestration context and are not claimed as independent reviewers.

1. **Cognitive architecture / cognitive-science lead** — task decomposition, external cognition, bounded operations, retrieval-vs-reasoning separation.
2. **Agent systems / software architecture lead** — interfaces, routing, typed handoffs, resource isolation, modular failure boundaries.
3. **Evaluation / statistics lead** — matched-model ablations, task-packet identity, blocking metrics, cost/latency accounting.
4. **Scientific-method / causal attribution lead** — distinguishing workflow gain from resource substitution and intrinsic-model claims.
5. **Computational creativity / search lead** — using generative breadth and cross-domain recombination without premature convergence.
6. **Adversarial reviewer** — decorative scaffolding, hidden resource deltas, post-hoc adaptation, fake independence, and complexity that does not improve registered QoIs.

### Delegated findings

| Finding | Primary roles | Adversarial condition |
|---|---|---|
| model capability != system capability | systems + causal attribution | external solver success must not be called intrinsic model gain |
| capability operator must name strength and weakness | cognitive architecture + evaluation | reject decorative operators with no target mechanism |
| smallest-compensator rule | evaluation + systems | richer scaffold must lose if simpler matched baseline ties it at lower cost |
| immutable external memory is failure suppression | cognitive architecture + scientific method | must measure repeated-null/refutation resurrection, not just narrative quality |
| routing/substitution require provenance | systems + causal attribution | hidden tool/specialist deltas invalidate pure workflow attribution |
| same-context critique remains non-independent | scientific method + adversarial | any independence claim requires observable context separation |

## 4. Fresh primary-source projections

### 4.1 BenchAgent: more agents are not automatically better

Fu et al. (2026), `arXiv:2606.05670`, compare single-agent, fixed multi-agent, and evolving multi-agent workflows under a normalized execution protocol. Under their substrate-internal comparisons, most tested multi-agent systems trail the matched single-agent anchor and occupy worse accuracy-cost positions.

**RAKL consequence:** complexity, agent count, or role count cannot be treated as capability gain. Every scaffold needs a matched simpler baseline.

### 4.2 Reliability decomposition: architecture can matter, attribution matters more

Dastidar (2026), `arXiv:2607.17044`, reports a production-agent decomposition in which the full architecture outperforms the bare base model on several benchmarks, while the isolated verification loop accounts for only part of the uplift and some comparisons remain unresolved. The work also separates deterministic, self-reflective and planner-mediated verification oracles.

**RAKL consequence:** measure the whole-system gain, then decompose which component/resource produced it. Do not attribute all uplift to the named mechanism.

### 4.3 VerifiAgent: verification can be routed by reasoning type

Han, Buntine and Shareghi (Findings of EMNLP 2025, DOI `10.18653/v1/2025.findings-emnlp.891`) combine meta-verification with adaptive tool-based verification selected by reasoning type.

**RAKL consequence:** verifier choice is itself a routing problem. Verification should be an explicit capability/operator coordinate rather than one universal self-check.

### 4.4 SWE-agent: interfaces can change expressed capability

Yang et al. (NeurIPS 2024), `arXiv:2405.15793`, study agent-computer interface design and show that the interface around an LM materially affects software-engineering task behavior.

**RAKL consequence:** the environment/interface is part of the system under test. Capability can be shaped by making useful actions and observations easier for the model.

### 4.5 Agentless: simpler workflows are a serious baseline

Xia et al. (2024), `arXiv:2407.01489`, show that a simple localization-repair-validation workflow can compete strongly with more complex software-engineering agents.

**RAKL consequence:** the smallest-compensator rule needs an explicit simple baseline. Architecture complexity is a cost and a hypothesis, not a virtue.

## 5. Main formal result: capability shaping is a typed operator

For atomic research operation `k`, RAKL now represents a candidate operator as

\[
\mathcal O_k=(S_k,W_k,G_k,C_k,V_k,H_k),
\]

with:

- `S_k`: strengths to exploit;
- `W_k`: weaknesses to target;
- `G_k`: amplification mechanisms;
- `C_k`: compensators/externalizers;
- `V_k`: verifier/oracle contract;
- `H_k`: typed handoff/memory contract.

The full theory is in `docs/AI_CAPABILITY_SHAPING.md`.

The operator must be frozen before evaluation. An operator with no named strength or weakness is rejected as having no declared capability target. A declared strength without an amplification mechanism, or a weakness without a compensator, is incomplete.

## 6. Model capability and system capability are separated

RAKL records the observed system as

\[
Y(T)=F(M,A,E;T),
\]

where `M` is the base model, `A` the research architecture, `E` declared external resources, and `T` the task family.

This yields separate attribution classes:

```text
MODEL_UTILIZATION_AMPLIFICATION
FAILURE_SUPPRESSION
EXTERNAL_CAPABILITY_SUBSTITUTION
SPECIALIST_COMPLEMENTATION
ROUTING_GAIN
DECOMPOSITION_GAIN
MEMORY_EXTERNALIZATION_GAIN
UNRESOLVED_MIXED_ATTRIBUTION
```

A calculator, theorem prover, database, deterministic verifier, or specialist can legitimately increase **system** capability without proving that the base model itself became intrinsically better.

## 7. Frozen benchmark chronology

Before implementation, the run committed:

```text
research/SELF_RAKL_RESEARCH_015_FROZEN_BENCHMARK.json
commit = ce94ec78139b402b4bd4d8693fcaa616a6fab4b5
```

The benchmark contains 17 hostile worlds including:

- same-model amplification;
- failure suppression;
- combined amplification and suppression;
- decorative multi-agent/scaffold overhead;
- nominal quality gain with blocking-validity regression;
- declared versus hidden external-resource deltas;
- base-model mismatch;
- task-packet mismatch;
- hidden-label/post-hoc adaptation;
- same-context review mislabeled independent;
- external-oracle substitution;
- long-horizon decomposition;
- memory externalization;
- verifier false alarms;
- unknown chronology / `CANNOT_CHECK`.

No acceptance threshold was changed after implementation.

## 8. Supporting implementation

Candidate branch:

```text
self-rakl/capability-shaping-v1
```

Implementation:

```text
src/rakl/capability.py
tests/test_capability.py
src/rakl/__init__.py
```

The API provides:

```text
CapabilityShapingOperator
CapabilityMetricObservation
CapabilityTrial
CapabilityTrialReport
validate_capability_operator
evaluate_capability_shaping
```

The evaluator is support-only. It cannot activate a default workflow, modify routing, promote canonical knowledge, or establish intrinsic model-weight improvement.

## 9. Hostile implementation tests

The test packet covers:

- valid frozen operator contract;
- missing amplification mechanism;
- missing compensator;
- post-hoc operator definition;
- same-resource amplification + failure suppression;
- failure suppression without nominal quality gain;
- decorative scaffold with only cost overhead;
- blocking regression dominating nominal quality gain;
- declared external solver classified as system/resource gain;
- hidden resource delta invalidation;
- resource delta misreported as pure decomposition gain;
- different base-model invalidation;
- different task-packet invalidation;
- hidden label leakage;
- post-hoc operator adaptation;
- fake independent review;
- unknown benchmark chronology;
- immutable operator contract.

The exact candidate head `c197d10a64de429037268e9ea9ea4c1daeeed5e2` completed the unchanged PR `test` workflow successfully (`run 31308006815`, pytest job `93231319190`). The candidate was three commits ahead and zero behind its frozen base and changed only the new capability module, new tests, and public support exports. `main` still matched the frozen incumbent immediately before promotion, so it was advanced by a non-forced fast-forward.

## 10. Capability map

The first RAKL capability map is now explicit:

```text
decomposition -> exploit generative subproblem breadth; suppress hidden-dependency loss
search -> exploit semantic breadth; suppress surface/familiar-domain attraction
hypothesis generation -> exploit diversity; suppress premature convergence
analogy -> exploit abstraction; suppress false friends and transfer overreach
mathematics -> exploit symbolic fluency; suppress silent algebra/unit errors
causal reasoning -> exploit mechanism proposal; suppress correlation-to-mechanism escalation
synthesis -> exploit integration; suppress context flattening
review -> exploit objection generation; suppress same-context reinforcement
memory -> exploit reconstruction; suppress forgotten null/refutation history
stopping -> exploit semantic judgment; suppress premature closure/endless search
```

These are hypotheses to test, not assertions that the listed compensators already improve performance.

## 11. New retained objects

After prior-art deduplication, Round 015 retains the following internal RAKL control objects:

1. `CAPABILITY_SHAPING_OPERATOR_CONTRACT`
2. `MODEL_SYSTEM_CAPABILITY_ATTRIBUTION_SPLIT`
3. `STRENGTH_WEAKNESS_COMPENSATOR_MAP`
4. `SMALLEST_COMPENSATOR_MATCHED_ABLATION_RULE`
5. `BLOCKING_VALIDITY_DOMINATES_CAPABILITY_UPLIFT`
6. `COGNITIVE_OPERATION_TYPED_HANDOFF_GRAPH`

These are useful internal objects; no individual headline novelty claim is asserted yet.

## 12. Saturation verdict

```text
RAKL_METHOD = ACTIVE_NON_FLAT
capability_shaping_lane = ACTIVE_NON_FLAT
similarity_lane = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

The lane is non-flat because it adds a new method-level coordinate and executable support contract. It is not validated as a default research architecture because the frozen worlds are contract/hostile tests, not matched empirical trials of real RAKL tasks.

## 13. Next discriminators

Highest-value next work:

1. Build a **matched-model capability-shaping benchmark** over real RAKL tasks: decomposition, search, analogy, verification, memory and synthesis.
2. Run baseline vs smallest targeted compensator vs richer scaffold under identical model/task/evaluator/resource conditions.
3. For tool/specialist additions, run factorial ablations that separate workflow effects from resource effects.
4. Measure failure-mode-specific changes, not only final answer score.
5. Preserve simple-baseline wins and nulls; complexity must earn its place.
6. Couple the capability map to `META_N052_REAL_FAR_DOMAIN_RETRIEVAL_BENCHMARK` so the JUMP pipeline becomes the first real capability-shaping case study.

The Constitution remains unchanged.
