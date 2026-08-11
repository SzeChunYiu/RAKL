#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 || ! "$1" =~ ^[0-9a-f]{40}$ || ! "$2" =~ ^[0-9]+$ ]]; then
  echo "usage: $0 <exact-clean-merged-repository-sha> <passed-model-stage-job-id>" >&2
  exit 64
fi

EXPECTED_REPO_SHA="$1"
STAGE_JOB_ID="$2"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper3
REPO="$ROOT/repo"
RUN_ROOT="$ROOT/semantic_descriptor_v1"
RECEIPT_ROOT="$RUN_ROOT/receipts"
LOG_ROOT="$ROOT/logs/semantic-v1"
PYTHON=/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11
CONTRACT="$REPO/research/paper3_semantic_descriptor_lunarc/CONTRACT_V1.json"
BATCH="$REPO/experiments/paper3/lunarc/run_semantic_descriptor.sbatch"
STAGE_HARVEST="$RECEIPT_ROOT/harvest-model-stage-${STAGE_JOB_ID}.json"
SCHEMA="$REPO/schemas/paper3-semantic-lunarc-submission-v1.schema.json"

mkdir -p "$RECEIPT_ROOT" "$LOG_ROOT" "$RUN_ROOT/runs"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
test -x "$PYTHON"

"$PYTHON" - "$REPO" "$CONTRACT" "$STAGE_HARVEST" "$EXPECTED_REPO_SHA" <<'PY'
import pathlib,sys
repo=pathlib.Path(sys.argv[1]); contract_path=pathlib.Path(sys.argv[2]); stage_path=pathlib.Path(sys.argv[3]); expected=sys.argv[4]
sys.path.insert(0,str(repo/'experiments/paper3/lunarc'))
from semantic_descriptor_common import inspect_model_files,load_json,validate_repo_and_contract,validate_schema
contract,failures=validate_repo_and_contract(repo=repo,contract_path=contract_path,expected_repo_sha=expected)
if failures: raise SystemExit(';'.join(failures))
stage=load_json(stage_path)
validate_schema(stage,repo/'schemas/paper3-semantic-lunarc-harvest-v1.schema.json')
if stage['verdict']!='HARVEST_MODEL_STAGE_PASS': raise SystemExit('model stage harvest did not pass')
if stage['expected_repo_sha']!=expected: raise SystemExit('model stage checkout differs')
_,asset_failures=inspect_model_files(pathlib.Path(contract['fs9']['model_dir']),contract['model']['required_files'])
if asset_failures: raise SystemExit(';'.join(asset_failures))
PY

CONTRACT_SHA256="$(sha256sum "$CONTRACT" | awk '{print $1}')"
STAGE_HARVEST_SHA256="$(sha256sum "$STAGE_HARVEST" | awk '{print $1}')"
JOB_ID="$(sbatch --parsable \
  --export=ALL,RAKL_EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA",RAKL_CONTRACT_SHA256="$CONTRACT_SHA256",RAKL_STAGE_HARVEST_PATH="$STAGE_HARVEST",RAKL_STAGE_HARVEST_SHA256="$STAGE_HARVEST_SHA256" \
  "$BATCH")"
JOB_ID="${JOB_ID%%;*}"
[[ "$JOB_ID" =~ ^[0-9]+$ ]]

"$PYTHON" - "$RECEIPT_ROOT/descriptor-submission-${JOB_ID}.json" "$SCHEMA" "$CONTRACT" "$EXPECTED_REPO_SHA" "$JOB_ID" "$STAGE_JOB_ID" "$STAGE_HARVEST_SHA256" <<'PY'
import hashlib,pathlib,sys
out=pathlib.Path(sys.argv[1]); schema_path=pathlib.Path(sys.argv[2]); contract_path=pathlib.Path(sys.argv[3]); sha=sys.argv[4]; job=sys.argv[5]; stage_job=sys.argv[6]; stage_sha=sys.argv[7]
sys.path.insert(0,str(contract_path.parents[2]/'experiments/paper3/lunarc'))
from semantic_descriptor_common import atomic_write_json,load_json,utc_now,validate_schema
contract=load_json(contract_path)
receipt={"schema_version":"paper3-semantic-lunarc-submission-v1","created_at_utc":utc_now(),"phase":"DESCRIPTOR","verdict":"SUBMITTED_DESCRIPTOR_BATCH_AFTER_STAGE_PASS","expected_repo_sha":sha,"frozen_parent_sha":contract["frozen_parent_sha"],"contract_sha256":hashlib.sha256(contract_path.read_bytes()).hexdigest(),"slurm_job_id":job,"parent_stage_job_id":stage_job,"parent_stage_harvest_sha256":stage_sha,"model_execution_observed_by_submitter":False,"descriptor_record_count_observed_by_submitter":0,"claim_boundary":"Submission receipt only; descriptor authority requires allocated execution and harvest."}
validate_schema(receipt,schema_path); atomic_write_json(out,receipt)
PY

echo "$JOB_ID"
