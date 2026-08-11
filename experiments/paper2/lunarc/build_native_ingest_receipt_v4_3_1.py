#!/usr/bin/env python3
"""Build the governed repository-ingest receipt for a harvested V4.3.1 job.

This builder never executes or re-scores a model.  It admits an already
harvested native bundle only after the checkout, scheduler, snapshot,
task/seed, result, normalization, and immutable V4.3 DIRECT parse-null parent agree.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
from typing import Any

import jsonschema


ROOT = Path(__file__).resolve().parents[3]
V43 = ROOT / "research/paper2_microtrial_v4_3"
V431 = ROOT / "research/paper2_microtrial_v4_3_1"
SCHEMA = ROOT / "schemas/paper2-v4-3-1-native-ingest-receipt.schema.json"
POLICY_ID = "PENDULUM_EXACT_JSON_OR_FENCE_PLUS_REGISTERED_ENVELOPE_UNWRAP_V4_3_1"
TASK_ID = "PENDULUM_SEALED_KNOWN_ANSWER_001"
CONDITIONS = {"DIRECT_CORPUS", "RAKL_CONTEXT"}
PACKET_HEAD_SHA = "0ab47a182537dc3842d7ea4ea24e45b92cc5dc8f"
OUTCOME_REASON = (
    "V4.3.1 registered-envelope unwrap repairs the V4.3 DIRECT schema-envelope "
    "serialization residual: both arms are parse_valid/scorable (DIRECT 1/5, "
    "RAKL_CONTEXT 3/5). Both still fail the unchanged exact conceptual gate, so "
    "exact_conceptual_pass_arm_count=0. This is serialization-only repair evidence, "
    "not a 1.5B improvement claim. Parent 3476566 remains the DIRECT parse-null "
    "residual. Zero valid scientific successes remain; arm comparison is not "
    "estimable; local zero provider API charge omits registered cost coordinates."
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _validate(document: dict[str, Any], schema_path: Path) -> None:
    jsonschema.Draft202012Validator(
        _load(schema_path), format_checker=jsonschema.FormatChecker()
    ).validate(document)


def _utc_timestamp(value: object, *, field: str) -> datetime:
    _require(isinstance(value, str), f"{field} is not a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} is not ISO-8601: {value}") from exc
    _require(parsed.tzinfo is not None, f"{field} has no timezone")
    _require(parsed.utcoffset() == timezone.utc.utcoffset(parsed), f"{field} is not UTC")
    return parsed


def _verify_standalone_evidence(
    *,
    native: Path,
    run: Path,
    result: dict[str, Any],
    task_seed: dict[str, Any],
    job_id: str,
) -> None:
    result_records = {record["blind_id"]: record for record in result["records"]}
    task_records = {record["blind_id"]: record for record in task_seed["records"]}
    _require(set(result_records) == set(task_records), "standalone arm identity mismatch")
    for blind_id, record in result_records.items():
        raw = _load(run / f"raw_outputs/{blind_id}.json")
        provider = _load(run / f"provider_receipts/{blind_id}.json")
        resource = _load(run / f"resource_receipts/{blind_id}.json")
        _require(raw == record["raw_output"], f"standalone raw output mismatch: {blind_id}")
        _require(provider == record["provider_receipt"], f"standalone provider receipt mismatch: {blind_id}")
        _require(resource == record["resource_receipt"], f"standalone resource receipt mismatch: {blind_id}")
        _require(
            task_records[blind_id]["raw_output_canonical_sha256"] == _canonical_sha(raw),
            f"canonical raw-output hash mismatch: {blind_id}",
        )
        _require(task_records[blind_id]["resource_receipt"] == resource, f"task/seed resource mismatch: {blind_id}")
        _require(task_records[blind_id]["score"] == record["score"], f"task/seed score mismatch: {blind_id}")

    blinded = _load(run / "blinded_scores.json")
    blinded_scores = {score["blind_id"]: score for score in blinded["scores"]}
    _require(
        blinded_scores == {blind_id: record["score"] for blind_id, record in result_records.items()},
        "standalone blinded-score records differ from result receipt",
    )
    _require(
        blinded["run_manifest_sha256"] == result["run_manifest_sha256"],
        "blinded-score manifest link mismatch",
    )

    warning = (
        "The following generation flags are not valid and may be ignored: "
        "['temperature', 'top_p', 'top_k']. Set `TRANSFORMERS_VERBOSITY=info` "
        "for more details.\n"
    )
    stderr = (native / f"logs/v4_3_1/p2-pend-v431-{job_id}.err").read_text(
        encoding="utf-8"
    )
    _require(stderr == warning * 2, "stderr warning bytes differ from admitted native log")

    stdout_lines = (
        native / f"logs/v4_3_1/p2-pend-v431-{job_id}.out"
    ).read_text(encoding="utf-8").splitlines()
    _require(len(stdout_lines) == 1, "stdout receipt-line count mismatch")
    _require(json.loads(stdout_lines[0]) == {"verdict": "PASS", "blockers": []}, "stdout preflight verdict mismatch")


def _summarize_task_seed(task_seed: dict[str, Any]) -> dict[str, Any]:
    source_records = {record["condition"]: record for record in task_seed["records"]}
    records = []
    exact_passes = 0
    for condition in ("DIRECT_CORPUS", "RAKL_CONTEXT"):
        source = source_records[condition]
        resource = source["resource_receipt"]
        score = source["score"]
        exact_pass = bool(
            isinstance(score["score"], dict)
            and score["score"].get("exact_conceptual_pass") is True
        )
        exact_passes += int(exact_pass)
        token_count = resource["input_tokens"] + resource["output_tokens"]
        records.append(
            {
                "blind_id": source["blind_id"],
                "condition": condition,
                "parse_valid": source["parse_valid"],
                "parse_error": score["parse_error"],
                "score": score["score"],
                "input_tokens": resource["input_tokens"],
                "output_tokens": resource["output_tokens"],
                "wall_time_ms": resource["wall_time_ms"],
                "process_high_water_rss_bytes_after_arm": resource[
                    "process_high_water_rss_bytes_after_arm"
                ],
                "provider_api_cost_usd": resource["provider_api_cost_usd"],
                "unpriced_coordinates": resource["unpriced_coordinates"],
                "token_count": token_count,
                "token_count_per_valid_scientific_success": (
                    token_count if exact_pass else "INFINITE"
                ),
            }
        )
    return {
        "task_id": task_seed["task_id"],
        "seed": task_seed["seed"],
        "arm_record_count": task_seed["arm_record_count"],
        "evaluated_task_seed_unit_count": task_seed["evaluated_task_seed_unit_count"],
        "parse_valid_arm_count": task_seed["parse_valid_arm_count"],
        "scorable_arm_count": task_seed["scorable_arm_count"],
        "exact_conceptual_pass_arm_count": exact_passes,
        "valid_scientific_success_arm_count": exact_passes,
        "arm_comparison_estimable": False,
        "score_comparison_permitted": False,
        "fully_costed_cost_per_success_estimable": False,
        "fully_costed": False,
        "reason": OUTCOME_REASON,
        "records": records,
    }


def verify_ingest_receipt(receipt: dict[str, Any], *, root: Path = ROOT) -> None:
    schema = receipt["ingest_schema"]
    schema_path = root / schema["path"]
    _require(schema_path.is_file(), "ingest schema path missing")
    _require(_sha(schema_path) == schema["sha256"], "ingest schema self-hash mismatch")

    job_id = str(receipt["native_execution"]["slurm_job_id"])
    copied: dict[str, tuple[int, str]] = {}
    prefix = f"research/paper2_microtrial_v4_3_1/native_job_{job_id}/"
    by_role: dict[str, list[Path]] = {}
    for item in receipt["source_files"]:
        path = root / item["path"]
        _require(path.is_file(), f"receipted source missing: {path}")
        _require(path.stat().st_size == item["bytes"], f"receipted size mismatch: {path}")
        _require(_sha(path) == item["sha256"], f"receipted hash mismatch: {path}")
        copied[item["path"].removeprefix(prefix)] = (item["bytes"], item["sha256"])
        by_role.setdefault(item["role"], []).append(path)
    _require(len(copied) == len(receipt["source_files"]), "duplicate receipted source path")

    bundle = receipt["source_bundle"]
    bundle_path = root / bundle["path"]
    _require(bundle_path.is_file(), "transport bundle missing")
    _require(bundle_path.stat().st_size == bundle["bytes"], "transport bundle size mismatch")
    _require(_sha(bundle_path) == bundle["sha256"], "transport bundle hash mismatch")
    _require(_bundle_members(bundle_path) == copied, "transport bundle member mismatch")

    result_path = by_role["result_receipt"][0]
    pre_path, post_path = sorted(by_role["snapshot_attestation"], key=lambda path: path.name)
    if pre_path.name.endswith("post.json"):
        pre_path, post_path = post_path, pre_path
    pre = _load(pre_path)
    post = _load(post_path)
    native = receipt["native_execution"]
    _require(
        native["post_attestation_result_receipt_sha256"] == _sha(result_path),
        "ingest post-result hash mismatch",
    )
    _require(post["result_receipt_sha256"] == _sha(result_path), "source post-result hash mismatch")
    _require(
        native["snapshot_canonical_sha256"]
        == pre["snapshot_canonical_sha256"]
        == post["snapshot_canonical_sha256"],
        "ingest snapshot identity mismatch",
    )
    v4_parent = receipt["v4_negative_parent"]
    _require(_sha(root / v4_parent["path"]) == v4_parent["sha256"], "V4 parent hash mismatch")
    run_manifest_path = by_role["run_manifest"][0]
    task_seed_path = by_role["task_seed_receipt"][0]
    result = _load(result_path)
    task_seed = _load(task_seed_path)
    _require(
        task_seed["result_receipt_sha256"] == _sha(result_path),
        "verified task/seed result link mismatch",
    )
    _require(
        task_seed["run_manifest_sha256"] == _sha(run_manifest_path),
        "verified task/seed run-manifest link mismatch",
    )
    _require(
        task_seed["snapshot_attestations"]["pre_sha256"] == _sha(pre_path),
        "verified task/seed pre-snapshot link mismatch",
    )
    _require(
        task_seed["snapshot_attestations"]["post_sha256"] == _sha(post_path),
        "verified task/seed post-snapshot link mismatch",
    )
    run = run_manifest_path.parent
    native_root = root / f"research/paper2_microtrial_v4_3_1/native_job_{job_id}"
    _require(run.is_relative_to(native_root), "receipted run path escapes native root")
    _verify_standalone_evidence(
        native=native_root,
        run=run,
        result=result,
        task_seed=task_seed,
        job_id=job_id,
    )
    _require(
        receipt["task_seed_outcome"] == _summarize_task_seed(task_seed),
        "ingest task/seed summary differs from verified source outcome",
    )
    _validate(receipt, schema_path)


def _role(relative: Path) -> str:
    text = relative.as_posix()
    if text.startswith("logs/") and text.endswith(".err"):
        return "stderr_log"
    if text.startswith("logs/") and text.endswith(".out"):
        return "stdout_log"
    if text.endswith("allocated_preflight.json"):
        return "allocated_preflight"
    if "model_snapshot_" in text:
        return "snapshot_attestation"
    if "/submission-" in f"/{text}":
        return "submission_receipt"
    if "/sacct-" in f"/{text}":
        return "scheduler_evidence"
    if "/harvest-" in f"/{text}":
        return "governed_harvest"
    if text.endswith("blinded_scores.json"):
        return "blinded_scores"
    if "/provider_receipts/" in f"/{text}":
        return "provider_receipt"
    if "/raw_outputs/" in f"/{text}":
        return "raw_output"
    if "/resource_receipts/" in f"/{text}":
        return "resource_receipt"
    if text.endswith("result_receipt.json"):
        return "result_receipt"
    if text.endswith("run_manifest.json"):
        return "run_manifest"
    if text.endswith("task_seed_receipt.json"):
        return "task_seed_receipt"
    raise ValueError(f"unclassified source file: {relative}")


def _bundle_members(bundle: Path) -> dict[str, tuple[int, str]]:
    result: dict[str, tuple[int, str]] = {}
    with tarfile.open(bundle, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            _require(
                not member.name.startswith("/") and ".." not in Path(member.name).parts,
                f"unsafe archive member: {member.name}",
            )
            stream = archive.extractfile(member)
            _require(stream is not None, f"unreadable archive member: {member.name}")
            payload = stream.read()
            _require(member.name not in result, f"duplicate archive member: {member.name}")
            result[member.name] = (len(payload), hashlib.sha256(payload).hexdigest())
    return result


def build(*, job_id: str, created_at_utc: str, expected_execution_head: str) -> dict[str, Any]:
    native = V431 / f"native_job_{job_id}"
    run = native / f"runs/v4_3_1/{TASK_ID}-seed-17-job-{job_id}"
    receipt_root = native / "receipts/v4_3_1"
    bundle = V431 / f"native_bundles/PAPER2_V4_3_1_NATIVE_JOB_{job_id}.tar.gz"
    _require(native.is_dir(), f"native directory missing: {native}")
    _require(bundle.is_file(), f"transport bundle missing: {bundle}")
    _require(SCHEMA.is_file(), f"ingest schema missing: {SCHEMA}")
    packet_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PACKET_HEAD_SHA, expected_execution_head],
        cwd=ROOT,
        check=False,
    ).returncode == 0
    _require(packet_ancestor, "packet head is not an ancestor of executed head")

    paths = {
        "submission": receipt_root / f"submission-{job_id}.json",
        "allocated": receipt_root / f"job-{job_id}/allocated_preflight.json",
        "snapshot_pre": receipt_root / f"job-{job_id}/model_snapshot_pre.json",
        "snapshot_post": receipt_root / f"job-{job_id}/model_snapshot_post.json",
        "sacct": receipt_root / f"sacct-{job_id}.json",
        "harvest": receipt_root / f"harvest-{job_id}.json",
        "run_manifest": run / "run_manifest.json",
        "result": run / "result_receipt.json",
        "task_seed": run / "task_seed_receipt.json",
    }
    documents = {name: _load(path) for name, path in paths.items()}
    submission = documents["submission"]
    allocated = documents["allocated"]
    pre = documents["snapshot_pre"]
    post = documents["snapshot_post"]
    sacct = documents["sacct"]
    harvest = documents["harvest"]
    manifest = documents["run_manifest"]
    result = documents["result"]
    task_seed = documents["task_seed"]
    component_schemas = {
        "submission": ROOT / "schemas/paper2-pendulum-submission-receipt-v4-3-1.schema.json",
        "snapshot_pre": ROOT / "schemas/paper2-model-snapshot-attestation-v4.schema.json",
        "snapshot_post": ROOT / "schemas/paper2-model-snapshot-attestation-v4.schema.json",
        "harvest": ROOT / "schemas/paper2-pendulum-native-harvest-receipt-v4-3-1.schema.json",
        "result": ROOT / "schemas/paper2-pendulum-microtrial-result.schema.json",
        "task_seed": ROOT / "schemas/paper2-pendulum-task-seed-receipt-v4-3-1.schema.json",
    }
    for name, schema_path in component_schemas.items():
        _validate(documents[name], schema_path)
    chronology = [
        _utc_timestamp(submission["created_at_utc"], field="submission.created_at_utc"),
        _utc_timestamp(allocated["created_at_utc"], field="allocated.created_at_utc"),
        _utc_timestamp(pre["created_at_utc"], field="snapshot_pre.created_at_utc"),
        _utc_timestamp(post["created_at_utc"], field="snapshot_post.created_at_utc"),
        _utc_timestamp(harvest["created_at_utc"], field="harvest.created_at_utc"),
        _utc_timestamp(created_at_utc, field="ingest.created_at_utc"),
    ]
    _require(chronology == sorted(chronology), "native/ingest chronology is not monotone")
    _require(chronology[-1] <= datetime.now(timezone.utc), "ingest timestamp is in the future")

    _require(submission["slurm_job_id"] == job_id, "submission job mismatch")
    _require(submission["expected_repo_sha"] == expected_execution_head, "submission head mismatch")
    _require(submission["v4_reinterpretation_permitted"] is False, "V4 reinterpretation enabled")
    _require(submission["output_normalization_policy_id"] == POLICY_ID, "submission policy mismatch")
    _require(harvest["slurm_job_id"] == job_id, "harvest job mismatch")
    _require(harvest["verdict"] == "HARVEST_V4_3_1_TASK_SEED_PASS_NONCONFIRMATORY", "harvest did not pass")
    _require(harvest["failures"] == [], "harvest contains failures")
    _require(harvest["v4_reinterpretation_permitted"] is False, "harvest enables V4 reinterpretation")
    _require(harvest["output_normalization_policy_id"] == POLICY_ID, "harvest policy mismatch")

    expected_hash_links = {
        "submission": harvest["submission_receipt"]["sha256"],
        "allocated": harvest["allocated_preflight_receipt"]["sha256"],
        "snapshot_pre": harvest["snapshot_attestations"]["pre_sha256"],
        "snapshot_post": harvest["snapshot_attestations"]["post_sha256"],
        "result": harvest["result_receipt"]["sha256"],
        "run_manifest": harvest["run_manifest"]["sha256"],
    }
    for name, expected in expected_hash_links.items():
        _require(_sha(paths[name]) == expected, f"harvest hash mismatch: {name}")
    _require(task_seed["result_receipt_sha256"] == _sha(paths["result"]), "task/seed result link mismatch")
    _require(task_seed["run_manifest_sha256"] == _sha(paths["run_manifest"]), "task/seed manifest link mismatch")
    _require(task_seed["snapshot_attestations"]["pre_sha256"] == _sha(paths["snapshot_pre"]), "task/seed pre-snapshot mismatch")
    _require(task_seed["snapshot_attestations"]["post_sha256"] == _sha(paths["snapshot_post"]), "task/seed post-snapshot mismatch")
    _require(post["result_receipt_sha256"] == _sha(paths["result"]), "post attestation result mismatch")

    checkout = harvest["execution_checkout"]
    _require(
        checkout
        == result["execution_checkout"]
        == task_seed["execution_checkout"]
        == manifest["execution_checkout"],
        "execution checkout lineage mismatch",
    )
    _require(checkout["clean"] is True and checkout["subject_ancestor"] is True, "execution checkout not clean/ancestral")
    _require(checkout["head_sha"] == expected_execution_head, "executed head differs from expected head")
    for attestation in (pre, post):
        _require(attestation["execution_checkout"]["head_sha"] == checkout["head_sha"], "snapshot head mismatch")
        _require(attestation["execution_checkout"]["tree_sha"] == checkout["tree_sha"], "snapshot tree mismatch")
        _require(attestation["execution_checkout"]["status_entry_count"] == 0, "snapshot checkout dirty")
    _require(pre["phase"] == "PRE_INFERENCE" and post["phase"] == "POST_INFERENCE", "snapshot phase mismatch")
    _require(pre["files"] == post["files"] and len(pre["files"]) == 8, "pre/post snapshot files differ")
    _require(
        pre["snapshot_canonical_sha256"]
        == post["snapshot_canonical_sha256"]
        == task_seed["snapshot_attestations"]["snapshot_canonical_sha256"],
        "snapshot identity mismatch",
    )

    _require(allocated["verdict"] == "PASS" and allocated["blockers"] == [], "allocated preflight did not pass")
    _require(allocated["evaluated_result_record_count"] == 0, "allocated preflight observed results")
    _require(allocated["empirical_claim_permitted"] is False, "allocated preflight granted empirical authority")

    jobs = [row for row in sacct.get("jobs", []) if str(row.get("job_id")) == job_id]
    _require(len(jobs) == 1, "scheduler root row not unique")
    scheduler = jobs[0]
    _require(scheduler == harvest["scheduler_evidence"]["root_row"], "harvest scheduler row mismatch")
    _require(scheduler["name"] == "p2-pend-v431", "scheduler name mismatch")
    _require(scheduler["state"]["current"] == ["COMPLETED"], "scheduler state mismatch")
    _require(scheduler["exit_code"]["status"] == ["SUCCESS"], "scheduler exit status mismatch")
    _require(scheduler["exit_code"]["return_code"]["number"] == 0, "scheduler return code mismatch")

    _require(task_seed["task_id"] == TASK_ID and task_seed["seed"] == 17, "task/seed mismatch")
    _require(task_seed["arm_record_count"] == 2 and task_seed["evaluated_task_seed_unit_count"] == 1, "task/seed counts mismatch")
    _require(task_seed["parse_valid_arm_count"] == 2 and task_seed["scorable_arm_count"] == 2, "task/seed parse counts mismatch")
    _require(task_seed["output_normalization"]["policy_id"] == POLICY_ID, "task/seed policy mismatch")
    _require(task_seed["output_normalization"]["v4_reinterpretation_permitted"] is False, "task/seed enables V4 reinterpretation")
    result_records = {record["condition"]: record for record in result["records"]}
    task_records = {record["condition"]: record for record in task_seed["records"]}
    _require(set(result_records) == set(task_records) == CONDITIONS, "arm set mismatch")
    for condition in CONDITIONS:
        source = result_records[condition]
        index = task_records[condition]
        for key in ("blind_id", "condition", "resource_receipt", "score"):
            _require(source[key] == index[key], f"task/seed arm mismatch: {condition}/{key}")
        _require(source["score"]["parse_valid"] == index["parse_valid"], f"parse flag mismatch: {condition}")
    direct = task_records["DIRECT_CORPUS"]
    rakl = task_records["RAKL_CONTEXT"]
    _require(direct["parse_valid"] is True and isinstance(direct["score"]["score"], dict), "DIRECT_CORPUS must be parse-valid under V4.3.1")
    _require(rakl["parse_valid"] is True and isinstance(rakl["score"]["score"], dict), "RAKL_CONTEXT must be parse-valid under V4.3.1")
    _require(direct["score"]["score"]["exact_conceptual_pass"] is False, "unexpected DIRECT exact conceptual pass")
    _require(rakl["score"]["score"]["exact_conceptual_pass"] is False, "unexpected RAKL exact conceptual pass")
    _require(direct["score"]["score"]["conceptual_correct"] == 1, "unexpected DIRECT conceptual_correct")
    _require(rakl["score"]["score"]["conceptual_correct"] == 3, "unexpected RAKL conceptual_correct")
    _verify_standalone_evidence(
        native=native, run=run, result=result, task_seed=task_seed, job_id=job_id
    )

    v43_ingest = V43 / "PAPER2_V4_3_NATIVE_JOB_3476566_INGEST_RECEIPT_20260811.json"
    v4_negative = _load(v43_ingest)
    _require(
        manifest["bound_artifact_sha256"]["v4_3_direct_parse_parent"] == _sha(v43_ingest),
        "V4.3 DIRECT parse-null parent binding mismatch",
    )
    _require(v4_negative["task_seed_outcome"]["exact_conceptual_pass_arm_count"] == 0, "V4.3 exact-pass history changed")
    _require(v4_negative["task_seed_outcome"]["parse_valid_arm_count"] == 1, "V4.3 parse-null residual changed")
    _require(v4_negative["task_seed_outcome"]["score_comparison_permitted"] is False, "V4.3 comparison enabled")

    source_files = []
    cardinality: dict[str, int] = {}
    member_map: dict[str, tuple[int, str]] = {}
    prefix = f"research/paper2_microtrial_v4_3_1/native_job_{job_id}/"
    for path in sorted(p for p in native.rglob("*") if p.is_file()):
        relative = path.relative_to(native)
        role = _role(relative)
        cardinality[role] = cardinality.get(role, 0) + 1
        item = {
            "role": role,
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha(path),
        }
        source_files.append(item)
        member_map[item["path"].removeprefix(prefix)] = (item["bytes"], item["sha256"])
    _require(len(source_files) == 18, "native source file count is not 18")
    expected_cardinality = {
        "stderr_log": 1,
        "stdout_log": 1,
        "allocated_preflight": 1,
        "snapshot_attestation": 2,
        "submission_receipt": 1,
        "scheduler_evidence": 1,
        "governed_harvest": 1,
        "blinded_scores": 1,
        "provider_receipt": 2,
        "raw_output": 2,
        "resource_receipt": 2,
        "result_receipt": 1,
        "run_manifest": 1,
        "task_seed_receipt": 1,
    }
    _require(cardinality == expected_cardinality, f"source role cardinality mismatch: {cardinality}")
    _require(_bundle_members(bundle) == member_map, "transport bundle differs from copied source files")

    claim_boundary = (
        "Adaptive non-confirmatory engineering evidence only. V4.3.1 job 3476576 "
        "repairs DIRECT schema-envelope serialization so both arms are parse_valid/"
        "scorable (DIRECT 1/5, RAKL_CONTEXT 3/5) with exact_conceptual_pass_arm_count=0 "
        "under the unchanged exact gate on Qwen2.5-1.5B-Instruct. This is not a 1.5B "
        "improvement claim. Parent job 3476566 remains the DIRECT schema-envelope "
        "parse-null residual. No invented passes, no gate softening, no arm win/loss, "
        "paired effect, promotional metric, #138 experience section B authority, "
        "general superiority, independent review, or peer-review claim is permitted."
    )
    receipt = {
        "schema_version": "paper2-v4-3-1-native-ingest-receipt-v1",
        "receipt_id": f"PAPER2_V4_3_1_NATIVE_JOB_{job_id}_INGEST_RECEIPT_20260811",
        "created_at_utc": created_at_utc,
        "verdict": "NATIVE_EXECUTION_CHAIN_PASS__BOTH_ARMS_SCORABLE_NO_EXACT_PASS__SERIALIZATION_REPAIR_STILL_ZERO_EXACT",
        "object": (
            "One native LUNARC execution of the adaptive non-confirmatory V4.3.1 pendulum "
            "task/seed replay under two prompt-materialization arms on Qwen2.5-1.5B-Instruct "
            "(serialization-only repair after V4.3 DIRECT parse-null)."
        ),
        "qoi": (
            "Did the exact receipt chain pass, which frozen V4.3.1 outputs were "
            "parse-valid/scorable, and did any arm achieve exact conceptual success under "
            "the unchanged exact gate?"
        ),
        "ingest_schema": {
            "path": SCHEMA.relative_to(ROOT).as_posix(),
            "sha256": _sha(SCHEMA),
        },
        "source_bundle": {
            "path": bundle.relative_to(ROOT).as_posix(),
            "bytes": bundle.stat().st_size,
            "sha256": _sha(bundle),
        },
        "source_files": source_files,
        "native_execution": {
            "slurm_job_id": job_id,
            "account": scheduler["account"],
            "partition": scheduler["partition"],
            "nodes": scheduler["nodes"],
            "scheduler_state": scheduler["state"]["current"],
            "scheduler_exit_status": scheduler["exit_code"]["status"],
            "scheduler_return_code": scheduler["exit_code"]["return_code"]["number"],
            "scheduler_elapsed_seconds": scheduler["time"]["elapsed"],
            "governed_harvest_verdict": harvest["verdict"],
            "governed_harvest_failures": harvest["failures"],
            "execution_checkout": {
                "clean": checkout["clean"],
                "head_sha": checkout["head_sha"],
                "repo_path": checkout["repo_path"],
                "subject_ancestor": checkout["subject_ancestor"],
                "tree_sha": checkout["tree_sha"],
            },
            "packet_head_sha": PACKET_HEAD_SHA,
            "packet_head_ancestor_of_execution_head": packet_ancestor,
            "packet_parent_sha": harvest["packet_parent_sha"],
            "output_normalization_policy_id": POLICY_ID,
            "v4_reinterpretation_permitted": False,
            "snapshot_file_count": len(pre["files"]),
            "snapshot_canonical_sha256": pre["snapshot_canonical_sha256"],
            "pre_post_snapshot_identity_equal": pre["files"] == post["files"],
            "post_attestation_result_receipt_sha256": post["result_receipt_sha256"],
            "stderr_warning_lines": len(
                (native / f"logs/v4_3_1/p2-pend-v431-{job_id}.err")
                .read_text(encoding="utf-8")
                .splitlines()
            ),
            "stderr_warning": (
                "Transformers reported temperature/top_p/top_k generation flags as invalid "
                "or ignored; retained as execution evidence and not used to grant or deny "
                "score authority."
            ),
        },
        "v4_negative_parent": {
            "path": v43_ingest.relative_to(ROOT).as_posix(),
            "sha256": _sha(v43_ingest),
            "frozen_parse_valid_arm_count": v4_negative["task_seed_outcome"]["parse_valid_arm_count"],
            "frozen_scorable_arm_count": v4_negative["task_seed_outcome"]["scorable_arm_count"],
            "reinterpretation_permitted": False,
        },
        "task_seed_outcome": _summarize_task_seed(task_seed),
        "typed_residual": {
            "residual_id": "PAPER2_V4_3_1_BOTH_ARMS_PARSE_NO_EXACT_PASS_SERIALIZATION_ONLY",
            "root_cause_ladder": ["R1_SCHEMA_PARSER_TRANSFORM", "R7_PROJECTION_FUNCTIONAL_FORM"],
            "observed_signature": (
                "V4.3.1 registered-envelope unwrap repairs DIRECT_CORPUS parse_valid; both arms "
                "are scorable (DIRECT conceptual 1/5, RAKL_CONTEXT 3/5) with "
                "exact_conceptual_pass=false under the unchanged exact gate on "
                "Qwen2.5-1.5B-Instruct. Parent 3476566 remains the DIRECT schema-envelope "
                "parse-null residual."
            ),
            "null_or_competing_explanations": [
                "Serialization repair can restore parse_valid without changing scientific content quality.",
                "Both arms still fail the exact conceptual gate (DIRECT 1/5, RAKL 3/5); 1.5B size alone did not mint exact passes.",
                "One known-answer task and deterministic seed cannot distinguish a systematic architecture effect from task-specific output variance.",
            ],
            "next_discriminator": (
                "NO_1_5B_IMPROVEMENT_CLAIM: both-parse repair is serialization-only; "
                "exact_conceptual_pass remains 0. Do not soften the exact gate. Keep 3476566 as "
                "prior DIRECT parse-null residual. Paper-eligible promotional metrics remain "
                "BLOCKED (sealed microtrial authority only)."
            ),
        },
        "quantitative_figure_generated": False,
        "claim_boundary": claim_boundary,
    }
    verify_ingest_receipt(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--created-at-utc", required=True)
    parser.add_argument("--expected-execution-head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = build(
        job_id=args.job_id,
        created_at_utc=args.created_at_utc,
        expected_execution_head=args.expected_execution_head,
    )
    _validate(receipt, SCHEMA)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "verdict": receipt["verdict"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
