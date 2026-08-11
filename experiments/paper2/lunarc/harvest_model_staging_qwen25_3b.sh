#!/usr/bin/env bash
# Harvest Qwen2.5-3B model-only staging result.
set -euo pipefail
if [[ $# -ne 1 || ! "$1" =~ ^[0-9]+$ ]]; then
  echo "usage: $0 <staging-slurm-job-id>" >&2
  exit 64
fi
JOB_ID="$1"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
FINAL=/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/paper2-model-qwen25-3b-v1
RECEIPT_ROOT="$ROOT/receipts/qwen25_3b_stage"
test -d "$FINAL"
test -f "$FINAL/STAGING_PASS_RECEIPT.json"
python3 - "$RECEIPT_ROOT/harvest-stage-${JOB_ID}.json" "$FINAL" "$JOB_ID" <<'PY'
import datetime, hashlib, json, pathlib, sys
out=pathlib.Path(sys.argv[1]); final=pathlib.Path(sys.argv[2]); job=sys.argv[3]
pass_receipt=final/"STAGING_PASS_RECEIPT.json"
payload=json.loads(pass_receipt.read_text(encoding="utf-8"))
if payload.get("verdict") != "STAGING_PASS_ATOMICALLY_PROMOTED":
    raise SystemExit("staging pass receipt missing")
if str(payload.get("slurm_job_id")) != job:
    raise SystemExit("staging job mismatch")
receipt={
  "schema_version":"paper2-model-staging-harvest-receipt-v4-3",
  "created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
  "verdict":"MODEL_STAGING_HARVEST_PASS",
  "slurm_job_id":job,
  "final_root":str(final),
  "pass_receipt_sha256":hashlib.sha256(pass_receipt.read_bytes()).hexdigest(),
  "model_execution_performed":False,
  "claim_boundary":"Harvest only for Qwen2.5-3B ExperienceBenchmark model staging; no ORACLE score.",
}
tmp=out.with_suffix(out.suffix+".tmp")
tmp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
tmp.replace(out)
print(out)
PY
echo "$RECEIPT_ROOT/harvest-stage-${JOB_ID}.json"
