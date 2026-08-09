from pathlib import Path

from rakl.meta_history import HistoricalIssueKind, HistoricalLedgerVerdict, compile_meta_fiber_history


def test_round041_live_repair_keeps_old_and_reconciled_identities_distinct() -> None:
    research = Path(__file__).resolve().parents[1] / "research"
    report = compile_meta_fiber_history(research)

    assert report.verdict == HistoricalLedgerVerdict.CONSISTENT_WITH_RECONCILIATION_HISTORY
    assert not report.unresolved_issues

    canonical = {item.fiber_id for item in report.canonical_fibers}
    assert {
        "META_N091_POST_PROMOTION_REF_STATE_ATTESTATION",
        "META_N092_PR_TEST_EXECUTED_SUBJECT_BINDING",
        "META_N123_SCOPED_SELF_EVOLUTION_EVIDENCE",
        "META_N124_ADAPTIVE_ASSURANCE_RESERVE",
    } <= canonical
    assert "META_N091_SCOPED_SELF_EVOLUTION_EVIDENCE" not in canonical
    assert "META_N092_ADAPTIVE_ASSURANCE_RESERVE" not in canonical

    # Legacy declaration schemas are recovered structurally rather than turned
    # into false orphan references.
    assert {
        "META_N095_TARGET_CONDITIONED_SUPPORT_HYPERPATH",
        "META_N096_EPISTEMIC_CUTSET_GAP_COMPLETION",
        "META_N097_POST_SATURATION_GENERATIVE_EXPANSION",
        "META_N098_PATH_CORRIDOR_CONTEXT_COMPILATION",
        "META_N099_GAP_COMPLETION_EMPIRICAL_BENCHMARK",
        "META_N121_MEASUREMENT_TRANSFORM_AND_UQ_EXECUTION",
        "META_N122_CHALLENGE_LEARNING_CONTROL",
    } <= canonical

    resolved_orphans = {
        issue.fiber_id
        for issue in report.issues
        if issue.kind == HistoricalIssueKind.ORPHAN_REFERENCE and issue.resolved
    }
    assert "META_N024_INTEGRATION_SUBJECT_IDENTITY_WORKFLOW_ACTIVATION" in resolved_orphans
    assert "META_N015_CLAIM_EVIDENCE_PROVENANCE_REAL_UTILITY" in resolved_orphans

    # Reconciliation history stays visible as negative evidence.
    resolved_collisions = [
        issue
        for issue in report.issues
        if issue.kind == HistoricalIssueKind.NAMESPACE_SLOT_COLLISION and issue.resolved
    ]
    assert resolved_collisions

    assert report.can_support_registry_bookkeeping()
    assert not report.can_grant_scientific_authority()
    assert not report.can_grant_method_authority()
    assert not report.can_grant_target_authority()
    assert not report.can_grant_independent_review_credit()
    assert not report.can_grant_framework_saturation()
