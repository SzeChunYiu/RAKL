# Paper III LUNARC subject-binding freeze window (issue #144)

Status: `PROCESS_FIX / NO_EVALUATOR_CHANGE / NO_PREDICATE_RELAXATION / A1_ALREADY_COMPLETE`

## Defect

`validate_repo_and_contract` requires, for every submit/runtime/harvest bound to
`<expected>`:

```text
git rev-parse HEAD                     == <expected>
git rev-parse refs/remotes/origin/main == <expected>
git status --porcelain --untracked-files=all   empty
```

Model staging is one-shot (`final_model_path_already_exists`). Descriptor submit
additionally requires the stage harvest receipt to carry the same
`expected_repo_sha`.

Once local `refs/remotes/origin/main` advances past the staging subject — usually
because a later session ran `git fetch` after unrelated mainline merges — stage
harvest fails closed (`origin_main_sha_mismatch` / `exact_checkout_sha_mismatch`)
and the promoted asset is stranded. That fail-closed behaviour is correct; the
process defect is that stage → harvest was documented as resumable across
sessions without stating the freeze deadline.

## Non-goals (deliberately rejected here)

This process fix does **not**:

- relax `HEAD == origin/main` to ancestry;
- re-freeze or supersede `CONTRACT_V1.json`;
- rewrite `refs/remotes/origin/main`;
- make staging overwrite an already-promoted model path;
- redo section A1 of issue #138.

Canonical A1 evidence remains jobs `3476291` / `3476296` at subject
`0c5384e84ac62ab0fe14a7f728a0f68ffd3f2186` (PR #159).

## Freeze-window rule

A stage receipt is harvestable only while the local FS9 checkout still satisfies
the equality predicate above for that stage's `expected_repo_sha`.

Covered interval: **stage submit through stage-harvest exit** (and, when chaining
descriptor, through descriptor harvest exit as well).

During the window:

1. Do **not** `git fetch`, `git remote update`, or otherwise rewrite
   `refs/remotes/origin/main`.
2. Keep `HEAD` pinned to the bound subject; do not check out another commit.
3. Keep the tree clean.
4. Prefer
   `experiments/paper3/lunarc/submit_and_harvest_semantic_model_stage.sh`, which
   submits, polls, re-asserts the freeze predicate, and harvests before returning.

The equality predicate itself is unchanged and remains re-checked inside the
allocation.

## When a restage is required

Restage only if a new bound subject must be executed (process validation of this
wrapper, or a future lane that intentionally rebinds). Preserve any prior
promoted model under `assets/superseded/stage-<job>-<revision>/` before clearing
the contract `model_dir`. Do **not** restage merely because main moved after a
successful A1 harvest.

## Exact next submit commands (FS9)

Connection:

```bash
ssh billy-old 'ssh lunarc'
```

Root: `/projects/hep/fs9/users/scyiu/RAKL-paper3`

### Preferred: freeze-window stage → harvest

```bash
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper3
REPO=$ROOT/repo
cd "$REPO"
# Pin without fetching mid-window. Only fetch *before* opening the window.
git fetch origin main
EXPECTED="$(git rev-parse refs/remotes/origin/main)"
git checkout --detach "$EXPECTED"
test -z "$(git status --porcelain --untracked-files=all)"
# If model_dir already exists from a prior promotion, supersede it first.
bash experiments/paper3/lunarc/submit_and_harvest_semantic_model_stage.sh "$EXPECTED"
```

### Then descriptor (still inside an unbroken freeze window)

```bash
# Create a fresh payload-free ZERO_LABELS_OBSERVED chronology after contract
# zero_label_observed_at_utc, then:
STAGE_JOB=<id printed by the chain>
OBS=/path/to/fresh-zero-label-observation.json
bash experiments/paper3/lunarc/submit_semantic_descriptor.sh "$EXPECTED" "$STAGE_JOB" "$OBS"
# wait for COMPLETED, then post-descriptor chronology + harvest:
bash experiments/paper3/lunarc/harvest_semantic_descriptor.sh descriptor <DESC_JOB> /path/to/post-descriptor-chronology.json
```

### Anti-pattern (the #144 failure mode)

```bash
# session 1
bash experiments/paper3/lunarc/submit_semantic_model_stage.sh "$EXPECTED"
# ... hours later, after main advanced and someone fetched ...
bash experiments/paper3/lunarc/harvest_semantic_descriptor.sh model-stage <STAGE_JOB>
# → HARVEST_MODEL_STAGE_CANNOT_CHECK with origin_main_sha_mismatch
```

## Authority boundary

Framework/execution-process documentation and a non-bound chain wrapper only.
No semantic-descriptor scientific claim, no confirmatory-gate result, no training
authorization, and no evaluator/schema/predicate change.
