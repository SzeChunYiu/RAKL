# Paper 5 attribution task eligibility v1

**Purpose:** prevent the causal-attribution benchmark from grading itself using internally defined notions of progress on unsolved open problems.

## Primary rule

The confirmatory four-arm attribution benchmark uses tasks whose evaluation contract is frozen independently of the solver output and whose target outcome/quality can be checked without accepting RAKL's own research-state judgment as ground truth.

Eligible task sources may include:
- hidden-solution mathematical/reasoning tasks with exact answer/proof/checker criteria;
- bug-finding, code-repair, retrieval, synthesis or research-method tasks with independently constructed tests/labels;
- held-out research-process tasks whose correct next action or defect class is adjudicated from a frozen evidence packet;
- construction/optimization tasks with an executable evaluator frozen before candidate execution;
- source/retrieval tasks with a content-identified corpus and independently audited relevance labels.

The six unsolved Millennium root problems are **not** used as routine binary success labels merely because an agent or RAKL state says that progress occurred. Their live trajectories remain observational case-study evidence unless a local subtask has an independently checkable evaluation contract.

## Hidden outcome requirement

Where a task has a known target answer, proof, defect label, relevant-memory set, or best-action label, that target is hidden from all solver arms and from the sham-memory construction. The evaluator may access it only through the frozen evaluation path.

## Task contamination checks

Before inclusion, each task is screened for:
- occurrence in the development sequence;
- answer leakage into the learned RAKL state;
- semantic-equivalent answer leakage in sham controls;
- occurrence in the solver-visible benchmark-generation notes;
- direct inclusion of evaluator rubric/threshold in solver context beyond the allowed task specification;
- source-cutoff violations.

A contaminated task is removed/replaced before outcomes are opened, with the replacement identity frozen. Post-outcome deletion for poor performance is forbidden.

## Open-research local atoms

A local atom from RAKL_math may enter the confirmatory benchmark only if its evaluator is independently specified before execution. Examples include:
- detecting a planted surrogate/root-coordinate mismatch;
- selecting/rejecting a tool given a frozen applicability witness;
- identifying a source-scope defect against a frozen primary-source packet;
- detecting a gluing/interface omission in a known-answer synthetic or source-derived model;
- reproducing a verified local lemma/check rather than claiming progress on the unsolved root.

Such tasks measure research behavior. They do not turn the unresolved root into a solved/unsolved benchmark label.

## Arm-blind evaluation

The primary evaluator receives a normalized output object without the arm name or memory provenance. Any solver-output fields that trivially identify the arm are stripped by a frozen parser when this can be done without changing semantic content. If arm blinding is technically impossible for a task class, that limitation is declared and the evaluator-separation claim is narrowed.

## Ground-truth authority

Task eligibility and evaluator identity are benchmark authority only. They do not grant mathematical theorem authority to RAKL research outputs beyond the task's registered evaluation scope.