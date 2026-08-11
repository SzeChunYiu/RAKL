from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

import rakl.paper2_pendulum_microtrial_v4_2 as runner
from rakl.paper2_pendulum_microtrial import BackendGeneration


ROOT = Path(__file__).resolve().parents[1]


ANSWER = json.dumps(
    {
        "small_angle_is_asymptotic": True,
        "finite_amplitude_increases_period": True,
        "context_distinct_claims_not_direct_contradictions": True,
        "ideal_period_is_mass_invariant": True,
        "context_alignment_required_before_contradiction": True,
        "supporting_source_ids": ["S1"],
        "rejected_as_misaligned_source_ids": ["S4"],
        "refuted_source_ids": ["S6"],
    },
    sort_keys=True,
)


def test_v4_2_reuses_v4_1_normalizer_without_widening() -> None:
    assert runner.normalize_pendulum_output_v4_2(f"```json\n{ANSWER}\n```\n") == ANSWER
    with pytest.raises(ValueError, match="V4.1 output normalization rejected"):
        runner.normalize_pendulum_output_v4_2(f"```json\n{ANSWER}\n```\nExplanation: no")


def test_v4_2_prompts_include_field_polarity_without_gold_leak() -> None:
    for name in ("DIRECT_CORPUS_PROMPT.txt", "RAKL_CONTEXT_PROMPT.txt", "SYSTEM_PROMPT.txt"):
        text = (ROOT / "research/paper2_microtrial_v4_2" / name).read_text(encoding="utf-8")
        runner._require_field_polarity_prompt(text, label=name)


def test_v4_2_stop_after_json_fence_clips_trailing_prose() -> None:
    raw = f"```json\n{ANSWER}\n```\n\nExplanation: trailing"

    def backend(prompt: str, **kwargs: object) -> BackendGeneration:
        return BackendGeneration(
            raw_text=raw,
            input_tokens=10,
            output_tokens=20,
            backend_version="test",
            wall_time_ms=1,
            process_high_water_rss_bytes_after_arm=1,
        )

    wrapped = runner._stopping_backend(backend)
    out = wrapped("prompt")
    assert out.raw_text == f"```json\n{ANSWER}\n```"
    assert "Explanation" not in out.raw_text
    assert "+v4_2_stop_after_json_fence" in out.backend_version


def test_v4_2_candidate_packet_validates_and_binds_memory_review() -> None:
    packet = json.loads(
        (ROOT / "research/paper2_microtrial_v4_2/EXECUTION_PACKET_V4_2_20260811.json").read_text()
    )
    runner.validate_v4_2_candidate_packet(packet, base_dir=ROOT)
    # Tampering the memory review hash must fail closed.
    packet["bindings"]["research_memory_review"]["sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="V4.2 binding mismatch:research_memory_review"):
        runner.validate_v4_2_candidate_packet(packet, base_dir=ROOT)


def test_v4_2_batch_contract_bindings_match_bytes() -> None:
    batch = json.loads(
        (ROOT / "research/paper2_microtrial_v4_2/BATCH_CONTRACT_V4_2.json").read_text()
    )
    assert batch["chronology_class"] == "ADAPTIVE_PROMPT_INTERFACE_REPLAY_FRESH_ONLY_TO_V4_2_OUTPUTS"
    assert batch["prompt_interface_policy_id"] == runner.PROMPT_INTERFACE_POLICY_ID
    assert (
        batch["output_normalization_policy_id"]
        == "PENDULUM_EXACT_JSON_OR_SINGLE_LOWERCASE_JSON_FENCE_V4_1"
    )
    for binding in batch["bindings"]:
        path = ROOT / binding["path"]
        assert path.is_file(), binding["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == binding["sha256"]


def test_v4_2_does_not_weaken_exact_conceptual_gate() -> None:
    packet = json.loads(
        (ROOT / "research/paper2_microtrial_v4_2/EXECUTION_PACKET_V4_2_20260811.json").read_text()
    )
    assert packet["threshold_or_score_change_permitted"] is False
    evaluator = json.loads(
        (ROOT / packet["bindings"]["evaluator"]["path"]).read_text(encoding="utf-8")
    )
    assert evaluator["evaluator_id"] == "PENDULUM_KNOWN_ANSWER_V2"
