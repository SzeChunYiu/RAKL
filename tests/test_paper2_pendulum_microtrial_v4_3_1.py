from __future__ import annotations
import hashlib, json
from pathlib import Path
import pytest
import rakl.paper2_pendulum_microtrial_v4_3_1 as runner
from rakl import paper2_pendulum_microtrial as v4

ROOT = Path(__file__).resolve().parents[1]
ANSWER = json.dumps({"small_angle_is_asymptotic": True, "finite_amplitude_increases_period": True, "context_distinct_claims_not_direct_contradictions": True, "ideal_period_is_mass_invariant": True, "context_alignment_required_before_contradiction": True, "supporting_source_ids": ["S1"], "rejected_as_misaligned_source_ids": ["S4"], "refuted_source_ids": ["S6"]}, sort_keys=True)
ENVELOPE = {
  "fields": json.loads(ANSWER),
  "id": "PENDULUM_STRUCTURED_ANSWER_V2",
}

def test_v4_3_1_unwraps_registered_envelope_without_softening_values() -> None:
    raw = json.dumps(ENVELOPE, indent=2)
    body = runner.normalize_pendulum_output_v4_3_1(raw)
    answer = v4._parse_answer(body)
    assert answer.small_angle_is_asymptotic is True
    assert answer.supporting_source_ids == ("S1",)

def test_v4_3_1_still_rejects_fence_plus_prose() -> None:
    with pytest.raises(ValueError, match="V4.1 output normalization rejected"):
        runner.normalize_pendulum_output_v4_3_1(f"```json\n{ANSWER}\n```\nExplanation: no")

def test_v4_3_1_accepts_flat_fence() -> None:
    assert runner.normalize_pendulum_output_v4_3_1(f"```json\n{ANSWER}\n```\n") == ANSWER

def test_v4_3_1_candidate_packet_validates() -> None:
    packet = json.loads((ROOT / "research/paper2_microtrial_v4_3_1/EXECUTION_PACKET_V4_3_1_20260811.json").read_text())
    runner.validate_v4_3_1_candidate_packet(packet, base_dir=ROOT)

def test_v4_3_1_batch_bindings_match_bytes() -> None:
    batch = json.loads((ROOT / "research/paper2_microtrial_v4_3_1/BATCH_CONTRACT_V4_3_1.json").read_text())
    assert batch["threshold_or_score_change_permitted"] is False
    for binding in batch["bindings"]:
        path = ROOT / binding["path"]
        assert path.is_file(), binding["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == binding["sha256"]

def test_v4_3_1_does_not_weaken_exact_gate() -> None:
    packet = json.loads((ROOT / "research/paper2_microtrial_v4_3_1/EXECUTION_PACKET_V4_3_1_20260811.json").read_text())
    assert packet["threshold_or_score_change_permitted"] is False
    evaluator = json.loads((ROOT / packet["bindings"]["evaluator"]["path"]).read_text(encoding="utf-8"))
    assert evaluator["evaluator_id"] == "PENDULUM_KNOWN_ANSWER_V2"

def test_v4_3_1_prompts_are_flat_shape() -> None:
    for name in ("direct_prompt", "rakl_prompt"):
        text = (ROOT / json.loads((ROOT / "research/paper2_microtrial_v4_3_1/EXECUTION_PACKET_V4_3_1_20260811.json").read_text())["bindings"][name]["path"]).read_text()
        assert "OUTPUT OBJECT SHAPE" in text
        assert 'OUTPUT SCHEMA\n{"fields"' not in text

def test_v4_3_ingest_3476566_parent_is_present_for_v4_3_1() -> None:
    receipt = json.loads((ROOT / "research/paper2_microtrial_v4_3/PAPER2_V4_3_NATIVE_JOB_3476566_INGEST_RECEIPT_20260811.json").read_text())
    assert receipt["native_execution"]["slurm_job_id"] == "3476566"
    assert receipt["task_seed_outcome"]["parse_valid_arm_count"] == 1
    assert receipt["task_seed_outcome"]["exact_conceptual_pass_arm_count"] == 0
    assert receipt["task_seed_outcome"]["records"][0]["condition"] == "DIRECT_CORPUS"
    assert receipt["task_seed_outcome"]["records"][0]["parse_valid"] is False
