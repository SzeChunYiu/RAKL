import hashlib
import json
from pathlib import Path

from rakl.authority_ledger import AuthorityLedger, AuthorityProposal
from rakl.epistemic_noninterference import check_epistemic_noninterference
from rakl.objective_transfer_benchmark import Decision
from rakl.objective_transfer_benchmark_v2 import FAMILIES
from rakl.semantic_shortcut_router import resolve_obstruction_transformation_route
from rakl.semantic_shortcut_router_v2 import CandidateRejectionCertificate
from rakl.semantic_shortcut_router_v3 import CompositionRejectionCertificate
from rakl.semantic_shortcut_consolidation import StructuralConsolidationVerdict
from rakl.training_policy_authority import TrainingPolicyMode, choose_active_training_policy
from rakl.training_scheduler import choose_adaptive_training_batch


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "research" / "orion_p1_p4_closure_v2"


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def test_p1_p2_exact_subject_transport_matches_approved_freeze():
    witness = json.loads((PACKET / "P1_P2_TRANSPORT_WITNESS.json").read_text())
    assert witness["all_subjects_identical"] is True
    for row in witness["paper1_subjects"] + witness["paper2_subjects"]:
        assert row["approved_blob"] == row["current_blob"]
        assert _git_blob_sha(ROOT / row["path"]) == row["current_blob"]


def test_all_runtime_required_orion_nodes_are_promotion_grade():
    graph = json.loads((PACKET / "DEPENDENCY_GRAPH.json").read_text())
    forbidden = tuple(graph["strict_invariant"]["forbidden_active_terminals"])
    required = []
    for paper in graph["papers"].values():
        for node in paper["nodes"]:
            if node["runtime_required"]:
                required.append(node)
                assert not any(token in node["terminal"] for token in forbidden), node
        assert paper["active_negative_required_nodes"] == []
    assert required
    assert graph["all_runtime_required_nodes_promotion_grade"] is True


def test_p2_six_family_registered_pass_is_preserved_but_non_sovereign_after_audit():
    graph = json.loads((PACKET / "DEPENDENCY_GRAPH.json").read_text())
    p2 = {node["id"]: node for node in graph["papers"]["P2"]["nodes"]}
    broad = p2["P2_SIX_FAMILY_APPLICABILITY"]
    assert broad["runtime_required"] is False
    assert broad["terminal"] == "SCOPED_ASSURANCE__REGISTERED_PASS_NONPROBATIVE_FOR_BROAD_GENERALIZATION"

    confirmatory = json.loads(
        (ROOT / "research/empirical_10_of_10_v1/PAPER3/OBJECTIVE/ROBUSTNESS_CONFIRMATORY_RESULT_V1.json").read_text()
    )
    assert confirmatory["broad_known_world_robustness_supported"] is True
    assert confirmatory["gate_reasons"] == []
    assert confirmatory["family_sign_test"]["positive_families"] == 6

    audit = json.loads(
        (ROOT / "research/paper2_six_family_audit_v1/results/SIX_FAMILY_AUDIT.json").read_text()
    )
    assert audit["A_full_arm_constant_loss"]["full_arm_loss_is_constant"] is True
    assert audit["B_sign_test_degeneracy"]["all_seeds_six_of_six_positive"] is True
    assert audit["B_sign_test_degeneracy"]["sign_test_is_structurally_guaranteed"] is True
    assert audit["status"] == "AUXILIARY_DIAGNOSTIC_ONLY__NOT_PART_OF_FROZEN_REGISTRATION"
    assert audit["grants_scientific_authority"] is False

    correction = json.loads(
        (ROOT / "research/paper2_six_family_governance_repair_v1/CORRECTION.json").read_text()
    )
    assert correction["current_interpretation"]["not_a_refutation"] is True
    assert correction["current_interpretation"]["runtime_required"] is False
    assert correction["grants_scientific_authority"] is False


def test_p3_structured_experience_successor_is_green_and_not_model_capability_dependent():
    receipt = json.loads((PACKET / "P3_STRUCTURED_EXPERIENCE_ACTION_RECEIPT.json").read_text())
    assert receipt["terminal"] == "PROMOTE_TO_MECHANIC_STRUCTURED_VERIFIED_EXPERIENCE_TO_ACTION"
    assert receipt["all_gates_pass"] is True
    assert receipt["typed_selective_experience"]["exact_action_accuracy"] == 1.0
    assert receipt["typed_selective_experience"]["unsafe_apply_rate"] == 0.0
    assert receipt["parents"]["COMPOSITE_SIMPLE_PARENT"]["information_ceiling"] < 0.95
    assert all(item["caught"] for item in receipt["mutations"].values())
    assert receipt["replaces_active_dependency_on_model_capability"] is True
    assert receipt["grants_scientific_authority"] is False


def test_p4_failed_or_missing_adaptive_evidence_retains_static_active_parent():
    decision = choose_active_training_policy()
    assert decision.mode is TrainingPolicyMode.STATIC_STRUCTURAL


def test_paper_runtime_surfaces_import_together():
    assert AuthorityLedger is not None and AuthorityProposal is not None
    assert check_epistemic_noninterference is not None
    assert Decision is not None and len(FAMILIES) == 6
    assert resolve_obstruction_transformation_route is not None
    assert CandidateRejectionCertificate is not None
    assert CompositionRejectionCertificate is not None
    assert StructuralConsolidationVerdict is not None
    assert choose_adaptive_training_batch is not None
