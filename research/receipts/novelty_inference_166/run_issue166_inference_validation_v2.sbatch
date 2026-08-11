#!/bin/bash
#SBATCH --job-name=p2-inf-166b
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/novelty_inference_166/p2-inf-166-%j.out
#SBATCH --error=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/novelty_inference_166/p2-inf-166-%j.err

set -euo pipefail
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO=/projects/hep/fs9/users/scyiu/RAKL-paper2/repo
PYTHON=/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/paper2-cpu-v3-2/runtime/python/bin/python3.11
DEPS=/projects/hep/fs9/users/scyiu/RAKL-paper2/runs/novelty_inference_166/pydeps
RCP=/projects/hep/fs9/users/scyiu/RAKL-paper2/receipts/novelty_inference_166
RUN=/projects/hep/fs9/users/scyiu/RAKL-paper2/runs/novelty_inference_166
EXPECTED_REPO_SHA="${EXPECTED_REPO_SHA:?}"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$DEPS:$REPO/src"

cd "$REPO"
HEAD=$(git rev-parse HEAD)
ORIG=$(git rev-parse refs/remotes/origin/main)
if [[ "$HEAD" != "$EXPECTED_REPO_SHA" || "$ORIG" != "$EXPECTED_REPO_SHA" ]]; then
  echo "SHA mismatch head=$HEAD origin=$ORIG expected=$EXPECTED_REPO_SHA" >&2
  exit 42
fi
if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  echo "dirty checkout" >&2
  exit 43
fi

OUTDIR="$RUN/job-${SLURM_JOB_ID}"
mkdir -p "$OUTDIR"
echo "running #166 validation v2 at $EXPECTED_REPO_SHA"

set +e
"$PYTHON" -m pytest -q   tests/test_inference.py   tests/test_rakl_v3_experience_benchmark.py   tests/test_epistemic_noninterference.py   tests/test_authority_leakage_benchmark.py   --tb=line 2>&1 | tee "$OUTDIR/pytest.out"
PYTEST_RC=${PIPESTATUS[0]}
set -e

OUTDIR="$OUTDIR" "$PYTHON" - <<'PY'
import json, os, random, time
from rakl.inference import paired_lift_verdict, InferenceStatus
outdir = os.environ['OUTDIR']
rng = random.Random(166)
n_tasks, n_trials = 8, 400
sign_fp = interval_fp = 0
t0 = time.time()
for i in range(n_trials):
    diffs = [rng.gauss(0.0, 0.05) for _ in range(n_tasks)]
    if (sum(diffs) / len(diffs)) > 0:
        sign_fp += 1
    v = paired_lift_verdict(diffs, alpha=0.05, n_boot=2000, n_perm=2000, seed=1000 + i)
    if v.status == InferenceStatus.MEASURED_AND_DISTINGUISHABLE and v.excludes_null and v.point_estimate > 0:
        interval_fp += 1
receipt = {
  "schema_version": "paper2-issue166-null-sim-v1",
  "issue": 166,
  "claim_boundary": "Software/methodology validation only under synthetic true-null paired diffs. No Paper II empirical task outcomes opened. Does not grant transfer_gain or capability authority.",
  "n_tasks": n_tasks,
  "n_trials": n_trials,
  "sign_test_false_positive_rate": sign_fp / n_trials,
  "interval_excludes_null_false_positive_rate": interval_fp / n_trials,
  "sign_fp_count": sign_fp,
  "interval_fp_count": interval_fp,
  "elapsed_seconds": time.time() - t0,
  "parent_failed_job_id": "3476530",
  "verdict": "NULL_SIM_COMPLETE",
}
path = os.path.join(outdir, "sign_vs_interval_null_sim.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(receipt, f, indent=2, sort_keys=True)
    f.write("\n")
print(json.dumps(receipt, indent=2, sort_keys=True))
PY

"$PYTHON" - <<PY
import datetime, json, pathlib, subprocess, os
outdir = pathlib.Path("$OUTDIR")
repo = pathlib.Path("$REPO")
pytest_out = (outdir / "pytest.out").read_text(encoding="utf-8", errors="replace")
sim = json.loads((outdir / "sign_vs_interval_null_sim.json").read_text(encoding="utf-8"))
sha = subprocess.check_output(["git","rev-parse","HEAD"], cwd=repo, text=True).strip()
rc = int("$PYTEST_RC")
receipt = {
  "schema_version": "paper2-issue166-lunarc-validation-receipt-v1",
  "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
  "issue": 166,
  "related_issues": [152, 154, 155, 138],
  "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
  "supersedes_job_id": "3476530",
  "expected_repo_sha": "$EXPECTED_REPO_SHA",
  "executed_repo_sha": sha,
  "account": "lu2026-2-51",
  "partition": "lu48",
  "pytest_exit_code": rc,
  "pytest_deps_path": "$DEPS",
  "pytest_summary_tail": pytest_out.strip().splitlines()[-30:],
  "null_simulation": sim,
  "claim_boundary": "Cluster validation of stdlib inference + Paper II novelty gate tests on FS9 runtime. Not an empirical RESET-vs-LEARNING or 2x2 factorial result.",
  "verdict": "PASS" if rc == 0 else "FAIL_TESTS",
}
out = pathlib.Path("$RCP") / f"validation-{os.environ['SLURM_JOB_ID']}.json"
tmp = out.with_suffix(".tmp")
tmp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
tmp.replace(out)
print("WROTE", out)
print("VERDICT", receipt["verdict"])
PY
exit "$PYTEST_RC"
