#!/usr/bin/env bash
# Copy FS9 #166 confirmatory receipts into the repo tree (or a destination dir).
# Usage: harvest_issue166_inference_validation.sh <slurm-job-id> [dest-dir]
# Default dest: research/receipts/novelty_inference_166 (relative to repo root / cwd).
set -euo pipefail

if [[ $# -lt 1 || ! "$1" =~ ^[0-9]+$ ]]; then
  echo "usage: $0 <slurm-job-id> [dest-dir]" >&2
  exit 64
fi

JOB_ID="$1"
ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
FS9_RCP=$ROOT/receipts/novelty_inference_166
FS9_RUN=$ROOT/runs/novelty_inference_166/job-${JOB_ID}

if [[ $# -ge 2 ]]; then
  DEST="$2"
else
  # Prefer repo-relative path when invoked from a checkout that has research/receipts.
  if [[ -d research/receipts ]]; then
    DEST=research/receipts/novelty_inference_166
  elif [[ -d "$ROOT/repo/research/receipts" ]]; then
    DEST=$ROOT/repo/research/receipts/novelty_inference_166
  else
    DEST=$FS9_RCP
  fi
fi

mkdir -p "$DEST/job-${JOB_ID}"

for f in submission-${JOB_ID}.json validation-${JOB_ID}.json; do
  if [[ -f "$FS9_RCP/$f" ]]; then
    cp -f "$FS9_RCP/$f" "$DEST/$f"
    echo "copied $FS9_RCP/$f -> $DEST/$f"
  else
    echo "missing $FS9_RCP/$f" >&2
  fi
done

for f in pytest.out sign_vs_interval_null_sim.json; do
  if [[ -f "$FS9_RUN/$f" ]]; then
    cp -f "$FS9_RUN/$f" "$DEST/job-${JOB_ID}/$f"
    echo "copied $FS9_RUN/$f -> $DEST/job-${JOB_ID}/$f"
  else
    echo "missing $FS9_RUN/$f" >&2
  fi
done

if command -v sha256sum >/dev/null 2>&1; then
  (cd "$DEST" && sha256sum "validation-${JOB_ID}.json" "job-${JOB_ID}/sign_vs_interval_null_sim.json" 2>/dev/null || true)
elif command -v shasum >/dev/null 2>&1; then
  (cd "$DEST" && shasum -a 256 "validation-${JOB_ID}.json" "job-${JOB_ID}/sign_vs_interval_null_sim.json" 2>/dev/null || true)
fi

echo "harvest complete for job $JOB_ID -> $DEST"
