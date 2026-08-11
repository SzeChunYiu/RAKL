from __future__ import annotations

from rakl.math_context import (
    AnalogyScanStatus,
    ContextGateVerdict,
    CrossDomainAnalogy,
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


def _daily_analogy() -> CrossDomainAnalogy:
    return CrossDomainAnalogy(
        source_kind="everyday",
        source_situation="a workshop reuses one shared jig for many products instead of rebuilding it",
        common_abstraction=("shared intermediate resource", "reuse versus recomputation"),
        source_to_target_mapping=("jig -> shared subcomputation", "product -> output dependency"),
        shared_constraints=("one reusable object can serve many downstream consumers",),
        disanalogies=("physical jig capacity is not a Boolean circuit complexity measure",),
        proposed_principle="charge creation of reusable structure separately from downstream reuse",
        validation_obligation="define a graph-cover quantity with a proved per-fusion budget and test it on known easy families",
        provenance_note="ordinary workshop analogy used only for proposal generation",
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
        "analogy_scan_status": AnalogyScanStatus.BRIDGES_RETAINED.value,
        "cross_domain_analogies": (_daily_analogy(),),
        "analogy_scan_notes": "retained one reuse analogy after explicit disanalogy check",
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


def test_naive_timestamp_is_rejected_as_ambiguous() -> None:
    report = audit_math_context_fiber(_fiber(frozen_at="2026-08-11T04:00:00"))
    assert report.verdict is ContextGateVerdict.FAIL
    assert "context_freeze_time_missing_or_invalid" in report.reasons


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


def test_cross_domain_analogy_requires_mapping_disanalogy_and_validation() -> None:
    bad = CrossDomainAnalogy(
        source_kind="everyday",
        source_situation="shared tool",
        common_abstraction=("reuse",),
        source_to_target_mapping=(),
        shared_constraints=("shared resource",),
        disanalogies=(),
        proposed_principle="charge shared structure",
        validation_obligation="",
        provenance_note="ordinary analogy",
    )
    report = audit_math_context_fiber(_fiber(cross_domain_analogies=(bad,)))
    assert report.verdict is ContextGateVerdict.FAIL
    assert "cross_domain_analogy_0:source_to_target_mapping_missing" in report.reasons
    assert "cross_domain_analogy_0:disanalogies_missing" in report.reasons
    assert "cross_domain_analogy_0:validation_obligation_missing" in report.reasons


def test_no_safe_bridge_is_allowed_only_with_explicit_notes() -> None:
    report = audit_math_context_fiber(
        _fiber(
            analogy_scan_status=AnalogyScanStatus.NO_SAFE_BRIDGE_FOUND.value,
            cross_domain_analogies=(),
            analogy_scan_notes="searched queueing, shared-resource and caching analogies; none survived the mapping gate",
        )
    )
    assert report.verdict is ContextGateVerdict.PASS
