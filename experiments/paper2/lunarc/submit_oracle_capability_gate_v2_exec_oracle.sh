#!/usr/bin/env bash
# Submit ORACLE_CAPABILITY_GATE_V2_0_EXEC Phase-1 ORACLE @ 7B on LUNARC FS9.
# Bound to frozen protocol_subject_hash from research/paper2_oracle_capability_gate_v2_exec/.
# learning_loop_mode=root_cause_v1; diagnostic_arm=ORACLE_PROCEDURE_UPPER_BOUND.
# Parent floors preserved; CAPABLE_MODEL remains NO_REFUTED until receipt.
# Does NOT submit learning staircase, 14B/32B, Paper-III (#217), or reopen #138.
set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9a-f]{40}$ ]]; then
  echo "usage: $0 <exact-clean-merged-repository-sha>" >&2
  exit 64
fi

EXPECTED_REPO_SHA="$1"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="$ROOT/repo"
PACKET_REL=research/paper2_oracle_capability_gate_v2_exec
PROTOCOL_SUBJECT_HASH=e20eeadcc7d8b431095db8cfadbd9f9e73841f4fea29ece81302348c2dd542d1
CONTRACT_REL=research/paper2_oracle_capability_gate_v2_exec/BATCH_CONTRACT_V2_EXEC_ORACLE.json
CONTRACT="$REPO/$CONTRACT_REL"
PACKET="$REPO/$PACKET_REL/PROTOCOL_FREEZE_PACKET.json"
PYTHON="$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11"
RECEIPT_ROOT="$ROOT/receipts/oracle_capability_gate_v2_exec"
LOG_ROOT="$ROOT/logs/oracle_capability_gate_v2_exec"
RUN_ROOT="$ROOT/runs/oracle_capability_gate_v2_exec"
SBATCH_REL=experiments/paper2/lunarc/run_oracle_capability_gate_v2_exec_oracle.sbatch
LEARNING_LOOP_MODE=root_cause_v1
DIAGNOSTIC_ARM=ORACLE_PROCEDURE_UPPER_BOUND
MODEL_SNAPSHOT="$ROOT/assets/paper2-model-qwen25-7b-v1/model/Qwen--Qwen2.5-7B-Instruct/a09a35458c702b33eeacc393d103063234e8bc28"

mkdir -p "$RECEIPT_ROOT" "$LOG_ROOT" "$RUN_ROOT"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
test -x "$PYTHON"
test -f "$CONTRACT"
test -f "$REPO/$SBATCH_REL"
test -d "$MODEL_SNAPSHOT"

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
if packet.get("execution_authority",{}).get("oracle_job_authorized_by_this_packet") is not True:
    raise SystemExit("executable packet must authorize ORACLE")
if packet.get("execution_authority",{}).get("authorized_first_oracle_scale") != "Qwen2.5-7B-Instruct":
    raise SystemExit("authorized first ORACLE scale must be 7B")
if packet.get("execution_authority",{}).get("phase0_architecture_authorized") is not False:
    raise SystemExit("phase0 must remain unauthorized")
if packet.get("parent_negative_history",{}).get("reopen_issue_138") is not False:
    raise SystemExit("must not reopen #138")
if packet.get("v4_1_pendulum_compatibility",{}).get("score_reuse_allowed") is not False:
    raise SystemExit("V4.1 score reuse must be forbidden")
forbidden=set(packet.get("v4_1_pendulum_compatibility",{}).get("jobs_explicitly_not_experience_evidence",[]))
if not {3476520,3476521,3476524}.issubset(forbidden): raise SystemExit("missing V4.1 forbidden jobs")
witness=json.loads((repo/"research/paper2_oracle_capability_gate_v2_exec/DIFFERENCE_WITNESS_V2_EXEC.json").read_text(encoding="utf-8"))
if witness.get("explicitly_not_14B_32B_escalation") is not True: raise SystemExit("must refuse 14B/32B")
if witness.get("task_gate_revisit_not_scale_escalation") is not True: raise SystemExit("must be task/gate revisit")
if witness.get("learning_staircase_authorized") is not False: raise SystemExit("learning staircase must remain unauthorized")
if witness.get("reopen_issue_138") is not False: raise SystemExit("witness reopen_issue_138 must be false")
if packet.get("primary_execution",{}).get("model_scale") != "Qwen2.5-7B-Instruct":
    raise SystemExit("packet model_scale must be 7B")
if packet.get("model",{}).get("model_id") != "Qwen/Qwen2.5-7B-Instruct":
    raise SystemExit("packet model_id must be Qwen2.5-7B-Instruct")
if list(packet.get("transfer_task_ids",[])) != ["T1","T2","T3","T4","T5"]:
    raise SystemExit("transfer set must be sealed T1–T5")
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
  "schema_version":"paper2-oracle-capability-gate-submission-receipt-v1",
  "created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
  "issue":379,
  "section":"PHASE1_ORACLE_7B_V2_EXEC",
  "verdict":"SUBMITTED_ORACLE_CAPABILITY_GATE_V2_0_EXEC",
  "expected_repo_sha":sha,
  "slurm_job_id":job,
  "protocol_subject_hash":protocol_hash,
  "protocol_freeze_packet_sha256":packet_sha,
  "batch_contract_sha256":batch_sha,
  "arms":["ORACLE_PROCEDURE_UPPER_BOUND"],
  "phases":["FRESH_TRANSFER"],
  "transfer_task_ids":["T1","T2","T3","T4","T5"],
  "learning_loop_mode":"root_cause_v1",
  "diagnostic_arm":"ORACLE_PROCEDURE_UPPER_BOUND",
  "model_scale":"Qwen2.5-7B-Instruct",
  "CAPABLE_MODEL_AVAILABLE":"NO_REFUTED",
  "v4_1_score_reuse_allowed":False,
  "v4_1_jobs_not_evidence":[3476520,3476521,3476524],
  "paper3_issue_217_path":False,
  "experience_benchmark_7B_submitted":True,
  "reopen_issue_138":False,
  "reinterpret_parent_job_3476788_as_lift":False,
  "reinterpret_parent_job_3476778_as_lift":False,
  "reinterpret_parent_job_3476756_as_lift":False,
  "model_execution_observed_by_submitter":False,
  "claim_boundary":"Submission receipt only for #379 V2_0_EXEC 7B ORACLE after sealed tasks freeze. Not manuscript authority. Not experience-learning efficacy.",
}
tmp=out.with_suffix(out.suffix+".tmp")
tmp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
tmp.replace(out)
PY

echo "$JOB_ID"
