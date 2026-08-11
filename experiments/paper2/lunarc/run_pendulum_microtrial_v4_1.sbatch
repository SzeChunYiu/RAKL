#!/usr/bin/env bash
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=9G
#SBATCH --job-name=p2-pend-v4-1
#SBATCH --output=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/v4_1/p2-pend-v4-1-%j.out
#SBATCH --error=/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/v4_1/p2-pend-v4-1-%j.err

set -euo pipefail

ROOT=/projects/hep/fs9/users/scyiu/RAKL-paper2
REPO="$ROOT/repo"
STAGED="$ROOT/assets/paper2-cpu-v3-2"
PYTHON="$STAGED/runtime/python/bin/python3.11"
PACKET_REL=research/paper2_microtrial_v4_1/EXECUTION_PACKET_V4_1_20260811.json
BATCH_CONTRACT_REL=research/paper2_microtrial_v4_1/BATCH_CONTRACT_V4_1.json
RESULT_SCHEMA_REL=schemas/paper2-pendulum-microtrial-result.schema.json
TASK_SEED_BUILDER_REL=experiments/paper2/lunarc/build_task_seed_receipt_v4_1.py
ATTESTER_REL=experiments/paper2/lunarc/attest_model_snapshot_v4.py
ATTESTATION_SCHEMA_REL=schemas/paper2-model-snapshot-attestation-v4.schema.json
TASK_SEED_SCHEMA_REL=schemas/paper2-pendulum-task-seed-receipt-v4-1.schema.json
MODEL_MANIFEST_REL=research/paper2_microtrial_v4/MODEL_MANIFEST_V4.json
TOKENIZER_MANIFEST_REL=research/paper2_microtrial_v4/TOKENIZER_MANIFEST_V4.json

: "${EXPECTED_REPO_SHA:?EXPECTED_REPO_SHA is required}"
: "${BATCH_CONTRACT_SHA256:?BATCH_CONTRACT_SHA256 is required}"
: "${SLURM_JOB_ID:?SLURM_JOB_ID is required}"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"

test -x "$PYTHON"
test "$(sha256sum "$REPO/$BATCH_CONTRACT_REL" | awk '{print $1}')" = "$BATCH_CONTRACT_SHA256"
test "$(git -C "$REPO" rev-parse HEAD)" = "$EXPECTED_REPO_SHA"
test "$(git -C "$REPO" rev-parse refs/remotes/origin/main)" = "$EXPECTED_REPO_SHA"
test -z "$(git -C "$REPO" status --porcelain --untracked-files=all)"
git -C "$REPO" merge-base --is-ancestor 3bf46b505af249802faa277d3ec865f4d9664853 "$EXPECTED_REPO_SHA"
test "$(git -C "$REPO" remote get-url origin)" = "https://github.com/SzeChunYiu/RAKL.git"

# Revalidate every executable/evidence binding on the allocated node.  The
# inherited V4 semantic auditor does not know V4.1's normalization lineage.
"$PYTHON" - "$REPO" "$REPO/$BATCH_CONTRACT_REL" "$EXPECTED_REPO_SHA" <<'PY'
import hashlib, json, pathlib, subprocess, sys
repo=pathlib.Path(sys.argv[1]); contract_path=pathlib.Path(sys.argv[2]); expected=sys.argv[3]
contract=json.loads(contract_path.read_text(encoding="utf-8"))
if contract.get("output_normalization_policy_id") != "PENDULUM_EXACT_JSON_OR_SINGLE_LOWERCASE_JSON_FENCE_V4_1":
    raise SystemExit("V4.1 normalization policy mismatch")
if contract.get("v4_reinterpretation_permitted") is not False:
    raise SystemExit("V4 reinterpretation prohibition missing")
if contract.get("chronology_class") != "ADAPTIVE_PARSER_REPLAY_FRESH_ONLY_TO_V4_1_OUTPUTS":
    raise SystemExit("adaptive chronology class mismatch")
if contract.get("parent_v4_results_opened_before_batch_freeze") is not True:
    raise SystemExit("adaptive V4 parent chronology missing")
if contract.get("v4_1_outputs_opened_before_batch_freeze") is not False:
    raise SystemExit("V4.1 output chronology violated")
if subprocess.run(["git","merge-base","--is-ancestor",contract["minimum_execution_ancestor_sha"],expected],cwd=repo).returncode:
    raise SystemExit("packet parent is not an ancestor")
for binding in contract["bindings"]:
    path=repo/binding["path"]
    if not path.is_file(): raise SystemExit(f"allocated binding missing:{binding['role']}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != binding["sha256"]:
        raise SystemExit(f"allocated binding mismatch:{binding['role']}")
packet=json.loads((repo/"research/paper2_microtrial_v4_1/EXECUTION_PACKET_V4_1_20260811.json").read_text())
policy_path=repo/"research/paper2_microtrial_v4_1/OUTPUT_NORMALIZATION_CONTRACT_V4_1.json"
ingest_path=repo/"research/paper2_microtrial_v4/PAPER2_V4_NATIVE_JOB_3475193_INGEST_RECEIPT_20260811.json"
normalizer_path=repo/"src/rakl/paper2_pendulum_microtrial_v4_1.py"
if packet.get("chronology_class") != contract["chronology_class"]:
    raise SystemExit("packet chronology class mismatch")
if packet.get("adaptive_replay_status") != "FROZEN_ADAPTIVE_CANDIDATE_REQUIRES_POST_MERGE_BATCH_HEAD_BINDING":
    raise SystemExit("packet adaptive replay status mismatch")
if packet.get("parent_v4_results_opened_before_v4_1_freeze") is not True:
    raise SystemExit("packet adaptive chronology missing")
if packet.get("v4_1_outputs_opened_before_freeze") is not False:
    raise SystemExit("packet V4.1 output chronology violated")
if packet.get("evaluated_results_opened_before_freeze_scope") != "V4_1_OUTPUTS_ONLY_PARENT_V4_KNOWN":
    raise SystemExit("packet result-access scope mismatch")
if packet.get("evaluated_task_seed_unit_count_before_freeze_scope") != "V4_1_OUTPUTS_ONLY_PARENT_V4_KNOWN":
    raise SystemExit("packet evaluated-unit scope mismatch")
if packet.get("v4_negative_history",{}).get("reinterpretation_permitted") is not False:
    raise SystemExit("packet V4 reinterpretation prohibition missing")
for name,path in (("output_normalization_contract",policy_path),("v4_native_ingest",ingest_path),("output_normalizer",normalizer_path)):
    binding=packet.get("bindings",{}).get(name,{})
    if binding.get("path") != str(path.relative_to(repo)):
        raise SystemExit(f"packet binding path mismatch:{name}")
    if binding.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
        raise SystemExit(f"packet binding hash mismatch:{name}")
policy=json.loads(policy_path.read_text())
if policy.get("contract_id") != contract["output_normalization_policy_id"]:
    raise SystemExit("normalization contract identity mismatch")
if policy.get("chronology_class") != contract["chronology_class"]:
    raise SystemExit("normalization contract chronology class mismatch")
if policy.get("status") != "FROZEN_AFTER_V4_RESULT_BEFORE_V4_1_OUTPUT_ACCESS":
    raise SystemExit("normalization contract chronology mismatch")
if policy.get("v4_reinterpretation_permitted") is not False or policy.get("threshold_or_score_change_permitted") is not False:
    raise SystemExit("normalization contract authority mismatch")
ingest=json.loads(ingest_path.read_text())
outcome=ingest.get("task_seed_outcome",{})
if ingest.get("native_execution",{}).get("slurm_job_id") != "3475193":
    raise SystemExit("V4 negative parent job mismatch")
if outcome.get("frozen_parse_valid_arm_count") != 0 or outcome.get("frozen_scorable_arm_count") != 0:
    raise SystemExit("V4 negative parent score state mismatch")
if outcome.get("posthoc_normalized_scores_authorized") is not False:
    raise SystemExit("V4 posthoc score prohibition missing")
PY

cd "$REPO"
RUN_ROOT="$ROOT/runs/v4_1"
OUTPUT_DIR="$RUN_ROOT/PENDULUM_SEALED_KNOWN_ANSWER_001-seed-17-job-${SLURM_JOB_ID}"
RECEIPT_DIR="$ROOT/receipts/v4_1/job-${SLURM_JOB_ID}"
test ! -e "$OUTPUT_DIR"
test ! -e "$RECEIPT_DIR"
mkdir -p "$RECEIPT_DIR"
CREATED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Allocated-node semantic preflight must pass before inference is attempted.
PYTHONPATH="$REPO/src" "$PYTHON" -m rakl.paper2_pendulum_microtrial preflight \
  "$PACKET_REL" \
  --output "$RECEIPT_DIR/allocated_preflight.json" \
  --created-at-utc "$CREATED_AT_UTC"

"$PYTHON" "$ATTESTER_REL" \
  --repo "$REPO" \
  --packet "$PACKET_REL" \
  --model-manifest "$MODEL_MANIFEST_REL" \
  --tokenizer-manifest "$TOKENIZER_MANIFEST_REL" \
  --schema "$ATTESTATION_SCHEMA_REL" \
  --phase PRE_INFERENCE \
  --output "$RECEIPT_DIR/model_snapshot_pre.json"

PYTHONPATH="$REPO/src" "$PYTHON" -m rakl.paper2_pendulum_microtrial_v4_1 \
  "$PACKET_REL" \
  --output-dir "$OUTPUT_DIR" \
  --created-at-utc "$CREATED_AT_UTC" \
  --expected-checkout-head-sha "$EXPECTED_REPO_SHA"

"$PYTHON" "$ATTESTER_REL" \
  --repo "$REPO" \
  --packet "$PACKET_REL" \
  --model-manifest "$MODEL_MANIFEST_REL" \
  --tokenizer-manifest "$TOKENIZER_MANIFEST_REL" \
  --schema "$ATTESTATION_SCHEMA_REL" \
  --phase POST_INFERENCE \
  --result "$OUTPUT_DIR/result_receipt.json" \
  --output "$RECEIPT_DIR/model_snapshot_post.json"

"$PYTHON" "$TASK_SEED_BUILDER_REL" \
  --packet "$PACKET_REL" \
  --result "$OUTPUT_DIR/result_receipt.json" \
  --run-manifest "$OUTPUT_DIR/run_manifest.json" \
  --result-schema "$RESULT_SCHEMA_REL" \
  --task-seed-schema "$TASK_SEED_SCHEMA_REL" \
  --pre-attestation "$RECEIPT_DIR/model_snapshot_pre.json" \
  --post-attestation "$RECEIPT_DIR/model_snapshot_post.json" \
  --attestation-schema "$ATTESTATION_SCHEMA_REL" \
  --output "$OUTPUT_DIR/task_seed_receipt.json"

sha256sum \
  "$RECEIPT_DIR/allocated_preflight.json" \
  "$RECEIPT_DIR/model_snapshot_pre.json" \
  "$OUTPUT_DIR/run_manifest.json" \
  "$OUTPUT_DIR/result_receipt.json" \
  "$RECEIPT_DIR/model_snapshot_post.json" \
  "$OUTPUT_DIR/task_seed_receipt.json"
