#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9]+$ ]]; then
  echo "usage: $0 <slurm-job-id>" >&2
  exit 64
fi

JOB_ID="$1"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
RUN_DIR="$ROOT/runs/v4_3_1/PENDULUM_SEALED_KNOWN_ANSWER_001-seed-17-job-${JOB_ID}"
ATTESTATION_DIR="$ROOT/receipts/v4_3_1/job-${JOB_ID}"
RECEIPT_ROOT="$ROOT/receipts/v4_3_1"
SUBMISSION_PATH="$RECEIPT_ROOT/submission-${JOB_ID}.json"
SACCT_PATH="$RECEIPT_ROOT/sacct-${JOB_ID}.json"
HARVEST_PATH="$RECEIPT_ROOT/harvest-${JOB_ID}.json"
REPO="$ROOT/repo"
PYTHON="$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11"
mkdir -p "$RECEIPT_ROOT"
sacct -j "$JOB_ID" --json > "$SACCT_PATH"

test -x "$PYTHON"
cd "$REPO"
"$PYTHON" experiments/paper2/lunarc/build_native_harvest_receipt_v4_3_1.py \
  --job-id "$JOB_ID" \
  --run-dir "$RUN_DIR" \
  --attestation-dir "$ATTESTATION_DIR" \
  --submission "$SUBMISSION_PATH" \
  --sacct "$SACCT_PATH" \
  --packet research/paper2_microtrial_v4_3_1/EXECUTION_PACKET_V4_3_1_20260811.json \
  --result-schema schemas/paper2-pendulum-microtrial-result.schema.json \
  --task-seed-schema schemas/paper2-pendulum-task-seed-receipt-v4-3-1.schema.json \
  --attestation-schema schemas/paper2-model-snapshot-attestation-v4.schema.json \
  --submission-schema schemas/paper2-pendulum-submission-receipt-v4-3-1.schema.json \
  --harvest-schema schemas/paper2-pendulum-native-harvest-receipt-v4-3-1.schema.json \
  --output "$HARVEST_PATH"
