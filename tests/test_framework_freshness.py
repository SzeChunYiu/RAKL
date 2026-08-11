"""Frozen planted-world tests for the proposal-only framework freshness receipt.

The three conditions named by the motivating issue are planted explicitly:
a current pin, a stale pin with direct-current-main shadow adoption, and a stale
pin incorrectly treated as authoritative.  Each fail-closed assertion is paired
with a no-alarm assertion so that a checker which always fires would fail here.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]

from rakl.framework_freshness import (
    ApplicationTestBinding,
    CompletenessFreshnessBindingVerdict,
    FrameworkFreshnessReceipt,
    FreshnessExecutionStatus,
    FreshnessVerdict,
    HistoricalReplayCondition,
    InspectedSurface,
    PinRelation,
    audit_completeness_claim_freshness_binding,
    audit_framework_freshness,
    classify_historical_replay,
    receipt_canonical_sha256,
    revalidation_required,
)


PIN_SHA = "15f1c3affe5bf85ba41ff0ab65b25ba19e0d28a3"
MAIN_SHA = "a521d577724dfedb3123e22cdbac457bce4e22f7"
APP_SHA = "d8ac4102285c4ed1ba0fbd5d8818dc4c4731a8cc"

FRAMEWORK_SURFACES = (
    "AGENTS.md",
    "docs/RAKL_V3_EVALUATION.md",
    "src/rakl/v3_runtime.py",
)
V3_FEATURES = ("TaskEpisode telemetry", "saturation vector", "experience substrate")
CLAIM_BOUNDARY = (
    "framework-process telemetry only; performs no submodule update, mints no "
    "method authority, and does not convert a direct-current-main read into a "
    "tested dependency synchronization"
)


def _surfaces(subject_sha: str) -> tuple[InspectedSurface, ...]:
    return tuple(
        InspectedSurface(path=path, subject_sha=subject_sha) for path in FRAMEWORK_SURFACES
    )


def _receipt(**overrides: Any) -> FrameworkFreshnessReceipt:
    values: dict[str, Any] = {
        "application_repository": "github.com/SzeChunYiu/RAKL_math",
        "application_subject_sha": APP_SHA,
        "framework_repository": "github.com/SzeChunYiu/RAKL",
        "framework_pin_sha": PIN_SHA,
        "task_episode_id": "episode::application-cycle::0001",
        "public_trace_event_id": "trace::EXPERIENCE_MEMORY_REVIEW::0001",
        "declared_pin_relation": PinRelation.PIN_BEHIND_CURRENT_MAIN,
        "declared_execution_status": FreshnessExecutionStatus.CURRENT_MAIN_READ_DIRECTLY_SHADOW,
        "claim_boundary": CLAIM_BOUNDARY,
        "observed_current_main_sha": MAIN_SHA,
        "current_main_observed_at_utc": "2026-08-11T09:15:00Z",
        "pin_is_ancestor_of_current_main": True,
        "current_main_is_ancestor_of_pin": False,
        "commits_behind_current_main": 37,
        "commits_ahead_of_current_main": 0,
        "inspected_surfaces": _surfaces(MAIN_SHA),
        "v3_feature_set_claimed_operational": V3_FEATURES,
        "application_pin_updated_in_episode": False,
        "application_test_binding": None,
        "evidence_pointers": ("config/rakl-framework-pin.json", "trace::0001"),
    }
    values.update(overrides)
    return FrameworkFreshnessReceipt(**values).with_content_hash()


def _current_pin_receipt(**overrides: Any) -> FrameworkFreshnessReceipt:
    """Planted world (a): the application pin already equals current main."""

    values: dict[str, Any] = {
        "framework_pin_sha": MAIN_SHA,
        "declared_pin_relation": PinRelation.EQUAL,
        "declared_execution_status": FreshnessExecutionStatus.PIN_CURRENT,
        "pin_is_ancestor_of_current_main": None,
        "current_main_is_ancestor_of_pin": None,
        "commits_behind_current_main": 0,
        "inspected_surfaces": _surfaces(MAIN_SHA),
    }
    values.update(overrides)
    return _receipt(**values)


def _synchronized_receipt(**overrides: Any) -> FrameworkFreshnessReceipt:
    """Planted world (d): the pin was moved to current main and retested."""

    values: dict[str, Any] = {
        "framework_pin_sha": MAIN_SHA,
        "declared_pin_relation": PinRelation.EQUAL,
        "declared_execution_status": FreshnessExecutionStatus.PIN_SYNCHRONIZED_AND_TESTED,
        "pin_is_ancestor_of_current_main": None,
        "current_main_is_ancestor_of_pin": None,
        "commits_behind_current_main": 0,
        "application_pin_updated_in_episode": True,
        "application_test_binding": ApplicationTestBinding(
            framework_subject_sha=MAIN_SHA,
            application_subject_sha=APP_SHA,
            command="pytest tests/",
            run_reference="run::application-suite::0001",
            complete_suite=True,
            passed=True,
        ),
    }
    values.update(overrides)
    return _receipt(**values)


# --- planted world (a): current pin -----------------------------------------


def test_current_pin_world_is_recorded_cleanly() -> None:
    report = audit_framework_freshness(_current_pin_receipt())
    assert report.verdict is FreshnessVerdict.RECORDED_PROPOSAL_ONLY
    assert report.effective_status is FreshnessExecutionStatus.PIN_CURRENT
    assert report.derived_pin_relation is PinRelation.EQUAL
    assert report.permits_dependency_synchronization_claim is False


# --- planted world (b): stale pin, direct current-main shadow read -----------


def test_stale_pin_with_direct_current_main_read_is_shadow_adoption() -> None:
    report = audit_framework_freshness(_receipt())
    assert report.verdict is FreshnessVerdict.RECORDED_PROPOSAL_ONLY
    assert (
        report.effective_status
        is FreshnessExecutionStatus.CURRENT_MAIN_READ_DIRECTLY_SHADOW
    )
    assert report.derived_pin_relation is PinRelation.PIN_BEHIND_CURRENT_MAIN
    assert report.permits_dependency_synchronization_claim is False


def test_shadow_read_cannot_be_implicitly_upgraded_to_synchronization() -> None:
    report = audit_framework_freshness(
        _receipt(
            declared_execution_status=FreshnessExecutionStatus.PIN_SYNCHRONIZED_AND_TESTED
        )
    )
    assert report.verdict is FreshnessVerdict.REFUTED_CLAIM
    assert "declared_status_upgrades_evidence" in report.reasons
    assert (
        report.effective_status
        is FreshnessExecutionStatus.CURRENT_MAIN_READ_DIRECTLY_SHADOW
    )
    assert report.permits_dependency_synchronization_claim is False


# --- planted world (c): stale pin treated as authoritative -------------------


def test_stale_pin_treated_as_authoritative_is_refuted() -> None:
    report = audit_framework_freshness(
        _receipt(
            declared_pin_relation=PinRelation.EQUAL,
            declared_execution_status=FreshnessExecutionStatus.PIN_CURRENT,
            inspected_surfaces=_surfaces(PIN_SHA),
        )
    )
    assert report.verdict is FreshnessVerdict.REFUTED_CLAIM
    assert (
        report.effective_status
        is FreshnessExecutionStatus.STALE_PIN_TREATED_AS_AUTHORITATIVE
    )
    assert "declared_pin_relation_contradicts_observation" in report.reasons
    assert "declared_status_upgrades_evidence" in report.reasons


def test_surfaces_read_at_the_stale_pin_are_not_a_current_main_read() -> None:
    report = audit_framework_freshness(
        _receipt(
            declared_execution_status=FreshnessExecutionStatus.STALE_PIN_TREATED_AS_AUTHORITATIVE,
            inspected_surfaces=_surfaces(PIN_SHA),
        )
    )
    assert (
        report.effective_status
        is FreshnessExecutionStatus.STALE_PIN_TREATED_AS_AUTHORITATIVE
    )


def test_honestly_declared_stale_pin_defect_is_preserved_not_refuted() -> None:
    """Negative history is a valid receipt; the defect rides in the status."""

    report = audit_framework_freshness(
        _receipt(
            declared_execution_status=FreshnessExecutionStatus.STALE_PIN_TREATED_AS_AUTHORITATIVE,
            inspected_surfaces=(),
        )
    )
    assert report.verdict is FreshnessVerdict.RECORDED_PROPOSAL_ONLY
    assert (
        report.effective_status
        is FreshnessExecutionStatus.STALE_PIN_TREATED_AS_AUTHORITATIVE
    )
    assert report.permits_dependency_synchronization_claim is False


# --- fail-closed: missing current-main observation ---------------------------


@pytest.mark.parametrize(
    "overrides",
    [
        {"observed_current_main_sha": None},
        {"current_main_observed_at_utc": None},
        {"pin_is_ancestor_of_current_main": None},
        {"current_main_is_ancestor_of_pin": None},
    ],
)
def test_missing_current_main_observation_never_defaults_to_pin_current(
    overrides: dict[str, Any],
) -> None:
    report = audit_framework_freshness(_receipt(**overrides))
    assert report.verdict is FreshnessVerdict.CANNOT_CHECK
    assert report.effective_status is FreshnessExecutionStatus.CURRENT_MAIN_UNOBSERVED
    assert report.effective_status is not FreshnessExecutionStatus.PIN_CURRENT
    assert report.derived_pin_relation is PinRelation.UNOBSERVED


def test_observed_current_main_is_not_reported_as_unobserved() -> None:
    report = audit_framework_freshness(_receipt())
    assert report.effective_status is not FreshnessExecutionStatus.CURRENT_MAIN_UNOBSERVED


# --- fail-closed: missing application-test binding ---------------------------


def test_synchronization_without_test_binding_fails_closed() -> None:
    report = audit_framework_freshness(_synchronized_receipt(application_test_binding=None))
    assert report.verdict is FreshnessVerdict.CANNOT_CHECK
    assert (
        report.effective_status
        is FreshnessExecutionStatus.APPLICATION_TEST_BINDING_MISSING
    )
    assert report.permits_dependency_synchronization_claim is False


@pytest.mark.parametrize(
    "binding_overrides",
    [
        {"framework_subject_sha": PIN_SHA},
        {"application_subject_sha": "0" * 40},
    ],
)
def test_test_binding_pointing_at_another_subject_fails_closed(
    binding_overrides: dict[str, Any],
) -> None:
    base = _synchronized_receipt()
    assert base.application_test_binding is not None
    report = audit_framework_freshness(
        _synchronized_receipt(
            application_test_binding=replace(
                base.application_test_binding, **binding_overrides
            )
        )
    )
    assert report.verdict is FreshnessVerdict.CANNOT_CHECK
    assert (
        report.effective_status
        is FreshnessExecutionStatus.APPLICATION_TEST_BINDING_MISSING
    )


def test_complete_tested_synchronization_passes_and_licenses_the_claim() -> None:
    report = audit_framework_freshness(_synchronized_receipt())
    assert report.verdict is FreshnessVerdict.RECORDED_PROPOSAL_ONLY
    assert report.effective_status is FreshnessExecutionStatus.PIN_SYNCHRONIZED_AND_TESTED
    assert report.permits_dependency_synchronization_claim is True


@pytest.mark.parametrize(
    "binding_overrides", [{"complete_suite": False}, {"passed": False}]
)
def test_untested_synchronization_is_checked_and_distinct_from_unchecked(
    binding_overrides: dict[str, Any],
) -> None:
    base = _synchronized_receipt()
    assert base.application_test_binding is not None
    receipt = _synchronized_receipt(
        declared_execution_status=(
            FreshnessExecutionStatus.PIN_SYNCHRONIZED_WITHOUT_APPLICATION_TESTS
        ),
        application_test_binding=replace(
            base.application_test_binding, **binding_overrides
        ),
    )
    report = audit_framework_freshness(receipt)
    assert report.verdict is FreshnessVerdict.RECORDED_PROPOSAL_ONLY
    assert (
        report.effective_status
        is FreshnessExecutionStatus.PIN_SYNCHRONIZED_WITHOUT_APPLICATION_TESTS
    )
    assert (
        report.effective_status
        is not FreshnessExecutionStatus.APPLICATION_TEST_BINDING_MISSING
    )
    assert report.permits_dependency_synchronization_claim is False


def test_untested_synchronization_cannot_declare_itself_tested() -> None:
    base = _synchronized_receipt()
    assert base.application_test_binding is not None
    report = audit_framework_freshness(
        _synchronized_receipt(
            application_test_binding=replace(base.application_test_binding, passed=False)
        )
    )
    assert report.verdict is FreshnessVerdict.REFUTED_CLAIM
    assert "declared_status_upgrades_evidence" in report.reasons


# --- receipt integrity -------------------------------------------------------


def test_missing_receipt_fails_closed() -> None:
    report = audit_framework_freshness(None)
    assert report.verdict is FreshnessVerdict.CANNOT_CHECK
    assert report.effective_status is FreshnessExecutionStatus.RECEIPT_UNVERIFIABLE


def test_absent_content_hash_cannot_be_checked_but_present_hash_can() -> None:
    unhashed = replace(_receipt(), receipt_canonical_sha256="")
    unchecked = audit_framework_freshness(unhashed)
    assert unchecked.verdict is FreshnessVerdict.CANNOT_CHECK
    assert "receipt_canonical_sha256_missing" in unchecked.reasons
    assert audit_framework_freshness(_receipt()).verdict is (
        FreshnessVerdict.RECORDED_PROPOSAL_ONLY
    )


def test_tampered_content_hash_is_refuted_not_merely_unchecked() -> None:
    tampered = replace(_receipt(), task_episode_id="episode::rewritten")
    report = audit_framework_freshness(tampered)
    assert report.verdict is FreshnessVerdict.REFUTED_CLAIM
    assert "receipt_canonical_sha256_mismatch" in report.reasons


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"application_subject_sha": "not-a-sha"}, "application_subject_sha_invalid"),
        ({"framework_pin_sha": "zz"}, "framework_pin_sha_invalid"),
        (
            {"current_main_observed_at_utc": "2026-08-11T09:15:00+02:00"},
            "current_main_observed_at_utc_not_utc",
        ),
        ({"claim_boundary": "  "}, "claim_boundary_missing"),
        ({"task_episode_id": ""}, "task_episode_id_missing"),
        ({"public_trace_event_id": ""}, "public_trace_event_id_missing"),
        ({"evidence_pointers": ()}, "evidence_pointers_missing"),
    ],
)
def test_structurally_unbound_receipts_cannot_be_checked(
    overrides: dict[str, Any], reason: str
) -> None:
    report = audit_framework_freshness(_receipt(**overrides))
    assert report.verdict is FreshnessVerdict.CANNOT_CHECK
    assert report.effective_status is FreshnessExecutionStatus.RECEIPT_UNVERIFIABLE
    assert reason in report.reasons


def test_adoption_without_a_named_feature_set_cannot_be_checked() -> None:
    report = audit_framework_freshness(_receipt(v3_feature_set_claimed_operational=()))
    assert report.verdict is FreshnessVerdict.CANNOT_CHECK
    assert "adoption_recorded_without_naming_the_operational_feature_set" in report.reasons


def test_diverged_pin_is_classified_rather_than_silently_accepted() -> None:
    report = audit_framework_freshness(
        _receipt(
            declared_pin_relation=PinRelation.DIVERGED,
            pin_is_ancestor_of_current_main=False,
            current_main_is_ancestor_of_pin=False,
        )
    )
    assert report.derived_pin_relation is PinRelation.DIVERGED
    assert report.verdict is FreshnessVerdict.RECORDED_PROPOSAL_ONLY


def test_receipt_object_mints_no_authority() -> None:
    report = audit_framework_freshness(_synchronized_receipt())
    assert report.grants_method_authority is False
    assert report.performs_submodule_update is False
    document = _synchronized_receipt().to_dict()
    assert document["performs_submodule_update"] is False
    assert document["grants_method_authority"] is False
    assert document["grants_application_mathematical_authority"] is False


# --- revalidation trigger ----------------------------------------------------


def test_unchanged_watched_subjects_do_not_trigger_revalidation() -> None:
    report = revalidation_required(
        _receipt(),
        observed_application_subject_sha=APP_SHA,
        observed_framework_pin_sha=PIN_SHA,
        observed_framework_main_sha=MAIN_SHA,
    )
    assert report.required is False
    assert report.changed_subjects == ()


@pytest.mark.parametrize(
    ("observed", "changed"),
    [
        ({"observed_application_subject_sha": "1" * 40}, "application_subject_sha"),
        ({"observed_framework_pin_sha": "2" * 40}, "framework_pin_sha"),
        ({"observed_framework_main_sha": "3" * 40}, "framework_main_sha"),
    ],
)
def test_each_watched_subject_triggers_revalidation(
    observed: dict[str, Any], changed: str
) -> None:
    kwargs: dict[str, Any] = {
        "observed_application_subject_sha": APP_SHA,
        "observed_framework_pin_sha": PIN_SHA,
        "observed_framework_main_sha": MAIN_SHA,
    }
    kwargs.update(observed)
    report = revalidation_required(_receipt(), **kwargs)
    assert report.required is True
    assert changed in report.changed_subjects


def test_unobservable_subject_triggers_revalidation_rather_than_assuming_unchanged() -> None:
    report = revalidation_required(
        _receipt(),
        observed_application_subject_sha=APP_SHA,
        observed_framework_pin_sha=PIN_SHA,
        observed_framework_main_sha=None,
    )
    assert report.required is True
    assert "framework_main_sha_not_re_observed" in report.reasons


def test_receipt_that_never_bound_current_main_always_needs_revalidation() -> None:
    report = revalidation_required(
        _receipt(observed_current_main_sha=None),
        observed_application_subject_sha=APP_SHA,
        observed_framework_pin_sha=PIN_SHA,
        observed_framework_main_sha=MAIN_SHA,
    )
    assert report.required is True
    assert "framework_main_sha_was_never_bound_by_the_receipt" in report.reasons


# --- schema ------------------------------------------------------------------


def test_receipt_documents_validate_against_the_frozen_schema() -> None:
    root = Path(__file__).resolve().parents[1]
    schema = json.loads(
        (root / "schemas/framework-freshness-receipt-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for receipt in (
        _receipt(),
        _current_pin_receipt(),
        _synchronized_receipt(),
        _receipt(observed_current_main_sha=None, current_main_observed_at_utc=None),
    ):
        assert list(validator.iter_errors(receipt.to_dict())) == []


def test_schema_rejects_a_receipt_that_claims_authority() -> None:
    root = Path(__file__).resolve().parents[1]
    schema = json.loads(
        (root / "schemas/framework-freshness-receipt-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = Draft202012Validator(schema)
    document = _receipt().to_dict()
    document["grants_method_authority"] = True
    assert list(validator.iter_errors(document)) != []


def test_content_hash_excludes_only_itself() -> None:
    receipt = _receipt()
    document = receipt.to_dict()
    assert receipt.receipt_canonical_sha256 == receipt_canonical_sha256(document)
    document["task_episode_id"] = "episode::other"
    assert receipt_canonical_sha256(document) != receipt.receipt_canonical_sha256


# --- completeness-claim prerequisite: bind current-main + pin relation -------


def test_bound_pin_mismatch_licenses_completeness_claim_prerequisite() -> None:
    report = audit_completeness_claim_freshness_binding(_receipt())
    assert report.verdict is CompletenessFreshnessBindingVerdict.BOUND_PROPOSAL_ONLY
    assert report.permits_completeness_claim is True
    assert report.derived_pin_relation is PinRelation.PIN_BEHIND_CURRENT_MAIN
    assert report.observed_current_main_sha == MAIN_SHA
    assert any("mismatch is bound" in reason for reason in report.reasons)
    freshness = audit_framework_freshness(_receipt())
    assert freshness.permits_completeness_claim is True
    assert freshness.pin_mismatch_bound is True
    assert freshness.current_main_sha_bound is True


def test_current_pin_also_licenses_completeness_claim_prerequisite() -> None:
    report = audit_completeness_claim_freshness_binding(_current_pin_receipt())
    assert report.verdict is CompletenessFreshnessBindingVerdict.BOUND_PROPOSAL_ONLY
    assert report.permits_completeness_claim is True
    assert report.derived_pin_relation is PinRelation.EQUAL
    freshness = audit_framework_freshness(_current_pin_receipt())
    assert freshness.pin_mismatch_bound is False
    assert freshness.pin_relation_bound is True


def test_honest_stale_pin_defect_still_binds_mismatch_for_completeness() -> None:
    """Defect rides in adoption status; the mismatch itself remains bound."""

    receipt = _receipt(
        declared_execution_status=FreshnessExecutionStatus.STALE_PIN_TREATED_AS_AUTHORITATIVE,
        inspected_surfaces=(),
    )
    report = audit_completeness_claim_freshness_binding(receipt)
    assert report.verdict is CompletenessFreshnessBindingVerdict.BOUND_PROPOSAL_ONLY
    assert (
        report.effective_status
        is FreshnessExecutionStatus.STALE_PIN_TREATED_AS_AUTHORITATIVE
    )
    assert report.derived_pin_relation is PinRelation.PIN_BEHIND_CURRENT_MAIN


def test_missing_current_main_sha_blocks_completeness_claim() -> None:
    report = audit_completeness_claim_freshness_binding(
        _receipt(observed_current_main_sha=None)
    )
    assert (
        report.verdict
        is CompletenessFreshnessBindingVerdict.REJECTED_UNBOUND_CURRENT_MAIN
    )
    assert report.permits_completeness_claim is False
    assert audit_framework_freshness(
        _receipt(observed_current_main_sha=None)
    ).permits_completeness_claim is False


def test_named_main_without_ancestry_blocks_as_unbound_pin_relation() -> None:
    """Main SHA alone is not a pin relation; mismatch must be derived."""

    report = audit_completeness_claim_freshness_binding(
        _receipt(
            pin_is_ancestor_of_current_main=None,
            current_main_is_ancestor_of_pin=None,
        )
    )
    assert (
        report.verdict
        is CompletenessFreshnessBindingVerdict.REJECTED_UNBOUND_PIN_RELATION
    )
    assert report.permits_completeness_claim is False
    assert report.observed_current_main_sha == MAIN_SHA


def test_refuted_freshness_receipt_blocks_completeness_claim() -> None:
    report = audit_completeness_claim_freshness_binding(
        _receipt(
            declared_execution_status=FreshnessExecutionStatus.PIN_SYNCHRONIZED_AND_TESTED
        )
    )
    assert (
        report.verdict is CompletenessFreshnessBindingVerdict.REJECTED_FRESHNESS_REFUTED
    )
    assert report.permits_completeness_claim is False


def test_missing_freshness_receipt_blocks_completeness_claim() -> None:
    report = audit_completeness_claim_freshness_binding(None)
    assert (
        report.verdict
        is CompletenessFreshnessBindingVerdict.REJECTED_FRESHNESS_RECEIPT_UNVERIFIABLE
    )
    assert report.permits_completeness_claim is False


# --- historical replay of the three planted worlds ---------------------------


def test_historical_replay_classifies_the_three_planted_worlds() -> None:
    current = classify_historical_replay(_current_pin_receipt())
    shadow = classify_historical_replay(_receipt())
    stale = classify_historical_replay(
        _receipt(
            declared_execution_status=FreshnessExecutionStatus.STALE_PIN_TREATED_AS_AUTHORITATIVE,
            inspected_surfaces=(),
        )
    )
    assert current.condition is HistoricalReplayCondition.CURRENT_PIN
    assert shadow.condition is HistoricalReplayCondition.STALE_PIN_SHADOW_ADOPTION
    assert (
        stale.condition
        is HistoricalReplayCondition.STALE_PIN_TREATED_AS_AUTHORITATIVE
    )
    assert current.classified and shadow.classified and stale.classified


def test_historical_replay_fails_closed_when_current_main_unobserved() -> None:
    report = classify_historical_replay(_receipt(observed_current_main_sha=None))
    assert report.condition is HistoricalReplayCondition.UNCLASSIFIED
    assert report.classified is False
    assert (
        report.freshness.effective_status
        is FreshnessExecutionStatus.CURRENT_MAIN_UNOBSERVED
    )


def test_historical_replay_fails_closed_when_sync_test_binding_missing() -> None:
    report = classify_historical_replay(
        _synchronized_receipt(application_test_binding=None)
    )
    assert report.condition is HistoricalReplayCondition.UNCLASSIFIED
    assert (
        report.freshness.effective_status
        is FreshnessExecutionStatus.APPLICATION_TEST_BINDING_MISSING
    )
