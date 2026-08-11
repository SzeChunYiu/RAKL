#!/bin/bash
#SBATCH --job-name=p2-alr-154
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/alr_baselines_v1/p2-alr-154-%j.out
#SBATCH --error=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/alr_baselines_v1/p2-alr-154-%j.err

# Paper II / issue #154 ALR model baseline (non-confirmatory).
# Deterministic controls + BASE_DIRECT_STRONG_PROMPT on staged Qwen2.5-0.5B.
# Does not clear #247. grants_authority=false.

set -euo pipefail
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="${REPO:-$ROOT/repo}"
PYTHON="${PYTHON:-$ROOT/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11}"
# Default to HF snapshot hash dir (config.json lives under snapshot/, not repo root).
MODEL="${MODEL_DIR:-$ROOT/assets/paper2-cpu-v3-2/model/Qwen--Qwen2.5-0.5B-Instruct/7ae557604adf67be50417f59c2c2f167def9a775}"
RCP=$ROOT/receipts/alr_baselines_v1
RUN=$ROOT/runs/alr_baselines_v1
EXPECTED_REPO_SHA="${EXPECTED_REPO_SHA:?}"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$REPO/src"

mkdir -p "$RCP" "$RUN" "$ROOT/logs/alr_baselines_v1"
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
echo "ALR baselines #154 at $EXPECTED_REPO_SHA job=$SLURM_JOB_ID model=$MODEL"

OUTDIR="$OUTDIR" MODEL_DIR="$MODEL" EXPECTED_REPO_SHA="$EXPECTED_REPO_SHA" \
RCP="$RCP" REPO="$REPO" "$PYTHON" - <<'PY'
import datetime, json, os, pathlib, traceback
from rakl.alr_model_baselines import (
    HfCausalLmBackend,
    plan_lunarc_submission,
    run_baseline_arm,
    run_deterministic_controls,
    validate_preregistration,
)

outdir = pathlib.Path(os.environ["OUTDIR"])
rcp = pathlib.Path(os.environ["RCP"])
model_dir = pathlib.Path(os.environ["MODEL_DIR"])
job_id = os.environ.get("SLURM_JOB_ID", "unknown")
sha = os.environ["EXPECTED_REPO_SHA"]

validate_preregistration()
plan = dict(plan_lunarc_submission())
if plan.get("status") != "READY_TO_SUBMIT":
    raise SystemExit(f"lunarc plan not ready: {plan}")

controls = [r.to_dict() for r in run_deterministic_controls()]
model_receipt = None
model_error = None
try:
    backend = HfCausalLmBackend(model_dir, max_new_tokens=192, device="cpu")
    model_receipt = run_baseline_arm(
        "BASE_DIRECT_STRONG_PROMPT",
        authorize_model_run=True,
        model_backend=backend,
    ).to_dict()
except Exception as exc:  # noqa: BLE001 - record fail-closed
    model_error = {"error": str(exc), "traceback": traceback.format_exc()}
    model_receipt = {
        "status": "BLOCKED",
        "reason": f"model backend failed: {exc}",
        "grants_authority": False,
        "evaluation": None,
    }

bundle = {
    "schema_version": "paper2-alr-baseline-job-receipt-v1",
    "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    "issue": 154,
    "slurm_job_id": job_id,
    "expected_repo_sha": sha,
    "model_dir": str(model_dir),
    "lunarc_plan": plan,
    "deterministic_controls": controls,
    "model_arm": model_receipt,
    "model_error": model_error,
    "grants_authority": False,
    "claim_boundary": (
        "Non-confirmatory ALR V2 baseline job. Deterministic controls + one direct-prompt "
        "model arm. Does not mint novelty, RAKL superiority, or confirmatory ALR claims."
    ),
    "verdict": (
        "MODEL_SCORED_NON_CONFIRMATORY"
        if isinstance(model_receipt, dict) and model_receipt.get("status") == "MODEL_SCORED_NON_CONFIRMATORY"
        else "BLOCKED_OR_PARTIAL"
    ),
}
out = outdir / "alr_baseline_bundle.json"
out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
final = rcp / f"job-{job_id}.json"
final.write_text(out.read_text(encoding="utf-8"), encoding="utf-8")
print("WROTE", final)
print("VERDICT", bundle["verdict"])
if bundle["verdict"] != "MODEL_SCORED_NON_CONFIRMATORY":
    raise SystemExit(2)
PY
