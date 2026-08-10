#!/bin/bash
# This allocated-node smoke test is submitted only after the v2 gate passes.
# Account and partition are supplied by the exact run manifest/preflight CLI.
#SBATCH --job-name=rakl_p3_preflight
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --gres=gpu:1
#SBATCH --time=00:10:00
#SBATCH --output=paper3_preflight_%j.out

set -euo pipefail

: "${RAKL_EXPERIMENT_MANIFEST:?missing exact experiment manifest}"
: "${RAKL_GATE_RECEIPT:?missing exact gate receipt}"
: "${RAKL_EXPECTED_SUBJECT_SHA:?missing exact Git subject}"
: "${RAKL_REPO_PATH:?missing exact repository path}"

repo_path="$RAKL_REPO_PATH"
observed_subject="$(git -C "$repo_path" rev-parse HEAD)"
test "$observed_subject" = "$RAKL_EXPECTED_SUBJECT_SHA"
test -z "$(git -C "$repo_path" status --porcelain)"
export RAKL_OBSERVED_SUBJECT_SHA="$observed_subject"

python - "$RAKL_EXPERIMENT_MANIFEST" "$RAKL_GATE_RECEIPT" <<'PY'
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

manifest_path = Path(sys.argv[1]).resolve()
gate_path = Path(sys.argv[2]).resolve()
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
gate = json.loads(gate_path.read_text(encoding="utf-8"))

def canonical_hash(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()

assert manifest["subject_sha"] == os.environ["RAKL_EXPECTED_SUBJECT_SHA"]
assert str(Path(manifest["repo_path"]).resolve()) == str(Path(os.environ["RAKL_REPO_PATH"]).resolve())
observed_subject = os.environ["RAKL_OBSERVED_SUBJECT_SHA"]
assert observed_subject == manifest["subject_sha"]
assert canonical_hash(manifest) == os.environ["RAKL_EXPECTED_MANIFEST_SHA256"]
assert canonical_hash(gate) == os.environ["RAKL_EXPECTED_GATE_SHA256"]
assert canonical_hash(gate) == manifest["gate_receipt_sha256"]
assert gate["protocol_sha256"] == manifest["protocol_sha256"]
assert gate["benchmark_sha256"] == manifest["benchmark_sha256"]
assert gate["annotation_gate"]["passed"] is True
assert gate["diagnostic_signal_gate"]["passed"] is True
assert gate["overall_cheap_gate_passed"] is True
assert gate["expensive_training_authorized"] is True
assert gate["gate_verdict"] == "PASS_AUTHORIZE_CONDITIONAL_NEXT_PHASE"
lineage = {}
for artifact in ("protocol", "benchmark", "annotation_import_receipt"):
    artifact_path = Path(manifest[f"{artifact}_path"])
    assert artifact_path.is_absolute() and artifact_path.is_file()
    lineage[artifact] = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert canonical_hash(lineage[artifact]) == manifest[f"{artifact}_sha256"]
assert lineage["benchmark"]["subject_sha"] == manifest["subject_sha"]
assert lineage["benchmark"]["protocol_sha256"] == manifest["protocol_sha256"]
assert lineage["annotation_import_receipt"]["subject_sha"] == manifest["subject_sha"]
assert lineage["annotation_import_receipt"]["protocol_sha256"] == manifest["protocol_sha256"]
assert lineage["annotation_import_receipt"]["benchmark_sha256"] == manifest["benchmark_sha256"]
assert lineage["annotation_import_receipt"]["passed"] is True
assert lineage["annotation_import_receipt"]["training_authorized"] is False
assert lineage["annotation_import_receipt"]["failures"] == []
for artifact in ("task_set", "environment", "seed_schedule", "model_artifact"):
    artifact_path = Path(manifest[f"{artifact}_path"])
    assert artifact_path.is_file()
    assert hashlib.sha256(artifact_path.read_bytes()).hexdigest() == manifest[f"{artifact}_sha256"]

output = Path(manifest["fs9_output_dir"])
fs9_root = Path("/projects/hep/fs9/users/scyiu/RAKL-paper3")
assert ".." not in output.parts
assert output.parent == fs9_root
output.mkdir(parents=False, exist_ok=False)
receipt_dir = output / "receipts"
receipt_dir.mkdir()

gpu = subprocess.run(
    ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
    capture_output=True,
    text=True,
    check=True,
    shell=False,
).stdout.strip().splitlines()
receipt = {
    "schema_version": "paper3-lunarc-allocated-preflight-v1",
    "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "subject_sha": manifest["subject_sha"],
    "manifest_sha256": canonical_hash(manifest),
    "gate_receipt_sha256": canonical_hash(gate),
    "slurm_job_id": os.environ["SLURM_JOB_ID"],
    "slurm_account": os.environ.get("SLURM_JOB_ACCOUNT"),
    "slurm_partition": os.environ.get("SLURM_JOB_PARTITION"),
    "node": platform.node(),
    "python": platform.python_version(),
    "gpu": gpu,
    "verdict": "ALLOCATED_PREFLIGHT_PASS",
}
temporary = receipt_dir / ".allocated_preflight.json.tmp"
final = receipt_dir / "allocated_preflight.json"
temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
temporary.replace(final)
print(final)
PY
