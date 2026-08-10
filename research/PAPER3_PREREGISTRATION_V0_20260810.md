# Paper 3 structural-amortization preregistration v0

Date: 2026-08-10  
Status: mechanism-level preregistration. Large-scale result access has not occurred.

## Central question

Can one context/QoI-scoped structural representation improve both learning-data efficiency and inference-time reuse beyond strong semantic, skill-graph and workflow-prior parents?

## H1 — incremental structural transfer signal

On held-out transfer pairs, structural features/witness status add material predictive value after semantic similarity is included.

Primary analysis:

`transfer_success ~ semantic_similarity + structural_similarity + interaction + (1|family)`

The exact model may be logistic or a preregistered nonparametric analogue depending label balance, but the choice is frozen before the final split is opened.

## H2 — Q2/Q3 mechanism

- Q2 low-semantic/high-structural cases should transfer materially better under RAKL than semantic retrieval parents.
- Q3 high-semantic/low-structural decoys should be rejected materially more often by RAKL than semantic/analogy-only parents.

A system that improves Q2 but also transfers Q3 aggressively does not establish safe structural reuse.

## H3 — training efficiency

At a frozen structural-OOD capability target, structural curation reduces examples/tokens/compute relative to strong parents in task mixtures with cross-domain structural redundancy.

Baselines include at minimum:
- uniform/random;
- semantic dedup/diversification;
- Skill-It-like dependency sampling;
- MASS-like skill-graph selection.

## H4 — inference efficiency

With a frozen base model and operator/skill universe, structural retrieval/adaptation lowers total test-time cost at equal or better target capability than:
- semantic exemplar/memory retrieval;
- analogy prompting;
- reasoning-primitive retrieval;
- structural workflow prior/SWIFT-like transfer where implementable.

## H5 — redundancy mechanism

Create datasets at controlled structural redundancy levels while surface diversity is held approximately fixed. Preregister a monotone/rank test between redundancy and RAKL cost-to-capability advantage.

If the curve is flat, the structural-amortization mechanism is unsupported even if one benchmark happens to improve.

## H6 — shared substrate

The same persistent structural identifier and invariant/boundary record used in training curation must be addressable at inference. If training and inference require unrelated representations, report two separate methods rather than one shared-substrate result.

## Cost accounting

Count:
- structure extraction/induction;
- human/expert adjudication where used;
- training;
- retrieval;
- adaptation/reasoning;
- tool calls;
- verification;
- wall time/compute where reproducible.

A runtime token reduction is not a net-efficiency claim if offline induction cost is omitted.

## Data split

Split by surface domain within structural family. The strongest Q2 tests hold out the target domain entirely while exposing the source structure in other domains.

A second split holds out entire structure families to quantify genuine structure-new generalization; reuse is not expected to help when the relevant structure is absent from the library.

## Annotation

For human-curated items, record independently:
- role mapping;
- relation mapping;
- invariant set;
- boundary conditions;
- QoI;
- valid/invalid transfer label.

Use at least two independent annotations plus adjudication for confirmatory items. Report agreement by coordinate rather than one aggregate score.

## Primary endpoints

1. structural-OOD capability;
2. invalid-transfer rate in Q3;
3. cost-to-target capability;
4. incremental transfer prediction from structural features.

Secondary:
- tokens/examples to target;
- search nodes/tool calls;
- latency;
- calibration;
- break-even reuse count;
- performance on genuinely structure-new tasks.

## Falsifiers / stop rules

Do not scale the training study if any pilot condition holds:
- structural label agreement is poor;
- Q3 invalid transfer remains high;
- structural features add no information beyond semantic features;
- witness extraction/verification cost dominates plausible reuse savings;
- parent method matches the full cost/capability frontier.

Large-model training is a later-stage experiment, not a prerequisite for learning that the mechanism is false.
