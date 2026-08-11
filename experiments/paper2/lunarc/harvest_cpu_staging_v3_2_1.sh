#!/bin/bash
# Re-harvests already completed V3.2 jobs; never submits jobs or invokes a model.
set -euo pipefail
usage() {
  echo "usage: $0 --repair-repo PATH --expected-repair-sha SHA --source-repo PATH --submission-receipt PATH --prior-harvest-receipt PATH --receipt-output PATH" >&2
}
repair_repo=""; expected_repair_sha=""; source_repo=""; submission=""; prior_harvest=""; output=""
while (($#)); do
  case "$1" in
    --repair-repo) repair_repo="$2"; shift 2 ;;
    --expected-repair-sha) expected_repair_sha="$2"; shift 2 ;;
    --source-repo) source_repo="$2"; shift 2 ;;
    --submission-receipt) submission="$2"; shift 2 ;;
    --prior-harvest-receipt) prior_harvest="$2"; shift 2 ;;
    --receipt-output) output="$2"; shift 2 ;;
    *) usage; exit 64 ;;
  esac
done
[[ -n "$repair_repo" && -n "$expected_repair_sha" && -n "$source_repo" && -n "$submission" && -n "$prior_harvest" && -n "$output" ]] || { usage; exit 64; }
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$repair_repo/src" python3 -m rakl.paper2_cpu_staging_v3_2_1 \
  --repair-contract "$repair_repo/research/paper2_microtrial_v3/CPU_STAGING_HARVEST_REPAIR_CONTRACT_V3_2_1.json" \
  --repair-repo "$repair_repo" \
  --expected-repair-sha "$expected_repair_sha" \
  --source-contract "$source_repo/research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3_2.json" \
  --source-repo "$source_repo" \
  --submission-receipt "$submission" \
  --prior-harvest-receipt "$prior_harvest" \
  --receipt-root "/projects/hep/fs9/users/scyiu/RAKL-paper2/receipts/v3_2" \
  --final-root "/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/paper2-cpu-v3-2" \
  --failure-root "/projects/hep/fs9/users/scyiu/RAKL-paper2/failures/v3_2" \
  --receipt-output "$output"
