"""Frozen hostile worlds for the pre-action fibre receipt (issue #123).

The four worlds are exactly the ones the issue enumerates. World 4 is the
no-alarm control: a design that flags a cheap non-consequential action is
refuted by it, not vindicated.

The acceptance boundary has two halves and both are asserted here: retrospective
status must be mechanically unavoidable when chronology is missing, *and*
retrospective episodes must stay fully usable for search priority and failure
learning.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from rakl.experience_substrate import EpisodeOutcome, TaskEpisode
from rakl.pre_action_receipt import (
    BindingVerdict,
    ChronologyStatus,
    PreActionFibreReceipt,
    RejectedRetrieval,
    RetrievalAuthority,
    SelectedRetrieval,
    admissible_for_failure_learning,
    admissible_for_search_priority,
    audit_pre_action_binding,
)

FRAMEWORK_COMMIT = "1fe6477aac2299a210e99e1624e9f7e795a2a6d4"
APPLICATION_COMMIT = "6557b1b25fa839fe71aba8047c958d5da892edd8"
PAYLOAD_HASH = "a" * 64


def _receipt(**overrides: object) -> PreActionFibreReceipt:
    base = dict(
        receipt_id="R-1",
        framework_repository="SzeChunYiu/RAKL",
        framework_commit=FRAMEWORK_COMMIT,
        application_repository="SzeChunYiu/RAKL_math",
        application_commit=APPLICATION_COMMIT,
        task_id="T-1",
        atom_id="A-1",
        context_hash="ctx-1",
        fibre_snapshot_hash="fibre-1",
        operator_ids=("op.scaling_discriminator",),
        selected_retrievals=(
            SelectedRetrieval(
                retrieval_id="K-canonical-1",
                authority=RetrievalAuthority.CANONICAL,
                payload_hash=PAYLOAD_HASH,
            ),
        ),
        rejected_retrievals=(
            RejectedRetrieval(
                retrieval_id="K-relevant-but-rejected-1",
                rejection_reason="enabling assumption absent in target context",
            ),
        ),
        predeclared_discriminator="F=1 scaling separates ancient-Euler branch from the alternative",
        allowed_outcome_branches=("SUCCESS", "FAILURE"),
        frozen_at_utc="2026-08-11T09:00:00Z",
        sequence_index=0,
    )
    base.update(overrides)
    return PreActionFibreReceipt(**base)  # type: ignore[arg-type]


def _episode(receipt: PreActionFibreReceipt | None, **overrides: object) -> TaskEpisode:
    pointers = ("artifact:observation-1",)
    if receipt is not None:
        pointers = (receipt.episode_pointer,) + pointers
    base = dict(
        episode_id="E-1",
        task_id="T-1",
        atom_id="A-1",
        context_hash="ctx-1",
        problem_signature=("navier-stokes-like-scaling",),
        fibre_snapshot_hash="fibre-1",
        operator_ids=("op.scaling_discriminator",),
        action_trace=("ran discriminator",),
        observation_ids=("O-1",),
        verification_ids=(),
        outcome=EpisodeOutcome.FAILURE,
        residual_signature=("far_field_escape",),
        evidence_pointers=pointers,
        artifact_hash="episode-hash-1",
        timestamp="2026-08-11T10:00:00Z",
    )
    base.update(overrides)
    return TaskEpisode(**base)  # type: ignore[arg-type]


def test_clean_prospective_binding_verifies() -> None:
    receipt = _receipt()
    report = audit_pre_action_binding(receipt, _episode(receipt))

    assert report.verdict is BindingVerdict.PROSPECTIVE_BINDING_VERIFIED
    assert report.chronology_status is ChronologyStatus.PROSPECTIVE_BOUND
    assert report.prospective_gate_admissible
    assert report.reasons == ()


# --- world 1: a relevant item exists but is omitted from the fibre ------------


def test_receipt_makes_no_completeness_claim_when_a_relevant_item_is_omitted() -> None:
    """A verified binding must not silently acquire a coverage claim.

    Two receipts that differ only by whether a relevant artifact was retrieved
    produce the *same* verdict, because chronology is not coverage. Coverage is
    RAKL issue #119's object; this receipt must never stand in for it.
    """

    with_item = _receipt(
        selected_retrievals=(
            SelectedRetrieval(
                retrieval_id="K-canonical-1",
                authority=RetrievalAuthority.CANONICAL,
                payload_hash=PAYLOAD_HASH,
            ),
            SelectedRetrieval(
                retrieval_id="K-relevant-2",
                authority=RetrievalAuthority.CANONICAL,
                payload_hash="b" * 64,
            ),
        )
    )
    without_item = _receipt()

    with_report = audit_pre_action_binding(with_item, _episode(with_item))
    without_report = audit_pre_action_binding(without_item, _episode(without_item))

    assert with_report.verdict is without_report.verdict
    assert with_report.verdict is BindingVerdict.PROSPECTIVE_BINDING_VERIFIED
    assert not with_report.implies_fibre_search_universe_complete
    assert not without_report.implies_fibre_search_universe_complete


# --- world 2: a pending/noncanonical artifact must not acquire authority ------


@pytest.mark.parametrize(
    "authority",
    [RetrievalAuthority.PENDING, RetrievalAuthority.NONCANONICAL, RetrievalAuthority.UNSPECIFIED],
)
def test_non_canonical_retrieval_informs_but_never_bears_authority(
    authority: RetrievalAuthority,
) -> None:
    receipt = _receipt(
        selected_retrievals=(
            SelectedRetrieval(
                retrieval_id="K-canonical-1",
                authority=RetrievalAuthority.CANONICAL,
                payload_hash=PAYLOAD_HASH,
            ),
            SelectedRetrieval(
                retrieval_id="K-weak-1",
                authority=authority,
                payload_hash="c" * 64,
            ),
        )
    )
    report = audit_pre_action_binding(receipt, _episode(receipt))

    # The weak artifact is recorded and may inform the action ...
    assert "K-weak-1" in report.non_authority_bearing_retrieval_ids
    # ... but never carries authority into it.
    assert "K-weak-1" not in report.authority_bearing_retrieval_ids
    assert report.authority_bearing_retrieval_ids == ("K-canonical-1",)
    # Retrieving a weak artifact is not itself a chronology defect.
    assert report.verdict is BindingVerdict.PROSPECTIVE_BINDING_VERIFIED


# --- world 3: the discriminator is changed after seeing the result ------------


def test_discriminator_substituted_after_the_result_breaks_the_binding() -> None:
    """The predeclared discriminator is inside the hashed content on purpose."""

    original = _receipt()
    episode = _episode(original)

    substituted = replace(
        original,
        predeclared_discriminator="whatever the observed result happened to show",
    )
    assert substituted.receipt_canonical_sha256 != original.receipt_canonical_sha256

    report = audit_pre_action_binding(substituted, episode)
    assert report.verdict is BindingVerdict.RETROSPECTIVE_BINDING_REFUTED
    assert report.chronology_status is ChronologyStatus.RETROSPECTIVE_ONLY
    assert not report.prospective_gate_admissible
    assert "episode_does_not_reference_this_receipt_content_hash" in report.reasons


def test_outcome_outside_the_predeclared_branches_is_refuted() -> None:
    receipt = _receipt(allowed_outcome_branches=("SUCCESS", "FAILURE"))
    episode = _episode(receipt, outcome=EpisodeOutcome.BLOCKED)

    report = audit_pre_action_binding(receipt, episode)
    assert report.verdict is BindingVerdict.RETROSPECTIVE_BINDING_REFUTED
    assert any(reason.startswith("outcome_outside_predeclared_branches") for reason in report.reasons)


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("fibre_snapshot_hash", "fibre-2"),
        ("atom_id", "A-2"),
        ("context_hash", "ctx-2"),
        ("operator_ids", ("op.something_else",)),
        ("task_id", "T-2"),
    ],
)
def test_any_binding_field_mismatch_forces_retrospective(field_name: str, value: object) -> None:
    receipt = _receipt()
    episode = _episode(receipt, **{field_name: value})

    report = audit_pre_action_binding(receipt, episode)
    assert report.chronology_status is ChronologyStatus.RETROSPECTIVE_ONLY
    assert not report.prospective_gate_admissible


def test_a_receipt_frozen_after_the_episode_cannot_be_prospective() -> None:
    receipt = _receipt(frozen_at_utc="2026-08-11T11:00:00Z")
    episode = _episode(receipt, timestamp="2026-08-11T10:00:00Z")

    report = audit_pre_action_binding(receipt, episode)
    assert report.verdict is BindingVerdict.RETROSPECTIVE_BINDING_REFUTED
    assert "receipt_does_not_strictly_precede_episode" in report.reasons


# --- world 4: a genuinely cheap action must not incur ceremony (no-alarm) -----


def test_cheap_non_consequential_action_incurs_no_ceremony() -> None:
    """No-alarm control.

    An action that never claimed prospective credit is not defective. It is
    recorded as retrospective, with no receipt, and nothing else is flagged.
    """

    episode = _episode(None, episode_id="E-cheap", operator_ids=("op.read_a_file",))
    report = audit_pre_action_binding(None, episode)

    assert report.verdict is BindingVerdict.RETROSPECTIVE_NO_RECEIPT
    assert report.verdict is not BindingVerdict.RETROSPECTIVE_BINDING_REFUTED
    assert report.reasons == ("no_pre_action_receipt_supplied",)
    assert admissible_for_search_priority(episode)
    assert admissible_for_failure_learning(episode)


# --- acceptance boundary, second half -----------------------------------------


def _all_worlds() -> list[tuple[str, PreActionFibreReceipt | None, TaskEpisode]]:
    clean = _receipt()
    substituted = replace(_receipt(), predeclared_discriminator="post hoc")
    malformed = _receipt(framework_commit="not-a-git-oid")
    return [
        ("clean prospective", clean, _episode(clean)),
        ("world 3 substituted discriminator", substituted, _episode(_receipt())),
        ("world 4 no receipt", None, _episode(None)),
        ("cannot check", malformed, _episode(malformed)),
        ("mismatched fibre", clean, _episode(clean, fibre_snapshot_hash="fibre-9")),
    ]


def test_retrospective_episodes_remain_usable_in_every_world() -> None:
    """Chronology status must never gate search priority or failure learning."""

    for label, receipt, episode in _all_worlds():
        report = audit_pre_action_binding(receipt, episode)
        assert admissible_for_search_priority(episode), label
        assert admissible_for_failure_learning(episode), label
        # and the two admissibilities are genuinely not a function of status
        assert admissible_for_search_priority(episode) is True, label
        assert report.chronology_status in {
            ChronologyStatus.PROSPECTIVE_BOUND,
            ChronologyStatus.RETROSPECTIVE_ONLY,
        }, label


def test_only_a_verified_binding_is_prospective_in_every_world() -> None:
    """Retrospective status is unavoidable: nothing declared can promote it."""

    for label, receipt, episode in _all_worlds():
        report = audit_pre_action_binding(receipt, episode)
        expected = report.verdict is BindingVerdict.PROSPECTIVE_BINDING_VERIFIED
        assert report.prospective_gate_admissible is expected, label


def test_cannot_check_is_distinct_from_refuted() -> None:
    """"Could not check" is never reported as "checked and defective"."""

    malformed = _receipt(framework_commit="not-a-git-oid")
    report = audit_pre_action_binding(malformed, _episode(malformed))

    assert report.verdict is BindingVerdict.CANNOT_CHECK
    assert report.chronology_status is ChronologyStatus.RETROSPECTIVE_ONLY
    assert "framework_commit_not_a_git_oid" in report.reasons


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("predeclared_discriminator", "different"),
        ("allowed_outcome_branches", ("SUCCESS",)),
        ("fibre_snapshot_hash", "fibre-2"),
        ("operator_ids", ("op.other",)),
        ("framework_commit", "0" * 40),
        ("sequence_index", 7),
    ],
)
def test_every_hashed_field_changes_the_receipt_pointer(field_name: str, value: object) -> None:
    """Validate the checker: the content hash actually covers what it claims."""

    original = _receipt()
    mutated = replace(original, **{field_name: value})
    assert mutated.receipt_canonical_sha256 != original.receipt_canonical_sha256
    assert mutated.episode_pointer != original.episode_pointer


def test_receipt_document_validates_against_its_schema() -> None:
    import json
    from pathlib import Path

    import jsonschema

    schema = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "schemas"
            / "pre-action-fibre-receipt-v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(_receipt().document(), schema)


def test_receipt_document_hash_is_derived_not_supplied() -> None:
    """A document cannot carry a hash that disagrees with its own content."""

    receipt = _receipt()
    document = dict(receipt.document())
    recomputed = replace(receipt, predeclared_discriminator="different").document()

    assert document["receipt_canonical_sha256"] != recomputed["receipt_canonical_sha256"]
    assert document["receipt_canonical_sha256"] == receipt.receipt_canonical_sha256


def test_receipt_rejects_structurally_invalid_retrievals() -> None:
    with pytest.raises(ValueError, match="payload_hash must be sha256"):
        SelectedRetrieval(
            retrieval_id="K-1",
            authority=RetrievalAuthority.CANONICAL,
            payload_hash="short",
        )
    with pytest.raises(ValueError, match="rejection_reason"):
        RejectedRetrieval(retrieval_id="K-1", rejection_reason="")
