#!/usr/bin/env bash
# Harvest ExperienceBenchmark v1.3 Phase-1 ORACLE artifacts for a completed SLURM job.
# Does not invoke the model. Does not reopen #138 or reinterpret 3476548 as lift.
set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9]+$ ]]; then
  echo "usage: $0 <slurm-job-id>" >&2
  exit 64
fi

JOB_ID="$1"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="$ROOT/repo"
PYTHON="$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11"
RECEIPT_ROOT="$ROOT/receipts/experience_v1_3_oracle"
RUN_DIR="$ROOT/runs/experience_v1_3_oracle/paper2-experience-benchmark-v1_3-oracle-job-${JOB_ID}"
SUBMISSION_PATH="$RECEIPT_ROOT/submission-${JOB_ID}.json"
SACCT_PATH="$RECEIPT_ROOT/sacct-${JOB_ID}.json"
HARVEST_PATH="$RECEIPT_ROOT/harvest-${JOB_ID}.json"
PROTOCOL_SUBJECT_HASH=ed116353230dc526fa45657d1a81afab26a460fe3b8411480a0f84bb1f711672

mkdir -p "$RECEIPT_ROOT"
test -x "$PYTHON"
test -d "$RUN_DIR"
test -f "$SUBMISSION_PATH"
test -f "$RUN_DIR/runs.jsonl"
test -f "$RUN_DIR/run_manifest.json"

if [[ "$JOB_ID" == "3476520" || "$JOB_ID" == "3476521" || "$JOB_ID" == "3476524" || "$JOB_ID" == "3476548" ]]; then
  echo "REFUSED: job $JOB_ID is not a v1.3 ORACLE harvest subject" >&2
  exit 42
fi

sacct -j "$JOB_ID" --json > "$SACCT_PATH"

"$PYTHON" - "$HARVEST_PATH" "$JOB_ID" "$RUN_DIR" "$SUBMISSION_PATH" "$SACCT_PATH" "$REPO" "$PROTOCOL_SUBJECT_HASH" <<'PY'
import datetime, hashlib, json, pathlib, sys
out=pathlib.Path(sys.argv[1]); job=sys.argv[2]; run_dir=pathlib.Path(sys.argv[3])
submission_path=pathlib.Path(sys.argv[4]); sacct_path=pathlib.Path(sys.argv[5])
repo=pathlib.Path(sys.argv[6]); protocol_hash=sys.argv[7]
manifest=json.loads((run_dir/"run_manifest.json").read_text(encoding="utf-8"))
submission=json.loads(submission_path.read_text(encoding="utf-8"))
if manifest.get("protocol_subject_hash") != protocol_hash: raise SystemExit("manifest protocol hash mismatch")
if submission.get("protocol_subject_hash") != protocol_hash: raise SystemExit("submission protocol hash mismatch")
if submission.get("slurm_job_id") != job: raise SystemExit("submission job mismatch")
if manifest.get("scheduler_job_id") != job: raise SystemExit("manifest job mismatch")
if manifest.get("learning_loop_mode") != "root_cause_v1": raise SystemExit("learning loop mismatch")
if manifest.get("diagnostic_arm") != "ORACLE_PROCEDURE_UPPER_BOUND": raise SystemExit("diagnostic arm mismatch")
if manifest.get("oracle_transfer_only") is not True: raise SystemExit("expected oracle_transfer_only")
if manifest.get("v4_1_score_reuse_allowed") is not False: raise SystemExit("V4.1 reuse flag violated")
if manifest.get("paper3_issue_217_path") is not False: raise SystemExit("Paper3 path flag violated")
runs_path=run_dir/"runs.jsonl"
run_lines=[json.loads(line) for line in runs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
if sorted({run["task_id"] for run in run_lines}) != ["T1","T2","T3"]:
    raise SystemExit("ORACLE harvest expects exactly T1/T2/T3")
sn_hash=(run_dir/"states"/"Sn.hash").read_text(encoding="utf-8").strip()
receipt={
  "schema_version":"paper2-experience-benchmark-harvest-receipt-v1",
  "created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
  "issue":247,
  "section":"PHASE1_ORACLE_0_5B",
  "verdict":"HARVESTED_EXPERIENCE_BENCHMARK_V1_3_ORACLE_AWAITING_VALIDATION",
  "slurm_job_id":job,
  "protocol_subject_hash":protocol_hash,
  "expected_repo_sha":submission.get("expected_repo_sha"),
  "run_dir":str(run_dir),
  "run_manifest_sha256":hashlib.sha256((run_dir/"run_manifest.json").read_bytes()).hexdigest(),
  "runs_jsonl_sha256":hashlib.sha256(runs_path.read_bytes()).hexdigest(),
  "learned_state_after_development_hash":sn_hash,
  "run_count":len(run_lines),
  "arms_observed":sorted({run["arm"] for run in run_lines}),
  "task_ids_observed":sorted({run["task_id"] for run in run_lines}),
  "learning_loop_mode":"root_cause_v1",
  "diagnostic_arm":"ORACLE_PROCEDURE_UPPER_BOUND",
  "sacct_path":str(sacct_path),
  "sacct_sha256":hashlib.sha256(sacct_path.read_bytes()).hexdigest(),
  "submission_sha256":hashlib.sha256(submission_path.read_bytes()).hexdigest(),
  "v4_1_score_reuse_allowed":False,
  "paper3_issue_217_path":False,
  "reopen_issue_138":False,
  "reinterpret_parent_job_3476548_as_lift":False,
  "claim_boundary":"Harvest receipt only for #247 Phase-1 ORACLE. validate + protected attestations still required before manuscript ingest.",
  "repo_head_at_harvest":__import__("subprocess").run(["git","-C",str(repo),"rev-parse","HEAD"],check=True,capture_output=True,text=True).stdout.strip(),
}
tmp=out.with_suffix(out.suffix+".tmp")
tmp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
tmp.replace(out)
print(out)
PY

echo "$HARVEST_PATH"
