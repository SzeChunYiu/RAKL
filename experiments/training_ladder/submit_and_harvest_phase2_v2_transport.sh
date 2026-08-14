#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  submit_and_harvest_phase2_v2_transport.sh preflight <SUBJECT_SHA> [REPO_ROOT]
  submit_and_harvest_phase2_v2_transport.sh submit    <SUBJECT_SHA> [REPO_ROOT]
  submit_and_harvest_phase2_v2_transport.sh harvest   <JOB_ID> <SUBJECT_SHA> [REPO_ROOT]
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

PACKET_V1_REL="research/paper4_phase2_execution_transport_v1"
PACKET_V2_REL="research/paper4_phase2_execution_transport_v2"
TRANSPORT_V1_REL="$PACKET_V1_REL/PROTOCOL.json"
TRANSPORT_V2_REL="$PACKET_V2_REL/PROTOCOL.json"
SBATCH_REL="experiments/training_ladder/run_phase2_v1_lunarc_transport_v1.sbatch"
HARVEST_V2_REL="experiments/training_ladder/harvest_phase2_v2.py"
OUT_ROOT="${OUT_ROOT:-$REPO_ROOT/experiments/training_ladder/phase2_v1_out}"
TRANSPORT_RUNS="$OUT_ROOT/_transport_v2"

INTERPRETER_PATHS=(
  "research/paper4_phase2_execution_transport_v1/PROTOCOL.json"
  "research/paper4_phase2_execution_transport_v2/PROTOCOL.json"
  "experiments/training_ladder/submit_and_harvest_phase2_v2_transport.sh"
  "experiments/training_ladder/harvest_phase2_v2.py"
  "experiments/training_ladder/harvest_phase2_v1.py"
  "experiments/training_ladder/validate_phase2_v1_terminal.py"
  "experiments/training_ladder/run_phase2_v1_lunarc_transport_v1.sbatch"
  "src/rakl/phase2_adaptive_receipt_admission.py"
  "src/rakl/training_policy_authority.py"
)

checkout_exact_subject() {
  cd "$REPO_ROOT"
  git cat-file -e "${SUBJECT_SHA}^{commit}"
  git checkout --detach "$SUBJECT_SHA" >/dev/null
  if [ "$(git rev-parse HEAD)" != "$SUBJECT_SHA" ]; then
    echo "CANNOT_CHECK_EXECUTION_STATE: exact subject checkout failed" >&2
    exit 3
  fi
  if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "CANNOT_CHECK_EXECUTION_STATE: tracked checkout is dirty" >&2
    exit 3
  fi
}

verify_frozen_subject() {
  checkout_exact_subject
  python - "$TRANSPORT_V1_REL" "$TRANSPORT_V2_REL" <<'PY'
import json, subprocess, sys
from pathlib import Path
v1=Path(sys.argv[1]); v2=Path(sys.argv[2])
p1=json.loads(v1.read_text()); p2=json.loads(v2.read_text())
assert p1['schema_version']=='paper4-phase2-execution-transport-v1'
assert p2['schema_version']=='paper4-phase2-execution-transport-v2'
assert p2['chronology']['phase2_model_outputs_accessed_before_v2_freeze'] is False
assert p2['chronology']['phase2_job_submitted_before_v2_freeze'] is False
assert p2['scientific_subject_unchanged']['changed_from_v1'] is False
for path, expected in p1['frozen_git_blobs'].items():
    actual=subprocess.check_output(['git','hash-object',path], text=True).strip()
    if actual != expected:
        raise SystemExit(f'FROZEN_P4_PHASE2_SCIENCE_BLOB_MISMATCH:{path}:{actual}:{expected}')
for path, expected in p2['frozen_v1_and_authority_blobs'].items():
    actual=subprocess.check_output(['git','hash-object',path], text=True).strip()
    if actual != expected:
        raise SystemExit(f'FROZEN_P4_PHASE2_V1_PARENT_BLOB_MISMATCH:{path}:{actual}:{expected}')
assert p2['grants_scientific_authority'] is False
print('P4 Phase-2 v2 frozen parent/science subject: PASS')
PY
  bash -n "$SBATCH_REL"
  bash -n "experiments/training_ladder/submit_and_harvest_phase2_v2_transport.sh"
  python -m py_compile "$HARVEST_V2_REL"
}

write_submission_receipt() {
  local job_id="$1"
  mkdir -p "$TRANSPORT_RUNS"
  python - "$TRANSPORT_V1_REL" "$TRANSPORT_V2_REL" "$TRANSPORT_RUNS/SUBMISSION_${job_id}.json" "$SUBJECT_SHA" "$job_id" "${INTERPRETER_PATHS[@]}" <<'PY'
import hashlib, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
v1=Path(sys.argv[1]); v2=Path(sys.argv[2]); out=Path(sys.argv[3]); subject=sys.argv[4]; job_id=sys.argv[5]; paths=sys.argv[6:]
p1=json.loads(v1.read_text()); p2=json.loads(v2.read_text())
blobs={p:subprocess.check_output(['git','hash-object',p],text=True).strip() for p in paths}
receipt={
 'schema_version':'paper4-phase2-submission-receipt-v1',
 'transport_binding_version':2,
 'submitted_at':datetime.now(timezone.utc).isoformat(),
 'subject_sha':subject,
 'slurm_job_id':str(job_id),
 'model_id':p1['scientific_subject_unchanged']['model_id'],
 'model_revision':p1['scientific_subject_unchanged']['model_revision'],
 'transport_protocol_sha256':hashlib.sha256(v1.read_bytes()).hexdigest(),
 'transport_v2_protocol_sha256':hashlib.sha256(v2.read_bytes()).hexdigest(),
 'transport_sbatch_git_blob':blobs['experiments/training_ladder/run_phase2_v1_lunarc_transport_v1.sbatch'],
 'harvest_interpreter_git_blobs':blobs,
 'frozen_git_blobs':p1['frozen_git_blobs'],
 'scientific_settings_changed':False,
 'grants_scientific_authority':False,
 'standalone_paper4_authorized':False,
}
out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(out)
PY
}

if [ "$MODE" = preflight ]; then
  verify_frozen_subject
  tmp="$(mktemp -d)"
  python -m experiments.training_ladder.phase2_adaptive_v1 --outdir "$tmp" --dry-run >/dev/null
  test -s "$tmp/DATA_MANIFEST.json"
  rm -rf "$tmp"
  command -v sbatch >/dev/null || echo "NOTE: sbatch unavailable; scientific preflight still passed" >&2
  echo "P4_PHASE2_EXECUTION_V2_PREFLIGHT_PASS subject=$SUBJECT_SHA"
  exit 0
fi

if [ "$MODE" = submit ]; then
  verify_frozen_subject
  command -v sbatch >/dev/null || { echo "RESOURCE_BLOCKED: sbatch unavailable" >&2; exit 2; }
  mkdir -p "$OUT_ROOT"
  raw_job="$(sbatch --parsable \
    --export=ALL,REPO_ROOT="$REPO_ROOT",SUBJECT_SHA="$SUBJECT_SHA" \
    "$SBATCH_REL")"
  JOB_ID="${raw_job%%;*}"
  [[ "$JOB_ID" =~ ^[0-9]+$ ]] || { echo "CANNOT_CHECK_EXECUTION_STATE: invalid sbatch response: $raw_job" >&2; exit 3; }
  write_submission_receipt "$JOB_ID"
  echo "P4_PHASE2_V2_SUBMITTED job_id=$JOB_ID subject=$SUBJECT_SHA"
  exit 0
fi

# Harvest is deliberately forced back onto the submitted repository subject
# before any scientific result interpretation or authority import occurs.
checkout_exact_subject
SUBMISSION="$TRANSPORT_RUNS/SUBMISSION_${JOB_ID}.json"
[ -f "$SUBMISSION" ] || { echo "CANNOT_CHECK_EXECUTION_STATE: missing v2 submission receipt" >&2; exit 3; }
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
python "$HARVEST_V2_REL" \
  --repo-root "$REPO_ROOT" \
  --outdir "$OUT_DIR" \
  --submission "$SUBMISSION" \
  --transport-v1 "$REPO_ROOT/$TRANSPORT_V1_REL" \
  --transport-v2 "$REPO_ROOT/$TRANSPORT_V2_REL" \
  --subject-sha "$SUBJECT_SHA" \
  --job-id "$JOB_ID" \
  --scheduler-state "$STATE" \
  --write "$HARVEST"

echo "P4_PHASE2_V2_HARVESTED job_id=$JOB_ID subject=$SUBJECT_SHA receipt=$HARVEST"
