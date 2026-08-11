#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9a-f]{40}$ ]]; then
  echo "usage: $0 <exact-clean-merged-repository-sha>" >&2
  exit 64
fi

EXPECTED_REPO_SHA="$1"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="$ROOT/repo"
CONTRACT_REL=research/paper2_microtrial_v4_2/BATCH_CONTRACT_V4_2.json
CONTRACT="$REPO/$CONTRACT_REL"
PACKET="$REPO/research/paper2_microtrial_v4_2/EXECUTION_PACKET_V4_2_20260811.json"
POLICY="$REPO/research/paper2_microtrial_v4_1/OUTPUT_NORMALIZATION_CONTRACT_V4_1.json"
RECEIPT_ROOT="$ROOT/receipts/v4_2"
LOG_ROOT="$ROOT/logs/v4_2"
RUN_ROOT="$ROOT/runs/v4_2"
PYTHON="$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11"
SUBMISSION_SCHEMA="$REPO/schemas/paper2-pendulum-submission-receipt-v4-2.schema.json"

mkdir -p "$RECEIPT_ROOT" "$LOG_ROOT" "$RUN_ROOT"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
test -x "$PYTHON"

"$PYTHON" - "$REPO" "$CONTRACT" "$EXPECTED_REPO_SHA" <<'PY'
import hashlib, json, pathlib, subprocess, sys
repo=pathlib.Path(sys.argv[1]); contract_path=pathlib.Path(sys.argv[2]); expected=sys.argv[3]
contract=json.loads(contract_path.read_text(encoding="utf-8"))
def command(*args):
    return subprocess.run(args,cwd=repo,text=True,capture_output=True,check=True).stdout.strip()
if command("git","rev-parse","HEAD") != expected: raise SystemExit("exact checkout head mismatch")
if command("git","rev-parse","refs/remotes/origin/main") != expected: raise SystemExit("checkout is not exact merged origin/main head")
if command("git","status","--porcelain","--untracked-files=all"): raise SystemExit("checkout is dirty")
if command("git","remote","get-url","origin") != "https://github.com/SzeChunYiu/RAKL.git": raise SystemExit("origin mismatch")
if subprocess.run(["git","merge-base","--is-ancestor",contract["minimum_execution_ancestor_sha"],expected],cwd=repo).returncode:
    raise SystemExit("frozen packet parent is not an ancestor")
for binding in contract["bindings"]:
    path=repo/binding["path"]
    if not path.is_file(): raise SystemExit(f"binding missing:{binding['role']}")
    observed=hashlib.sha256(path.read_bytes()).hexdigest()
    if observed != binding["sha256"]: raise SystemExit(f"binding mismatch:{binding['role']}")
PY

BATCH_REL="$("$PYTHON" -c 'import json,sys; print(next(x["path"] for x in json.load(open(sys.argv[1]))["bindings"] if x["role"]=="batch_script"))' "$CONTRACT")"
BATCH_CONTRACT_SHA256="$(sha256sum "$CONTRACT" | awk '{print $1}')"
PACKET_SHA256="$(sha256sum "$PACKET" | awk '{print $1}')"
POLICY_SHA256="$(sha256sum "$POLICY" | awk '{print $1}')"
JOB_ID="$(sbatch --parsable --export=ALL,EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA",BATCH_CONTRACT_SHA256="$BATCH_CONTRACT_SHA256" "$REPO/$BATCH_REL")"

"$PYTHON" - "$RECEIPT_ROOT/submission-${JOB_ID}.json" "$CONTRACT" "$SUBMISSION_SCHEMA" "$EXPECTED_REPO_SHA" "$JOB_ID" "$PACKET_SHA256" "$POLICY_SHA256" <<'PY'
import datetime,hashlib,json,pathlib,sys,jsonschema
out=pathlib.Path(sys.argv[1]); contract_path=pathlib.Path(sys.argv[2]); schema_path=pathlib.Path(sys.argv[3])
sha=sys.argv[4]; job=sys.argv[5]; packet_sha=sys.argv[6]; policy_sha=sys.argv[7]
contract=json.loads(contract_path.read_text(encoding="utf-8"))
receipt={
  "schema_version":"paper2-pendulum-submission-receipt-v4.2",
  "created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
  "verdict":"SUBMITTED_NONCONFIRMATORY_V4_2_TASK_SEED_BATCH",
  "expected_repo_sha":sha,
  "packet_parent_sha":contract["packet_parent_sha"],
  "batch_contract_sha256":hashlib.sha256(contract_path.read_bytes()).hexdigest(),
  "execution_packet_sha256":packet_sha,
  "output_normalization_contract_sha256":policy_sha,
  "output_normalization_policy_id":contract["output_normalization_policy_id"],
  "slurm_job_id":job,
  "model_execution_observed_by_submitter":False,
  "evaluated_result_record_count_observed_by_submitter":0,
  "v4_reinterpretation_permitted":False,
  "claim_boundary":"Submission receipt only for a fresh V4.2 batch; harvest is required and V4/V4.1 negatives remain frozen; V4.2 harvest required."
}
schema=json.loads(schema_path.read_text(encoding="utf-8"))
jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).validate(receipt)
tmp=out.with_suffix(out.suffix+".tmp"); tmp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n"); tmp.replace(out)
PY

echo "$JOB_ID"
