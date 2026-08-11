# Paper 5 retained-novelty audit protocol v1

**Purpose:** test whether RAKL's internally retained seven-axis novelty labels correspond to independent judgments of semantic novelty/supersession rather than measuring self-declared archive growth.

**Authority:** this protocol audits metrology. It does not grant scientific authority to the underlying research objects.

## 1. Objects under audit

Audit candidate state changes that contribute nonzero retained novelty on any v3 axis:

```text
KNOWLEDGE
OPERATOR
EXPERIENCE_PATTERN
OBSTRUCTION
RELATION
PATH
META_METHOD
```

The audit unit is one proposed retained-novelty event plus its exact predecessor state and source/evidence lineage.

## 2. Sampling

For each framework evaluation epoch, sample before inspection:

- at least 20% of nonzero retained-novelty events per axis when the axis has fewer than 500 events;
- otherwise at least 100 events per axis;
- include all events that contribute to a version-promotion primary endpoint if fewer than the above sample;
- additionally sample a matched set of zero-retained proposals to estimate false-negative identity collapse.

Freeze the sample IDs and hash before annotation.

If an axis has fewer than 10 events, audit all events and report that agreement estimates are unstable.

## 3. Reviewer separation

Target confirmatory audit:
- two annotators/review processes independently inspect the same frozen packet without seeing the other response;
- one separate adjudicator resolves disagreements after both responses are frozen;
- evidence-lineage/provenance identity is audited separately from semantic judgment when possible.

Same-session LLM role labels do not count as independent annotation and may be used only for development of the rubric.

## 4. Visible packet

Each item contains only:
- exact old-state identity or relevant predecessor objects;
- candidate object/change;
- claimed novelty axis/axes;
- source/evidence lineage required to understand semantic identity;
- canonical definitions for the seven axes;
- explicit scope/context.

Do not show:
- RAKL's internal explanation for why it counted the object as novel;
- downstream benchmark outcome;
- version-promotion decision;
- another annotator's answer.

## 5. Annotation questions

For each claimed axis, independently answer:

1. `SEMANTICALLY_NEW` — adds a distinct canonical object/coordinate under the frozen identity rubric;
2. `DUPLICATE_OR_EQUIVALENT` — semantically already present under another representation/name;
3. `SUPERSESSION_ONLY` — changes/corrects an existing object without adding the claimed novelty unit;
4. `WRONG_AXIS` — may be new but belongs to another novelty axis;
5. `INSUFFICIENT_EVIDENCE` — cannot determine from packet.

For zero-retained controls, ask whether the proposal was correctly collapsed/superseded or whether distinct novelty was lost.

## 6. Primary audit metrics

For each axis and pooled:

```text
retained_novelty_precision
  = adjudicated SEMANTICALLY_NEW among internally retained events / auditable internally retained events

false_collapse_rate
  = adjudicated semantic novelty among internally zero-retained controls / auditable zero-retained controls

wrong_axis_rate
insufficient_evidence_rate
```

Also report annotator agreement before adjudication. Use a statistic appropriate to the categorical labels (for example Cohen's kappa for two complete annotators or Krippendorff's alpha for missing/cannot-assess settings) together with the raw agreement matrix; do not report the coefficient alone.

## 7. Promotion interpretation

An internally computed seven-axis growth curve is labelled `INTERNAL_METROLOGY` until this audit passes the preregistered precision/false-collapse criteria.

A strong version-evolution paper claim that depends materially on retained novelty requires:
- audit sample frozen before reviewing the labels;
- independent responses frozen before adjudication;
- provenance clean;
- acceptable retained-novelty precision;
- no material false-collapse or wrong-axis failure that would change the version-level conclusion.

Exact thresholds must be frozen in the final evaluation packet before the audited epoch result is opened.

## 8. Negative results

If precision is low, Paper 5 must not replace semantic novelty with raw object counts. Instead:
- report the internal curve and audit failure separately;
- identify identity/ontology failure modes;
- treat improved novelty metrology as a future framework challenger;
- preserve all original state events and annotations.

This audit therefore makes the growth metric falsifiable rather than self-validating.