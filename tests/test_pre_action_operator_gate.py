"""Fail-closed pre-execution gate for consequential operators (issue #123).

The receipt object already binds fibre/operator/falsifier content. These tests
assert that the execution gate refuses consequential operators when that binding
is missing, mismatched, or unverifiable — and only allows execution when all
three coordinates match.
"""

from __future__ import annotations

import pytest

from rakl.pre_action_receipt import (
    OperatorExecutionGateVerdict,
    PreActionFibreReceipt,
    RejectedRetrieval,
    RetrievalAuthority,
    SelectedRetrieval,
    gate_consequential_operator_execution,
    require_consequential_operator_receipt,
)

FRAMEWORK_COMMIT = "1fe6477aac2299a210e99e1624e9f7e795a2a6d4"
APPLICATION_COMMIT = "6557b1b25fa839fe71aba8047c958d5da892edd8"
PAYLOAD_HASH = "a" * 64
OPERATOR_ID = "op.scaling_discriminator"
FIBRE_HASH = "fibre-1"
FALSIFIER = "F=1 scaling separates ancient-Euler branch from the alternative"


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
        fibre_snapshot_hash=FIBRE_HASH,
        operator_ids=(OPERATOR_ID,),
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
        predeclared_discriminator=FALSIFIER,
        allowed_outcome_branches=("SUCCESS", "FAILURE"),
        frozen_at_utc="2026-08-11T09:00:00Z",
        sequence_index=0,
    )
    base.update(overrides)
    return PreActionFibreReceipt(**base)  # type: ignore[arg-type]


def _gate(receipt: PreActionFibreReceipt | None, **overrides: object):
    kwargs = dict(
        intended_operator_id=OPERATOR_ID,
        intended_fibre_snapshot_hash=FIBRE_HASH,
        intended_falsifier=FALSIFIER,
    )
    kwargs.update(overrides)
    return gate_consequential_operator_execution(receipt, **kwargs)  # type: ignore[arg-type]


def test_bound_receipt_allows_consequential_execution() -> None:
    receipt = _receipt()
    report = _gate(receipt, intended_atom_id="A-1", intended_context_hash="ctx-1", intended_task_id="T-1")
    assert report.verdict is OperatorExecutionGateVerdict.ALLOWED
    assert report.may_execute is True
    assert report.grants_prospective_or_theorem_authority is False
    assert report.receipt_content_hash == receipt.receipt_canonical_sha256
    assert "fibre_snapshot_bound" in report.reasons
    assert "operator_bound" in report.reasons
    assert "falsifier_and_outcome_branches_bound" in report.reasons


def test_missing_receipt_blocks_execution() -> None:
    report = _gate(None)
    assert report.verdict is OperatorExecutionGateVerdict.BLOCKED
    assert report.may_execute is False
    assert "no_pre_action_fibre_receipt_before_consequential_operator" in report.reasons
    assert "fibre_operator_falsifier_unbound" in report.reasons


def test_fibre_mismatch_blocks_execution() -> None:
    report = _gate(_receipt(), intended_fibre_snapshot_hash="fibre-OTHER")
    assert report.verdict is OperatorExecutionGateVerdict.BLOCKED
    assert report.may_execute is False
    assert "fibre_snapshot_hash_mismatch" in report.reasons


def test_operator_mismatch_blocks_execution() -> None:
    report = _gate(_receipt(), intended_operator_id="op.other")
    assert report.verdict is OperatorExecutionGateVerdict.BLOCKED
    assert report.may_execute is False
    assert "operator_id_not_bound_by_receipt" in report.reasons


def test_falsifier_mismatch_blocks_execution() -> None:
    report = _gate(_receipt(), intended_falsifier="a different discriminator invented after the result")
    assert report.verdict is OperatorExecutionGateVerdict.BLOCKED
    assert report.may_execute is False
    assert "falsifier_mismatch" in report.reasons


def test_malformed_receipt_cannot_check_and_refuses_execution() -> None:
    report = _gate(_receipt(framework_commit="not-a-git-oid"))
    assert report.verdict is OperatorExecutionGateVerdict.CANNOT_CHECK
    assert report.may_execute is False
    assert "framework_commit_not_a_git_oid" in report.reasons


def test_missing_intended_coordinates_cannot_check() -> None:
    assert (
        _gate(_receipt(), intended_operator_id="").verdict
        is OperatorExecutionGateVerdict.CANNOT_CHECK
    )
    assert (
        _gate(_receipt(), intended_fibre_snapshot_hash="").verdict
        is OperatorExecutionGateVerdict.CANNOT_CHECK
    )
    assert (
        _gate(_receipt(), intended_falsifier="").verdict
        is OperatorExecutionGateVerdict.CANNOT_CHECK
    )


def test_require_raises_when_blocked() -> None:
    with pytest.raises(ValueError, match="pre-action fibre receipt gate"):
        require_consequential_operator_receipt(
            None,
            intended_operator_id=OPERATOR_ID,
            intended_fibre_snapshot_hash=FIBRE_HASH,
            intended_falsifier=FALSIFIER,
        )


def test_require_returns_allowed_report() -> None:
    receipt = _receipt()
    report = require_consequential_operator_receipt(
        receipt,
        intended_operator_id=OPERATOR_ID,
        intended_fibre_snapshot_hash=FIBRE_HASH,
        intended_falsifier=FALSIFIER,
    )
    assert report.may_execute is True


def test_optional_atom_context_task_mismatches_block() -> None:
    receipt = _receipt()
    assert "atom_id_mismatch" in _gate(receipt, intended_atom_id="A-OTHER").reasons
    assert "context_hash_mismatch" in _gate(receipt, intended_context_hash="ctx-OTHER").reasons
    assert "task_id_mismatch" in _gate(receipt, intended_task_id="T-OTHER").reasons
