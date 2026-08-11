"""Frozen hostile-world tests for the proposal-only pre-action fibre receipt.

The four worlds named by the motivating issue are planted explicitly:

1. a relevant item exists but is omitted from the fibre;
2. a pending/noncanonical artifact is retrieved and must not acquire authority;
3. the agent changes the discriminator after seeing the result;
4. the action is genuinely cheap and must not incur disproportionate ceremony.

World 4 is the mandatory no-alarm control.  Every fail-closed assertion here is
paired with a positive control, because a checker that rejects everything is
worth less than no checker at all: it gets switched off after its first real run.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]

from rakl.experience_substrate import EpisodeOutcome, TaskEpisode
from rakl.pre_action_receipt import (
    ActionConsequence,
    EpisodeChronologyStatus,
    ObservedActionEffects,
    PreActionFibreReceipt,
    RetrievalAuthority,
    RetrievalBinding,
    RetrievalDisposition,
    audit_pre_action_chronology,
    receipt_canonical_sha256,
)


FRAMEWORK_SHA = "bd1a2768f0f474ff44ffa25243241f94bfaf6466"
APP_SHA = "6557b1b25fa839fe71aba8047c958d5da892edd8"
FIBRE_SNAPSHOT = "f" * 64
CONTEXT_HASH = "c" * 64

SELECT_TIME = "2026-08-11T09:00:00Z"
EXECUTE_TIME = "2026-08-11T09:04:00Z"

NO_MUTATION = ObservedActionEffects(
    mutated_candidate_state=False,
    mutated_lesson_state=False,
    mutated_tool_state=False,
    mutated_route_state=False,
)
CANDIDATE_MUTATED = ObservedActionEffects(
    mutated_candidate_state=True,
    mutated_lesson_state=False,
    mutated_tool_state=False,
    mutated_route_state=False,
)
EFFECTS_UNOBSERVED = ObservedActionEffects(
    mutated_candidate_state=None,
    mutated_lesson_state=False,
    mutated_tool_state=False,
    mutated_route_state=False,
)


def make_receipt(**overrides: Any) -> PreActionFibreReceipt:
    base = PreActionFibreReceipt(
        framework_repository="SzeChunYiu/RAKL",
        framework_commit=FRAMEWORK_SHA,
        application_repository="SzeChunYiu/RAKL_math",
        application_revision=APP_SHA,
        task_id="TASK-NS-B2a",
        atom_id="ATOM-ancient-euler-scaling",
        context_hash=CONTEXT_HASH,
        fibre_snapshot_hash=FIBRE_SNAPSHOT,
        operator_id="OP-scaling-discriminator",
        predeclared_discriminator="F=1 ancient-Euler scaling admits no self-similar core",
        allowed_outcome_branches=("SCALING_EXCLUDED", "SCALING_SURVIVES", "INCONCLUSIVE"),
        timestamp=SELECT_TIME,
        sequence_index=7,
        public_trace_event_id="TRACE-0041",
        declared_consequence=ActionConsequence.CONSEQUENTIAL,
        retrieval_bindings=(
            RetrievalBinding(
                retrieval_id="RET-canonical-1",
                disposition=RetrievalDisposition.SELECTED,
                authority=RetrievalAuthority.CANONICAL,
                evidence_pointer="evidence://canonical-1",
            ),
            RetrievalBinding(
                retrieval_id="RET-rejected-1",
                disposition=RetrievalDisposition.RELEVANT_BUT_REJECTED,
                authority=RetrievalAuthority.CANONICAL,
                rejection_reason="compactness assumption absent in target context",
                evidence_pointer="evidence://rejected-1",
            ),
        ),
        authority_bearing_retrieval_ids=("RET-canonical-1",),
        coverage_receipt_id="COV-0009",
        evidence_pointers=("evidence://selection-packet",),
    )
    return replace(base, **overrides).with_content_hash()


def make_episode(**overrides: Any) -> TaskEpisode:
    base = TaskEpisode(
        episode_id="EP-0007",
        task_id="TASK-NS-B2a",
        atom_id="ATOM-ancient-euler-scaling",
        context_hash=CONTEXT_HASH,
        problem_signature=("navier_stokes", "scaling"),
        fibre_snapshot_hash=FIBRE_SNAPSHOT,
        operator_ids=("OP-scaling-discriminator",),
        action_trace=("ran scaling discriminator",),
        observation_ids=("OBS-1",),
        verification_ids=("VER-1",),
        outcome=EpisodeOutcome.PARTIAL_SUCCESS,
        residual_signature=("far_field_escape_open",),
        evidence_pointers=("evidence://result",),
        artifact_hash="a" * 64,
        timestamp=EXECUTE_TIME,
        cost=1.0,
    )
    return replace(base, **overrides)


def audit(
    receipt: PreActionFibreReceipt | None,
    episode: TaskEpisode | None = None,
    **kwargs: Any,
):
    params: dict[str, Any] = {
        "declared_consequence": ActionConsequence.CONSEQUENTIAL,
        "observed_effects": CANDIDATE_MUTATED,
        "observed_outcome_branch": "SCALING_SURVIVES",
    }
    params.update(kwargs)
    return audit_pre_action_chronology(
        receipt, episode if episode is not None else make_episode(), **params
    )


# --- positive control ---------------------------------------------------------


def test_a_bound_receipt_that_precedes_its_episode_is_prospectively_bound() -> None:
    report = audit(make_receipt())
    assert report.status is EpisodeChronologyStatus.PROSPECTIVELY_BOUND
    assert report.satisfies_prospective_gate is True
    assert report.receipt_required is True


def test_the_bound_case_reports_no_defect_reason() -> None:
    """No-alarm control for the whole consequential path."""

    report = audit(make_receipt())
    joined = " ".join(report.reasons)
    for alarm in ("mismatch", "not_predeclared", "differs", "after_the_episode"):
        assert alarm not in joined


# --- load-bearing behaviour: retrospective status is unavoidable --------------


def test_a_consequential_episode_without_a_receipt_is_retrospective_only() -> None:
    report = audit(None)
    assert report.status is EpisodeChronologyStatus.RETROSPECTIVE_ONLY
    assert report.satisfies_prospective_gate is False
    assert "no_pre_action_fibre_receipt_precedes_this_episode" in report.reasons


def test_an_unclassified_action_is_treated_as_consequential() -> None:
    """Declining to classify must buy nothing."""

    report = audit(None, declared_consequence=ActionConsequence.UNCLASSIFIED)
    assert report.status is EpisodeChronologyStatus.RETROSPECTIVE_ONLY
    assert "unclassified_action_treated_as_consequential" in report.reasons
    assert report.receipt_required is True


def test_a_retrospective_episode_stays_usable_for_learning() -> None:
    """The acceptance boundary: downgraded, not discarded."""

    report = audit(None)
    assert report.usable_for_search_priority is True
    assert report.usable_for_failure_learning is True


def test_a_prospectively_bound_episode_is_also_usable_for_learning() -> None:
    report = audit(make_receipt())
    assert report.usable_for_search_priority is True
    assert report.usable_for_failure_learning is True


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("atom_id", "ATOM-something-else"),
        ("context_hash", "d" * 64),
        ("fibre_snapshot_hash", "e" * 64),
        ("task_id", "TASK-OTHER"),
        ("operator_id", "OP-unrelated"),
    ],
)
def test_a_receipt_bound_to_a_different_selection_does_not_rescue_the_episode(
    field_name: str, value: str
) -> None:
    report = audit(make_receipt(**{field_name: value}))
    assert report.status is EpisodeChronologyStatus.RETROSPECTIVE_ONLY
    assert report.satisfies_prospective_gate is False
    assert "no_receipt_binds_this_exact_episode" in report.reasons


def test_a_receipt_dated_after_its_episode_is_a_refuted_backfill() -> None:
    report = audit(make_receipt(timestamp="2026-08-11T09:09:00Z"))
    assert report.status is EpisodeChronologyStatus.REFUTED_CLAIM
    assert report.satisfies_prospective_gate is False
    assert any("timestamped_after" in reason for reason in report.reasons)


def test_a_receipt_simultaneous_with_its_episode_is_not_strictly_earlier() -> None:
    report = audit(make_receipt(timestamp=EXECUTE_TIME))
    assert report.status is EpisodeChronologyStatus.RETROSPECTIVE_ONLY
    assert "receipt_is_not_strictly_earlier_than_the_episode" in report.reasons


def test_a_tampered_receipt_is_refuted_not_merely_downgraded() -> None:
    """Editing a frozen receipt must be visible, not silently accepted."""

    honest = make_receipt()
    tampered = replace(
        honest, predeclared_discriminator="whatever the result turned out to be"
    )
    report = audit(tampered)
    assert report.status is EpisodeChronologyStatus.REFUTED_CLAIM
    assert any("content_hash" in reason for reason in report.reasons)


# --- hostile world 1: a relevant item exists but is omitted from the fibre ----


def test_the_receipt_never_claims_the_fibre_search_universe_was_complete() -> None:
    """An omitted relevant item is a coverage defect, not a chronology defect.

    The receipt must not let the omission be laundered into completeness, so the
    disclaimer is emitted on the bound path, where the temptation exists.
    """

    report = audit(make_receipt())
    assert report.status is EpisodeChronologyStatus.PROSPECTIVELY_BOUND
    assert report.claims_fibre_search_universe_complete is False
    assert (
        "fibre_search_universe_completeness_is_not_claimed_by_this_receipt"
        in report.reasons
    )
    assert make_receipt().to_dict()["claims_fibre_search_universe_complete"] is False


def test_a_missing_coverage_receipt_is_reported_not_silently_treated_as_coverage() -> None:
    report = audit(make_receipt(coverage_receipt_id=None))
    assert report.status is EpisodeChronologyStatus.PROSPECTIVELY_BOUND
    assert (
        "no_coverage_receipt_referenced_universe_completeness_remains_unbound"
        in report.reasons
    )


def test_relevant_but_rejected_retrievals_are_surfaced_by_the_report() -> None:
    """Recording what was rejected is how an omission becomes visible at all."""

    report = audit(make_receipt())
    assert report.relevant_but_rejected_retrieval_ids == ("RET-rejected-1",)


def test_a_rejected_retrieval_without_a_reason_cannot_be_checked() -> None:
    receipt = make_receipt(
        retrieval_bindings=(
            RetrievalBinding(
                retrieval_id="RET-rejected-1",
                disposition=RetrievalDisposition.RELEVANT_BUT_REJECTED,
                authority=RetrievalAuthority.CANONICAL,
                rejection_reason="",
                evidence_pointer="evidence://rejected-1",
            ),
        ),
        authority_bearing_retrieval_ids=(),
    )
    report = audit(receipt)
    assert report.status is EpisodeChronologyStatus.CANNOT_CHECK
    assert "relevant_but_rejected_retrieval_without_reason" in report.reasons


# --- hostile world 2: a pending artifact must not acquire authority ----------


PENDING_BINDING = RetrievalBinding(
    retrieval_id="RET-pending-1",
    disposition=RetrievalDisposition.SELECTED,
    authority=RetrievalAuthority.PENDING,
    evidence_pointer="evidence://pending-1",
)


def test_claiming_authority_for_a_pending_retrieval_is_refuted() -> None:
    receipt = make_receipt(
        retrieval_bindings=(PENDING_BINDING,),
        authority_bearing_retrieval_ids=("RET-pending-1",),
    )
    report = audit(receipt)
    assert report.status is EpisodeChronologyStatus.REFUTED_CLAIM
    assert any(
        "noncanonical_or_pending_retrieval" in reason for reason in report.reasons
    )


def test_reading_a_pending_retrieval_without_claiming_authority_is_allowed() -> None:
    """No-alarm control: retrieval is not endorsement."""

    receipt = make_receipt(
        retrieval_bindings=make_receipt().retrieval_bindings + (PENDING_BINDING,),
        authority_bearing_retrieval_ids=("RET-canonical-1",),
    )
    report = audit(receipt)
    assert report.status is EpisodeChronologyStatus.PROSPECTIVELY_BOUND
    assert report.non_authoritative_selected_retrieval_ids == ("RET-pending-1",)


def test_authority_claimed_for_an_unselected_retrieval_is_refuted() -> None:
    receipt = make_receipt(authority_bearing_retrieval_ids=("RET-rejected-1",))
    report = audit(receipt)
    assert report.status is EpisodeChronologyStatus.REFUTED_CLAIM
    assert any("was_not_selected" in reason for reason in report.reasons)


def test_an_observer_contradicting_the_declared_authority_refutes_the_receipt() -> None:
    report = audit(
        make_receipt(),
        observed_retrieval_authorities={"RET-canonical-1": RetrievalAuthority.PENDING},
    )
    assert report.status is EpisodeChronologyStatus.REFUTED_CLAIM
    assert any(
        "contradicted_by_observation" in reason for reason in report.reasons
    )


def test_an_observer_agreeing_with_the_declared_authority_raises_no_alarm() -> None:
    report = audit(
        make_receipt(),
        observed_retrieval_authorities={
            "RET-canonical-1": RetrievalAuthority.CANONICAL
        },
    )
    assert report.status is EpisodeChronologyStatus.PROSPECTIVELY_BOUND


# --- hostile world 3: the discriminator changes after the result -------------


def test_an_outcome_branch_that_was_not_predeclared_is_refuted() -> None:
    report = audit(make_receipt(), observed_outcome_branch="ACTUALLY_A_DIFFERENT_WIN")
    assert report.status is EpisodeChronologyStatus.REFUTED_CLAIM
    assert report.satisfies_prospective_gate is False
    assert "observed_outcome_branch_was_not_predeclared" in report.reasons


def test_a_reported_discriminator_differing_from_the_predeclared_one_is_refuted() -> None:
    report = audit(
        make_receipt(),
        observed_discriminator="whichever test the result happened to pass",
    )
    assert report.status is EpisodeChronologyStatus.REFUTED_CLAIM
    assert any("differs_from_the_predeclared" in r for r in report.reasons)


def test_an_unchanged_discriminator_raises_no_alarm() -> None:
    receipt = make_receipt()
    report = audit(
        receipt, observed_discriminator=receipt.predeclared_discriminator
    )
    assert report.status is EpisodeChronologyStatus.PROSPECTIVELY_BOUND


@pytest.mark.parametrize(
    "branch", ["SCALING_EXCLUDED", "SCALING_SURVIVES", "INCONCLUSIVE"]
)
def test_every_predeclared_branch_is_accepted(branch: str) -> None:
    """A predeclared falsifier must accept its own losing branch."""

    report = audit(make_receipt(), observed_outcome_branch=branch)
    assert report.status is EpisodeChronologyStatus.PROSPECTIVELY_BOUND


# --- hostile world 4: the mandatory no-alarm control -------------------------


def test_a_genuinely_cheap_action_needs_no_receipt() -> None:
    report = audit(
        None,
        declared_consequence=ActionConsequence.NON_CONSEQUENTIAL_DECLARED,
        observed_effects=NO_MUTATION,
    )
    assert report.status is EpisodeChronologyStatus.NON_CONSEQUENTIAL_NO_RECEIPT_REQUIRED
    assert report.receipt_required is False


def test_a_cheap_action_emits_no_reason_demanding_ceremony() -> None:
    """`receipt_required is False` must be distinct from 'required and missing'."""

    report = audit(
        None,
        declared_consequence=ActionConsequence.NON_CONSEQUENTIAL_DECLARED,
        observed_effects=NO_MUTATION,
    )
    joined = " ".join(report.reasons)
    assert "receipt" not in joined
    assert "retrospective" not in joined
    assert report.reasons == (
        "no_governed_state_mutation_observed",
        "cheap_action_owes_no_chronology_ceremony",
    )


def test_a_cheap_action_still_does_not_satisfy_a_prospective_gate() -> None:
    """Cheapness excuses ceremony; it does not mint prospective credit."""

    report = audit(
        None,
        declared_consequence=ActionConsequence.NON_CONSEQUENTIAL_DECLARED,
        observed_effects=NO_MUTATION,
    )
    assert report.satisfies_prospective_gate is False


# --- the classifier is a trust surface, and it is closed ---------------------


def test_a_declared_cheap_action_that_mutated_state_is_refuted() -> None:
    """Misclassification must not be a bypass."""

    report = audit(
        None,
        declared_consequence=ActionConsequence.NON_CONSEQUENTIAL_DECLARED,
        observed_effects=CANDIDATE_MUTATED,
    )
    assert report.status is EpisodeChronologyStatus.REFUTED_CLAIM
    assert (
        "action_declared_non_consequential_mutated_governed_state" in report.reasons
    )
    assert report.receipt_required is True


def test_unobserved_effects_fail_closed_rather_than_reading_as_harmless() -> None:
    report = audit(
        None,
        declared_consequence=ActionConsequence.NON_CONSEQUENTIAL_DECLARED,
        observed_effects=EFFECTS_UNOBSERVED,
    )
    assert report.status is EpisodeChronologyStatus.CANNOT_CHECK
    assert report.satisfies_prospective_gate is False
    assert "unobserved:candidate_state" in report.reasons


# --- authority and completeness are never minted -----------------------------


@pytest.mark.parametrize(
    "receipt_factory, kwargs",
    [
        (lambda: make_receipt(), {}),
        (lambda: None, {}),
    ],
)
def test_no_report_grants_authority(receipt_factory: Any, kwargs: Any) -> None:
    report = audit(receipt_factory(), **kwargs)
    assert report.grants_proof_authority is False
    assert report.grants_lesson_authority is False
    assert report.grants_tool_authority is False
    assert report.grants_gluing_authority is False
    assert report.grants_theorem_authority is False
    assert report.grants_review_independence is False
    assert report.grants_framework_authority is False
    assert report.claims_fibre_search_universe_complete is False
    assert report.establishes_wall_clock_priority is False


def test_the_receipt_does_not_claim_wall_clock_priority() -> None:
    """An agent can write any timestamp; the object says so in machine-readable form."""

    assert make_receipt().to_dict()["establishes_wall_clock_priority"] is False


# --- content binding ----------------------------------------------------------


def test_the_content_hash_covers_the_predeclared_discriminator() -> None:
    original = make_receipt()
    altered = make_receipt(predeclared_discriminator="a different falsifier")
    assert original.receipt_canonical_sha256 != altered.receipt_canonical_sha256


def test_the_content_hash_covers_the_allowed_outcome_branches() -> None:
    original = make_receipt()
    altered = make_receipt(
        allowed_outcome_branches=("SCALING_EXCLUDED", "SCALING_SURVIVES")
    )
    assert original.receipt_canonical_sha256 != altered.receipt_canonical_sha256


def test_the_content_hash_excludes_itself() -> None:
    receipt = make_receipt()
    assert receipt_canonical_sha256(receipt.to_dict()) == (
        receipt.receipt_canonical_sha256
    )


def test_hashing_is_idempotent() -> None:
    receipt = make_receipt()
    assert receipt.with_content_hash() == receipt


# --- schema -------------------------------------------------------------------


def _schema() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    return json.loads(
        (root / "schemas/pre-action-fibre-receipt-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_receipt_documents_validate_against_the_frozen_schema() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    validator.validate(make_receipt().to_dict())
    validator.validate(
        make_receipt(
            coverage_receipt_id=None,
            declared_consequence=ActionConsequence.NON_CONSEQUENTIAL_DECLARED,
            authority_bearing_retrieval_ids=(),
        ).to_dict()
    )


def test_schema_rejects_a_receipt_that_claims_authority() -> None:
    validator = Draft202012Validator(_schema())
    document = make_receipt().to_dict()
    document["grants_theorem_authority"] = True
    assert not validator.is_valid(document)


def test_schema_rejects_a_receipt_that_claims_complete_coverage() -> None:
    validator = Draft202012Validator(_schema())
    document = make_receipt().to_dict()
    document["claims_fibre_search_universe_complete"] = True
    assert not validator.is_valid(document)


def test_schema_rejects_a_receipt_with_no_predeclared_branches() -> None:
    validator = Draft202012Validator(_schema())
    document = make_receipt().to_dict()
    document["allowed_outcome_branches"] = []
    assert not validator.is_valid(document)


def test_schema_rejects_a_selected_retrieval_carrying_a_rejection_reason() -> None:
    validator = Draft202012Validator(_schema())
    document = make_receipt().to_dict()
    document["retrieval_bindings"][0]["rejection_reason"] = "invented afterwards"
    assert not validator.is_valid(document)
