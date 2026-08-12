#!/bin/bash
# Paper IV Phase-1 (#461) exposure executor — LUNARC A100 batch template.
#
# NOTE: this job CHARGES compute allocation lu2026-2-51 (project account below).
# It runs the frozen-protocol exposure ladder on the staged Qwen model and emits
# exposure_outcomes.jsonl + run_manifest.json. It is a Phase 0/1 instrument only:
# grants_scientific_authority=false. Review the outputs; this script does not
# submit or promote anything.
#
#SBATCH -A lu2026-2-51
#SBATCH -p gpua100
#SBATCH --gres=gpu:a100:1
#SBATCH -t 12:00:00
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -J rakl_p4_phase1
#SBATCH -o rakl_p4_phase1_%j.out
#SBATCH -e rakl_p4_phase1_%j.err

set -euo pipefail

# --------------------------------------------------------------------------- #
# Parameters (override on submit, e.g. `sbatch --export=ALL,MODEL_PATH=... run_phase1.sbatch`)
# --------------------------------------------------------------------------- #
# Staged Qwen ladder lives under /projects/hep/fs9/users/scyiu/RAKL-paper2/assets/*/model
REPO_ROOT="${REPO_ROOT:-/projects/hep/fs9/users/scyiu/orion}"
ASSET_ROOT="${ASSET_ROOT:-/projects/hep/fs9/users/scyiu/RAKL-paper2/assets}"
# Staged Qwen ladder (exact dirs):
#   0.5B: $ASSET_ROOT/paper2-cpu-v3-2/model/Qwen--Qwen2.5-0.5B-Instruct
#   1.5B: $ASSET_ROOT/paper2-model-qwen25-1_5b-v4-3/model/Qwen--Qwen2.5-1.5B-Instruct
#   3B:   $ASSET_ROOT/paper2-model-qwen25-3b-v1/model/Qwen--Qwen2.5-3B-Instruct
#   7B:   $ASSET_ROOT/paper2-model-qwen25-7b-v1/model/Qwen--Qwen2.5-7B-Instruct
MODEL_PATH="${MODEL_PATH:-$ASSET_ROOT/paper2-cpu-v3-2/model/Qwen--Qwen2.5-0.5B-Instruct}"
MAX_EXPOSURE="${MAX_EXPOSURE:-64}"
FAMILIES="${FAMILIES:-sequence_composition,balance_conservation,state_reachability}"
OUT_DIR="${OUT_DIR:-$REPO_ROOT/experiments/training_ladder/phase1_out}"
PACKET_DIR="${PACKET_DIR:-$REPO_ROOT/research/paper4_training_ladder_461}"
VENV_DIR="${VENV_DIR:-$HOME/.venvs/rakl-paper4}"

echo "[phase1] host=$(hostname) job=${SLURM_JOB_ID:-local}"
echo "[phase1] charging allocation: lu2026-2-51"
echo "[phase1] model_path=$MODEL_PATH"
echo "[phase1] out_dir=$OUT_DIR"

# --------------------------------------------------------------------------- #
# Environment: LUNARC PyTorch toolchain + a venv for peft/accelerate on top.
# --------------------------------------------------------------------------- #
# A PyTorch module is preferred but optional (name varies across the stack); the venv
# self-contains a CUDA torch either way. Do not let a failed module load abort the job.
module purge 2>/dev/null || true
module load PyTorch/2.1.2-foss-2023a-CUDA-12.1.1 2>/dev/null \
  || echo "[phase1] PyTorch module unavailable; using the venv's own CUDA torch"

if [ ! -d "$VENV_DIR" ]; then
  echo "[phase1] creating venv at $VENV_DIR"
  python -m venv --system-site-packages "$VENV_DIR"
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  python -m pip install --upgrade pip
  # Install torch too (no-op if inherited from a module); + LoRA/training extras.
  python -m pip install "torch" "peft>=0.10" "accelerate>=0.27"
else
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
fi

python -c "import torch; print('[phase1] torch', torch.__version__, 'cuda', torch.cuda.is_available())"

# --------------------------------------------------------------------------- #
# Run the executor against the staged model. Offline: no hub downloads on nodes.
# --------------------------------------------------------------------------- #
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONHASHSEED=0

# Staged models use an HF-cache layout (a revision-hash subdir holds config.json +
# weights). Auto-resolve MODEL_PATH to the directory that actually contains config.json.
if [ ! -f "$MODEL_PATH/config.json" ]; then
  resolved="$(find "$MODEL_PATH" -maxdepth 2 -name config.json -printf '%h\n' 2>/dev/null | head -1)"
  if [ -n "$resolved" ]; then
    MODEL_PATH="$resolved"
    echo "[phase1] resolved model dir -> $MODEL_PATH"
  else
    echo "[phase1] ERROR: no config.json under $MODEL_PATH" >&2; exit 2
  fi
fi

cd "$REPO_ROOT"
# Make the 'orion' package importable (orion -> rakl impl) without installing.
export PYTHONPATH="$REPO_ROOT/src:${PYTHONPATH:-}"
python experiments/training_ladder/exposure_executor.py \
  --model "$MODEL_PATH" \
  --families "$FAMILIES" \
  --max-exposure "$MAX_EXPOSURE" \
  --packet-dir "$PACKET_DIR" \
  --out "$OUT_DIR" \
  --device cuda

echo "[phase1] done. outcomes: $OUT_DIR/exposure_outcomes.jsonl ; manifest: $OUT_DIR/run_manifest.json"
echo "[phase1] reminder: Phase 0/1 instrument only; grants_scientific_authority=false."
