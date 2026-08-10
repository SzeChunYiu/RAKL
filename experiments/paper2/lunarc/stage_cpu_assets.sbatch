#!/bin/bash
#SBATCH --job-name=rakl_p2_stage_v3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/stage_cpu_v3_%j.out

set -euo pipefail
: "${RAKL_STAGING_CONTRACT:?missing byte-bound staging contract}"
: "${RAKL_EXPECTED_REPO_SHA:?missing exact repository SHA supplied at submission}"
: "${RAKL_REPO_PATH:?missing exact repository path}"
: "${RAKL_PROBE_JOB_ID:?missing prerequisite network-probe job id}"
: "${SLURM_JOB_ID:?staging must run in a SLURM batch allocation}"

probe_receipt="/projects/hep/fs9/users/scyiu/RAKL-paper2/receipts/v3/network-probe-${RAKL_PROBE_JOB_ID}.json"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="${RAKL_REPO_PATH}/src" python3 -m rakl.paper2_cpu_staging stage-assets \
  --contract "${RAKL_STAGING_CONTRACT}" \
  --repo "${RAKL_REPO_PATH}" \
  --expected-repo-sha "${RAKL_EXPECTED_REPO_SHA}" \
  --probe-receipt "${probe_receipt}"
