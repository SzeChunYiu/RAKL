#!/bin/bash
# Gate-authorized single-GPU Paper 3 training template. Submission is performed
# only through python -m rakl.paper3_lunarc_workload; never call sbatch directly.
#SBATCH --job-name=rakl_p3_train
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=1-00:00:00

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
  --expected-workload training
