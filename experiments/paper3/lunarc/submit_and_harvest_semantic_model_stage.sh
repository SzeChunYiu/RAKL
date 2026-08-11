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
# mandatory immediately after the stage job completes, writes a subject-freeze
# pin receipt, and refuses to run if the local origin/main tip moves during the
# window.
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
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Prefer the checkout copy so a merged FS9 tree uses its own helpers.
if [[ -f "$REPO/experiments/paper3/lunarc/subject_freeze_window.sh" ]]; then
  # shellcheck source=/dev/null
  source "$REPO/experiments/paper3/lunarc/subject_freeze_window.sh"
else
  # shellcheck source=/dev/null
  source "$HERE/subject_freeze_window.sh"
fi
SUBMIT="$REPO/experiments/paper3/lunarc/submit_semantic_model_stage.sh"
HARVEST="$REPO/experiments/paper3/lunarc/harvest_semantic_descriptor.sh"

cd "$REPO"
rakl_assert_subject_frozen "$EXPECTED_REPO_SHA" "pre_submit"

PIN="$(rakl_write_subject_freeze_pin "$EXPECTED_REPO_SHA" "MODEL_STAGE_SUBMIT_THROUGH_HARVEST")"
echo "FREEZE_WINDOW_OPEN expected=${EXPECTED_REPO_SHA} pin=${PIN}" >&2
echo "FREEZE_WINDOW_RULE no_git_fetch_until_harvest_exits" >&2

JOB_ID="$("$SUBMIT" "$EXPECTED_REPO_SHA")"
JOB_ID="${JOB_ID##*$'\n'}"
[[ "$JOB_ID" =~ ^[0-9]+$ ]]
rakl_write_subject_freeze_pin "$EXPECTED_REPO_SHA" "MODEL_STAGE_RUNNING" "$JOB_ID" >/dev/null
echo "STAGE_JOB_ID=${JOB_ID}" >&2

rakl_wait_slurm_completed "$JOB_ID" "$EXPECTED_REPO_SHA" "stage"
rakl_assert_subject_frozen "$EXPECTED_REPO_SHA" "pre_harvest"
"$HARVEST" model-stage "$JOB_ID"
rakl_assert_subject_frozen "$EXPECTED_REPO_SHA" "post_harvest"
rakl_write_subject_freeze_pin "$EXPECTED_REPO_SHA" "MODEL_STAGE_HARVESTED" "$JOB_ID" >/dev/null

HARVEST_PATH="$RECEIPT_ROOT/harvest-model-stage-${JOB_ID}.json"
test -f "$HARVEST_PATH"
echo "FREEZE_WINDOW_CLOSED harvest=${HARVEST_PATH}" >&2
echo "$JOB_ID"
