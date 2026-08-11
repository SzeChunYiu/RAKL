#!/usr/bin/env bash
# Submit Paper-II ExperienceBenchmark v1.3_1 Phase-1 ORACLE @ 1.5B on LUNARC FS9.
# Bound to frozen protocol_subject_hash from research/paper2_experience_benchmark_v1_3_1/.
# learning_loop_mode=root_cause_v1; diagnostic_arm=ORACLE_PROCEDURE_UPPER_BOUND.
# Parent is floored v1.3 0.5B ORACLE (3476730/3476731), not broken v1.2.
# Does NOT submit learning staircase, Paper-III (#217), or reopen #138.
set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9a-f]{40}$ ]]; then
  echo "usage: $0 <exact-clean-merged-repository-sha>" >&2
  exit 64
fi

EXPECTED_REPO_SHA="$1"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="$ROOT/repo"
PACKET_REL=research/paper2_experience_benchmark_v1_3_1
PROTOCOL_SUBJECT_HASH=61b9fd42f2a58713f04de1e6a170a0e233beeb057c38f01939e384b7b4cb2bc3
CONTRACT_REL=research/paper2_experience_benchmark_v1_3_1/BATCH_CONTRACT_V1_3_1_ORACLE.json
CONTRACT="$REPO/$CONTRACT_REL"
PACKET="$REPO/$PACKET_REL/PROTOCOL_FREEZE_PACKET.json"
PYTHON="$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11"
RECEIPT_ROOT="$ROOT/receipts/experience_v1_3_1_oracle"
LOG_ROOT="$ROOT/logs/experience_v1_3_1_oracle"
RUN_ROOT="$ROOT/runs/experience_v1_3_1_oracle"
SBATCH_REL=experiments/paper2/lunarc/run_experience_benchmark_v1_3_1_oracle.sbatch
LEARNING_LOOP_MODE=root_cause_v1
DIAGNOSTIC_ARM=ORACLE_PROCEDURE_UPPER_BOUND

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
if packet.get("learning_loop_mode") != "root_cause_v1": raise SystemExit("learning_loop_mode must be root_cause_v1")
if packet.get("primary_execution",{}).get("first_job_arm") != "ORACLE_PROCEDURE_UPPER_BOUND":
    raise SystemExit("packet primary_execution must start with ORACLE")
if packet.get("parent_negative_history",{}).get("reopen_issue_138") is not False:
    raise SystemExit("must not reopen #138")
if packet.get("v4_1_pendulum_compatibility",{}).get("score_reuse_allowed") is not False:
    raise SystemExit("V4.1 score reuse must be forbidden")
forbidden=set(packet.get("v4_1_pendulum_compatibility",{}).get("jobs_explicitly_not_experience_evidence",[]))
if not {3476520,3476521,3476524}.issubset(forbidden): raise SystemExit("missing V4.1 forbidden jobs")
witness=json.loads((repo/"research/paper2_experience_benchmark_v1_3_1/DIFFERENCE_WITNESS_V1_3_1.json").read_text(encoding="utf-8"))
if witness.get("explicitly_not_scale_only_escape_from_v1_2") is not True: raise SystemExit("must not be scale-only escape from v1.2")
if witness.get("scale_change_from_floored_0_5B_oracle") is not True: raise SystemExit("must record scale change from floored 0.5B ORACLE")
if witness.get("learning_staircase_authorized") is not False: raise SystemExit("learning staircase must remain unauthorized")
if witness.get("reopen_issue_138") is not False: raise SystemExit("witness reopen_issue_138 must be false")
if witness.get("parent_scientific_verdict") != "MODEL_CAPABILITY_FLOOR_0_5B": raise SystemExit("parent must be floored 0.5B ORACLE")
if packet.get("primary_execution",{}).get("model_scale") != "Qwen2.5-1.5B-Instruct":
    raise SystemExit("packet model_scale must be 1.5B")
if packet.get("model",{}).get("model_id") != "Qwen/Qwen2.5-1.5B-Instruct":
    raise SystemExit("packet model_id must be Qwen2.5-1.5B-Instruct")
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
  --export=ALL,EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA",BATCH_CONTRACT_SHA256="$BATCH_CONTRACT_SHA256",PROTOCOL_SUBJECT_HASH="$PROTOCOL_SUBJECT_HASH",LEARNING_LOOP_MODE="$LEARNING_LOOP_MODE",DIAGNOSTIC_ARM="$DIAGNOSTIC_ARM" \
  "$REPO/$SBATCH_REL")"

"$PYTHON" - "$RECEIPT_ROOT/submission-${JOB_ID}.json" "$EXPECTED_REPO_SHA" "$JOB_ID" "$PACKET_SHA256" "$BATCH_CONTRACT_SHA256" "$PROTOCOL_SUBJECT_HASH" <<'PY'
import datetime, json, pathlib, sys
out=pathlib.Path(sys.argv[1]); sha=sys.argv[2]; job=sys.argv[3]; packet_sha=sys.argv[4]
batch_sha=sys.argv[5]; protocol_hash=sys.argv[6]
receipt={
  "schema_version":"paper2-experience-benchmark-submission-receipt-v1",
  "created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
  "issue":247,
  "section":"PHASE1_ORACLE_1_5B",
  "verdict":"SUBMITTED_EXPERIENCE_BENCHMARK_V1_3_1_ORACLE",
  "expected_repo_sha":sha,
  "slurm_job_id":job,
  "protocol_subject_hash":protocol_hash,
  "protocol_freeze_packet_sha256":packet_sha,
  "batch_contract_sha256":batch_sha,
  "arms":["ORACLE_PROCEDURE_UPPER_BOUND"],
  "phases":["FRESH_TRANSFER"],
  "learning_loop_mode":"root_cause_v1",
  "diagnostic_arm":"ORACLE_PROCEDURE_UPPER_BOUND",
  "model_scale":"Qwen2.5-1.5B-Instruct",
  "v4_1_score_reuse_allowed":False,
  "v4_1_jobs_not_evidence":[3476520,3476521,3476524],
  "paper3_issue_217_path":False,
  "experience_benchmark_1_5B_submitted":True,
  "reopen_issue_138":False,
  "reinterpret_parent_job_3476548_as_lift":False,
  "model_execution_observed_by_submitter":False,
  "claim_boundary":"Submission receipt only for #247 Phase-1 1.5B ORACLE after floored 0.5B. Not manuscript authority. Not experience-learning efficacy.",
}
tmp=out.with_suffix(out.suffix+".tmp")
tmp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
tmp.replace(out)
PY

echo "$JOB_ID"
