#!/bin/bash
#SBATCH --job-name=p2-a3a4-156
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:20:00
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/a3_a4_conformance_v1/p2-a3a4-156-%j.out
#SBATCH --error=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/a3_a4_conformance_v1/p2-a3a4-156-%j.err

set -euo pipefail
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="${REPO:-$ROOT/repo}"
PYTHON="${PYTHON:-$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11}"
DEPS="${PYTEST_DEPS:-$ROOT/runs/a3_a4_conformance_v1/pydeps}"
RCP=$ROOT/receipts/a3_a4_conformance_v1
RUN=$ROOT/runs/a3_a4_conformance_v1
EXPECTED_REPO_SHA="${EXPECTED_REPO_SHA:?}"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$DEPS:$REPO/src"

mkdir -p "$RCP" "$RUN" "$DEPS" "$ROOT/logs/a3_a4_conformance_v1"
cd "$REPO"
HEAD=$(git rev-parse HEAD)
ORIG=$(git rev-parse refs/remotes/origin/main)
if [[ "$HEAD" != "$EXPECTED_REPO_SHA" || "$ORIG" != "$EXPECTED_REPO_SHA" ]]; then
  echo "SHA mismatch" >&2; exit 42
fi
if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  echo "dirty" >&2; exit 43
fi
OUTDIR="$RUN/job-${SLURM_JOB_ID}"
mkdir -p "$OUTDIR"

if ! "$PYTHON" -c "import pytest" 2>/dev/null; then
  "$PYTHON" -m pip install --no-cache-dir --target "$DEPS" "pytest>=8" >/dev/null
fi

set +e
"$PYTHON" -m pytest -q tests/test_ablation_a3_a4_conformance.py --tb=line 2>&1 | tee "$OUTDIR/pytest.out"
PY_RC=${PIPESTATUS[0]}
set -e

OUTDIR="$OUTDIR" RCP="$RCP" EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA" PY_RC="$PY_RC" "$PYTHON" - <<'PY'
import datetime, json, os, pathlib
from rakl.ablation_a3_a4_conformance import run_conformance

outdir = pathlib.Path(os.environ["OUTDIR"])
rcp = pathlib.Path(os.environ["RCP"])
job = os.environ.get("SLURM_JOB_ID", "unknown")
report = run_conformance()
payload = report.to_dict()
bundle = {
    "schema_version": "paper2-a3-a4-conformance-job-receipt-v1",
    "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
    "issue": 156,
    "slurm_job_id": job,
    "expected_repo_sha": os.environ["EXPECTED_REPO_SHA"],
    "pytest_exit_code": int(os.environ["PY_RC"]),
    "conformance": payload,
    "grants_authority": False,
    "claim_boundary": "Cluster re-validation of frozen A3↔A4 cheap conformance only. Not matched empirical ablation.",
    "verdict": "CONFORMANCE_PASS" if int(os.environ["PY_RC"]) == 0 else "FAIL",
}
(outdir / "a3_a4_bundle.json").write_text(json.dumps(bundle, indent=2, sort_keys=True)+"\n", encoding="utf-8")
(rcp / f"job-{job}.json").write_text(json.dumps(bundle, indent=2, sort_keys=True)+"\n", encoding="utf-8")
print("VERDICT", bundle["verdict"])
raise SystemExit(0 if bundle["verdict"] == "CONFORMANCE_PASS" else 2)
PY
