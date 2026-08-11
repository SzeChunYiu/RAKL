#!/usr/bin/env bash
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=9G
#SBATCH --job-name=p2-pend-v4
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/v4/p2-pend-v4-%j.out
#SBATCH --error=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/v4/p2-pend-v4-%j.err

set -euo pipefail

ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="$ROOT/repo"
STAGED="$ROOT/assets/paper2-cpu-v3-2"
PYTHON="$STAGED/runtime/python/bin/python3.11"
PACKET_REL=research/paper2_microtrial_v4/EXECUTION_PACKET_V4_20260811.json
BATCH_CONTRACT_REL=research/paper2_microtrial_v4/BATCH_CONTRACT_V4.json
SCHEMA_REL=schemas/paper2-pendulum-microtrial-result.schema.json
TASK_SEED_BUILDER_REL=experiments/paper2/lunarc/build_task_seed_receipt_v4.py
ATTESTER_REL=experiments/paper2/lunarc/attest_model_snapshot_v4.py
ATTESTATION_SCHEMA_REL=schemas/paper2-model-snapshot-attestation-v4.schema.json
TASK_SEED_SCHEMA_REL=schemas/paper2-pendulum-task-seed-receipt-v4.schema.json
MODEL_MANIFEST_REL=research/paper2_microtrial_v4/MODEL_MANIFEST_V4.json
TOKENIZER_MANIFEST_REL=research/paper2_microtrial_v4/TOKENIZER_MANIFEST_V4.json

: "${EXPECTED_REPO_SHA:?EXPECTED_REPO_SHA is required}"
: "${BATCH_CONTRACT_SHA256:?BATCH_CONTRACT_SHA256 is required}"
: "${SLURM_JOB_ID:?SLURM_JOB_ID is required}"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"

test -x "$PYTHON"
test "$(sha256sum "$REPO/$BATCH_CONTRACT_REL" | awk '{print $1}')" = "$BATCH_CONTRACT_SHA256"
test "$(git -C "$REPO" rev-parse HEAD)" = "$EXPECTED_REPO_SHA"
test -z "$(git -C "$REPO" status --porcelain --untracked-files=all)"
git -C "$REPO" merge-base --is-ancestor af2d0be61522d1f8f657a48daaf6369ff3e44a3e "$EXPECTED_REPO_SHA"
test "$(git -C "$REPO" remote get-url origin)" = "https://github.com/SzeChunYiu/RAKL.git"

cd "$REPO"
RUN_ROOT="$ROOT/runs/v4"
OUTPUT_DIR="$RUN_ROOT/PENDULUM_SEALED_KNOWN_ANSWER_001-seed-17-job-${SLURM_JOB_ID}"
ATTESTATION_DIR="$ROOT/receipts/v4/job-${SLURM_JOB_ID}"
test ! -e "$OUTPUT_DIR"
test ! -e "$ATTESTATION_DIR"
mkdir -p "$ATTESTATION_DIR"
CREATED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

"$PYTHON" "$ATTESTER_REL" \
  --repo "$REPO" \
  --packet "$PACKET_REL" \
  --model-manifest "$MODEL_MANIFEST_REL" \
  --tokenizer-manifest "$TOKENIZER_MANIFEST_REL" \
  --schema "$ATTESTATION_SCHEMA_REL" \
  --phase PRE_INFERENCE \
  --output "$ATTESTATION_DIR/model_snapshot_pre.json"

PYTHONPATH="$REPO/src" "$PYTHON" -m rakl.paper2_pendulum_microtrial run \
  "$PACKET_REL" \
  --output-dir "$OUTPUT_DIR" \
  --created-at-utc "$CREATED_AT_UTC"

"$PYTHON" "$ATTESTER_REL" \
  --repo "$REPO" \
  --packet "$PACKET_REL" \
  --model-manifest "$MODEL_MANIFEST_REL" \
  --tokenizer-manifest "$TOKENIZER_MANIFEST_REL" \
  --schema "$ATTESTATION_SCHEMA_REL" \
  --phase POST_INFERENCE \
  --result "$OUTPUT_DIR/result_receipt.json" \
  --output "$ATTESTATION_DIR/model_snapshot_post.json"

"$PYTHON" "$TASK_SEED_BUILDER_REL" \
  --packet "$PACKET_REL" \
  --result "$OUTPUT_DIR/result_receipt.json" \
  --result-schema "$SCHEMA_REL" \
  --task-seed-schema "$TASK_SEED_SCHEMA_REL" \
  --pre-attestation "$ATTESTATION_DIR/model_snapshot_pre.json" \
  --post-attestation "$ATTESTATION_DIR/model_snapshot_post.json" \
  --attestation-schema "$ATTESTATION_SCHEMA_REL" \
  --output "$OUTPUT_DIR/task_seed_receipt.json"

sha256sum \
  "$ATTESTATION_DIR/model_snapshot_pre.json" \
  "$OUTPUT_DIR/result_receipt.json" \
  "$ATTESTATION_DIR/model_snapshot_post.json" \
  "$OUTPUT_DIR/task_seed_receipt.json"
