#!/usr/bin/env bash
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --job-name=p2-pend-v4-3
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/v4_3/p2-pend-v4-3-%j.out
#SBATCH --error=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/v4_3/p2-pend-v4-3-%j.err
set -euo pipefail
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="$ROOT/repo"
PYTHON="$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11"
PACKET_REL=research/paper2_microtrial_v4_3/EXECUTION_PACKET_V4_3_20260811.json
BATCH_CONTRACT_REL=research/paper2_microtrial_v4_3/BATCH_CONTRACT_V4_3.json
RESULT_SCHEMA_REL=schemas/paper2-pendulum-microtrial-result.schema.json
TASK_SEED_BUILDER_REL=experiments/paper2/lunarc/build_task_seed_receipt_v4_3.py
ATTESTER_REL=experiments/paper2/lunarc/attest_model_snapshot_v4.py
ATTESTATION_SCHEMA_REL=schemas/paper2-model-snapshot-attestation-v4.schema.json
TASK_SEED_SCHEMA_REL=schemas/paper2-pendulum-task-seed-receipt-v4-3.schema.json
MODEL_MANIFEST_REL=research/paper2_microtrial_v4_3/MODEL_MANIFEST_V4_3.json
TOKENIZER_MANIFEST_REL=research/paper2_microtrial_v4_3/TOKENIZER_MANIFEST_V4_3.json
: "${EXPECTED_REPO_SHA:?}"
: "${BATCH_CONTRACT_SHA256:?}"
: "${SLURM_JOB_ID:?}"
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}" MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
test -x "$PYTHON"
test "$(sha256sum "$REPO/$BATCH_CONTRACT_REL" | awk '{print $1}')" = "$BATCH_CONTRACT_SHA256"
test "$(git -C "$REPO" rev-parse HEAD)" = "$EXPECTED_REPO_SHA"
test "$(git -C "$REPO" rev-parse refs/remotes/origin/main)" = "$EXPECTED_REPO_SHA"
test -z "$(git -C "$REPO" status --porcelain --untracked-files=all)"
git -C "$REPO" merge-base --is-ancestor 0f1f9f6072f878a745c5a5d549d8b07db7e46961 "$EXPECTED_REPO_SHA"
test "$(git -C "$REPO" remote get-url origin)" = "https://github.com/SzeChunYiu/RAKL.git"
"$PYTHON" - "$REPO" "$REPO/$BATCH_CONTRACT_REL" "$EXPECTED_REPO_SHA" <<'PY'
import hashlib, json, pathlib, subprocess, sys
repo=pathlib.Path(sys.argv[1]); contract_path=pathlib.Path(sys.argv[2]); expected=sys.argv[3]
contract=json.loads(contract_path.read_text(encoding="utf-8"))
assert contract.get("output_normalization_policy_id") == "PENDULUM_EXACT_JSON_OR_SINGLE_LOWERCASE_JSON_FENCE_V4_1"
assert contract.get("prompt_interface_policy_id") == "PENDULUM_FIELD_POLARITY_AND_STOP_AFTER_JSON_V4_2"
assert contract.get("chronology_class") == "MODEL_SCALE_STAGING_REPLAY_FRESH_ONLY_TO_V4_3_OUTPUTS"
assert contract.get("threshold_or_score_change_permitted") is False
if subprocess.run(["git","merge-base","--is-ancestor",contract["minimum_execution_ancestor_sha"],expected],cwd=repo).returncode:
    raise SystemExit("packet parent is not an ancestor")
for binding in contract["bindings"]:
    path=repo/binding["path"]
    if not path.is_file(): raise SystemExit(f"allocated binding missing:{binding['role']}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != binding["sha256"]:
        raise SystemExit(f"allocated binding mismatch:{binding['role']}")
model=json.loads((repo/"research/paper2_microtrial_v4_3/MODEL_MANIFEST_V4_3.json").read_text())
assert model.get("model_id")=="Qwen/Qwen2.5-1.5B-Instruct"
assert model.get("revision")=="989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
PY
cd "$REPO"
RUN_ROOT="$ROOT/runs/v4_3"
OUTPUT_DIR="$RUN_ROOT/PENDULUM_SEALED_KNOWN_ANSWER_001-seed-17-job-${SLURM_JOB_ID}"
RECEIPT_DIR="$ROOT/receipts/v4_3/job-${SLURM_JOB_ID}"
test ! -e "$OUTPUT_DIR"; test ! -e "$RECEIPT_DIR"
mkdir -p "$RECEIPT_DIR" "$ROOT/logs/v4_3" "$RUN_ROOT"
CREATED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
PYTHONPATH="$REPO/src" "$PYTHON" -m rakl.paper2_pendulum_microtrial preflight "$PACKET_REL" --output "$RECEIPT_DIR/allocated_preflight.json" --created-at-utc "$CREATED_AT_UTC"
"$PYTHON" "$ATTESTER_REL" --repo "$REPO" --packet "$PACKET_REL" --model-manifest "$MODEL_MANIFEST_REL" --tokenizer-manifest "$TOKENIZER_MANIFEST_REL" --schema "$ATTESTATION_SCHEMA_REL" --phase PRE_INFERENCE --output "$RECEIPT_DIR/model_snapshot_pre.json"
PYTHONPATH="$REPO/src" "$PYTHON" -m rakl.paper2_pendulum_microtrial_v4_3 "$PACKET_REL" --output-dir "$OUTPUT_DIR" --created-at-utc "$CREATED_AT_UTC" --expected-checkout-head-sha "$EXPECTED_REPO_SHA"
"$PYTHON" "$ATTESTER_REL" --repo "$REPO" --packet "$PACKET_REL" --model-manifest "$MODEL_MANIFEST_REL" --tokenizer-manifest "$TOKENIZER_MANIFEST_REL" --schema "$ATTESTATION_SCHEMA_REL" --phase POST_INFERENCE --result "$OUTPUT_DIR/result_receipt.json" --output "$RECEIPT_DIR/model_snapshot_post.json"
"$PYTHON" "$TASK_SEED_BUILDER_REL" --packet "$PACKET_REL" --result "$OUTPUT_DIR/result_receipt.json" --run-manifest "$OUTPUT_DIR/run_manifest.json" --result-schema "$RESULT_SCHEMA_REL" --task-seed-schema "$TASK_SEED_SCHEMA_REL" --pre-attestation "$RECEIPT_DIR/model_snapshot_pre.json" --post-attestation "$RECEIPT_DIR/model_snapshot_post.json" --attestation-schema "$ATTESTATION_SCHEMA_REL" --output "$OUTPUT_DIR/task_seed_receipt.json"
