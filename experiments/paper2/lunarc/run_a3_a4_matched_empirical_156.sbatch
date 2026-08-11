#!/bin/bash
#SBATCH --job-name=p2-a3a4-156
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:20:00
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/a3_a4_matched_156/p2-a3a4-156-%j.out
#SBATCH --error=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/a3_a4_matched_156/p2-a3a4-156-%j.err

# Paper II / issue #156 — cheap CPU freeze validation for matched A3↔A4 ablation.
# Validates packet + conformance + EMPIRICS_UNRUN dry status. Does NOT invent
# model ALR numbers and does not claim A4>A3 novelty.

set -euo pipefail
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="${REPO:-$ROOT/repo}"
PYTHON="${PYTHON:-$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11}"
DEPS="${PYTEST_DEPS:-$ROOT/runs/a3_a4_matched_156/pydeps}"
RCP=$ROOT/receipts/a3_a4_matched_156
RUN=$ROOT/runs/a3_a4_matched_156
EXPECTED_REPO_SHA="${EXPECTED_REPO_SHA:?}"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$DEPS:$REPO/src"

mkdir -p "$RCP" "$RUN" "$ROOT/logs/a3_a4_matched_156" "$DEPS"

cd "$REPO"
HEAD=$(git rev-parse HEAD)
ORIG=$(git rev-parse refs/remotes/origin/main)
if [[ "$HEAD" != "$EXPECTED_REPO_SHA" || "$ORIG" != "$EXPECTED_REPO_SHA" ]]; then
  echo "SHA mismatch head=$HEAD origin=$ORIG expected=$EXPECTED_REPO_SHA" >&2
  exit 42
fi
if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  echo "dirty checkout" >&2
  git status --porcelain --untracked-files=all >&2
  exit 43
fi

OUTDIR="$RUN/job-${SLURM_JOB_ID}"
mkdir -p "$OUTDIR"
echo "running #156 A3↔A4 matched empirical freeze validation at $EXPECTED_REPO_SHA (job $SLURM_JOB_ID)"

if ! "$PYTHON" -c "import pytest" 2>/dev/null; then
  echo "staging pytest into $DEPS"
  "$PYTHON" -m pip install --no-cache-dir --target "$DEPS" "pytest>=8" "jsonschema>=4" >/dev/null
fi

set +e
"$PYTHON" -m pytest -q \
  tests/test_ablation_a3_a4_conformance.py \
  tests/test_ablation_a3_a4_matched_empirical.py \
  --tb=line 2>&1 | tee "$OUTDIR/pytest.out"
PYTEST_RC=${PIPESTATUS[0]}
set -e

OUTDIR="$OUTDIR" SLURM_JOB_ID="$SLURM_JOB_ID" EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA" \
PYTEST_RC="$PYTEST_RC" "$PYTHON" - <<'PY'
import json, os, pathlib, shutil
from rakl.ablation_a3_a4_matched_empirical import run_dry_status, validate_packet

outdir = pathlib.Path(os.environ["OUTDIR"])
job_id = os.environ["SLURM_JOB_ID"]
packet = validate_packet()
report = run_dry_status(packet=packet, slurm_job_id=job_id)
# Copy in-repo status into job outdir for harvest.
src = pathlib.Path("research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICAL_STATUS.json")
shutil.copy2(src, outdir / "A3_A4_MATCHED_EMPIRICAL_STATUS.json")
receipt = {
    "schema_version": "paper2-a3-a4-matched-empirical-lunarc-receipt-v1",
    "issue": 156,
    "slurm_job_id": job_id,
    "expected_repo_sha": os.environ["EXPECTED_REPO_SHA"],
    "pytest_rc": int(os.environ["PYTEST_RC"]),
    "status": report.status,
    "packet_hash": report.packet_hash,
    "packet_status": packet.get("status"),
    "a3_score": None,
    "a4_score": None,
    "grants_scientific_authority": False,
    "results_invented": False,
    "claim_boundary": (
        "CPU freeze validation only. EMPIRICS_UNRUN — no model arm scores. "
        "Not MemTX/PPMF/AutoSci; no A4>A3 novelty claim."
    ),
    "verdict": "FREEZE_VALIDATED_EMPIRICS_UNRUN" if int(os.environ["PYTEST_RC"]) == 0 and report.status == "EMPIRICS_UNRUN" else "FREEZE_VALIDATION_FAILED",
}
(outdir / "lunarc_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
rcp = pathlib.Path("/projects/hep/fs9/users/scyiu/RAKL-paper2/receipts/a3_a4_matched_156")
rcp.mkdir(parents=True, exist_ok=True)
(rcp / f"job-{job_id}-receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2, sort_keys=True))
raise SystemExit(0 if receipt["verdict"] == "FREEZE_VALIDATED_EMPIRICS_UNRUN" else 1)
PY
