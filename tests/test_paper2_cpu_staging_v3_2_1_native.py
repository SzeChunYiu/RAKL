from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat
import copy

import pytest

import rakl.paper2_cpu_staging_v3_2 as frozen


ROOT = Path(__file__).resolve().parents[1]
NATIVE_BOOTSTRAP = ROOT / "research/paper2_microtrial_v3/native_receipts/BOOTSTRAP_NATIVE_V3_2_1_3DB76E3.json"
NATIVE_HARVEST = ROOT / "research/paper2_microtrial_v3/native_receipts/HARVEST_PASS_NATIVE_V3_2_1_JOBS_3475123_3475124.json"
PRIOR_HARVEST = ROOT / "research/paper2_microtrial_v3/native_receipts/HARVEST_CANNOT_CHECK_NATIVE_V3_2_JOBS_3475123_3475124.json"
CONTRACT = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_HARVEST_REPAIR_CONTRACT_V3_2_1.json"
SYNTHESIS = ROOT / "research/paper2_microtrial_v3/PAPER2_NATIVE_V3_2_1_HARVEST_PASS_RECEIPT_20260811.json"
CHRONOLOGY = ROOT / "research/paper2_microtrial_v3/PAPER2_V3_2_1_PRE_REHARVEST_CHRONOLOGY_DISCREPANCY_20260811.json"
INTERNAL_REVIEW = ROOT / "research/paper2_microtrial_v3/PAPER2_NATIVE_V3_2_1_HARVEST_PASS_INTERNAL_REVIEW_20260811.json"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate(path: Path, schema_path: Path) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator(
        _load(schema_path), format_checker=jsonschema.FormatChecker()
    ).validate(_load(path))


def test_native_bootstrap_is_exact_clean_distinct_repair_checkout() -> None:
    receipt = _load(NATIVE_BOOTSTRAP)
    assert _sha(NATIVE_BOOTSTRAP) == "e9285276c28718ea7fac60fba4cbe358d554377bccc99f49aad1ab225d9302f6"
    assert receipt["verdict"] == "BOOTSTRAP_PASS_ATOMICALLY_PROMOTED"
    assert receipt["expected_repo_sha"] == "3db76e37c6e8a72fad32a38bc28aef2f093a5152"
    assert receipt["observed_repo_sha"] == receipt["expected_repo_sha"]
    assert receipt["observed_repo_tree"] == "80e961f4db739914b773c999034ae3ea1d7f6733"
    assert receipt["checkout_clean"] is True
    assert receipt["detached_head"] is True
    assert receipt["jobs_submitted"] == 0
    assert receipt["model_execution_performed"] is False
    assert receipt["evaluated_result_record_count"] == 0


def test_native_v3_2_1_harvest_pass_is_exact_and_schema_valid() -> None:
    receipt = _load(NATIVE_HARVEST)
    assert _sha(NATIVE_HARVEST) == "8dc6207f771943cc4597ba2504e11e886e55af9ae1901b131100f6baf439824a"
    assert receipt["verdict"] == "HARVEST_STAGING_PASS"
    assert receipt["failures"] == []
    assert receipt["job_ids"] == ["3475123", "3475124"]
    assert receipt["jobs_submitted_by_repair"] == 0
    assert receipt["model_execution_performed"] is False
    assert receipt["evaluated_result_record_count"] == 0
    assert receipt["source_repository_sha"] == "c10ba7a261af02cc42690022226555a3197351ae"
    assert receipt["source_repository_tree"] == "4f8053958d9ed4ea6e506ffa6dc8e60ee36715a5"
    assert receipt["repair_repository_sha"] == "3db76e37c6e8a72fad32a38bc28aef2f093a5152"
    assert receipt["prior_harvest_receipt_sha256"] == _sha(PRIOR_HARVEST)
    assert receipt["prior_negative_history_preserved"] is True
    _validate(
        NATIVE_HARVEST,
        ROOT / "schemas/paper2-cpu-staging-harvest-receipt-v3-2-1.schema.json",
    )


def test_native_contract_canonical_identity_and_prior_negative_history() -> None:
    contract = _load(CONTRACT)
    receipt = _load(NATIVE_HARVEST)
    assert frozen._canonical_sha256(contract) == receipt["repair_contract_canonical_sha256"]
    assert _sha(PRIOR_HARVEST) == "2e2ecd6f5cb2ad84f17352fea598b30210de225f745e1d9c13154b8872a03e96"
    assert _load(PRIOR_HARVEST)["verdict"] == "HARVEST_CANNOT_CHECK"
    assert _load(PRIOR_HARVEST)["failures"] == ["staging_job_or_receipt_failed"]


def test_post_harvest_synthesis_is_exact_source_derived_and_schema_valid() -> None:
    receipt = _load(SYNTHESIS)
    declared_harvest = ROOT / receipt["native_harvest"]["path"]
    declared_bootstrap = ROOT / receipt["repair_checkout_bootstrap"]["path"]
    assert declared_harvest == NATIVE_HARVEST
    assert declared_bootstrap == NATIVE_BOOTSTRAP
    assert receipt["native_harvest"]["sha256"] == _sha(declared_harvest)
    assert receipt["repair_checkout_bootstrap"]["sha256"] == _sha(declared_bootstrap)
    assert receipt["negative_history"]["v3_2_harvest_cannot_check_sha256"] == _sha(PRIOR_HARVEST)
    submissions = receipt["cumulative_source_submissions"]
    for item in submissions:
        source = ROOT / item["path"]
        observed = _load(source)
        assert _sha(source) == item["sha256"]
        assert observed["submitted_job_ids"] == item["job_ids"]
        assert int(observed["model_execution_performed"]) == item["model_executions"]
        assert observed["evaluated_result_record_count"] == item["evaluated_result_records"]
    assert receipt["cumulative_native_staging_counts"] == {
        "jobs_submitted": sum(len(item["job_ids"]) for item in submissions),
        "model_executions": sum(item["model_executions"] for item in submissions),
        "evaluated_result_records": sum(
            item["evaluated_result_records"] for item in submissions
        ),
    }
    pre = receipt["pre_reharvest_synthesis_binding"]
    assert _sha(ROOT / pre["path"]) == pre["sha256"]
    assert receipt["quantitative_figure_generated"] is False
    schema_path = ROOT / receipt["schema_binding"]["path"]
    assert receipt["schema_binding"]["sha256"] == _sha(schema_path)
    _validate(SYNTHESIS, schema_path)


def test_pre_reharvest_chronology_metadata_error_is_preserved_and_corrected() -> None:
    receipt = _load(CHRONOLOGY)
    for item in receipt["affected_artifacts"]:
        source = ROOT / item["path"]
        assert _sha(source) == item["sha256"]
        assert _load(source)["created_at_utc"] == item["recorded_created_at_utc"]
    assert receipt["git_freeze"]["candidate_committed_at_utc"] == "2026-08-11T02:25:24Z"
    assert receipt["native_harvest_created_at_utc"] == "2026-08-11T02:31:55Z"
    assert receipt["chronology_result"] == (
        "EXACT_ARTIFACT_BYTES_FROZEN_BEFORE_NATIVE_RESULT__CREATED_AT_FIELDS_INVALID"
    )
    _validate(
        CHRONOLOGY,
        ROOT / "schemas/paper2-v3-2-1-pre-reharvest-chronology-discrepancy.schema.json",
    )


def test_wrapper_mode_fix_candidate_is_executable_without_content_change() -> None:
    wrapper = ROOT / "experiments/paper2/lunarc/harvest_cpu_staging_v3_2_1.sh"
    mode = stat.S_IMODE(wrapper.stat().st_mode)
    assert mode == 0o755
    contract = _load(CONTRACT)
    binding = next(item for item in contract["bindings"] if item["role"] == "harvest_repair_script")
    assert binding["sha256"] == _sha(wrapper)


def test_post_harvest_internal_review_is_exactly_bound_and_schema_valid() -> None:
    review = _load(INTERNAL_REVIEW)
    assert review["blocking_concerns"] == []
    assert review["verdict"] == "PASS__NATIVE_HARVEST_STAGING_PASS__EXECUTION_PACKET_NOT_YET_FROZEN"
    for item in review["reviewed_artifacts"]:
        assert _sha(ROOT / item["path"]) == item["sha256"]
    schema_path = ROOT / review["schema_binding"]["path"]
    assert _sha(schema_path) == review["schema_binding"]["sha256"]
    _validate(INTERNAL_REVIEW, schema_path)


def test_post_result_schemas_reject_path_count_and_review_mutations() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    synthesis = _load(SYNTHESIS)
    synthesis_schema = _load(ROOT / synthesis["schema_binding"]["path"])
    validator = jsonschema.Draft202012Validator(synthesis_schema)
    mutations = []
    changed = copy.deepcopy(synthesis)
    changed["native_harvest"]["path"] = "research/nonexistent.json"
    mutations.append(changed)
    changed = copy.deepcopy(synthesis)
    changed["native_harvest"]["failures"] = "not-an-array"
    mutations.append(changed)
    changed = copy.deepcopy(synthesis)
    changed["cumulative_source_submissions"][0]["job_ids"] = ["999", "998"]
    mutations.append(changed)
    for mutation in mutations:
        assert list(validator.iter_errors(mutation))

    review = _load(INTERNAL_REVIEW)
    review_schema = _load(ROOT / review["schema_binding"]["path"])
    review_validator = jsonschema.Draft202012Validator(review_schema)
    duplicate = copy.deepcopy(review)
    duplicate["reviewed_artifacts"] = [
        duplicate["reviewed_artifacts"][0]
        for _ in duplicate["reviewed_artifacts"]
    ]
    inverted = copy.deepcopy(review)
    inverted["passes"] = list(reversed(inverted["passes"]))
    duplicated_concern = copy.deepcopy(review)
    duplicated_concern["concern_ledger"][1] = duplicated_concern["concern_ledger"][0]
    for mutation in (duplicate, inverted, duplicated_concern):
        assert list(review_validator.iter_errors(mutation))
