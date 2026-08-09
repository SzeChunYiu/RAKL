from rakl import (
    CheckConclusion,
    PromotionDecision,
    PromotionGate,
    PromotionPacket,
    RequiredCheck,
)
from rakl.meta import MethodChangeClass


INCUMBENT = "a" * 40
CANDIDATE = "b" * 40


def clean_packet(**overrides) -> PromotionPacket:
    values = {
        "incumbent_sha": INCUMBENT,
        "candidate_sha": CANDIDATE,
        "observed_main_sha": INCUMBENT,
        "benchmark_frozen_before_candidate": True,
        "receipt_present": True,
        "history_preserved": True,
        "required_checks": (
            RequiredCheck(
                "test",
                CheckConclusion.SUCCESS,
                source="github-actions",
                exact_candidate_sha=True,
                trusted_source=True,
            ),
        ),
        "expected_required_checks": ("test",),
        "validator_fingerprints_unchanged": True,
        "changed_protected_paths": (),
        "fast_forward_compatible": True,
        "blocking_failures": (),
        "improvements": {"promotion_gate_exactness": 1.0},
        "regressions": {},
    }
    values.update(overrides)
    return PromotionPacket(**values)


def test_passing_class_b_candidate_can_promote():
    verdict = PromotionGate.evaluate(MethodChangeClass.WORKFLOW, clean_packet())
    assert verdict.decision == PromotionDecision.PROMOTE
    assert verdict.may_move_main


def test_failed_candidate_is_blocked():
    packet = clean_packet(
        required_checks=(
            RequiredCheck(
                "test",
                CheckConclusion.FAILURE,
                source="github-actions",
            ),
        )
    )
    verdict = PromotionGate.evaluate(MethodChangeClass.WORKFLOW, packet)
    assert verdict.decision == PromotionDecision.BLOCK
    assert not verdict.may_move_main


def test_missing_or_pending_check_is_cannot_check():
    missing = clean_packet(required_checks=())
    pending = clean_packet(
        required_checks=(
            RequiredCheck(
                "test",
                CheckConclusion.PENDING,
                source="github-actions",
            ),
        )
    )

    assert (
        PromotionGate.evaluate(MethodChangeClass.WORKFLOW, missing).decision
        == PromotionDecision.CANNOT_CHECK
    )
    assert (
        PromotionGate.evaluate(MethodChangeClass.WORKFLOW, pending).decision
        == PromotionDecision.CANNOT_CHECK
    )


def test_constitutional_candidate_remains_proposal_only_even_if_green():
    verdict = PromotionGate.evaluate(MethodChangeClass.CONSTITUTION, clean_packet())
    assert verdict.decision == PromotionDecision.PROPOSAL_ONLY
    assert not verdict.may_move_main


def test_candidate_cannot_change_its_own_protected_evaluator():
    packet = clean_packet(
        validator_fingerprints_unchanged=False,
        changed_protected_paths=(".github/workflows/test.yml",),
    )
    verdict = PromotionGate.evaluate(MethodChangeClass.WORKFLOW, packet)
    assert verdict.decision == PromotionDecision.BLOCK
    assert any("protected evaluator" in reason for reason in verdict.reasons)


def test_class_b_requires_registered_improvement():
    verdict = PromotionGate.evaluate(
        MethodChangeClass.WORKFLOW,
        clean_packet(improvements={}),
    )
    assert verdict.decision == PromotionDecision.BLOCK
    assert any("no registered positive" in reason for reason in verdict.reasons)


def test_premature_main_movement_is_process_violation():
    packet = clean_packet(observed_main_sha=CANDIDATE)
    verdict = PromotionGate.evaluate(MethodChangeClass.WORKFLOW, packet)
    assert verdict.decision == PromotionDecision.PROCESS_VIOLATION
    assert not verdict.may_move_main


def test_green_check_from_wrong_revision_or_untrusted_source_is_blocked():
    wrong_revision = clean_packet(
        required_checks=(
            RequiredCheck(
                "test",
                CheckConclusion.SUCCESS,
                source="github-actions",
                exact_candidate_sha=False,
            ),
        )
    )
    untrusted = clean_packet(
        required_checks=(
            RequiredCheck(
                "test",
                CheckConclusion.SUCCESS,
                source="arbitrary-status-writer",
                trusted_source=False,
            ),
        )
    )

    assert (
        PromotionGate.evaluate(MethodChangeClass.WORKFLOW, wrong_revision).decision
        == PromotionDecision.BLOCK
    )
    assert (
        PromotionGate.evaluate(MethodChangeClass.WORKFLOW, untrusted).decision
        == PromotionDecision.BLOCK
    )


def test_class_a_does_not_require_qoi_improvement_but_keeps_hard_gates():
    packet = clean_packet(improvements={})
    assert (
        PromotionGate.evaluate(MethodChangeClass.IMPLEMENTATION, packet).decision
        == PromotionDecision.PROMOTE
    )

    blocked = clean_packet(
        improvements={},
        benchmark_frozen_before_candidate=False,
    )
    assert (
        PromotionGate.evaluate(MethodChangeClass.IMPLEMENTATION, blocked).decision
        == PromotionDecision.BLOCK
    )
