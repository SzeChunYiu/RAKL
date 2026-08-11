#!/usr/bin/env bash
set -euo pipefail
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="${REPO:-$ROOT/repo}"
PYTHON="${PYTHON:-$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11}"
RCP=$ROOT/receipts/a3_a4_conformance_v1
RUN=$ROOT/runs/a3_a4_conformance_v1
LOG=$ROOT/logs/a3_a4_conformance_v1
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SBATCH_SRC="$SCRIPT_DIR/run_a3_a4_conformance_v1.sbatch"
AUTH="$REPO/research/paper2_closest_parent/A3_A4_LUNARC_AUTHORIZE_RECEIPT.json"
mkdir -p "$RCP" "$RUN" "$LOG"
test -f "$SBATCH_SRC"
test -f "$AUTH"
cd "$REPO"
git fetch origin main
git checkout --detach "refs/remotes/origin/main"
EXPECTED_REPO_SHA=$(git rev-parse HEAD)
if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  echo dirty >&2; exit 43
fi
"$PYTHON" -c 'import json; a=json.load(open("research/paper2_closest_parent/A3_A4_LUNARC_AUTHORIZE_RECEIPT.json")); assert a["authorize_lunarc_a3_a4_conformance"] is True'
SBATCH_DST="$RUN/run_a3_a4_conformance_v1.sbatch"
cp "$SBATCH_SRC" "$SBATCH_DST"
JOB_ID=$(EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA" REPO="$REPO" PYTHON="$PYTHON" sbatch --parsable "$SBATCH_DST")
echo "$JOB_ID"
python3 - <<PY
import datetime, json, pathlib
rcp=pathlib.Path("$RCP"); job="$JOB_ID"
receipt={
 "schema_version":"paper2-a3-a4-lunarc-submission-receipt-v1",
 "created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
 "issue":156,
 "slurm_job_id":job,
 "expected_repo_sha":"$EXPECTED_REPO_SHA",
 "verdict":"SUBMITTED_A3_A4_CONFORMANCE_CLUSTER_VALIDATION",
 "grants_authority":False,
 "claim_boundary":"Submission only for cheap A3↔A4 conformance re-validation; not empirical ablation.",
}
(rcp/f"submission-{job}.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print("WROTE", rcp/f"submission-{job}.json")
PY
