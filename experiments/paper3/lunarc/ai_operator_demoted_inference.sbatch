#!/bin/bash
# Demoted AI_OPERATOR Paper3 inference pilot. Not confirmatory human-gate compute.
#SBATCH --job-name=rakl_p3_aiop_infer
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=0-02:00:00

set -euo pipefail
: "${RAKL_EXPERIMENT_MANIFEST:?missing manifest}"
: "${RAKL_GATE_RECEIPT:?missing gate receipt}"
: "${RAKL_EXPECTED_EXECUTION_SUBJECT_SHA:?missing execution subject}"
: "${RAKL_EXPECTED_MANIFEST_SHA256:?missing manifest hash}"
: "${RAKL_EXPECTED_GATE_SHA256:?missing gate hash}"
: "${RAKL_REPO_PATH:?missing exact repository path}"
: "${RAKL_PYTHON_EXECUTABLE:?missing frozen Python executable}"

exec "$RAKL_PYTHON_EXECUTABLE" \
  "$RAKL_REPO_PATH/experiments/paper3/lunarc/ai_operator_demoted_workload_runtime.py" \
  --expected-workload inference
