# Paper IV generator-defect correction

**Status:** load-bearing correction to the interpretation of the executed Phase-0/1 v1 packet.  
**Evidence cutoff:** repository main commit `8beb877d0f3ef3504b5ca2fdd02fb99c75ed4c38` and its frozen root-cause artifacts.  
**Publication rule:** the v1 run is **negative instrument history**, not evidence for or against the learner-conditioned structural-allocation mechanism.

## What changed

The earlier manuscript prose described the frozen Qwen2.5 0.5B–7B Phase-0/1 v1 run as a “supported negative” and localized the obstruction to a model capability floor. Subsequent root-cause analysis invalidated that inference.

The v1 generator exposed only **two unique rendered inputs per structural family**: within a family, all valid cases were identical and all invalid cases were identical. Stronger training still collapsed to a constant predictor on the affected family. In addition, the apparent `state_reachability` signal was confounded because valid inputs contained more edges than invalid inputs. The frozen output terminals remain historical observations, but they cannot identify structural rule learning, a state-dependent residual, repetition value, or a model capability floor.

## Correct interpretation

```text
V1_PHASE1_STATUS=INSTRUMENT_GENERATOR_DEFECT
MECHANISM_SIGNAL=CANNOT_CHECK
MODEL_CAPABILITY_FLOOR=CANNOT_CHECK_FROM_V1
NO_STATE_DEPENDENT_RESIDUAL=CANNOT_CHECK_FROM_V1
REPETITION_REMAINS_VALUABLE=CANNOT_CHECK_FROM_V1
PHASE2_ADAPTIVE_SCHEDULER=NOT_OPEN
```

The residual hypothesis is unresolved.

## Required repair before a valid Phase-1 conclusion

The next generator must provide:

- varied instances within every structural family;
- length-matched valid/invalid cases so trivial surface length cannot predict the label;
- disjoint instance-level train and probe partitions;
- a preregistered learnability positive-control gate before interpreting a null residual;
- frozen chronology, hashes and unchanged no-authority semantics.

## Build enforcement

`scripts/repair_paper4_generator_defect.py` fail-closed patches the stale v1 interpretation in the manuscript checkout used by the unified hardening workflow. CI fails if any registered “supported negative/capability-floor” wording survives. The hardening artifact archives the exact patched `PAPER4_PATCHED_MAIN.tex`, compiled PDF, log, extracted text and page renders.

This correction does not erase the v1 packet. It preserves it as negative history while preventing an invalid causal interpretation from entering the publication record.
