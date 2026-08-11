#!/bin/bash
# Gate-authorized single-GPU Paper 3 frozen-model inference template. The input
# weights are hashed before and after execution and mutation fails the receipt.
#SBATCH --job-name=rakl_p3_infer
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --time=04:00:00

set -euo pipefail
: "${RAKL_EXPERIMENT_MANIFEST:?missing manifest}"
: "${RAKL_GATE_RECEIPT:?missing gate receipt}"
: "${RAKL_EXPECTED_SUBJECT_SHA:?missing exact subject}"
: "${RAKL_EXPECTED_MANIFEST_SHA256:?missing manifest hash}"
: "${RAKL_EXPECTED_GATE_SHA256:?missing gate hash}"
: "${RAKL_REPO_PATH:?missing exact repository path}"
: "${RAKL_PYTHON_EXECUTABLE:?missing frozen Python executable}"

exec "$RAKL_PYTHON_EXECUTABLE" \
  "$RAKL_REPO_PATH/experiments/paper3/lunarc/gated_workload_runtime.py" \
  --expected-workload inference
