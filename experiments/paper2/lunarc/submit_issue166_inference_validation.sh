#!/usr/bin/env bash
# Submit FS9 confirmatory validation for issue #166 (pytest + true-null FP sim).
# Stages pytest into a job-local target so PYTHONNOUSERSITE=1 frozen runtimes work.
set -euo pipefail

ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="${REPO:-$ROOT/repo}"
PYTHON="${PYTHON:-$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11}"
DEPS="${PYTEST_DEPS:-$ROOT/runs/novelty_inference_166/pydeps}"
RCP=$ROOT/receipts/novelty_inference_166
RUN=$ROOT/runs/novelty_inference_166
LOG=$ROOT/logs/novelty_inference_166
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SBATCH_SRC="$SCRIPT_DIR/run_issue166_inference_validation.sbatch"
PARENT_FAILED_JOB_ID="${PARENT_FAILED_JOB_ID:-}"

mkdir -p "$RCP" "$RUN" "$LOG" "$DEPS"

if [[ ! -x "$PYTHON" ]]; then
  echo "missing python: $PYTHON" >&2
  exit 66
fi
if [[ ! -f "$SBATCH_SRC" ]]; then
  echo "missing sbatch template: $SBATCH_SRC" >&2
  exit 66
fi

cd "$REPO"
EXPECTED_REPO_SHA=$(git rev-parse refs/remotes/origin/main)
HEAD=$(git rev-parse HEAD)
if [[ "$HEAD" != "$EXPECTED_REPO_SHA" ]]; then
  echo "checkout HEAD=$HEAD != origin/main=$EXPECTED_REPO_SHA; refusing submit" >&2
  exit 42
fi
if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  echo "dirty checkout; refusing submit" >&2
  git status --porcelain --untracked-files=all >&2
  exit 43
fi

# Stage pytest into job-local target without mutating the frozen runtime asset.
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
if ! "$PYTHON" -c "import sys; sys.path.insert(0, '$DEPS'); import pytest" 2>/dev/null; then
  echo "staging pytest into $DEPS (frozen runtime lacks pytest; see job 3476530)"
  "$PYTHON" -m pip install --no-cache-dir --target "$DEPS" "pytest>=8" >/dev/null
fi
"$PYTHON" -c "import sys; sys.path.insert(0, '$DEPS'); import pytest; print('pytest', pytest.__version__)"

SBATCH_DST="$RUN/run_issue166_inference_validation.sbatch"
cp "$SBATCH_SRC" "$SBATCH_DST"

JOB_ID=$(
  EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA" \
  PARENT_FAILED_JOB_ID="$PARENT_FAILED_JOB_ID" \
  PYTEST_DEPS="$DEPS" \
  REPO="$REPO" \
  PYTHON="$PYTHON" \
  sbatch --parsable "$SBATCH_DST"
)
echo "submitted job $JOB_ID"

python3 - <<PY
import datetime, json, pathlib
rcp = pathlib.Path("$RCP")
job_id = "$JOB_ID"
receipt = {
  "schema_version": "paper2-issue166-lunarc-submission-receipt-v1",
  "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
  "issue": 166,
  "slurm_job_id": job_id,
  "expected_repo_sha": "$EXPECTED_REPO_SHA",
  "account": "lu2026-2-51",
  "partition": "lu48",
  "batch_script": "$SBATCH_DST",
  "pytest_deps_path": "$DEPS",
  "repair_note": (
      "Stages pytest into job-local pydeps when frozen paper2 python has "
      "PYTHONNOUSERSITE=1 and no pytest (3476530 failure mode)."
  ),
  "claim_boundary": "Submission only for #166 FS9 inference-gate validation (pytest + synthetic null FP simulation). No Paper II empirical outcomes.",
  "verdict": "SUBMITTED_ISSUE166_INFERENCE_VALIDATION",
}
parent = "$PARENT_FAILED_JOB_ID"
if parent:
    receipt["supersedes_job_id"] = parent
    receipt["verdict"] = "SUBMITTED_ISSUE166_INFERENCE_VALIDATION_REPAIR"
out = rcp / f"submission-{job_id}.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("WROTE", out)
PY
