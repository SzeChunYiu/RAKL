#!/usr/bin/env bash
# Submit FS9 matched A3↔A4 model empirics (#156) after freeze validation.
set -euo pipefail

ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="${REPO:-$ROOT/repo}"
PYTHON="${PYTHON:-$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11}"
RCP=$ROOT/receipts/a3_a4_matched_empirics_156
RUN=$ROOT/runs/a3_a4_matched_empirics_156
LOG=$ROOT/logs/a3_a4_matched_empirics_156
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SBATCH_SRC="$SCRIPT_DIR/run_a3_a4_matched_empirics_score_156.sbatch"
AUTH="$REPO/research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICS_AUTHORIZE_RECEIPT.json"

mkdir -p "$RCP" "$RUN" "$LOG"
test -x "$PYTHON"
test -f "$SBATCH_SRC"
test -f "$AUTH"

[[ "$(hostname)" == cosmos* ]] || { echo "submission is permitted only from a LUNARC login host" >&2; exit 2; }

cd "$REPO"
git fetch origin main
git checkout --detach "refs/remotes/origin/main"
EXPECTED_REPO_SHA=$(git rev-parse HEAD)
if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  echo "dirty checkout after detach; refusing" >&2
  git status --porcelain --untracked-files=all >&2
  exit 43
fi

"$PYTHON" - <<PY
import sys
sys.path.insert(0, "src")
from rakl.ablation_a3_a4_matched_empirical import (
    plan_matched_empirics_submission,
    validate_empirics_authorize,
    validate_packet,
)
validate_packet()
validate_empirics_authorize()
plan = plan_matched_empirics_submission()
assert plan["status"] == "READY_TO_SUBMIT", plan
print("plan_ok", plan["status"])
PY

SBATCH_DST="$RUN/run_a3_a4_matched_empirics_score_156.sbatch"
cp "$SBATCH_SRC" "$SBATCH_DST"
JOB_ID=$(
  EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA" \
  REPO="$REPO" \
  PYTHON="$PYTHON" \
  sbatch --parsable "$SBATCH_DST"
)
echo "$JOB_ID"

python3 - <<PY
import datetime, json, pathlib
rcp = pathlib.Path("$RCP")
job_id = "$JOB_ID"
receipt = {
  "schema_version": "paper2-a3-a4-matched-empirics-lunarc-submission-receipt-v1",
  "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
  "issue": 156,
  "slurm_job_id": job_id,
  "expected_repo_sha": "$EXPECTED_REPO_SHA",
  "account": "lu2026-2-51",
  "partition": "lu48",
  "batch_script": "$SBATCH_DST",
  "authorize_receipt": "research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICS_AUTHORIZE_RECEIPT.json",
  "claim_boundary": (
      "Submission for matched A3↔A4 model empirics (#156). "
      "Non-confirmatory; not MemTX/PPMF/AutoSci; no A4>A3 novelty claim."
  ),
  "verdict": "SUBMITTED_A3_A4_MATCHED_EMPIRICS_SCORE_V1",
  "grants_scientific_authority": False,
}
out = rcp / f"submission-{job_id}.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("WROTE", out)
PY
