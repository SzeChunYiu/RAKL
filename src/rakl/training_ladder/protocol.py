from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence

from rakl.training_projection import structural_catalog_digest

from .controls import build_hostile_control_suite, hostile_suite_digest
from .exposure import REGISTERED_EXPOSURE_COUNTS, ExposureProbeKind, build_exposure_curve_harness
from .generator import STRUCTURAL_FAMILIES, TrainingCase, build_known_structure_catalog
from .types import ControlKind, FamilyId
from .verifier import verify_case

PROTOCOL_VERSION = "training-ladder-phase0-1-v1"
ISSUE_ID = 461
PARENT_ISSUE_ID = 455

ALLOWED_TERMINALS = (
    "MECHANISM_SIGNAL_PRESENT",
    "REPETITION_REMAINS_VALUABLE",
    "NO_STATE_DEPENDENT_RESIDUAL",
    "INSTRUMENT_OR_GENERATOR_DEFECT",
    "MODEL_FLOOR",
)

FORBIDDEN_CLAIMS = (
    "adaptive_training_effective",
    "static_beats_adaptive",
    "training_cost_reduction",
    "paper_vi_licensed",
    "scientific_authority_from_mastery",
)


@dataclass(frozen=True)
class ProtocolFreezeValidation:
    verdict: str
    reasons: tuple[str, ...]
    protocol_subject_hash: str


def _canonical_sha256(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _verified_catalog(seed_offsets: Sequence[int] = (0, 1, 2)) -> tuple[TrainingCase, ...]:
    return tuple(verify_case(case) for case in build_known_structure_catalog(seed_offsets=seed_offsets))


def _protocol_subject_fields(
    *,
    protocol_version: str,
    issue: int,
    parent_issue: int,
    repo_sha: str,
    rakl_version: str,
    generator: Mapping[str, Any],
    hostile_controls: Mapping[str, Any],
    exposure_curve_harness: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "protocol_version": protocol_version,
        "issue": issue,
        "parent_issue": parent_issue,
        "repo_sha": repo_sha,
        "rakl_version": rakl_version,
        "generator": dict(generator),
        "hostile_controls": dict(hostile_controls),
        "exposure_curve": {
            "harness_hash": exposure_curve_harness["harness_hash"],
            "exposure_counts": exposure_curve_harness["exposure_counts"],
            "probe_kinds": exposure_curve_harness["probe_kinds"],
            "comparator_proxies": exposure_curve_harness["comparator_proxies"],
        },
        "allowed_terminals": list(ALLOWED_TERMINALS),
        "forbidden_claims": list(FORBIDDEN_CLAIMS),
    }


def _catalog_subject(cases: Sequence[TrainingCase]) -> dict[str, Any]:
    structures = tuple(case.structure for case in cases)
    return {
        "family_ids": [family.value for family in STRUCTURAL_FAMILIES],
        "case_count": len(cases),
        "structural_catalog_hash": structural_catalog_digest(structures),
        "case_content_hashes": sorted(case.content_hash for case in cases),
        "gold_labels": {case.case_id: case.gold_label.value for case in cases if case.gold_label},
    }


def build_protocol_freeze_packet(
    *,
    repo_sha: str,
    rakl_version: str,
    frozen_at: str | None = None,
) -> dict[str, Any]:
    cases = _verified_catalog()
    hostile = build_hostile_control_suite(seed_offset=0)
    probe_map = {
        ExposureProbeKind.SAME_STRUCTURE: [c.case_id for c in cases if c.control_kind == ControlKind.NORMAL][:3],
        ExposureProbeKind.NEW_COMPOSITION: [c.case_id for c in cases if c.case_id.startswith("seq")][:2],
        ExposureProbeKind.NEW_BOUNDARY: [c.case_id for c in cases if c.case_id.startswith("bal")][:2],
        ExposureProbeKind.NEW_REPRESENTATION: [c.case_id for c in cases if c.case_id.startswith("fsm")][:2],
        ExposureProbeKind.NEW_DOMAIN: [c.case_id for c in cases if c.family_id == FamilyId.BALANCE_CONSERVATION][:2],
        ExposureProbeKind.HOSTILE_NEAR_MISS: [c.case_id for c in hostile.semantic_near_decoys],
    }
    harness = build_exposure_curve_harness(
        harness_id="training-ladder-phase0-1-harness",
        case_ids_by_probe=probe_map,
        frozen_before_outcomes=True,
    )
    catalog_subject = _catalog_subject(cases)
    hostile_subject = {
        "suite_digest": hostile_suite_digest(hostile),
        "template_leak_count": len(hostile.template_leak_probes),
        "ablation_twin_count": len(hostile.coordinate_ablated_twins),
        "decoy_count": len(hostile.semantic_near_decoys),
    }
    exposure_curve_harness = {
        "harness_id": harness.harness_id,
        "harness_hash": harness.harness_hash,
        "exposure_counts": list(REGISTERED_EXPOSURE_COUNTS),
        "probe_kinds": [kind.value for kind in ExposureProbeKind],
        "mastery_coordinates": [coord.value for coord in harness.mastery_coordinates],
        "comparator_proxies": list(harness.comparator_proxies),
        "schedule_entry_count": len(harness.schedule),
    }
    subject_fields = _protocol_subject_fields(
        protocol_version=PROTOCOL_VERSION,
        issue=ISSUE_ID,
        parent_issue=PARENT_ISSUE_ID,
        repo_sha=repo_sha,
        rakl_version=rakl_version,
        generator=catalog_subject,
        hostile_controls=hostile_subject,
        exposure_curve_harness=exposure_curve_harness,
    )
    protocol_subject_hash = _canonical_sha256(subject_fields)
    return {
        "schema_version": "rakl-training-ladder-protocol-freeze-v1",
        "benchmark_id": "training-time-rakl-phase0-1",
        "protocol_version": PROTOCOL_VERSION,
        "issue": ISSUE_ID,
        "parent_issue": PARENT_ISSUE_ID,
        "repo_sha": repo_sha,
        "rakl_version": rakl_version,
        "packet_frozen_at": frozen_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frozen_before_outcomes": True,
        "frozen_before_learner_runs": True,
        "grants_scientific_authority": False,
        "scientific_claim_status": "NO_EMPIRICAL_RESULT",
        "evaluated_results_accessed": False,
        "learner_outcomes_accessed": False,
        "phase": "0/1",
        "blocked_successors": {
            "466": "MECHANISM_SIGNAL_PRESENT required",
            "467": "ADAPTIVE_RESIDUAL_SUPPORTED required",
        },
        "structural_families": [family.value for family in STRUCTURAL_FAMILIES],
        "generator": catalog_subject,
        "hostile_controls": hostile_subject,
        "exposure_curve_harness": exposure_curve_harness,
        "allowed_terminals": list(ALLOWED_TERMINALS),
        "forbidden_claims": list(FORBIDDEN_CLAIMS),
        "authority_boundary": (
            "Phase 0/1 instrument only. Establishes generator validity and exposure-curve "
            "scaffold. Does not authorize #466 adaptive allocation, #467 train/inference "
            "identity test, or Paper VI. Training utility is not scientific authority."
        ),
        "runs": [],
        "protocol_subject_hash": protocol_subject_hash,
    }


def build_protocol_freeze_receipt(packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "rakl-training-ladder-protocol-freeze-receipt-v1",
        "benchmark_id": packet["benchmark_id"],
        "protocol_version": packet["protocol_version"],
        "issue": packet["issue"],
        "verdict": "PROTOCOL_FREEZE_PASS",
        "protocol_subject_hash": packet["protocol_subject_hash"],
        "frozen_before_outcomes": packet["frozen_before_outcomes"],
        "evaluated_results_accessed": packet["evaluated_results_accessed"],
        "learner_outcomes_accessed": packet["learner_outcomes_accessed"],
        "scientific_claim_status": packet["scientific_claim_status"],
        "grants_scientific_authority": False,
        "runs_present": len(packet.get("runs", [])) > 0,
        "receipt_frozen_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def validate_protocol_freeze(packet_dir: Path) -> ProtocolFreezeValidation:
    packet_path = packet_dir / "PROTOCOL_FREEZE_PACKET.json"
    if not packet_path.is_file():
        return ProtocolFreezeValidation("PROTOCOL_FREEZE_FAIL", ("missing_packet",), "")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    reasons: list[str] = []

    if packet.get("evaluated_results_accessed"):
        reasons.append("evaluated_results_already_accessed")
    if packet.get("learner_outcomes_accessed"):
        reasons.append("learner_outcomes_already_accessed")
    if packet.get("frozen_before_outcomes") is not True:
        reasons.append("not_frozen_before_outcomes")
    if packet.get("runs"):
        reasons.append("runs_present_before_freeze")
    for forbidden in ("results.jsonl", "exposure_outcomes.jsonl", "learner_checkpoints"):
        if (packet_dir / forbidden).is_file():
            reasons.append(f"forbidden_outcome_artifact:{forbidden}")

    expected_hash = _canonical_sha256(
        _protocol_subject_fields(
            protocol_version=packet["protocol_version"],
            issue=packet["issue"],
            parent_issue=packet["parent_issue"],
            repo_sha=packet["repo_sha"],
            rakl_version=packet["rakl_version"],
            generator=packet["generator"],
            hostile_controls=packet["hostile_controls"],
            exposure_curve_harness=packet["exposure_curve_harness"],
        )
    )
    if packet.get("protocol_subject_hash") != expected_hash:
        reasons.append("protocol_subject_hash_mismatch")

    if reasons:
        return ProtocolFreezeValidation("PROTOCOL_FREEZE_FAIL", tuple(reasons), packet.get("protocol_subject_hash", ""))
    return ProtocolFreezeValidation("PROTOCOL_FREEZE_PASS", ("pre_outcome_freeze_valid",), packet["protocol_subject_hash"])
