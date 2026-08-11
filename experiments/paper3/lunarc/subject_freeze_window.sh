#!/usr/bin/env bash
# Shared subject freeze-window helpers for Paper-III LUNARC chains (issue #144).
# Source this file; do not execute it directly.
#
# Does NOT relax HEAD == refs/remotes/origin/main == expected_repo_sha.
# Does NOT rewrite git refs. Bound CONTRACT_V1 scripts are left untouched.

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "source subject_freeze_window.sh; do not execute" >&2
  exit 64
fi

RAKL_PAPER3_ROOT="${RAKL_PAPER3_ROOT:-/projects/hep/fs9/users/scyiu/RAKL-paper3}"
RAKL_PAPER3_REPO="${RAKL_PAPER3_REPO:-$RAKL_PAPER3_ROOT/repo}"
RAKL_PAPER3_RECEIPT_ROOT="${RAKL_PAPER3_RECEIPT_ROOT:-$RAKL_PAPER3_ROOT/semantic_descriptor_v1/receipts}"
RAKL_FREEZE_POLL_SECONDS="${RAKL_FREEZE_POLL_SECONDS:-${RAKL_STAGE_POLL_SECONDS:-10}}"
RAKL_FREEZE_MAX_POLLS="${RAKL_FREEZE_MAX_POLLS:-${RAKL_STAGE_MAX_POLLS:-360}}"

rakl_assert_subject_frozen() {
  local expected="$1"
  local label="$2"
  local head origin_main dirty
  head="$(git -C "$RAKL_PAPER3_REPO" rev-parse HEAD)"
  origin_main="$(git -C "$RAKL_PAPER3_REPO" rev-parse refs/remotes/origin/main)"
  dirty="$(git -C "$RAKL_PAPER3_REPO" status --porcelain --untracked-files=all || true)"
  if [[ "$head" != "$expected" ]]; then
    echo "freeze_window_broken:${label}:exact_checkout_sha_mismatch:${head}" >&2
    return 78
  fi
  if [[ "$origin_main" != "$expected" ]]; then
    echo "freeze_window_broken:${label}:origin_main_sha_mismatch:${origin_main}" >&2
    return 78
  fi
  if [[ -n "$dirty" ]]; then
    echo "freeze_window_broken:${label}:checkout_dirty" >&2
    return 78
  fi
  return 0
}

rakl_write_subject_freeze_pin() {
  local expected="$1"
  local phase="$2"
  local job_id="${3:-}"
  mkdir -p "$RAKL_PAPER3_RECEIPT_ROOT"
  local out="$RAKL_PAPER3_RECEIPT_ROOT/subject-freeze-pin-${expected}.json"
  local tmp="${out}.tmp"
  local created
  created="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cat >"$tmp" <<EOF
{
  "schema_version": "paper3-subject-freeze-pin-v1",
  "created_at_utc": "${created}",
  "expected_repo_sha": "${expected}",
  "phase": "${phase}",
  "slurm_job_id": $( [[ -n "$job_id" ]] && printf '"%s"' "$job_id" || printf 'null' ),
  "no_git_fetch": true,
  "predicate": "HEAD == refs/remotes/origin/main == expected_repo_sha",
  "claim_boundary": "Operator freeze-window pin only; does not mint harvest or scientific authority and does not relax CONTRACT_V1 subject equality."
}
EOF
  mv "$tmp" "$out"
  echo "$out"
}

rakl_wait_slurm_completed() {
  local job_id="$1"
  local expected="$2"
  local label_prefix="$3"
  local i state
  for ((i = 1; i <= RAKL_FREEZE_MAX_POLLS; i++)); do
    rakl_assert_subject_frozen "$expected" "${label_prefix}_poll_${i}" || return $?
    state="$(sacct -j "$job_id" -n -X -o State --parsable2 | head -1 | tr -d '[:space:]')"
    echo "poll=${i} job=${job_id} state=${state}" >&2
    case "$state" in
      COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF_MEMORY|NODE_FAIL|BOOT_FAIL|DEADLINE)
        break
        ;;
      ""|PENDING|RUNNING|CONFIGURING|COMPLETING|RESIZING|SUSPENDED)
        sleep "$RAKL_FREEZE_POLL_SECONDS"
        ;;
      *)
        echo "unexpected_slurm_state:${state}" >&2
        return 75
        ;;
    esac
  done
  state="$(sacct -j "$job_id" -n -X -o State --parsable2 | head -1 | tr -d '[:space:]')"
  if [[ "$state" != "COMPLETED" ]]; then
    echo "job_not_completed:${job_id}:${state}" >&2
    return 76
  fi
  return 0
}
