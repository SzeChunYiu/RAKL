from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from rakl.experience_substrate import (
    EpisodeOutcome,
    TaskEpisode,
    episode_content_bytes,
    validate_episode,
)


ROOT = Path(__file__).resolve().parents[1]


def _valid_episode() -> TaskEpisode:
    draft = TaskEpisode(
        episode_id="EP-HASH-CONTRACT",
        task_id="task-hash-contract",
        atom_id="A-HASH",
        context_hash="sha256:" + "1" * 64,
        problem_signature=("task episode", "exact content identity"),
        fibre_snapshot_hash="sha256:" + "2" * 64,
        operator_ids=("OP-HASH-CHECK",),
        action_trace=("freeze content", "compute exact digest"),
        observation_ids=("OBS-HASH",),
        verification_ids=("VERIFY-HASH",),
        outcome=EpisodeOutcome.SUCCESS,
        residual_signature=(),
        evidence_pointers=("test:task-episode-hash-contract",),
        artifact_hash="",
        timestamp="2026-08-11T14:00:00Z",
        cost=0.0,
    )
    return replace(draft, artifact_hash=sha256(episode_content_bytes(draft)).hexdigest())


def _json_episode(episode: TaskEpisode) -> dict:
    payload = asdict(episode)
    payload["outcome"] = episode.outcome.value
    for name in (
        "problem_signature", "operator_ids", "action_trace", "observation_ids",
        "verification_ids", "residual_signature", "evidence_pointers",
    ):
        payload[name] = list(payload[name])
    return payload


def test_runtime_rejects_hash_shapes_that_used_to_bypass_digest_check() -> None:
    episode = _valid_episode()
    assert validate_episode(episode) == ()

    for malformed in (
        "sha256:" + episode.artifact_hash,
        episode.artifact_hash[:-1],
        episode.artifact_hash + "0",
        "g" * 64,
        "not-a-digest",
    ):
        assert "episode:artifact_hash_invalid" in validate_episode(
            replace(episode, artifact_hash=malformed)
        )


def test_runtime_checks_content_after_hash_shape_passes() -> None:
    episode = _valid_episode()
    forged = replace(episode, artifact_hash="0" * 64)
    assert validate_episode(forged) == ("episode:artifact_hash_mismatch",)


def test_task_episode_schema_matches_runtime_raw_sha256_contract() -> None:
    schema = json.loads((ROOT / "schemas/task-episode.schema.json").read_text())
    validator = Draft202012Validator(schema)
    payload = _json_episode(_valid_episode())
    assert list(validator.iter_errors(payload)) == []

    for malformed in (
        "sha256:" + payload["artifact_hash"],
        payload["artifact_hash"][:-1],
        payload["artifact_hash"] + "0",
        "g" * 64,
        "not-a-digest",
    ):
        hostile = dict(payload, artifact_hash=malformed)
        assert list(validator.iter_errors(hostile))

