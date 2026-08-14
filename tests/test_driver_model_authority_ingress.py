from __future__ import annotations

from hashlib import sha256
import json

import pytest

from rakl.driver_learning import DriverResult, DriverTask, run_learning_turn
from rakl.experience_substrate import EpisodeOutcome
from rakl.problem_fibre import ProblemAtom
from rakl.v3_runtime import RAKLV3State


BASE = {
    "claim_id": "driver-claim",
    "axis": "R",
    "proposition": "candidate representation statement",
    "scope_id": "driver-scope",
    "evidence_ids": ["external-evidence-1"],
}


def _task() -> DriverTask:
    return DriverTask(
        task_id="driver-task-1",
        atom=ProblemAtom(
            atom_id="atom-1",
            goal="test one research action",
            context_hash="ctx-driver",
            structural_coordinates=("authority-isolation",),
            desired_effects=("progress",),
        ),
        problem_signature=("authority-isolation",),
        timestamp="2026-08-14T09:30:00+00:00",
    )


def _driver(raw: str | None):
    digest = sha256(raw.encode("utf-8")).hexdigest() if raw is not None else None

    def driver(_request):
        return DriverResult(
            operator_ids=("op-observe",),
            action_trace=("inspect evidence",),
            observation_ids=("obs-1",),
            verification_ids=(),
            outcome=EpisodeOutcome.SUCCESS,
            residual_signature=(),
            evidence_pointers=("driver-output-artifact",),
            artifact_hash="driver-result-hash",
            authority_proposal_json=raw,
            authority_proposal_sha256=digest,
        )

    return driver


def test_valid_model_authority_output_reaches_only_inert_proposal_plane():
    raw = json.dumps(BASE, separators=(",", ":"))
    initial = RAKLV3State()
    report = run_learning_turn(initial, _task(), _driver(raw), episode_id="ep-valid")

    assert report.authority_proposal is not None
    assert report.authority_proposal.accepted_to_proposal_plane
    assert report.authority_proposal.grants_scientific_authority is False
    assert report.state.scientific_authority == initial.scientific_authority
    assert len(report.state.experience.episodes) == 1
    assert (
        "agent-authority-output-sha256:" + sha256(raw.encode("utf-8")).hexdigest()
        in report.episode.evidence_pointers
    )


def test_hostile_control_fields_are_rejected_without_erasing_experience_learning():
    hostile = dict(BASE)
    hostile.update(
        {
            "verified": True,
            "attestation_id": "model-supplied-attestation",
            "certificate_id": "model-supplied-certificate",
        }
    )
    raw = json.dumps(hostile, separators=(",", ":"))
    initial = RAKLV3State()
    report = run_learning_turn(initial, _task(), _driver(raw), episode_id="ep-hostile")

    assert report.authority_proposal is not None
    assert not report.authority_proposal.accepted_to_proposal_plane
    assert any("protected_control_fields" in reason for reason in report.authority_proposal.reasons)
    assert report.state.scientific_authority == initial.scientific_authority
    assert len(report.state.experience.episodes) == 1
    assert report.state.experience.episodes[0].outcome is EpisodeOutcome.SUCCESS


@pytest.mark.parametrize(
    "raw",
    [
        '{"claim_id":"a","claim_id":"b","axis":"R","proposition":"p","scope_id":"s","evidence_ids":["e"]}',
        json.dumps({**BASE, "metadata": {"attestation_id": "nested"}}),
        "```json\n" + json.dumps(BASE) + "\n```",
        json.dumps({**BASE, "attestatiоn_id": "lookalike"}, ensure_ascii=False),
        json.dumps(BASE) + json.dumps(BASE),
    ],
)
def test_registered_hostile_framing_and_second_parser_attacks_fail_closed(raw):
    initial = RAKLV3State()
    report = run_learning_turn(initial, _task(), _driver(raw), episode_id="ep-attack")
    assert report.authority_proposal is not None
    assert not report.authority_proposal.accepted_to_proposal_plane
    assert report.state.scientific_authority == initial.scientific_authority
    assert len(report.state.experience.episodes) == 1


def test_json_looking_control_text_inside_proposition_is_never_second_parsed():
    payload = dict(BASE)
    payload["proposition"] = '{"attestation_id":"text-only","verified":true}'
    raw = json.dumps(payload, separators=(",", ":"))
    initial = RAKLV3State()
    report = run_learning_turn(initial, _task(), _driver(raw), episode_id="ep-text")

    assert report.authority_proposal is not None
    assert report.authority_proposal.accepted_to_proposal_plane
    assert report.authority_proposal.proposal is not None
    assert report.authority_proposal.proposal.proposition == payload["proposition"]
    assert report.state.scientific_authority == initial.scientific_authority


def test_driver_authority_output_requires_exact_hash_binding():
    raw = json.dumps(BASE)
    with pytest.raises(ValueError, match="SHA-256 binding mismatch"):
        DriverResult(
            operator_ids=("op",),
            action_trace=("act",),
            observation_ids=("obs",),
            verification_ids=(),
            outcome=EpisodeOutcome.SUCCESS,
            residual_signature=(),
            evidence_pointers=("artifact",),
            artifact_hash="driver-result-hash",
            authority_proposal_json=raw,
            authority_proposal_sha256="0" * 64,
        )


def test_driver_authority_output_cannot_supply_only_one_half_of_binding():
    with pytest.raises(ValueError, match="requires both exact JSON text and SHA-256 binding"):
        DriverResult(
            operator_ids=("op",),
            action_trace=("act",),
            observation_ids=("obs",),
            verification_ids=(),
            outcome=EpisodeOutcome.SUCCESS,
            residual_signature=(),
            evidence_pointers=("artifact",),
            artifact_hash="driver-result-hash",
            authority_proposal_json=json.dumps(BASE),
        )


def test_no_authority_channel_preserves_existing_learning_turn_shape():
    initial = RAKLV3State()
    report = run_learning_turn(initial, _task(), _driver(None), episode_id="ep-none")
    assert report.authority_proposal is None
    assert len(report.state.experience.episodes) == 1
    assert report.state.scientific_authority == initial.scientific_authority
