#!/usr/bin/env bash
set -euo pipefail

# Submission/harvest transport for the already-frozen Paper-III capability
# qualification. This script changes no scientific setting. Its only job is
# to bind repository subject -> SLURM job -> raw Stage-5 receipt fail-closed.

usage() {
  cat <<'EOF'
Usage:
  submit_and_harvest_capability_stage4_v1.sh preflight <SUBJECT_SHA> [REPO_ROOT]
  submit_and_harvest_capability_stage4_v1.sh submit    <SUBJECT_SHA> [REPO_ROOT]
  submit_and_harvest_capability_stage4_v1.sh harvest   <JOB_ID> <SUBJECT_SHA> [REPO_ROOT]

Defaults:
  REPO_ROOT=/projects/hep/fs9/users/scyiu/orion
EOF
}

MODE="${1:-}"
[ -n "$MODE" ] || { usage; exit 64; }
shift

case "$MODE" in
  preflight|submit)
    SUBJECT_SHA="${1:-}"
    [ -n "$SUBJECT_SHA" ] || { usage; exit 64; }
    shift || true
    REPO_ROOT="${1:-/projects/hep/fs9/users/scyiu/orion}"
    ;;
  harvest)
    JOB_ID="${1:-}"
    SUBJECT_SHA="${2:-}"
    [ -n "$JOB_ID" ] && [ -n "$SUBJECT_SHA" ] || { usage; exit 64; }
    shift 2 || true
    REPO_ROOT="${1:-/projects/hep/fs9/users/scyiu/orion}"
    ;;
  *)
    usage
    exit 64
    ;;
esac

PACKET_REL="research/empirical_10_of_10_v1/CAPABILITY_QUALIFICATION"
TRANSPORT_REL="$PACKET_REL/STAGE4_EXECUTION_TRANSPORT_V1.json"
SBATCH_REL="experiments/paper3/run_capability_stage4_v1_lunarc.sbatch"
TRANSPORT_DIR_REL="$PACKET_REL/EXECUTION_TRANSPORT"

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

transport = json.loads(Path(sys.argv[1]).read_text())
for path, expected in transport["frozen_blob_contract"].items():
    actual = subprocess.check_output(["git", "hash-object", path], text=True).strip()
    if actual != expected:
        raise SystemExit(f"FROZEN_BLOB_MISMATCH:{path}:{actual}:{expected}")
fixed = transport["fixed_scientific_subject"]
assert fixed["model_revision"] == "a09a35458c702b33eeacc393d103063234e8bc28"
assert fixed["panel_sha256"] == "0ab994fb0f8f3523014023ff703151afe4c66e86a8f030435f509d141055cc0e"
assert fixed["panel_n"] == 132
assert fixed["model_substitution_allowed"] is False
assert transport["grants_scientific_authority"] is False
print("frozen execution subject: PASS")
PY

  # Re-materialize the sealed panel before a scheduler submission. This does
  # not call a model and therefore cannot consume qualification outcomes.
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' RETURN
  python experiments/paper3/run_capability_stage4_v1.py --outdir "$TMP" --dry-run >/dev/null
  rm -rf "$TMP"
  trap - RETURN
}

write_submission_receipt() {
  local job_id="$1"
  mkdir -p "$REPO_ROOT/$TRANSPORT_DIR_REL"
  python - "$REPO_ROOT/$TRANSPORT_REL" "$REPO_ROOT/$TRANSPORT_DIR_REL/SUBMISSION_${job_id}.json" "$SUBJECT_SHA" "$job_id" <<'PY'
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

transport_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
subject = sys.argv[3]
job_id = sys.argv[4]
transport = json.loads(transport_path.read_text())
receipt = {
    "schema_version": "rakl-capability-stage4-submission-receipt-v1",
    "submitted_at": datetime.now(timezone.utc).isoformat(),
    "subject_sha": subject,
    "slurm_job_id": str(job_id),
    "transport_sha256": hashlib.sha256(transport_path.read_bytes()).hexdigest(),
    "frozen_blob_contract": transport["frozen_blob_contract"],
    "scientific_subject": transport["fixed_scientific_subject"],
    "grants_scientific_authority": False,
}
out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(out_path)
PY
}

if [ "$MODE" = preflight ]; then
  check_subject
  command -v sbatch >/dev/null || echo "NOTE: sbatch unavailable in this shell; scientific preflight still passed" >&2
  echo "STAGE4_EXECUTION_PREFLIGHT_PASS subject=$SUBJECT_SHA"
  exit 0
fi

if [ "$MODE" = submit ]; then
  check_subject
  command -v sbatch >/dev/null || { echo "CAPABLE_MODEL_NOT_FEASIBLE_UNDER_RESOURCE_ENVELOPE: sbatch unavailable" >&2; exit 2; }
  raw_job="$(sbatch --parsable --export=ALL,SUBJECT_SHA="$SUBJECT_SHA",REPO_ROOT="$REPO_ROOT" "$SBATCH_REL")"
  JOB_ID="${raw_job%%;*}"
  [[ "$JOB_ID" =~ ^[0-9]+$ ]] || { echo "CANNOT_CHECK_EXECUTION_STATE: invalid sbatch response: $raw_job" >&2; exit 3; }
  write_submission_receipt "$JOB_ID"
  echo "STAGE4_SUBMITTED job_id=$JOB_ID subject=$SUBJECT_SHA"
  exit 0
fi

# harvest
cd "$REPO_ROOT"
SUBMISSION="$REPO_ROOT/$TRANSPORT_DIR_REL/SUBMISSION_${JOB_ID}.json"
[ -f "$SUBMISSION" ] || { echo "CANNOT_CHECK_EXECUTION_STATE: missing submission receipt $SUBMISSION" >&2; exit 3; }
python - "$SUBMISSION" "$SUBJECT_SHA" "$JOB_ID" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
assert r["subject_sha"] == sys.argv[2], "submission_subject_mismatch"
assert str(r["slurm_job_id"]) == str(sys.argv[3]), "submission_job_mismatch"
assert r["grants_scientific_authority"] is False
PY

command -v sacct >/dev/null || { echo "CANNOT_CHECK_EXECUTION_STATE: sacct unavailable" >&2; exit 3; }
STATE="$(sacct -n -X -j "$JOB_ID" --format=State -P | sed '/^[[:space:]]*$/d' | head -n1 | cut -d'|' -f1 | tr -d '[:space:]')"
[ -n "$STATE" ] || { echo "CANNOT_CHECK_EXECUTION_STATE: scheduler state unavailable for $JOB_ID" >&2; exit 3; }
case "$STATE" in
  COMPLETED) ;;
  PENDING|RUNNING|CONFIGURING|COMPLETING|SUSPENDED|REQUEUED|RESIZING)
    echo "CANNOT_CHECK_EXECUTION_STATE: job $JOB_ID state=$STATE" >&2
    exit 3
    ;;
  *)
    echo "CAPABLE_MODEL_NOT_FEASIBLE_UNDER_RESOURCE_ENVELOPE: job $JOB_ID state=$STATE" >&2
    exit 2
    ;;
esac

OUT_DIR="$REPO_ROOT/$PACKET_REL/STAGE4_RUN_${JOB_ID}"
RAW_RECEIPT="$OUT_DIR/FINAL_CAPABILITY_RECEIPT.json"
[ -f "$RAW_RECEIPT" ] || { echo "CANNOT_CHECK_EXECUTION_STATE: completed job missing $RAW_RECEIPT" >&2; exit 3; }
mkdir -p "$REPO_ROOT/$TRANSPORT_DIR_REL"
HARVEST="$REPO_ROOT/$TRANSPORT_DIR_REL/HARVEST_${JOB_ID}.json"
python - "$REPO_ROOT/$TRANSPORT_REL" "$SUBMISSION" "$RAW_RECEIPT" "$HARVEST" "$SUBJECT_SHA" "$JOB_ID" "$STATE" <<'PY'
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

transport_path = Path(sys.argv[1])
submission_path = Path(sys.argv[2])
raw_path = Path(sys.argv[3])
out_path = Path(sys.argv[4])
subject, job_id, scheduler_state = sys.argv[5:8]
transport = json.loads(transport_path.read_text())
submission = json.loads(submission_path.read_text())
raw = json.loads(raw_path.read_text())
allowed = set(transport["allowed_raw_terminals"])
terminal = raw.get("terminal")
if terminal not in allowed:
    raise SystemExit(f"UNREGISTERED_STAGE5_TERMINAL:{terminal}")
if submission["subject_sha"] != subject or str(submission["slurm_job_id"]) != str(job_id):
    raise SystemExit("submission_binding_mismatch")
if scheduler_state != "COMPLETED":
    raise SystemExit("scheduler_not_completed")
fixed = transport["fixed_scientific_subject"]
if raw.get("panel_sha256") != fixed["panel_sha256"]:
    raise SystemExit("panel_sha256_mismatch")
model = raw.get("model", {})
if model.get("revision") != fixed["model_revision"]:
    raise SystemExit("model_revision_mismatch")
if raw.get("model_substitution_performed") is not False:
    raise SystemExit("model_substitution_detected")
if raw.get("grants_scientific_authority") is not False:
    raise SystemExit("invalid_scientific_authority_flag")
if terminal in {"CAPABLE_MODEL_AUTHORIZE_RECEIPT_V3", "DIAGNOSTIC_OVERFIT_OR_INSUFFICIENT_CAPABILITY"}:
    if raw.get("all_132_cases_completed") is not True:
        raise SystemExit("incomplete_132_case_result")
receipt = {
    "schema_version": "rakl-capability-stage4-harvest-receipt-v1",
    "harvested_at": datetime.now(timezone.utc).isoformat(),
    "subject_sha": subject,
    "slurm_job_id": str(job_id),
    "scheduler_state": scheduler_state,
    "raw_terminal": terminal,
    "raw_receipt_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    "raw_output_directory": str(raw_path.parent),
    "panel_sha256": raw.get("panel_sha256"),
    "model_revision": model.get("revision"),
    "model_substitution_performed": False,
    "claim_boundary": transport["claim_boundary"],
    "grants_scientific_authority": False,
    "grants_model_level_efficacy": False,
}
out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps(receipt, indent=2, sort_keys=True))
PY

echo "STAGE4_HARVESTED job_id=$JOB_ID subject=$SUBJECT_SHA state=$STATE receipt=$HARVEST"
