#!/usr/bin/env bash
# Submit FS9 non-confirmatory ALR baseline job (#154).
set -euo pipefail

ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="${REPO:-$ROOT/repo}"
PYTHON="${PYTHON:-$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11}"
RCP=$ROOT/receipts/alr_baselines_v1
RUN=$ROOT/runs/alr_baselines_v1
LOG=$ROOT/logs/alr_baselines_v1
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SBATCH_SRC="$SCRIPT_DIR/run_alr_model_baselines_v1.sbatch"
AUTH="$REPO/research/paper2_alr_model_baselines_v1/LUNARC_AUTHORIZE_RECEIPT.json"

mkdir -p "$RCP" "$RUN" "$LOG"
test -x "$PYTHON"
test -f "$SBATCH_SRC"
test -f "$AUTH"

cd "$REPO"
# refresh main
git fetch origin main
git checkout --detach "refs/remotes/origin/main"
EXPECTED_REPO_SHA=$(git rev-parse HEAD)
if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  echo "dirty checkout after detach; refusing" >&2
  git status --porcelain --untracked-files=all >&2
  exit 43
fi

"$PYTHON" - <<PY
import json, pathlib, sys
sys.path.insert(0, "src")
from rakl.alr_model_baselines import plan_lunarc_submission, validate_preregistration
validate_preregistration()
plan = plan_lunarc_submission()
assert plan["status"] == "READY_TO_SUBMIT", plan
print("plan_ok", plan["status"])
PY

SBATCH_DST="$RUN/run_alr_model_baselines_v1.sbatch"
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
  "schema_version": "paper2-alr-lunarc-submission-receipt-v1",
  "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
  "issue": 154,
  "slurm_job_id": job_id,
  "expected_repo_sha": "$EXPECTED_REPO_SHA",
  "account": "lu2026-2-51",
  "partition": "lu48",
  "batch_script": "$SBATCH_DST",
  "authorize_receipt": "research/paper2_alr_model_baselines_v1/LUNARC_AUTHORIZE_RECEIPT.json",
  "claim_boundary": "Submission only for non-confirmatory ALR V2 baseline (#154). No promotional ALR claim.",
  "verdict": "SUBMITTED_ALR_BASELINE_V1_NONCONFIRMATORY",
  "grants_authority": False,
}
out = rcp / f"submission-{job_id}.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("WROTE", out)
PY
