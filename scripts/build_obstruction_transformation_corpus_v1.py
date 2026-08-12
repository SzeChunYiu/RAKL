#!/usr/bin/env python3
"""Build obstruction_transformation_corpus_v1 seed artifacts (issue #402)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rakl.obstruction_transformation_corpus import (  # noqa: E402
    CORPUS_DIR,
    RECEIPTS_DIR,
    _runtime_payload,
    build_coverage_report,
    build_dedup_report,
    episode_content_hash,
    episode_from_dict,
    validate_corpus,
)
from rakl.paper3_annotation import canonical_sha256  # noqa: E402
from rakl.semantic_shortcut import build_transformation_memory  # noqa: E402


def _fp(
    oid: str,
    domain: str,
    *,
    roles: list[str],
    relations: list[str],
    constraints: list[str],
    failure_mechanisms: list[str],
    invariants: list[str],
    desired: list[str],
    forbidden: list[str] | None = None,
) -> dict:
    return {
        "obstruction_id": oid,
        "domain": domain,
        "roles": roles,
        "relations": relations,
        "constraints": constraints,
        "failure_mechanisms": failure_mechanisms,
        "invariants_to_preserve": invariants,
        "desired_transition": desired,
        "forbidden_losses": forbidden or [],
    }


def _episode(**kwargs) -> dict:
    row = dict(kwargs)
    # Ensure required defaults
    row.setdefault("relaxed_or_broken_constraints", [])
    row.setdefault("lineage_ids", [])
    row.setdefault("verification_receipt", None)
    # Compute content hash after stripping hash + corpus-only fields used in hash body
    hash_body = {
        k: v
        for k, v in row.items()
        if k
        not in {
            "artifact_hash",
            "domain_lane",
            "verification_receipt",
            "split_hints",
            "notes",
        }
    }
    row["artifact_hash"] = canonical_sha256(hash_body)
    # Recompute with artifact_hash excluded via helper for consistency with loader
    row["artifact_hash"] = episode_content_hash(row)
    return row


def seed_episodes() -> list[dict]:
    episodes: list[dict] = []

    # 1) VERIFIED_LOCAL — RAKL capable-model gate terminus (in-repo receipts)
    episodes.append(
        _episode(
            episode_id="OTC-V1-RAKL-CAPABLE-MODEL-GATE-TERMINUS",
            domain_lane="scientific_experimental_method",
            source_domain="scientific_experimental_method",
            source_context="RAKL Paper II confirmatory empirics under ORACLE capability ladder",
            source_obstruction=_fp(
                "O-capable-model-absent",
                "scientific_experimental_method",
                roles=["evaluator", "subject_model", "confirmatory_protocol", "claim_boundary"],
                relations=[
                    "confirmatory_job_requires_capable_model",
                    "oracle_success_rate_gates_authorize",
                ],
                constraints=[
                    "preregistered_scale_staircase",
                    "no_outcome_driven_threshold_softening",
                    "no_14B_32B_without_new_preregistration",
                ],
                failure_mechanisms=[
                    "model_capability_floor_below_two_thirds",
                    "confirmatory_authorize_without_capable_model",
                ],
                invariants=[
                    "negative_history_preserved",
                    "CAPABLE_MODEL_AVAILABLE_fail_closed",
                ],
                desired=[
                    "authorized_confirmatory_execution_or_honest_terminal",
                ],
                forbidden=[
                    "fake_capable_model_clearance",
                    "promotional_lift_from_non_confirmatory_scores",
                ],
            ),
            transformation_name="terminal_stop_capable_model_no_refuted",
            operation="fail_closed_gate_then_record_ladder_terminus",
            preconditions=[
                "authorized_ORACLE_scales_exhausted_or_gate_failed",
                "success_rate_below_two_thirds_at_each_authorized_scale",
                "V2_EXEC_sealed_tasks_evaluated_under_frozen_protocol",
            ],
            resulting_relations=[
                "CAPABLE_MODEL_AVAILABLE=NO_REFUTED",
                "confirmatory_model_jobs_forbidden",
                "Wave-2_confirmatory_unlock=no",
            ],
            preserved_invariants=[
                "prior_floor_receipts_immutable",
                "no_threshold_softening_after_outcomes",
            ],
            relaxed_or_broken_constraints=[
                "expectation_that_7B_V2_EXEC_clears_gate",
            ],
            known_breakpoints=[
                "reopen_only_with_pre_outcome_protocol_redesign_or_authorized_ORACLE_ge_2_of_3",
            ],
            evidence_pointers=[
                "research/paper2_oracle_capability_gate_v2_exec/ORACLE_DECISION_RECEIPT_V2_EXEC.json",
                "research/STRONGEST_VERSION_CAMPAIGN_SCOREBOARD_20260812.json",
                "research/paper2_alr_a3a4_confirmatory_prep_wave1_v1/CAPABILITY_GATE.json",
            ],
            authority="VERIFIED_LOCAL",
            verification_receipt="VR-RAKL-CAPABLE-MODEL-GATE-TERMINUS.json",
            lineage_ids=[],
            split_hints=["DEVELOPMENT_MEMORY"],
            notes="In-repo RAKL event; source-event verification is local receipt binding only.",
        )
    )

    # 2) VERIFIED_LOCAL — A3↔A4 matched confirmatory blocked
    episodes.append(
        _episode(
            episode_id="OTC-V1-RAKL-A3A4-MATCHED-BLOCKED",
            domain_lane="scientific_experimental_method",
            source_domain="scientific_experimental_method",
            source_context="Paper II A3↔A4 matched empirical ablation after #156 / Wave-1 prep",
            source_obstruction=_fp(
                "O-a3a4-identification-without-capable-model",
                "scientific_experimental_method",
                roles=["A3_arm", "A4_arm", "matched_panel", "typed_authority_license"],
                relations=[
                    "matched_resources_and_prompts",
                    "typed_authority_intervention_on_A4",
                ],
                constraints=[
                    "external_system_naming_ban",
                    "parent_V1_packet_immutable",
                    "capable_model_gate_shared_with_ALR",
                ],
                failure_mechanisms=[
                    "interpreting_non_confirmatory_scores_as_A4_gt_A3",
                    "confirmatory_run_without_authorize_receipt",
                ],
                invariants=[
                    "non_confirmatory_3476749_history_only",
                    "prep_hashes_bound",
                ],
                desired=["confirmatory_matched_identification_or_honest_CANNOT_EXECUTE"],
                forbidden=["A4_gt_A3_claim_under_NO_REFUTED"],
            ),
            transformation_name="cannot_execute_confirmatory_a3_a4_terminal",
            operation="record_CANNOT_EXECUTE_and_forbid_confirmatory_jobs",
            preconditions=[
                "wave1_prep_frozen",
                "CAPABLE_MODEL_AVAILABLE=false",
                "no_confirmatory_authorize_receipt",
            ],
            resulting_relations=[
                "scientific_verdict=CANNOT_EXECUTE_CONFIRMATORY_A3_A4_MATCHED_ABLATION",
                "confirmatory_A3_A4_forbidden",
            ],
            preserved_invariants=[
                "parent_matched_packet_v1_immutable",
                "non_confirmatory_scores_not_reinterpreted",
            ],
            relaxed_or_broken_constraints=[],
            known_breakpoints=[
                "science_acceptance_remains_open_until_capable_model_gate_clears",
            ],
            evidence_pointers=[
                "research/capability_gated_closeout_20260812/ISSUE_352_TERMINAL_RECEIPT.json",
                "research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICAL_PACKET_V1.json",
                "research/paper2_alr_a3a4_confirmatory_prep_wave1_v1/PREP_PACKET.json",
            ],
            authority="VERIFIED_LOCAL",
            verification_receipt="VR-RAKL-A3A4-MATCHED-BLOCKED.json",
            lineage_ids=["OTC-V1-RAKL-CAPABLE-MODEL-GATE-TERMINUS"],
            split_hints=["DEVELOPMENT_MEMORY"],
        )
    )

    # 3) SUPERSEDED — scale-shopping proposal replaced by ladder terminus
    episodes.append(
        _episode(
            episode_id="OTC-V1-RAKL-SCALE-SHOPPING-SUPERSEDED",
            domain_lane="scientific_experimental_method",
            source_domain="scientific_experimental_method",
            source_context="Post-FLOOR_7B temptation to escalate to 14B/32B without new preregistration",
            source_obstruction=_fp(
                "O-scale-shopping-after-floor",
                "scientific_experimental_method",
                roles=["operator", "oracle_ladder", "claim_boundary"],
                relations=["escalation_after_negative_outcome"],
                constraints=["preregistered_stop_rule"],
                failure_mechanisms=["outcome_driven_scale_shopping"],
                invariants=["protocol_identity_before_outcomes"],
                desired=["clear_capable_model_by_larger_scale"],
                forbidden=["silent_protocol_mutation"],
            ),
            transformation_name="unauthorized_scale_escalation",
            operation="propose_14B_or_32B_without_new_preregistration",
            preconditions=["prior_scale_failed_gate"],
            resulting_relations=["protocol_illegal_escalation_proposed"],
            preserved_invariants=["negative_outcome_still_on_record"],
            relaxed_or_broken_constraints=["preregistered_stop_at_7B"],
            known_breakpoints=["blocked_by_campaign_scoreboard_and_V2_EXEC_terminus"],
            evidence_pointers=[
                "research/STRONGEST_VERSION_CAMPAIGN_SCOREBOARD_20260812.md",
            ],
            authority="SUPERSEDED",
            verification_receipt=None,
            lineage_ids=["OTC-V1-RAKL-CAPABLE-MODEL-GATE-TERMINUS"],
            split_hints=["DEVELOPMENT_MEMORY"],
            notes="Negative/history example; not a viable SEARCH/JUMP route.",
        )
    )

    # 4) Algorithms — visited-set / cycle break (PROPOSAL_ONLY)
    episodes.append(
        _episode(
            episode_id="OTC-V1-ALG-FINITE-REVISITATION-VISITED-SET",
            domain_lane="algorithms_data_structures",
            source_domain="algorithms_data_structures",
            source_context="PROPOSAL_ONLY structural exemplar: iterating a map over a finite set with possible revisits",
            source_obstruction=_fp(
                "O-finite-state-revisitation",
                "algorithms_data_structures",
                roles=["walker", "finite_state_set", "transition_map"],
                relations=["iterated_application", "possible_return_to_seen_state"],
                constraints=["finite_cardinality", "deterministic_transition"],
                failure_mechanisms=["nontermination_via_cycle", "duplicate_work_on_revisit"],
                invariants=["state_set_membership_well_defined"],
                desired=["detect_or_break_revisitation", "ensure_progress_or_halt"],
                forbidden=["silently_loop_forever"],
            ),
            transformation_name="record_visited_and_halt_on_repeat",
            operation="maintain_visited_set_reject_reentry",
            preconditions=[
                "states_hashable_or_orderable",
                "transition_observable",
            ],
            resulting_relations=[
                "cycle_detected_or_traversal_terminates",
                "each_state_processed_at_most_once",
            ],
            preserved_invariants=["deterministic_transition_semantics"],
            relaxed_or_broken_constraints=["assumption_that_path_is_acyclic"],
            known_breakpoints=[
                "fails_if_state_identity_unstable",
                "does_not_by_itself_prove_semantic_correctness_of_map",
            ],
            evidence_pointers=[
                "docs/SEMANTIC_SHORTCUT_ROUTER.md#structural-semantic-coordinates",
                "PROPOSAL_ONLY:classic_visited_set_pattern",
            ],
            authority="PROPOSAL_ONLY",
            split_hints=["DEVELOPMENT_MEMORY"],
        )
    )

    # 5) Lexical restatement of #4 (same mechanism) — for dedup classification
    episodes.append(
        _episode(
            episode_id="OTC-V1-ALG-FINITE-REVISITATION-MARK-ARRAY",
            domain_lane="algorithms_data_structures",
            source_domain="algorithms_data_structures",
            source_context="PROPOSAL_ONLY vocabulary restatement of visited-set cycle break (mark array)",
            source_obstruction=_fp(
                "O-finite-state-revisitation-mark-array",
                "algorithms_data_structures",
                roles=["walker", "finite_state_set", "transition_map"],
                relations=["iterated_application", "possible_return_to_seen_state"],
                constraints=["finite_cardinality", "deterministic_transition"],
                failure_mechanisms=["nontermination_via_cycle", "duplicate_work_on_revisit"],
                invariants=["state_set_membership_well_defined"],
                desired=["detect_or_break_revisitation", "ensure_progress_or_halt"],
                forbidden=["silently_loop_forever"],
            ),
            transformation_name="record_visited_and_halt_on_repeat",
            operation="maintain_visited_set_reject_reentry",
            preconditions=[
                "states_hashable_or_orderable",
                "transition_observable",
            ],
            resulting_relations=[
                "cycle_detected_or_traversal_terminates",
                "each_state_processed_at_most_once",
            ],
            preserved_invariants=["deterministic_transition_semantics"],
            relaxed_or_broken_constraints=["assumption_that_path_is_acyclic"],
            known_breakpoints=[
                "fails_if_state_identity_unstable",
                "does_not_by_itself_prove_semantic_correctness_of_map",
            ],
            evidence_pointers=[
                "docs/SEMANTIC_SHORTCUT_ROUTER.md#structural-semantic-coordinates",
                "PROPOSAL_ONLY:mark_array_restatement",
            ],
            authority="PROPOSAL_ONLY",
            lineage_ids=["OTC-V1-ALG-FINITE-REVISITATION-VISITED-SET"],
            split_hints=["DEVELOPMENT_MEMORY"],
            notes="Structural duplicate / vocabulary restatement of visited-set episode.",
        )
    )

    # 6) Hostile near-miss — shared failure, different forbidden loss
    episodes.append(
        _episode(
            episode_id="OTC-V1-ALG-FINITE-REVISITATION-ALLOW-REVISIT-CACHE",
            domain_lane="algorithms_data_structures",
            source_domain="algorithms_data_structures",
            source_context="HOSTILE_NEAR_MISS: revisitation tolerated when memoized values remain valid",
            source_obstruction=_fp(
                "O-finite-state-revisitation-cache-ok",
                "algorithms_data_structures",
                roles=["walker", "finite_state_set", "transition_map"],
                relations=["iterated_application", "possible_return_to_seen_state"],
                constraints=["finite_cardinality", "deterministic_transition"],
                failure_mechanisms=["nontermination_via_cycle", "duplicate_work_on_revisit"],
                invariants=["state_set_membership_well_defined", "memo_soundness"],
                desired=["reuse_memoized_result_on_revisit"],
                forbidden=["discard_valid_memo", "force_single_visit_when_cache_hit_is_safe"],
            ),
            transformation_name="memoize_and_reuse_on_revisit",
            operation="cache_result_by_state_allow_reentry_read",
            preconditions=["pure_transition_or_sound_memo", "cache_invalidation_policy_known"],
            resulting_relations=["revisit_returns_cached_value", "work_not_duplicated"],
            preserved_invariants=["memo_soundness"],
            relaxed_or_broken_constraints=["single_visit_mandate"],
            known_breakpoints=["unsound_if_state_identity_collides", "unsound_under_mutation"],
            evidence_pointers=["PROPOSAL_ONLY:hostile_near_miss_cache_revisit"],
            authority="PROPOSAL_ONLY",
            split_hints=["HOSTILE_NEAR_MISSES", "EVALUATION_MEMORY"],
        )
    )

    # 7) Software verification / debugging
    episodes.append(
        _episode(
            episode_id="OTC-V1-SW-SHARED-MUTABLE-FLAKE-ISOLATE",
            domain_lane="software_verification_debugging",
            source_domain="software_verification_debugging",
            source_context="PROPOSAL_ONLY: flaky test from shared mutable fixture across cases",
            source_obstruction=_fp(
                "O-shared-mutable-test-state",
                "software_verification_debugging",
                roles=["test_case", "shared_fixture", "mutator", "assertor"],
                relations=["tests_mutate_shared_state", "order_dependent_assertions"],
                constraints=["parallel_or_shuffled_order_possible"],
                failure_mechanisms=["order_dependent_flake", "cross_test_contamination"],
                invariants=["each_test_logical_independence"],
                desired=["deterministic_isolated_pass_fail"],
                forbidden=["hide_flake_by_forcing_order"],
            ),
            transformation_name="isolate_fixtures_per_test",
            operation="fresh_fixture_or_transaction_rollback_per_case",
            preconditions=["fixture_clonable_or_rebuildable"],
            resulting_relations=["tests_independent", "order_shuffle_stable"],
            preserved_invariants=["asserted_behavioral_contract"],
            relaxed_or_broken_constraints=["shared_mutable_optimization"],
            known_breakpoints=["expensive_fixture_rebuild", "hidden_process_global_state"],
            evidence_pointers=["PROPOSAL_ONLY:test_isolation_pattern"],
            authority="PROPOSAL_ONLY",
            split_hints=["DEVELOPMENT_MEMORY"],
        )
    )

    # 8) Control / dynamical systems
    episodes.append(
        _episode(
            episode_id="OTC-V1-CTRL-UNSTABLE-FEEDBACK-ADD-DAMPING",
            domain_lane="control_dynamical_systems",
            source_domain="control_dynamical_systems",
            source_context="PROPOSAL_ONLY: high-gain feedback induces oscillation",
            source_obstruction=_fp(
                "O-unstable-high-gain-feedback",
                "control_dynamical_systems",
                roles=["controller", "plant", "error_signal", "actuator"],
                relations=["feedback_loop", "gain_amplifies_error"],
                constraints=["actuator_limits", "delay_in_loop"],
                failure_mechanisms=["oscillation", "actuator_saturation"],
                invariants=["stability_margin_requirement"],
                desired=["damped_stable_tracking"],
                forbidden=["remove_feedback_entirely_without_replacement"],
            ),
            transformation_name="reduce_gain_or_add_damping",
            operation="lower_proportional_gain_and_or_add_derivative_term",
            preconditions=["loop_structure_known", "gain_tunable"],
            resulting_relations=["oscillation_attenuated", "stability_margin_improved"],
            preserved_invariants=["closed_loop_tracking_objective"],
            relaxed_or_broken_constraints=["aggressive_rise_time_target"],
            known_breakpoints=["CANNOT_CHECK:plant_model_mismatch", "delay_dominant_loops"],
            evidence_pointers=["PROPOSAL_ONLY:classical_damping_intuition"],
            authority="PROPOSAL_ONLY",
            split_hints=["EVALUATION_MEMORY"],
        )
    )

    # 9) Optimization / OR
    episodes.append(
        _episode(
            episode_id="OTC-V1-OPT-LOCAL-MIN-MULTISTART",
            domain_lane="optimization_operations_research",
            source_domain="optimization_operations_research",
            source_context="PROPOSAL_ONLY: local search trapped in basin",
            source_obstruction=_fp(
                "O-local-minimum-trap",
                "optimization_operations_research",
                roles=["searcher", "objective", "basin", "init_point"],
                relations=["local_move_neighborhood", "objective_decrease_preferred"],
                constraints=["nonconvex_landscape"],
                failure_mechanisms=["premature_convergence", "basin_entrapment"],
                invariants=["objective_definition_fixed"],
                desired=["escape_basin_or_certify_local_only"],
                forbidden=["relabel_local_min_as_global_without_certificate"],
            ),
            transformation_name="multi_start_or_basin_hopping",
            operation="restart_from_diverse_inits_compare_best",
            preconditions=["restart_budget_available", "init_distribution_defined"],
            resulting_relations=["multiple_basins_sampled", "best_of_restarts_reported"],
            preserved_invariants=["objective_definition_fixed"],
            relaxed_or_broken_constraints=["single_trajectory_mandate"],
            known_breakpoints=["still_not_global_certificate", "UNKNOWN:adequate_init_coverage"],
            evidence_pointers=["PROPOSAL_ONLY:multistart_pattern"],
            authority="PROPOSAL_ONLY",
            split_hints=["DEVELOPMENT_MEMORY"],
        )
    )

    # 10) Engineering fault repair
    episodes.append(
        _episode(
            episode_id="OTC-V1-ENG-SPOF-ADD-REDUNDANCY",
            domain_lane="engineering_fault_repair",
            source_domain="engineering_fault_repair",
            source_context="PROPOSAL_ONLY: single point of failure in critical path",
            source_obstruction=_fp(
                "O-single-point-of-failure",
                "engineering_fault_repair",
                roles=["critical_component", "dependent_services", "failure_mode"],
                relations=["all_paths_through_one_component"],
                constraints=["availability_SLO"],
                failure_mechanisms=["total_outage_on_one_fault"],
                invariants=["safety_interlocks_must_remain"],
                desired=["survive_single_component_fault"],
                forbidden=["disable_safety_interlocks_to_gain_availability"],
            ),
            transformation_name="introduce_redundant_path",
            operation="add_failover_replica_or_alternate_route",
            preconditions=["failure_detection_exists", "state_replication_feasible"],
            resulting_relations=["single_fault_no_longer_total_outage"],
            preserved_invariants=["safety_interlocks_must_remain"],
            relaxed_or_broken_constraints=["minimize_component_count"],
            known_breakpoints=["correlated_failures", "failover_split_brain"],
            evidence_pointers=["PROPOSAL_ONLY:redundancy_pattern"],
            authority="PROPOSAL_ONLY",
            split_hints=["DEVELOPMENT_MEMORY"],
        )
    )

    # 11) Biology / regulatory (explicit proposal; not literature-verified)
    episodes.append(
        _episode(
            episode_id="OTC-V1-BIO-RUNAWAY-FEEDBACK-NEGATIVE-REGULATION",
            domain_lane="biology_regulatory_systems",
            source_domain="biology_regulatory_systems",
            source_context="PROPOSAL_ONLY analogy: runaway positive feedback without negative regulation",
            source_obstruction=_fp(
                "O-runaway-positive-feedback",
                "biology_regulatory_systems",
                roles=["signal", "amplifier", "effector"],
                relations=["positive_feedback_loop"],
                constraints=["finite_resource_pool"],
                failure_mechanisms=["unbounded_amplification", "resource_exhaustion"],
                invariants=["organism_viability_window"],
                desired=["restore_bounded_homeostasis"],
                forbidden=["kill_all_signaling"],
            ),
            transformation_name="add_negative_feedback_regulation",
            operation="introduce_inhibitor_or_degradation_path_on_signal",
            preconditions=["CANNOT_CHECK:concrete_pathway_identity_in_cited_source"],
            resulting_relations=["signal_bounded", "homeostasis_restored"],
            preserved_invariants=["organism_viability_window"],
            relaxed_or_broken_constraints=["unregulated_amplification"],
            known_breakpoints=[
                "surface_resemblance_insufficient_for_SOURCE_EVENT_VERIFIED",
                "pathway-specific_exceptions",
            ],
            evidence_pointers=["PROPOSAL_ONLY:textbook_negative_feedback_schema"],
            authority="PROPOSAL_ONLY",
            split_hints=["EVALUATION_MEMORY"],
        )
    )

    # 12) Organizational / workflow
    episodes.append(
        _episode(
            episode_id="OTC-V1-ORG-APPROVAL-BOTTLENECK-PARALLEL-AUDIT",
            domain_lane="organizational_workflow_systems",
            source_domain="organizational_workflow_systems",
            source_context="PROPOSAL_ONLY: single approver bottleneck stalls throughput",
            source_obstruction=_fp(
                "O-single-approver-bottleneck",
                "organizational_workflow_systems",
                roles=["requester", "sole_approver", "work_item", "audit_log"],
                relations=["all_approvals_serialize_on_one_person"],
                constraints=["compliance_requires_authorization"],
                failure_mechanisms=["queue_explosion", "idle_downstream"],
                invariants=["auditability_of_authorization"],
                desired=["higher_throughput_without_losing_audit"],
                forbidden=["approve_without_record"],
            ),
            transformation_name="delegate_with_parallel_authority_and_audit",
            operation="authorize_multiple_approvers_plus_immutable_audit_trail",
            preconditions=["delegation_policy_exists", "audit_log_writeable"],
            resulting_relations=["approvals_parallelizable", "audit_trail_intact"],
            preserved_invariants=["auditability_of_authorization"],
            relaxed_or_broken_constraints=["single_human_gate"],
            known_breakpoints=["inconsistent_delegates", "audit_log_tampering"],
            evidence_pointers=["PROPOSAL_ONLY:delegation_with_audit"],
            authority="PROPOSAL_ONLY",
            split_hints=["DEVELOPMENT_MEMORY"],
        )
    )

    # 13) Ordinary planning
    episodes.append(
        _episode(
            episode_id="OTC-V1-ORD-LOST-OBJECT-RETRACE-LAST-LOCUS",
            domain_lane="ordinary_planning_cases",
            source_domain="ordinary_planning_cases",
            source_context="PROPOSAL_ONLY everyday: lost object search",
            source_obstruction=_fp(
                "O-lost-object-unbounded-search",
                "ordinary_planning_cases",
                roles=["searcher", "missing_object", "candidate_locations"],
                relations=["object_last_seen_at_locus", "search_expands_without_bound"],
                constraints=["finite_attention_budget"],
                failure_mechanisms=["thrashing_random_search", "skipping_last_known_locus"],
                invariants=["object_conservation_in_space"],
                desired=["recover_object_or_bound_absence"],
                forbidden=["claim_absence_without_exhausting_last_known_path"],
            ),
            transformation_name="retrace_from_last_known_locus",
            operation="order_search_by_recency_path_then_expand",
            preconditions=["last_known_locus_remembered"],
            resulting_relations=["search_ordered", "last_known_path_checked_first"],
            preserved_invariants=["object_conservation_in_space"],
            relaxed_or_broken_constraints=["uniform_random_search"],
            known_breakpoints=["false_last_known_memory", "object_moved_by_other_agent"],
            evidence_pointers=["PROPOSAL_ONLY:everyday_retrace_heuristic"],
            authority="PROPOSAL_ONLY",
            split_hints=["DEVELOPMENT_MEMORY"],
        )
    )

    # 14) Formal mathematics — counterexample before forall-by-example
    episodes.append(
        _episode(
            episode_id="OTC-V1-MATH-FORALL-BY-EXAMPLES-COUNTEREXAMPLE-FIRST",
            domain_lane="formal_mathematics_theorem_proving",
            source_domain="formal_mathematics_theorem_proving",
            source_context="PROPOSAL_ONLY: attempting to establish ∀ via confirming examples only",
            source_obstruction=_fp(
                "O-forall-supported-only-by-examples",
                "formal_mathematics_theorem_proving",
                roles=["claimant", "universal_statement", "example_oracle", "adversary"],
                relations=["examples_entail_existential_support_only"],
                constraints=["statement_is_universal"],
                failure_mechanisms=["induction_from_examples_fallacy", "missed_counterexample"],
                invariants=["statement_quantifier_structure"],
                desired=["refute_or_prove_with_proper_universal_method"],
                forbidden=["promote_examples_to_proof"],
            ),
            transformation_name="search_counterexample_before_proof_attempt",
            operation="adversarial_instance_search_then_repair_statement_or_proof_plan",
            preconditions=["statement_formalizable_enough_to_test_instances"],
            resulting_relations=[
                "counterexample_found_or_instance_space_sampled",
                "examples_demoted_from_proof_status",
            ],
            preserved_invariants=["statement_quantifier_structure"],
            relaxed_or_broken_constraints=["example_sufficiency_assumption"],
            known_breakpoints=[
                "does_not_mint_proof",
                "CANNOT_CHECK:undecidable_instance_space",
            ],
            evidence_pointers=["PROPOSAL_ONLY:counterexample_first_heuristic"],
            authority="PROPOSAL_ONLY",
            split_hints=["EVALUATION_MEMORY"],
        )
    )

    # 15) Formal math — different transform on related obstruction (not collapsed)
    episodes.append(
        _episode(
            episode_id="OTC-V1-MATH-FORALL-BY-EXAMPLES-INDUCTION-SCHEMA",
            domain_lane="formal_mathematics_theorem_proving",
            source_domain="formal_mathematics_theorem_proving",
            source_context="PROPOSAL_ONLY: same quantifier obstruction, induction-schema transformation",
            source_obstruction=_fp(
                "O-forall-supported-only-by-examples-induction",
                "formal_mathematics_theorem_proving",
                roles=["claimant", "universal_statement", "example_oracle", "adversary"],
                relations=["examples_entail_existential_support_only"],
                constraints=["statement_is_universal"],
                failure_mechanisms=["induction_from_examples_fallacy", "missed_counterexample"],
                invariants=["statement_quantifier_structure"],
                desired=["refute_or_prove_with_proper_universal_method"],
                forbidden=["promote_examples_to_proof"],
            ),
            transformation_name="apply_induction_schema",
            operation="choose_well_founded_measure_and_inductive_step",
            preconditions=[
                "well_founded_measure_exists",
                "inductive_step_obligations_stated",
            ],
            resulting_relations=["proof_obligations_reduced_to_base_and_step"],
            preserved_invariants=["statement_quantifier_structure"],
            relaxed_or_broken_constraints=["example_sufficiency_assumption"],
            known_breakpoints=[
                "wrong_measure",
                "does_not_apply_to_non-inductive_universals",
            ],
            evidence_pointers=["PROPOSAL_ONLY:induction_schema_alternative"],
            authority="PROPOSAL_ONLY",
            split_hints=["HOSTILE_NEAR_MISSES"],
            notes="Same obstruction morphology family; different transformation — must not collapse with counterexample-first.",
        )
    )

    return episodes


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    corpus = ROOT / CORPUS_DIR
    corpus.mkdir(parents=True, exist_ok=True)
    (ROOT / RECEIPTS_DIR).mkdir(parents=True, exist_ok=True)

    ontology = {
        "ontology_version_id": "obstruction-transformation-corpus-ontology-v1",
        "frozen_before_bulk_collection": True,
        "frozen_at_utc": "2026-08-12T05:10:00Z",
        "fingerprint_coordinates": [
            "roles",
            "relations",
            "constraints",
            "failure_mechanisms",
            "invariants_to_preserve",
            "desired_transition",
            "forbidden_losses",
        ],
        "domain_vocabulary_policy": "Domain nouns are recorded separately from structural fingerprint coordinates and are never the structural ground truth.",
        "transformation_normalization_rules": [
            "transformation_name is a stable family label",
            "operation is the concrete act applied",
            "effects are recorded resulting_relations, not hoped-for goals",
            "every source precondition must be listed even if UNKNOWN:/CANNOT_CHECK",
        ],
        "episode_identity_policy": {
            "unique_episode_id_required": True,
            "structural_duplicate_key": "hash(sorted structural coords)",
            "equivalence_classes": [
                "same_source_same_event",
                "same_mechanism_restated_vocabulary",
                "same_transformation_materially_different_preconditions",
                "same_obstruction_different_transformation",
                "same_transformation_different_effect",
                "hostile_near_miss_shared_failure_divergent_forbidden_loss",
            ],
            "do_not_collapse_when_preconditions_or_forbidden_losses_differ": True,
        },
        "source_authority_rubric": {
            "PROPOSAL_ONLY": "Default for synthetic/generated/model-summarized candidates",
            "SOURCE_EVENT_VERIFIED": "Underlying source checked for exact O/T/O' claims",
            "VERIFIED_LOCAL": "In-repo or locally witnessed event with bound receipts",
            "PROOF_BACKED": "Machine-checked or published proof binds the transformation effect",
            "SUPERSEDED": "Retained negative/history; not a viable strict route",
        },
        "synthetic_default_authority": "PROPOSAL_ONLY",
        "promotion_rule": "Verified authorities require a SOURCE_VERIFICATION_RECEIPTS entry; model summary of a paper is insufficient.",
        "provenance_allowed_evidence_classes": [
            "in_repo_receipt_json",
            "primary_source_pointer",
            "explicit_PROPOSAL_ONLY_marker",
            "supersession_lineage_pointer",
        ],
        "version_snapshot_hashing": "snapshot_hash = semantic_shortcut._memory_hash over memory_id, source_universe, episodes, evidence_pointers",
        "correction_supersession_policy": "Corrections append SUPERSEDED lineage; never silent rewrite of prior episode content under the same episode_id.",
        "training_evaluation_leakage_policy": "Design fixtures from PR #376 tests and DEVELOPMENT construction notes must not enter EVALUATION_MEMORY / FRESH_TARGETS confirmatory partitions for #401.",
        "grants_scientific_authority": False,
    }
    write_json(corpus / "ONTOLOGY_VERSION.json", ontology)

    source_universe = {
        "manifest_id": "otc-v1-source-universe",
        "source_universe": [
            "research/paper2_oracle_capability_gate_v2_exec/",
            "research/paper2_closest_parent/",
            "research/paper2_alr_a3a4_confirmatory_prep_wave1_v1/",
            "research/STRONGEST_VERSION_CAMPAIGN_SCOREBOARD_20260812.json",
            "docs/SEMANTIC_SHORTCUT_ROUTER.md",
            "PROPOSAL_ONLY:seed_structural_exemplars_v1",
        ],
        "seed_domain_lanes": [
            "formal_mathematics_theorem_proving",
            "algorithms_data_structures",
            "software_verification_debugging",
            "control_dynamical_systems",
            "optimization_operations_research",
            "engineering_fault_repair",
            "biology_regulatory_systems",
            "scientific_experimental_method",
            "organizational_workflow_systems",
            "ordinary_planning_cases",
        ],
        "coverage_scope": "REGISTERED_SOURCE_UNIVERSE_ONLY",
        "complete_knowledge_claim": False,
        "grants_scientific_authority": False,
    }
    write_json(corpus / "SOURCE_UNIVERSE_MANIFEST.json", source_universe)

    episodes = seed_episodes()
    episodes_path = corpus / "EPISODES.jsonl"
    with episodes_path.open("w", encoding="utf-8") as handle:
        for row in episodes:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    # Verification receipts for VERIFIED_LOCAL episodes
    write_json(
        ROOT / RECEIPTS_DIR / "VR-RAKL-CAPABLE-MODEL-GATE-TERMINUS.json",
        {
            "receipt_id": "VR-RAKL-CAPABLE-MODEL-GATE-TERMINUS",
            "episode_id": "OTC-V1-RAKL-CAPABLE-MODEL-GATE-TERMINUS",
            "authority_granted": "VERIFIED_LOCAL",
            "verification_status": "PASS_LOCAL",
            "checks": [
                "obstruction_matches_recorded_capable_model_gate",
                "transformation_matches_terminal_stop_NO_REFUTED",
                "effects_match_scoreboard_and_V2_EXEC_decision_receipt",
                "preconditions_supported_by_authorized_scale_floors_and_3476813",
            ],
            "evidence_pointers": [
                "research/paper2_oracle_capability_gate_v2_exec/ORACLE_DECISION_RECEIPT_V2_EXEC.json",
                "research/STRONGEST_VERSION_CAMPAIGN_SCOREBOARD_20260812.json",
            ],
            "non_guarantees": [
                "Does not imply target-transfer validity outside RAKL campaign context",
                "Does not clear CAPABLE_MODEL_AVAILABLE",
            ],
            "grants_target_authority": False,
        },
    )
    write_json(
        ROOT / RECEIPTS_DIR / "VR-RAKL-A3A4-MATCHED-BLOCKED.json",
        {
            "receipt_id": "VR-RAKL-A3A4-MATCHED-BLOCKED",
            "episode_id": "OTC-V1-RAKL-A3A4-MATCHED-BLOCKED",
            "authority_granted": "VERIFIED_LOCAL",
            "verification_status": "PASS_LOCAL",
            "checks": [
                "obstruction_matches_issue_352_science_blocker",
                "transformation_matches_CANNOT_EXECUTE_terminal",
                "parent_packet_immutable_pointer_present",
                "non_confirmatory_3476749_not_reinterpreted",
            ],
            "evidence_pointers": [
                "research/paper2_closest_parent/ISSUE_352_TERMINAL_RECEIPT.json",
                "research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICAL_PACKET_V1.json",
            ],
            "non_guarantees": [
                "Does not answer the A3↔A4 scientific question",
                "Does not authorize confirmatory jobs",
            ],
            "grants_target_authority": False,
        },
    )

    dedup = build_dedup_report(episodes)
    write_json(corpus / "DEDUP_EQUIVALENCE_REPORT.json", dedup)

    coverage = build_coverage_report(
        episodes, source_universe=source_universe["source_universe"]
    )
    write_json(corpus / "COVERAGE_REPORT.json", coverage)

    # Splits
    by_hint: dict[str, list[str]] = {
        "DEVELOPMENT_MEMORY": [],
        "EVALUATION_MEMORY": [],
        "FRESH_TARGETS": [],
        "HOSTILE_NEAR_MISSES": [],
    }
    for row in episodes:
        for hint in row.get("split_hints") or ["DEVELOPMENT_MEMORY"]:
            by_hint.setdefault(hint, []).append(row["episode_id"])

    splits = {
        "schema_version": "obstruction-transformation-corpus-split-v1",
        "bound_issue_for_confirmatory_eval": 401,
        "partitions": {
            "DEVELOPMENT_MEMORY": {
                "episode_ids": sorted(set(by_hint["DEVELOPMENT_MEMORY"])),
                "purpose": "Corpus construction, router dry-runs, non-confirmatory tooling",
            },
            "EVALUATION_MEMORY": {
                "episode_ids": sorted(set(by_hint["EVALUATION_MEMORY"])),
                "purpose": "Held for #401 matched evaluation memory snapshot; not for silent redesign after outcomes",
            },
            "FRESH_TARGETS": {
                "episode_ids": [],
                "target_fingerprints": [],
                "purpose": "Fresh obstruction targets for #401; empty until #401 freezes targets pre-outcome",
            },
            "HOSTILE_NEAR_MISSES": {
                "episode_ids": sorted(set(by_hint["HOSTILE_NEAR_MISSES"])),
                "purpose": "Near-miss controls where shared failure morphology must not auto-license transfer",
            },
        },
        "design_fixture_exclusion": [
            "A",
            "B",
            "D",
            "J",
            "Z-verified",
        ],
        "grants_scientific_authority": False,
    }
    write_json(corpus / "SPLIT_MANIFEST.json", splits)

    leakage = {
        "schema_version": "obstruction-transformation-corpus-leakage-audit-v1",
        "design_fixture_episode_ids_excluded": ["A", "B", "D", "J", "Z-verified"],
        "design_fixture_source": "tests/test_semantic_shortcut.py (PR #376)",
        "evaluation_memory_disjoint_from_design_fixtures": True,
        "fresh_targets_disjoint_from_design_fixtures": True,
        "post_outcome_literature_policy": "If external literature is added after #401 target outcomes are visible, version a later evaluation epoch rather than mutating this snapshot.",
        "grants_scientific_authority": False,
    }
    write_json(corpus / "LEAKAGE_AUDIT.json", leakage)

    retrieval_eval = {
        "schema_version": "obstruction-transformation-corpus-retrieval-eval-v1",
        "status": "INSTRUMENT_ONLY_NOT_CONFIRMATORY",
        "owned_by_issue": 402,
        "confirmatory_efficacy_owned_by_issue": 401,
        "metrics_registered": [
            "recall_at_k_known_useful_episodes",
            "structural_near_miss_rate",
            "proposal_only_crowding_rate",
            "full_vs_partial_effect_classification_accuracy",
            "candidate_coverage_under_bounded_search",
            "latency_index_size_retrieval_cost",
        ],
        "scores": None,
        "note": "Retrieval scores do not imply valid JUMP; target mapping remains a separate witness. Confirmatory measurement is #401.",
        "grants_scientific_authority": False,
    }
    write_json(corpus / "RETRIEVAL_EVALUATION.json", retrieval_eval)

    # Build runtime memory snapshot
    runtime_episodes = [
        episode_from_dict(_runtime_payload(row)) for row in episodes
    ]

    memory = build_transformation_memory(
        memory_id="otc-v1-seed-memory",
        source_universe=tuple(source_universe["source_universe"]),
        episodes=tuple(runtime_episodes),
        evidence_pointers=(
            "research/obstruction_transformation_corpus_v1/EPISODES.jsonl",
            "research/obstruction_transformation_corpus_v1/ONTOLOGY_VERSION.json",
            "research/obstruction_transformation_corpus_v1/SOURCE_UNIVERSE_MANIFEST.json",
            "research/obstruction_transformation_corpus_v1/SOURCE_VERIFICATION_RECEIPTS/",
        ),
    )

    snapshot_manifest = {
        "schema_version": "obstruction-transformation-corpus-snapshot-v1",
        "memory_id": memory.memory_id,
        "snapshot_hash": memory.snapshot_hash,
        "episode_count": len(memory.episodes),
        "source_universe": list(memory.source_universe),
        "evidence_pointers": list(memory.evidence_pointers),
        "ontology_version_id": ontology["ontology_version_id"],
        "complete_knowledge_claim": False,
        "grants_scientific_authority": False,
        "runtime_loadable": True,
        "loader": "rakl.obstruction_transformation_corpus.load_transformation_memory",
    }
    write_json(corpus / "SNAPSHOT_MANIFEST.json", snapshot_manifest)

    # Serializable memory JSON for inspection (episodes as runtime payloads)
    memory_json = {
        "memory_id": memory.memory_id,
        "source_universe": list(memory.source_universe),
        "evidence_pointers": list(memory.evidence_pointers),
        "snapshot_hash": memory.snapshot_hash,
        "episodes": [_runtime_payload(r) for r in episodes],
    }
    write_json(corpus / "MEMORY_SNAPSHOT.json", memory_json)

    protocol = """# Obstruction–Transformation Episode Corpus Protocol v1

**Issue:** #402  
**Status:** `TRANSFORMATION_MEMORY / PROVENANCE_FIRST / COVERAGE_MEASURED / NO_SYNTHETIC_AUTHORITY`  
**Ontology:** frozen before seed collection (`ONTOLOGY_VERSION.json`)

## Unit of storage

```text
O = relational obstruction (structural fingerprint)
T = transformation under explicit preconditions
O' = observed/verified changed relations
```

## Authority

| Class | Meaning |
|-------|---------|
| PROPOSAL_ONLY | Default for synthetic/generated/model-summarized candidates |
| SOURCE_EVENT_VERIFIED | Underlying source checked for exact O/T/O' |
| VERIFIED_LOCAL | In-repo/local event with verification receipt |
| PROOF_BACKED | Proof binds the transformation effect |
| SUPERSEDED | History/negative; not a strict viable route |

Synthetic candidates **cannot** become strict verified SEARCH/JUMP routes by default.

## Phases covered by this seed release

0. Ontology/identity/authority/provenance/hash/leakage rules frozen  
1. Heterogeneous seed lanes populated (structural diversity, not equal paper counts)  
2. Two-stage extraction pattern recorded; only local RAKL events verified in v1  
3. Structural dedup/equivalence report emitted  
4. Coverage metrology emitted (scoped to registered source universe)  
5. Disjoint splits frozen for #401 (`SPLIT_MANIFEST.json`)  
6. Retrieval metrics registered but **not** scored confirmatory here (#401 owns efficacy)

## Non-claims

- Not complete knowledge  
- Not theorem/scientific authority  
- Not #401 confirmatory efficacy  
- Proposal-only episodes guide search only
"""
    (corpus / "CORPUS_PROTOCOL.md").write_text(protocol, encoding="utf-8")

    changelog = """# CHANGELOG — obstruction_transformation_corpus_v1

## 2026-08-12 — v1 seed

- Freeze ontology/identity/authority/provenance/hash/leakage rules before bulk collection.
- Seed 15 episodes across 10 domain lanes.
- Verify two in-repo RAKL events as `VERIFIED_LOCAL` with receipts.
- Keep remaining structural exemplars as `PROPOSAL_ONLY` (and one `SUPERSEDED`).
- Emit dedup, coverage, split, leakage, and deterministic `snapshot_hash`.
- Register retrieval metrics without confirmatory scores (#401 owns efficacy).
"""
    (corpus / "CHANGELOG.md").write_text(changelog, encoding="utf-8")

    report = validate_corpus(ROOT)
    print(json.dumps({
        "ok": report.ok,
        "memory_id": report.memory_id,
        "snapshot_hash": report.snapshot_hash,
        "episode_count": report.episode_count,
        "authority_counts": dict(report.authority_counts),
        "domain_counts": dict(report.domain_counts),
        "reasons": list(report.reasons),
    }, indent=2))
    if not report.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
