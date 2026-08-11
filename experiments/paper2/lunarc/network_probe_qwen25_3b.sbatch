#!/bin/bash
#SBATCH --job-name=rakl_p2_probe_3b
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:20:00
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/qwen25_3b_stage/network_probe_3b_%j.out

set -euo pipefail
: "${RAKL_STAGING_CONTRACT:?missing byte-bound staging contract}"
: "${RAKL_EXPECTED_REPO_SHA:?missing exact repository SHA supplied at submission}"
: "${RAKL_REPO_PATH:?missing exact repository path}"
: "${SLURM_JOB_ID:?network probe must run in a SLURM batch allocation}"

mkdir -p /projects/hep/fs9/users/scyiu/RAKL-paper2/logs/qwen25_3b_stage \
  /projects/hep/fs9/users/scyiu/RAKL-paper2/receipts/qwen25_3b_stage
receipt="/projects/hep/fs9/users/scyiu/RAKL-paper2/receipts/qwen25_3b_stage/network-probe-${SLURM_JOB_ID}.json"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="${RAKL_REPO_PATH}/src" python3 -m rakl.paper2_model_staging_v4_3 network-probe \
  --contract "${RAKL_STAGING_CONTRACT}" \
  --repo "${RAKL_REPO_PATH}" \
  --expected-repo-sha "${RAKL_EXPECTED_REPO_SHA}" \
  --receipt-output "${receipt}"
