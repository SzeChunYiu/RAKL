# Paper IV external A100 handoff

## Scientific question

Does the already-frozen Adaptive RAKL arm causally beat Static RAKL and survive the strongest-parent/harm/cost gates on the exact Qwen2.5-7B Phase-2 study?

**Do not substitute the new local structure-conditioned challenger into this experiment.** The current Phase-2 protocol was frozen before this branch and must remain unchanged.

## Exact audited subject

Use the already-audited repository subject:

```text
6d73ec7ffbc3928e5e56847316b7fe08446a1440
```

The execution transport itself checks all load-bearing frozen blobs. If a later subject is used, it must pass the same exact frozen-blob check; do not patch scientific files to make the preflight green.

## Preconditions

On LUNARC/A100 or equivalent environment with SLURM and the already staged exact model revision:

```text
Qwen/Qwen2.5-7B-Instruct
a09a35458c702b33eeacc393d103063234e8bc28
```

Repository default path expected by current script unless explicitly supplied:

```text
/projects/hep/fs9/users/scyiu/orion
```

## Commands

```bash
cd /projects/hep/fs9/users/scyiu/orion
git fetch --all --prune

SUBJECT=6d73ec7ffbc3928e5e56847316b7fe08446a1440

bash experiments/training_ladder/submit_and_harvest_phase2_v1_transport.sh \
  preflight "$SUBJECT" "$PWD"
```

The preflight must print:

```text
P4_PHASE2_EXECUTION_PREFLIGHT_PASS subject=<SUBJECT>
```

Then submit exactly once:

```bash
bash experiments/training_ladder/submit_and_harvest_phase2_v1_transport.sh \
  submit "$SUBJECT" "$PWD"
```

Record the emitted numeric `JOB_ID`. Do not open/inspect arm outcomes during execution.

After SLURM reports the job complete:

```bash
JOB_ID=<numeric job id>

bash experiments/training_ladder/submit_and_harvest_phase2_v1_transport.sh \
  harvest "$JOB_ID" "$SUBJECT" "$PWD"
```

The harvest path separates scheduler completion from the scientific terminal, re-computes the registered analysis, validates the data manifest/fresh assurance/resource accounting, and keeps standalone Paper-IV authorization false.

## Forbidden actions

Before the scientific terminal is frozen, do not:

- modify model/checkpoint/quantization;
- alter any arm;
- change MDE, sample size, bootstrap/sign-flip/Holm plan;
- lower a hard harm threshold;
- change train/selection/assurance partitions;
- swap the static or strongest-parent implementation;
- add the new `training_scheduler_challenger_v2` to the confirmatory experiment;
- retry with a new seed because the result is unfavorable;
- interpret `RESOURCE_BLOCKED` or scheduler failure as RAKL scientific failure;
- infer standalone Paper-IV publication authority from a raw positive flag.

## Result decision tree

### `ADAPTIVE_RESIDUAL_SUPPORTED`

1. Preserve raw bundle and canonical admission receipt.
2. Confirm active policy changes only through `training_policy_authority`.
3. Freeze and run issue #467: **exact train -> inference structural identity reuse** on fresh tasks.
4. Then freeze/run #468: cross-family and >=2 model/checkpoint regimes.
5. Paper IV becomes standalone only if issue #462 is satisfied after these results.

### `ADAPTIVE_RESIDUAL_SUPPORTED_HIGH_COST`

Do not call this a clean training-efficiency win. Static remains preferred unless the registered consumer accepts the explicit cost tradeoff under a separately frozen policy.

### `PARENT_MATCHES_OR_BEATS`

Preserve as a valid scientific result. Assimilate the parent only through the normal mechanic-research packet/fresh-assurance path. Narrow Paper IV to any residual structural/shared-substrate contribution that remains.

### `STATIC_EQUALS_ADAPTIVE`

The learner-conditioned allocation extension is unsupported on this powered test. Default to absorbing the conceptual material into Paper III / capstone unless a separately frozen successor asks a materially different question.

### `ADAPTIVE_HARMS_COMPOSITION_OR_RETENTION`

Reject adaptive activation even if the average capability metric improves. The harm is noncompensatory.

### `UNDERPOWERED`

Do not call null/no effect. Any power amendment must be a versioned pre-outcome successor.

### invalid / contaminated / resource blocked

Preserve the epoch and root-cause it. Repair only under a new protocol identity.

## Separate research successor on this branch

The new file

```text
src/rakl/training_scheduler_challenger_v2.py
```

repairs a distinct *software-mechanic* defect: global collapse of structural identity in the current marginal-gain challenger.

After the frozen Phase-2 result is safely terminal, another AI may build a new **development-only** packet for this structure-conditioned challenger. It must:

1. use the counterexample in `tests/test_training_scheduler_challenger_v2.py`;
2. compare v2 against production v1, marginal-gain v1, static structural, and strongest model/skill-aware parent where meaningful;
3. include >=3 heterogeneous structural identities/families;
4. use disjoint development and fresh-assurance seeds;
5. charge probing/selection overhead;
6. preserve candidate-level hard safety;
7. never reuse Phase-2 confirmatory outcomes to tune the successor;
8. never activate the successor without the external `ADAPTIVE_RESIDUAL_SUPPORTED`-style authority path.

## Paper-IV manuscript repairs that are safe regardless of Phase-2 sign

Apply issue #517's formal correction:

- saturation receipt at `theta_t` **need not** remain valid after a weight update; do not claim every nonzero update necessarily changes allocation/probes;
- replace universal “no scalar mastery score can be sufficient” with the precise claim that **any many-to-one scalarization that identifies policy-distinct mastery vectors is insufficient**; scalar projections are allowed only when policy sufficiency is separately established.

Also update the abstract/status box to reflect the already-completed corrected v2 Phase-0/1 evidence; it must no longer say the full v2 ladder is pending.