"""Integrity tests for SRSU-P6-GOVERNED-ACCEPTANCE (Paper VI scoped utility).

These guard the packet's own epistemic contract, not the numeric outcome:
no scalar ranking, no authority grant, conformance/measured split present,
negative history retained, registered falsifiers all evaluated, and the
external anchor recorded rather than imported from a branch main lacks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PACKET = Path(__file__).resolve().parents[1] / "research" / "paper6_scoped_utility_v1"

V1 = PACKET / "PREREGISTRATION_V1.json"
V1_1 = PACKET / "PREREGISTRATION_V1_1.json"
R1 = PACKET / "RESULTS_V1.json"
R1_1 = PACKET / "RESULTS_V1_1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def test_all_packet_artifacts_present() -> None:
    for path in (V1, V1_1, R1, R1_1, PACKET / "README.md"):
        assert path.exists(), f"missing packet artifact: {path}"


@pytest.mark.parametrize("path", [V1, V1_1])
def test_no_authority_and_no_scalar_ranking(path: Path) -> None:
    doc = _load(path)
    assert doc["grants_scientific_authority"] is False
    assert doc["grants_promotion_authority"] is False
    assert doc["permits_scalar_ranking"] is False


@pytest.mark.parametrize("path", [R1, R1_1])
def test_results_carry_no_authority_and_no_scalar_ranking(path: Path) -> None:
    doc = _load(path)
    assert doc["grants_scientific_authority"] is False
    assert doc["permits_scalar_ranking"] is False


def test_conformance_and_measured_are_disjoint_and_nonempty() -> None:
    split = _load(V1)["claim_class_split"]
    conformance = set(split["CONFORMANCE_not_evidence"])
    measured = set(split["MEASURED_evidence"])
    assert conformance and measured
    assert not (conformance & measured), "a coordinate cannot be both conformance and measured"
    # the tautological coordinate must be on the conformance side
    assert any("false_promotion_rate_on_planted" in item for item in conformance)


def test_v1_freeze_precedes_outcome_access() -> None:
    assert _load(V1)["frozen_before_outcome_access"] is True


def test_arm_b_is_labelled_a_reimplementation_control_not_a_system() -> None:
    arms = {arm["arm_id"]: arm for arm in _load(V1)["arms"]}
    b = arms["B_GREEDY_HELDOUT_SCALAR"]
    assert b["kind"] == "REIMPLEMENTATION_CONTROL_ARM"
    assert "not the Karpathy" in b["source_system_note"] or "NOT the Karpathy" in b["source_system_note"]


def test_llm_judge_arm_is_blocked_and_not_simulated() -> None:
    arms = {arm["arm_id"]: arm for arm in _load(V1)["arms"]}
    e = arms["E_LLM_JUDGE_FITNESS"]
    assert e["kind"] == "BLOCKED"
    assert e["state"] == "CANNOT_CHECK"


def test_held_out_generalization_is_cannot_check() -> None:
    gen = _load(V1)["generalization_status"]
    assert gen["held_out_defect_families"] == "CANNOT_CHECK"
    assert "RES-EXT-001" in gen["reason"]


def test_successor_declares_defect_and_discloses_chronology() -> None:
    doc = _load(V1_1)
    why = doc["why_a_successor_exists"]
    assert doc["parent_packet_id"] == "SRSU-P6-GOVERNED-ACCEPTANCE-V1"
    assert why["classification"].startswith("CONFORMANCE_REPAIR_TO_THE_FROZEN_SPEC")
    assert "seen before" in why["chronology_disclosure"]
    # negative history must be retained, not rewritten
    assert "RESULTS_V1.json" in why["v1_retained"]


def test_v1_negative_history_shows_the_degenerate_control() -> None:
    """The retained v1 run must still exhibit the defect it is retained for."""
    cell = _load(R1)["results"][0]["arms"]["B_GREEDY_HELDOUT_SCALAR"]
    acceptance = cell["false_promotion_rate"] + cell["true_promotion_rate"]
    assert acceptance < 0.05, "v1 control arm should be degenerate; history must not be rewritten"


def test_v1_1_control_arm_is_throughput_matched() -> None:
    """Arm B must actually be matched to arm D, or D-vs-B is not a fair comparison."""
    for cell in _load(R1_1)["primary_neutral_scalar_model"]:
        arms = cell["arms"]
        acc_b = (
            arms["B_GREEDY_HELDOUT_SCALAR_MATCHED"]["false_promotion_rate"]
            + arms["B_GREEDY_HELDOUT_SCALAR_MATCHED"]["true_promotion_rate"]
        )
        acc_d = arms["D_FAIL_OPEN"]["false_promotion_rate"] + arms["D_FAIL_OPEN"]["true_promotion_rate"]
        assert abs(acc_b - acc_d) < 0.05, f"n_repro={cell['n_repro']} not throughput-matched"


def test_governed_arm_false_promotion_is_conformance_zero() -> None:
    """Documented as conformance, so it must in fact be zero; if not, the label is wrong."""
    for cell in _load(R1_1)["primary_neutral_scalar_model"]:
        assert cell["arms"]["A_ORION_GOVERNED"]["false_promotion_rate"] == 0.0


def test_leakage_variant_is_present_and_marked_not_headline() -> None:
    doc = _load(R1_1)
    assert "sensitivity_leakage_inflated_not_headline" in doc
    model = _load(V1_1)["scalar_informativeness_model"]
    assert model["primary"].startswith("NEUTRAL")


def test_registry_anchor_is_recorded_not_imported() -> None:
    """main does not carry the registry; the anchor must be copied, and the rates real."""
    anchor = _load(V1)["evidence_availability_anchor"]
    assert anchor["evidence_grade"] == "PRIMARY_ABSTRACT"
    assert anchor["recorded_rates"]["code_released"] == 0.83
    assert anchor["recorded_rates"]["seeds_or_traces_released"] == 0.38
    assert "2608.05179" in anchor["source"]
    # no packet file may import the registry loader, which main lacks
    for path in PACKET.glob("*.json"):
        if path.name.startswith("._"):
            continue  # macOS AppleDouble sidecar, never part of the packet
        assert "external_agent_registry" not in path.read_text()


CORRECTION = PACKET / "CLASSIFICATION_CORRECTION_V1.json"


def test_correction_exists_and_does_not_edit_the_frozen_prereg() -> None:
    doc = _load(CORRECTION)
    assert doc["frozen_prereg_edited"] is False
    assert doc["direction"] == "SELF_PENALIZING"
    # the frozen prereg must still carry its ORIGINAL (wrong) split
    original = set(_load(V1)["claim_class_split"]["MEASURED_evidence"])
    assert any("arm_A_vs_arm_D" in item for item in original), (
        "the frozen prereg must retain its wrong split; the record of the error is the point"
    )


def test_retracted_contrasts_are_predicted_by_closed_form() -> None:
    """The retraction must stay true against the live results, not just be asserted."""
    for cell in _load(R1_1)["primary_neutral_scalar_model"]:
        n = cell["n_repro"]
        arms = cell["arms"]
        mean_unavail = ((12 - n) * (1 - 0.83) + n * (1 - 0.38)) / 12
        d_obs = arms["D_FAIL_OPEN"]["false_promotion_rate"]
        assert abs(d_obs - 0.5 * mean_unavail) < 0.03, (
            f"n_repro={n}: arm D no longer matches its closed form; revisit the retraction"
        )
        b = arms["B_GREEDY_HELDOUT_SCALAR_MATCHED"]
        acc_b = b["false_promotion_rate"] + b["true_promotion_rate"]
        assert abs(b["false_promotion_rate"] - 0.5 * acc_b) < 0.03


def test_surviving_claims_do_not_rest_on_the_repaired_control_arm() -> None:
    survives = _load(CORRECTION)["what_survives"]
    assert "arm A" in survives["rests_on"]
    assert "arm B" in survives["does_not_rest_on"]
    assert "arm D" in survives["does_not_rest_on"]
    assert survives["epistemic_character"].startswith("DERIVED_OPERATING_REGIME_CONSTRAINT")


def test_readme_does_not_still_lead_with_the_retracted_finding() -> None:
    readme = (PACKET / "README.md").read_text()
    idx = readme.find("3.31")
    assert idx != -1, "the retracted number should still appear, inside the retraction"
    assert "What was retracted" in readme[:idx], "3.31x must only appear after the retraction notice"


def test_forbidden_claims_are_registered() -> None:
    forbidden = " ".join(_load(V1)["forbidden_claims"]).lower()
    assert "orion_score" in forbidden
    assert "architecture >" in forbidden


def test_all_registered_falsifiers_are_evaluated_in_the_readme() -> None:
    readme = (PACKET / "README.md").read_text()
    for tag in ("F1", "F2", "F3", "F4"):
        assert tag in readme, f"falsifier {tag} not reported"
    assert "F5" in readme
