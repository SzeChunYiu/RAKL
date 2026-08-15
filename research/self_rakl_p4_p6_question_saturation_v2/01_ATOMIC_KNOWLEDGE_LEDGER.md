# Atomic knowledge ledger — Papers IV–VI

Cutoff: 2026-08-15.  Same-context synthesis; primary-source identifiers are recorded for later citation verification.  No source listed here becomes a scientific receipt merely by appearing in this ledger.

## Ledger vocabulary

```text
ESTABLISHED_IN_RAKL      exact repo artifact/result already exists
CURRENT_RAKL_NEGATIVE    preserved negative/invalid result constrains successors
EXTERNAL_PARENT          function substantially occupied outside RAKL
OPEN_RESIDUAL            differentiated RAKL question remains open
IMPLEMENTATION_GAP       contract exists but live wiring/control is missing
MEASUREMENT_GAP          proposed effect has no adequate instrument/result
QUESTION_CONFUSION       one headline question collapses separable scientific objects
```

---

# Paper IV — Structural Learning Mechanics

## P4-A01 — learner-conditioned data selection is not novel by itself

Status: `EXTERNAL_PARENT`.

Strong anchors:

- STAT: Skill-Targeted Adaptive Training, ICLR 2026 (OpenReview `m3jG3GaNIj`): profiles a student's missing skills and adaptively selects/synthesizes data.
- MATES, arXiv `2406.06046`: model-aware selection using locally probed data influence as the learner evolves.
- Group-MATES, arXiv `2502.14709`: group-level/model-aware data utility.

Implication: Paper IV must not headline adaptive curriculum, model-conditioned selection, missing-skill targeting, or saturation-aware reweighting in isolation.

## P4-A02 — structured skill/data graphs are occupied functions

Status: `EXTERNAL_PARENT`.

Anchors:

- MASS, ICML 2025 / PMLR 267: mathematical data selection using a skill graph; reports large token savings and equal-token gains.
- SkillDAG, arXiv `2606.03056`: typed dependency/conflict/specialization/duplicate graph for agent skill retrieval with online graph evolution.

Implication: “use a graph/typed structure for selection” is insufficient novelty. RAKL must earn a residual from the semantics of its directional/QoI/boundary structural object and from train-to-inference identity reuse.

## P4-A03 — current Phase-0/1 result is capability-graded, not a general law

Status: `ESTABLISHED_IN_RAKL`.

Artifact: `research/paper4_phase1_results_v2/README.md`.

Observed terminals:

```text
state_reachability @ 7B: MECHANISM_SIGNAL_PRESENT
sequence_composition @ 1.5B/3B/7B: NO_STATE_DEPENDENT_RESIDUAL
balance_conservation <=3B: MODEL_FLOOR
balance_conservation @ 7B: REPETITION_REMAINS_VALUABLE
```

Only one family/model cell provides the desired differential state-dependent signal. Therefore a universal structural-exposure law is not earned.

## P4-A04 — information value and policy value are different objects

Status: `QUESTION_CONFUSION` + `OPEN_RESIDUAL`.

The current Paper-IV residual combines:

```text
structural state carries information about next-exposure value
+
allocator correctly acts on the state
```

These are separable. A useful state can be paired with a harmful allocator; an adaptive allocator can win using information already available to a simpler parent.

The local structure-identity counterexample on PR #708 is a concrete witness: a representation can identify a real low-mastery structure while an allocator that collapses identity spends budget on the wrong structure.

## P4-A05 — right first estimand is incremental predictive information

Status: `OPEN_RESIDUAL`.

Question:

> Given the current model/checkpoint, does the RAKL structural state predict the vector of future transfer gain/harm from an exposure beyond loss, gradient/influence and strongest skill-state parents?

Minimum design requirements:

- cross-fitted/fresh outcome prediction; predictor selection cannot see confirmatory labels;
- candidate identity and structure identity preserved;
- proper scoring / calibration, not only rank correlation;
- per-coordinate gain/harm targets;
- direct comparison to STAT/MATES-style state and influence parents;
- negative result retained even if a downstream heuristic happens to win.

This is an **information sufficiency** question, not yet an allocation question.

## P4-A06 — second estimand is decision value under constraints

Status: `OPEN_RESIDUAL`.

Conditional on P4-A05:

> Does a policy using incremental structural information improve a registered decision target over Static Structural and strongest adaptive parents after all probing/selection/training cost, with composition/boundary/retention harms noncompensatory?

The existing five-arm Phase-2 experiment addresses part of this question for the frozen Adaptive-v1 policy. Its result must not be reinterpreted as the answer to P4-A05.

## P4-A07 — exact train-to-inference identity is a third, independent claim

Status: `OPEN_RESIDUAL`.

Question:

> Is the same registered structural object that was useful for training allocation also the object that reduces inference-time transfer/re-derivation cost on fresh tasks?

A training win with an unrelated latent inference representation does not establish one shared RAKL substrate.

## P4-A08 — broad Paper-IV title requires heterogeneous regimes

Status: `MEASUREMENT_GAP`.

A single 7B state-reachability signal cannot support a general “Structural Learning Mechanics” law. Broad wording should require multiple independent structural families and multiple learner/checkpoint regimes, including negative/harm regimes and an explicit applicability boundary.

---

# Paper V — Verified Discovery in Mathematics

## P5-A01 — research-level proof search is no longer the empty frontier

Status: `EXTERNAL_PARENT`.

Anchors:

- Aletheia / “Towards Autonomous Mathematics Research”, arXiv `2602.10177`: end-to-end research agent spanning literature/navigation/long-horizon reasoning and reported research-level outcomes.
- Formal Conjectures, arXiv `2605.13171`: 2,615 Lean 4 statements, including 1,029 open research conjectures and solved autoformalization problems, explicitly designed as an evolving verified-discovery benchmark.
- BFS-Prover, arXiv `2502.03438`; HTPS, arXiv `2205.11491`; DeepSeek-Prover-V2, arXiv `2504.21801`; AlphaProof family: strong proof-search parents.

Implication: Paper V should not derive novelty from “LLM + verifier + search can do mathematics.”

## P5-A02 — RAKL's durable object is research promotion, not generation

Status: `OPEN_RESIDUAL` with strong architectural substrate.

Recommended object:

```text
machine-generated candidate
-> intended-specification alignment
-> exact theorem truth/proof
-> novelty dossier
-> research-value status
-> verifier/trust-chain status
-> research promotion or typed block
```

The five coordinates are already explicit in the manuscript. The question becomes whether this product is a **minimal and useful promotion interface** across heterogeneous proposers.

## P5-A03 — theorem truth cannot discharge the intended-claim problem

Status: `ESTABLISHED_IN_RAKL` architecturally; mechanization/evidence still open.

A proof assistant checks its formal statement. It does not prove that the statement faithfully formalizes the researcher's intended informal target. Therefore exact theorem proof and specification alignment remain separate load-bearing coordinates.

## P5-A04 — novelty is an external-world process

Status: `ESTABLISHED_IN_RAKL` architecturally; natural-world measurement open.

Truth of a fixed proved statement may remain stable while novelty decreases after an older/equivalent result is found. Novelty therefore requires cutoff, search universe/route coverage and equivalence analysis; no proof checker can mint it.

## P5-A05 — verifier trust is a meta-assurance coordinate

Status: `OPEN_RESIDUAL` / cross-cutting with Paper VI.

A proof receipt can be internally correct relative to a checker whose implementation/dependency identity later changes or is discovered unsound. Paper V should expose the trusted-computing-base boundary explicitly and test version/axiom/hash substitution attacks.

## P5-A06 — assurance must be evaluated against reject-all

Status: `MEASUREMENT_REQUIREMENT`.

Zero false promotion is meaningless if the architecture blocks everything. A hostile benchmark therefore needs co-primary:

```text
invalid intended-research promotion rate
AND
valid research-promotion recall
```

plus typed `CANNOT_CHECK` quality and total assurance cost.

## P5-A07 — proof-search benefit and assurance benefit are separate

Status: `QUESTION_CONFUSION` in broad “verified discovery” language.

Verification can improve epistemic safety while increasing search cost; a better search policy can increase theorem yield while leaving research-promotion assurance unchanged. VTG/search efficiency should therefore remain a secondary mechanic unless its own strongest-parent gate is positive.

## P5-A08 — executor independence is testable by proposer replacement

Status: `OPEN_RESIDUAL`.

Run the same promotion state machine with at least:

```text
neural/LLM proposer
symbolic/enumerative/tactic proposer
```

The relevant invariant is stable authority semantics, not equal theorem-solving power.

---

# Paper VI — Orion Scientific Research Engine

## P6-A01 — self-evolving skill libraries and held-out selection are occupied

Status: `EXTERNAL_PARENT`.

Anchors:

- EvoSkill, arXiv `2603.02766`: failure analysis -> skill mutations -> held-out validation -> Pareto frontier; reports transfer.
- SkillFoundry, arXiv `2604.03964`: scientific resources -> scoped/provenanced/tested executable skills -> expand/repair/merge/prune loop.
- SkillDAG, arXiv `2606.03056`: typed skill graph that evolves during execution.

Implication: Paper VI cannot claim novelty from “agent learns reusable skills,” “keeps a Pareto frontier,” or “self-evolves a skill library” alone.

## P6-A02 — evaluator evolution is now itself a frontier

Status: `EXTERNAL_PARENT` + `OPEN_RAKL_RESIDUAL`.

Anchor: Red Queen Gödel Machine, arXiv `2606.26294`.

Key concept: evaluation criteria may evolve, but the criterion is fixed **within an epoch** so the target does not move during the comparison. This directly overlaps RAKL's higher-order evaluator/meta-policy mutation surface.

RAKL residual must therefore be stronger than “evaluators can evolve.” It should center evidence/authority chronology, benchmark audit, and a non-sovereign evaluator transition contract.

## P6-A03 — benchmark correctness is part of the self-evolution problem

Status: `EXTERNAL_PARENT` + direct repo incident relevance.

Anchor: BenchGuard, arXiv `2604.24955`, reports author-confirmed defects in scientific-agent benchmarks and automated artifact auditing.

RAKL evidence: `docs/EVALUATOR_INTEGRITY_MERGE_ORDER_INCIDENT_710.md` records a real merge before a deferred trusted-parent-evaluator verdict; the later verdict was `valid=false` and is preserved as firewall evidence.

Implication: “candidate improves under evaluator E” is uninterpretable unless E itself has a valid, frozen, content-bound status for that epoch.

## P6-A04 — same-context multi-model review is not an independent assurance root

Status: `EXTERNAL_THREAT`.

Anchor: BadScientist, ACL 2026, demonstrates convincing unsound AI-generated papers can obtain high acceptance rates from multi-model LLM review systems and identifies concern/acceptance conflicts.

Implication: “several LLM reviewers agree” must never satisfy RAKL's outer-assurance/independent-review coordinate by itself.

## P6-A05 — current meta-evolution loses diagnosis information

Status: `IMPLEMENTATION_GAP`.

`mechanic_diagnosis.py` represents `DISCRIMINATOR_REQUIRED`, while `meta_evolution.py::EvolutionPortrait` accepts only a tuple of causes. A multi-cause diagnosis can therefore reach mutation routing before the registered discriminator is resolved.

Successor: `meta_evolution_v2.py` consumes the diagnosis verdict and fails to mutation until enough layer-level information exists.

## P6-A06 — current outer assurance is under-typed

Status: `IMPLEMENTATION_GAP`.

Current higher-order governance consumes `outer_assurance_frozen: bool`. That bit cannot encode:

```text
which evaluator?
which benchmark bytes?
which subject?
was it frozen before candidate outcome?
was candidate outcome used to construct the evaluator?
is the outer evaluator the target evaluator itself?
```

The v2 challenger replaces the bit with an identity/chronology-bound receipt.

## P6-A07 — mutation credit must not transfer for free

Status: `IMPLEMENTATION_GAP`.

Current mutation-policy weight is global per operator. A successful representation reset on Paper IV can therefore raise its prior on unrelated Paper-V/Paper-VI fibres. The successor indexes credit by operator + target layer + scope key. Cross-scope gain needs an explicit transfer/assimilation result.

## P6-A08 — repeated failure count is not evidence diversity

Status: `IMPLEMENTATION_GAP`.

Three reruns or near-duplicate mutations do not justify opening a larger architecture space merely because a counter reaches three. Escalation should depend on distinct failure-family/evidence-epoch identities and eventually on assurance quality, not attempt count.

## P6-A09 — Pareto selection must be validity-gated

Status: `IMPLEMENTATION_GAP` relative to the repo's own documented semantics.

`docs/CONTEXTUAL_METHOD_CAPABILITY_FRONTIER.md` says blocking validity precedes Pareto optimization. `CandidateDelta` in the current meta-evolution kernel contains only soft improvement coordinates. The v2 challenger adds a wrapper that removes `FAIL` and `CANNOT_CHECK` candidates before dominance calculation.

## P6-A10 — right capstone question is evaluator-governed recursive improvement

Status: `RECOMMENDED_HEADLINE`.

> Can Orion expand a validated research-capability frontier by diagnosing a weakness, assimilating or inventing a method change, and demonstrating fresh scoped improvement while the evaluator/benchmark/authority boundary that authorizes that change remains frozen and uncontaminated — and can evaluator changes themselves occur only through a separate outer epoch?

This question subsumes the layer contribution/cost table as instrumentation. It also remains meaningful when the incumbent loses to an external agent or the challenger fails.

---

# Cross-paper dependency map

```text
Paper IV asks whether a typed structural state is predictive/actionable/reusable.
        |
        v
Paper III governs whether a learned method may be installed.
        |
        v
Paper VI demonstrates recursive method acquisition/evolution under protected evaluation.

Paper V supplies a domain where strong authority oracles exist,
but separates proof truth from specification/novelty/value/trust.
        |
        v
Paper VI can use verified mathematics as one hard-oracle self-evolution domain,
without making math the only domain of the capstone.
```

The series is strongest when IV and V are **domain-specific measurement/assurance papers** and VI is the **recursive system-level self-evolution demonstration**, rather than when all three independently claim generic intelligence improvement.
