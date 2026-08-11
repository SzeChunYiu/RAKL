#!/bin/bash
# Harvests scheduler/staging receipts only; it never invokes the model runner.
set -euo pipefail
usage() { echo "usage: $0 --repo PATH --submission-receipt PATH --receipt-output PATH" >&2; }
repo=""; submission=""; output=""
while (($#)); do
  case "$1" in
    --repo) repo="$2"; shift 2 ;;
    --submission-receipt) submission="$2"; shift 2 ;;
    --receipt-output) output="$2"; shift 2 ;;
    *) usage; exit 64 ;;
  esac
done
[[ -n "$repo" && -n "$submission" && -n "$output" ]] || { usage; exit 64; }
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$repo/src" python3 -m rakl.paper2_cpu_staging_v3_2 harvest \
  --contract "$repo/research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3_2.json" \
  --repo "$repo" \
  --submission-receipt "$submission" \
  --receipt-root "/projects/hep/fs9/users/scyiu/RAKL-paper2/receipts/v3_2" \
  --final-root "/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/paper2-cpu-v3-2" \
  --failure-root "/projects/hep/fs9/users/scyiu/RAKL-paper2/failures/v3_2" \
  --receipt-output "$output"
