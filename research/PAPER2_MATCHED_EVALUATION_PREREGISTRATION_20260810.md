# Paper 2 matched scientific-workflow evaluation — preregistration draft

Date: 2026-08-10  
Status: design/freeze candidate. No confirmatory result has been observed under this protocol.

## 1. Causal question

Holding the base model family, sealed scientific task world, evidence-access condition, tool registry and resource ceiling fixed, what changes when the research-control architecture changes?

The design deliberately separates two interventions:

1. **reasoning/control architecture**;
2. **evidence access**.

This separation is required because an architecture cannot reason its way to evidence it never receives, and giving one arm a better evidence substrate would confound epistemic governance with acquisition advantage.

## 2. Factorial structure

### Architecture arms

- `DIRECT_STRONG`: strong direct synthesis prompt with the full evidence allowed by its evidence-access arm;
- `RAG_STRONG`: query decomposition + strong retrieval + cited synthesis;
- `GENERIC_AGENT`: strong planner/executor or ReAct-style research agent;
- `HYPOTHESIS_EVIDENCE_LOOP`: explicit hypothesis -> evidence -> revision state without the full RAKL authority/atlas machinery;
- `RAKL_FIXED`: full registered RAKL architecture, no method self-modification;
- `RAKL_EVOLVING`: Self-RAKL only in fresh-assurance tasks for which the candidate/evaluator boundary is frozen.

### Evidence-access arms

- `PUBLIC`: ordinary task-accessible evidence universe;
- `CURATED`: curated evidence bundle available equally to all architecture arms;
- `COMPLETE_SEALED`: benchmark-complete sealed packet used for known-answer/process evaluation.

The primary Paper-2 architecture estimand compares architectures **within the same evidence-access level**. Cross-level comparisons estimate the value/ceiling of acquisition separately.

## 3. Evidence-topology strata

Tasks are stratified before result access:

- `SINGLE_DOMINANT_SIGNAL`;
- `DISTRIBUTED`;
- `CONTRADICTION_RICH`;
- `PROVENANCE_DEPENDENT`;
- `MECHANISM_DISCRIMINATION`.

The paper will report a capability frontier rather than force one global superiority statement. A simpler lawful parent winning on simple aggregation tasks is a positive scientific result: it identifies where RAKL complexity is unnecessary.

## 4. Registered failure classes

The deterministic pilot registry owns ten process failure classes:

1. context mismatch;
2. estimand/QoI mismatch;
3. identity/alias false merge;
4. evidence-lineage duplication;
5. prediction -> mechanism escalation;
6. mechanism -> identification escalation;
7. negative-history erasure;
8. evaluator capture;
9. mandatory-evidence omission;
10. ontology-conditioned discovery miss.

The pilot task file is `benchmarks/epistemic_control/tasks_v0.json`. It is a conformance instrument, not the final confirmatory LLM benchmark.

## 5. Primary outcomes

### P2-1 Unsupported Authority Upgrade Rate (UAUR)

Number/rate of claims promoted to an authority class not licensed by the sealed evidence and task design.

### P2-2 Hidden scientific-defect detection

Balanced accuracy / recall over preregistered defect classes.

### P2-3 Counterevidence uptake

Whether material counterevidence changes the active conclusion, narrows scope or causes justified abstention.

### P2-4 Cost-valid scientific success

Probability of a valid final scientific outcome without crossing blocking invariants under the common resource ceiling.

## 6. Secondary outcomes

- context/QoI error rate;
- evidence-lineage inflation;
- negative-history loss;
- protected-evaluator violations;
- mandatory-evidence omission;
- hidden-mechanism recall at fixed budget;
- provenance exactness;
- final task correctness/calibration;
- input/output/preprocessing tokens;
- retrieval/tool/verification calls;
- wall time.

No scalar utility is canonical. Pareto frontiers are primary when validity and cost trade off.

## 7. Blocking failures

The following cannot be averaged away by a high endpoint score:

- unsupported authority upgrade in a protected claim class;
- evaluator capture;
- omission of preregistered mandatory counterevidence/scope material;
- negative-history deletion in the registered failure world;
- hidden-mechanism miss when OWMD recall is the primary target.

## 8. Strong parent baselines

The evaluation must not use a weak single-prompt straw man. Parent mechanisms should be reproduced/assimilated where feasible:

- strong RAG / evidence-contract synthesis;
- a strong generic planner/executor agent;
- explicit hypothesis/evidence revision;
- clean-room scientific synthesis controls inspired by SciConBench;
- mechanized evidence binding inspired by GAVEL where the task supports atomic evidence identifiers;
- trajectory-to-evidence qualification inspired by recent research-agent evidence-conversion work.

If a parent method provides a useful operator, RAKL may assimilate it. The matched comparison must then distinguish the parent mechanism from the additional RAKL controls rather than pretending the parent does not exist.

## 9. Prospective OWMD

A separate hidden-function benchmark will:

- remove the canonical mechanism name from the query;
- provide only function/constraint/dynamics signatures;
- include lexical/semantic decoys;
- compare lexical, dense semantic, LLM query expansion, citation-neighborhood/methodology retrieval and RAKL OWMD;
- measure recall@budget, false-positive mechanism rate, time/tokens/tool calls and downstream usefulness.

Retrospective recovery of a mechanism already known to the developers receives no fresh discovery credit.

## 10. Statistical plan

Paired task worlds are the primary unit.

- binary paired outcomes: McNemar + paired risk-difference confidence interval;
- continuous/count outcomes: paired bootstrap over task worlds;
- repeated stochastic generations: generation nested within task, not treated as independent scientific tasks;
- model-family robustness: stratified or hierarchical analysis;
- multiple primary endpoints: Holm correction or a frozen hierarchical testing order.

A pilot may update sample-size estimates before the final test split is opened. It may not redefine the primary estimand after confirmatory outcomes are observed.

## 11. Resource accounting

For each run record at minimum:

`input_tokens`, `output_tokens`, `preprocess_tokens`, `retrieval_calls`, `tool_calls`, `verification_calls`, `wall_seconds`.

If monetary or compute cost is reproducibly available, record it separately. Missing cost coordinates remain missing; they are not silently set equal.

## 12. Evaluator protection

The confirmatory evaluator, task outcomes, task split and protected invariants are frozen before candidate output access. A self-modifying candidate cannot edit the evaluator in the same assurance transaction.

LLM judges are used only when executable/domain checks are unavailable, with blinded arm identity and a frozen rubric.

## 13. Falsifiers

The Paper-2 empirical case is narrowed or rejected if:

- strong simpler conditions match the process and endpoint outcomes at lower cost without more blocking failures;
- apparent RAKL gains disappear when evidence access is equalized;
- ablations do not selectively worsen the failure mode they are supposed to control;
- OWMD does not improve hidden-function discovery beyond strong query-expansion/methodology-retrieval parents;
- results depend mainly on one model or one hand-designed task family.

## 14. Saturation effect

Executing this evaluation will create new manuscript semantic objects regardless of whether results are positive or null. The current same-context manuscript-saturation certificate therefore must be reopened and re-earned after results are assimilated.
