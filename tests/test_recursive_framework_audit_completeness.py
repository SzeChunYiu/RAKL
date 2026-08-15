"""RFA v1 completeness: the packet pieces the first implementation left out.

Covers the parent-child interface binding and transport license (packet 06),
the atomicity admissibility conditions (06), and the stopping law -- mandatory
triggers, value of audit, bounded node closure (08).

These are additive checks. The frozen benchmark's own invariants (S01-S08) and
the 37-case conformance are asserted elsewhere and are untouched by this file:
``decide`` is not exercised here and its purity is unaffected.
"""

from __future__ import annotations

import pytest

from rakl.recursive_framework_audit import (
    AtomicityReceipt,
    AtomicitySplitCondition,
    AuditAction,
    AuditTrigger,
    InterfaceContract,
    NodeClosureTerminal,
    OptionalAuditCandidate,
    assess_bounded_node_closure,
    issue_atomicity_receipt,
    mandatory_audit_triggered,
    select_optional_audit,
)


def _complete_interface(**overrides: object) -> InterfaceContract:
    fields: dict[str, object] = dict(
        parent_fiber_id="parent",
        child_fiber_id="child",
        child_obligations=("return a typed residual",),
        parent_obligation_discharged="bound the target under the parent framework",
        inherited_inputs=("frozen cutoff", "evaluator epoch"),
        returned_outputs=("child residual", "child closure state"),
        assumptions=("regime is stationary within the child scope",),
        scope="child fiber scope",
        units="dimensionless target units",
        authority_transportable=("EVIDENCE_REFERENCE",),
        authority_forbidden=("SCIENTIFIC_AUTHORITY", "METHOD_PROMOTION"),
        uncertainty_composition="child intervals compose additively at the parent",
        failure_semantics="child CANNOT_CHECK propagates as parent CANNOT_CHECK",
    )
    fields.update(overrides)
    return InterfaceContract(**fields)  # type: ignore[arg-type]


# --- interface contract -----------------------------------------------------


def test_interface_is_incomplete_until_every_packet_binding_is_present() -> None:
    assert _complete_interface().complete is True
    assert InterfaceContract(parent_fiber_id="p", child_fiber_id="c").complete is False
    for missing in (
        "parent_obligation_discharged",
        "scope",
        "units",
        "uncertainty_composition",
        "failure_semantics",
    ):
        assert _complete_interface(**{missing: ""}).complete is False
    assert _complete_interface(inherited_inputs=()).complete is False
    assert _complete_interface(returned_outputs=()).complete is False
    assert _complete_interface(assumptions=()).complete is False
    assert _complete_interface(child_obligations=()).complete is False


def test_authority_transport_fails_closed() -> None:
    contract = _complete_interface()
    assert contract.licenses("EVIDENCE_REFERENCE") is True
    assert contract.licenses("SCIENTIFIC_AUTHORITY") is False
    # Never-mentioned authority is unlicensed, not permitted by omission.
    assert contract.licenses("MECHANISM_IDENTIFICATION") is False
    assert contract.unlicensed_transports(
        ("EVIDENCE_REFERENCE", "SCIENTIFIC_AUTHORITY", "MECHANISM_IDENTIFICATION")
    ) == ("SCIENTIFIC_AUTHORITY", "MECHANISM_IDENTIFICATION")


def test_interface_never_grants_authority_and_rejects_contradictory_license() -> None:
    contract = _complete_interface()
    assert contract.grants_scientific_authority is False
    assert contract.grants_method_promotion_authority is False
    with pytest.raises(ValueError, match="both transportable and forbidden"):
        _complete_interface(
            authority_transportable=("SCIENTIFIC_AUTHORITY",),
            authority_forbidden=("SCIENTIFIC_AUTHORITY",),
        )


# --- provisional atomicity --------------------------------------------------


def test_atomicity_receipt_requires_all_five_conditions() -> None:
    every = tuple(AtomicitySplitCondition)
    receipt = issue_atomicity_receipt(
        target_id="tau",
        split_family="regime-split",
        evaluator_epoch="epoch-1",
        evidence_cutoff="2026-08-15",
        satisfied_conditions=every,
    )
    assert isinstance(receipt, AtomicityReceipt)
    assert receipt.terminal == "PROVISIONALLY_ATOMIC_AT_REGISTERED_CUTOFF"
    assert receipt.grants_scientific_authority is False

    for dropped in every:
        with pytest.raises(ValueError, match="conditions not established"):
            issue_atomicity_receipt(
                target_id="tau",
                split_family="regime-split",
                evaluator_epoch="epoch-1",
                evidence_cutoff="2026-08-15",
                satisfied_conditions=[c for c in every if c is not dropped],
            )


def test_issued_receipt_is_still_index_scoped() -> None:
    receipt = issue_atomicity_receipt(
        target_id="tau",
        split_family="regime-split",
        evaluator_epoch="epoch-1",
        evidence_cutoff="2026-08-15",
        satisfied_conditions=tuple(AtomicitySplitCondition),
    )
    assert receipt.valid_for("tau", "regime-split", "epoch-1", "2026-08-15") is True
    assert receipt.valid_for("tau", "regime-split", "epoch-2", "2026-08-15") is False


# --- stopping law -----------------------------------------------------------


def test_mandatory_trigger_detection() -> None:
    assert mandatory_audit_triggered(()) is False
    assert mandatory_audit_triggered((AuditTrigger.EVALUATOR_INVALID,)) is True
    assert len(tuple(AuditTrigger)) == 10


def test_uncalibrated_selection_needs_decision_separation_then_priority_then_cost() -> None:
    cheap_but_blind = OptionalAuditCandidate(
        action=AuditAction.REVISE_MEASUREMENT, registered_priority=0, cost=1
    )
    assert select_optional_audit((cheap_but_blind,)) is None

    high_priority = OptionalAuditCandidate(
        action=AuditAction.AUDIT_EVALUATOR, registered_priority=0, cost=9, separates_decision=True
    )
    low_priority_cheap = OptionalAuditCandidate(
        action=AuditAction.SPLIT, registered_priority=3, cost=1, separates_decision=True
    )
    assert select_optional_audit((low_priority_cheap, high_priority)) is high_priority

    same_priority_expensive = OptionalAuditCandidate(
        action=AuditAction.MERGE, registered_priority=0, cost=20, separates_decision=True
    )
    assert select_optional_audit((same_priority_expensive, high_priority)) is high_priority
    assert select_optional_audit(()) is None


def test_calibrated_selection_never_invents_priors_and_requires_positive_voa() -> None:
    partial = (
        OptionalAuditCandidate(
            action=AuditAction.SPLIT, registered_priority=1, cost=2, expected_utility_gain=9
        ),
        OptionalAuditCandidate(action=AuditAction.MERGE, registered_priority=1, cost=2),
    )
    with pytest.raises(ValueError, match="expected utility gain"):
        select_optional_audit(partial, calibrated=True)

    not_worth_it = (
        OptionalAuditCandidate(
            action=AuditAction.SPLIT, registered_priority=1, cost=10, expected_utility_gain=10
        ),
    )
    assert select_optional_audit(not_worth_it, calibrated=True) is None

    worth_it = OptionalAuditCandidate(
        action=AuditAction.RUN_DISCRIMINATOR, registered_priority=1, cost=1, expected_utility_gain=8
    )
    assert select_optional_audit(not_worth_it + (worth_it,), calibrated=True) is worth_it


def test_bounded_node_closure_requires_all_eight_conditions() -> None:
    met = dict(
        question_decision_sufficient=True,
        framework_not_dominated=True,
        decomposition_checks_pass=True,
        interfaces_complete=True,
        measurement_and_evaluator_valid=True,
        target_solved_or_blocker_typed=True,
        no_decision_relevant_residual=True,
        no_material_optional_audit_value=True,
    )
    closed = assess_bounded_node_closure(**met)
    assert closed.terminal is NodeClosureTerminal.NODE_CLOSED_AT_REGISTERED_CUTOFF
    assert closed.closed is True
    assert closed.unmet_conditions == ()
    assert closed.grants_scientific_authority is False
    assert closed.grants_method_promotion_authority is False

    for condition in met:
        opened = assess_bounded_node_closure(**{**met, condition: False})
        assert opened.terminal is NodeClosureTerminal.NODE_OPEN
        assert opened.unmet_conditions == (condition,)
        assert opened.closed is False


def test_resource_bound_with_open_conditions_is_cannot_check_not_open_or_closed() -> None:
    met = dict(
        question_decision_sufficient=True,
        framework_not_dominated=True,
        decomposition_checks_pass=True,
        interfaces_complete=False,
        measurement_and_evaluator_valid=True,
        target_solved_or_blocker_typed=True,
        no_decision_relevant_residual=True,
        no_material_optional_audit_value=True,
    )
    blocked = assess_bounded_node_closure(resource_bound=True, **met)
    assert blocked.terminal is NodeClosureTerminal.CANNOT_CHECK_RESOURCE_BOUND
    assert blocked.unmet_conditions == ("interfaces_complete",)
    assert blocked.closed is False

    # A resource cap with every condition already met still closes: the cap is
    # only a blocker while a material condition is open.
    met_all = {**met, "interfaces_complete": True}
    assert (
        assess_bounded_node_closure(resource_bound=True, **met_all).terminal
        is NodeClosureTerminal.NODE_CLOSED_AT_REGISTERED_CUTOFF
    )
