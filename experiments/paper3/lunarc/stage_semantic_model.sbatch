#!/usr/bin/env bash
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --job-name=p3-bge-stage
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper3/logs/semantic-v1/p3-bge-stage-%j.out
#SBATCH --error=/projects/hep/fs9/users/scyiu/RAKL-paper3/logs/semantic-v1/p3-bge-stage-%j.err

set -euo pipefail
umask 077

ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper3
REPO="$ROOT/repo"
PYTHON=/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11
CONTRACT="$REPO/research/paper3_semantic_descriptor_lunarc/CONTRACT_V1.json"
OUTPUT="$ROOT/semantic_descriptor_v1/receipts/model-stage-execution-${SLURM_JOB_ID}.json"

: "${RAKL_EXPECTED_REPO_SHA:?RAKL_EXPECTED_REPO_SHA is required}"
: "${RAKL_CONTRACT_SHA256:?RAKL_CONTRACT_SHA256 is required}"
: "${SLURM_JOB_ID:?SLURM_JOB_ID is required}"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
export HF_HUB_DISABLE_TELEMETRY=1
test -x "$PYTHON"
test "$(git -C "$REPO" rev-parse HEAD)" = "$RAKL_EXPECTED_REPO_SHA"
test -z "$(git -C "$REPO" status --porcelain --untracked-files=all)"
test "$(sha256sum "$CONTRACT" | awk '{print $1}')" = "$RAKL_CONTRACT_SHA256"

exec "$PYTHON" "$REPO/experiments/paper3/lunarc/stage_semantic_model.py" \
  --repo "$REPO" \
  --contract "$CONTRACT" \
  --output "$OUTPUT"
