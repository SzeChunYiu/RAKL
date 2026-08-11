#!/usr/bin/env bash
# Submit the Paper-III model-stage job and harvest it inside one subject freeze window.
#
# Process fix for issue #144: a completed one-shot stage receipt is only harvestable
# while HEAD == refs/remotes/origin/main == expected_repo_sha. Once local
# refs/remotes/origin/main advances (usually via git fetch after mainline merges),
# harvest fails closed with origin_main_sha_mismatch / exact_checkout_sha_mismatch
# and the promoted asset is stranded by the one-shot guard.
#
# This wrapper does NOT relax that equality predicate. It makes stage harvest
# mandatory immediately after the stage job completes, and refuses to run if the
# local origin/main tip moves during the window.
#
# Freeze-window rules (submit through harvest exit):
#   1. Do not run `git fetch` / `git remote update` / any command that rewrites
#      refs/remotes/origin/main.
#   2. Keep the FS9 checkout clean and pinned to EXPECTED for the whole window.
#   3. Prefer this chain over a later-session harvest of a stale stage job id.
#
# usage: submit_and_harvest_semantic_model_stage.sh <exact-clean-merged-repository-sha>
set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9a-f]{40}$ ]]; then
  echo "usage: $0 <exact-clean-merged-repository-sha>" >&2
  exit 64
fi

EXPECTED_REPO_SHA="$1"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper3
REPO="$ROOT/repo"
RECEIPT_ROOT="$ROOT/semantic_descriptor_v1/receipts"
SUBMIT="$REPO/experiments/paper3/lunarc/submit_semantic_model_stage.sh"
HARVEST="$REPO/experiments/paper3/lunarc/harvest_semantic_descriptor.sh"
POLL_SECONDS="${RAKL_STAGE_POLL_SECONDS:-10}"
MAX_POLLS="${RAKL_STAGE_MAX_POLLS:-360}"

cd "$REPO"

assert_subject_frozen() {
  local label="$1"
  local head origin_main dirty
  head="$(git rev-parse HEAD)"
  origin_main="$(git rev-parse refs/remotes/origin/main)"
  dirty="$(git status --porcelain --untracked-files=all || true)"
  if [[ "$head" != "$EXPECTED_REPO_SHA" ]]; then
    echo "freeze_window_broken:${label}:exact_checkout_sha_mismatch:${head}" >&2
    exit 78
  fi
  if [[ "$origin_main" != "$EXPECTED_REPO_SHA" ]]; then
    echo "freeze_window_broken:${label}:origin_main_sha_mismatch:${origin_main}" >&2
    exit 78
  fi
  if [[ -n "$dirty" ]]; then
    echo "freeze_window_broken:${label}:checkout_dirty" >&2
    exit 78
  fi
}

# Refuse to start if origin/main is already past the requested subject.
assert_subject_frozen "pre_submit"

echo "FREEZE_WINDOW_OPEN expected=${EXPECTED_REPO_SHA}" >&2
echo "FREEZE_WINDOW_RULE no_git_fetch_until_harvest_exits" >&2

JOB_ID="$("$SUBMIT" "$EXPECTED_REPO_SHA")"
JOB_ID="${JOB_ID##*$'\n'}"
[[ "$JOB_ID" =~ ^[0-9]+$ ]]

echo "STAGE_JOB_ID=${JOB_ID}" >&2

for ((i = 1; i <= MAX_POLLS; i++)); do
  assert_subject_frozen "poll_${i}"
  STATE="$(sacct -j "$JOB_ID" -n -X -o State --parsable2 | head -1 | tr -d '[:space:]')"
  echo "poll=${i} state=${STATE}" >&2
  case "$STATE" in
    COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF_MEMORY|NODE_FAIL|BOOT_FAIL|DEADLINE)
      break
      ;;
    ""|PENDING|RUNNING|CONFIGURING|COMPLETING|RESIZING|SUSPENDED)
      sleep "$POLL_SECONDS"
      ;;
    *)
      echo "unexpected_slurm_state:${STATE}" >&2
      exit 75
      ;;
  esac
done

STATE="$(sacct -j "$JOB_ID" -n -X -o State --parsable2 | head -1 | tr -d '[:space:]')"
if [[ "$STATE" != "COMPLETED" ]]; then
  echo "stage_job_not_completed:${JOB_ID}:${STATE}" >&2
  exit 76
fi

assert_subject_frozen "pre_harvest"
"$HARVEST" model-stage "$JOB_ID"
assert_subject_frozen "post_harvest"

HARVEST_PATH="$RECEIPT_ROOT/harvest-model-stage-${JOB_ID}.json"
test -f "$HARVEST_PATH"
echo "FREEZE_WINDOW_CLOSED harvest=${HARVEST_PATH}" >&2
echo "$JOB_ID"
