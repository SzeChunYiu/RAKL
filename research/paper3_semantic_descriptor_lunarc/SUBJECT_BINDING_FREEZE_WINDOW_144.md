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
the equality predicate above for that stage's `expected_repo_sha`. The same
window covers descriptor submit through descriptor harvest when chaining both
phases.

Covered interval: **stage submit through stage-harvest exit** (and, when chaining
descriptor, through descriptor harvest exit as well).

During the window:

1. Do **not** `git fetch`, `git remote update`, or otherwise rewrite
   `refs/remotes/origin/main`.
2. Keep `HEAD` pinned to the bound subject; do not check out another commit.
3. Keep the tree clean.
4. Prefer the chain wrappers, which write a `subject-freeze-pin-<sha>.json`
   receipt, poll SLURM while re-asserting equality, and harvest before returning:
   - `experiments/paper3/lunarc/submit_and_harvest_semantic_model_stage.sh`
   - `experiments/paper3/lunarc/submit_and_harvest_semantic_descriptor.sh`
   - shared helpers in `experiments/paper3/lunarc/subject_freeze_window.sh`

The equality predicate itself is unchanged and remains re-checked inside the
allocation. Bound `CONTRACT_V1.json` scripts are not modified.

## Current executed subjects (process evidence only)

| Subject | Stage | Descriptor | Notes |
|---|---|---|---|
| `0c5384e8…` | `3476291` | `3476296` | Canonical A1 / PR #159 |
| `787c7e00…` | `3476519` | `3476529` | Later subject rebind; not A1 redo |

Do not restage again unless intentionally validating a new subject or this
freeze-window wrapper after merge.

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
STAGE_JOB=<id printed by the stage chain>
PRE_OBS=/path/to/fresh-zero-label-observation.json
POST_CHRONO=/path/to/post-descriptor-chronology.json
# Create PRE_OBS before submit; create POST_CHRONO after descriptor completes
# if using the split submitter. The descriptor chain below expects both paths
# up front only when POST_CHRONO already exists; otherwise submit, wait, write
# POST_CHRONO, then harvest manually still inside the freeze window.
bash experiments/paper3/lunarc/submit_and_harvest_semantic_descriptor.sh \
  "$EXPECTED" "$STAGE_JOB" "$PRE_OBS" "$POST_CHRONO"
```

When `POST_CHRONO` cannot exist before the descriptor finishes, keep the freeze
window open manually:

```bash
DESC_JOB=$(bash experiments/paper3/lunarc/submit_semantic_descriptor.sh "$EXPECTED" "$STAGE_JOB" "$PRE_OBS")
# wait for COMPLETED without git fetch; write POST_CHRONO; then:
bash experiments/paper3/lunarc/harvest_semantic_descriptor.sh descriptor "$DESC_JOB" "$POST_CHRONO"
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
