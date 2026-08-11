from __future__ import annotations

from rakl.math_context import (
    ContextGateVerdict,
    MathContextFiber,
    MethodTransfer,
    audit_math_context_fiber,
)


def _transfer() -> MethodTransfer:
    return MethodTransfer(
        source_context="formula lower bounds",
        method="spectral lower bound",
        shared_structure=("same sign matrix",),
        required_assumptions=("tree-like recomputation",),
        disanalogies=("target permits DAG reuse",),
        repair_question="what quantity remains monotone when subcomputations are reused?",
        source_anchors=("doi:example",),
    )


def _fiber(**overrides: object) -> MathContextFiber:
    values: dict[str, object] = {
        "atom_id": "O1",
        "object_context": "lower-bound invariant stable under unrestricted reuse",
        "structural_coordinates": ("DAG reuse", "fusion", "explicit graph"),
        "equivalent_formulations": ("cyclic construction lower bound",),
        "solved_analogues": ("depth-bounded formula lower bounds",),
        "near_solved_analogues": (),
        "method_transfers": (_transfer(),),
        "explicit_disanalogies": ("formula methods charge recomputation; circuits share it",),
        "source_anchors": ("doi:example",),
        "frozen_at": "2026-08-11T04:00:00+00:00",
        "first_candidate_at": "2026-08-11T04:01:00+00:00",
        "packet_hash": "sha256:context",
    }
    values.update(overrides)
    return MathContextFiber(**values)  # type: ignore[arg-type]


def test_missing_context_fiber_fails_closed() -> None:
    report = audit_math_context_fiber(None)
    assert report.verdict is ContextGateVerdict.CANNOT_CHECK
    assert report.reasons == ("math_context_fiber_missing",)


def test_complete_context_fiber_passes() -> None:
    report = audit_math_context_fiber(_fiber())
    assert report.verdict is ContextGateVerdict.PASS


def test_candidate_before_context_freeze_is_rejected() -> None:
    report = audit_math_context_fiber(
        _fiber(first_candidate_at="2026-08-11T03:59:59+00:00")
    )
    assert report.verdict is ContextGateVerdict.FAIL
    assert "context_not_frozen_before_candidate_generation" in report.reasons


def test_method_transfer_must_record_disanalogy_and_repair_question() -> None:
    bad_transfer = MethodTransfer(
        source_context="formula lower bounds",
        method="spectral lower bound",
        shared_structure=("same sign matrix",),
        required_assumptions=("tree-like recomputation",),
        disanalogies=(),
        repair_question="",
        source_anchors=("doi:example",),
    )
    report = audit_math_context_fiber(_fiber(method_transfers=(bad_transfer,)))
    assert report.verdict is ContextGateVerdict.FAIL
    assert "method_transfer_0:disanalogies_missing" in report.reasons
    assert "method_transfer_0:repair_question_missing" in report.reasons
