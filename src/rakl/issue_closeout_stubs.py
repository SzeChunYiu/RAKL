"""Proposal-only closeout stubs for research issues #129/#130/#132/#155/#156/#157.

Status: ``DONE_FOR_NOW_CONTRACT / PROPOSAL_ONLY / NO_SCIENTIFIC_AUTHORITY``.

These objects freeze schema identity and the hard authority refusal. They are
not wired into promotion gates and never mint theorem/tool/review authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple


class StubStatus(str, Enum):
    STUB_FROZEN = "STUB_FROZEN"
    PROTOCOL_FROZEN = "PROTOCOL_FROZEN"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class CloseoutStubReport:
    schema_version: str
    status: StubStatus
    issue: int
    reasons: Tuple[str, ...]
    grants_scientific_authority: bool = False

    def __post_init__(self) -> None:
        if self.grants_scientific_authority:
            raise ValueError("closeout stubs cannot grant scientific authority")
        if self.issue <= 0:
            raise ValueError("issue must be positive")
        if not self.reasons:
            raise ValueError("at least one reason required")
        if not self.schema_version:
            raise ValueError("schema_version required")

    @property
    def artifact_hash(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "issue": self.issue,
            "reasons": list(self.reasons),
            "grants_scientific_authority": False,
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(blob).hexdigest()

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "issue": self.issue,
            "reasons": list(self.reasons),
            "grants_scientific_authority": False,
            "artifact_hash": self.artifact_hash,
        }


ISSUE_SCHEMA: Dict[int, str] = {
    129: "associative-experience-retrieval-report-v1",
    130: "epistemic-gps-navigation-report-v1",
    132: "conceptual-basis-independence-report-v1",
    155: "learning-governance-factorial-protocol-v1",
    156: "closest-parent-ablation-suite-v1",
    157: "experience-to-method-promotion-receipt-v1",
}


def freeze_stub(issue: int, *reasons: str, status: StubStatus = StubStatus.STUB_FROZEN) -> CloseoutStubReport:
    if issue not in ISSUE_SCHEMA:
        raise ValueError(f"unsupported closeout issue: {issue}")
    if issue in (155, 156) and status == StubStatus.STUB_FROZEN:
        status = StubStatus.PROTOCOL_FROZEN
    return CloseoutStubReport(
        schema_version=ISSUE_SCHEMA[issue],
        status=status,
        issue=issue,
        reasons=tuple(reasons) if reasons else ("done_for_now_contract_frozen",),
    )


def freeze_all_closeout_stubs() -> Tuple[CloseoutStubReport, ...]:
    return (
        freeze_stub(
            129,
            "associative_retrieval_operator_contract_frozen",
            "similarity_witness_still_required_before_transfer",
        ),
        freeze_stub(
            130,
            "epistemic_navigation_controller_contract_frozen",
            "not_a_shortest_path_claim_over_mathematics",
        ),
        freeze_stub(
            132,
            "conceptual_basis_independence_metric_contract_frozen",
            "same_session_roles_are_not_independent_review",
        ),
        freeze_stub(
            155,
            "2x2_learning_x_governance_protocol_frozen",
            "no_evaluated_model_result_precedes_this_freeze",
        ),
        freeze_stub(
            156,
            "closest_parent_ablation_suite_inventory_frozen",
            "autosci_memtx_provenance_firewall_parents_named_only",
        ),
        freeze_stub(
            157,
            "experience_to_method_requires_protected_fresh_assurance",
            "experience_alone_never_promotes",
        ),
    )


__all__ = [
    "CloseoutStubReport",
    "ISSUE_SCHEMA",
    "StubStatus",
    "freeze_all_closeout_stubs",
    "freeze_stub",
]
