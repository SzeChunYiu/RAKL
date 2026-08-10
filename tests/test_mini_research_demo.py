from __future__ import annotations

import json

from rakl.mini_research_demo import receipt_json, run_mini_research_demo


def test_known_answer_demo_unblocks_target_without_rewriting_negative_history():
    receipt = run_mini_research_demo()
    assert receipt.raw_sources == 8
    assert receipt.projected_claims == 9
    assert receipt.canonical_claims_after_exact_identity_collapse == 7
    assert receipt.target_support_paths_before_new_evidence == 0
    assert receipt.blocking_epistemic_cuts_before_new_evidence == 1
    assert receipt.target_support_paths_after_new_evidence == 1
    assert receipt.blocking_epistemic_cuts_after_new_evidence == 0
    assert receipt.negative_history_objects == 1
    assert receipt.true_aligned_contradictions_or_refutations == 1
    assert receipt.apparent_contradictions_avoided_by_context_alignment == 2


def test_demo_context_is_bounded_and_rehydratable():
    receipt = run_mini_research_demo()
    assert receipt.archive_token_estimate == 270
    assert receipt.active_context_tokens == 52
    assert receipt.active_to_archive_token_ratio < 0.20
    assert receipt.source_rehydration_roots == ("raw:S1", "raw:S3", "raw:S7")
    assert receipt.canonical_memory_views == 4
    assert receipt.lossless_memory_views == 1
    assert receipt.lossy_memory_views == 1


def test_demo_has_scoped_saturation_and_complete_atomic_trace_without_llm_claim():
    receipt = run_mini_research_demo()
    assert receipt.semantic_novelty_by_round == (("R0", 6), ("R1", 1), ("R2", 0), ("R3", 0))
    assert receipt.terminal_saturation_state == "SATURATED_SCOPED"
    assert receipt.atomic_trace_verdict == "VALID_SCOPED_TRACE"
    assert receipt.atomic_stages_registered == 17
    assert receipt.atomic_stages_executed_in_demo_trace == 17
    assert receipt.llm_calls_in_deterministic_demo == 0
    assert receipt.scientific_superiority_authority is False


def test_demo_receipt_is_stable_machine_readable_json():
    data = json.loads(receipt_json())
    assert data["demo_id"] == "PENDULUM_CONTEXT_ATLAS_001"
    assert data["target_period_seconds_first_order"] > 2.0
    assert data["scientific_superiority_authority"] is False
