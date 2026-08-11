from __future__ import annotations
import hashlib, json
from pathlib import Path
import pytest
import rakl.paper2_pendulum_microtrial_v4_3 as runner
ROOT = Path(__file__).resolve().parents[1]
ANSWER = json.dumps({"small_angle_is_asymptotic": True, "finite_amplitude_increases_period": True, "context_distinct_claims_not_direct_contradictions": True, "ideal_period_is_mass_invariant": True, "context_alignment_required_before_contradiction": True, "supporting_source_ids": ["S1"], "rejected_as_misaligned_source_ids": ["S4"], "refuted_source_ids": ["S6"]}, sort_keys=True)

def test_v4_3_reuses_v4_2_normalizer_without_widening() -> None:
    assert runner.normalize_pendulum_output_v4_3(f"```json\n{ANSWER}\n```\n") == ANSWER
    with pytest.raises(ValueError, match="V4.1 output normalization rejected"):
        runner.normalize_pendulum_output_v4_3(f"```json\n{ANSWER}\n```\nExplanation: no")

def test_v4_3_candidate_packet_validates() -> None:
    packet = json.loads((ROOT / "research/paper2_microtrial_v4_3/EXECUTION_PACKET_V4_3_20260811.json").read_text())
    runner.validate_v4_3_candidate_packet(packet, base_dir=ROOT)

def test_v4_3_batch_contract_bindings_match_bytes() -> None:
    batch = json.loads((ROOT / "research/paper2_microtrial_v4_3/BATCH_CONTRACT_V4_3.json").read_text())
    assert batch["chronology_class"] == runner.CHRONOLOGY_CLASS
    assert batch["threshold_or_score_change_permitted"] is False
    for binding in batch["bindings"]:
        path = ROOT / binding["path"]
        assert path.is_file(), binding["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == binding["sha256"]

def test_v4_3_does_not_weaken_exact_conceptual_gate() -> None:
    packet = json.loads((ROOT / "research/paper2_microtrial_v4_3/EXECUTION_PACKET_V4_3_20260811.json").read_text())
    assert packet["threshold_or_score_change_permitted"] is False
    evaluator = json.loads((ROOT / packet["bindings"]["evaluator"]["path"]).read_text(encoding="utf-8"))
    assert evaluator["evaluator_id"] == "PENDULUM_KNOWN_ANSWER_V2"

def test_v4_3_model_identity_is_1_5b() -> None:
    model = json.loads((ROOT / "research/paper2_microtrial_v4_3/MODEL_MANIFEST_V4_3.json").read_text())
    assert model["model_id"] == "Qwen/Qwen2.5-1.5B-Instruct"
    assert model["revision"] == "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
    assert model["generation"]["seed"] == 17

def test_v4_3_staging_contract_model_only_overlay() -> None:
    contract = json.loads((ROOT / "research/paper2_microtrial_v4_3/MODEL_STAGING_CONTRACT_V4_3.json").read_text())
    assert contract["overlay_policy"]["model_only"] is True
    assert contract["overlay_policy"]["python_wheel_redownload_permitted"] is False
    for binding in contract["bindings"]:
        path = ROOT / binding["path"]
        assert path.is_file(), binding["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == binding["sha256"]

def test_v4_3_difference_witness_is_model_scale_only() -> None:
    witness = json.loads((ROOT / "research/paper2_microtrial_v4_3/DIFFERENCE_WITNESS_V4_3.json").read_text())
    changed = set(witness["changed_structural_coordinates"])
    assert "model_parameter_scale_0_5B_to_1_5B" in changed
    assert "exact_conceptual_pass_threshold" not in changed
