"""Frozen planted-world tests for artifact-contract coverage.

Fixtures are synthetic artifact types and paths.  No application-side
mathematics enters framework authority.

Two properties carry most of the weight.  First, the preservation rule is
selected by lifecycle: applying the immutable-evidence rule to an intentionally
evolving state file is the near-miss regression this object exists to prevent,
so an evolving file that legitimately changed must pass.  Second, an ordinary
prose-only change must not activate the checker at all — a checker that fires on
documentation edits gets switched off.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]

from rakl.artifact_contract_coverage import (
    ArtifactContract,
    ArtifactContractCoverageReceipt,
    ArtifactContractStatus,
    ArtifactLifecycle,
    ChangedArtifact,
    ContractCoverageVerdict,
    DeclaredNonArtifact,
    audit_artifact_contract_coverage,
    receipt_canonical_sha256,
)


SUBJECT_SHA = "8a608f340d47b4b6ae612275b0595faf6b804432"
MERGE_BASE_SHA = "d8ac4102285c4ed1ba0fbd5d8818dc4c4731a8cc"
BLOB = "b" * 40
CLAIM_BOUNDARY = (
    "changed-artifact inventory only; grants no strict-process credit, no "
    "framework authority, and is not independent review"
)

CONTRACTS = (
    ArtifactContract(
        artifact_type="context_fiber",
        owner_module="rakl.math_context",
        schema_id="math-context-fiber.schema.json",
        runtime_validator_id="rakl.math_context.validate_context_fiber",
        lifecycle=ArtifactLifecycle.IMMUTABLE_EVIDENCE,
        path_globs=("*/01_context/*.json",),
    ),
    ArtifactContract(
        artifact_type="research_trace",
        owner_module="rakl.research_trace",
        schema_id="math-research-trace.schema.json",
        runtime_validator_id="rakl.research_trace.validate_trace",
        lifecycle=ArtifactLifecycle.APPEND_ONLY_LEDGER,
        path_globs=("*/03_trace/*.json",),
    ),
    ArtifactContract(
        artifact_type="problem_dag_obligations",
        owner_module="rakl.problem_fibre",
        schema_id="open-obligations.schema.json",
        runtime_validator_id="rakl.problem_fibre.validate_obligations",
        lifecycle=ArtifactLifecycle.EVOLVING_STATE,
        path_globs=("*/02_problem_dag/open_obligations.yaml",),
    ),
    ArtifactContract(
        artifact_type="saturation_view",
        owner_module="rakl.saturation_vector",
        schema_id="saturation-view.schema.json",
        runtime_validator_id="rakl.saturation_vector.validate_view",
        lifecycle=ArtifactLifecycle.DERIVED_VIEW,
        path_globs=("*/09_views/*.json",),
    ),
)


def _artifact(**overrides: Any) -> ChangedArtifact:
    """A well-formed immutable evidence artifact: added, unchanged since."""

    values: dict[str, Any] = {
        "path": "lane_alpha/01_context/CONTEXT_0001.json",
        "artifact_type": "context_fiber",
        "declared_lifecycle": ArtifactLifecycle.IMMUTABLE_EVIDENCE,
        "historical_blob_sha": BLOB,
        "historical_content_sha256": "c" * 64,
        "historical_blob_preserved": True,
        "current_content_sha256": "c" * 64,
        "declared_internal_hash": "d" * 64,
        "computed_internal_hash": "d" * 64,
        "schema_valid": True,
        "runtime_valid": True,
        "artifact_event_at_utc": "2026-08-10T09:00:00Z",
        "introducing_commit_at_utc": "2026-08-10T10:00:00Z",
    }
    values.update(overrides)
    return ChangedArtifact(**values)


def _evolving(**overrides: Any) -> ChangedArtifact:
    """The near-miss: a DAG obligations file that legitimately changed."""

    values: dict[str, Any] = {
        "path": "lane_beta/02_problem_dag/open_obligations.yaml",
        "artifact_type": "problem_dag_obligations",
        "declared_lifecycle": ArtifactLifecycle.EVOLVING_STATE,
        "historical_blob_sha": "a" * 40,
        "historical_content_sha256": "1" * 64,
        "historical_blob_preserved": True,
        "current_content_sha256": "2" * 64,
        "declared_internal_hash": "e" * 64,
        "computed_internal_hash": "e" * 64,
        "schema_valid": True,
        "runtime_valid": True,
        "artifact_event_at_utc": "2026-08-10T09:00:00Z",
        "introducing_commit_at_utc": "2026-08-10T10:00:00Z",
    }
    values.update(overrides)
    return ChangedArtifact(**values)


def _ledger(**overrides: Any) -> ChangedArtifact:
    values: dict[str, Any] = {
        "path": "lane_beta/03_trace/TRACE.json",
        "artifact_type": "research_trace",
        "declared_lifecycle": ArtifactLifecycle.APPEND_ONLY_LEDGER,
        "historical_blob_sha": "9" * 40,
        "historical_content_sha256": "3" * 64,
        "historical_blob_preserved": True,
        "current_content_sha256": "4" * 64,
        "current_content_extends_historical": True,
        "declared_internal_hash": "f" * 64,
        "computed_internal_hash": "f" * 64,
        "schema_valid": True,
        "runtime_valid": True,
        "artifact_event_at_utc": "2026-08-10T09:00:00Z",
        "introducing_commit_at_utc": "2026-08-10T10:00:00Z",
    }
    values.update(overrides)
    return ChangedArtifact(**values)


def _view(**overrides: Any) -> ChangedArtifact:
    values: dict[str, Any] = {
        "path": "lane_beta/09_views/SATURATION.json",
        "artifact_type": "saturation_view",
        "declared_lifecycle": ArtifactLifecycle.DERIVED_VIEW,
        "historical_blob_sha": "7" * 40,
        "historical_content_sha256": "5" * 64,
        "historical_blob_preserved": True,
        "current_content_sha256": "6" * 64,
        "declared_internal_hash": "0" * 64,
        "computed_internal_hash": "0" * 64,
        "schema_valid": True,
        "runtime_valid": True,
        "artifact_event_at_utc": "2026-08-10T09:00:00Z",
        "introducing_commit_at_utc": "2026-08-10T10:00:00Z",
        "derived_from": "lane_beta/05_saturation/RAW.json",
    }
    values.update(overrides)
    return ChangedArtifact(**values)


def _receipt(**overrides: Any) -> ArtifactContractCoverageReceipt:
    values: dict[str, Any] = {
        "subject_repository": "github.com/example/application_repo",
        "subject_sha": SUBJECT_SHA,
        "merge_base_sha": MERGE_BASE_SHA,
        "changed_artifacts": (_artifact(),),
        "declared_non_artifacts": (),
        "claim_boundary": CLAIM_BOUNDARY,
        "evidence_pointers": ("pr::81",),
    }
    values.update(overrides)
    return ArtifactContractCoverageReceipt(**values).with_content_hash()


def _audit(
    receipt: ArtifactContractCoverageReceipt | None,
    changed_paths: tuple[str, ...] | None = None,
) -> Any:
    """Audit against the observed diff.

    When ``changed_paths`` is omitted the diff is taken to be exactly what the
    receipt inventories, which isolates the contract checks.  The omission world
    below supplies a diff wider than the inventory on purpose.
    """

    if changed_paths is None:
        if receipt is None:
            changed_paths = ()
        else:
            changed_paths = tuple(
                [a.path for a in receipt.changed_artifacts]
                + [d.path for d in receipt.declared_non_artifacts]
            )
    return audit_artifact_contract_coverage(
        receipt, contracts=CONTRACTS, changed_paths=changed_paths
    )


def _status(report: Any, path: str) -> ArtifactContractStatus:
    return next(f.status for f in report.findings if f.path == path)


# --- non-activation control (mandatory) --------------------------------------


def test_prose_only_change_does_not_activate_the_checker() -> None:
    report = _audit(
        _receipt(
            changed_artifacts=(),
            declared_non_artifacts=(
                DeclaredNonArtifact("docs/NOTES.md", "prose only"),
                DeclaredNonArtifact("README.md", "prose only"),
            ),
        )
    )
    assert report.verdict is ContractCoverageVerdict.NOT_ACTIVATED
    assert report.activated is False
    assert report.findings == ()
    assert report.permits_strict_process_credit is False


def test_an_artifact_change_does_activate_the_checker() -> None:
    report = _audit(_receipt())
    assert report.activated is True
    assert report.verdict is ContractCoverageVerdict.COVERAGE_SATISFIED_PROPOSAL_ONLY


def test_the_non_artifact_declaration_is_not_self_certifying() -> None:
    """Declaring an owned path 'prose' must not route it around its contract."""

    report = _audit(
        _receipt(
            changed_artifacts=(),
            declared_non_artifacts=(
                DeclaredNonArtifact(
                    "lane_alpha/01_context/CONTEXT_0002.json", "just a note"
                ),
            ),
        )
    )
    assert report.verdict is ContractCoverageVerdict.CANNOT_CHECK
    assert (
        _status(report, "lane_alpha/01_context/CONTEXT_0002.json")
        is ArtifactContractStatus.MISDECLARED_AS_NON_ARTIFACT
    )


# --- the inventory must be bound to the real diff ----------------------------

_ELEVEN_PATHS = tuple(
    f"lane_alpha/01_context/CONTEXT_{i:04d}.json" for i in range(1, 12)
)


def test_an_inventory_that_omits_diff_paths_fails_closed() -> None:
    """The verbatim #134 failure: eleven artifacts added, two inventoried.

    Every inventoried artifact passes its contract, so without a binding to the
    observed diff this returns a clean pass — which is exactly how the
    motivating PR earned strict-process credit it had not established.
    """

    inventoried = (
        _artifact(path=_ELEVEN_PATHS[0]),
        _artifact(path=_ELEVEN_PATHS[1]),
    )
    report = _audit(
        _receipt(changed_artifacts=inventoried), changed_paths=_ELEVEN_PATHS
    )
    assert report.verdict is ContractCoverageVerdict.CANNOT_CHECK
    assert report.permits_strict_process_credit is False
    omitted = [
        f.path
        for f in report.findings
        if f.status is ArtifactContractStatus.UNINVENTORIED_CHANGED_PATH
    ]
    assert sorted(omitted) == sorted(_ELEVEN_PATHS[2:])
    assert len(omitted) == 9


def test_a_complete_inventory_of_the_same_diff_passes() -> None:
    """No-alarm counterpart: inventory all eleven and the check clears."""

    report = _audit(
        _receipt(changed_artifacts=tuple(_artifact(path=p) for p in _ELEVEN_PATHS)),
        changed_paths=_ELEVEN_PATHS,
    )
    assert report.verdict is ContractCoverageVerdict.COVERAGE_SATISFIED_PROPOSAL_ONLY
    assert report.permits_strict_process_credit is True


def test_omission_is_caught_even_for_a_path_no_contract_owns() -> None:
    report = _audit(
        _receipt(), changed_paths=(_artifact().path, "lane_alpha/99_unknown/THING.bin")
    )
    assert report.verdict is ContractCoverageVerdict.CANNOT_CHECK
    assert (
        _status(report, "lane_alpha/99_unknown/THING.bin")
        is ArtifactContractStatus.UNINVENTORIED_CHANGED_PATH
    )


def test_inventorying_a_path_the_diff_never_touched_cannot_be_checked() -> None:
    report = _audit(_receipt(), changed_paths=())
    assert report.verdict is ContractCoverageVerdict.CANNOT_CHECK
    assert any(
        r.startswith("inventoried_path_absent_from_changed_paths")
        for r in report.reasons
    )


def test_prose_only_diff_still_does_not_activate_under_the_diff_binding() -> None:
    report = _audit(
        _receipt(
            changed_artifacts=(),
            declared_non_artifacts=(DeclaredNonArtifact("docs/NOTES.md", "prose only"),),
        ),
        changed_paths=("docs/NOTES.md",),
    )
    assert report.verdict is ContractCoverageVerdict.NOT_ACTIVATED


# --- clean baseline across all four lifecycles -------------------------------


def test_all_four_lifecycles_pass_under_their_own_rule() -> None:
    report = _audit(
        _receipt(changed_artifacts=(_artifact(), _ledger(), _evolving(), _view()))
    )
    assert report.verdict is ContractCoverageVerdict.COVERAGE_SATISFIED_PROPOSAL_ONLY
    assert report.permits_strict_process_credit is True
    assert all(
        f.status is ArtifactContractStatus.CONTRACT_SATISFIED for f in report.findings
    )


def test_evolving_state_may_change_without_being_frozen() -> None:
    """The near-miss regression: a byte-identity rule here would be wrong."""

    report = _audit(_receipt(changed_artifacts=(_evolving(),)))
    assert report.verdict is ContractCoverageVerdict.COVERAGE_SATISFIED_PROPOSAL_ONLY
    applied = next(f.applied_lifecycle for f in report.findings)
    assert applied is ArtifactLifecycle.EVOLVING_STATE


def test_evolving_state_must_still_preserve_its_historical_blob() -> None:
    report = _audit(
        _receipt(changed_artifacts=(_evolving(historical_blob_preserved=False),))
    )
    assert report.verdict is ContractCoverageVerdict.CONTRACT_VIOLATED
    assert (
        _status(report, "lane_beta/02_problem_dag/open_obligations.yaml")
        is ArtifactContractStatus.HISTORICAL_BLOB_NOT_PRESERVED
    )


def test_append_only_ledger_may_grow_but_not_lose_its_prefix() -> None:
    ok = _audit(_receipt(changed_artifacts=(_ledger(),)))
    assert ok.verdict is ContractCoverageVerdict.COVERAGE_SATISFIED_PROPOSAL_ONLY

    broken = _audit(
        _receipt(changed_artifacts=(_ledger(current_content_extends_historical=False),))
    )
    assert broken.verdict is ContractCoverageVerdict.CONTRACT_VIOLATED
    assert (
        _status(broken, "lane_beta/03_trace/TRACE.json")
        is ArtifactContractStatus.LEDGER_PREFIX_BROKEN
    )


def test_derived_view_must_declare_its_source() -> None:
    report = _audit(_receipt(changed_artifacts=(_view(derived_from=None),)))
    assert report.verdict is ContractCoverageVerdict.CONTRACT_VIOLATED
    assert (
        _status(report, "lane_beta/09_views/SATURATION.json")
        is ArtifactContractStatus.DERIVED_VIEW_SOURCE_UNDECLARED
    )


# --- planted worlds from the issue -------------------------------------------


def test_unknown_artifact_type_is_explicitly_unowned() -> None:
    report = _audit(
        _receipt(changed_artifacts=(_artifact(artifact_type="continuation_packet"),))
    )
    assert report.verdict is ContractCoverageVerdict.COVERAGE_UNOWNED
    assert (
        _status(report, "lane_alpha/01_context/CONTEXT_0001.json")
        is ArtifactContractStatus.UNOWNED_ARTIFACT_TYPE
    )
    assert report.permits_strict_process_credit is False


def test_false_internal_hash_is_a_violation() -> None:
    report = _audit(
        _receipt(changed_artifacts=(_artifact(computed_internal_hash="9" * 64),))
    )
    assert report.verdict is ContractCoverageVerdict.CONTRACT_VIOLATED
    assert (
        _status(report, "lane_alpha/01_context/CONTEXT_0001.json")
        is ArtifactContractStatus.INTERNAL_HASH_FALSE
    )


def test_schema_valid_but_runtime_invalid_is_its_own_status() -> None:
    report = _audit(
        _receipt(changed_artifacts=(_artifact(schema_valid=True, runtime_valid=False),))
    )
    assert report.verdict is ContractCoverageVerdict.CONTRACT_VIOLATED
    assert (
        _status(report, "lane_alpha/01_context/CONTEXT_0001.json")
        is ArtifactContractStatus.SCHEMA_VALID_RUNTIME_INVALID
    )


def test_schema_invalid_is_distinguished_from_runtime_invalid() -> None:
    report = _audit(
        _receipt(changed_artifacts=(_artifact(schema_valid=False, runtime_valid=True),))
    )
    assert (
        _status(report, "lane_alpha/01_context/CONTEXT_0001.json")
        is ArtifactContractStatus.SCHEMA_INVALID
    )


def test_impossible_git_chronology_is_a_violation() -> None:
    report = _audit(
        _receipt(
            changed_artifacts=(
                _artifact(
                    artifact_event_at_utc="2026-08-10T11:00:00Z",
                    introducing_commit_at_utc="2026-08-10T10:00:00Z",
                ),
            )
        )
    )
    assert report.verdict is ContractCoverageVerdict.CONTRACT_VIOLATED
    assert (
        _status(report, "lane_alpha/01_context/CONTEXT_0001.json")
        is ArtifactContractStatus.CHRONOLOGY_IMPOSSIBLE
    )


def test_equal_event_and_commit_time_is_not_impossible() -> None:
    report = _audit(
        _receipt(
            changed_artifacts=(
                _artifact(
                    artifact_event_at_utc="2026-08-10T10:00:00Z",
                    introducing_commit_at_utc="2026-08-10T10:00:00Z",
                ),
            )
        )
    )
    assert report.verdict is ContractCoverageVerdict.COVERAGE_SATISFIED_PROPOSAL_ONLY


# --- planted worlds from the issue comment -----------------------------------


@pytest.mark.parametrize(
    ("artifact", "declared"),
    [
        (_evolving(), ArtifactLifecycle.IMMUTABLE_EVIDENCE),
        (_artifact(), ArtifactLifecycle.EVOLVING_STATE),
        (_ledger(), ArtifactLifecycle.DERIVED_VIEW),
    ],
)
def test_misclassified_lifecycle_is_caught_in_both_directions(
    artifact: ChangedArtifact, declared: ArtifactLifecycle
) -> None:
    """Freezing mutable state and thawing evidence are both misclassifications."""

    report = _audit(
        _receipt(changed_artifacts=(replace(artifact, declared_lifecycle=declared),))
    )
    assert report.verdict is ContractCoverageVerdict.CONTRACT_VIOLATED
    assert _status(report, artifact.path) is ArtifactContractStatus.LIFECYCLE_MISCLASSIFIED


def test_unauthorized_evidence_rewrite_is_a_violation() -> None:
    report = _audit(
        _receipt(changed_artifacts=(_artifact(current_content_sha256="9" * 64),))
    )
    assert report.verdict is ContractCoverageVerdict.CONTRACT_VIOLATED
    assert (
        _status(report, "lane_alpha/01_context/CONTEXT_0001.json")
        is ArtifactContractStatus.UNAUTHORIZED_EVIDENCE_REWRITE
    )


def test_authorized_evidence_rewrite_is_named_not_silently_absorbed() -> None:
    """Authorized, but never invisible: it keeps its own status and reason."""

    report = _audit(
        _receipt(
            changed_artifacts=(
                _artifact(
                    current_content_sha256="9" * 64,
                    evidence_rewrite_authorization_id="authorization::migration::0001",
                ),
            )
        )
    )
    assert report.verdict is ContractCoverageVerdict.COVERAGE_SATISFIED_PROPOSAL_ONLY
    assert (
        _status(report, "lane_alpha/01_context/CONTEXT_0001.json")
        is ArtifactContractStatus.AUTHORIZED_EVIDENCE_REWRITE
    )
    assert (
        "authorized_evidence_rewrite:lane_alpha/01_context/CONTEXT_0001.json"
        in report.reasons
    )


def test_unchanged_immutable_evidence_is_not_reported_as_a_rewrite() -> None:
    report = _audit(_receipt())
    assert (
        _status(report, "lane_alpha/01_context/CONTEXT_0001.json")
        is ArtifactContractStatus.CONTRACT_SATISFIED
    )


# --- could-not-check is never a pass -----------------------------------------


@pytest.mark.parametrize(
    "overrides",
    [
        {"declared_internal_hash": None},
        {"computed_internal_hash": None},
        {"schema_valid": None},
        {"runtime_valid": None},
        {"artifact_event_at_utc": None},
        {"introducing_commit_at_utc": None},
        {"current_content_sha256": None},
        {"artifact_event_at_utc": "2026-08-10T09:00:00+02:00"},
    ],
)
def test_unobserved_evidence_yields_observation_missing_not_a_pass(
    overrides: dict[str, Any],
) -> None:
    report = _audit(_receipt(changed_artifacts=(_artifact(**overrides),)))
    assert report.verdict is ContractCoverageVerdict.CANNOT_CHECK
    assert (
        _status(report, "lane_alpha/01_context/CONTEXT_0001.json")
        is ArtifactContractStatus.OBSERVATION_MISSING
    )
    assert report.permits_strict_process_credit is False


def test_unobserved_ledger_extension_cannot_be_checked() -> None:
    report = _audit(
        _receipt(
            changed_artifacts=(_ledger(current_content_extends_historical=None),)
        )
    )
    assert report.verdict is ContractCoverageVerdict.CANNOT_CHECK
    assert (
        _status(report, "lane_beta/03_trace/TRACE.json")
        is ArtifactContractStatus.OBSERVATION_MISSING
    )


def test_a_real_defect_outranks_an_unobserved_sibling() -> None:
    report = _audit(
        _receipt(
            changed_artifacts=(
                _artifact(computed_internal_hash="9" * 64),
                _ledger(schema_valid=None),
            )
        )
    )
    assert report.verdict is ContractCoverageVerdict.CONTRACT_VIOLATED


# --- receipt integrity -------------------------------------------------------


def test_missing_receipt_fails_closed() -> None:
    report = _audit(None)
    assert report.verdict is ContractCoverageVerdict.CANNOT_CHECK
    assert report.activated is True


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"subject_sha": "nope"}, "subject_sha_invalid"),
        ({"merge_base_sha": "nope"}, "merge_base_sha_invalid"),
        ({"claim_boundary": "  "}, "claim_boundary_missing"),
        ({"subject_repository": ""}, "subject_repository_missing"),
        (
            {"changed_artifacts": (_artifact(), _artifact())},
            "duplicate_changed_path",
        ),
        (
            {"changed_artifacts": (_artifact(historical_content_sha256="short"),)},
            "historical_content_sha256_invalid:lane_alpha/01_context/CONTEXT_0001.json",
        ),
        (
            {
                "changed_artifacts": (),
                "declared_non_artifacts": (DeclaredNonArtifact("docs/x.md", " "),),
            },
            "non_artifact_declared_without_reason:docs/x.md",
        ),
    ],
)
def test_structurally_unbound_receipts_cannot_be_checked(
    overrides: dict[str, Any], reason: str
) -> None:
    report = _audit(_receipt(**overrides))
    assert report.verdict is ContractCoverageVerdict.CANNOT_CHECK
    assert reason in report.reasons


def test_absent_content_hash_cannot_be_checked_but_present_hash_can() -> None:
    unhashed = replace(_receipt(), receipt_canonical_sha256="")
    report = _audit(unhashed)
    assert report.verdict is ContractCoverageVerdict.CANNOT_CHECK
    assert "receipt_canonical_sha256_missing" in report.reasons
    assert _audit(_receipt()).verdict is (
        ContractCoverageVerdict.COVERAGE_SATISFIED_PROPOSAL_ONLY
    )


def test_tampered_content_hash_cannot_be_checked() -> None:
    tampered = replace(_receipt(), subject_repository="github.com/example/other")
    report = _audit(tampered)
    assert report.verdict is ContractCoverageVerdict.CANNOT_CHECK
    assert "receipt_canonical_sha256_mismatch" in report.reasons


def test_content_hash_excludes_only_itself() -> None:
    receipt = _receipt()
    document = receipt.to_dict()
    assert receipt.receipt_canonical_sha256 == receipt_canonical_sha256(document)
    document["subject_repository"] = "github.com/example/other"
    assert receipt_canonical_sha256(document) != receipt.receipt_canonical_sha256


def test_receipt_grants_no_process_credit_or_authority() -> None:
    report = _audit(_receipt())
    assert report.grants_framework_authority is False
    assert report.is_independent_review is False
    document = _receipt().to_dict()
    assert document["grants_strict_process_credit"] is False
    assert document["grants_framework_authority"] is False
    assert document["is_independent_review"] is False


# --- schema ------------------------------------------------------------------


def _schema() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    return json.loads(
        (root / "schemas/artifact-contract-coverage-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_documents_validate_against_the_frozen_schema() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for receipt in (
        _receipt(),
        _receipt(changed_artifacts=(_artifact(), _ledger(), _evolving(), _view())),
        _receipt(
            changed_artifacts=(),
            declared_non_artifacts=(DeclaredNonArtifact("docs/NOTES.md", "prose only"),),
        ),
        _receipt(changed_artifacts=(_artifact(current_content_sha256=None),)),
    ):
        assert list(validator.iter_errors(receipt.to_dict())) == []


@pytest.mark.parametrize(
    "mutator",
    [
        lambda d: d.update(grants_strict_process_credit=True),
        lambda d: d.update(is_independent_review=True),
        lambda d: d["changed_artifacts"][0].update(declared_lifecycle="MUTABLE"),
    ],
)
def test_schema_rejects_credit_claims_and_unknown_lifecycles(mutator: Any) -> None:
    document = _receipt().to_dict()
    mutator(document)
    assert list(Draft202012Validator(_schema()).iter_errors(document)) != []
