#!/usr/bin/env bash
# Harvest ExperienceBenchmark §B2 artifacts for a completed SLURM job.
# Does not invoke the model. Does not reinterpret V4.1/V4.2 pendulum jobs.
set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9]+$ ]]; then
  echo "usage: $0 <slurm-job-id>" >&2
  exit 64
fi

JOB_ID="$1"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="$ROOT/repo"
PYTHON="$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11"
RECEIPT_ROOT="$ROOT/receipts/experience_v1_2"
RUN_DIR="$ROOT/runs/experience_v1_2/paper2-experience-benchmark-v1_2-job-${JOB_ID}"
SUBMISSION_PATH="$RECEIPT_ROOT/submission-${JOB_ID}.json"
SACCT_PATH="$RECEIPT_ROOT/sacct-${JOB_ID}.json"
HARVEST_PATH="$RECEIPT_ROOT/harvest-${JOB_ID}.json"
PROTOCOL_SUBJECT_HASH=c4ae092b70859d145b7a4b8a7d6485b3d2a552867756fec6783c1e35f7d5f352

mkdir -p "$RECEIPT_ROOT"
test -x "$PYTHON"
test -d "$RUN_DIR"
test -f "$SUBMISSION_PATH"
test -f "$RUN_DIR/runs.jsonl"
test -f "$RUN_DIR/run_manifest.json"

# Refuse accidental harvest of forbidden V4.1 pendulum job ids as §B evidence.
if [[ "$JOB_ID" == "3476520" || "$JOB_ID" == "3476521" || "$JOB_ID" == "3476524" ]]; then
  echo "REFUSED: job $JOB_ID is a V4.1 pendulum job and is not ExperienceBenchmark evidence" >&2
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
if manifest.get("v4_1_score_reuse_allowed") is not False: raise SystemExit("V4.1 reuse flag violated")
if manifest.get("paper3_issue_217_path") is not False: raise SystemExit("Paper3 path flag violated")
runs_path=run_dir/"runs.jsonl"
run_lines=[json.loads(line) for line in runs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
sn_hash=(run_dir/"states"/"Sn.hash").read_text(encoding="utf-8").strip()
receipt={
  "schema_version":"paper2-experience-benchmark-harvest-receipt-v1",
  "created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
  "issue":138,
  "section":"B2",
  "verdict":"HARVESTED_EXPERIENCE_BENCHMARK_V1_2_AWAITING_VALIDATION",
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
  "sacct_path":str(sacct_path),
  "sacct_sha256":hashlib.sha256(sacct_path.read_bytes()).hexdigest(),
  "submission_sha256":hashlib.sha256(submission_path.read_bytes()).hexdigest(),
  "v4_1_score_reuse_allowed":False,
  "paper3_issue_217_path":False,
  "claim_boundary":"Harvest receipt only. validate_experience_benchmark + protected attestations still required before manuscript ingest.",
  "repo_head_at_harvest":__import__("subprocess").run(["git","-C",str(repo),"rev-parse","HEAD"],check=True,capture_output=True,text=True).stdout.strip(),
}
tmp=out.with_suffix(out.suffix+".tmp")
tmp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
tmp.replace(out)
print(out)
PY

echo "$HARVEST_PATH"
