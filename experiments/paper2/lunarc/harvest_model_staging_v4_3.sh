#!/usr/bin/env bash
# usage: $0 <probe-job-id> <stage-job-id>
set -euo pipefail
if [[ $# -ne 2 || ! "$1" =~ ^[0-9]+$ || ! "$2" =~ ^[0-9]+$ ]]; then
  echo "usage: $0 <probe-job-id> <stage-job-id>" >&2
  exit 64
fi
PROBE_JOB="$1"
STAGE_JOB="$2"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
RECEIPT_ROOT="$ROOT/receipts/v4_3"
FINAL=/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/paper2-model-qwen25-1_5b-v4-3
PYTHON=/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11
mkdir -p "$RECEIPT_ROOT"
sacct -j "$PROBE_JOB,$STAGE_JOB" --json > "$RECEIPT_ROOT/sacct-model-stage-${PROBE_JOB}-${STAGE_JOB}.json"
test -x "$PYTHON"
test -d "$FINAL"
test -f "$FINAL/STAGING_PASS_RECEIPT.json"
test -f "$RECEIPT_ROOT/network-probe-${PROBE_JOB}.json"

"$PYTHON" - "$RECEIPT_ROOT/harvest-model-stage-${PROBE_JOB}-${STAGE_JOB}.json" \
  "$RECEIPT_ROOT/network-probe-${PROBE_JOB}.json" \
  "$FINAL/STAGING_PASS_RECEIPT.json" \
  "$RECEIPT_ROOT/sacct-model-stage-${PROBE_JOB}-${STAGE_JOB}.json" \
  "$PROBE_JOB" "$STAGE_JOB" <<'PY'
import datetime,hashlib,json,pathlib,sys
out,probe_path,stage_path,sacct_path=map(pathlib.Path, sys.argv[1:5])
probe_job,stage_job=sys.argv[5:7]
probe=json.loads(probe_path.read_text()); stage=json.loads(stage_path.read_text())
if probe.get("verdict") != "NETWORK_PROBE_PASS": raise SystemExit("probe not pass")
if stage.get("verdict") != "STAGING_PASS_ATOMICALLY_PROMOTED": raise SystemExit("stage not pass")
receipt={
  "schema_version":"paper2-model-staging-harvest-receipt-v4-3",
  "created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
  "verdict":"MODEL_STAGING_HARVEST_PASS",
  "probe_job_id":probe_job,
  "staging_job_id":stage_job,
  "probe_receipt_sha256":hashlib.sha256(probe_path.read_bytes()).hexdigest(),
  "staging_receipt_sha256":hashlib.sha256(stage_path.read_bytes()).hexdigest(),
  "sacct_sha256":hashlib.sha256(sacct_path.read_bytes()).hexdigest(),
  "final_root":stage.get("final_root"),
  "model_execution_performed":False,
  "claim_boundary":"Model-only staging harvest; does not authorize sealed microtrial scores or promotional numbers.",
}
tmp=out.with_suffix(out.suffix+".tmp"); tmp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n"); tmp.replace(out)
print(out)
PY
