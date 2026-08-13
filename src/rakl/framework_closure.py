from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class ClosureDisposition(str, Enum):
    CLOSED_CODE_TEST = "CLOSED_CODE_TEST"
    CLOSED_THEOREM_OR_PROOF_OBLIGATION = "CLOSED_THEOREM_OR_PROOF_OBLIGATION"
    CLOSED_ASSUMPTION_BOUNDARY = "CLOSED_ASSUMPTION_BOUNDARY"
    OUT_OF_SCOPE_GATED = "OUT_OF_SCOPE_GATED"
    OPEN_EMPIRICAL = "OPEN_EMPIRICAL"
    OPEN_EXTERNAL_ASSURANCE = "OPEN_EXTERNAL_ASSURANCE"
    REJECTED_AS_INVALID_CLAIM = "REJECTED_AS_INVALID_CLAIM"


@dataclass(frozen=True)
class ClosureIssue:
    issue_id: str
    title: str
    owner_surface: str
    severity: str
    subject_hash: str
    disposition: ClosureDisposition
    evidence_ids: Tuple[str, ...] = ()
    test_paths: Tuple[str, ...] = ()
    falsifier: str | None = None
    next_epistemic_cut: str | None = None
    reviewer_context_ids: Tuple[str, ...] = ()

    def problems(self) -> Tuple[str, ...]:
        out = []
        if not all((self.issue_id, self.title, self.owner_surface, self.severity, self.subject_hash)):
            out.append("missing_required_identity")
        if self.disposition in {
            ClosureDisposition.CLOSED_CODE_TEST,
            ClosureDisposition.CLOSED_THEOREM_OR_PROOF_OBLIGATION,
            ClosureDisposition.CLOSED_ASSUMPTION_BOUNDARY,
            ClosureDisposition.REJECTED_AS_INVALID_CLAIM,
        } and not self.evidence_ids:
            out.append("closed_or_rejected_issue_missing_evidence")
        if self.disposition is ClosureDisposition.CLOSED_CODE_TEST and not self.test_paths:
            out.append("code_closed_issue_missing_test")
        if self.disposition in {
            ClosureDisposition.OPEN_EMPIRICAL,
            ClosureDisposition.OPEN_EXTERNAL_ASSURANCE,
            ClosureDisposition.OUT_OF_SCOPE_GATED,
        }:
            if not self.next_epistemic_cut:
                out.append("open_or_gated_issue_missing_next_cut")
            if self.disposition is ClosureDisposition.OPEN_EMPIRICAL and not self.falsifier:
                out.append("open_empirical_issue_missing_falsifier")
        return tuple(out)


@dataclass(frozen=True)
class ClosureLedger:
    ledger_id: str
    frozen_subject_hash: str
    issues: Tuple[ClosureIssue, ...]
    audit_context_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.ledger_id or not self.frozen_subject_hash:
            raise ValueError("closure ledger requires identity and frozen subject")
        if not self.issues:
            raise ValueError("closure ledger requires issues")
        ids = [item.issue_id for item in self.issues]
        if len(ids) != len(set(ids)):
            raise ValueError("closure issue ids must be unique")

    @property
    def problems(self) -> Tuple[Tuple[str, Tuple[str, ...]], ...]:
        return tuple((issue.issue_id, issue.problems()) for issue in self.issues if issue.problems())

    @property
    def has_unowned_or_unclassified_issue(self) -> bool:
        return bool(self.problems)

    @property
    def registered_issues_all_owned(self) -> bool:
        return not self.problems

    @property
    def establishes_no_hidden_issue_exists(self) -> bool:
        return False

    @property
    def grants_scientific_authority(self) -> bool:
        return False
