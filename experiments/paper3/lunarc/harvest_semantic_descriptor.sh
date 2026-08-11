#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 || ! "$1" =~ ^(model-stage|descriptor)$ || ! "$2" =~ ^[0-9]+$ ]]; then
  echo "usage: $0 <model-stage|descriptor> <slurm-job-id>" >&2
  exit 64
fi

PHASE="$1"
JOB_ID="$2"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper3
REPO="$ROOT/repo"
RECEIPT_ROOT="$ROOT/semantic_descriptor_v1/receipts"
PYTHON=/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11
CONTRACT="$REPO/research/paper3_semantic_descriptor_lunarc/CONTRACT_V1.json"
SACCT="$RECEIPT_ROOT/sacct-${PHASE}-${JOB_ID}.json"

if [[ "$PHASE" == model-stage ]]; then
  SUBMISSION="$RECEIPT_ROOT/model-stage-submission-${JOB_ID}.json"
  EXECUTION="$RECEIPT_ROOT/model-stage-execution-${JOB_ID}.json"
  OUTPUT="$RECEIPT_ROOT/harvest-model-stage-${JOB_ID}.json"
else
  SUBMISSION="$RECEIPT_ROOT/descriptor-submission-${JOB_ID}.json"
  EXECUTION="$RECEIPT_ROOT/descriptor-execution-${JOB_ID}.json"
  OUTPUT="$RECEIPT_ROOT/harvest-descriptor-${JOB_ID}.json"
fi

mkdir -p "$RECEIPT_ROOT"
sacct -j "$JOB_ID" --json > "$SACCT"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
export PYTHONPATH="$REPO/src"
test -x "$PYTHON"

"$PYTHON" "$REPO/experiments/paper3/lunarc/build_semantic_descriptor_harvest.py" \
  --phase "$PHASE" \
  --job-id "$JOB_ID" \
  --repo "$REPO" \
  --contract "$CONTRACT" \
  --submission "$SUBMISSION" \
  --execution "$EXECUTION" \
  --sacct "$SACCT" \
  --output "$OUTPUT"

echo "$OUTPUT"
