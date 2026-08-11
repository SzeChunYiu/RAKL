from __future__ import annotations

import base64
import hashlib
import json
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator

from rakl.application_feedback import (
    FeedbackImportVerdict,
    import_application_feedback,
    parse_application_feedback_bundle,
    stage_feedback_meta_observation,
)


ROOT = Path(__file__).resolve().parents[1]
IMPORT_ROOT = ROOT / "research/application_feedback/p_vs_np/math_round2_20260811"
BUNDLE_PATH = IMPORT_ROOT / "application-feedback-bundle.json"
RECEIPT_PATH = IMPORT_ROOT / "application-feedback-import-receipt.json"
OBJECT_SNAPSHOT_PATH = IMPORT_ROOT / "producer-object-snapshot.json"
PROVENANCE_PATH = IMPORT_ROOT / "import-provenance.json"
BUNDLE_BYTES_SHA256 = "d02d8b9fca8707eaff6063808150b27ad2c84a69ab91b369e16bd571d1debe25"
RECEIPT_BYTES_SHA256 = "5d50d604ad3be95599a3d6926481057653d696e6878e73825a8a047985929354"
OBJECT_SNAPSHOT_BYTES_SHA256 = "86cb8842d57f17a742460dc32048fd2b9e22e985c06aa4b1998f2cf6703281c0"
PROVENANCE_BYTES_SHA256 = "a35e28cc9b3f74bc6bc6061546351d7143db8c26346d8203a0147414c2819705"
FRAMEWORK_IMPORT_SHA = "f224d91d9fbd2844a89921ca4a30b77a7954ecd2"
FRAMEWORK_IMPORT_TREE_SHA = "8ed91734773262b90c46cc051bfa1faf836113c5"
FRAMEWORK_IMPORT_VERSION = "0.6.6"
MATH_LESSON_IDS = {
    "MATH-METHOD-WITNESS-OPTIMUM-SEPARATION",
    "MATH-METHOD-THEOREM-POLARITY-AUDIT",
    "MATH-METHOD-ROW-LEVEL-DIFFERENCE-WITNESS",
    "MATH-METHOD-SOURCE-NATIVE-STATEMENT-NORMALIZATION",
}


def _run_git(repo: Path, *args: str, input_bytes: bytes | None = None) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_bytes,
        capture_output=True,
        check=True,
    )
    return completed.stdout.decode("utf-8").strip()


def _materialize_exact_producer_object_snapshot(tmp_path: Path) -> Path:
    snapshot = json.loads(OBJECT_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    repo = tmp_path / "RAKL_math-producer"
    repo.mkdir()
    _run_git(repo, "init", "-q")
    _run_git(repo, "remote", "add", "origin", snapshot["producer_repository_url"])
    for record in snapshot["objects"]:
        content = base64.b64decode(record["content_base64"], validate=True)
        observed_oid = _run_git(
            repo,
            "hash-object",
            "-w",
            "-t",
            record["type"],
            "--stdin",
            input_bytes=content,
        )
        assert observed_oid == record["oid"]
    _run_git(repo, "update-ref", "HEAD", snapshot["producer_commit_sha"])
    assert _run_git(repo, "rev-parse", "HEAD^{tree}") == snapshot["producer_tree_sha"]
    return repo


def test_exact_pnp_mathematical_feedback_bundle_imports_only_to_quarantine(
    tmp_path: Path,
) -> None:
    bundle_bytes = BUNDLE_PATH.read_bytes()
    receipt_bytes = RECEIPT_PATH.read_bytes()
    object_snapshot_bytes = OBJECT_SNAPSHOT_PATH.read_bytes()
    provenance_bytes = PROVENANCE_PATH.read_bytes()
    assert hashlib.sha256(bundle_bytes).hexdigest() == BUNDLE_BYTES_SHA256
    assert hashlib.sha256(receipt_bytes).hexdigest() == RECEIPT_BYTES_SHA256
    assert hashlib.sha256(object_snapshot_bytes).hexdigest() == OBJECT_SNAPSHOT_BYTES_SHA256
    assert hashlib.sha256(provenance_bytes).hexdigest() == PROVENANCE_BYTES_SHA256

    document = json.loads(bundle_bytes)
    stored_receipt = json.loads(receipt_bytes)
    provenance = json.loads(provenance_bytes)
    source_repo = _materialize_exact_producer_object_snapshot(tmp_path)

    imported = import_application_feedback(
        document,
        source_repository=source_repo,
        current_framework_commit_sha=FRAMEWORK_IMPORT_SHA,
        current_framework_version=FRAMEWORK_IMPORT_VERSION,
    )
    assert document["framework_requirement"]["commit_sha"] == FRAMEWORK_IMPORT_SHA
    assert document["framework_requirement"]["version"] == FRAMEWORK_IMPORT_VERSION
    assert provenance["framework_import_subject"]["commit_sha"] == FRAMEWORK_IMPORT_SHA
    assert provenance["framework_import_subject"]["tree_sha"] == FRAMEWORK_IMPORT_TREE_SHA
    assert provenance["framework_import_subject"]["version"] == FRAMEWORK_IMPORT_VERSION
    assert imported.to_dict() == stored_receipt
    assert imported.verdict is FeedbackImportVerdict.QUARANTINED_PROPOSAL
    assert imported.effective_authority == "HEURISTIC"
    assert imported.inventory_mutation_performed is False
    assert imported.failure_lattice_mutation_performed is False
    assert imported.grants_scientific_authority is False
    assert imported.grants_method_promotion is False

    latest_revalidation = provenance["framework_latest_main_revalidation"]
    current_main_attempt = import_application_feedback(
        document,
        source_repository=source_repo,
        current_framework_commit_sha=latest_revalidation["commit_sha"],
        current_framework_version=document["framework_requirement"]["version"],
    )
    assert current_main_attempt.verdict is FeedbackImportVerdict.CANNOT_CHECK
    assert "framework_commit_pin_stale" in current_main_attempt.reasons
    assert latest_revalidation["interpretation"].startswith(
        "Historical exact-f224 quarantine receipt only"
    )

    for schema_name, instance in (
        ("application-feedback-bundle.schema.json", document),
        ("application-feedback-import-receipt.schema.json", stored_receipt),
    ):
        schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert list(Draft202012Validator(schema).iter_errors(instance)) == []

    assert provenance["source_main_fetch"]["commit_sha"] == (
        "350861b1c2755033893068e5519b8b06a6315aa6"
    )
    assert provenance["transport"]["preserved_bytes_sha256"] == BUNDLE_BYTES_SHA256
    assert provenance["transport"]["git_blob_sha"] == (
        "1db5b38871df4bf146bb9a9fce76fe1b90ee59a6"
    )
    assert provenance["transport"]["delivery_merge_commit_sha"] == (
        "696da1ba2f17c7d1859e96338fb98d489c3311c7"
    )
    assert provenance["producer_pin"]["commit_sha"] == document["producer"]["commit_sha"]
    assert provenance["producer_pin"]["tree_sha"] == document["producer"]["tree_sha"]

    bundle = parse_application_feedback_bundle(document)
    assert len(bundle.items) == 1
    staged = stage_feedback_meta_observation(bundle, imported, bundle.items[0].item_id)
    assert staged["validation_status"] == "UNVALIDATED_PROPOSAL"
    assert staged["import_state"] == "QUARANTINED_PROPOSAL"
    assert staged["grants_method_promotion"] is False
    assert {row["lesson_id"] for row in staged["mathematical_lessons"]} == MATH_LESSON_IDS
    assert staged["excluded_nonmathematical_observations"] == [
        "HTTP access status",
        "Git branch movement",
        "CI execution",
        "artifact hashing",
        "timestamp chronology",
        "framework pin synchronization",
    ]
    assert staged["root_status"] == "OPEN_PROBLEM / NO_SOLUTION_CERTIFICATE"
    assert all(
        value is False
        for key, value in staged["authority_contract"].items()
        if key.startswith("grants_")
    )
