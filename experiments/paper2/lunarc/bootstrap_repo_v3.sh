#!/bin/bash
# LUNARC login-host repository bootstrap for Paper 2 CPU staging V3.
# This script only prepares and attests an exact detached repository checkout.
set -euo pipefail

readonly GITHUB_REMOTE="https://github.com/SzeChunYiu/RAKL.git"
readonly DEFAULT_FS9_ROOT="/projects/hep/fs9/users/scyiu/RAKL-paper2"

usage() {
  cat >&2 <<'EOF'
usage: bootstrap_repo_v3.sh --expected-repo-sha SHA --receipt-output PATH [--fs9-root PATH]

No job is submitted and no model is executed. If repo/ already exists it must
already be the exact clean detached checkout requested by --expected-repo-sha.
EOF
}

expected_repo_sha=""
receipt_output=""
fs9_root="$DEFAULT_FS9_ROOT"
while (($#)); do
  case "$1" in
    --expected-repo-sha) expected_repo_sha="${2:-}"; shift 2 ;;
    --receipt-output) receipt_output="${2:-}"; shift 2 ;;
    --fs9-root) fs9_root="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 64 ;;
  esac
done

[[ "$expected_repo_sha" =~ ^[0-9a-f]{40}$ ]] || {
  echo "--expected-repo-sha must be an exact lowercase 40-hex commit SHA" >&2
  exit 64
}
[[ -n "$receipt_output" && -n "$fs9_root" ]] || { usage; exit 64; }
command -v git >/dev/null || { echo "git is required" >&2; exit 69; }
command -v python3 >/dev/null || { echo "python3 is required for atomic receipts" >&2; exit 69; }

repo_path="$fs9_root/repo"
candidate_path=""
observed_repo_sha=""
observed_repo_tree=""
checkout_clean=false
detached_head=false
repo_created=false
verdict="BOOTSTRAP_FAILURE"
failure="bootstrap_interrupted"
receipt_enabled=true

# Receipt generation is centralized in the EXIT trap so failures after argument
# validation are also preserved. os.replace is an atomic rename on the receipt's
# filesystem; fsync covers both the file and its containing directory.
write_receipt() {
  local exit_status="$1"
  local tmp_output
  mkdir -p "$(dirname "$receipt_output")"
  tmp_output="$(dirname "$receipt_output")/.bootstrap-receipt.$$.tmp"
  RAKL_RECEIPT_TMP="$tmp_output" \
  RAKL_RECEIPT_OUTPUT="$receipt_output" \
  RAKL_EXIT_STATUS="$exit_status" \
  RAKL_VERDICT="$verdict" \
  RAKL_FAILURE="$failure" \
  RAKL_EXPECTED_REPO_SHA="$expected_repo_sha" \
  RAKL_OBSERVED_REPO_SHA="$observed_repo_sha" \
  RAKL_OBSERVED_REPO_TREE="$observed_repo_tree" \
  RAKL_FS9_ROOT="$fs9_root" \
  RAKL_REPO_PATH="$repo_path" \
  RAKL_CANDIDATE_PATH="$candidate_path" \
  RAKL_GITHUB_REMOTE="$GITHUB_REMOTE" \
  RAKL_CHECKOUT_CLEAN="$checkout_clean" \
  RAKL_DETACHED_HEAD="$detached_head" \
  RAKL_REPO_CREATED="$repo_created" \
  python3 - <<'PY'
import datetime
import json
import os
from pathlib import Path

def flag(name: str) -> bool:
    return os.environ[name] == "true"

failure = os.environ["RAKL_FAILURE"]
receipt = {
    "schema_version": "paper2-repo-bootstrap-v3",
    "bootstrap_id": "PAPER2_CPU_V3_REPO_BOOTSTRAP",
    "observed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    "verdict": os.environ["RAKL_VERDICT"],
    "exit_status": int(os.environ["RAKL_EXIT_STATUS"]),
    "github_remote": os.environ["RAKL_GITHUB_REMOTE"],
    "fs9_root": os.environ["RAKL_FS9_ROOT"],
    "repo_path": os.environ["RAKL_REPO_PATH"],
    "candidate_path": os.environ["RAKL_CANDIDATE_PATH"] or None,
    "expected_repo_sha": os.environ["RAKL_EXPECTED_REPO_SHA"],
    "observed_repo_sha": os.environ["RAKL_OBSERVED_REPO_SHA"] or None,
    "observed_repo_tree": os.environ["RAKL_OBSERVED_REPO_TREE"] or None,
    "checkout_clean": flag("RAKL_CHECKOUT_CLEAN"),
    "detached_head": flag("RAKL_DETACHED_HEAD"),
    "repo_created": flag("RAKL_REPO_CREATED"),
    "failure": failure or None,
    "jobs_submitted": 0,
    "model_execution_performed": False,
    "evaluated_result_record_count": 0,
}
output = Path(os.environ["RAKL_RECEIPT_OUTPUT"])
tmp = Path(os.environ["RAKL_RECEIPT_TMP"])
payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
with tmp.open("x", encoding="utf-8") as handle:
    handle.write(payload)
    handle.flush()
    os.fsync(handle.fileno())
os.chmod(tmp, 0o600)
os.replace(tmp, output)
directory_fd = os.open(output.parent, os.O_RDONLY)
try:
    os.fsync(directory_fd)
finally:
    os.close(directory_fd)
PY
}

finish() {
  local status=$?
  trap - EXIT
  if [[ "$receipt_enabled" == true ]]; then
    write_receipt "$status" || {
      echo "failed to write bootstrap receipt atomically: $receipt_output" >&2
      [[ $status -ne 0 ]] || status=70
    }
  fi
  exit "$status"
}
trap finish EXIT

fail() {
  failure="$1"
  echo "repository bootstrap refused: $failure" >&2
  exit 2
}

verify_checkout() {
  local checkout="$1"
  local status_output
  [[ -d "$checkout/.git" ]] || fail "repository_git_directory_missing"
  [[ "$(git -C "$checkout" remote get-url origin 2>/dev/null || true)" == "$GITHUB_REMOTE" ]] || \
    fail "repository_origin_remote_mismatch"
  git -C "$checkout" cat-file -e "${expected_repo_sha}^{commit}" 2>/dev/null || \
    fail "expected_commit_object_missing"
  observed_repo_sha="$(git -C "$checkout" rev-parse --verify HEAD 2>/dev/null || true)"
  [[ "$observed_repo_sha" == "$expected_repo_sha" ]] || fail "repository_sha_mismatch"
  observed_repo_tree="$(git -C "$checkout" rev-parse --verify 'HEAD^{tree}' 2>/dev/null || true)"
  [[ "$observed_repo_tree" =~ ^[0-9a-f]{40}$ ]] || fail "repository_tree_invalid"
  status_output="$(git -C "$checkout" status --porcelain --untracked-files=all)" || \
    fail "repository_status_check_failed"
  [[ -z "$status_output" ]] || \
    fail "repository_checkout_not_clean"
  checkout_clean=true
  if git -C "$checkout" symbolic-ref -q HEAD >/dev/null 2>&1; then
    fail "repository_head_not_detached"
  fi
  detached_head=true
}

# Create every governed FS9 directory with user-only permissions before cloning.
umask 077
mkdir -p "$fs9_root" "$fs9_root/logs" "$fs9_root/receipts" \
  "$fs9_root/receipts/v3" "$fs9_root/failures" "$fs9_root/failures/v3" \
  "$fs9_root/assets"
chmod 700 "$fs9_root" "$fs9_root/logs" "$fs9_root/receipts" \
  "$fs9_root/receipts/v3" "$fs9_root/failures" "$fs9_root/failures/v3" \
  "$fs9_root/assets"

if [[ -e "$repo_path" || -L "$repo_path" ]]; then
  verify_checkout "$repo_path"
  verdict="BOOTSTRAP_PASS_EXISTING_EXACT_CHECKOUT"
  failure=""
  exit 0
fi

candidate_path="$fs9_root/.repo-candidate-$(date -u +%Y%m%dT%H%M%SZ)-$$"
[[ ! -e "$candidate_path" && ! -L "$candidate_path" ]] || fail "candidate_path_already_exists"
git clone --no-checkout --origin origin "$GITHUB_REMOTE" "$candidate_path" || \
  fail "repository_clone_failed"
chmod 700 "$candidate_path"
[[ "$(git -C "$candidate_path" remote get-url origin 2>/dev/null || true)" == "$GITHUB_REMOTE" ]] || \
  fail "candidate_origin_remote_mismatch"
if ! git -C "$candidate_path" cat-file -e "${expected_repo_sha}^{commit}" 2>/dev/null; then
  git -C "$candidate_path" fetch --no-tags origin "$expected_repo_sha" || \
    fail "expected_commit_fetch_failed"
fi
git -C "$candidate_path" checkout --detach "$expected_repo_sha" || \
  fail "detached_checkout_failed"
verify_checkout "$candidate_path"

# GNU mv --no-target-directory maps to rename(2) here and refuses to place the
# candidate inside a concurrently-created repo directory.
mv --no-target-directory "$candidate_path" "$repo_path" || fail "atomic_repo_promotion_failed"
candidate_path=""
repo_created=true
verify_checkout "$repo_path"
verdict="BOOTSTRAP_PASS_ATOMICALLY_PROMOTED"
failure=""
