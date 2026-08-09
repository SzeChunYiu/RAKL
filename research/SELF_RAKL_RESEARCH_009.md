# SELF-RAKL Research Round 009 — Theoretical Foundations for Publication

Date: 2026-08-09

Starting `main`: `40562e2039a1f88dfdd520f65c7d5301f5d2990b`

Entering global state: `ACTIVE_NON_FLAT`.

This round is **research/documentation only**. It does not modify active RAKL behavior or the Constitution.

## 1. Frozen expert panel

Five roles were fixed before theoretical synthesis.

1. **Formal epistemology / mathematical-methods researcher** — background in belief revision, partial identification, local-to-global formalisms, set-valued inference, and proof obligations. Task: define the RAKL epistemic state and distinguish definitional invariants from empirical claims.
2. **Philosophy-of-science / scientific-modeling researcher** — background in perspectival realism, model pluralism, representation, mechanism, and underdetermination. Task: prevent RAKL from relabeling established philosophy as a novel contribution.
3. **Autonomous-science / LLM-systems researcher** — background in scientific agents, research automation, world models, hypothesis search, and experiment loops. Task: identify the closest current systems and the level at which RAKL can remain distinct.
4. **Experimental-design / metascience researcher** — background in active learning, Bayesian/goal-oriented design, falsification, stopping rules, reproducibility, and benchmark design. Task: convert theoretical claims into discriminating experiments and cost-controlled ablations.
5. **Adversarial novelty reviewer** — background in priority disputes, semantic equivalence, benchmark leakage, and scientific overclaiming. Task: assume the proposed method is not novel and search for prior frameworks that collapse the claim.

Panel rule: an ingredient is counted as RAKL novelty only if the adversarial reviewer cannot normalize it to prior work and the distinction changes a formal state transition or a measurable benchmark decision.

## 2. Native publication problem

The repository already contains many strong principles, but they are distributed across Constitution, Knowledge Atlas, perspectival-pluralism, saturation, RAKLBench, and Self-RAKL documents.

That creates a publication weakness:

```text
many defensible principles
        ↓
described mainly as architecture/practice
        ↓
reviewer can interpret RAKL as a bundle of agent-engineering heuristics
```

The round therefore asks a different object-level question:

> What is the smallest formal scientific-method object that explains the RAKL principles and generates falsifiable predictions distinct from ordinary LLM agent workflows?

## 3. External research routes

### 3.1 Autonomous-science systems

Current systems already cover much of the visible workflow.

- **AI co-scientist**: generate/debate/evolve multi-agent hypothesis generation and experimental validation.
- **AI Scientist-v2**: end-to-end research with progressive agentic tree search.
- **Agent Laboratory**: literature, experimentation, and report-writing workflow with human feedback.
- **Robin**: iterative literature, hypothesis, experiment proposal, data interpretation, and updated hypotheses in a lab-in-the-loop setting.
- **Kosmos**: long-horizon data/literature discovery using a structured world model and traceable citations.
- **AutoDiscovery**: open-ended hypothesis search driven by Bayesian surprise and MCTS.
- **POPPER**: agentic sequential falsification with statistical error control.
- **Science Hypothesis Map POMDP**: explicit science-driven belief-space planning under uncertainty.

Panel verdict: **workflow completeness, multi-agent orchestration, active search, belief-space planning, and falsification are prior art.**

### 3.2 Philosophy and formal epistemology

- **Perspectival realism/model pluralism** already legitimizes multiple partial scientific representations and warns against monist “view from nowhere” reasoning.
- **Sheaf-theoretic local-to-global formalisms** already make compatibility of local data and obstructions to global sections mathematically explicit in their own domains.
- **Belief revision** already studies rational hypothesis/state revision under new information.
- **Partial identification** already provides mathematical tools for retaining an identified set and making decisions under ambiguity rather than arbitrarily choosing one underdetermined theory.

Panel verdict: **local views, pluralism, obstruction, belief change, and identified sets are not individually novel RAKL ideas.**

### 3.3 Evidence-governance neighbors

Two 2026 results materially narrow the publication claim.

- **Active Epistemic Control for Query-Efficient Verified Planning** separates a grounded fact store from a belief store and gates final commitment on grounded preconditions/compatibility.
- **An Autonomous Scientific Knowledge Generation Framework for AI-Driven Scientific Discovery** integrates ontology-guided literature acquisition, extraction, semantic harmonization, knowledge fusion, provenance/context preservation, and validation.

Panel verdict: RAKL must not claim novelty merely for “grounded facts separate from predictions,” ontology normalization, provenance, context preservation, or validated knowledge fusion.

### 3.4 Epistemic-process evaluation

The 2026 paper **AI scientists produce results without reasoning scientifically** reports that successful autonomous-science outcomes can coexist with frequent evidence ignoring and weak refutation-driven belief revision.

This is directly decision-relevant to RAKL.

Panel verdict: RAKLBench must measure the **epistemic process**—authority transitions, evidence uptake, contradiction handling, partial identification, negative-history preservation, and stopping—not only final task success.

## 4. Theoretical synthesis

The panel converged on a new description:

> **RAKL is an evidence-governed recursive atlas process, not a particular agent architecture.**

The formal state introduced in `docs/THEORETICAL_FRAMEWORK.md` is

\[
K_t=
(\mathcal A_t,\mathcal V_t,\mathcal O_t,\mathcal F_t,
 \mathcal E_t,\mathcal H^-_t,\mathcal S_t),
\]

representing the local-view atlas, surviving model/identified set, obstructions, recursive fiber frontier, evidence/provenance, negative history, and saturation state.

The proposer is separated from the authority transition:

\[
G_\theta(K_t,a_t)\rightarrow\mathcal P_t
\]

but canonical update occurs only through an evidence-aware validator and update operator:

\[
K_{t+1}=\mathcal U(K_t,a_t,e_{t+1},V).
\]

This turns “LLM proposes; evidence governs” into a theory-level property that can be attacked with known-answer worlds.

## 5. Candidate publication novelty after deduplication

The panel rejected novelty claims for individual ingredients. The retained candidate contribution is the **joint epistemic transition discipline**:

1. projection/context before competition;
2. typed/scoped transition relations before equivalence closure;
3. non-forced gluing with plural/identified-set outputs;
4. scoped authority separating representation, prediction, mechanism, identification, and decision;
5. proposal generation with no direct canonical authority;
6. residual-driven recursive atomic fibers;
7. immutable negative history;
8. semantic and evidence-lineage-aware saturation;
9. recursively governed self-improvement using frozen evaluation and protected evaluator authority.

The adversarial novelty criterion is intentionally strong:

> If a pre-cutoff framework is found that is semantically equivalent to this integrated method after terminology normalization, the RAKL method-level novelty claim is weakened or refuted.

This criterion is frozen in `RAKL_PAPER_THEORY_CLAIM_REGISTRY_001.json`.

## 6. New proof obligations

This round opens proof obligations rather than pretending that suggestive notation is already a theorem.

### PO-1 Generation non-authority
Changing proposer output alone cannot increase canonical authority.

### PO-2 Mechanism non-upgrade
Prediction or observational equivalence cannot create mechanistic authority.

### PO-3 Typed non-escalation
Mixed/weaker relation edges cannot create stronger equivalence without a licensed composition map.

### PO-4 Non-forced gluing
Aligned incompatible charts remain an obstruction/identified set unless new evidence resolves them.

### PO-5 Negative-history monotonicity
Prior null/refuted events remain addressable after every successor update.

### PO-6 Conservative lineage saturation
Discovering shared ancestry or aliasing cannot manufacture additional independent-flat credit.

### PO-7 Evidence absence honesty
Missing external evidence produces partial/blocked/`CANNOT_CHECK`, not confidence-based substitution.

### PO-8 Residual reopening
A native residual invalidates local saturation certificates in every capable scope.

### PO-9 Meta-evaluator separation
A candidate method cannot earn promotion solely from an evaluator inside its own write authority.

## 7. Publication benchmark implications

A novel-method paper needs mechanism-separating ablations, not just end-to-end demonstrations.

The registered evaluation families are:

```text
known-answer epistemic worlds
hostile literature/provenance worlds
discriminator-selection worlds
historical time-cutoff rediscovery
long-horizon epistemic integrity
self-RAKL evaluator-gaming worlds
```

Required ablations remove context alignment, typed relations, authority layering, negative history, lineage-aware saturation, residual targeting, external evaluator separation, and semantic stopping one at a time.

The strongest evidence would show that each ablation selectively increases the failure mode predicted by the theory.

## 8. Semantic novelty verdict

Retained theory-level objects after deduplication:

1. `RAKL_EPISTEMIC_STATE_VECTOR` — a single explicit state joining atlas, survivors/identified sets, obstructions, fibers, evidence, negative history, and saturation.
2. `AUTHORITY_GATED_UPDATE_CALCULUS` — proposer output and canonical authority are separate transition channels.
3. `RAKL_THEORY_PROOF_OBLIGATION_SET` — formal/executable invariants explicitly separated from empirical claims.
4. `METHOD_LEVEL_NOVELTY_ENVELOPE` — novelty is claimed for the integrated transition discipline, not inherited ingredients.
5. `PROCESS_LEVEL_EPISTEMIC_EVALUATION_PROGRAM` — benchmark the research-state transitions that outcome-only agent evaluation can miss.
6. `NOVELTY_FALSIFICATION_REGISTRY` — a pre-cutoff semantically equivalent prior method is an explicit refuter, not a citation to be rhetorically distinguished after the fact.

Existing Apple/atlas, saturation, Self-RAKL, and evaluator-integrity concepts are **reorganized and formalized**, not double-counted as new discoveries.

Therefore:

```text
RAKL_METHOD = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

## 9. Open meta-fibers

This round opens:

- `META_N030_FORMAL_EPISTEMIC_STATE_AND_UPDATE`
- `META_N031_THEORY_TO_BENCHMARK_IDENTIFIABILITY`
- `META_N032_ADVERSARIAL_METHOD_NOVELTY_REVIEW`
- `META_N033_PROCESS_LEVEL_SCIENTIFIC_REASONING_BENCHMARK`
- `META_N034_HISTORICAL_TIME_CUTOFF_CONTAMINATION_CONTROL`

None changes the Constitution.

## 10. Next discriminators

Highest-value sequence:

1. **N032** — conduct an independent closest-work equivalence review using the frozen claim registry; attempt to refute method-level novelty.
2. **N030** — turn PO-1 through PO-9 into precise definitions/propositions and machine-checkable invariants where possible.
3. **N031/N033** — freeze theory-discriminating benchmark worlds before tuning RAKL to them.
4. **N034** — construct historical time-cutoff tasks with contamination audits.
5. Only after these are stable, draft the paper's headline abstract/results claims.

Outcome instructions:

- **positive**: narrow the novelty claim to exactly what survives semantic-equivalence review and preregister its predicted empirical effects;
- **null**: if RAKL controls do not improve predicted process metrics, preserve the null and weaken the method claim;
- **refuted**: if an equivalent prior method is found, record it as superseding novelty evidence and reposition RAKL as an implementation/extension;
- **partial-ID**: if prior art overlaps some but not all components, publish a scoped contribution matrix rather than a binary novelty claim;
- **blocked**: if full texts/code needed for equivalence cannot be accessed, mark those cells unknown and do not infer absence;
- **transport**: source/API failures change no novelty conclusion and should be retried without counting as an independent flat research round.
