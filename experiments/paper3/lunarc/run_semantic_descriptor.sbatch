#!/usr/bin/env bash
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --job-name=p3-bge-desc
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper3/logs/semantic-v1/p3-bge-desc-%j.out
#SBATCH --error=/projects/hep/fs9/users/scyiu/RAKL-paper3/logs/semantic-v1/p3-bge-desc-%j.err

set -euo pipefail
umask 077

ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper3
REPO="$ROOT/repo"
RUNTIME_ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/paper2-cpu-v3-2/runtime/python
PYTHON="$RUNTIME_ROOT/bin/python3.11"
CONTRACT="$REPO/research/paper3_semantic_descriptor_lunarc/CONTRACT_V1.json"
OUTPUT="$ROOT/semantic_descriptor_v1/receipts/descriptor-execution-${SLURM_JOB_ID}.json"

: "${RAKL_EXPECTED_REPO_SHA:?RAKL_EXPECTED_REPO_SHA is required}"
: "${RAKL_CONTRACT_SHA256:?RAKL_CONTRACT_SHA256 is required}"
: "${RAKL_STAGE_HARVEST_PATH:?RAKL_STAGE_HARVEST_PATH is required}"
: "${RAKL_STAGE_HARVEST_SHA256:?RAKL_STAGE_HARVEST_SHA256 is required}"
: "${SLURM_JOB_ID:?SLURM_JOB_ID is required}"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME="${TMPDIR:-/tmp}/paper3-hf-${SLURM_JOB_ID}"
export TORCH_HOME="${TMPDIR:-/tmp}/paper3-torch-${SLURM_JOB_ID}"
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
test -x "$PYTHON"
test "$(git -C "$REPO" rev-parse HEAD)" = "$RAKL_EXPECTED_REPO_SHA"
test -z "$(git -C "$REPO" status --porcelain --untracked-files=all)"
test "$(sha256sum "$CONTRACT" | awk '{print $1}')" = "$RAKL_CONTRACT_SHA256"
test "$(sha256sum "$RAKL_STAGE_HARVEST_PATH" | awk '{print $1}')" = "$RAKL_STAGE_HARVEST_SHA256"

cd "$REPO"
PYTHONPATH="$REPO/src" exec "$PYTHON" \
  experiments/paper3/lunarc/semantic_descriptor_runtime.py \
  --repo "$REPO" \
  --contract "$CONTRACT" \
  --stage-harvest "$RAKL_STAGE_HARVEST_PATH" \
  --output "$OUTPUT"
