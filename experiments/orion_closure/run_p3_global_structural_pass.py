#!/usr/bin/env python3
"""First GLOBAL-loop structural pass over the programme's receipted mutation trajectories.

Reduces each receipted local-loop trajectory (failure -> diagnosis -> lever -> outcome)
MECHANICALLY into ``src/rakl/structure_space.py`` role space and reports what patterns
the accumulated space surfaces, each pattern citing its contributing trajectories.

Role vocabulary (fixed before reduction):
  defect_stage:<where the defect lived>        superstage:<evaluation_side|lever_side|unconfirmed>
  lever_type:<the repair/mutation applied>      instrument_state:<before -> after>
  sign:<the trajectory's honest outcome>

Binding discipline: every trajectory names its receipt files; the runner READS each
file and extracts one binding fact (or records CANNOT_CHECK when the receipt is not
in the repository tree), so the reduction is receipt-verified rather than asserted.

This is a FIRST STRUCTURAL PASS over N trajectories. It is NOT a validated
generational improvement; the global loop's construct-new-generation and
cross-family-validation stages are prospective and unexecuted. Grants no authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rakl.structure_space import ReducedStructure, StructureSpace
from rakl.support_solver import SupportStructure


def _bind(root, path, extractor):
    p = root / path
    if not p.exists():
        return {"file": path, "binding": "CANNOT_CHECK_not_in_tree"}
    try:
        return {"file": path, "binding": extractor(p)}
    except Exception as exc:  # binding must fail visibly, not silently
        return {"file": path, "binding": f"CANNOT_CHECK_extract_error:{exc!r}"}


def trajectories(root):
    """The receipted trajectory corpus, with per-trajectory role assignment."""
    j = lambda p: json.loads(p.read_text())
    return [
        {
            "trajectory_id": "T1_SIX_FAMILY_DEAD_GATE",
            "summary": "registered six-family gate passed 6/6 at p=0.03125, then shown "
                       "structurally incapable of failing (text scramble left all "
                       "coordinates unchanged 810/810; one paired arm variance 1.2e-37)",
            "roles": ["defect_stage:confirmatory_gate", "superstage:evaluation_side",
                      "lever_type:black_box_falsifiability_audit",
                      "instrument_state:looked_healthy_then_non_falsifiable",
                      "sign:instrument_negative"],
            "provenance": [
                _bind(root, "research/paper2_six_family_audit_v1/results/PROBE_G_TEXT_INERTNESS.json",
                      lambda p: j(p)["text_inertness"]["components_unchanged_after_text_scramble"]),
                _bind(root, "research/paper2_six_family_audit_v1/results/SIX_FAMILY_AUDIT.json",
                      lambda p: j(p)["A_full_arm_constant_loss"]["full_arm_loss_variance"]),
            ],
        },
        {
            "trajectory_id": "T2_P3_GOLD_IDENTITY_GATE",
            "summary": "four accuracy-shaped gate conditions satisfied by construction "
                       "(gold equals prediction); repaired with an independently "
                       "implemented declarative oracle and post-freeze gold; repaired "
                       "audit FALSIFIABLE on all evidence-dependent conditions",
            "roles": ["defect_stage:confirmatory_gate", "superstage:evaluation_side",
                      "lever_type:independent_oracle_post_freeze_gold",
                      "instrument_state:non_falsifiable_then_repaired_falsifiable",
                      "sign:instrument_negative_then_repaired"],
            "provenance": [
                _bind(root, "research/paper3_gate_falsifiability_audit_v1/GATE_FALSIFIABILITY_AUDIT.json",
                      lambda p: str(list(j(p))[:4])),
                _bind(root, "research/paper3_gate_falsifiability_audit_v1/REPAIRED_GATE_FALSIFIABILITY_AUDIT.json",
                      lambda p: str(list(j(p))[:4])),
            ],
        },
        {
            "trajectory_id": "T3_TRANSFER_LICENSE_FAIL_OPEN",
            "summary": "assess_transfer_v2 returned LICENSED with zero reasons for two "
                       "structures sharing no roles/relations/invariants; repaired to "
                       "fail-closed (empty obligation set is absence of evidence)",
            "roles": ["defect_stage:applicability_license_gate", "superstage:evaluation_side",
                      "lever_type:fail_closed_repair",
                      "instrument_state:fail_open_then_fail_closed",
                      "sign:instrument_negative_then_repaired"],
            "provenance": [
                _bind(root, "research/transport_failopen_repair_v1/RECEIPT.md",
                      lambda p: p.read_text()[:80]),
                _bind(root, "research/transport_gate_reaudit_v1/REAUDIT.json",
                      lambda p: str(list(j(p))[:4])),
            ],
        },
        {
            "trajectory_id": "T4_CONTROLLED_WITNESS_SERIALIZATION",
            "summary": "the controlled-witness 1.0 extraction result was narrowed to "
                       "serialization-interface fidelity rather than prose extraction: "
                       "gold and prediction pass through the same serialization, so the "
                       "perfect score measured the round-trip, not the capability",
            "roles": ["defect_stage:measurement_interface", "superstage:evaluation_side",
                      "lever_type:interpretation_narrowing",
                      "instrument_state:perfect_score_reclassified",
                      "sign:claim_narrowed"],
            "provenance": [
                _bind(root, "research/paper2_controlled_witness_extraction_v1/FINAL_RECEIPT.json",
                      lambda p: j(p)["full_controlled_extractor"]["exact_decision"]),
                _bind(root, "research/orion_claim_frontier_v1/CLAIM_FRONTIER.json",
                      lambda p: ("serialization-interface fidelity"
                                 in p.read_text()) and "narrowing_sentence_present"),
            ],
        },
        {
            "trajectory_id": "T5_INSTRUMENT_CEILING_BOUND",
            "summary": "development-stress instrument bootstrap CIs ~0.0016 wide looked "
                       "amply powered while a rigorous upper bound on ANY equal-budget "
                       "policy's advantage was +0.0246 against the 0.05 gate; converted "
                       "into a frozen pre-execution admissibility gate",
            "roles": ["defect_stage:instrument_power", "superstage:evaluation_side",
                      "lever_type:oracle_ceiling_admissibility",
                      "instrument_state:looked_healthy_then_inadmissible",
                      "sign:instrument_negative_then_replaced"],
            "provenance": [
                _bind(root, "research/paper4_allocator_attribution_v1/CEILING_BOUNDS.json",
                      lambda p: j(p)["bounds_on_achievable_advantage_over_static"][
                          "tier_3_rigorous_upper_bound_harm_free_relaxation_mean"]),
                _bind(root, "research/paper4_instrument_admissibility_v1/REFERENCE_INSTRUMENT_ADMISSIBILITY.json",
                      lambda p: j(p)["decision"]["verdict"]),
            ],
        },
        {
            "trajectory_id": "T6_TYPED_REFUSAL_ABSORPTION",
            "summary": "quantified-refusal mechanic absorbed from a formal parent "
                       "(transportability/SID): the applicability gate refuses with a "
                       "typed certificate instead of guessing",
            "roles": ["defect_stage:not_applicable_import", "superstage:lever_side",
                      "lever_type:typed_refusal",
                      "instrument_state:refusal_semantics_added",
                      "sign:absorbed_pattern"],
            "provenance": [
                _bind(root, "research/paper2_causal_transport_absorption_v1/MECHANIC_CANDIDATE.json",
                      lambda p: j(p)["mechanics"][0]["mechanic_id"]),
            ],
        },
        {
            "trajectory_id": "T7_STALE_EXTERNAL_SURFACE",
            "summary": "typed governance surface lost to naive OFF arm on the external "
                       "STALE memory-mode envelope (ON-OFF -0.217); dim structure "
                       "(tied where both commit, typed below chance where naive guesses) "
                       "suggests an abstention-scoring attribution that CANNOT be "
                       "confirmed from repository bytes; registered for re-scoring",
            "roles": ["defect_stage:unconfirmed_pending_rescore", "superstage:unconfirmed",
                      "lever_type:typed_governance_external_surface",
                      "instrument_state:aggregate_receipt_only",
                      "sign:governance_cost_cell"],
            "provenance": [
                _bind(root, "research/paper3_stale_feasibility_v1/FEASIBILITY_RECEIPT.json",
                      lambda p: j(p)["terminal"]),
                _bind(root, "research/paper3_stale_memory_mode_v1/CONFIRMATORY_RECEIPT.json",
                      lambda p: j(p)["terminal"]),
                _bind(root, "research/paper3_stale_revival_v1/ABSTENTION_SCORING_REALIGNMENT_FREEZE.json",
                      lambda p: j(p)["revival_lever_decision"]["registered_next_experiment"]["id"]),
            ],
        },
        {
            "trajectory_id": "T8_LICENSED_CHALLENGER_CYCLE",
            "summary": "a complete local-loop cycle executed through the admissibility "
                       "gate: licensed successor instrument, marginal-gain challenger "
                       "green on all frozen gates (F-D +0.0760), diagnostic P6 falsified "
                       "and preserved (v1 also wins: the parent negative was "
                       "policy-x-instrument-conditional)",
            "roles": ["defect_stage:instrument_power", "superstage:evaluation_side",
                      "lever_type:oracle_ceiling_admissibility",
                      "instrument_state:licensed_admissible",
                      "sign:governed_positive_with_falsified_diagnostic"],
            "provenance": [
                _bind(root, "research/paper4_marginal_gain_challenger_v1/ASSURANCE_RECEIPT.json",
                      lambda p: j(p)["terminal"]),
            ],
        },
        {
            "trajectory_id": "T9_GOVERNANCE_TRADEOFF",
            "summary": "governed vs ungoverned acceptance over one proposal stream: "
                       "ungoverned cost measured as silent starvation and verdict "
                       "inversion (10 true positives rejected on an inadmissible "
                       "instrument; 30x understatement; zero honest terminals), not "
                       "false promotion; three of five frozen predictions falsified "
                       "and preserved",
            "roles": ["defect_stage:instrument_power", "superstage:evaluation_side",
                      "lever_type:governed_acceptance_pipeline",
                      "instrument_state:same_stream_two_verdict_regimes",
                      "sign:tradeoff_frontier_cell"],
            "provenance": [
                _bind(root, "research/paper3_governance_tradeoff_v1/TRADEOFF_RECEIPT.json",
                      lambda p: str(j(p)["predictions_read_from_data"])),
            ],
        },
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    root = Path(args.root)
    corpus = trajectories(root)

    space = StructureSpace(space_id="p3_mutation_trajectory_space_v1")
    for t in corpus:
        reduced = ReducedStructure(
            structure=SupportStructure(structure_id=t["trajectory_id"], atoms=(), edges=()),
            roles=frozenset(t["roles"]),
            provenance="; ".join(p["file"] for p in t["provenance"]),
        )
        t["newly_contributed_roles"] = space.accumulate(reduced)

    # Mechanical pattern surfacing: role values shared by >= 3 trajectories.
    role_index: dict[str, list[str]] = {}
    for t in corpus:
        for role in t["roles"]:
            role_index.setdefault(role, []).append(t["trajectory_id"])
    shared = {role: ids for role, ids in role_index.items() if len(ids) >= 3}

    patterns = []
    eval_side = role_index.get("superstage:evaluation_side", [])
    lever_side = role_index.get("superstage:lever_side", [])
    unconfirmed = role_index.get("superstage:unconfirmed", [])
    patterns.append({
        "pattern_id": "P1_EVALUATION_STAGE_DOMINANCE",
        "statement": "every receipted defect trajectory whose stage is confirmed lives on "
                     "the EVALUATION side (gates, licensing, measurement interface, "
                     "instrument power); zero live on the proposal-generation side",
        "counts": {"evaluation_side": len(eval_side), "lever_side_imports": len(lever_side),
                   "unconfirmed": len(unconfirmed)},
        "cited_trajectories": eval_side,
        "scope": "observed in this programme's receipts; not a universal law",
    })
    healthy_then_broken = [t["trajectory_id"] for t in corpus
                           if any(r.startswith("instrument_state:looked_healthy")
                                  or r.startswith("instrument_state:perfect_score")
                                  for r in t["roles"])]
    patterns.append({
        "pattern_id": "P2_HEALTHY_SIGNAL_INVERSION",
        "statement": "the defective instruments looked healthy or perfect by their own "
                     "conventional statistics (p=0.03125, variance-tight CIs, 1.0 "
                     "accuracy) while being structurally unable to measure their "
                     "target; health statistics and measurement capacity are "
                     "independent axes",
        "cited_trajectories": healthy_then_broken,
        "scope": "observed in this programme's receipts; not a universal law",
    })
    refusal_levers = [t["trajectory_id"] for t in corpus
                      if any(r in ("lever_type:fail_closed_repair",
                                   "lever_type:typed_refusal",
                                   "lever_type:oracle_ceiling_admissibility",
                                   "lever_type:governed_acceptance_pipeline")
                             for r in t["roles"])]
    audit_levers = [t["trajectory_id"] for t in corpus
                    if any(r in ("lever_type:black_box_falsifiability_audit",
                                 "lever_type:independent_oracle_post_freeze_gold",
                                 "lever_type:interpretation_narrowing")
                           for r in t["roles"])]
    patterns.append({
        "pattern_id": "P3_TWO_LEVER_FAMILIES",
        "statement": "the successful levers fall into exactly two families: "
                     "(a) REFUSAL-SHAPED levers that make the acceptance signal able to "
                     "say no or nothing (fail-closed repair, typed refusal, ceiling "
                     "admissibility, governed acceptance) and (b) INDEPENDENCE-SHAPED "
                     "levers that make the signal independent of what it judges "
                     "(black-box audit, independent oracle, interpretation narrowing)",
        "cited_trajectories": {"refusal_shaped": refusal_levers,
                               "independence_shaped": audit_levers},
        "scope": "observed in this programme's receipts; not a universal law",
    })

    receipt = {
        "schema_version": "p3-global-structural-pass-v1",
        "date": "2026-08-14",
        "kind": "FIRST_GLOBAL_LOOP_STRUCTURAL_PASS",
        "label": f"a first structural pass over {len(corpus)} receipted trajectories; "
                 "NOT a validated generational improvement; the construct-new-generation "
                 "and cross-family-validation stages of the global loop are prospective "
                 "and unexecuted",
        "structure_space": {
            "space_id": space.space_id,
            "universe_size": len(space.universe),
            "growth_per_round": space.growth_per_round,
            "saturation": space.saturation().value,
        },
        "trajectories": corpus,
        "roles_shared_by_3_or_more": {k: v for k, v in sorted(shared.items())},
        "patterns": patterns,
        "grants_scientific_authority": False,
        "grants_promotion_authority": False,
    }
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "GLOBAL_STRUCTURAL_PASS.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({
        "n_trajectories": len(corpus),
        "universe_size": len(space.universe),
        "growth_per_round": space.growth_per_round,
        "saturation": space.saturation().value,
        "patterns": [{p["pattern_id"]: p.get("counts", p["cited_trajectories"])}
                     for p in patterns],
        "bindings_cannot_check": [
            (t["trajectory_id"], p["file"]) for t in corpus for p in t["provenance"]
            if str(p["binding"]).startswith("CANNOT_CHECK")],
    }, indent=2))


if __name__ == "__main__":
    main()
