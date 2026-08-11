from __future__ import annotations

import copy
import hashlib
import importlib.resources
import json
import subprocess
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from rakl.application_feedback import (
    ApplicationFeedbackBundle,
    FeedbackImportVerdict,
    FeedbackItem,
    FeedbackKind,
    RepositoryPin,
    canonical_json_sha256,
    import_application_feedback,
    parse_application_feedback_bundle,
    stage_feedback_failure,
    stage_feedback_meta_observation,
    stage_feedback_tool_candidate,
)
from rakl.failure_lattice import FailureExperienceLattice
from rakl.research_tool_inventory import ResearchToolAuthority, ResearchToolInventory

FRAMEWORK_SHA = "f" * 40
FRAMEWORK_VERSION = "0.6.0"


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_repo(tmp_path: Path) -> tuple[Path, dict[str, dict[str, object]]]:
    repo = tmp_path / "RAKL_math"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "remote", "add", "origin", "https://github.com/example/RAKL_math.git")

    payloads: dict[str, dict[str, object]] = {
        "failure": {
            "failure_id": "failure-1",
            "atom_id": "atom-1",
            "candidate_id": "candidate-1",
            "context_packet_hash": "PENDING",
            "research_trace_event_id": "trace-failure",
            "method_family": "bounded-transfer",
            "failure_mode": "counterexample",
            "residual_signature": ["residual:x"],
            "broken_assumptions": ["assumption:y"],
            "scope_conditions": ["scope:z"],
            "competing_diagnoses": ["diagnosis:a", "diagnosis:b"],
            "selected_diagnosis": "diagnosis:a",
            "diagnosis_status": "SUPPORTED",
            "evidence_pointers": ["result-failure"],
            "falsifier_or_attempt": "falsifier:1",
            "observed_result": "candidate fails the registered discriminator",
            "artifact_hash": "PENDING",
            "timestamp": "2026-08-11T08:00:00Z",
            "local_repair_attempts": [],
        },
        "tool": {
            "tool_id": "tool-1",
            "name": "bounded lemma split",
            "kind": "decomposition",
            "abstraction": "split one implication into typed lemmas",
            "source_atom_id": "atom-1",
            "source_candidate_id": "candidate-2",
            "source_result_ids": ["result-tool"],
            "source_context_hash": "PENDING",
            "requested_authority": "PROOF_BACKED",
            "preconditions": ["typed theorem statement"],
            "structural_signature": ["implication-chain"],
            "operation": "split implication",
            "guaranteed_effects": ["localizes a failed proof edge"],
            "non_guarantees": ["does not prove any lemma"],
            "validation_obligations": ["recheck every child lemma"],
            "evidence_pointers": ["result-tool"],
            "known_failure_ids": ["failure-1"],
            "successful_reuse_ids": [],
            "proof_backing": ["proof-receipt:2"],
            "artifact_hash": "PENDING",
        },
        "meta": {
            "observation_id": "meta-1",
            "method_surface": "failure-diagnosis",
            "observation": "failure observation and diagnosis were conflated",
            "evidence_pointers": ["result-meta", "trace-meta"],
            "candidate_framework_delta": "separate observation from diagnosis",
            "validation_status": "UNVALIDATED_PROPOSAL",
        },
    }
    for directory in ("results", "traces", "contexts"):
        (repo / directory).mkdir()
    for name, payload in payloads.items():
        result_id = f"result-{name}"
        trace_id = str(payload.get("research_trace_event_id", f"trace-{name}"))
        result_path = repo / "results" / f"{name}.json"
        trace_path = repo / "traces" / f"{name}.json"
        context_path = repo / "contexts" / f"{name}.json"
        result_path.write_text(
            json.dumps({"result_id": result_id, "observed": True}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        trace_path.write_text(
            json.dumps({"event_id": trace_id, "state": "RESULT_OBSERVED"}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        context_path.write_text(
            json.dumps({"context_id": f"context-{name}", "frozen": True}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        result_sha = _sha256(result_path)
        context_sha = _sha256(context_path)
        if name == "failure":
            payload["artifact_hash"] = result_sha
            payload["context_packet_hash"] = context_sha
        elif name == "tool":
            payload["artifact_hash"] = result_sha
            payload["source_context_hash"] = context_sha
        else:
            payload["context_sha256"] = context_sha
    lessons = repo / "lessons"
    lessons.mkdir()
    for name, payload in payloads.items():
        (lessons / f"{name}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "freeze feedback sources")
    return repo, payloads


def _bundle_document(repo: Path, payloads: dict[str, dict[str, object]]) -> dict[str, object]:
    commit = _git(repo, "rev-parse", "HEAD")
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    namespace = "github.com/example/RAKL_math"
    items = []
    for name, kind in (
        ("failure", "FAILURE_EXPERIENCE"),
        ("tool", "TOOL_CANDIDATE"),
        ("meta", "META_OBSERVATION"),
    ):
        path = f"lessons/{name}.json"
        result_path = f"results/{name}.json"
        trace_path = f"traces/{name}.json"
        context_path = f"contexts/{name}.json"
        items.append(
            {
                "item_id": f"{namespace}::{kind.lower()}::{name}-1",
                "kind": kind,
                "source": {
                    "path": path,
                    "git_blob_sha": _git(repo, "rev-parse", f"HEAD:{path}"),
                },
                "payload": copy.deepcopy(payloads[name]),
                "payload_canonical_sha256": canonical_json_sha256(payloads[name]),
                "application_bindings": {
                    "result_id": f"result-{name}",
                    "result_path": result_path,
                    "result_git_blob_sha": _git(repo, "rev-parse", f"HEAD:{result_path}"),
                    "result_sha256": _sha256(repo / result_path),
                    "trace_event_id": str(payloads[name].get("research_trace_event_id", f"trace-{name}")),
                    "trace_path": trace_path,
                    "trace_git_blob_sha": _git(repo, "rev-parse", f"HEAD:{trace_path}"),
                    "trace_sha256": _sha256(repo / trace_path),
                    "context_path": context_path,
                    "context_git_blob_sha": _git(repo, "rev-parse", f"HEAD:{context_path}"),
                    "context_sha256": _sha256(repo / context_path),
                    "observed_at_utc": "2026-08-11T08:00:00Z",
                },
                "supersedes": [],
            }
        )
    document: dict[str, object] = {
        "schema_version": "application-feedback-bundle-v1",
        "bundle_id": f"{namespace}::feedback-bundle::bundle-1",
        "producer": {
            "repository_namespace": namespace,
            "repository_url": "https://github.com/example/RAKL_math.git",
            "commit_sha": commit,
            "tree_sha": tree,
        },
        "framework_requirement": {
            "repository_url": "https://github.com/SzeChunYiu/RAKL.git",
            "commit_sha": FRAMEWORK_SHA,
            "version": FRAMEWORK_VERSION,
        },
        "authority_envelope": {
            "requested_authority": "PROOF_BACKED",
            "proposal_only": True,
            "inventory_mutation_allowed": False,
            "failure_lattice_mutation_allowed": False,
            "promotion_allowed": False,
        },
        "previous_bundle": None,
        "items": items,
    }
    document["bundle_canonical_sha256"] = canonical_json_sha256(document)
    return document


def _import(document: dict[str, object], repo: Path, *, prior=()):
    return import_application_feedback(
        document,
        source_repository=repo,
        current_framework_commit_sha=FRAMEWORK_SHA,
        current_framework_version=FRAMEWORK_VERSION,
        prior_receipts=prior,
    )


def _rehash(document: dict[str, object]) -> None:
    document.pop("bundle_canonical_sha256", None)
    document["bundle_canonical_sha256"] = canonical_json_sha256(document)


def test_valid_import_is_deterministic_immutable_and_proposal_only(tmp_path: Path) -> None:
    repo, payloads = _source_repo(tmp_path)
    document = _bundle_document(repo, payloads)

    first = _import(document, repo)
    second = _import(copy.deepcopy(document), repo)

    assert first == second
    assert first.verdict is FeedbackImportVerdict.QUARANTINED_PROPOSAL
    assert first.grants_scientific_authority is False
    assert first.grants_method_promotion is False
    assert first.inventory_mutation_performed is False
    assert first.failure_lattice_mutation_performed is False
    assert first.quarantined_item_ids == tuple(item["item_id"] for item in document["items"])
    assert first.bundle_canonical_sha256 == document["bundle_canonical_sha256"]
    with pytest.raises(FrozenInstanceError):
        first.verdict = FeedbackImportVerdict.REJECT  # type: ignore[misc]
    bundle = parse_application_feedback_bundle(document)
    assert isinstance(bundle, ApplicationFeedbackBundle)
    assert isinstance(bundle.producer, RepositoryPin)
    assert all(isinstance(item, FeedbackItem) for item in bundle.items)


def test_schema_files_are_valid_and_accept_receipt_and_bundle(tmp_path: Path) -> None:
    repo, payloads = _source_repo(tmp_path)
    document = _bundle_document(repo, payloads)
    receipt = _import(document, repo)
    root = Path(__file__).resolve().parents[1]
    for name, instance in (
        ("application-feedback-bundle.schema.json", document),
        ("application-feedback-import-receipt.schema.json", receipt.to_dict()),
    ):
        schema = json.loads((root / "schemas" / name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert list(Draft202012Validator(schema).iter_errors(instance)) == []
    packaged = importlib.resources.files("rakl.schemas").joinpath(
        "application-feedback-bundle.schema.json"
    )
    assert packaged.read_bytes() == (
        root / "schemas/application-feedback-bundle.schema.json"
    ).read_bytes()


@pytest.mark.parametrize(
    ("mutator", "reason"),
    [
        (lambda d: d["items"][0].update(payload_canonical_sha256="0" * 64), "payload_canonical_sha256_mismatch"),
        (lambda d: d.update(bundle_canonical_sha256="0" * 64), "bundle_canonical_sha256_mismatch"),
        (lambda d: d["items"][0]["source"].update(git_blob_sha="0" * 40), "source_blob_mismatch"),
        (lambda d: d["producer"].update(tree_sha="0" * 40), "producer_tree_mismatch"),
    ],
)
def test_hash_and_repository_binding_mismatches_reject(tmp_path: Path, mutator, reason: str) -> None:
    repo, payloads = _source_repo(tmp_path)
    document = _bundle_document(repo, payloads)
    mutator(document)
    if reason not in {"bundle_canonical_sha256_mismatch"}:
        _rehash(document)
    receipt = _import(document, repo)
    assert receipt.verdict is FeedbackImportVerdict.REJECT
    assert any(reason in item for item in receipt.reasons)


def test_stale_framework_pin_fails_closed(tmp_path: Path) -> None:
    repo, payloads = _source_repo(tmp_path)
    document = _bundle_document(repo, payloads)
    document["framework_requirement"]["commit_sha"] = "e" * 40
    _rehash(document)
    receipt = _import(document, repo)
    assert receipt.verdict is FeedbackImportVerdict.CANNOT_CHECK
    assert "framework_commit_pin_stale" in receipt.reasons


def test_stale_source_checkout_fails_closed(tmp_path: Path) -> None:
    repo, payloads = _source_repo(tmp_path)
    document = _bundle_document(repo, payloads)
    (repo / "unrelated.txt").write_text("later\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "move source head")
    receipt = _import(document, repo)
    assert receipt.verdict is FeedbackImportVerdict.CANNOT_CHECK
    assert "producer_checkout_not_at_pinned_commit" in receipt.reasons


def test_unknown_schema_and_missing_result_trace_fail_closed(tmp_path: Path) -> None:
    repo, payloads = _source_repo(tmp_path)
    unknown = _bundle_document(repo, payloads)
    unknown["schema_version"] = "application-feedback-bundle-v999"
    _rehash(unknown)
    assert _import(unknown, repo).verdict is FeedbackImportVerdict.CANNOT_CHECK

    missing = _bundle_document(repo, payloads)
    del missing["items"][0]["application_bindings"]["trace_event_id"]
    del missing["items"][1]["application_bindings"]["result_id"]
    _rehash(missing)
    receipt = _import(missing, repo)
    assert receipt.verdict is not FeedbackImportVerdict.QUARANTINED_PROPOSAL
    assert any("trace_event_id_missing" in reason for reason in receipt.reasons)
    assert any("result_id_missing" in reason for reason in receipt.reasons)


def test_malformed_typed_payload_and_nonfinite_json_fail_closed(tmp_path: Path) -> None:
    repo, payloads = _source_repo(tmp_path)
    malformed = _bundle_document(repo, payloads)
    malformed["items"][0]["payload"]["residual_signature"] = "not-an-array"
    malformed["items"][0]["payload_canonical_sha256"] = canonical_json_sha256(
        malformed["items"][0]["payload"]
    )
    # The committed source is intentionally no longer equal to the claimed
    # typed payload, but the audit must return a receipt rather than crash.
    _rehash(malformed)
    receipt = _import(malformed, repo)
    assert receipt.verdict is FeedbackImportVerdict.REJECT
    assert any("failure_payload_invalid" in reason for reason in receipt.reasons)

    nonfinite = _bundle_document(repo, payloads)
    nonfinite["items"][0]["payload"]["score"] = float("nan")
    nonfinite["bundle_canonical_sha256"] = "0" * 64
    receipt = _import(nonfinite, repo)
    assert receipt.verdict is not FeedbackImportVerdict.QUARANTINED_PROPOSAL
    assert any("canonical_json_invalid" in reason for reason in receipt.reasons)

    scalar = copy.deepcopy(payloads)
    scalar["failure"]["failure_id"] = 123
    (repo / "lessons/failure.json").write_text(
        json.dumps(scalar["failure"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "commit malformed scalar")
    scalar_document = _bundle_document(repo, scalar)
    receipt = _import(scalar_document, repo)
    assert receipt.verdict is FeedbackImportVerdict.REJECT
    assert any("failure_payload_invalid" in reason for reason in receipt.reasons)


def test_duplicate_and_namespaced_id_violations_reject(tmp_path: Path) -> None:
    repo, payloads = _source_repo(tmp_path)
    duplicate = _bundle_document(repo, payloads)
    duplicate["items"][1]["item_id"] = duplicate["items"][0]["item_id"]
    _rehash(duplicate)
    receipt = _import(duplicate, repo)
    assert receipt.verdict is FeedbackImportVerdict.REJECT
    assert "duplicate_item_id_in_bundle" in receipt.reasons

    unnamespaced = _bundle_document(repo, payloads)
    unnamespaced["items"][0]["item_id"] = "failure-1"
    _rehash(unnamespaced)
    receipt = _import(unnamespaced, repo)
    assert receipt.verdict is FeedbackImportVerdict.REJECT
    assert any(
        "item_id_not_namespaced" in reason or "bundle_schema_invalid" in reason
        for reason in receipt.reasons
    )

    foreign_namespace = _bundle_document(repo, payloads)
    foreign_namespace["producer"]["repository_namespace"] = "github.com/attacker/other"
    for item in foreign_namespace["items"]:
        item["item_id"] = item["item_id"].replace(
            "github.com/example/RAKL_math", "github.com/attacker/other"
        )
    foreign_namespace["bundle_id"] = foreign_namespace["bundle_id"].replace(
        "github.com/example/RAKL_math", "github.com/attacker/other"
    )
    _rehash(foreign_namespace)
    receipt = _import(foreign_namespace, repo)
    assert receipt.verdict is FeedbackImportVerdict.REJECT
    assert "producer_namespace_repository_mismatch" in receipt.reasons


@pytest.mark.parametrize("foreign_authority", ["VERIFIED_LOCAL", "PROOF_BACKED"])
def test_foreign_authority_is_downgraded_and_staging_requires_receipt(
    tmp_path: Path, foreign_authority: str
) -> None:
    repo, payloads = _source_repo(tmp_path)
    document = _bundle_document(repo, payloads)
    document["authority_envelope"]["requested_authority"] = foreign_authority
    _rehash(document)
    bundle = parse_application_feedback_bundle(document)
    receipt = _import(document, repo)

    tool_id = next(item.item_id for item in bundle.items if item.kind is FeedbackKind.TOOL_CANDIDATE)
    staged_tool = stage_feedback_tool_candidate(bundle, receipt, tool_id)
    assert staged_tool.authority is ResearchToolAuthority.HEURISTIC
    assert receipt.authority_downgrades == (
        f"foreign_authority_downgraded:{foreign_authority}->HEURISTIC",
    )
    assert "ToolApplicabilityWitness" in staged_tool.validation_obligations
    assert "DifferenceWitness" in staged_tool.validation_obligations

    failure_id = next(item.item_id for item in bundle.items if item.kind is FeedbackKind.FAILURE_EXPERIENCE)
    assert stage_feedback_failure(bundle, receipt, failure_id).failure_id == "failure-1"
    meta_id = next(item.item_id for item in bundle.items if item.kind is FeedbackKind.META_OBSERVATION)
    staged_meta = stage_feedback_meta_observation(bundle, receipt, meta_id)
    assert staged_meta["validation_status"] == "UNVALIDATED_PROPOSAL"

    rejected = copy.copy(receipt)
    object.__setattr__(rejected, "verdict", FeedbackImportVerdict.REJECT)
    with pytest.raises(ValueError, match="acceptable quarantined receipt"):
        stage_feedback_tool_candidate(bundle, rejected, tool_id)


def test_typed_application_identity_mismatch_rejects(tmp_path: Path) -> None:
    repo, payloads = _source_repo(tmp_path)
    document = _bundle_document(repo, payloads)
    document["items"][0]["application_bindings"]["trace_event_id"] = "trace-other"
    _rehash(document)
    receipt = _import(document, repo)
    assert receipt.verdict is FeedbackImportVerdict.REJECT
    assert any("payload_trace_identity_mismatch" in reason for reason in receipt.reasons)


def test_framework_url_runtime_schema_and_exact_artifact_bindings_fail_closed(
    tmp_path: Path,
) -> None:
    repo, payloads = _source_repo(tmp_path)

    wrong_framework = _bundle_document(repo, payloads)
    wrong_framework["framework_requirement"]["repository_url"] = "https://attacker.invalid/RAKL"
    _rehash(wrong_framework)
    receipt = _import(wrong_framework, repo)
    assert receipt.verdict is FeedbackImportVerdict.REJECT
    assert "framework_repository_url_mismatch" in receipt.reasons

    extra = _bundle_document(repo, payloads)
    extra["unexpected"] = True
    extra["authority_envelope"]["requested_authority"] = "ROOT"
    _rehash(extra)
    receipt = _import(extra, repo)
    assert receipt.verdict is FeedbackImportVerdict.REJECT
    assert any("bundle_schema_invalid" in reason for reason in receipt.reasons)

    false_result = _bundle_document(repo, payloads)
    false_result["items"][1]["application_bindings"]["result_sha256"] = "0" * 64
    _rehash(false_result)
    receipt = _import(false_result, repo)
    assert receipt.verdict is FeedbackImportVerdict.REJECT
    assert any("result_sha256_mismatch" in reason for reason in receipt.reasons)

    non_utc = _bundle_document(repo, payloads)
    non_utc["items"][0]["application_bindings"]["observed_at_utc"] = (
        "2026-08-11T10:00:00+02:00"
    )
    _rehash(non_utc)
    assert _import(non_utc, repo).verdict is FeedbackImportVerdict.REJECT


def test_negative_receipts_validate_and_rejected_history_cannot_authorize_lineage(
    tmp_path: Path,
) -> None:
    repo, payloads = _source_repo(tmp_path)
    root = Path(__file__).resolve().parents[1]
    receipt_schema = json.loads(
        (root / "schemas/application-feedback-import-receipt.schema.json").read_text(
            encoding="utf-8"
        )
    )
    invalid = {
        "schema_version": "bad",
        "bundle_id": "",
        "bundle_canonical_sha256": "x",
    }
    cannot = _import(invalid, repo)
    assert cannot.verdict is FeedbackImportVerdict.CANNOT_CHECK
    assert list(Draft202012Validator(receipt_schema).iter_errors(cannot.to_dict())) == []

    overlong = dict(invalid, bundle_id="x" * 513)
    cannot = _import(overlong, repo)
    assert cannot.verdict is FeedbackImportVerdict.CANNOT_CHECK
    assert list(Draft202012Validator(receipt_schema).iter_errors(cannot.to_dict())) == []

    first_document = _bundle_document(repo, payloads)
    first = _import(first_document, repo)
    rejected_history = replace(first, verdict=FeedbackImportVerdict.REJECT)
    successor = _bundle_document(repo, payloads)
    successor["bundle_id"] = "github.com/example/RAKL_math::feedback-bundle::rejected-parent"
    successor["previous_bundle"] = {
        "bundle_id": rejected_history.bundle_id,
        "bundle_canonical_sha256": rejected_history.bundle_canonical_sha256,
    }
    successor["items"] = [successor["items"][0]]
    successor["items"][0]["item_id"] = (
        "github.com/example/RAKL_math::failure_experience::after-reject"
    )
    successor["items"][0]["supersedes"] = [first_document["items"][0]["item_id"]]
    _rehash(successor)
    receipt = _import(successor, repo, prior=(rejected_history,))
    assert receipt.verdict is FeedbackImportVerdict.CANNOT_CHECK
    assert "previous_bundle_receipt_missing" in receipt.reasons


def test_import_does_not_mutate_failure_lattice_or_tool_inventory(tmp_path: Path) -> None:
    repo, payloads = _source_repo(tmp_path)
    document = _bundle_document(repo, payloads)
    failures = FailureExperienceLattice()
    tools = ResearchToolInventory()
    before_failures = copy.deepcopy(failures)
    before_tools = copy.deepcopy(tools)

    receipt = _import(document, repo)

    assert receipt.verdict is FeedbackImportVerdict.QUARANTINED_PROPOSAL
    assert failures == before_failures
    assert tools == before_tools
    assert not hasattr(receipt, "promote")


def test_idempotence_and_conflicting_bundle_fail_closed(tmp_path: Path) -> None:
    repo, payloads = _source_repo(tmp_path)
    document = _bundle_document(repo, payloads)
    first = _import(document, repo)
    assert _import(document, repo, prior=(first,)) == first

    conflict = copy.deepcopy(document)
    conflict["items"][0]["application_bindings"]["result_id"] = "different-result"
    _rehash(conflict)
    receipt = _import(conflict, repo, prior=(first,))
    assert receipt.verdict is FeedbackImportVerdict.REJECT
    assert "bundle_id_collision" in receipt.reasons


def test_supersession_preserves_negative_history_and_requires_previous_bundle(tmp_path: Path) -> None:
    repo, payloads = _source_repo(tmp_path)
    first_document = _bundle_document(repo, payloads)
    first = _import(first_document, repo)
    old_failure_id = first_document["items"][0]["item_id"]

    payloads2 = copy.deepcopy(payloads)
    payloads2["failure"]["failure_id"] = "failure-2"
    (repo / "lessons/failure.json").write_text(
        json.dumps(payloads2["failure"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "superseding diagnosis")
    second_document = _bundle_document(repo, payloads2)
    second_document["bundle_id"] = "github.com/example/RAKL_math::feedback-bundle::bundle-2"
    second_document["previous_bundle"] = {
        "bundle_id": first.bundle_id,
        "bundle_canonical_sha256": first.bundle_canonical_sha256,
    }
    second_document["items"][0]["item_id"] = "github.com/example/RAKL_math::failure_experience::failure-2"
    second_document["items"][0]["supersedes"] = [old_failure_id]
    # Feedback bundles are append-only deltas. Repeating unchanged logical
    # items under a new bundle identity is a duplicate, not an idempotent replay.
    second_document["items"] = [second_document["items"][0]]
    _rehash(second_document)

    second = _import(second_document, repo, prior=(first,))
    assert second.verdict is FeedbackImportVerdict.QUARANTINED_PROPOSAL
    assert old_failure_id in second.preserved_item_ids
    assert (second_document["items"][0]["item_id"], old_failure_id) in second.supersession_edges
    assert old_failure_id not in second.quarantined_item_ids

    no_history = _import(second_document, repo)
    assert no_history.verdict is FeedbackImportVerdict.CANNOT_CHECK
    assert "previous_bundle_receipt_missing" in no_history.reasons


def test_ambiguous_supersession_rejects_without_deleting_predecessor(tmp_path: Path) -> None:
    repo, payloads = _source_repo(tmp_path)
    first_document = _bundle_document(repo, payloads)
    first = _import(first_document, repo)
    old_id = first_document["items"][0]["item_id"]

    second_document = _bundle_document(repo, payloads)
    second_document["bundle_id"] = "github.com/example/RAKL_math::feedback-bundle::ambiguous"
    base = copy.deepcopy(second_document["items"][0])
    base["item_id"] = "github.com/example/RAKL_math::failure_experience::successor-a"
    base["supersedes"] = [old_id]
    rival = copy.deepcopy(base)
    rival["item_id"] = "github.com/example/RAKL_math::failure_experience::successor-b"
    second_document["items"] = [base, rival]
    second_document["previous_bundle"] = {
        "bundle_id": first.bundle_id,
        "bundle_canonical_sha256": first.bundle_canonical_sha256,
    }
    _rehash(second_document)
    receipt = _import(second_document, repo, prior=(first,))
    assert receipt.verdict is FeedbackImportVerdict.REJECT
    assert any("ambiguous_supersession" in reason for reason in receipt.reasons)
    assert old_id in receipt.preserved_item_ids
