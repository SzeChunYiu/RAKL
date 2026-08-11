#!/usr/bin/env bash
# Login-host operator wrapper for V4.3 model-only staging.
# usage: $0 <exact-clean-merged-repository-sha>
set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9a-f]{40}$ ]]; then
  echo "usage: $0 <exact-clean-merged-repository-sha>" >&2
  exit 64
fi

EXPECTED_REPO_SHA="$1"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="$ROOT/repo"
CONTRACT_REL=research/paper2_microtrial_v4_3/MODEL_STAGING_CONTRACT_V4_3.json
CONTRACT="$REPO/$CONTRACT_REL"
PYTHON=/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11
RECEIPT_ROOT="$ROOT/receipts/v4_3"
LOG_ROOT="$ROOT/logs/v4_3"

[[ "$(hostname)" == cosmos* ]] || { echo "submission is permitted only from a LUNARC login host" >&2; exit 2; }
mkdir -p "$RECEIPT_ROOT" "$LOG_ROOT"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
test -x "$PYTHON"
test -f "$CONTRACT"

"$PYTHON" - "$REPO" "$CONTRACT" "$EXPECTED_REPO_SHA" <<'PY'
import hashlib, json, pathlib, subprocess, sys
repo=pathlib.Path(sys.argv[1]); contract_path=pathlib.Path(sys.argv[2]); expected=sys.argv[3]
def command(*args):
    return subprocess.run(args, cwd=repo, text=True, capture_output=True, check=True).stdout.strip()
if command("git","rev-parse","HEAD") != expected: raise SystemExit("exact checkout head mismatch")
if command("git","rev-parse","refs/remotes/origin/main") != expected: raise SystemExit("checkout is not exact merged origin/main head")
if command("git","status","--porcelain","--untracked-files=all"): raise SystemExit("checkout is dirty")
if command("git","remote","get-url","origin") != "https://github.com/SzeChunYiu/RAKL.git": raise SystemExit("origin mismatch")
contract=json.loads(contract_path.read_text(encoding="utf-8"))
for binding in contract["bindings"]:
    path=repo/binding["path"]
    if not path.is_file(): raise SystemExit(f"binding missing:{binding['role']}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != binding["sha256"]:
        raise SystemExit(f"binding mismatch:{binding['role']}")
final=pathlib.Path(contract["final_root"])
if final.exists(): raise SystemExit("final model assets root already exists")
PY

CONTRACT_ABS="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve())' "$CONTRACT")"
PROBE_JOB="$(sbatch --parsable \
  --export=ALL,RAKL_STAGING_CONTRACT="$CONTRACT_ABS",RAKL_EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA",RAKL_REPO_PATH="$REPO" \
  "$REPO/experiments/paper2/lunarc/network_probe_v4_3.sbatch")"
PROBE_JOB="${PROBE_JOB%%;*}"
[[ "$PROBE_JOB" =~ ^[0-9]+$ ]]

STAGE_JOB="$(sbatch --parsable \
  --dependency=afterok:${PROBE_JOB} \
  --export=ALL,RAKL_STAGING_CONTRACT="$CONTRACT_ABS",RAKL_EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA",RAKL_REPO_PATH="$REPO",RAKL_PROBE_JOB_ID="$PROBE_JOB" \
  "$REPO/experiments/paper2/lunarc/stage_model_assets_v4_3.sbatch")"
STAGE_JOB="${STAGE_JOB%%;*}"
[[ "$STAGE_JOB" =~ ^[0-9]+$ ]]

"$PYTHON" - "$RECEIPT_ROOT/model-stage-submission-${PROBE_JOB}-${STAGE_JOB}.json" "$CONTRACT" "$EXPECTED_REPO_SHA" "$PROBE_JOB" "$STAGE_JOB" <<'PY'
import datetime,hashlib,json,pathlib,sys
out=pathlib.Path(sys.argv[1]); contract_path=pathlib.Path(sys.argv[2]); sha=sys.argv[3]; probe=sys.argv[4]; stage=sys.argv[5]
contract=json.loads(contract_path.read_text(encoding="utf-8"))
receipt={
  "schema_version":"paper2-model-staging-submission-receipt-v4-3",
  "created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
  "verdict":"SUBMITTED_MODEL_ONLY_PROBE_AND_STAGE",
  "expected_repo_sha":sha,
  "contract_id":contract["contract_id"],
  "contract_sha256":hashlib.sha256(contract_path.read_bytes()).hexdigest(),
  "probe_job_id":probe,
  "staging_job_id":stage,
  "model_execution_observed_by_submitter":False,
  "claim_boundary":"Submission receipt only for V4.3 model-only staging; harvest required before sealed microtrial.",
}
tmp=out.with_suffix(out.suffix+".tmp"); tmp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n"); tmp.replace(out)
PY

echo "PROBE_JOB_ID=${PROBE_JOB}"
echo "STAGE_JOB_ID=${STAGE_JOB}"
echo "${PROBE_JOB} ${STAGE_JOB}"
