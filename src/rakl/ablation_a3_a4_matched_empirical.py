"""Matched A3 vs A4 empirical ablation freeze/runner for Paper II (#156).

Freezes the evaluation packet and refuses to invent results. Scoring is allowed
only when both arms supply complete response payloads for the frozen ALR V2
panel. Default execution emits ``EMPIRICS_UNRUN``.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, MutableMapping, Sequence

from .ablation_a3_a4_conformance import AblationArm, run_conformance
from .authority_leakage_benchmark import TransitionResponse
from .authority_leakage_panel_v2 import evaluate_panel_v2, frozen_case_panel_v2

__all__ = [
    "PACKET_PATH",
    "STATUS_PATH",
    "MatchedEmpiricalReport",
    "load_packet",
    "packet_artifact_hash",
    "validate_packet",
    "run_dry_status",
    "score_matched_arm_responses",
]

_REPO = Path(__file__).resolve().parents[2]
PACKET_PATH = (
    _REPO / "research" / "paper2_closest_parent" / "A3_A4_MATCHED_EMPIRICAL_PACKET_V1.json"
)
STATUS_PATH = (
    _REPO / "research" / "paper2_closest_parent" / "A3_A4_MATCHED_EMPIRICAL_STATUS.json"
)
_SCHEMA_PATH = _REPO / "schemas" / "paper2-a3-a4-matched-empirical-packet-v1.schema.json"
_FORBIDDEN = ("MemTX", "PPMF", "AutoSci", "MemClaw")


@dataclass(frozen=True)
class MatchedEmpiricalReport:
    status: str
    packet_hash: str
    grants_scientific_authority: bool
    a3_score: Mapping[str, object] | None
    a4_score: Mapping[str, object] | None
    wall_time_ms: Mapping[str, float] | None
    failures: tuple[str, ...]
    claim_boundary: str

    def to_dict(self) -> MutableMapping[str, object]:
        return {
            "schema_version": "paper2-a3-a4-matched-empirical-status-v1",
            "status": self.status,
            "packet_hash": self.packet_hash,
            "grants_scientific_authority": False,
            "a3_score": dict(self.a3_score) if self.a3_score is not None else None,
            "a4_score": dict(self.a4_score) if self.a4_score is not None else None,
            "wall_time_ms": dict(self.wall_time_ms) if self.wall_time_ms is not None else None,
            "failures": list(self.failures),
            "claim_boundary": self.claim_boundary,
            "issue": 156,
        }


def load_packet(path: Path | None = None) -> Mapping[str, object]:
    target = path or PACKET_PATH
    return json.loads(target.read_text(encoding="utf-8"))


def packet_artifact_hash(packet: Mapping[str, object]) -> str:
    body = {k: v for k, v in packet.items() if k != "artifact_hash"}
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_packet(packet: Mapping[str, object] | None = None) -> Mapping[str, object]:
    data = dict(packet) if packet is not None else dict(load_packet())
    if data.get("grants_scientific_authority") is not False:
        raise AssertionError("matched empirical packet cannot grant authority")
    if data.get("issue") != 156:
        raise AssertionError("packet must bind issue 156")
    if data.get("execution_coordinates", {}).get("results_invented") is not False:
        raise AssertionError("results_invented must be false")
    digest = packet_artifact_hash(data)
    if data.get("artifact_hash") != digest:
        raise AssertionError("artifact_hash mismatch")

    arms = data.get("arms")
    if not isinstance(arms, list) or len(arms) != 2:
        raise AssertionError("expected exactly two arms")
    arm_ids = {str(row.get("arm_id")) for row in arms}
    expected = {
        AblationArm.A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED.value,
        AblationArm.A4_SCIENTIFIC_AUTHORITY_TYPING.value,
    }
    if arm_ids != expected:
        raise AssertionError(f"unexpected arms: {sorted(arm_ids)}")
    for row in arms:
        note = str(row.get("not_external_system") or "")
        for label in _FORBIDDEN:
            if label in str(row.get("arm_id")):
                raise AssertionError(f"arm_id must not contain {label}")
            if label in note and "Not " not in note and "not " not in note:
                # Allow explicit "Not MemTX" disclaimers; forbid affirmative naming.
                pass
        for label in _FORBIDDEN:
            if note.startswith(label) or f" is {label}" in note:
                raise AssertionError(f"arm falsely named as {label}")

    naming = data.get("naming_rule") or {}
    if naming.get("arms_may_not_be_named_as_external_systems") is not True:
        raise AssertionError("naming rule must forbid external-system arm names")

    # Conformance prerequisite must still pass.
    conf = run_conformance()
    if not conf.all_passed:
        raise AssertionError("A3↔A4 conformance prerequisite failed")
    req_hash = (data.get("conformance_prerequisite") or {}).get("artifact_hash")
    if req_hash != conf.artifact_hash:
        raise AssertionError("conformance artifact_hash drift vs packet binding")

    # Evaluator freeze receipt binding.
    binding = data.get("evaluator_binding") or {}
    receipt_path = _REPO / str(binding.get("freeze_receipt_path"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    for key in (
        "panel_visible_sha256",
        "protocol_sha256",
        "panel_source_sha256",
        "scorer_source_sha256",
    ):
        if binding.get(key) != receipt.get(key):
            raise AssertionError(f"evaluator binding drift on {key}")
    if len(frozen_case_panel_v2()) != int(binding.get("case_count") or -1):
        raise AssertionError("case_count does not match frozen ALR V2 panel")

    if _SCHEMA_PATH.is_file():
        try:
            import jsonschema
        except ImportError:  # pragma: no cover
            jsonschema = None
        if jsonschema is not None:
            schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
            jsonschema.validate(data, schema)
    return data


def run_dry_status(
    *,
    packet: Mapping[str, object] | None = None,
    slurm_job_id: str | None = None,
) -> MatchedEmpiricalReport:
    """Validate freeze and emit EMPIRICS_UNRUN — invent no arm scores."""

    data = validate_packet(packet)
    report = MatchedEmpiricalReport(
        status="EMPIRICS_UNRUN",
        packet_hash=str(data["artifact_hash"]),
        grants_scientific_authority=False,
        a3_score=None,
        a4_score=None,
        wall_time_ms=None,
        failures=(),
        claim_boundary=(
            "Freeze validated; no arm response payloads scored. "
            "Not an A4>A3 novelty claim; not MemTX/PPMF/AutoSci."
        ),
    )
    payload = report.to_dict()
    payload["packet_status"] = data.get("status")
    payload["lunarc_authorized"] = bool(
        (data.get("execution_coordinates") or {}).get("lunarc_authorized")
    )
    if slurm_job_id:
        payload["slurm_job_id"] = slurm_job_id
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def score_matched_arm_responses(
    a3_responses: Sequence[TransitionResponse],
    a4_responses: Sequence[TransitionResponse],
    *,
    packet: Mapping[str, object] | None = None,
) -> MatchedEmpiricalReport:
    """Score supplied arm responses on the frozen ALR V2 panel.

    Refuses to invent missing responses. Still grants no scientific authority.
    """

    data = validate_packet(packet)
    failures: list[str] = []

    t0 = time.perf_counter()
    a3_eval = evaluate_panel_v2(responses=a3_responses)
    a3_ms = (time.perf_counter() - t0) * 1000.0
    t1 = time.perf_counter()
    a4_eval = evaluate_panel_v2(responses=a4_responses)
    a4_ms = (time.perf_counter() - t1) * 1000.0

    if a3_eval.get("status") != "SCORED":
        failures.append(f"A3 evaluate status={a3_eval.get('status')}: {a3_eval.get('reason')}")
    if a4_eval.get("status") != "SCORED":
        failures.append(f"A4 evaluate status={a4_eval.get('status')}: {a4_eval.get('reason')}")

    status = "SCORED_ARM_RESPONSES" if not failures else "EMPIRICS_BLOCKED"
    report = MatchedEmpiricalReport(
        status=status,
        packet_hash=str(data["artifact_hash"]),
        grants_scientific_authority=False,
        a3_score=a3_eval.get("score") if isinstance(a3_eval.get("score"), Mapping) else None,
        a4_score=a4_eval.get("score") if isinstance(a4_eval.get("score"), Mapping) else None,
        wall_time_ms={
            AblationArm.A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED.value: a3_ms,
            AblationArm.A4_SCIENTIFIC_AUTHORITY_TYPING.value: a4_ms,
        },
        failures=tuple(failures),
        claim_boundary=(
            "Scores bind only the supplied responders on the frozen ALR V2 panel. "
            "Not a claim against MemTX/PPMF/AutoSci; grants_scientific_authority=false."
        ),
    )
    STATUS_PATH.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report
