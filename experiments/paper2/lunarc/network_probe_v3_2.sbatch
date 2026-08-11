#!/bin/bash
#SBATCH --job-name=rakl_p2_netprobe_v32
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:10:00
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/network_probe_v3_2_%j.out

set -euo pipefail
: "${RAKL_STAGING_CONTRACT:?missing byte-bound staging contract}"
: "${RAKL_EXPECTED_REPO_SHA:?missing exact repository SHA supplied at submission}"
: "${RAKL_REPO_PATH:?missing exact repository path}"
: "${SLURM_JOB_ID:?network probe must run in a SLURM batch allocation}"

receipt="/projects/hep/fs9/users/scyiu/RAKL-paper2/receipts/v3_2/network-probe-${SLURM_JOB_ID}.json"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="${RAKL_REPO_PATH}/src" python3 -m rakl.paper2_cpu_staging_v3_2 network-probe \
  --contract "${RAKL_STAGING_CONTRACT}" \
  --repo "${RAKL_REPO_PATH}" \
  --expected-repo-sha "${RAKL_EXPECTED_REPO_SHA}" \
  --receipt-output "${receipt}"
