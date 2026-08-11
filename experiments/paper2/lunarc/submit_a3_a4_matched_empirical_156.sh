#!/usr/bin/env bash
# Submit FS9 cheap CPU freeze validation for issue #156 matched A3↔A4 ablation.
# Does not invent model empirics. Operator-authorized submit (no dry-run gate).
set -euo pipefail

ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="${REPO:-$ROOT/repo}"
PYTHON="${PYTHON:-$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11}"
DEPS="${PYTEST_DEPS:-$ROOT/runs/a3_a4_matched_156/pydeps}"
RCP=$ROOT/receipts/a3_a4_matched_156
RUN=$ROOT/runs/a3_a4_matched_156
LOG=$ROOT/logs/a3_a4_matched_156
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SBATCH_SRC="$SCRIPT_DIR/run_a3_a4_matched_empirical_156.sbatch"

mkdir -p "$RCP" "$RUN" "$LOG" "$DEPS"

[[ "$(hostname)" == cosmos* ]] || { echo "submission is permitted only from a LUNARC login host" >&2; exit 2; }

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

# Stage pytest/jsonschema for frozen runtime.
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
if ! "$PYTHON" -c "import sys; sys.path.insert(0, '$DEPS'); import pytest, jsonschema" 2>/dev/null; then
  echo "staging pytest+jsonschema into $DEPS"
  "$PYTHON" -m pip install --no-cache-dir --target "$DEPS" "pytest>=8" "jsonschema>=4" >/dev/null
fi

SBATCH_DST="$RUN/run_a3_a4_matched_empirical_156.sbatch"
cp "$SBATCH_SRC" "$SBATCH_DST"

JOB_ID=$(
  EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA" \
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
  "schema_version": "paper2-a3-a4-matched-empirical-lunarc-submission-receipt-v1",
  "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
  "issue": 156,
  "slurm_job_id": job_id,
  "expected_repo_sha": "$EXPECTED_REPO_SHA",
  "account": "lu2026-2-51",
  "partition": "lu48",
  "batch_script": "$SBATCH_DST",
  "pytest_deps_path": "$DEPS",
  "claim_boundary": (
      "Submission for #156 FS9 CPU freeze validation only. "
      "EMPIRICS_UNRUN expected; no invented model ALR; not MemTX/PPMF/AutoSci."
  ),
  "verdict": "SUBMITTED_A3_A4_MATCHED_EMPIRICAL_FREEZE_VALIDATION",
  "grants_scientific_authority": False,
}
out = rcp / f"submission-{job_id}.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("WROTE", out)
PY
