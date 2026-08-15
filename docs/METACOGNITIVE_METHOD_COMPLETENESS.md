# Metacognitive Method Completeness

Status: support architecture; does not amend the Constitution.

## 1. Motivation

Self-RAKL can improve known fibers and still fail to notice that its *method vocabulary itself* is incomplete. Human reflection suggests a useful analogy, but RAKL should not anthropomorphize an LLM or treat introspective language as self-knowledge.

The engineering target is **externally governed metacognition**: measurable monitoring of the method's performance and limits, followed by constrained control actions that can reopen a known fiber, request an explanation reconstruction, require a countermodel/outside view, or open a candidate ontology/operator gap.

The central rule is:

> **A model may report uncertainty; RAKL measures and governs what that report is allowed to change.**

## 2. Monitor and control are separate

Let `Omega_t` denote the incumbent method/operator basis and `K_t` the epistemic state. A metacognitive monitor receives observable task/outcome information:

\[
\mathcal M(K_t,\Omega_t,a_t,e_t)\to d_t,
\]

where `d_t` is a diagnostic packet, not a scientific state update.

A separate controller maps a validated diagnostic into a follow-up action:

\[
\mathcal C(d_t,\Lambda,B)\to
\{
\text{NO_AUDIT},
\text{REOPEN_KNOWN_FIBER},
\text{RECONSTRUCT_EXPLANATION},
\text{COUNTERMODEL},
\text{OUTSIDE_REVIEW},
\text{ONTOLOGY_CHALLENGE},
\text{OPERATOR_CHALLENGE},
\text{CANNOT_CHECK}
\}.
\]

Neither monitor nor controller mints scientific authority or method promotion.

## 3. Domain-scoped calibration, not global self-awareness

RAKL should maintain a calibration surface indexed by at least method fiber and context:

\[
\operatorname{Cal}(m,f,\gamma),
\]

rather than one scalar "self-awareness" score.

A model that is well calibrated for retrieval may be poorly calibrated for mechanism identification. Cross-domain metacognitive transfer requires direct evidence; otherwise the correct state is `CANNOT_CHECK`.

This also applies to RAKL itself: success on provenance tests does not imply good self-diagnosis of ontology gaps.

## 4. Triggered reflection rather than continuous reflection

Reflection has cost and can interfere with task execution. RAKL therefore invokes metacognitive audits only when a registered signal is present or the expected cost of a missed failure justifies the audit.

Typical high-value triggers include:

```text
HIGH_CONFIDENCE_ERROR
REPEATED_UNCLASSIFIED_RESIDUAL
TARGET_UNREACHABLE
EXPLANATION_RECONSTRUCTION
BIAS_RISK
EXTERNAL_REVIEW
DOMAIN_TRANSFER
FEEDBACK_UPDATE
HIGH_VALUE_CHECKPOINT
```

A low-value uncertainty signal may be skipped when the audit cost exceeds the registered expected failure cost. If probabilities are not calibrated, the policy uses a preregistered priority/risk class rather than fabricating expected values.

## 5. Explanation reconstruction as a gap detector

Verbal familiarity can create an illusion of understanding. RAKL therefore distinguishes:

```text
can state a conclusion
!=
can reconstruct the required explanation
```

For a claim/operation with frozen required explanatory elements `R`, the auditor asks for a reconstruction `P` and computes

\[
G_{exp}=R\setminus P.
\]

A non-empty set is an `EXPLANATION_GAP`.

The required set must be frozen or externally specified before the reconstruction is scored; the proposer cannot weaken the rubric after seeing its answer.

Examples of required elements include:

```text
assumptions
building blocks
interaction
mechanism ancestry
observation map
scope
falsifier
error semantics
```

An explanation gap is not itself proof that the scientific claim is false. It is evidence that the current reasoning object is insufficiently reconstructed for the registered authority target.

## 6. Consider-the-opposite becomes a countermodel contract

Generic prompts such as "be unbiased" or "critique yourself" are too weak to count as a completed challenge.

A countermodel check requires an explicit alternative that would reverse or materially narrow the incumbent conclusion under the same registered target. The packet records:

```text
incumbent claim
countermodel
shared evidence
assumptions that differ
observation that discriminates them
outcome
```

If a countermodel is requested but not actually constructed, the audit remains incomplete.

## 7. Outside view and independence

Humans can see bias in others more readily than in themselves, and self-distancing can improve some forms of reasoning. RAKL translates this into a stricter outside-view rule.

An outside review receives full independent-review credit only when:

1. the process/context is independently instantiated; and
2. the evidence lineage used for the review is sufficiently independent for the claimed role.

A future stronger criterion should also test **conceptual-basis independence**: whether the reviewer uses a meaningfully different decomposition/ontology rather than replaying the incumbent categories with different wording.

Same-model/same-context critique remains useful but is never silently upgraded to independent evidence.

## 8. Feedback calibrates strategy; it does not automatically prove capability growth

Outcome feedback can improve calibration and response strategy without improving underlying task sensitivity. Therefore RAKL records at least two coordinates:

```text
CALIBRATION_CHANGE
TASK_CAPABILITY_CHANGE
```

and forbids:

\[
\Delta \text{calibration}>0
\not\Rightarrow
\Delta \text{capability}>0.
\]

A capability improvement still requires the appropriate frozen performance benchmark.

## 9. From unknown weakness to ontology/operator gap

Metacognition connects directly to the Method Completeness Challenge.

### Known weakness

If an error maps to an existing fiber, reopen that fiber. Do not invent a new operator merely because the failure was surprising.

### Candidate ontology gap

Repeated residuals that remain outside the incumbent failure taxonomy support only:

```text
ONTOLOGY_GAP_CANDIDATE
```

A new residual class requires its own frozen benchmark before activation.

### Candidate method-basis gap

For target `tau`, if:

\[
\operatorname{Reachable}(\tau\mid K_t,\Omega_t)=0,
\]

RAKL first identifies the blocking epistemic cut `B_tau`. If the cut is real and no incumbent operator can resolve it, the diagnostic becomes:

```text
METHOD_BASIS_GAP_CANDIDATE
```

not `NEW_OPERATOR_PROVEN`.

The candidate operator must then enter the normal Self-RAKL challenger protocol.

### Formulation gap candidates (recursive framework audit)

The recursive framework audit (`src/rakl/recursive_framework_audit.py`) projects each
responsibility coordinate of an open formulation onto a proposal-side diagnostic
(`FORMULATION_GAP_CANDIDATES` in `src/rakl/metacognition.py`):

```text
QUESTION_FORMULATION_GAP_CANDIDATE
FRAMEWORK_GAP_CANDIDATE
DECOMPOSITION_GAP_CANDIDATE
INTERFACE_GAP_CANDIDATE
MEASUREMENT_GAP_CANDIDATE
EVALUATOR_GAP_CANDIDATE
```

These are still **proposal-side**: a diagnostic names where additional checking is
warranted; it never repairs, promotes, or mints authority, and an unknown coordinate fails
closed to `CANNOT_CHECK`.

## 10. Intellectual humility as a protocol, not a personality trait

RAKL does not need to simulate a humble personality. It needs **revisability**.

Operational humility means:

```text
high confidence can be downgraded by external error evidence
active authority can be withdrawn after refutation
CANNOT_CHECK is preferred to invented certainty
negative history remains addressable
an outside challenger can reopen a method fiber
```

A system that says "I may be wrong" but cannot lower authority after contradictory evidence is not operationally humble.

## 11. Curiosity becomes explicit information-gap routing

Human curiosity research motivates a useful search intuition, but RAKL should not depend on an affective analogue. A curiosity-like trigger is represented as an explicit discrepancy between what is required for the target and what is currently supported:

\[
G_{info}(\tau)=Requirements(\tau)-Supported(K_t).
\]

The active query policy then chooses actions that reduce the highest decision-relevant or mechanism-separating gap per cost.

## 12. Current executable support layer

`src/rakl/metacognition.py` implements a deterministic fail-closed classifier with these outcomes:

```text
NO_AUDIT_REQUIRED
CALIBRATED_NO_NEW_GAP
KNOWN_WEAKNESS
CALIBRATION_WEAKNESS
EXPLANATION_GAP
ONTOLOGY_GAP_CANDIDATE
METHOD_BASIS_GAP_CANDIDATE
QUESTION_FORMULATION_GAP_CANDIDATE
FRAMEWORK_GAP_CANDIDATE
DECOMPOSITION_GAP_CANDIDATE
INTERFACE_GAP_CANDIDATE
MEASUREMENT_GAP_CANDIDATE
EVALUATOR_GAP_CANDIDATE
INDEPENDENT_REVIEW_REQUIRED
CANNOT_CHECK
```

The strongest gap verdict is still only a candidate diagnosis. The module cannot:

- mint scientific authority;
- repair an ontology automatically;
- activate a new operator;
- alter routing;
- amend the Constitution;
- promote a method challenger.

## 13. Prospective scientific test

A publish-grade test should hide missing weakness/operator classes from the incumbent system and compare:

1. ordinary same-context self-reflection;
2. generic critic/debate;
3. outcome-feedback calibration only;
4. RAKL structured metacognitive audit;
5. RAKL audit plus genuinely independent outside review.

Primary outcomes:

```text
held-out missing-weakness detection
false invention of new weakness classes
known-vs-unknown weakness discrimination
method-basis-gap recall
explanation-gap recall
calibration error
independent-review misuse
reflection tokens / latency / cost
downstream improvement after separately governed repair
```

Null criterion: if structured audits do not improve held-out missing-operator/ontology discovery over ordinary reflection at matched cost, retain the psychology mapping as explanation only and do not expand runtime complexity.

## 14. Novelty boundary

RAKL does not claim invention of metacognition, confidence calibration, self-explanation, counterfactual debiasing, self-distancing, curiosity, feedback learning, intellectual humility, or external metacognitive control.

The candidate contribution is narrower: **these mechanisms are translated into a scientific-method completeness controller operating over RAKL's contextual atlas, authority system, residual ontology, target reachability, negative history, and governed self-evolution protocol.**
