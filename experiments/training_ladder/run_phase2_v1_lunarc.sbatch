#!/bin/bash
# Paper IV Phase-2 (#466) exact five-arm Adaptive-vs-Static execution on LUNARC A100.
#
# Resource-portability successor only.  It does NOT change PROTOCOL_V3.json,
# INFERENCE_PLAN.json, model revision, LoRA configuration, seeds, arms, MDE,
# safety gates or evaluator.  It exposes the already staged exact 7B snapshot to
# huggingface_hub through an offline cache layout so phase2_adaptive_v1.py can run
# without a Hub/network dependency on the compute node.
#
#SBATCH -A lu2026-2-51
#SBATCH -p gpua100
#SBATCH --gres=gpu:a100:1
#SBATCH -t 12:00:00
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -J orion_p4_phase2
#SBATCH -o orion_p4_phase2_%j.out
#SBATCH -e orion_p4_phase2_%j.err

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/projects/hep/fs9/users/scyiu/orion}"
ASSET_ROOT="${ASSET_ROOT:-/projects/hep/fs9/users/scyiu/RAKL-paper2/assets}"
MODEL_ROOT="${MODEL_ROOT:-$ASSET_ROOT/paper2-model-qwen25-7b-v1/model/Qwen--Qwen2.5-7B-Instruct}"
MODEL_REVISION="a09a35458c702b33eeacc393d103063234e8bc28"
MODEL_ID="Qwen/Qwen2.5-7B-Instruct"
OUT_DIR="${OUT_DIR:-$REPO_ROOT/experiments/training_ladder/phase2_v1_out/${SLURM_JOB_ID:-local}}"
VENV_DIR="${VENV_DIR:-$HOME/.venvs/rakl-paper4-phase2}"
SUBJECT_SHA="${SUBJECT_SHA:-}"

cd "$REPO_ROOT"
if [ -n "$SUBJECT_SHA" ]; then
  test "$(git rev-parse HEAD)" = "$SUBJECT_SHA" || {
    echo "[phase2] ERROR repository subject mismatch" >&2; exit 3;
  }
fi

echo "[phase2] host=$(hostname) job=${SLURM_JOB_ID:-local}"
echo "[phase2] repo=$(git rev-parse HEAD)"
echo "[phase2] exact model=$MODEL_ID@$MODEL_REVISION"
echo "[phase2] output=$OUT_DIR"

module purge 2>/dev/null || true
module load PyTorch/2.1.2-foss-2023a-CUDA-12.1.1 2>/dev/null \
  || echo "[phase2] PyTorch module unavailable; using venv CUDA torch"

if [ ! -d "$VENV_DIR" ]; then
  python -m venv --system-site-packages "$VENV_DIR"
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  python -m pip install --upgrade pip
  python -m pip install "torch" "transformers" "huggingface_hub" "peft>=0.10" "accelerate>=0.27"
else
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
fi

python - <<'PY'
import torch
print('[phase2] torch', torch.__version__, 'cuda', torch.cuda.is_available())
if not torch.cuda.is_available():
    raise SystemExit('CUDA unavailable: do not substitute another model/runtime')
PY

# Locate the exact staged revision.  Phase-1 v2 already used this staged asset.
if [ -f "$MODEL_ROOT/$MODEL_REVISION/config.json" ]; then
  MODEL_DIR="$MODEL_ROOT/$MODEL_REVISION"
elif [ -f "$MODEL_ROOT/config.json" ]; then
  MODEL_DIR="$MODEL_ROOT"
else
  MODEL_DIR="$(find "$MODEL_ROOT" -maxdepth 3 -path "*/$MODEL_REVISION/config.json" -printf '%h\n' 2>/dev/null | head -1)"
fi
if [ -z "${MODEL_DIR:-}" ] || [ ! -f "$MODEL_DIR/config.json" ]; then
  echo "[phase2] ERROR exact staged revision not found under $MODEL_ROOT" >&2
  exit 4
fi

echo "[phase2] staged model dir=$MODEL_DIR"

# Build the cache shape snapshot_download(repo_id, revision=<exact hash>) expects.
CACHE_ROOT="${TMPDIR:-/tmp}/orion-p4-hf-cache-${SLURM_JOB_ID:-$$}"
SNAP_DIR="$CACHE_ROOT/models--Qwen--Qwen2.5-7B-Instruct/snapshots/$MODEL_REVISION"
mkdir -p "$(dirname "$SNAP_DIR")"
ln -s "$MODEL_DIR" "$SNAP_DIR"
export HF_HUB_CACHE="$CACHE_ROOT"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONHASHSEED=0
export PYTHONPATH="$REPO_ROOT/src:$REPO_ROOT:${PYTHONPATH:-}"

mkdir -p "$OUT_DIR"
python -m experiments.training_ladder.phase2_adaptive_v1 --outdir "$OUT_DIR"

test -s "$OUT_DIR/FINAL_RECEIPT.json"
python - <<PY
import json, pathlib
p = json.loads(pathlib.Path('$OUT_DIR/FINAL_RECEIPT.json').read_text())
assert p['model_id'] == '$MODEL_ID'
assert p['model_revision'] == '$MODEL_REVISION'
assert p.get('grants_scientific_authority') is False
print('[phase2] terminal=', p['terminal'])
PY
sha256sum "$OUT_DIR/FINAL_RECEIPT.json" "$OUT_DIR/DATA_MANIFEST.json" > "$OUT_DIR/SHA256SUMS.txt"
echo "[phase2] complete: $OUT_DIR"
