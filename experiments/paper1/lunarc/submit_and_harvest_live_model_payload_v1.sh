#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  submit_and_harvest_live_model_payload_v1.sh preflight <SUBJECT_SHA> [REPO_ROOT]
  submit_and_harvest_live_model_payload_v1.sh submit    <SUBJECT_SHA> [REPO_ROOT]
  submit_and_harvest_live_model_payload_v1.sh harvest   <JOB_ID> <SUBJECT_SHA> [REPO_ROOT]
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

PACKET_REL="research/paper1_live_model_payload_assurance_v1"
TRANSPORT_REL="$PACKET_REL/EXECUTION_TRANSPORT_V1.json"
SBATCH_REL="experiments/paper1/run_live_model_payload_assurance_v1_lunarc.sbatch"
TRANSPORT_DIR_REL="$PACKET_REL/EXECUTION_TRANSPORT"
EXACT_MODEL_PATH="/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/paper2-model-qwen25-7b-v1/model/Qwen--Qwen2.5-7B-Instruct/a09a35458c702b33eeacc393d103063234e8bc28"

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
import hashlib, importlib.util, json, subprocess, sys
from pathlib import Path

transport = json.loads(Path(sys.argv[1]).read_text())
for path, expected in transport['frozen_source_blobs'].items():
    actual = subprocess.check_output(['git','hash-object',path], text=True).strip()
    if actual != expected:
        raise SystemExit(f'FROZEN_BLOB_MISMATCH:{path}:{actual}:{expected}')
path=Path('experiments/paper1/build_live_model_payload_panel_v1.py')
spec=importlib.util.spec_from_file_location('p1panel_transport', path)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
rows=mod.build()
body=mod.serialize(rows)
fixed=transport['fixed_subject']
assert len(rows)==fixed['panel_n']==96
assert len(body)==fixed['panel_bytes']==148332
assert hashlib.sha256(body).hexdigest()==fixed['panel_sha256']
assert fixed['model_substitution_allowed'] is False
assert transport['grants_scientific_authority'] is False
print('P1 frozen execution subject: PASS')
PY
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' RETURN
  python experiments/paper1/run_live_model_payload_assurance_v1.py --outdir "$TMP" --dry-run >/dev/null
  rm -rf "$TMP"
  trap - RETURN
}

write_submission_receipt() {
  local job_id="$1"
  mkdir -p "$REPO_ROOT/$TRANSPORT_DIR_REL"
  python - "$REPO_ROOT/$TRANSPORT_REL" "$REPO_ROOT/$TRANSPORT_DIR_REL/SUBMISSION_${job_id}.json" "$SUBJECT_SHA" "$job_id" "$EXACT_MODEL_PATH" <<'PY'
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
transport_path=Path(sys.argv[1]); out=Path(sys.argv[2]); subject=sys.argv[3]; job_id=sys.argv[4]; model_path=sys.argv[5]
transport=json.loads(transport_path.read_text())
assert model_path == transport['fixed_subject']['model_path']
receipt={
  'schema_version':'paper1-live-model-payload-submission-receipt-v1',
  'submitted_at':datetime.now(timezone.utc).isoformat(),
  'subject_sha':subject,
  'slurm_job_id':str(job_id),
  'model_path':model_path,
  'transport_sha256':hashlib.sha256(transport_path.read_bytes()).hexdigest(),
  'frozen_source_blobs':transport['frozen_source_blobs'],
  'panel_sha256':transport['fixed_subject']['panel_sha256'],
  'grants_scientific_authority':False,
}
out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(out)
PY
}

if [ "$MODE" = preflight ]; then
  check_subject
  command -v sbatch >/dev/null || echo "NOTE: sbatch unavailable; preflight still passed" >&2
  echo "P1_EXECUTION_PREFLIGHT_PASS subject=$SUBJECT_SHA"
  exit 0
fi

if [ "$MODE" = submit ]; then
  check_subject
  command -v sbatch >/dev/null || { echo "RESOURCE_BLOCKED_LIVE_MODEL_PAYLOAD_ASSURANCE: sbatch unavailable" >&2; exit 2; }
  raw_job="$(sbatch --parsable --export=ALL,SUBJECT_SHA="$SUBJECT_SHA",REPO_ROOT="$REPO_ROOT",MODEL_PATH="$EXACT_MODEL_PATH" "$SBATCH_REL")"
  JOB_ID="${raw_job%%;*}"
  [[ "$JOB_ID" =~ ^[0-9]+$ ]] || { echo "CANNOT_CHECK_EXECUTION_STATE: invalid sbatch response: $raw_job" >&2; exit 3; }
  write_submission_receipt "$JOB_ID"
  echo "P1_SUBMITTED job_id=$JOB_ID subject=$SUBJECT_SHA"
  exit 0
fi

cd "$REPO_ROOT"
SUBMISSION="$REPO_ROOT/$TRANSPORT_DIR_REL/SUBMISSION_${JOB_ID}.json"
[ -f "$SUBMISSION" ] || { echo "CANNOT_CHECK_EXECUTION_STATE: missing submission receipt" >&2; exit 3; }
python - "$SUBMISSION" "$SUBJECT_SHA" "$JOB_ID" "$EXACT_MODEL_PATH" <<'PY'
import json, sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
assert r['subject_sha']==sys.argv[2]
assert str(r['slurm_job_id'])==str(sys.argv[3])
assert r['model_path']==sys.argv[4]
assert r['grants_scientific_authority'] is False
PY
command -v sacct >/dev/null || { echo "CANNOT_CHECK_EXECUTION_STATE: sacct unavailable" >&2; exit 3; }
STATE="$(sacct -n -X -j "$JOB_ID" --format=State -P | sed '/^[[:space:]]*$/d' | head -n1 | cut -d'|' -f1 | tr -d '[:space:]')"
[ -n "$STATE" ] || { echo "CANNOT_CHECK_EXECUTION_STATE: scheduler state unavailable" >&2; exit 3; }
case "$STATE" in
  COMPLETED) ;;
  PENDING|RUNNING|CONFIGURING|COMPLETING|SUSPENDED|REQUEUED|RESIZING) echo "CANNOT_CHECK_EXECUTION_STATE: job state=$STATE" >&2; exit 3 ;;
  *) echo "RESOURCE_BLOCKED_LIVE_MODEL_PAYLOAD_ASSURANCE: job state=$STATE" >&2; exit 2 ;;
esac

OUT_DIR="$REPO_ROOT/$PACKET_REL/RUN_${JOB_ID}"
RAW_RECEIPT="$OUT_DIR/FINAL_RECEIPT.json"
RAW_ROWS="$OUT_DIR/RAW_RESULTS.jsonl"
[ -f "$RAW_RECEIPT" ] && [ -f "$RAW_ROWS" ] || { echo "CANNOT_CHECK_EXECUTION_STATE: completed job missing raw result artifacts" >&2; exit 3; }
mkdir -p "$REPO_ROOT/$TRANSPORT_DIR_REL"
HARVEST="$REPO_ROOT/$TRANSPORT_DIR_REL/HARVEST_${JOB_ID}.json"
python - "$REPO_ROOT/$TRANSPORT_REL" "$SUBMISSION" "$RAW_RECEIPT" "$RAW_ROWS" "$HARVEST" "$SUBJECT_SHA" "$JOB_ID" "$STATE" <<'PY'
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
transport_path=Path(sys.argv[1]); submission_path=Path(sys.argv[2]); raw_receipt_path=Path(sys.argv[3]); raw_rows_path=Path(sys.argv[4]); out=Path(sys.argv[5])
subject,job_id,state=sys.argv[6:9]
transport=json.loads(transport_path.read_text()); submission=json.loads(submission_path.read_text()); raw=json.loads(raw_receipt_path.read_text())
fixed=transport['fixed_subject']; allowed=set(transport['allowed_terminals'])
if state!='COMPLETED': raise SystemExit('scheduler_not_completed')
if submission['subject_sha']!=subject or str(submission['slurm_job_id'])!=str(job_id): raise SystemExit('submission_binding_mismatch')
if submission['model_path']!=fixed['model_path']: raise SystemExit('model_path_mismatch')
if raw.get('subject_git_sha')!=subject: raise SystemExit('subject_git_sha_mismatch')
if raw.get('panel',{}).get('panel_sha256')!=fixed['panel_sha256'] or raw.get('panel',{}).get('n')!=fixed['panel_n']: raise SystemExit('panel_identity_mismatch')
if raw.get('model',{}).get('revision')!=fixed['model_revision']: raise SystemExit('model_revision_mismatch')
protocol_path=Path('research/paper1_live_model_payload_assurance_v1/PROTOCOL.json')
if raw.get('protocol_sha256')!=hashlib.sha256(protocol_path.read_bytes()).hexdigest(): raise SystemExit('protocol_hash_mismatch')
if raw.get('raw_results_sha256')!=hashlib.sha256(raw_rows_path.read_bytes()).hexdigest(): raise SystemExit('raw_results_hash_mismatch')
rows=sum(1 for line in raw_rows_path.read_text().splitlines() if line.strip())
if rows!=fixed['panel_n'] or raw.get('metrics',{}).get('n')!=fixed['panel_n']: raise SystemExit('incomplete_96_case_result')
terminal=raw.get('terminal')
if terminal not in allowed: raise SystemExit(f'unregistered_terminal:{terminal}')
if raw.get('grants_scientific_authority') is not False: raise SystemExit('invalid_scientific_authority_flag')
receipt={
 'schema_version':'paper1-live-model-payload-harvest-receipt-v1',
 'harvested_at':datetime.now(timezone.utc).isoformat(),
 'subject_sha':subject,'slurm_job_id':str(job_id),'scheduler_state':state,
 'terminal':terminal,'model_path':fixed['model_path'],'model_revision':fixed['model_revision'],
 'panel_sha256':fixed['panel_sha256'],'raw_receipt_sha256':hashlib.sha256(raw_receipt_path.read_bytes()).hexdigest(),
 'raw_results_sha256':hashlib.sha256(raw_rows_path.read_bytes()).hexdigest(),
 'claim_boundary':transport['claim_boundary'],'grants_scientific_authority':False,
}
out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps(receipt,indent=2,sort_keys=True))
PY

echo "P1_HARVESTED job_id=$JOB_ID subject=$SUBJECT_SHA receipt=$HARVEST"
