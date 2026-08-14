#!/bin/bash
# Submit the frozen Paper-IV Phase-2 successor on LUNARC.
# Run from a LUNARC login node after checking out the exact ORION closure subject.
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/projects/hep/fs9/users/scyiu/orion}"
cd "$REPO_ROOT"
SUBJECT_SHA="$(git rev-parse HEAD)"
OUT_ROOT="${OUT_ROOT:-$REPO_ROOT/experiments/training_ladder/phase2_v1_out}"
mkdir -p "$OUT_ROOT"

job_id="$(sbatch --parsable \
  --export=ALL,REPO_ROOT="$REPO_ROOT",SUBJECT_SHA="$SUBJECT_SHA",OUT_DIR="$OUT_ROOT/%j" \
  experiments/training_ladder/run_phase2_v1_lunarc.sbatch)"

printf '%s\n' "$job_id" | tee "$OUT_ROOT/LATEST_SUBMITTED_JOB_ID.txt"
cat > "$OUT_ROOT/SUBMISSION_${job_id}.json" <<EOF
{
  "schema_version": "orion-p4-phase2-lunarc-submission-v1",
  "job_id": "$job_id",
  "subject_sha": "$SUBJECT_SHA",
  "protocol": "research/paper4_phase2_v1/PROTOCOL_V3.json",
  "inference": "research/paper4_phase2_v1/INFERENCE_PLAN.json",
  "model_revision": "a09a35458c702b33eeacc393d103063234e8bc28",
  "outcome_accessed_at_submission": false,
  "grants_scientific_authority": false
}
EOF

echo "submitted Paper-IV Phase-2 job $job_id at subject $SUBJECT_SHA"
