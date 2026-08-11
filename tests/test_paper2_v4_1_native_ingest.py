from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

import pytest

from rakl.failure_lattice import (
    FailureDiagnosisStatus,
    FailureExperience,
    FailureExperienceLattice,
    FailureLink,
    FailureRelation,
    add_failure_experience,
    add_failure_link,
    global_failure_portrait,
)
from rakl.research_trace import (
    MathResearchTrace,
    ResearchTraceEntry,
    ResearchTraceEventType,
    TraceGateVerdict,
    audit_research_trace,
)


jsonschema = pytest.importorskip("jsonschema")

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "research/paper2_microtrial_v4"
V41 = ROOT / "research/paper2_microtrial_v4_1"
NATIVE = V41 / "native_job_3475212"
RUN = NATIVE / "runs/v4_1/PENDULUM_SEALED_KNOWN_ANSWER_001-seed-17-job-3475212"
INGEST = V41 / "PAPER2_V4_1_NATIVE_JOB_3475212_INGEST_RECEIPT_20260811.json"
SCHEMA = ROOT / "schemas/paper2-v4-1-native-ingest-receipt.schema.json"
BUNDLE = V41 / "native_bundles/PAPER2_V4_1_NATIVE_JOB_3475212.tar.gz"
BUILDER = ROOT / "experiments/paper2/lunarc/build_native_ingest_receipt_v4_1.py"
FAILURE_TRACE = V41 / "PAPER2_V4_V4_1_PUBLIC_FAILURE_TRACE_20260811.json"
FAILURE_LATTICE = V41 / "PAPER2_V4_V4_1_FAILURE_EXPERIENCE_LATTICE_20260811.json"

SPEC = importlib.util.spec_from_file_location("paper2_v41_native_ingest", BUILDER)
assert SPEC is not None and SPEC.loader is not None
BUILDER_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER_MODULE)


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _validator(schema: Path) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        _load(schema), format_checker=jsonschema.FormatChecker()
    )


def test_v4_1_native_ingest_schema_and_every_copied_byte_are_bound() -> None:
    receipt = _load(INGEST)
    _validator(SCHEMA).validate(receipt)
    assert _sha(SCHEMA) == receipt["ingest_schema"]["sha256"]
    assert receipt["source_bundle"] == {
        "bytes": BUNDLE.stat().st_size,
        "path": BUNDLE.relative_to(ROOT).as_posix(),
        "sha256": _sha(BUNDLE),
    }
    assert len(receipt["source_files"]) == 18
    assert len({item["path"] for item in receipt["source_files"]}) == 18
    for item in receipt["source_files"]:
        path = ROOT / item["path"]
        assert path.stat().st_size == item["bytes"]
        assert _sha(path) == item["sha256"]

    prefix = "research/paper2_microtrial_v4_1/native_job_3475212/"
    copied = {
        item["path"].removeprefix(prefix): (item["bytes"], item["sha256"])
        for item in receipt["source_files"]
    }
    with tarfile.open(BUNDLE, "r:gz") as archive:
        archived = {
            member.name: (
                member.size,
                hashlib.sha256(archive.extractfile(member).read()).hexdigest(),
            )
            for member in archive.getmembers()
            if member.isfile()
        }
    assert archived == copied


def test_v4_1_native_component_receipts_validate_under_frozen_schemas() -> None:
    pairs = (
        (
            NATIVE / "receipts/v4_1/submission-3475212.json",
            ROOT / "schemas/paper2-pendulum-submission-receipt-v4-1.schema.json",
        ),
        (
            NATIVE / "receipts/v4_1/harvest-3475212.json",
            ROOT / "schemas/paper2-pendulum-native-harvest-receipt-v4-1.schema.json",
        ),
        (
            NATIVE / "receipts/v4_1/job-3475212/model_snapshot_pre.json",
            ROOT / "schemas/paper2-model-snapshot-attestation-v4.schema.json",
        ),
        (
            NATIVE / "receipts/v4_1/job-3475212/model_snapshot_post.json",
            ROOT / "schemas/paper2-model-snapshot-attestation-v4.schema.json",
        ),
        (
            RUN / "task_seed_receipt.json",
            ROOT / "schemas/paper2-pendulum-task-seed-receipt-v4-1.schema.json",
        ),
        (
            RUN / "result_receipt.json",
            ROOT / "schemas/paper2-pendulum-microtrial-result.schema.json",
        ),
    )
    for document, schema in pairs:
        _validator(schema).validate(_load(document))


def test_v4_1_native_builder_reproduces_the_exact_ingest(tmp_path: Path) -> None:
    output = tmp_path / "ingest.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--job-id",
            "3475212",
            "--created-at-utc",
            "2026-08-11T05:35:00Z",
            "--expected-execution-head",
            "4a8d5ff19e3e6b26b95cb7408bbf55475208989c",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "native ingest builder failed\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    assert output.read_bytes() == INGEST.read_bytes()


@pytest.mark.parametrize("created_at", ("2000-01-01T00:00:00Z", "not-a-timestamp"))
def test_v4_1_native_builder_rejects_impossible_ingest_chronology(
    tmp_path: Path, created_at: str
) -> None:
    output = tmp_path / "impossible.json"
    completed = subprocess.run(
        [
            "python",
            str(BUILDER),
            "--job-id",
            "3475212",
            "--created-at-utc",
            created_at,
            "--expected-execution-head",
            "4a8d5ff19e3e6b26b95cb7408bbf55475208989c",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert not output.exists()


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value["source_files"][0].__setitem__("sha256", "0" * 64),
        lambda value: value["source_files"][0].__setitem__(
            "bytes", value["source_files"][0]["bytes"] + 1
        ),
        lambda value: value["source_bundle"].__setitem__("sha256", "0" * 64),
        lambda value: value["ingest_schema"].__setitem__("sha256", "0" * 64),
        lambda value: value["native_execution"].__setitem__(
            "post_attestation_result_receipt_sha256", "0" * 64
        ),
        lambda value: value["native_execution"].__setitem__(
            "snapshot_canonical_sha256", "0" * 64
        ),
    ),
)
def test_executable_ingest_verifier_rejects_external_lineage_mutations(mutation) -> None:
    receipt = deepcopy(_load(INGEST))
    mutation(receipt)
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        BUILDER_MODULE.verify_ingest_receipt(receipt)


@pytest.mark.parametrize("target", ("raw", "resource", "score", "stderr"))
def test_standalone_semantic_verifier_rejects_planted_byte_changes(
    tmp_path: Path, target: str
) -> None:
    native = tmp_path / "native"
    shutil.copytree(NATIVE, native)
    run = native / "runs/v4_1/PENDULUM_SEALED_KNOWN_ANSWER_001-seed-17-job-3475212"
    if target == "raw":
        path = run / "raw_outputs/BLIND_3C791A.json"
        value = _load(path)
        value["raw_text"] += " "
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif target == "resource":
        path = run / "resource_receipts/BLIND_3C791A.json"
        value = _load(path)
        value["input_tokens"] += 1
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif target == "score":
        path = run / "blinded_scores.json"
        value = _load(path)
        value["scores"][0]["score"]["conceptual_correct"] = 4
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        path = native / "logs/v4_1/p2-pend-v4-1-3475212.err"
        path.write_text(path.read_text(encoding="utf-8") + "planted\n", encoding="utf-8")

    with pytest.raises(ValueError):
        BUILDER_MODULE._verify_standalone_evidence(
            native=native,
            run=run,
            result=_load(run / "result_receipt.json"),
            task_seed=_load(run / "task_seed_receipt.json"),
            job_id="3475212",
        )


@pytest.mark.parametrize("target", ("raw", "resource", "score", "stderr"))
def test_public_verifier_rejects_consistently_rehashed_semantic_attack(
    tmp_path: Path, target: str
) -> None:
    root = tmp_path / "repo"
    schema_copy = root / SCHEMA.relative_to(ROOT)
    schema_copy.parent.mkdir(parents=True)
    shutil.copyfile(SCHEMA, schema_copy)
    v4_parent = V4 / "PAPER2_V4_NATIVE_JOB_3475193_INGEST_RECEIPT_20260811.json"
    v4_copy = root / v4_parent.relative_to(ROOT)
    v4_copy.parent.mkdir(parents=True)
    shutil.copyfile(v4_parent, v4_copy)
    native = root / NATIVE.relative_to(ROOT)
    shutil.copytree(NATIVE, native)
    bundle = root / BUNDLE.relative_to(ROOT)
    bundle.parent.mkdir(parents=True)
    shutil.copyfile(BUNDLE, bundle)

    run = native / "runs/v4_1/PENDULUM_SEALED_KNOWN_ANSWER_001-seed-17-job-3475212"
    if target == "raw":
        changed = run / "raw_outputs/BLIND_3C791A.json"
        value = _load(changed)
        value["raw_text"] += " "
        changed.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif target == "resource":
        changed = run / "resource_receipts/BLIND_3C791A.json"
        value = _load(changed)
        value["input_tokens"] += 1
        changed.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif target == "score":
        changed = run / "blinded_scores.json"
        value = _load(changed)
        value["scores"][0]["score"]["conceptual_correct"] = 4
        changed.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        changed = native / "logs/v4_1/p2-pend-v4-1-3475212.err"
        changed.write_text(changed.read_text(encoding="utf-8") + "planted\n", encoding="utf-8")

    receipt = deepcopy(_load(INGEST))
    changed_repo_path = changed.relative_to(root).as_posix()
    item = next(row for row in receipt["source_files"] if row["path"] == changed_repo_path)
    item["bytes"] = changed.stat().st_size
    item["sha256"] = _sha(changed)
    with tarfile.open(bundle, "w:gz") as archive:
        for path in sorted(value for value in native.rglob("*") if value.is_file()):
            archive.add(path, arcname=path.relative_to(native).as_posix(), recursive=False)
    receipt["source_bundle"]["bytes"] = bundle.stat().st_size
    receipt["source_bundle"]["sha256"] = _sha(bundle)

    with pytest.raises(ValueError):
        BUILDER_MODULE.verify_ingest_receipt(receipt, root=root)


def test_public_verifier_rejects_full_chain_score_summary_divergence(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    schema_copy = root / SCHEMA.relative_to(ROOT)
    schema_copy.parent.mkdir(parents=True)
    shutil.copyfile(SCHEMA, schema_copy)
    v4_parent = V4 / "PAPER2_V4_NATIVE_JOB_3475193_INGEST_RECEIPT_20260811.json"
    v4_copy = root / v4_parent.relative_to(ROOT)
    v4_copy.parent.mkdir(parents=True)
    shutil.copyfile(v4_parent, v4_copy)
    native = root / NATIVE.relative_to(ROOT)
    shutil.copytree(NATIVE, native)
    bundle = root / BUNDLE.relative_to(ROOT)
    bundle.parent.mkdir(parents=True)
    shutil.copyfile(BUNDLE, bundle)
    run = native / "runs/v4_1/PENDULUM_SEALED_KNOWN_ANSWER_001-seed-17-job-3475212"

    result_path = run / "result_receipt.json"
    result = _load(result_path)
    result_rakl = next(row for row in result["records"] if row["condition"] == "RAKL_CONTEXT")
    result_rakl["score"]["score"]["conceptual_correct"] = 4
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result_sha = _sha(result_path)

    post_path = native / "receipts/v4_1/job-3475212/model_snapshot_post.json"
    post = _load(post_path)
    post["result_receipt_sha256"] = result_sha
    post_path.write_text(json.dumps(post, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    post_sha = _sha(post_path)

    task_path = run / "task_seed_receipt.json"
    task = _load(task_path)
    task_rakl = next(row for row in task["records"] if row["condition"] == "RAKL_CONTEXT")
    task_rakl["score"]["score"]["conceptual_correct"] = 4
    task["result_receipt_sha256"] = result_sha
    task["snapshot_attestations"]["post_sha256"] = post_sha
    task_path.write_text(json.dumps(task, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    task_sha = _sha(task_path)

    blinded_path = run / "blinded_scores.json"
    blinded = _load(blinded_path)
    blinded_rakl = next(row for row in blinded["scores"] if row["blind_id"] == "BLIND_3C791A")
    blinded_rakl["score"]["conceptual_correct"] = 4
    blinded_path.write_text(
        json.dumps(blinded, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    harvest_path = native / "receipts/v4_1/harvest-3475212.json"
    harvest = _load(harvest_path)
    harvest["result_receipt"]["sha256"] = result_sha
    harvest["snapshot_attestations"]["post_sha256"] = post_sha
    harvest["task_seed_receipt"]["sha256"] = task_sha
    harvest_path.write_text(
        json.dumps(harvest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    stdout_path = native / "logs/v4_1/p2-pend-v4-1-3475212.out"
    stdout = stdout_path.read_text(encoding="utf-8")
    original = _load(INGEST)
    stdout = stdout.replace(
        original["native_execution"]["post_attestation_result_receipt_sha256"],
        result_sha,
    )
    old_post = next(
        row["sha256"]
        for row in original["source_files"]
        if row["path"].endswith("model_snapshot_post.json")
    )
    old_task = next(
        row["sha256"]
        for row in original["source_files"]
        if row["path"].endswith("task_seed_receipt.json")
    )
    stdout = stdout.replace(old_post, post_sha).replace(old_task, task_sha)
    stdout_path.write_text(stdout, encoding="utf-8")

    receipt = deepcopy(original)
    receipt["native_execution"]["post_attestation_result_receipt_sha256"] = result_sha
    changed = (
        result_path,
        post_path,
        task_path,
        blinded_path,
        harvest_path,
        stdout_path,
    )
    entries = {row["path"]: row for row in receipt["source_files"]}
    for path in changed:
        item = entries[path.relative_to(root).as_posix()]
        item["bytes"] = path.stat().st_size
        item["sha256"] = _sha(path)
    with tarfile.open(bundle, "w:gz") as archive:
        for path in sorted(value for value in native.rglob("*") if value.is_file()):
            archive.add(path, arcname=path.relative_to(native).as_posix(), recursive=False)
    receipt["source_bundle"]["bytes"] = bundle.stat().st_size
    receipt["source_bundle"]["sha256"] = _sha(bundle)

    with pytest.raises(ValueError, match="summary differs"):
        BUILDER_MODULE.verify_ingest_receipt(receipt, root=root)


@pytest.mark.parametrize("job_id", ["3475212", "3476520", "3476521", "3476524"])
def test_v4_1_tip_job_ingest_receipts_verify_against_committed_bundles(
    job_id: str,
) -> None:
    """Tip-job transport bundles must stay byte-exact with their ingest receipts.

    #192 landed tip ingest receipts whose source_bundle SHA/size must match the
    committed tar.gz files; a mismatched materialized tarball must fail closed.
    """
    receipt_path = V41 / f"PAPER2_V4_1_NATIVE_JOB_{job_id}_INGEST_RECEIPT_20260811.json"
    receipt = _load(receipt_path)
    _validator(SCHEMA).validate(receipt)
    BUILDER_MODULE.verify_ingest_receipt(receipt, root=ROOT)
    assert receipt["native_execution"]["slurm_job_id"] == job_id
    assert receipt["native_execution"]["governed_harvest_verdict"] == (
        "HARVEST_V4_1_TASK_SEED_PASS_NONCONFIRMATORY"
    )
    assert receipt["verdict"] == (
        "NATIVE_EXECUTION_CHAIN_PASS__ONE_ARM_SCORABLE_NO_EXACT_PASS__"
        "COMPARISON_NOT_ESTIMABLE"
    )
    assert receipt["task_seed_outcome"]["exact_conceptual_pass_arm_count"] == 0
    assert receipt["task_seed_outcome"]["valid_scientific_success_arm_count"] == 0
    assert receipt["quantitative_figure_generated"] is False


def test_v4_1_scheduler_checkout_snapshot_and_hash_lineage_pass() -> None:
    receipt = _load(INGEST)
    native = receipt["native_execution"]
    assert native["slurm_job_id"] == "3475212"
    assert native["scheduler_state"] == ["COMPLETED"]
    assert native["scheduler_exit_status"] == ["SUCCESS"]
    assert native["scheduler_return_code"] == 0
    assert native["scheduler_elapsed_seconds"] == 54
    assert native["governed_harvest_verdict"] == (
        "HARVEST_V4_1_TASK_SEED_PASS_NONCONFIRMATORY"
    )
    assert native["execution_checkout"] == {
        "clean": True,
        "head_sha": "4a8d5ff19e3e6b26b95cb7408bbf55475208989c",
        "repo_path": "/projects/hep/fs9/users/scyiu/RAKL-paper2/repo",
        "subject_ancestor": True,
        "tree_sha": "1ba49edbf23d46fcc8105f96d0dc45c286c3a9c5",
    }
    assert native["packet_head_sha"] == "f3211f86d1b7665e44cfa08fa4ec6e257d77c9eb"
    assert native["packet_head_ancestor_of_execution_head"] is True
    assert native["snapshot_file_count"] == 8
    assert native["pre_post_snapshot_identity_equal"] is True
    assert native["post_attestation_result_receipt_sha256"] == _sha(
        RUN / "result_receipt.json"
    )
    assert _sha(NATIVE / "receipts/v4_1/submission-3475212.json") == (
        "186a71d0620ca886b5cde6e8eb466c3fdc48c5c4cf4af7704cf02c3a24cc3a90"
    )
    assert _sha(NATIVE / "receipts/v4_1/sacct-3475212.json") == (
        "6a47f867ecf8fabe5b26ff52a4fcb83640d16e17f7c574f95d97ecf740d33a6e"
    )
    assert _sha(NATIVE / "receipts/v4_1/harvest-3475212.json") == (
        "f4836e3623b321fb8012625c99df22992a47547853211cb141096b19d92e634f"
    )


def test_v4_1_partial_parse_pass_has_no_comparative_or_success_authority() -> None:
    receipt = _load(INGEST)
    assert receipt["verdict"] == (
        "NATIVE_EXECUTION_CHAIN_PASS__ONE_ARM_SCORABLE_NO_EXACT_PASS__"
        "COMPARISON_NOT_ESTIMABLE"
    )
    outcome = receipt["task_seed_outcome"]
    assert outcome["parse_valid_arm_count"] == outcome["scorable_arm_count"] == 1
    assert outcome["exact_conceptual_pass_arm_count"] == 0
    assert outcome["valid_scientific_success_arm_count"] == 0
    assert outcome["arm_comparison_estimable"] is False
    assert outcome["score_comparison_permitted"] is False
    assert outcome["fully_costed_cost_per_success_estimable"] is False
    assert outcome["fully_costed"] is False
    records = {record["condition"]: record for record in outcome["records"]}
    assert records["DIRECT_CORPUS"]["parse_valid"] is False
    assert records["DIRECT_CORPUS"]["score"] is None
    assert records["RAKL_CONTEXT"]["parse_valid"] is True
    assert records["RAKL_CONTEXT"]["score"]["conceptual_correct"] == 3
    assert records["RAKL_CONTEXT"]["score"]["conceptual_total"] == 5
    assert records["RAKL_CONTEXT"]["score"]["exact_conceptual_pass"] is False
    assert {record["token_count_per_valid_scientific_success"] for record in records.values()} == {
        "INFINITE"
    }
    assert records["DIRECT_CORPUS"]["token_count"] == 958
    assert records["RAKL_CONTEXT"]["token_count"] == 1248
    assert receipt["quantitative_figure_generated"] is False


def test_v4_negative_parent_remains_byte_exact_and_unscorable() -> None:
    parent = V4 / "PAPER2_V4_NATIVE_JOB_3475193_INGEST_RECEIPT_20260811.json"
    assert _sha(parent) == "cb73e662832f913264b999140443d061bdcd18e07d725aaf9da16362397abd48"
    receipt = _load(INGEST)
    assert receipt["v4_negative_parent"] == {
        "frozen_parse_valid_arm_count": 0,
        "frozen_scorable_arm_count": 0,
        "path": parent.relative_to(ROOT).as_posix(),
        "reinterpretation_permitted": False,
        "sha256": _sha(parent),
    }


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value["task_seed_outcome"].__setitem__(
            "score_comparison_permitted", True
        ),
        lambda value: value["task_seed_outcome"].__setitem__(
            "exact_conceptual_pass_arm_count", 1
        ),
        lambda value: value["task_seed_outcome"]["records"][0].__setitem__(
            "score", {}
        ),
        lambda value: value["v4_negative_parent"].__setitem__(
            "reinterpretation_permitted", True
        ),
        lambda value: value.__setitem__("quantitative_figure_generated", True),
        lambda value: value.__setitem__("source_files", value["source_files"][:-1]),
        lambda value: value["source_files"].__setitem__(1, value["source_files"][0]),
        lambda value: value.__setitem__("verdict", "RAKL_WINS"),
    ),
)
def test_v4_1_ingest_schema_rejects_authority_and_lineage_mutations(mutation) -> None:
    receipt = deepcopy(_load(INGEST))
    mutation(receipt)
    with pytest.raises(jsonschema.ValidationError):
        _validator(SCHEMA).validate(receipt)


def test_manuscript_and_status_preserve_the_nonconfirmatory_null_boundary() -> None:
    manuscript = (
        ROOT
        / "paper/saturated_epistemic_mechanics/source/sections/13c_empirical_reporting_contract.tex"
    ).read_text(encoding="utf-8")
    status = (ROOT / "research/PAPER2_V4_1_LUNARC_PACKET_STATUS_20260811.md").read_text(
        encoding="utf-8"
    )
    for text in (manuscript, status):
        assert "3475212" in text
        assert "3 of 5" in text
        assert "zero exact conceptual passes" in text
        assert "No quantitative figure" in text
    assert "full matched empirical claim remains open" in manuscript
    assert "V4 job `3475193` remains two parse-invalid nulls" in status


def test_recursive_internal_review_binds_subjects_and_closes_only_internal_blockers() -> None:
    review = _load(V41 / "PAPER2_V4_1_NATIVE_INTERNAL_REVIEW_20260811.json")
    assert review["review_class"] == (
        "recursive_same_context_and_isolated_same_project_internal_not_independent"
    )
    assert review["blocking_concerns"] == []
    assert [item["status"] for item in review["passes"]] == [
        "CLOSED",
        "CLOSED_AFTER_RECURSION",
        "CLOSED_AFTER_RECURSION",
        "PASS",
        "PASS",
    ]
    assert review["passes"][-1]["blocking_concerns"] == []
    assert review["remaining_empirical_blockers"]
    assert review["quantitative_figure_generated"] is False
    assert review["verdict"] == (
        "INTERNAL_RESULT_INGEST_PASS__BLOCKERS_CLOSED__MATCHED_EMPIRICAL_CLAIM_OPEN"
    )
    assert "not independent review" in review["claim_boundary"].lower()
    for subject in review["subjects"].values():
        assert _sha(ROOT / subject["path"]) == subject["sha256"]


def test_material_negative_updates_failure_lattice_and_public_trace_without_candidate() -> None:
    trace_raw = _load(FAILURE_TRACE)
    lattice_raw = _load(FAILURE_LATTICE)
    _validator(ROOT / "schemas/math-research-trace.schema.json").validate(trace_raw)
    _validator(ROOT / "schemas/failure-experience-lattice.schema.json").validate(
        lattice_raw
    )

    entries = []
    for raw in trace_raw["entries"]:
        unhashed = dict(raw)
        artifact_hash = unhashed.pop("artifact_hash")
        assert artifact_hash == "sha256:" + _canonical_sha(unhashed)
        entries.append(
            ResearchTraceEntry(
                event_id=raw["event_id"],
                atom_id=raw["atom_id"],
                event_type=ResearchTraceEventType(raw["event_type"]),
                timestamp=raw["timestamp"],
                state_summary=raw["state_summary"],
                action_summary=raw["action_summary"],
                evidence_pointers=tuple(raw["evidence_pointers"]),
                alternatives_considered=tuple(raw["alternatives_considered"]),
                decision_rationale=raw["decision_rationale"],
                outputs=tuple(raw["outputs"]),
                uncertainties=tuple(raw["uncertainties"]),
                residuals=tuple(raw["residuals"]),
                next_steps=tuple(raw["next_steps"]),
                artifact_hash=raw["artifact_hash"],
                previous_event_hash=raw["previous_event_hash"],
            )
        )
    trace = MathResearchTrace(trace_id=trace_raw["trace_id"], entries=tuple(entries))
    assert audit_research_trace(trace).verdict is TraceGateVerdict.PASS
    assert not {
        ResearchTraceEventType.NEXT_STEP_PROPOSED,
        ResearchTraceEventType.CANDIDATE_PROPOSED,
    } & {entry.event_type for entry in trace.entries}

    lattice = FailureExperienceLattice()
    trace_ids = {entry.event_id for entry in trace.entries}
    for raw in lattice_raw["experiences"]:
        unhashed = dict(raw)
        artifact_hash = unhashed.pop("artifact_hash")
        assert artifact_hash == "sha256:" + _canonical_sha(unhashed)
        assert raw["research_trace_event_id"] in trace_ids
        experience = FailureExperience(
            failure_id=raw["failure_id"],
            atom_id=raw["atom_id"],
            candidate_id=raw["candidate_id"],
            context_packet_hash=raw["context_packet_hash"],
            research_trace_event_id=raw["research_trace_event_id"],
            method_family=raw["method_family"],
            failure_mode=raw["failure_mode"],
            residual_signature=tuple(raw["residual_signature"]),
            broken_assumptions=tuple(raw["broken_assumptions"]),
            scope_conditions=tuple(raw["scope_conditions"]),
            competing_diagnoses=tuple(raw["competing_diagnoses"]),
            selected_diagnosis=raw["selected_diagnosis"],
            diagnosis_status=FailureDiagnosisStatus(raw["diagnosis_status"]),
            evidence_pointers=tuple(raw["evidence_pointers"]),
            falsifier_or_attempt=raw["falsifier_or_attempt"],
            observed_result=raw["observed_result"],
            local_repair_attempts=tuple(raw["local_repair_attempts"]),
            timestamp=raw["timestamp"],
            artifact_hash=raw["artifact_hash"],
        )
        lattice = add_failure_experience(lattice, experience)
    for raw in lattice_raw["links"]:
        lattice = add_failure_link(
            lattice,
            FailureLink(
                source_id=raw["source_id"],
                target_id=raw["target_id"],
                relation=FailureRelation(raw["relation"]),
                rationale=raw["rationale"],
                evidence_pointers=tuple(raw["evidence_pointers"]),
            ),
        )
    portrait = global_failure_portrait(lattice)
    assert portrait["experience_count"] == 2
    assert portrait["link_count"] == 2
    assert portrait["verified_impossibilities"] == ()
    assert {link.relation for link in lattice.links} == {
        FailureRelation.SAME_METHOD_FAMILY_AS,
        FailureRelation.SHARES_RESIDUAL_WITH,
    }
    ingest = _load(INGEST)
    assert ingest["typed_residual"]["next_discriminator"].startswith(
        "CANNOT_PROPOSE_UNTIL_DUAL_MEMORY_REVIEW"
    )
