#!/usr/bin/env bash
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --job-name=p2-orcl-v2exec
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/oracle_capability_gate_v2_exec/p2-orcl-v2exec-%j.out
#SBATCH --error=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/oracle_capability_gate_v2_exec/p2-orcl-v2exec-%j.err

set -euo pipefail

ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="$ROOT/repo"
STAGED="$ROOT/assets/paper2-cpu-v3-2"
PYTHON="$STAGED/runtime/python/bin/python3.11"
PACKET_REL=research/paper2_oracle_capability_gate_v2_exec/PROTOCOL_FREEZE_PACKET.json
CONTRACT_REL=research/paper2_oracle_capability_gate_v2_exec/BATCH_CONTRACT_V2_EXEC_ORACLE.json
RUNNER_MODULE=rakl.paper2_experience_benchmark_runner

: "${EXPECTED_REPO_SHA:?EXPECTED_REPO_SHA is required}"
: "${BATCH_CONTRACT_SHA256:?BATCH_CONTRACT_SHA256 is required}"
: "${PROTOCOL_SUBJECT_HASH:?PROTOCOL_SUBJECT_HASH is required}"
: "${LEARNING_LOOP_MODE:?LEARNING_LOOP_MODE is required}"
: "${DIAGNOSTIC_ARM:?DIAGNOSTIC_ARM is required}"
: "${SLURM_JOB_ID:?SLURM_JOB_ID is required}"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"

test -x "$PYTHON"
test "$LEARNING_LOOP_MODE" = "root_cause_v1"
test "$DIAGNOSTIC_ARM" = "ORACLE_PROCEDURE_UPPER_BOUND"
test "$(sha256sum "$REPO/$CONTRACT_REL" | awk '{print $1}')" = "$BATCH_CONTRACT_SHA256"
test "$(git -C "$REPO" rev-parse HEAD)" = "$EXPECTED_REPO_SHA"
test "$(git -C "$REPO" rev-parse refs/remotes/origin/main)" = "$EXPECTED_REPO_SHA"
test -z "$(git -C "$REPO" status --porcelain --untracked-files=all)"
test "$(git -C "$REPO" remote get-url origin)" = "https://github.com/SzeChunYiu/RAKL.git"

"$PYTHON" - "$REPO" "$REPO/$PACKET_REL" "$REPO/$CONTRACT_REL" "$EXPECTED_REPO_SHA" "$PROTOCOL_SUBJECT_HASH" <<'PY'
import hashlib, json, pathlib, subprocess, sys
repo=pathlib.Path(sys.argv[1]); packet_path=pathlib.Path(sys.argv[2]); contract_path=pathlib.Path(sys.argv[3])
expected=sys.argv[4]; protocol_hash=sys.argv[5]
packet=json.loads(packet_path.read_text(encoding="utf-8"))
contract=json.loads(contract_path.read_text(encoding="utf-8"))
if packet.get("protocol_subject_hash") != protocol_hash: raise SystemExit("protocol hash mismatch")
if contract.get("protocol_subject_hash") != protocol_hash: raise SystemExit("contract protocol hash mismatch")
if packet.get("learning_loop_mode") != "root_cause_v1": raise SystemExit("learning loop mismatch")
if packet.get("model",{}).get("model_id") != "Qwen/Qwen2.5-7B-Instruct": raise SystemExit("expected 7B model")
if packet.get("primary_execution",{}).get("model_scale") != "Qwen2.5-7B-Instruct": raise SystemExit("expected 7B scale")
if packet.get("execution_authority",{}).get("oracle_job_authorized_by_this_packet") is not True:
    raise SystemExit("ORACLE not authorized by packet")
if list(packet.get("transfer_task_ids",[])) != ["T1","T2","T3","T4","T5"]:
    raise SystemExit("expected sealed T1–T5")
if packet.get("v4_1_pendulum_compatibility",{}).get("score_reuse_allowed") is not False:
    raise SystemExit("V4.1 reuse still forbidden")
if subprocess.run(["git","merge-base","--is-ancestor",contract["minimum_execution_ancestor_sha"],expected],cwd=repo).returncode:
    raise SystemExit("ancestor check failed")
for binding in contract["bindings"]:
    path=repo/binding["path"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != binding["sha256"]:
        raise SystemExit(f"allocated binding mismatch:{binding['role']}")
PY

cd "$REPO"
OUTPUT_DIR="$ROOT/runs/oracle_capability_gate_v2_exec/paper2-oracle-capability-gate-v2-exec-oracle-job-${SLURM_JOB_ID}"
RECEIPT_DIR="$ROOT/receipts/oracle_capability_gate_v2_exec/job-${SLURM_JOB_ID}"
test ! -e "$OUTPUT_DIR"
test ! -e "$RECEIPT_DIR"
mkdir -p "$RECEIPT_DIR"
CREATED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

PYTHONPATH="$REPO/src" "$PYTHON" -m "$RUNNER_MODULE" \
  --repo "$REPO" \
  --output-dir "$OUTPUT_DIR" \
  --expected-repo-sha "$EXPECTED_REPO_SHA" \
  --scheduler-job-id "$SLURM_JOB_ID" \
  --created-at-utc "$CREATED_AT_UTC" \
  --packet-rel research/paper2_oracle_capability_gate_v2_exec \
  --protocol-subject-hash "$PROTOCOL_SUBJECT_HASH" \
  --learning-loop-mode "$LEARNING_LOOP_MODE" \
  --diagnostic-arm "$DIAGNOSTIC_ARM"

sha256sum \
  "$OUTPUT_DIR/run_manifest.json" \
  "$OUTPUT_DIR/runs.jsonl" \
  "$OUTPUT_DIR/states/Sn.json" \
  "$OUTPUT_DIR/states/Sn.hash" | tee "$RECEIPT_DIR/artifact_sha256sums.txt"
