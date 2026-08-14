# Paper IV — Structural Learning Mechanics (conditional research lane)

## 2026-08-14 rescope: negative-results / metrology claims object

`main.tex` is now a **negative-results and metrology report**, built only on preserved
receipts. Primary contribution: the oracle-ceiling instrument-admissibility method
(`research/paper4_instrument_admissibility_v1/`) — an equal-budget allocation comparison
is uninformative when its achievable ceiling sits below its own registered MDE, a defect
invisible to conventional power analysis (CIs ≈0.0016 wide looked healthy while the
rigorous ceiling upper bound was 0.0246 against a 0.05 gate). Empirical core: the
preserved adaptive-v1 development negative with its frozen attribution, including the
falsified pre-registered prediction P1. Closing demonstration: the licensed successor
instrument and the marginal-gain challenger (`research/paper4_marginal_gain_challenger_v1/`),
including the falsified prediction P6 (the v1 policy also wins in a licensed instrument —
the parent negative was policy×instrument-conditional).

**This rescope does not reverse #462.** The original standalone positive-claims paper was
rejected there and stays rejected; the rescoped manuscript is a different claims object and
asserts nothing that gate governs. No training-policy authority moves; every preserved
negative stays verbatim. The remainder of this README describes the conditional research
lane, which continues unchanged below.

---

Paper IV remains a **conditional publication slot**, not yet an authorized standalone positive paper.
The historical Phase-0/1 v1 blanket negative is preserved as an **instrument artifact** (degenerate
generator) and is not the current evidence state. Under the strict ORION closure rule, a failed
adaptive hypothesis is also not allowed to remain the active training-policy dependency: the
strongest safe promoted parent remains active until an adaptive successor earns promotion.

## Current evidence state

The corrected Phase-0/1 v2 A100 rerun (`research/paper4_phase1_results_v2/`) uses varied,
length-matched train/probe instances with executable gold and disjoint partitions. On the frozen
Qwen2.5 ladder:

- 7B `state_reachability` -> `MECHANISM_SIGNAL_PRESENT`;
  principle mastery at exposure 2, late same-structure gain 0.0, unsaturated-coordinate late gain +0.25;
- `sequence_composition` -> `NO_STATE_DEPENDENT_RESIDUAL`;
- `balance_conservation` -> `REPETITION_REMAINS_VALUABLE` at 7B;
- lower model/family cells preserve their registered repetition/model-floor terminals.

The 7B state-reachability signal establishes a real learner-conditioned structural coordinate. It
does **not** by itself establish that an adaptive allocation policy is better than static structural
curation.

## Active training-policy authority

The vector `TrainingProjectionSnapshot` and fail-closed allocator remain implemented mechanics, but
RSHEA now separates **having an adaptive candidate** from **authorizing it as the active default**.
`src/rakl/training_policy_authority.py` makes `STATIC_STRUCTURAL` the active governed parent unless
an external fresh receipt has terminal `ADAPTIVE_RESIDUAL_SUPPORTED` and independently passes:

- fresh assurance;
- residual beyond the strongest fair adaptive parent;
- all registered hard-harm bounds; and
- full selection/probing/training overhead accounting.

A `RESOURCE_BLOCKED`, null, parent-win or harm receipt therefore never activates adaptive training,
and the scheduler cannot self-authorize from its own telemetry. This training-policy authority is
separate from scientific authority.

## RSHEA development failure and root cause

A fresh model-free development stress panel was frozen over 384 world-replicates spanning early
principle saturation, composition/boundary/representation/transfer lag and retention-sensitive
regimes. Under equal 48-example budgets, the current aggressive adaptive-v1 policy lost to the
static structural parent:

- balanced-mastery `Adaptive - Static = -0.01661`, bootstrap 95% CI
  `[-0.01740, -0.01583]`;
- hard-safety-minimum `Adaptive - Static = -0.05033`, bootstrap 95% CI
  `[-0.05782, -0.04311]`.

The failure is preserved as
`DEVELOPMENT_NEGATIVE_ADAPTIVE_OVERCONCENTRATES__STATIC_PARENT_RETAINS_DEFAULT`.
The localized mechanism is over-concentration: after the repetition floor, v1 commits the remaining
batch to one weakest coordinate for a whole allocation round, allowing principle/retention erosion
in saturation/forgetting regimes. We do **not** weaken the evaluator or relabel this result.
Instead, the active-default authority is revoked from adaptive-v1 and the static structural parent
remains the production-safe policy. Any future adaptive-v2 must be a versioned successor and beat
that parent under a fresh gate.

## Frozen Phase-2 causal experiment and execution successor

`research/paper4_phase2_v1/PROTOCOL_V3.json` and `INFERENCE_PLAN.json` freeze, before outcomes:

- exact Qwen2.5-7B revision `a09a35458c702b33eeacc393d103063234e8bc28`;
- Phase-1-equivalent LoRA/training semantics;
- five fair arms: uniform random, semantic diversity, strongest model-aware NLL parent,
  Static RAKL structural mix, Adaptive RAKL structural allocator;
- 48 final training examples per arm, six allocation rounds, disjoint selection probes and
  384-case fresh assurance panel;
- primary `Adaptive - Static` MDE 0.05, paired bootstrap/sign-flip + Holm inference;
- hard composition/boundary/hostile/retention harm bounds and full probe/training resource accounting;
- fixed stopping and no smaller-model / changed-quantization / changed-MDE rescue after outcomes.

RSHEA preserved several **pre-outcome instrument failures** rather than weakening the gates:
incomplete early freeze, Phase-1 loading-semantics mismatch, a revision-key schema alias, and
exact rendered-prompt overlap across train/selection/assurance. The current instrument passes the
exact-head dry-run leakage gate. See `research/paper4_phase2_v1/INSTRUMENT_HISTORY.json`.

The earlier current-session `RESOURCE_BLOCKED` receipt was traced to execution portability, not to
the scientific policy comparison: the Phase-1 programme had already staged the exact 7B revision on
LUNARC A100, while the Phase-2 runner expected a Hugging Face `snapshot_download` cache. The
versioned successor `experiments/training_ladder/run_phase2_v1_lunarc.sbatch` now exposes that same
staged exact revision through an offline Hugging Face cache layout and runs the unchanged frozen
Phase-2 module on the existing `gpua100` route. `submit_phase2_v1_lunarc.sh` binds the repository
subject SHA before submission. No model, LoRA, seed, MDE, evaluator, harm gate or arm is changed.

The five-arm 7B causal outcome is still **not yet a scientific result** until that external job is
actually executed and harvested. The important ORION difference is that `RESOURCE_BLOCKED` is no
longer the active mechanic: static structural allocation is active, while the exact adaptive
experiment has a concrete successor path to earn or lose promotion.

## Standalone Paper-IV gate

Issue #462 remains sovereign. `PAPER_IV_JUSTIFIED` still requires:

1. a distinguishable/material Adaptive-vs-Static Phase-2 result;
2. residual value beyond the strongest model-/transfer-/skill-aware parents;
3. acceptable forgetting/composition/cost;
4. a specifically structural mechanism that generalizes across fresh structural families and
   more than one model/checkpoint regime;
5. enough distinct content to satisfy the anti-salami boundary relative to the other mechanics papers/capstone.

Until those conditions are met, this directory is a conditional design/mechanism lane rather than
a publishable standalone adaptive-efficacy paper. ORION itself does not depend on that unproven
adaptive extension: its active training-policy node is the promoted static structural parent.
