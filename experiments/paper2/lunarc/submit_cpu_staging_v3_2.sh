#!/bin/bash
# Login-host operator wrapper. Default is dry-run; --submit is an explicit side effect.
set -euo pipefail

usage() {
  echo "usage: $0 --repo PATH --expected-repo-sha SHA --bootstrap-receipt PATH --account ACCOUNT --partition PARTITION --receipt-output PATH [--submit]" >&2
}
repo=""; expected=""; bootstrap_receipt=""; account=""; partition=""; receipt=""; submit=0
while (($#)); do
  case "$1" in
    --repo) repo="$2"; shift 2 ;;
    --expected-repo-sha) expected="$2"; shift 2 ;;
    --bootstrap-receipt) bootstrap_receipt="$2"; shift 2 ;;
    --account) account="$2"; shift 2 ;;
    --partition) partition="$2"; shift 2 ;;
    --receipt-output) receipt="$2"; shift 2 ;;
    --submit) submit=1; shift ;;
    *) usage; exit 64 ;;
  esac
done
[[ -n "$repo" && -n "$expected" && -n "$bootstrap_receipt" && -n "$account" && -n "$partition" && -n "$receipt" ]] || { usage; exit 64; }
[[ "$(hostname)" == cosmos* ]] || { echo "submission is permitted only from a LUNARC login host" >&2; exit 2; }
[[ "$expected" =~ ^[0-9a-f]{40}$ ]] || { echo "expected repository SHA must be lowercase 40-hex" >&2; exit 2; }
[[ -f "$bootstrap_receipt" ]] || { echo "successful repository bootstrap receipt is required" >&2; exit 2; }

# Fail closed before the first scheduler interaction unless the atomic bootstrap
# receipt binds this exact repo path and commit and attests a clean detached tree.
python3 - "$bootstrap_receipt" "$repo" "$expected" <<'PY'
import json
import pathlib
import sys

receipt_path, repo_path, expected = sys.argv[1:]
try:
    receipt = json.loads(pathlib.Path(receipt_path).read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    raise SystemExit(f"invalid bootstrap receipt: {exc}")
allowed = {
    "BOOTSTRAP_PASS_EXISTING_EXACT_CHECKOUT",
    "BOOTSTRAP_PASS_ATOMICALLY_PROMOTED",
}
checks = {
    "successful verdict": receipt.get("verdict") in allowed,
    "zero exit status": receipt.get("exit_status") == 0,
    "exact GitHub remote": receipt.get("github_remote") == "https://github.com/SzeChunYiu/RAKL.git",
    "exact repository SHA": receipt.get("expected_repo_sha") == expected and receipt.get("observed_repo_sha") == expected,
    "exact repository path": pathlib.Path(str(receipt.get("repo_path", ""))).resolve() == pathlib.Path(repo_path).resolve(),
    "clean checkout": receipt.get("checkout_clean") is True,
    "detached HEAD": receipt.get("detached_head") is True,
    "zero jobs": receipt.get("jobs_submitted") == 0,
    "no model execution": receipt.get("model_execution_performed") is False,
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise SystemExit("bootstrap receipt validation failed: " + ", ".join(failed))
PY
[[ "$(git -C "$repo" rev-parse HEAD)" == "$expected" ]] || { echo "exact repository SHA mismatch" >&2; exit 2; }
repo_status="$(git -C "$repo" status --porcelain --untracked-files=all)" || { echo "repository status check failed" >&2; exit 2; }
[[ -z "$repo_status" ]] || { echo "repository checkout is not clean" >&2; exit 2; }
[[ "$(git -C "$repo" remote get-url origin)" == "https://github.com/SzeChunYiu/RAKL.git" ]] || { echo "repository origin remote mismatch" >&2; exit 2; }
if git -C "$repo" symbolic-ref -q HEAD >/dev/null 2>&1; then
  echo "repository HEAD must be detached" >&2
  exit 2
fi
contract="$repo/research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3_2.json"
mapfile -t associations < <(sacctmgr -nP show assoc user="$USER" format=Account,Partition | awk -F'|' 'NF>=2 && $1!="" && $2!="" {print $1 ":" $2}')
argv=(python3 -m rakl.paper2_cpu_staging_v3_2 submit --contract "$contract" --repo "$repo" --expected-repo-sha "$expected" --bootstrap-receipt "$bootstrap_receipt" --account "$account" --partition "$partition" --receipt-output "$receipt")
for association in "${associations[@]}"; do argv+=(--association "$association"); done
((submit)) && argv+=(--submit)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$repo/src" "${argv[@]}"
