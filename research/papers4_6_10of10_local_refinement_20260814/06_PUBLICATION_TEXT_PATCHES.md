# Reader-facing manuscript patches

These are wording/evidence-synchronization repairs. They must not be used to invent a result.

## Paper IV — apply now

File:

`publication/papers/paper-04-structural-learning-mechanics/main.tex`

### 1. Fix stale experimental status

Current reader-facing abstract/status still says the corrected v2 full ladder is pending. That is stale relative to the current Paper-IV README/closure addendum.

Replace that status with language equivalent to:

> The historical Phase-0/1 v1 blanket negative is retained only as invalid-instrument history. The corrected v2 A100 ladder has now executed on the frozen Qwen2.5 scale family. At 7B, `state_reachability` yields `MECHANISM_SIGNAL_PRESENT`: principle mastery is reached early while a later unsaturated structural coordinate still has positive marginal value; `sequence_composition` yields `NO_STATE_DEPENDENT_RESIDUAL`; `balance_conservation` retains a repetition-value terminal. These results establish a scoped learner-conditioned structural signal, not an adaptive-allocation efficacy claim. A model-free development stress subsequently found the current aggressive Adaptive-v1 scheduler worse than Static Structural because it over-concentrated allocation, so Static remains the governed active parent. The exact five-arm 7B Phase-2 Adaptive-vs-Static/strongest-parent experiment is frozen and execution-ready but has no scientific outcome until its external job is run and harvested.

Do not copy the exact numeric Phase-2 result into the paper until it exists.

### 2. Narrow the saturation proposition

Replace the proposition title/claim with:

> **Checkpoint-bound saturation need not be invariant under training.** A saturation receipt valid for `(R_t, theta_t)` does not in general license the same decision at `(R_t, theta_{t+1})`; a parameter update may change one or more frozen probe outputs or the allocation decision. Therefore the receipt must be checkpoint-bound and staleable. This does not assert that every nonzero parameter update changes every registered probe or allocation.

Proof idea:

```text
pi_train depends on theta through the registered probe outputs.
There exist admissible parameter updates for which those outputs change.
Therefore invariance under arbitrary updates is not guaranteed.
Checkpoint binding is required.
```

Do **not** claim a nontrivial update necessarily changes a probe.

### 3. Replace universal scalar impossibility

Replace “no scalar mastery score is a sufficient statistic” with:

> **Many-to-one scalarization can be policy-insufficient.** Let `phi(M)` be a scalarization of the mastery vector. If there exist two mastery states `M1 != M2` requiring different allocation actions but `phi(M1)=phi(M2)`, then `phi` is insufficient for that policy. Coordinate averaging is one concrete failure mode. The vector is therefore the canonical representation in this work; a scalar projection may be used only when its policy sufficiency is separately established.

This is the exact quantifier repair required by issue #517.

### 4. Update contribution boundary

The Paper-IV novelty statement should **not** claim generic adaptive curriculum, missing-skill targeting, saturation-aware training, or model-aware data selection.

Headline residual:

```text
explicit directional/QoI/boundary-scoped structural identities
+ learner-specific vector mastery over principle/composition/boundary/representation/transfer/retention
+ noncompensatory safety/retention
+ strongest-parent causal comparison
+ exact train-to-inference structural identity reuse
```

## Paper V — patch now only where evidence already exists

File:

`publication/papers/paper-05-verified-discovery-in-mathematics/main.tex`

Safe immediate editorial changes:

1. make “LLM” a proposer example, not the defining architecture object;
2. state the primary architecture as **executor-independent mathematical-research assurance**;
3. keep five coordinates explicit: specification, truth, novelty, value, verifier trust;
4. add the finite known-world scalarization counterexample as a small architecture-conformance result only after exact branch tests pass;
5. retain VTG as proposal/search infrastructure whose efficiency is unearned until issue #528 executes;
6. do not add an autonomous-mathematician/discovery-success claim.

Suggested future title **after mechanization/hostile evidence is green**:

> `Verified Mathematical Discovery: Executor-Independent Assurance for Specification, Proof, Novelty and Verifier Trust`

Do not use the stronger title as a claim substitute before the Lean/hostile gates.

## Paper VI — apply the closure wording repair now

File:

`publication/papers/paper-06-rakl-scientific-research-engine/source/sections/14_manuscript_saturation.tex`

Current text says all thirteen registered mechanics were closed at the manuscript cutoff. Preserve the historical fact but bind it explicitly to its old roster.

Replace with wording equivalent to:

> The historical closure ledger recorded all thirteen mechanics in its exact cutoff roster as `CLOSED_AT_CUTOFF`, while also setting `GLOBAL_COMPLETENESS_CLAIMED=false`. This is a registry-relative historical certificate, not a present-tense claim about every later RAKL candidate. Subsequent framework-completion work registered additional pursuit-plane candidates, so current closure must be recomputed against a new exact mechanic-registry hash. An old certificate remains valid for its historical roster and cutoff but does not certify a later expanded roster.

Then define the new release form:

```text
ClosureCertificate(
  subject_sha,
  cutoff,
  mechanic_registry_hash,
  mechanic_ids,
  closed_mechanic_ids,
  GLOBAL_COMPLETENESS_CLAIMED=false
)
```

Reference `src/rakl/bounded_closure.py` only after branch CI passes and the module is accepted.

## Paper VI — evidence story

The final capstone should not present the architecture inventory as the primary result. After issue #588 executes, reorganize the empirical story around:

1. external-agent comparison frontier;
2. matched internal ablations;
3. explicit Orion losses;
4. one competitor-mechanic assimilation case;
5. fresh epoch-2 improvement or honest failure;
6. cost, validity, reproducibility and safety together.

## Global publication CI recommendation

Add a later single-writer build checker that rejects:

- manuscript numeric/status strings whose bound receipt changed;
- unbound implementation SHA/test count;
- current-tense “closed/ready/supported” claims whose registry/receipt hash is stale;
- historical paper-number namespace accidentally rewritten to publication-series-v2 identity;
- claims of independent human evidence when only AI/same-context review exists.

Do not auto-edit frozen historical artifacts. Fail the reader-facing build and require an explicit versioned manuscript patch.