#!/bin/bash
#SBATCH --job-name=p2-a3a4-emp
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/a3_a4_matched_empirics_156/p2-a3a4-emp-%j.out
#SBATCH --error=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/a3_a4_matched_empirics_156/p2-a3a4-emp-%j.err

# Paper II / issue #156 — matched A3↔A4 model empirics on frozen V2 panel.
# Requires FREEZE_VALIDATED + empirics authorize receipt. Non-confirmatory.

set -euo pipefail
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="${REPO:-$ROOT/repo}"
PYTHON="${PYTHON:-$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11}"
RCP=$ROOT/receipts/a3_a4_matched_empirics_156
RUN=$ROOT/runs/a3_a4_matched_empirics_156
EXPECTED_REPO_SHA="${EXPECTED_REPO_SHA:?}"
MODEL_ROOT="${MODEL_DIR:-$ROOT/assets/paper2-cpu-v3-2/model/Qwen--Qwen2.5-0.5B-Instruct}"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$REPO/src"

mkdir -p "$RCP" "$RUN" "$ROOT/logs/a3_a4_matched_empirics_156"

if [[ -f "$MODEL_ROOT/config.json" ]]; then
  MODEL="$MODEL_ROOT"
elif [[ -d "$MODEL_ROOT" ]]; then
  MODEL="$(find "$MODEL_ROOT" -mindepth 1 -maxdepth 1 -type d -exec test -f '{}/config.json' \; -print | sort | head -n 1)"
  if [[ -z "${MODEL}" ]]; then
    echo "no HF snapshot with config.json under $MODEL_ROOT" >&2
    exit 44
  fi
else
  echo "missing model path: $MODEL_ROOT" >&2
  exit 44
fi

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
echo "A3↔A4 matched empirics #156 at $EXPECTED_REPO_SHA job=$SLURM_JOB_ID model=$MODEL"

OUTDIR="$OUTDIR" MODEL_DIR="$MODEL" EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA" \
RCP="$RCP" "$PYTHON" - <<'PY'
import datetime, json, os, pathlib, traceback
from rakl.ablation_a3_a4_matched_empirical import (
    plan_matched_empirics_submission,
    run_matched_model_arms,
    validate_empirics_authorize,
    validate_packet,
)

outdir = pathlib.Path(os.environ["OUTDIR"])
rcp = pathlib.Path(os.environ["RCP"])
model_dir = pathlib.Path(os.environ["MODEL_DIR"])
job_id = os.environ.get("SLURM_JOB_ID", "unknown")
sha = os.environ["EXPECTED_REPO_SHA"]

packet = validate_packet()
auth = validate_empirics_authorize()
plan = plan_matched_empirics_submission()
if plan.get("status") != "READY_TO_SUBMIT":
    raise SystemExit(f"empirics plan not ready: {plan}")

error = None
report_dict = None
try:
    report = run_matched_model_arms(model_dir, authorize=True)
    report_dict = report.to_dict()
except Exception as exc:  # noqa: BLE001
    error = {"error": str(exc), "traceback": traceback.format_exc()}
    report_dict = {
        "status": "EMPIRICS_BLOCKED",
        "failures": [str(exc)],
        "a3_score": None,
        "a4_score": None,
        "grants_scientific_authority": False,
    }

verdict = (
    "SCORED_ARM_RESPONSES_NON_CONFIRMATORY"
    if isinstance(report_dict, dict) and report_dict.get("status") == "SCORED_ARM_RESPONSES"
    else "BLOCKED_OR_PARTIAL"
)
bundle = {
    "schema_version": "paper2-a3-a4-matched-empirics-job-receipt-v1",
    "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    "issue": 156,
    "slurm_job_id": job_id,
    "expected_repo_sha": sha,
    "model_dir": str(model_dir),
    "packet_hash": packet.get("artifact_hash"),
    "authorize_artifact_hash": auth.get("artifact_hash"),
    "plan": plan,
    "report": report_dict,
    "error": error,
    "grants_scientific_authority": False,
    "claim_boundary": (
        "Matched A3↔A4 model empirics on frozen V2. Non-confirmatory; "
        "not MemTX/PPMF/AutoSci; no A4>A3 novelty claim from this job alone."
    ),
    "verdict": verdict,
}
out = outdir / "matched_empirics_bundle.json"
out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
status = pathlib.Path("research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICAL_STATUS.json")
if status.is_file():
    (outdir / "A3_A4_MATCHED_EMPIRICAL_STATUS.json").write_text(
        status.read_text(encoding="utf-8"), encoding="utf-8"
    )
final = rcp / f"job-{job_id}.json"
final.write_text(out.read_text(encoding="utf-8"), encoding="utf-8")
print("WROTE", final)
print("VERDICT", verdict)
if verdict != "SCORED_ARM_RESPONSES_NON_CONFIRMATORY":
    raise SystemExit(2)
PY
