from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

import jsonschema

from rakl.research_trace import (
    MathResearchTrace,
    ResearchTraceEntry,
    ResearchTraceEventType,
    TraceGateVerdict,
    audit_pre_candidate_trace,
    audit_research_trace,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/real_math/millennium/yang_mills"
CONTEXT_HASH = "sha256:561518a9b62025454014828057a4ad657707f673f9e98b5fb27aceaf8d00f03e"


def _canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load(relative: str) -> dict:
    return json.loads((BASE / relative).read_text(encoding="utf-8"))


def test_restricted_source_can_hide_the_true_first_excitation_exactly() -> None:
    # T = diag(1, 1/2, 1/4).  Omega is the first basis vector.
    transfer_eigenvalues = (Fraction(1), Fraction(1, 2), Fraction(1, 4))
    assert transfer_eigenvalues[0] > transfer_eigenvalues[1] > transfer_eigenvalues[2] > 0

    # A Omega = e2, so the vacuum two-point function sees only eigenvalue 1/4.
    for n in range(9):
        correlator = transfer_eigenvalues[2] ** n
        assert correlator == Fraction(1, 4) ** n

    true_gap = -math.log(float(transfer_eigenvalues[1]))
    source_visible_rate = -math.log(float(transfer_eigenvalues[2]))
    assert math.isclose(true_gap, math.log(2.0))
    assert math.isclose(source_visible_rate, math.log(4.0))
    assert source_visible_rate > true_gap

    # The A-generated excited subspace contains e2 but not the lower state e1.
    a_visible_excited_indices = {2}
    assert 1 not in a_visible_excited_indices

    # Adding B Omega=e1 repairs this finite-dimensional visibility defect.
    ab_visible_excited_indices = {1, 2}
    assert ab_visible_excited_indices == {1, 2}


def test_yms1a_failure_delta_is_content_bound_and_schema_valid() -> None:
    delta = _load("07_memory/YM-S1A_FAILURE_EXPERIENCE_DELTA_20260811.json")
    experience = delta["experience"]
    assert experience["failure_id"] == "F-YM-S1A-RESTRICTED-SOURCE-HIDDEN-STATE"
    assert experience["diagnosis_status"] == "SUPPORTED"
    assert experience["research_trace_event_id"] == "YM-S1-E009"

    payload = copy.deepcopy(experience)
    artifact_hash = payload["artifact_hash"]
    payload["artifact_hash"] = ""
    assert artifact_hash == _canonical_hash(payload)

    schema = json.loads(
        (ROOT / "schemas/failure-experience-lattice.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate({"experiences": [experience], "links": delta["links"]})


def test_yms1_research_trace_appends_calibration_without_candidate() -> None:
    raw_trace = _load("09_trace/YM-S1_RESEARCH_TRACE_20260811.json")
    previous = ""
    entries: list[ResearchTraceEntry] = []

    for raw in raw_trace["entries"]:
        assert raw["previous_event_hash"] == previous
        payload = copy.deepcopy(raw)
        artifact_hash = payload["artifact_hash"]
        payload["artifact_hash"] = ""
        assert artifact_hash == _canonical_hash(payload)
        previous = artifact_hash
        entries.append(
            ResearchTraceEntry(
                event_id=raw["event_id"],
                atom_id=raw["atom_id"],
                event_type=ResearchTraceEventType(raw["event_type"]),
                timestamp=raw["timestamp"],
                state_summary=raw["state_summary"],
                action_summary=raw["action_summary"],
                evidence_pointers=tuple(raw["evidence_pointers"]),
                alternatives_considered=tuple(raw.get("alternatives_considered", ())),
                decision_rationale=raw.get("decision_rationale", ""),
                outputs=tuple(raw.get("outputs", ())),
                uncertainties=tuple(raw.get("uncertainties", ())),
                residuals=tuple(raw.get("residuals", ())),
                next_steps=tuple(raw.get("next_steps", ())),
                artifact_hash=raw["artifact_hash"],
                previous_event_hash=raw["previous_event_hash"],
            )
        )

    trace = MathResearchTrace(trace_id=raw_trace["trace_id"], entries=tuple(entries))
    assert audit_research_trace(trace).verdict is TraceGateVerdict.PASS
    assert (
        audit_pre_candidate_trace(
            trace, atom_id="YM-S1", context_packet_hash=CONTEXT_HASH
        ).verdict
        is TraceGateVerdict.PASS
    )

    event_types = [entry.event_type for entry in entries]
    assert ResearchTraceEventType.CANDIDATE_PROPOSED not in event_types
    assert event_types[-3:] == [
        ResearchTraceEventType.FALSIFIER_RUN,
        ResearchTraceEventType.RESULT_RECORDED,
        ResearchTraceEventType.RESIDUAL_OPENED,
    ]
    assert entries[-2].event_id == "YM-S1-E009"
    assert any(
        output.endswith("restricted_source_decay_not_full_gap")
        for output in entries[-2].outputs
    )
