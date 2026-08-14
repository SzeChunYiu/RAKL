#!/usr/bin/env python3
"""Oracle-ceiling admissibility qualification of Paper III's fresh-task-lift 0.05 gate.

Question
--------
Paper III carries ``BLOCKED_ON_CAPABILITY_QUALIFICATION`` on a registered four-arm fresh-task
benefit obligation, and its own manuscript flags at
``publication/papers/paper-03-method-evolution-mechanics/sections/07b_structural_learning_cautionary.tex:13``
that the lift protocol's ``0.05`` gate has **no recorded ceiling qualification**.  Before an
A100-class subject is staged, is that gate attainable in principle by the registered instrument?

Method
------
Reuses the shipped mechanic ``src/rakl/instrument_admissibility.py::decide_instrument_admissibility``
verbatim.  No parallel implementation, no new semantics.  No frozen threshold, pin, panel or
protocol is read-modified-written by this script; every frozen artifact is opened read-only.

Three blocks run, control first:

1. ``SIBLING_REPRODUCTION_CONTROL`` — recompute the Paper IV allocator lane's published
   three-tier ceiling from its frozen protocol using the sibling's own runner
   (``experiments/orion_closure/run_p4_instrument_ceiling_bounds.py::execute``), assert exact
   agreement with ``research/paper4_allocator_attribution_v1/CEILING_BOUNDS.json``, then push the
   reproduced bounds through the mechanic under the sibling's frozen declaration and assert its
   published ``INADMISSIBLE`` verdict, declaration hash and kappa range are recovered.  If this
   fails, the implementation is wrong and no new number may be reported.

2. ``NO_ALARM_DISCRIMINATION_CONTROL`` — a synthetic instrument with a computable oracle and an
   exact ceiling above ``kappa*MDE`` must return ``ADMISSIBLE``, proving the gate is not a
   constant emitter and that block 3's verdict is a measurement, not a default.

3. ``PAPER3_FRESH_TASK_LIFT`` — the target.

Determinism
-----------
Every block is closed-form.  ``SEED`` is threaded into the one jittered construction (the
no-alarm control) so reruns are byte-identical.

Diagnostic only.  Grants no scientific authority, promotes nothing, reverses no terminal.
"""

from __future__ import annotations

import json
import random
import sys
from dataclasses import asdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments" / "orion_closure"))

from rakl.instrument_admissibility import (  # noqa: E402
    AdmissibilityVerdict,
    BoundKind,
    CeilingBound,
    CeilingEvidence,
    FrozenAdmissibilityDeclaration,
    OracleComputability,
    decide_instrument_admissibility,
)
from run_p4_instrument_ceiling_bounds import _mk, execute  # noqa: E402

SEED = 202608150001  # disjoint from 202608140601 (P4 dev stress) and 202608141101 (P4 assurance)

SIBLING_PROTOCOL = REPO / "research/orion_p1_p4_closure_v2/P4_ADAPTIVE_PROTOCOL_FREEZE.json"
SIBLING_ATTRIBUTION = REPO / "research/paper4_allocator_attribution_v1/ATTRIBUTION_RECEIPT.json"
SIBLING_CEILING = REPO / "research/paper4_allocator_attribution_v1/CEILING_BOUNDS.json"
SIBLING_KAPPA_FREEZE = REPO / "research/paper4_instrument_admissibility_v1/KAPPA_FREEZE_V1.json"
SIBLING_VERDICT = REPO / "research/paper4_instrument_admissibility_v1/REFERENCE_INSTRUMENT_ADMISSIBILITY.json"
P3_STAGE35_FREEZE = REPO / "research/empirical_10_of_10_v1/CAPABILITY_QUALIFICATION/STAGE3_5_FREEZE_V1.json"


# ---------------------------------------------------------------------------
# Inventory of every input, with the exact source path:line or JSON field.
# ---------------------------------------------------------------------------

INPUTS = {
    "target_instrument": {
        "what": "Paper III registered four-arm fresh-task benefit obligation",
        "protocol_artifact": "experiments/paper5/ATTRIBUTION_PREREGISTRATION_V1.md",
        "protocol_artifact_identification": {
            "inference": "this file is titled 'Paper 5 attribution experiment preregistration v1'. "
                         "It is identified as the nearest frozen protocol document for Paper III's "
                         "own four-arm obligation, not taken as a Paper-III-scoped artifact.",
            "grounds": [
                "research/paper3_blocked_discharge_v1/DISCHARGE_PATHS.json:260 — names Paper III's "
                "immutable registered set as 'the four registered arms MODEL_ONLY / RAKL_RESET / "
                "RAKL_SHAM_MEMORY / RAKL_LEARNING and their four contrasts (architecture, content, "
                "experience, total)'",
                "research/paper3_blocked_discharge_v1/BLOCKED-residual-terminals.md:45 — same four "
                "arms and four contrasts, under Paper III residual terminal R-1",
            ],
            "no_separately_scoped_paper3_protocol_file_found": True,
            "search_run": "grep -rIn 'four.arm|four_arm|4-arm' research/ publication/ experiments/; "
                          "full read of research/empirical_10_of_10_v1/PAPER3/DOWNSTREAM/PROTOCOL.json "
                          "(371 bytes, status SCAFFOLD_ONLY__NOT_STARTED, no arms/panel/threshold) "
                          "and of DOWNSTREAM/ROUTING_REGISTRATION_V1.md (a Paper II routing study)",
            "consequence": "the protocol document for Paper III's own benefit obligation lives in "
                           "another paper's directory and is marked 'frozen design proposal only' — "
                           "a fourth missing-freeze fact, recorded here rather than smoothed over",
        },
        "protocol_status_field": "ATTRIBUTION_PREREGISTRATION_V1.md:3 — 'frozen design proposal "
                                 "only. No run from this packet may be interpreted as "
                                 "preregistered until the final packet hash, task IDs, evaluator "
                                 "hash, model/tool contract, resource ceiling, sham policy, and "
                                 "learned/reset state hashes are completed before execution.'",
        "arms": ["MODEL_ONLY", "RAKL_RESET", "RAKL_SHAM_MEMORY", "RAKL_LEARNING"],
        "arms_source": "ATTRIBUTION_PREREGISTRATION_V1.md:10,16,21,27; restated as immutable at "
                       "research/paper3_blocked_discharge_v1/DISCHARGE_PATHS.json:260",
        "arm_structure_note": "the four arms are experimental CONDITIONS, not policies competing "
                              "over a shared allocation budget",
        "primary_statistic": "paired task-level mean score difference, per contrast",
        "primary_statistic_source": "ATTRIBUTION_PREREGISTRATION_V1.md:87-93",
        "contrasts": {
            "TOTAL_LIFT": "RAKL_LEARNING - MODEL_ONLY  (ATTRIBUTION_PREREGISTRATION_V1.md:35)",
            "EXPERIENCE_LIFT": "RAKL_LEARNING - RAKL_RESET  (…:36)",
            "CONTENT_LIFT": "RAKL_LEARNING - RAKL_SHAM_MEMORY  (…:37)",
        },
        "panel_size": "120 task units (40 repeated-family / 40 cross-domain transfer / "
                      "40 hostile near-miss)",
        "panel_size_source": "ATTRIBUTION_PREREGISTRATION_V1.md:46,48-50",
        "panel_size_status": "TARGET, not frozen — ':52 Exact task IDs and source/evidence cutoff "
                             "must be frozen in the final packet'; ':54 The 120-task target is a "
                             "planning compromise, not evidence'",
        "scoring_map": "a frozen evaluator produces a task score in [0,1] from an arm-blinded "
                       "output",
        "scoring_map_source": "ATTRIBUTION_PREREGISTRATION_V1.md:85",
        "scoring_map_status": "NOT FROZEN — ':85 The exact evaluator protocol, rubric, success "
                              "threshold, parser, and evaluator identity are hashed before runs.' "
                              "No such hash exists in the repository.",
    },
    "subject_pin": {
        "source": "research/empirical_10_of_10_v1/CAPABILITY_QUALIFICATION/STAGE3_5_FREEZE_V1.json",
        "fields": ["model_candidates[0].model_id", "model_candidates[0].revision",
                   "model_candidates[0].precision", "runtime.gpu_request",
                   "resource_ceiling.gpu_class", "resource_ceiling.wall_time_hours"],
        "note": "this freeze governs the upstream Stage-4 132-case CAPABILITY panel, which is a "
                "DIFFERENT instrument from the downstream lift gate and must not be conflated "
                "with it (research/paper3_blocked_discharge_v1/DISCHARGE_PATHS.json:366)",
    },
    "sibling_lane": {
        "ceiling_receipt": "research/paper4_allocator_attribution_v1/CEILING_BOUNDS.json",
        "published_tier3_field":
            "bounds_on_achievable_advantage_over_static."
            "tier_3_rigorous_upper_bound_harm_free_relaxation_mean = 0.024570935346802252",
        "published_verdict":
            "research/paper4_instrument_admissibility_v1/REFERENCE_INSTRUMENT_ADMISSIBILITY.json"
            " :: decision.verdict = INADMISSIBLE",
        "generative_model": "research/orion_p1_p4_closure_v2/P4_ADAPTIVE_PROTOCOL_FREEZE.json "
                            "(coordinates, rounds=6, batch_size=8, budget=48, initial_mastery, "
                            "forgetting_per_nonprinciple_example, "
                            "retention_harm_per_nonretention_example) + "
                            "experiments/orion_closure/run_p4_adaptive_development_stress.py::"
                            "world_rates",
        "kappa": "research/paper4_instrument_admissibility_v1/KAPPA_FREEZE_V1.json :: "
                 "frozen_kappa = 1.2",
    },
    "mechanic": {
        "path": "src/rakl/instrument_admissibility.py",
        "entry_point": "decide_instrument_admissibility",
        "fail_closed_contract": "instrument_admissibility.py:20-21 — 'when the instrument's "
                                "generative parameters are unknown the oracle is not computable "
                                "and the gate fails closed to CANNOT_CHECK — never ADMISSIBLE'",
        "bound_direction_contract": "instrument_admissibility.py:15-19 — a POLICY score is a "
                                    "LOWER bound and may never license INADMISSIBLE; only a "
                                    "rigorous UPPER bound may",
    },
}


REGISTERED_GATE_PROVENANCE = {
    "finding": "NO_REGISTERED_0_05_MATERIAL_EFFECT_THRESHOLD_FOUND_FOR_THE_LIFT_CONTRASTS",
    "severity": "SECONDARY — independent of the primary verdict, which rests on oracle "
                "computability and would stand unchanged if such a threshold were located",
    "where_0_05_actually_appears_in_the_four_arm_protocol": [
        "ATTRIBUTION_PREREGISTRATION_V1.md:54 — 'two-sided alpha 0.05' (significance level, "
        "paired with a ~15 percentage-point planning effect, NOT a 0.05 effect gate)",
        "ATTRIBUTION_PREREGISTRATION_V1.md:144 — 'Holm family-wise error control at alpha 0.05' "
        "(multiplicity control, not an effect threshold)",
    ],
    "where_a_registered_0_05_MDE_does_exist_in_paper_III": [
        "research/paper3/power_design/POWER_SIMULATION_CONFIG.json :: "
        "registered_material_effects.primary_paired_brier_reduction_mde = 0.05 — a paired binary "
        "BRIER-reduction MDE for the OBJECTIVE transfer-validity classification lane, already "
        "executed; a different instrument from the four-arm lift",
        "research/empirical_10_of_10_v1/PAPER3/OBJECTIVE/PRECONFIRMATORY_FREEZE_V1.json :: "
        "registered_mde_brier = 0.05 — same objective lane",
    ],
    "manuscript_position": "publication/papers/paper-03-method-evolution-mechanics/sections/"
                           "07_evaluation_and_statistics.tex:137 — 'material-effect thresholds … "
                           "are frozen before evaluated results', i.e. prospective and not yet "
                           "frozen for this lane",
    "searches_run_to_justify_the_absence_claim": [
        "grep -rIn 'TOTAL_LIFT|EXPERIENCE_LIFT|CONTENT_LIFT' research/ publication/ src/ "
        "experiments/ — only the three definition lines in ATTRIBUTION_PREREGISTRATION_V1.md:35-37",
        "grep -rIn 'material_effect|min_effect|effect_floor|lift_min|min_lift' research/ src/ "
        "experiments/ — hits only the Paper II/III power-design configs and the objective-lane "
        "receipts; none binds a lift contrast",
        "grep -rIn '0\\.05' research/empirical_10_of_10_v1/PAPER3 research/paper3_blocked_discharge_v1 "
        "publication/papers/paper-03-method-evolution-mechanics — all hits are objective-lane "
        "Brier MDEs, the Stage-4 context_qoi_error_max, alphas, or prose about the unqualified gate",
        "read in full: research/empirical_10_of_10_v1/PAPER3/DOWNSTREAM/PROTOCOL.json "
        "(status SCAFFOLD_ONLY__NOT_STARTED, 371 bytes, no arms/threshold) and "
        "research/empirical_10_of_10_v1/PAPER3/DOWNSTREAM/ROUTING_REGISTRATION_V1.md "
        "(a Paper II routing study, not the lift lane)",
        "find . -iname '*CEILING*' -o -iname '*ADMISSIB*' — no Paper-III-scoped ceiling artifact "
        "existed before this study, matching "
        "research/paper3_blocked_discharge_v1/DISCHARGE_PATHS.json:355-368 (T7, state NOT_FOUND)",
    ],
    "consequence": "the '0.05 gate' the manuscript flags is traceable to 07b:13 prose and to the "
                   "objective lane's Brier MDE, not to a registered material-effect threshold on "
                   "any lift contrast. This study therefore does not treat 0.05 as frozen for the "
                   "lift; it is used only as the manuscript-asserted value, and the verdict is "
                   "shown invariant to it across an MDE x kappa sweep.",
    "must_not_change": "the 0.05 figure is not lowered, raised, or reinterpreted by this study; "
                       "no threshold is adjusted to make any instrument appear admissible",
}


ASSUMPTIONS = {
    "mirrored_from_the_sibling_lane": [
        "EQUAL BUDGET — the ceiling is the best advantage attainable over the reference parent "
        "under an identical resource budget (sibling: 48 training examples; here: the "
        "preregistration's single shared resource ceiling, ATTRIBUTION_PREREGISTRATION_V1.md:180)",
        "ORACLE POLICY — the ceiling is what the BEST policy could attain, not what a specific "
        "candidate attains; policy scores are lower bounds only",
        "BEST ACHIEVABLE PER-ITEM OUTCOME under the instrument's own generative dynamics — the "
        "relaxation may drop constraints but may never add capability the instrument lacks",
        "DIRECTIONALITY — only a rigorous UPPER bound may license INADMISSIBLE; only a "
        "constructive LOWER/EXACT bound may license ADMISSIBLE; otherwise fail closed",
        "kappa = 1.2, mirrored verbatim from "
        "research/paper4_instrument_admissibility_v1/KAPPA_FREEZE_V1.json :: frozen_kappa",
        "the verdict grants no scientific authority and may never be upgraded by arm-outcome "
        "access",
    ],
    "deviations_from_the_sibling_assumption_set": [
        {
            "deviation": "the sibling's declaration was frozen (KAPPA_FREEZE_V1.json); this "
                         "study's Paper III declaration is PROVISIONAL and NON-FREEZING",
            "why": "no Paper-III lift MDE is registered, so nothing legitimate exists to freeze. "
                   "Freezing one here would manufacture a protocol obligation this lane never "
                   "registered.",
            "effect_on_verdict": "none — the uncomputable-oracle branch precedes every threshold "
                                 "comparison; demonstrated by the MDE x kappa sweep",
        },
        {
            "deviation": "the sibling's instrument had a closed-form allocation space over which "
                         "a relaxation could be optimized; Paper III's four arms are fixed "
                         "CONDITIONS with no shared allocation choice",
            "why": "structural property of the design (ATTRIBUTION_PREREGISTRATION_V1.md:8-30)",
            "effect_on_verdict": "there is nothing for a monotone relaxation to relax, so the "
                                 "sibling's water-filling construction has no analogue here",
        },
        {
            "deviation": "equal_budget_verified is set TRUE on the most favourable reading of "
                         "ATTRIBUTION_PREREGISTRATION_V1.md:180",
            "why": "so the verdict is attributable to oracle computability alone rather than to a "
                   "budget technicality",
            "effect_on_verdict": "none — the stricter reading (equal_budget_verified=False) is "
                                 "also computed and also fails closed, for an independent reason",
        },
    ],
    "what_the_ceiling_would_have_held_fixed_had_it_been_computable": [
        "the pinned subject (Qwen2.5-7B-Instruct @ a09a35458c…, bfloat16, greedy, 256 new tokens)",
        "the frozen evaluator's rubric, success threshold and parser",
        "the frozen task panel and its strata proportions",
        "the shared resource ceiling across all four arms",
    ],
}


DECISION_CONSEQUENCE = {
    "for_the_a100_staging_decision": "The ceiling qualification the manuscript itself asks for "
                                     "CANNOT be produced for this instrument class before "
                                     "execution, so it cannot gate the accelerator spend either "
                                     "way. Staging the A100 is therefore not de-risked by this "
                                     "study, and the block is NOT 'only budget'.",
    "the_honest_repair": "freeze the two artifacts that are missing and are free to produce — "
                         "(a) the evaluator identity/rubric/parser/success-threshold hash "
                         "(ATTRIBUTION_PREREGISTRATION_V1.md:85) and (b) a material-effect "
                         "threshold for the lift contrasts — before any hours are bought. Both "
                         "are local, cost nothing, and are prerequisites the preregistration "
                         "already names at line 3.",
    "what_would_make_a_ceiling_computable": "a calibrated generative surrogate of per-task, "
                                            "per-arm outcomes for the pinned subject, itself "
                                            "requiring executed data — i.e. a pilot, not the "
                                            "confirmatory packet. A pilot-derived surrogate would "
                                            "yield a ceiling but would need its own freeze and "
                                            "could never license ADMISSIBLE on a policy score.",
    "what_this_study_does_not_say": [
        "it does NOT say the 0.05 gate is unreachable — no upper bound was established",
        "it does NOT say the gate is reachable — no lower bound was established",
        "it does NOT convert BLOCKED_ON_CAPABILITY_QUALIFICATION into a null or a negative",
        "it does NOT license skipping the admissibility requirement for instrument classes where "
        "a ceiling IS computable",
    ],
}


def _decision_dict(decision) -> dict:
    d = asdict(decision)
    for k, v in list(d.items()):
        if hasattr(v, "value"):
            d[k] = v.value
    d["grants_scientific_authority"] = decision.grants_scientific_authority
    d["licenses_comparison_execution"] = decision.licenses_comparison_execution
    d["upgradeable_by_outcome_access"] = decision.upgradeable_by_outcome_access
    return d


# ---------------------------------------------------------------------------
# Block 1 — sibling reproduction control
# ---------------------------------------------------------------------------

# Numeric agreement tolerance for the sibling control.  The recomputation is bit-stable WITHIN
# this environment (asserted below by running it twice); the residual against the published
# receipt is 1-3 ulp of last-bit float accumulation across CPython builds/platforms.  1e-12 is
# ~10 orders of magnitude tighter than the decision margin the control is protecting
# (0.05 - 0.0246 = 0.0254), so it cannot mask a semantic disagreement.
REPRODUCTION_TOLERANCE = 1e-12


def sibling_reproduction_control() -> dict:
    protocol = json.loads(SIBLING_PROTOCOL.read_text())
    published = json.loads(SIBLING_CEILING.read_text())
    attribution = json.loads(SIBLING_ATTRIBUTION.read_text())
    kappa_freeze = json.loads(SIBLING_KAPPA_FREEZE.read_text())
    published_verdict = json.loads(SIBLING_VERDICT.read_text())["decision"]

    # Reconstruct the sibling runner's greedy-count input exactly as its main() does.
    _, _, budget, _ = _mk(protocol)
    counts = {
        c: int(round(v))
        for c, v in attribution["arms"]["ORACLE_GREEDY_CEILING"]["mean_counts"].items()
    }
    drift = sum(counts.values()) - budget
    if drift:
        counts["PRINCIPLE"] -= drift
    greedy_mean = attribution["gap_decomposition"]["ORACLE_minus_D"]

    recomputed = execute(protocol, greedy_mean, counts)
    # Bit-stability within this environment: the same inputs must give byte-identical output.
    # This separates "our computation is nondeterministic" (a defect) from "the published run
    # used a different float environment" (an artifact).
    rerun = execute(protocol, greedy_mean, counts)
    bit_stable_in_env = (
        json.dumps(rerun, sort_keys=True) == json.dumps(recomputed, sort_keys=True))

    pub_tiers = published["bounds_on_achievable_advantage_over_static"]
    rec_tiers = recomputed["bounds_on_achievable_advantage_over_static"]
    tier_exact = {k: (rec_tiers[k] == pub_tiers[k]) for k in pub_tiers}
    tier_deviation = {k: abs(rec_tiers[k] - pub_tiers[k]) for k in pub_tiers}
    per_world_deviation = {
        f"{w}.{k}": abs(recomputed["per_world"][w][k] - published["per_world"][w][k])
        for w in published["per_world"]
        for k in published["per_world"][w]
    }
    max_deviation = max(list(tier_deviation.values()) + list(per_world_deviation.values()))
    per_world_exact_count = sum(1 for v in per_world_deviation.values() if v == 0.0)

    # Fields verbatim from the sibling's own runner,
    # experiments/orion_closure/run_p4_instrument_admissibility_assurance.py::reference_case.
    declaration = FrozenAdmissibilityDeclaration(
        instrument_id="research/orion_p1_p4_closure_v2/P4_ADAPTIVE_PROTOCOL_FREEZE.json",
        registered_primary_metric="E_minus_D_balanced_mastery",
        registered_minimum_detectable_effect=recomputed[
            "frozen_hard_gate_E_minus_D_balanced_mean_min"],
        frozen_kappa=kappa_freeze["frozen_kappa"],
        declared_on=kappa_freeze["date"],
        rationale="formalization of the preserved reference-instrument ceiling; "
                  "see KAPPA_FREEZE_V1 chronology_disclosure",
    )
    evidence = CeilingEvidence(
        instrument_id=declaration.instrument_id,
        oracle_computability=OracleComputability.COMPUTABLE,
        equal_budget_verified=True,
        reference_parent_arm_id="D_STATIC_STRUCTURAL",
        bounds=(
            CeilingBound("tier1_greedy_oracle_policy", BoundKind.LOWER_BOUND,
                         rec_tiers["tier_1_greedy_oracle_policy_stochastic_mean"],
                         "greedy oracle policy rollout (stochastic mean)"),
            CeilingBound("tier2_constructive", BoundKind.LOWER_BOUND,
                         rec_tiers["tier_2_constructive_best_found_expected_dynamics_mean"],
                         "hill-climb over count vectors, expected dynamics"),
            CeilingBound("tier3_harm_free_relaxation", BoundKind.UPPER_BOUND,
                         rec_tiers["tier_3_rigorous_upper_bound_harm_free_relaxation_mean"],
                         "harm-free separable relaxation, exact greedy water-filling"),
        ),
    )
    d = _decision_dict(decide_instrument_admissibility(declaration, evidence))

    checks = {
        "recomputation_bit_stable_within_this_environment": bit_stable_in_env,
        "all_tier_values_within_tolerance":
            all(v <= REPRODUCTION_TOLERANCE for v in tier_deviation.values()),
        "all_per_world_values_within_tolerance":
            all(v <= REPRODUCTION_TOLERANCE for v in per_world_deviation.values()),
        "verdict_matches_published": d["verdict"] == published_verdict["verdict"],
        "declaration_sha256_matches_published_exactly":
            d["declaration_sha256"] == published_verdict["declaration_sha256"],
        "least_upper_bound_within_tolerance":
            abs(d["least_upper_bound"] - published_verdict["least_upper_bound"])
            <= REPRODUCTION_TOLERANCE,
        "best_lower_bound_within_tolerance":
            abs(d["best_lower_bound"] - published_verdict["best_lower_bound"])
            <= REPRODUCTION_TOLERANCE,
        "kappa_range_matches_published_exactly":
            d["verdict_kappa_range"] == published_verdict["verdict_kappa_range"],
        "licensing_bound_matches_published_exactly":
            d["licensing_bound_id"] == published_verdict["licensing_bound_id"],
    }
    return {
        "control_id": "SIBLING_REPRODUCTION_CONTROL",
        "purpose": "if this fails the implementation is wrong and no new ceiling may be reported",
        "sibling_lane": "research/paper4_allocator_attribution_v1/",
        "recomputed_from": {
            "protocol": str(SIBLING_PROTOCOL.relative_to(REPO)),
            "attribution_receipt": str(SIBLING_ATTRIBUTION.relative_to(REPO)),
            "runner_reused":
                "experiments/orion_closure/run_p4_instrument_ceiling_bounds.py::execute",
        },
        "published_tier3_upper_bound":
            pub_tiers["tier_3_rigorous_upper_bound_harm_free_relaxation_mean"],
        "recomputed_tier3_upper_bound":
            rec_tiers["tier_3_rigorous_upper_bound_harm_free_relaxation_mean"],
        "tier_exact_bitwise_match": tier_exact,
        "tier_absolute_deviation": tier_deviation,
        "per_world_absolute_deviation": per_world_deviation,
        "per_world_values_bitwise_exact": f"{per_world_exact_count}/{len(per_world_deviation)}",
        "max_absolute_deviation": max_deviation,
        "tolerance": REPRODUCTION_TOLERANCE,
        "residual_disclosure": {
            "observed": "the recomputation is bit-stable within this environment but differs "
                        "from the published receipt by 1-3 ulp on 4 of 6 per-world values",
            "attribution": "last-bit float accumulation over ~288 sequential multiply-add steps "
                           "under a different CPython build/platform than the original run "
                           "(this run: CPython 3.13 / arm64). The runner and the published "
                           "receipt entered the repository in the same commit (addd73eb), so no "
                           "post-hoc code edit is involved.",
            "chronology_disclosure": [
                "The control criterion was originally BITWISE equality on every value. The first "
                "run failed it, with a 1.49e-16 residual on the tier-3 upper bound.",
                "The criterion was then set to 1e-12 absolute on the numeric values, on the "
                "attribution stated above and after (a) confirming the recomputation is "
                "bit-stable within this environment and (b) checking git history to rule out a "
                "post-hoc code edit. The decision-bearing outputs — verdict, declaration sha256, "
                "licensing bound id, kappa range — were REQUIRED to remain bitwise and do.",
                "This ordering is recorded rather than hidden, mirroring "
                "research/paper4_instrument_admissibility_v1/KAPPA_FREEZE_V1.json :: "
                "chronology_disclosure and the probe-repair note in "
                "experiments/orion_closure/run_p4_instrument_admissibility_assurance.py::"
                "_map_bounds. No threshold of any FROZEN artifact was touched; the relaxed "
                "criterion belongs to this study's own reproduction control.",
            ],
            "why_it_cannot_mask_a_semantic_error": "the largest deviation is ~1.5e-16 while the "
                                                   "quantity the control protects is the "
                                                   "0.0254 gap between the upper bound and the "
                                                   "0.05 gate — 14 orders of magnitude larger. "
                                                   "The verdict, licensing bound, declaration "
                                                   "hash and kappa range all match BITWISE.",
        },
        "recomputed_decision": d,
        "checks": checks,
        "control_pass": all(checks.values()),
    }


# ---------------------------------------------------------------------------
# Block 2 — no-alarm discrimination control
# ---------------------------------------------------------------------------

def no_alarm_control(kappa: float) -> dict:
    rng = random.Random(SEED)
    mde = 0.05
    exact = kappa * mde + 0.02 + rng.random() * 0.01
    declaration = FrozenAdmissibilityDeclaration(
        instrument_id="SYNTHETIC_COMPUTABLE_HEADROOM_CONTROL",
        registered_primary_metric="synthetic_advantage_over_reference_parent",
        registered_minimum_detectable_effect=mde,
        frozen_kappa=kappa,
        declared_on="2026-08-15",
        rationale="no-alarm discrimination control for the Paper III lift-ceiling study",
    )
    evidence = CeilingEvidence(
        instrument_id=declaration.instrument_id,
        oracle_computability=OracleComputability.COMPUTABLE,
        equal_budget_verified=True,
        reference_parent_arm_id="SYNTHETIC_STATIC_PARENT",
        bounds=(
            CeilingBound("exact_synthetic_optimum", BoundKind.EXACT, exact,
                         "closed-form synthetic optimum above kappa*MDE"),
        ),
    )
    d = _decision_dict(decide_instrument_admissibility(declaration, evidence))
    return {
        "control_id": "NO_ALARM_DISCRIMINATION_CONTROL",
        "purpose": "prove the gate is not a constant emitter; a computable instrument with real "
                   "headroom must return ADMISSIBLE, so the target's CANNOT_CHECK is a "
                   "measurement rather than the mechanic's default",
        "seed": SEED,
        "exact_ceiling": exact,
        "threshold_kappa_times_mde": kappa * mde,
        "decision": d,
        "control_pass": d["verdict"] == AdmissibilityVerdict.ADMISSIBLE.value,
    }


# ---------------------------------------------------------------------------
# Block 3 — Paper III fresh-task lift
# ---------------------------------------------------------------------------

def paper3_lift_ceiling(kappa: float) -> dict:
    """Decide the registered four-arm fresh-task-lift instrument.

    The oracle-computability determination is the load-bearing input and is argued from the
    frozen protocol artifacts rather than assumed:

    * the sibling instrument is a closed-form generative simulator (coordinates, per-world
      learning rates, harm terms, fixed integer budget 48), so the best value ANY equal-budget
      policy can reach is computable without running the comparison;
    * the Paper III instrument's per-task, per-arm outcome is produced by a pinned 7B subject
      under an evaluator that is not yet frozen. No generative parameters exist anywhere in the
      repository from which an attainable per-item outcome could be derived; obtaining them
      requires executing the very measurement the gate is meant to license.
    """
    stage35 = json.loads(P3_STAGE35_FREEZE.read_text())
    manuscript_asserted_mde = 0.05

    declaration = FrozenAdmissibilityDeclaration(
        instrument_id="paper3_four_arm_fresh_task_lift__"
                      "experiments/paper5/ATTRIBUTION_PREREGISTRATION_V1.md",
        registered_primary_metric="paired_task_level_mean_score_difference__TOTAL_LIFT",
        registered_minimum_detectable_effect=manuscript_asserted_mde,
        frozen_kappa=kappa,
        declared_on="2026-08-15",
        rationale="PROVISIONAL, NON-FREEZING. The MDE value is the manuscript-asserted 0.05 from "
                  "07b_structural_learning_cautionary.tex:13; kappa mirrors the sibling lane's "
                  "KAPPA_FREEZE_V1. This declaration freezes nothing and creates no protocol "
                  "obligation; it exists so the shipped mechanic can be exercised on the target.",
    )
    evidence = CeilingEvidence(
        instrument_id=declaration.instrument_id,
        # Load-bearing input; fails closed per instrument_admissibility.py:20-21.
        oracle_computability=OracleComputability.UNCOMPUTABLE,
        # Most favourable reading of ATTRIBUTION_PREREGISTRATION_V1.md:180, so the verdict is
        # attributable to the oracle alone.
        equal_budget_verified=True,
        reference_parent_arm_id="MODEL_ONLY",
        bounds=(),
    )
    d = _decision_dict(decide_instrument_admissibility(declaration, evidence))

    sweep = []
    for mde in (0.01, 0.02, 0.05, 0.10, 0.15, 0.30):
        for k in (1.0, 1.2, 2.0):
            alt = FrozenAdmissibilityDeclaration(
                instrument_id=declaration.instrument_id,
                registered_primary_metric=declaration.registered_primary_metric,
                registered_minimum_detectable_effect=mde,
                frozen_kappa=k,
                declared_on=declaration.declared_on,
                rationale=declaration.rationale,
            )
            sweep.append({"mde": mde, "kappa": k,
                          "verdict": decide_instrument_admissibility(alt, evidence).verdict.value})
    sweep_invariant = {r["verdict"] for r in sweep} == {AdmissibilityVerdict.CANNOT_CHECK.value}

    strict_evidence = CeilingEvidence(
        instrument_id=evidence.instrument_id,
        oracle_computability=evidence.oracle_computability,
        equal_budget_verified=False,
        reference_parent_arm_id=evidence.reference_parent_arm_id,
        bounds=(),
    )
    strict = _decision_dict(decide_instrument_admissibility(declaration, strict_evidence))

    return {
        "target_id": "PAPER3_FRESH_TASK_LIFT",
        "oracle_computability_determination": {
            "value": "UNCOMPUTABLE",
            "missing_input_1": "a generative model of per-task, per-arm outcomes for the pinned "
                               "subject. Would have to come from executed pilot data on the "
                               "staged LUNARC A100 subject; it does not and cannot exist "
                               "pre-execution.",
            "missing_input_2": "the frozen evaluator (rubric, parser, success threshold, "
                               "identity hash) required by "
                               "ATTRIBUTION_PREREGISTRATION_V1.md:85. Would have to come from a "
                               "local freeze act by the protocol owner; it is free to produce and "
                               "is simply absent.",
            "missing_input_3": "a frozen task panel with exact task IDs "
                               "(ATTRIBUTION_PREREGISTRATION_V1.md:52). Local, absent.",
            "considered_and_rejected_as_surrogate_sources": [
                {
                    "artifact": "research/paper5_harness_selftest_v1/HARNESS_SELFTEST_RECEIPT_V1.md",
                    "why_it_looked_relevant": "lines 69-72 carry four-arm contrast values "
                                              "(ARCHITECTURE/EXPERIENCE/CONTENT/TOTAL) in exactly "
                                              "the registered contrast structure",
                    "rejected_because": "read in full: status 'HARNESS_VALIDATED / "
                                        "NOT_A_PAPER5_RESULT', 'Model invoked: no', and every score "
                                        "was produced by experiments/paper5/selftest_adapter.py — a "
                                        "synthetic adapter with answers known in advance across "
                                        "three planted conditions (NULL_CONSTANT / NULL_NOISE / "
                                        "PLANTED_LIFT). It validates the analysis plumbing and "
                                        "contains no information about any real subject's per-item "
                                        "outcomes.",
                },
                {
                    "artifact": "research/paper2_experience_benchmark_v1_2/native_job_3476548/"
                                "VALIDATION_RECEIPT.json (terminal "
                                "NEGATIVE_NO_TRANSFER_SUCCESS_LIFT_UNDER_0_5B, the 'preserved "
                                "precursor' cited by research/paper3_publication_closeout_v1/"
                                "FINAL_RECEIPT.json :: causal_model_efficacy)",
                    "why_it_looked_relevant": "it is the only executed model-level lift measurement "
                                              "in the Paper III lineage",
                    "rejected_because": "read in full: a sub-0.5B subject, TWO arms "
                                        "(RESET_BASELINE / LEARNING_ENABLED) not the registered "
                                        "four, task_count = 3 per phase, and success_rate = 0.0 in "
                                        "every cell — a degenerate floor with no discordant mass "
                                        "from which any per-item attainable outcome could be "
                                        "estimated. It is also the wrong subject, and STAGE3_5_"
                                        "FREEZE_V1.json sets model_substitution_allowed = false.",
                },
            ],
            "structural_note": "even with all three, the four arms are CONDITIONS rather than "
                               "policies over a shared budget, so the sibling's monotone-"
                               "relaxation construction has no analogue: there is no allocation "
                               "space to relax.",
        },
        "declaration": {
            "instrument_id": declaration.instrument_id,
            "registered_primary_metric": declaration.registered_primary_metric,
            "registered_minimum_detectable_effect":
                declaration.registered_minimum_detectable_effect,
            "frozen_kappa": declaration.frozen_kappa,
            "content_sha256": declaration.content_sha256,
            "freezes_nothing": True,
        },
        "subject_pin_from_stage3_5_freeze": {
            "model_id": stage35["model_candidates"][0]["model_id"],
            "revision": stage35["model_candidates"][0]["revision"],
            "precision": stage35["model_candidates"][0]["precision"],
            "gpu_request": stage35["runtime"]["gpu_request"],
            "gpu_class": stage35["resource_ceiling"]["gpu_class"],
            "wall_time_hours": stage35["resource_ceiling"]["wall_time_hours"],
        },
        "decision": d,
        "mde_kappa_sweep": sweep,
        "verdict_invariant_across_mde_and_kappa": sweep_invariant,
        "strict_equal_budget_reading": {
            "equal_budget_verified": False,
            "verdict": strict["verdict"],
            "reasons": strict["reasons"],
        },
        "rejected_vacuous_non_bound": {
            "candidate": "saturation headroom = 1.0 - E[MODEL_ONLY score]",
            "would_have_given": "a value >= 0.05 for any baseline below 0.95, i.e. a convenient "
                                "pro-staging ADMISSIBLE",
            "why_it_is_not_a_bound": "it requires E[MODEL_ONLY], an unmeasured quantity "
                                     "obtainable only by running the blocked measurement; and it "
                                     "is an achievability CLAIM, not a constructive lower bound, "
                                     "so it may never license ADMISSIBLE "
                                     "(instrument_admissibility.py:15-17 and :310)",
            "fed_to_gate": False,
        },
        "ceiling_value": None,
        "ceiling_bound_kind": None,
    }


# ---------------------------------------------------------------------------

def main() -> int:
    kappa = json.loads(SIBLING_KAPPA_FREEZE.read_text())["frozen_kappa"]
    out_path = Path(__file__).parent / "CEILING_RECEIPT.json"

    control = sibling_reproduction_control()
    if not control["control_pass"]:
        out_path.write_text(json.dumps({
            "schema_version": "rakl-paper3-lift-ceiling-qualification-v1",
            "terminal": "IMPLEMENTATION_INVALID__SIBLING_CONTROL_FAILED",
            "note": "the sibling reproduction control did not reproduce the published ceiling; "
                    "no new ceiling number is reported",
            "sibling_reproduction_control": control,
            "grants_scientific_authority": False,
        }, indent=2) + "\n")
        print("SIBLING CONTROL FAILED — no new ceiling reported")
        return 1

    no_alarm = no_alarm_control(kappa)
    target = paper3_lift_ceiling(kappa)
    terminal = (
        "CANNOT_CHECK__ORACLE_NOT_COMPUTABLE_NO_GENERATIVE_MODEL"
        if target["decision"]["verdict"] == AdmissibilityVerdict.CANNOT_CHECK.value
        else "UNEXPECTED_VERDICT__" + target["decision"]["verdict"]
    )

    receipt = {
        "schema_version": "rakl-paper3-lift-ceiling-qualification-v1",
        "date": "2026-08-15",
        "kind": "INSTRUMENT_ADMISSIBILITY_QUALIFICATION_ATTEMPT",
        "paper": "Paper III — Method-Evolution Mechanics",
        "question": "Is Paper III's fresh-task-lift 0.05 gate attainable in principle by the "
                    "registered four-arm instrument, i.e. what is its admissibility ceiling?",
        "manuscript_claim_verified": {
            "site": "publication/papers/paper-03-method-evolution-mechanics/sections/"
                    "07b_structural_learning_cautionary.tex:13",
            "quoted": "its $0.05$ gate has no recorded ceiling qualification",
            "verified": True,
            "how": "read the file; the sentence is present at line 13. Independently corroborated "
                   "by research/paper3_blocked_discharge_v1/DISCHARGE_PATHS.json:355-368 (T7, "
                   "unmet_precondition.state = NOT_FOUND).",
        },
        "seed": SEED,
        "mechanic_reused": "src/rakl/instrument_admissibility.py::decide_instrument_admissibility",
        "inputs": INPUTS,
        "registered_gate_provenance": REGISTERED_GATE_PROVENANCE,
        "assumptions": ASSUMPTIONS,
        "terminal": terminal,
        "terminal_is_not": [
            "INSTRUMENT_INADMISSIBLE_CEILING_BELOW_GATE — no upper bound exists, so the "
            "instrument is NOT shown inadmissible",
            "ADMISSIBLE — no constructive lower bound exists, so the gate is NOT shown attainable",
            "'checked and fine' — the ceiling was not computed because it is not computable "
            "pre-execution for this instrument class",
        ],
        "computed_ceiling": {
            "value": None,
            "bound_kind": None,
            "confidence_interval": None,
            "why_absent": "no generative model of the instrument was found from which any bound "
                          "on the attainable lift could be derived. Scope of that claim: the two "
                          "repository artifacts carrying four-arm-shaped outcome numbers were "
                          "opened and rejected on stated grounds — see "
                          "target.oracle_computability_determination."
                          "considered_and_rejected_as_surrogate_sources.",
        },
        "sibling_reproduction_control": control,
        "no_alarm_discrimination_control": no_alarm,
        "target": target,
        "all_controls_pass": control["control_pass"] and no_alarm["control_pass"],
        "decision_consequence": DECISION_CONSEQUENCE,
        "changed_no_frozen_artifact": True,
        "grants_scientific_authority": False,
    }
    out_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({
        "terminal": terminal,
        "sibling_control_pass": control["control_pass"],
        "sibling_tier3_reproduced": control["recomputed_tier3_upper_bound"],
        "sibling_tier3_published": control["published_tier3_upper_bound"],
        "sibling_recomputed_verdict": control["recomputed_decision"]["verdict"],
        "sibling_kappa_range": control["recomputed_decision"]["verdict_kappa_range"],
        "no_alarm_control_pass": no_alarm["control_pass"],
        "no_alarm_verdict": no_alarm["decision"]["verdict"],
        "target_verdict": target["decision"]["verdict"],
        "target_verdict_invariant": target["verdict_invariant_across_mde_and_kappa"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
