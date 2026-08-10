from __future__ import annotations

import json
from pathlib import Path

from rakl.matched_microtrial import EvidenceCorpusFingerprint, validate_pendulum_evaluator_sources
from rakl.mini_research_demo import _sources


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research" / "ROUND044_MATCHED_LLM_MICROTRIAL_PREREGISTRATION.json"


def _packet() -> dict:
    return json.loads(PREREG.read_text(encoding="utf-8"))


def _frozen_ids() -> set[str]:
    return {source.source_id for source in _sources()}


def test_preregistered_evaluator_names_only_frozen_pendulum_sources():
    packet = _packet()
    evaluator = packet["sealed_known_answer_evaluator"]
    frozen = _frozen_ids()
    for field in (
        "required_support_source_ids",
        "allowed_support_source_ids",
        "misaligned_for_direct_target_contradiction_source_ids",
        "required_refuted_source_ids",
    ):
        assert set(evaluator[field]) <= frozen

    assert set(evaluator["required_refuted_source_ids"]) == {"S6"}
    assert "S6" not in evaluator["allowed_support_source_ids"]


def test_preregistered_evaluator_source_contract_validates_against_exact_corpus():
    corpus = EvidenceCorpusFingerprint.from_payloads(
        {
            source.source_id: source.text.encode("utf-8")
            for source in _sources()
        }
    )
    report = validate_pendulum_evaluator_sources(corpus)
    assert report.valid
    assert report.problems == ()


def test_preregistered_questions_are_grounded_in_existing_pendulum_world():
    packet = _packet()
    questions = "\n".join(item["prompt"].lower() for item in packet["question_set"])
    source_text = "\n".join(source.text.lower() for source in _sources())

    assert len(packet["question_set"]) == 4
    assert "time to reach" not in questions
    assert "time-to-angle" not in questions
    assert "small-angle" in questions
    assert "finite-amplitude" in questions
    assert "moon" in questions
    assert "mass" in questions

    for concept in ("small angle", "finite-amplitude", "moon", "mass"):
        assert concept in source_text


def test_preregistered_output_and_endpoints_cover_context_mass_and_refutation():
    packet = _packet()
    fields = set(packet["output_schema"]["fields"])
    endpoints = set(packet["primary_endpoints"])

    assert packet["output_schema"]["id"] == "PENDULUM_STRUCTURED_ANSWER_V2"
    assert "context_distinct_claims_not_direct_contradictions:boolean" in fields
    assert "ideal_period_is_mass_invariant:boolean" in fields
    assert "refuted_source_ids:list[string]" in fields
    assert "conceptual_correct / 5" in endpoints
    assert "refutation_recall" in endpoints
    assert "refutation_precision" in endpoints


def test_same_source_roles_are_allowed_to_differ_by_scientific_operation():
    evaluator = _packet()["sealed_known_answer_evaluator"]
    support = set(evaluator["allowed_support_source_ids"])
    misaligned = set(evaluator["misaligned_for_direct_target_contradiction_source_ids"])
    refuted = set(evaluator["required_refuted_source_ids"])

    assert support & misaligned == {"S4", "S5"}
    assert support.isdisjoint(refuted)
