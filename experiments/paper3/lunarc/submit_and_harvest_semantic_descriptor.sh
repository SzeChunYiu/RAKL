#!/usr/bin/env bash
# Submit the Paper-III descriptor job and harvest it inside one subject freeze window.
#
# Companion to submit_and_harvest_semantic_model_stage.sh for issue #144.
# Keeps HEAD == refs/remotes/origin/main == expected_repo_sha for descriptor
# submit → queue exit → post-chronology harvest. Does not relax CONTRACT_V1
# equality and does not modify bound submit/harvest scripts.
#
# usage:
#   submit_and_harvest_semantic_descriptor.sh \
#     <exact-clean-merged-repository-sha> \
#     <passed-model-stage-job-id> \
#     <pre-descriptor-zero-label-observation.json> \
#     <post-descriptor-label-chronology.json>
set -euo pipefail

if [[ $# -ne 4 || ! "$1" =~ ^[0-9a-f]{40}$ || ! "$2" =~ ^[0-9]+$ ]]; then
  echo "usage: $0 <exact-clean-merged-repository-sha> <passed-model-stage-job-id> <pre-zero-label.json> <post-label-chronology.json>" >&2
  exit 64
fi

EXPECTED_REPO_SHA="$1"
STAGE_JOB_ID="$2"
PRE_OBS="$(realpath "$3")"
POST_CHRONO="$(realpath "$4")"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper3
REPO="$ROOT/repo"
RECEIPT_ROOT="$ROOT/semantic_descriptor_v1/receipts"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$REPO/experiments/paper3/lunarc/subject_freeze_window.sh" ]]; then
  # shellcheck source=/dev/null
  source "$REPO/experiments/paper3/lunarc/subject_freeze_window.sh"
else
  # shellcheck source=/dev/null
  source "$HERE/subject_freeze_window.sh"
fi
SUBMIT="$REPO/experiments/paper3/lunarc/submit_semantic_descriptor.sh"
HARVEST="$REPO/experiments/paper3/lunarc/harvest_semantic_descriptor.sh"

test -f "$PRE_OBS"
test -f "$POST_CHRONO"

cd "$REPO"
rakl_assert_subject_frozen "$EXPECTED_REPO_SHA" "pre_descriptor_submit"
rakl_write_subject_freeze_pin "$EXPECTED_REPO_SHA" "DESCRIPTOR_SUBMIT_THROUGH_HARVEST" "$STAGE_JOB_ID" >/dev/null
echo "FREEZE_WINDOW_OPEN expected=${EXPECTED_REPO_SHA} phase=DESCRIPTOR parent_stage=${STAGE_JOB_ID}" >&2
echo "FREEZE_WINDOW_RULE no_git_fetch_until_harvest_exits" >&2

JOB_ID="$("$SUBMIT" "$EXPECTED_REPO_SHA" "$STAGE_JOB_ID" "$PRE_OBS")"
JOB_ID="${JOB_ID##*$'\n'}"
[[ "$JOB_ID" =~ ^[0-9]+$ ]]
rakl_write_subject_freeze_pin "$EXPECTED_REPO_SHA" "DESCRIPTOR_RUNNING" "$JOB_ID" >/dev/null
echo "DESCRIPTOR_JOB_ID=${JOB_ID}" >&2

rakl_wait_slurm_completed "$JOB_ID" "$EXPECTED_REPO_SHA" "descriptor"
rakl_assert_subject_frozen "$EXPECTED_REPO_SHA" "pre_descriptor_harvest"
"$HARVEST" descriptor "$JOB_ID" "$POST_CHRONO"
rakl_assert_subject_frozen "$EXPECTED_REPO_SHA" "post_descriptor_harvest"
rakl_write_subject_freeze_pin "$EXPECTED_REPO_SHA" "DESCRIPTOR_HARVESTED" "$JOB_ID" >/dev/null

HARVEST_PATH="$RECEIPT_ROOT/harvest-descriptor-${JOB_ID}.json"
test -f "$HARVEST_PATH"
echo "FREEZE_WINDOW_CLOSED harvest=${HARVEST_PATH}" >&2
echo "$JOB_ID"
