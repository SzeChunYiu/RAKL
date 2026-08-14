#!/bin/bash
#SBATCH -A lu2026-2-51
#SBATCH -p gpua100
#SBATCH --gres=gpu:a100:1
#SBATCH -t 02:00:00
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -J orion_p3_cap_v3s2
#SBATCH -o orion_p3_cap_v3s2_%j.out
#SBATCH -e orion_p3_cap_v3s2_%j.err

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/projects/hep/fs9/users/scyiu/orion}"
SUBJECT_SHA="${SUBJECT_SHA:?SUBJECT_SHA must bind the exact repository candidate}"
VENV_DIR="${VENV_DIR:-$HOME/.venvs/rakl-paper4}"
MODEL_PATH="${MODEL_PATH:-/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/paper2-model-qwen25-7b-v1/model/Qwen--Qwen2.5-7B-Instruct/a09a35458c702b33eeacc393d103063234e8bc28}"
OUT_DIR="${OUT_DIR:-$REPO_ROOT/research/empirical_10_of_10_v1/CAPABILITY_QUALIFICATION/STAGE4_SCORING_V2_RUN_${SLURM_JOB_ID:-manual}}"

module purge 2>/dev/null || true
module load PyTorch/2.1.2-foss-2023a-CUDA-12.1.1

if [ ! -d "$VENV_DIR" ]; then
  echo "RESOURCE_BLOCKED: required frozen venv missing before runner can emit a receipt: $VENV_DIR" >&2
  exit 20
fi
source "$VENV_DIR/bin/activate"

cd "$REPO_ROOT"
git fetch origin "$SUBJECT_SHA"
git checkout --detach "$SUBJECT_SHA"
test "$(git rev-parse HEAD)" = "$SUBJECT_SHA"

export PYTHONPATH="$REPO_ROOT/src:${PYTHONPATH:-}"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONHASHSEED=0

python - <<'PY'
import torch, transformers
assert torch.cuda.is_available(), 'cuda unavailable'
assert transformers.__version__ == '4.55.0', transformers.__version__
print('runtime', {'torch': torch.__version__, 'transformers': transformers.__version__, 'gpu': torch.cuda.get_device_name(0)})
PY

test -f "$MODEL_PATH/config.json"
test -f research/empirical_10_of_10_v1/CAPABILITY_QUALIFICATION/STAGE3_5_SCORING_HARDENING_V2.json

# Pre-outcome dry run reproduces the unchanged panel and blind shortcut controls.
python experiments/paper3/run_capability_stage4_v2.py \
  --outdir "$OUT_DIR/dry_run" \
  --dry-run

# The denominator-evasion falsifier must fail closed before any model output.
python -m pytest -q tests/test_p3_capability_scoring_hardening_v2.py

# The model runner deliberately uses distinct process codes for scientific
# PASS/FAIL/resource/degenerate terminals. Capture that code rather than letting
# `set -e` convert a valid scientific negative into scheduler failure.
set +e
python experiments/paper3/run_capability_stage4_v2.py \
  --outdir "$OUT_DIR" \
  --model-path "$MODEL_PATH"
RUNNER_CODE=$?
set -e

# A complete registered Stage-5 receipt means the scheduled execution attempt
# itself completed. This validator checks that runner code and terminal agree;
# only then does the wrapper exit 0 so harvest reads the scientific terminal.
python experiments/paper3/validate_capability_stage4_v2_terminal.py \
  "$OUT_DIR/FINAL_CAPABILITY_RECEIPT.json" "$RUNNER_CODE"

echo "qualification receipt: $OUT_DIR/FINAL_CAPABILITY_RECEIPT.json"
