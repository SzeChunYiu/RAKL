#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  submit_and_harvest_phase2_v1_transport.sh preflight <SUBJECT_SHA> [REPO_ROOT]
  submit_and_harvest_phase2_v1_transport.sh submit    <SUBJECT_SHA> [REPO_ROOT]
  submit_and_harvest_phase2_v1_transport.sh harvest   <JOB_ID> <SUBJECT_SHA> [REPO_ROOT]
EOF
}

MODE="${1:-}"
[ -n "$MODE" ] || { usage; exit 64; }
shift
case "$MODE" in
  preflight|submit)
    SUBJECT_SHA="${1:-}"; [ -n "$SUBJECT_SHA" ] || { usage; exit 64; }
    shift || true
    REPO_ROOT="${1:-/projects/hep/fs9/users/scyiu/orion}"
    ;;
  harvest)
    JOB_ID="${1:-}"; SUBJECT_SHA="${2:-}"
    [ -n "$JOB_ID" ] && [ -n "$SUBJECT_SHA" ] || { usage; exit 64; }
    shift 2 || true
    REPO_ROOT="${1:-/projects/hep/fs9/users/scyiu/orion}"
    ;;
  *) usage; exit 64 ;;
esac

PACKET_REL="research/paper4_phase2_execution_transport_v1"
TRANSPORT_REL="$PACKET_REL/PROTOCOL.json"
SBATCH_REL="experiments/training_ladder/run_phase2_v1_lunarc_transport_v1.sbatch"
OUT_ROOT="${OUT_ROOT:-$REPO_ROOT/experiments/training_ladder/phase2_v1_out}"
TRANSPORT_RUNS="$OUT_ROOT/_transport_v1"
MODEL_REVISION="a09a35458c702b33eeacc393d103063234e8bc28"

check_subject() {
  cd "$REPO_ROOT"
  git cat-file -e "${SUBJECT_SHA}^{commit}"
  git checkout --detach "$SUBJECT_SHA" >/dev/null
  test "$(git rev-parse HEAD)" = "$SUBJECT_SHA"
  if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "CANNOT_CHECK_EXECUTION_STATE: tracked checkout is dirty" >&2
    exit 3
  fi

  python - "$REPO_ROOT/$TRANSPORT_REL" <<'PY'
import json, subprocess, sys
from pathlib import Path
p=Path(sys.argv[1])
transport=json.loads(p.read_text())
assert transport['schema_version']=='paper4-phase2-execution-transport-v1'
assert transport['chronology']['phase2_model_outputs_accessed_before_freeze'] is False
assert transport['scientific_subject_unchanged']['scientific_settings_changed'] is False
for path, expected in transport['frozen_git_blobs'].items():
    actual=subprocess.check_output(['git','hash-object',path],text=True).strip()
    if actual != expected:
        raise SystemExit(f'FROZEN_P4_PHASE2_BLOB_MISMATCH:{path}:{actual}:{expected}')
assert transport['grants_scientific_authority'] is False
print('P4 frozen scientific subject: PASS')
PY

  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' RETURN
  python -m experiments.training_ladder.phase2_adaptive_v1 --outdir "$TMP" --dry-run >/dev/null
  test -s "$TMP/DATA_MANIFEST.json"
  python experiments/training_ladder/validate_phase2_v1_terminal.py --selftest >/dev/null
  bash -n "$SBATCH_REL"
  rm -rf "$TMP"
  trap - RETURN
}

write_submission_receipt() {
  local job_id="$1"
  mkdir -p "$TRANSPORT_RUNS"
  python - "$REPO_ROOT/$TRANSPORT_REL" "$TRANSPORT_RUNS/SUBMISSION_${job_id}.json" "$SUBJECT_SHA" "$job_id" "$SBATCH_REL" <<'PY'
import hashlib, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
transport_path=Path(sys.argv[1]); out=Path(sys.argv[2]); subject=sys.argv[3]; job_id=sys.argv[4]; sbatch_rel=sys.argv[5]
transport=json.loads(transport_path.read_text())
receipt={
 'schema_version':'paper4-phase2-submission-receipt-v1',
 'submitted_at':datetime.now(timezone.utc).isoformat(),
 'subject_sha':subject,
 'slurm_job_id':str(job_id),
 'model_id':transport['scientific_subject_unchanged']['model_id'],
 'model_revision':transport['scientific_subject_unchanged']['model_revision'],
 'transport_protocol_sha256':hashlib.sha256(transport_path.read_bytes()).hexdigest(),
 'transport_sbatch_git_blob':subprocess.check_output(['git','hash-object',sbatch_rel],text=True).strip(),
 'frozen_git_blobs':transport['frozen_git_blobs'],
 'scientific_settings_changed':False,
 'grants_scientific_authority':False,
 'standalone_paper4_authorized':False,
}
out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(out)
PY
}

if [ "$MODE" = preflight ]; then
  check_subject
  command -v sbatch >/dev/null || echo "NOTE: sbatch unavailable; scientific preflight still passed" >&2
  echo "P4_PHASE2_EXECUTION_PREFLIGHT_PASS subject=$SUBJECT_SHA"
  exit 0
fi

if [ "$MODE" = submit ]; then
  check_subject
  command -v sbatch >/dev/null || { echo "RESOURCE_BLOCKED: sbatch unavailable" >&2; exit 2; }
  mkdir -p "$OUT_ROOT"
  raw_job="$(sbatch --parsable \
    --export=ALL,REPO_ROOT="$REPO_ROOT",SUBJECT_SHA="$SUBJECT_SHA" \
    "$SBATCH_REL")"
  JOB_ID="${raw_job%%;*}"
  [[ "$JOB_ID" =~ ^[0-9]+$ ]] || { echo "CANNOT_CHECK_EXECUTION_STATE: invalid sbatch response: $raw_job" >&2; exit 3; }
  write_submission_receipt "$JOB_ID"
  echo "P4_PHASE2_SUBMITTED job_id=$JOB_ID subject=$SUBJECT_SHA"
  exit 0
fi

cd "$REPO_ROOT"
SUBMISSION="$TRANSPORT_RUNS/SUBMISSION_${JOB_ID}.json"
[ -f "$SUBMISSION" ] || { echo "CANNOT_CHECK_EXECUTION_STATE: missing submission receipt" >&2; exit 3; }
command -v sacct >/dev/null || { echo "CANNOT_CHECK_EXECUTION_STATE: sacct unavailable" >&2; exit 3; }
STATE="$(sacct -n -X -j "$JOB_ID" --format=State -P | sed '/^[[:space:]]*$/d' | head -n1 | cut -d'|' -f1 | tr -d '[:space:]')"
[ -n "$STATE" ] || { echo "CANNOT_CHECK_EXECUTION_STATE: scheduler state unavailable" >&2; exit 3; }
case "$STATE" in
  COMPLETED) ;;
  PENDING|RUNNING|CONFIGURING|COMPLETING|SUSPENDED|REQUEUED|RESIZING)
    echo "CANNOT_CHECK_EXECUTION_STATE: job state=$STATE" >&2; exit 3 ;;
  *)
    echo "CANNOT_CHECK_EXECUTION_STATE: scheduler failed before validated scientific completion state=$STATE" >&2; exit 3 ;;
esac

OUT_DIR="$OUT_ROOT/$JOB_ID"
HARVEST="$TRANSPORT_RUNS/HARVEST_${JOB_ID}.json"
python experiments/training_ladder/harvest_phase2_v1.py \
  --outdir "$OUT_DIR" \
  --submission "$SUBMISSION" \
  --transport "$REPO_ROOT/$TRANSPORT_REL" \
  --subject-sha "$SUBJECT_SHA" \
  --job-id "$JOB_ID" \
  --scheduler-state "$STATE" \
  --write "$HARVEST"

echo "P4_PHASE2_HARVESTED job_id=$JOB_ID subject=$SUBJECT_SHA receipt=$HARVEST"
