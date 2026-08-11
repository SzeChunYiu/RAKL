"""Offline positive-control sensitivity gate for Paper-2 V4.4 leak-free prompts.

A null arm gap is uninterpretable if the instrument cannot register a non-zero
difference when context *must* change the correct answer. This module plants
that condition against the frozen known-answer scorer — no model call, no
scientific authority, no capability-floor clearance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from .degeneracy_probe import ArmPair, DegeneracyStatus, probe_arm_answer_leak
from .matched_microtrial import PendulumStructuredAnswer, score_pendulum_answer

POSITIVE_CONTROL_ID = "PAPER2_V4_4_CONTEXT_SENSITIVITY_PLANTED_LIFT_V1"
SCHEMA_VERSION = "paper2-v4-4-positive-control-sensitivity-v1"

_FORBIDDEN_TYPE_B_MARKERS = (
    "CONTEXT_MISALIGNED_FOR_DIRECT_CONTRADICTION",
    "ALIGNED_REFUTATION",
    "retained as negative history",
    "mass-dependence claim retained as negative history",
)

_REQUIRED_CONTEXT_COORDINATE_MARKERS = (
    ('"source_id": "S4"', "small_angle"),
    ('"source_id": "S5"', "Moon"),
    ('"source_id": "S6"', "bob-mass dependence claim"),
)

_GOLD_FIELDS = {
    "misaligned_source_ids": frozenset({"S4", "S5"}),
    "required_refuted_source_ids": frozenset({"S6"}),
}

CONTEXT_AWARE_GOLD = PendulumStructuredAnswer(
    small_angle_is_asymptotic=True,
    finite_amplitude_increases_period=True,
    context_distinct_claims_not_direct_contradictions=True,
    ideal_period_is_mass_invariant=True,
    context_alignment_required_before_contradiction=True,
    supporting_source_ids=("S1", "S2", "S3", "S4", "S5", "S7", "S8"),
    rejected_as_misaligned_source_ids=("S4", "S5"),
    refuted_source_ids=("S6",),
)

CONTEXT_BLIND_BASELINE = PendulumStructuredAnswer(
    small_angle_is_asymptotic=True,
    finite_amplitude_increases_period=True,
    context_distinct_claims_not_direct_contradictions=False,
    ideal_period_is_mass_invariant=True,
    context_alignment_required_before_contradiction=False,
    supporting_source_ids=("S1", "S2", "S3", "S7", "S8"),
    rejected_as_misaligned_source_ids=(),
    refuted_source_ids=(),
)


@dataclass(frozen=True)
class PositiveControlSensitivityReport:
    passed: bool
    positive_control_id: str
    probe_status: str
    planted_exact_pass_delta: int
    planted_conceptual_delta: int
    planted_misalignment_recall_delta: float
    planted_refutation_recall_delta: float
    null_identical_exact_pass_delta: int
    problems: tuple[str, ...]
    claim_boundary: str
    grants_scientific_authority: bool
    grants_capability_floor_clearance: bool
    artifact_hash: str
    receipt_body: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return dict(self.receipt_body)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_retained_context_coordinates(rakl_prompt: str) -> list[str]:
    problems: list[str] = []
    for source_marker, coordinate in _REQUIRED_CONTEXT_COORDINATE_MARKERS:
        idx = rakl_prompt.find(source_marker)
        if idx < 0:
            problems.append(f"missing_source_marker:{source_marker}")
            continue
        window = rakl_prompt[max(0, idx - 200) : idx + 200]
        if coordinate not in window:
            problems.append(
                f"missing_context_coordinate_near_source:{source_marker}:{coordinate}"
            )
    return problems


def _require_no_type_b_markers(rakl_prompt: str) -> list[str]:
    return [
        f"forbidden_type_b_marker_present:{marker}"
        for marker in _FORBIDDEN_TYPE_B_MARKERS
        if marker in rakl_prompt
    ]


def evaluate_positive_control_sensitivity(
    *,
    rakl_prompt: str,
    direct_prompt: str,
    surface: str = "paper2_microtrial_v4_4",
) -> PositiveControlSensitivityReport:
    problems: list[str] = []
    probe = probe_arm_answer_leak(
        ArmPair(surface, rakl_prompt, direct_prompt, _GOLD_FIELDS)
    )
    if probe.status is not DegeneracyStatus.CLEAN:
        problems.append(f"leak_probe_not_clean:{probe.status.value}")

    problems.extend(_require_no_type_b_markers(rakl_prompt))
    problems.extend(_require_retained_context_coordinates(rakl_prompt))

    aware = score_pendulum_answer(CONTEXT_AWARE_GOLD)
    blind = score_pendulum_answer(CONTEXT_BLIND_BASELINE)
    null_a = score_pendulum_answer(CONTEXT_BLIND_BASELINE)
    null_b = score_pendulum_answer(CONTEXT_BLIND_BASELINE)

    planted_exact_delta = int(aware.exact_conceptual_pass) - int(blind.exact_conceptual_pass)
    planted_conceptual_delta = aware.conceptual_correct - blind.conceptual_correct
    planted_misalign_delta = aware.misalignment_recall - blind.misalignment_recall
    planted_refute_delta = aware.refutation_recall - blind.refutation_recall
    null_exact_delta = int(null_a.exact_conceptual_pass) - int(null_b.exact_conceptual_pass)

    if planted_exact_delta <= 0:
        problems.append(f"planted_exact_pass_delta_not_positive:{planted_exact_delta}")
    if planted_conceptual_delta <= 0:
        problems.append(f"planted_conceptual_delta_not_positive:{planted_conceptual_delta}")
    if planted_misalign_delta <= 0:
        problems.append(
            f"planted_misalignment_recall_delta_not_positive:{planted_misalign_delta}"
        )
    if planted_refute_delta <= 0:
        problems.append(
            f"planted_refutation_recall_delta_not_positive:{planted_refute_delta}"
        )
    if null_exact_delta != 0:
        problems.append(f"null_identical_delta_not_zero:{null_exact_delta}")

    claim_boundary = (
        "Offline planted context-sensitivity check for the V4.4 leak-free arm "
        "pair only. Grants no scientific authority, no RAKL-vs-DIRECT claim from "
        "sealed leaked v4_2/v4_3_1 fields, and no #247 capability-floor clearance."
    )
    body: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "positive_control_id": POSITIVE_CONTROL_ID,
        "surface": surface,
        "probe_status": probe.status.value,
        "rakl_prompt_sha256": _sha256_text(rakl_prompt),
        "direct_prompt_sha256": _sha256_text(direct_prompt),
        "context_aware_score": asdict(aware),
        "context_blind_score": asdict(blind),
        "planted_exact_pass_delta": planted_exact_delta,
        "planted_conceptual_delta": planted_conceptual_delta,
        "planted_misalignment_recall_delta": planted_misalign_delta,
        "planted_refutation_recall_delta": planted_refute_delta,
        "null_identical_exact_pass_delta": null_exact_delta,
        "problems": problems,
        "passed": not problems,
        "claim_boundary": claim_boundary,
        "grants_scientific_authority": False,
        "grants_capability_floor_clearance": False,
        "issue_coordination": [283, 247],
    }
    artifact_hash = _canonical_hash(body)
    return PositiveControlSensitivityReport(
        passed=not problems,
        positive_control_id=POSITIVE_CONTROL_ID,
        probe_status=probe.status.value,
        planted_exact_pass_delta=planted_exact_delta,
        planted_conceptual_delta=planted_conceptual_delta,
        planted_misalignment_recall_delta=planted_misalign_delta,
        planted_refutation_recall_delta=planted_refute_delta,
        null_identical_exact_pass_delta=null_exact_delta,
        problems=tuple(problems),
        claim_boundary=claim_boundary,
        grants_scientific_authority=False,
        grants_capability_floor_clearance=False,
        artifact_hash=artifact_hash,
        receipt_body={**body, "artifact_hash": artifact_hash},
    )


def write_receipt(
    report: PositiveControlSensitivityReport,
    output_path: Path,
    *,
    created_at_utc: str | None = None,
) -> dict[str, object]:
    created = created_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {**report.to_dict(), "created_at_utc": created}
    payload["artifact_hash"] = _canonical_hash(
        {k: v for k, v in payload.items() if k != "artifact_hash"}
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(output_path)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Paper-2 V4.4 offline positive-control sensitivity gate"
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--rakl-prompt", type=Path, default=None)
    parser.add_argument("--direct-prompt", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--created-at-utc", default=None)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    rakl_path = args.rakl_prompt or (
        repo / "research/paper2_microtrial_v4_4_leakfree_draft/RAKL_CONTEXT_PROMPT.txt"
    )
    direct_path = args.direct_prompt or (
        repo / "research/paper2_microtrial_v4_4_leakfree_draft/DIRECT_CORPUS_PROMPT.txt"
    )
    report = evaluate_positive_control_sensitivity(
        rakl_prompt=rakl_path.read_text(encoding="utf-8"),
        direct_prompt=direct_path.read_text(encoding="utf-8"),
        surface=str(rakl_path.parent.name),
    )
    write_receipt(report, args.output, created_at_utc=args.created_at_utc)
    if args.require_pass and not report.passed:
        print("POSITIVE_CONTROL_FAILED:" + ",".join(report.problems))
        return 1
    print(f"POSITIVE_CONTROL_{'PASS' if report.passed else 'FAIL'}:{report.artifact_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
