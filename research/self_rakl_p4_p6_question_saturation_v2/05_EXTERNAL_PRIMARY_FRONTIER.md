# External primary frontier used by question audit v2

Cutoff: 2026-08-15. This is a nearest-work ledger, not a claim that all literature is exhausted.

## Paper IV function parents

- **STAT: Skill-Targeted Adaptive Training**, ICLR 2026, OpenReview `m3jG3GaNIj` — learner missing-skill profile; adaptive selection/synthesis.
- **MATES**, arXiv `2406.06046` — model-aware data selection from locally probed influence.
- **Group-MATES**, arXiv `2502.14709` — group-level/model-aware data utility.
- **MASS: Mathematical Data Selection via Skill Graphs**, ICML 2025, PMLR 267 — skill graph guides mathematical pretraining data selection; reports token-efficiency/equal-token benefits.
- **SkillDAG**, arXiv `2606.03056` — self-evolving typed dependency/conflict/specialization/duplicate skill graph for inference-time skill selection.

Residual not absorbed by these anchors at this cutoff:

```text
checkpoint-bound typed directional/QoI/boundary structural state
-> incremental prediction of transfer gain/harm beyond strongest learner-state/influence parents
-> decision value under noncompensatory harms
-> exact train-to-inference structural identity reuse
```

Each arrow is a separate empirical obligation.

## Paper V function parents

- **Towards Autonomous Mathematics Research / Aletheia**, arXiv `2602.10177` — research-agent trajectory beyond olympiad solving, with reported research-level milestones.
- **Formal Conjectures**, arXiv `2605.13171` — evolving Lean 4 benchmark with 2,615 statements, including open research conjectures and solved formalization tasks.
- **BFS-Prover**, arXiv `2502.03438` — scalable best-first formal proof search.
- **HTPS**, arXiv `2205.11491` — hyper-tree/AND-OR proof search.
- **DeepSeek-Prover-V2**, arXiv `2504.21801` — strong formal theorem-proving system.
- **AlphaProof / Olympiad-level formal mathematical reasoning with reinforcement learning**, Nature 2026 — strong policy/value formal-search family.

Residual not absorbed at this cutoff:

```text
executor-independent research-promotion product
(specification, truth, novelty, value, verifier trust)
+
hostile false-promotion/valid-recall/cost evaluation
```

The proof/search frontier is a parent/consumer of this interface, not the novelty claim by itself.

## Paper VI/self-evolution function parents and threats

- **EvoSkill**, arXiv `2603.02766` — failure analysis -> skill mutation -> held-out validation -> Pareto frontier; transfer evidence.
- **SkillFoundry**, arXiv `2604.03964` — scientific resources -> scoped/provenanced/tested executable skills -> iterative expand/repair/merge/prune.
- **SkillDAG**, arXiv `2606.03056` — typed evolving skill graph.
- **Red Queen Gödel Machine**, arXiv `2606.26294` — evaluator/utility evolution across epochs with the evaluation criterion fixed within each epoch.
- **BenchGuard**, arXiv `2604.24955` — automated benchmark artifact audit; scientific benchmark defects are themselves consequential evidence.
- **BadScientist**, ACL 2026 — multi-model LLM reviewers can accept convincing but unsound generated research; reviewer agreement is not an independent truth oracle.
- **SciAgentArena**, arXiv `2606.12736` — approximately 200 scientific-agent tasks with stepwise verification and agent-agnostic environment; current agents remain uneven on open-ended/novel research.
- **ScienceAgentBench**, ICLR 2025; verified artifact update in 2026 — data-driven scientific-agent benchmark with executable evaluation.

Residual not absorbed at this cutoff:

```text
fixed audited evidence epoch
-> weakness diagnosis
-> discriminator when layer is underidentified
-> smallest-layer method mutation / external mechanic assimilation
-> fresh assurance under the unchanged evaluator
-> validity-gated frontier update

AND

evaluator/meta-policy change
-> separate identity-bound outer-assurance epoch
-> anchor replay / measured evaluator drift
-> new epoch
```

RAKL's distinctive burden is not that evaluators may evolve. It is to make evaluator evolution non-sovereign with respect to scientific/method authority and to preserve exact chronology/provenance when the ruler itself changes.

## Search limitations at cutoff

- Same-context search; not independent review.
- Proprietary system internals may remain `CANNOT_CHECK` even when public summaries exist.
- Functionally equivalent work under remote terminology can reopen this ledger.
- Publication after the cutoff reopens nearest-work status.
