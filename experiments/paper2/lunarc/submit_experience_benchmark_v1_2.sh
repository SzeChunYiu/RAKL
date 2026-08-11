#!/usr/bin/env bash
# Submit Paper-II ExperienceBenchmark §B2 (RESET vs LEARNING) on LUNARC FS9.
# Bound to frozen protocol_subject_hash from research/paper2_experience_benchmark_v1_2/.
# Does NOT submit Paper-III (#217) jobs and does NOT reuse V4.1/V4.2 pendulum scores.
set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9a-f]{40}$ ]]; then
  echo "usage: $0 <exact-clean-merged-repository-sha>" >&2
  exit 64
fi

EXPECTED_REPO_SHA="$1"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="$ROOT/repo"
PACKET_REL=research/paper2_experience_benchmark_v1_2
PROTOCOL_SUBJECT_HASH=c4ae092b70859d145b7a4b8a7d6485b3d2a552867756fec6783c1e35f7d5f352
CONTRACT_REL=research/paper2_experience_benchmark_v1_2/BATCH_CONTRACT_V1_2.json
CONTRACT="$REPO/$CONTRACT_REL"
PACKET="$REPO/$PACKET_REL/PROTOCOL_FREEZE_PACKET.json"
PYTHON="$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11"
RECEIPT_ROOT="$ROOT/receipts/experience_v1_2"
LOG_ROOT="$ROOT/logs/experience_v1_2"
RUN_ROOT="$ROOT/runs/experience_v1_2"
SBATCH_REL=experiments/paper2/lunarc/run_experience_benchmark_v1_2.sbatch

mkdir -p "$RECEIPT_ROOT" "$LOG_ROOT" "$RUN_ROOT"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
test -x "$PYTHON"
test -f "$CONTRACT"
test -f "$REPO/$SBATCH_REL"

"$PYTHON" - "$REPO" "$PACKET" "$CONTRACT" "$EXPECTED_REPO_SHA" "$PROTOCOL_SUBJECT_HASH" <<'PY'
import hashlib, json, pathlib, subprocess, sys
repo=pathlib.Path(sys.argv[1]); packet_path=pathlib.Path(sys.argv[2]); contract_path=pathlib.Path(sys.argv[3])
expected=sys.argv[4]; protocol_hash=sys.argv[5]
def command(*args):
    return subprocess.run(args,cwd=repo,text=True,capture_output=True,check=True).stdout.strip()
if command("git","rev-parse","HEAD") != expected: raise SystemExit("exact checkout head mismatch")
if command("git","rev-parse","refs/remotes/origin/main") != expected: raise SystemExit("checkout is not exact merged origin/main head")
if command("git","status","--porcelain","--untracked-files=all"): raise SystemExit("checkout is dirty")
if command("git","remote","get-url","origin") != "https://github.com/SzeChunYiu/RAKL.git": raise SystemExit("origin mismatch")
packet=json.loads(packet_path.read_text(encoding="utf-8"))
contract=json.loads(contract_path.read_text(encoding="utf-8"))
if packet.get("protocol_subject_hash") != protocol_hash: raise SystemExit("protocol_subject_hash mismatch")
if contract.get("protocol_subject_hash") != protocol_hash: raise SystemExit("batch contract protocol hash mismatch")
if packet.get("scientific_claim_status") != "NO_EMPIRICAL_RESULT": raise SystemExit("packet not awaiting execution")
if packet.get("v4_1_pendulum_compatibility",{}).get("score_reuse_allowed") is not False:
    raise SystemExit("V4.1 score reuse must be forbidden")
forbidden=set(packet.get("v4_1_pendulum_compatibility",{}).get("jobs_explicitly_not_experience_evidence",[]))
if not {3476520,3476521,3476524}.issubset(forbidden): raise SystemExit("missing V4.1 forbidden jobs")
for binding in contract["bindings"]:
    path=repo/binding["path"]
    if not path.is_file(): raise SystemExit(f"binding missing:{binding['role']}")
    observed=hashlib.sha256(path.read_bytes()).hexdigest()
    if observed != binding["sha256"]: raise SystemExit(f"binding mismatch:{binding['role']}")
if subprocess.run(["git","merge-base","--is-ancestor",contract["minimum_execution_ancestor_sha"],expected],cwd=repo).returncode:
    raise SystemExit("minimum execution ancestor is not an ancestor of subject")
PY

BATCH_CONTRACT_SHA256="$(sha256sum "$CONTRACT" | awk '{print $1}')"
PACKET_SHA256="$(sha256sum "$PACKET" | awk '{print $1}')"
JOB_ID="$(sbatch --parsable \
  --export=ALL,EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA",BATCH_CONTRACT_SHA256="$BATCH_CONTRACT_SHA256",PROTOCOL_SUBJECT_HASH="$PROTOCOL_SUBJECT_HASH" \
  "$REPO/$SBATCH_REL")"

"$PYTHON" - "$RECEIPT_ROOT/submission-${JOB_ID}.json" "$EXPECTED_REPO_SHA" "$JOB_ID" "$PACKET_SHA256" "$BATCH_CONTRACT_SHA256" "$PROTOCOL_SUBJECT_HASH" <<'PY'
import datetime, json, pathlib, sys
out=pathlib.Path(sys.argv[1]); sha=sys.argv[2]; job=sys.argv[3]; packet_sha=sys.argv[4]
batch_sha=sys.argv[5]; protocol_hash=sys.argv[6]
receipt={
  "schema_version":"paper2-experience-benchmark-submission-receipt-v1",
  "created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
  "issue":138,
  "section":"B2",
  "verdict":"SUBMITTED_EXPERIENCE_BENCHMARK_V1_2",
  "expected_repo_sha":sha,
  "slurm_job_id":job,
  "protocol_subject_hash":protocol_hash,
  "protocol_freeze_packet_sha256":packet_sha,
  "batch_contract_sha256":batch_sha,
  "arms":["RESET_BASELINE","LEARNING_ENABLED"],
  "phases":["DEVELOPMENT_SEQUENCE","FRESH_TRANSFER"],
  "v4_1_score_reuse_allowed":False,
  "v4_1_jobs_not_evidence":[3476520,3476521,3476524],
  "paper3_issue_217_path":False,
  "model_execution_observed_by_submitter":False,
  "claim_boundary":"Submission receipt only for #138 §B ExperienceBenchmark RESET/LEARNING jobs. Not manuscript authority.",
}
tmp=out.with_suffix(out.suffix+".tmp")
tmp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
tmp.replace(out)
PY

echo "$JOB_ID"
