"""Cheap A3 vs A4 ablation conformance for Paper II (#156).

Proves the *intended mechanism difference* between:

* ``A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED`` — provenance/schema-valid
  writes may commit under a single generic authority scalar;
* ``A4_SCIENTIFIC_AUTHORITY_TYPING`` — the same evidence may raise only the
  licensed G/R/M/I/D axis and must refuse prediction→mechanism escalation.

This is deterministic conformance, not an empirical ablation result. It grants
no scientific authority and does not claim superiority over MemTX/PPMF.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence, Tuple

from .authority_ledger import AuthorityAxis

__all__ = [
    "AblationArm",
    "AuthorityUpdateRequest",
    "ConformanceCase",
    "ConformanceDecision",
    "ConformanceReport",
    "PolicyDecision",
    "TransactionalGovernancePolicy",
    "ScientificAuthorityTypingPolicy",
    "decide",
    "frozen_conformance_panel",
    "run_conformance",
]


class AblationArm(str, Enum):
    A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED = "A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED"
    A4_SCIENTIFIC_AUTHORITY_TYPING = "A4_SCIENTIFIC_AUTHORITY_TYPING"


class ConformanceDecision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


@dataclass(frozen=True)
class AuthorityUpdateRequest:
    """Matched information available to both arms."""

    request_id: str
    claim_id: str
    proposition: str
    evidence_ids: Tuple[str, ...]
    provenance_valid: bool
    schema_valid: bool
    requested_axis: AuthorityAxis
    licensed_axes: Tuple[AuthorityAxis, ...]
    observation_kind: str  # e.g. predictive_fit | interventional_mediator

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id required")
        if not self.claim_id.strip():
            raise ValueError("claim_id required")
        if not self.proposition.strip():
            raise ValueError("proposition required")
        if not self.evidence_ids:
            raise ValueError("evidence_ids required")
        if not self.observation_kind.strip():
            raise ValueError("observation_kind required")


@dataclass(frozen=True)
class PolicyDecision:
    arm: AblationArm
    decision: ConformanceDecision
    reason: str


@dataclass(frozen=True)
class ConformanceCase:
    case_id: str
    request: AuthorityUpdateRequest
    expected_a3: ConformanceDecision
    expected_a4: ConformanceDecision
    family: str


@dataclass(frozen=True)
class ConformanceReport:
    schema_version: str
    status: str
    cases_checked: int
    all_passed: bool
    failures: Tuple[str, ...]
    grants_scientific_authority: bool
    artifact_hash: str

    def to_dict(self) -> Mapping[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "cases_checked": self.cases_checked,
            "all_passed": self.all_passed,
            "failures": list(self.failures),
            "grants_scientific_authority": False,
            "artifact_hash": self.artifact_hash,
        }


class TransactionalGovernancePolicy:
    """A3: accept schema+provenance-valid updates; ignore typed axes."""

    arm = AblationArm.A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED

    def decide(self, request: AuthorityUpdateRequest) -> PolicyDecision:
        if not request.schema_valid:
            return PolicyDecision(self.arm, ConformanceDecision.REJECT, "schema_invalid")
        if not request.provenance_valid:
            return PolicyDecision(self.arm, ConformanceDecision.REJECT, "provenance_invalid")
        return PolicyDecision(
            self.arm,
            ConformanceDecision.ACCEPT,
            "provenance_and_schema_valid_scalar_authority",
        )


class ScientificAuthorityTypingPolicy:
    """A4: accept only when requested axis is licensed by the observation."""

    arm = AblationArm.A4_SCIENTIFIC_AUTHORITY_TYPING

    def decide(self, request: AuthorityUpdateRequest) -> PolicyDecision:
        if not request.schema_valid:
            return PolicyDecision(self.arm, ConformanceDecision.REJECT, "schema_invalid")
        if not request.provenance_valid:
            return PolicyDecision(self.arm, ConformanceDecision.REJECT, "provenance_invalid")
        if request.requested_axis not in request.licensed_axes:
            return PolicyDecision(
                self.arm,
                ConformanceDecision.REJECT,
                f"axis_{request.requested_axis.value}_not_licensed_by_{request.observation_kind}",
            )
        return PolicyDecision(
            self.arm,
            ConformanceDecision.ACCEPT,
            f"axis_{request.requested_axis.value}_licensed",
        )


def decide(arm: AblationArm, request: AuthorityUpdateRequest) -> PolicyDecision:
    if arm is AblationArm.A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED:
        return TransactionalGovernancePolicy().decide(request)
    if arm is AblationArm.A4_SCIENTIFIC_AUTHORITY_TYPING:
        return ScientificAuthorityTypingPolicy().decide(request)
    raise ValueError(f"unsupported arm: {arm}")


def frozen_conformance_panel() -> Tuple[ConformanceCase, ...]:
    """Hostile + legal fixtures with identical information to both arms."""

    pred_not_mech = AuthorityUpdateRequest(
        request_id="req-pred-mech",
        claim_id="claim-mediator",
        proposition="M mediates X→Y",
        evidence_ids=("ev-predictive-fit",),
        provenance_valid=True,
        schema_valid=True,
        requested_axis=AuthorityAxis.MECHANISM,
        licensed_axes=(AuthorityAxis.REPRESENTATION,),
        observation_kind="predictive_fit_only",
    )
    legal_mech = AuthorityUpdateRequest(
        request_id="req-legal-mech",
        claim_id="claim-mediator",
        proposition="M mediates X→Y",
        evidence_ids=("ev-intervene-m",),
        provenance_valid=True,
        schema_valid=True,
        requested_axis=AuthorityAxis.MECHANISM,
        licensed_axes=(AuthorityAxis.REPRESENTATION, AuthorityAxis.MECHANISM),
        observation_kind="interventional_mediator",
    )
    mech_not_ident = AuthorityUpdateRequest(
        request_id="req-mech-ident",
        claim_id="claim-ident",
        proposition="unique mechanism identified",
        evidence_ids=("ev-plausible-mech",),
        provenance_valid=True,
        schema_valid=True,
        requested_axis=AuthorityAxis.IDENTIFICATION,
        licensed_axes=(AuthorityAxis.MECHANISM,),
        observation_kind="observationally_equivalent_rivals",
    )
    bad_provenance = AuthorityUpdateRequest(
        request_id="req-bad-prov",
        claim_id="claim-any",
        proposition="any claim",
        evidence_ids=("ev-x",),
        provenance_valid=False,
        schema_valid=True,
        requested_axis=AuthorityAxis.GROUNDING,
        licensed_axes=(AuthorityAxis.GROUNDING,),
        observation_kind="unsourced",
    )
    return (
        ConformanceCase(
            case_id="hostile-prediction-to-mechanism",
            request=pred_not_mech,
            expected_a3=ConformanceDecision.ACCEPT,
            expected_a4=ConformanceDecision.REJECT,
            family="prediction_to_mechanism_leakage",
        ),
        ConformanceCase(
            case_id="legal-mechanism-upgrade",
            request=legal_mech,
            expected_a3=ConformanceDecision.ACCEPT,
            expected_a4=ConformanceDecision.ACCEPT,
            family="valid_authority_upgrade_control",
        ),
        ConformanceCase(
            case_id="hostile-mechanism-to-identification",
            request=mech_not_ident,
            expected_a3=ConformanceDecision.ACCEPT,
            expected_a4=ConformanceDecision.REJECT,
            family="mechanism_to_identification_leakage",
        ),
        ConformanceCase(
            case_id="shared-provenance-reject",
            request=bad_provenance,
            expected_a3=ConformanceDecision.REJECT,
            expected_a4=ConformanceDecision.REJECT,
            family="information_matched_negative_control",
        ),
    )


def run_conformance(cases: Sequence[ConformanceCase] | None = None) -> ConformanceReport:
    panel = tuple(cases) if cases is not None else frozen_conformance_panel()
    failures: list[str] = []
    for case in panel:
        a3 = decide(AblationArm.A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED, case.request)
        a4 = decide(AblationArm.A4_SCIENTIFIC_AUTHORITY_TYPING, case.request)
        if a3.decision is not case.expected_a3:
            failures.append(f"{case.case_id}: A3 got {a3.decision.value} expected {case.expected_a3.value}")
        if a4.decision is not case.expected_a4:
            failures.append(f"{case.case_id}: A4 got {a4.decision.value} expected {case.expected_a4.value}")
        # Information availability invariant: both arms see identical request bytes.
        _ = case.request

    payload = {
        "schema_version": "paper2-a3-a4-conformance-v1",
        "status": "CONFORMANCE_PASS" if not failures else "CONFORMANCE_FAIL",
        "cases_checked": len(panel),
        "all_passed": not failures,
        "failures": failures,
        "grants_scientific_authority": False,
        "arm_gap_note": (
            "A3 is function-matched transactional governance only; not MemTX/PPMF. "
            "A4 adds typed axis licensing. No model ablation executed."
        ),
        "case_ids": [c.case_id for c in panel],
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(blob).hexdigest()
    return ConformanceReport(
        schema_version=payload["schema_version"],
        status=payload["status"],
        cases_checked=len(panel),
        all_passed=not failures,
        failures=tuple(failures),
        grants_scientific_authority=False,
        artifact_hash=digest,
    )
