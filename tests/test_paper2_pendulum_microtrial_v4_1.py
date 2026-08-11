from __future__ import annotations

import json

import pytest

import rakl.paper2_pendulum_microtrial_v4_1 as runner


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


def test_v4_1_accepts_bare_json_without_mutation() -> None:
    assert runner.normalize_pendulum_output_v4_1(ANSWER) == ANSWER


def test_v4_1_accepts_exactly_one_lowercase_json_fence() -> None:
    assert runner.normalize_pendulum_output_v4_1(f"```json\n{ANSWER}\n```\n") == ANSWER


@pytest.mark.parametrize(
    "raw",
    (
        f"```json\n{ANSWER}\n```\nExplanation: trailing prose",
        f"```JSON\n{ANSWER}\n```",
        f"```\n{ANSWER}\n```",
        f"```json\n{ANSWER}\n```\n```json\n{ANSWER}\n```",
    ),
)
def test_v4_1_rejects_nonexact_fence_or_trailing_content(raw: str) -> None:
    with pytest.raises(ValueError, match="V4.1 output normalization rejected"):
        runner.normalize_pendulum_output_v4_1(raw)


def test_v4_1_scoring_normalizes_only_under_explicit_policy() -> None:
    raw = {"BLIND_A": f"```json\n{ANSWER}\n```", "BLIND_B": f"```json\n{ANSWER}\n```\nprose"}
    strict = runner._score_blinded_outputs(raw)
    assert [row["parse_valid"] for row in strict] == [False, False]
    repaired = runner._score_blinded_outputs(
        raw, output_normalization_policy_id="PENDULUM_EXACT_JSON_OR_SINGLE_LOWERCASE_JSON_FENCE_V4_1"
    )
    assert [row["parse_valid"] for row in repaired] == [True, False]
